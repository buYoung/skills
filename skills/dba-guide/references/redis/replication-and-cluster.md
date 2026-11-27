# Redis Replication, Sentinel, and Cluster

Checked: 2026-11-27 (sources at the end).

Contents: [Replication](#replication) · [Consistency](#consistency) · [Sentinel](#sentinel) · [Cluster](#cluster) · [Resharding](#resharding) · [Failover and upgrades](#failover-and-rolling-upgrades)

## Choose a Topology

| Topology | Scales writes | Automatic failover | Multi-key ops | Use when |
|---|---|---|---|---|
| Single primary + replicas | No | No | All | Dataset fits one node; manual or scripted failover acceptable |
| Primary + replicas + Sentinel (3+ Sentinels) | No | Yes | All | Dataset and write load fit one node; need HA |
| Redis Cluster (3+ primaries, 1+ replica each) | Yes | Yes (built in) | Same hash slot only | Dataset or write load exceeds one node |

Moving from standalone to Cluster changes the application: multi-key commands, transactions, and scripts must use hash tags, only database 0 exists, and clients must be cluster-aware.

## Replication

Mechanism: the primary streams write commands to replicas asynchronously. After a disconnect the replica tries a partial resync (`PSYNC`) from the primary's backlog using the replication ID and offset; if the backlog no longer holds the gap, or the history is unknown, it does a full sync (RDB transfer, then the buffered stream).

- `repl-backlog-size` default 1 MB on every checked image. Size it to cover the longest disconnect you want to survive without a full sync: write bytes per second (from `instantaneous_output_repl_kbps` or the growth of `master_repl_offset`) times seconds of outage. Full syncs fork on the primary and reload the whole dataset on the replica.
- `repl-diskless-sync yes` (default since 7.0): the RDB streams directly over the socket. `repl-diskless-sync-delay 5` waits for more replicas to join.
- `repl-diskless-load disabled` (default): replica writes the received RDB to disk before loading. `swapdb` loads while serving the old dataset (needs memory for both); `flushdb` ([8.6](versions/8.6.md)) drops the old dataset first.
- `replica-read-only yes` (default). Writable replicas cause divergence; do not use them.
- `replica-ignore-maxmemory yes` (default): replicas do not evict; the primary's `DEL`s keep them in step. Give replicas at least as much memory headroom as the primary.
- Replica output buffer: `client-output-buffer-limit replica 256mb 64mb 60` (8.12 image shows `slave 268435456 67108864 60`). A replica that exceeds it during full sync is disconnected and retries, which can loop. Raise it for large write bursts during sync. 8.0 added `replica-full-sync-buffer-limit` on the replica side.
- 8.10 added replication stream compression (`repl-compression`, zstd level 0–22, default 0 = off; needs `io-threads` > 1 and a build with `BUILD_COMPRESSION=yes`); see [8.10](versions/8.10.md).
- A replica restarted with `SHUTDOWN` (save and quit) keeps replication metadata in its RDB and can partially resync. A replica that restarts from AOF cannot.

Set up and check:

```
# on the replica
REPLICAOF 10.0.0.1 6379
CONFIG SET masterauth <password>          # or masteruser + masterauth with ACLs
# on either
INFO replication
ROLE
```

Read `INFO replication`:

- Primary: `connected_slaves`, one `slaveN:ip=...,state=online,offset=...,lag=...` line per replica, `master_repl_offset`, `repl_backlog_size`, `repl_backlog_histlen`.
- Replica: `master_link_status:up`, `master_last_io_seconds_ago`, `master_sync_in_progress`, `slave_repl_offset`; 8.2+ adds `master_current_sync_attempts`, `master_total_sync_attempts`, `master_link_up_since_seconds`, `total_disconnect_time_sec`.
- `INFO stats` `sync_full`, `sync_partial_ok`, `sync_partial_err` on the primary: a rising `sync_full` means the backlog is too small or replicas are timing out.

Replication behind NAT or Docker port mapping: set `replica-announce-ip` and `replica-announce-port` so the primary and Sentinel report reachable addresses.

## Consistency

Redis replication is asynchronous. A write acknowledged by the primary can be lost if the primary fails before the replica receives it. Neither Sentinel nor Cluster provides strong consistency.

- `WAIT <numreplicas> <timeout-ms>` blocks until that many replicas acknowledged the client's prior writes. It lowers the loss window; it does not make the system CP.
- `WAITAOF <numlocal> <numreplicas> <timeout>` ([7.2](versions/7.2.md)) waits until writes are fsynced to the local AOF and/or replica AOFs.
- `min-replicas-to-write N` + `min-replicas-max-lag S`: the primary rejects writes unless N replicas have lag at most S seconds. Bounds how long an isolated primary accepts writes after a partition (defaults `0` and `10`). Cost: if replicas are down, writes stop.
- Need acknowledged writes to survive failover: use a durable managed engine ([MemoryDB](managed-services.md#memorydb)) or a database with synchronous replication.

## Sentinel

Sentinel monitors a primary and its replicas, agrees on failure, elects a leader, promotes a replica, reconfigures the others, and serves the current primary address to clients.

Rules:

- Run at least three Sentinels on hosts that fail independently. Two Sentinels cannot fail over safely.
- `quorum` only decides when the primary is objectively down (`ODOWN`); the failover itself needs votes from a majority of all Sentinels. No failover happens in a minority partition.
- Pair Sentinel with `min-replicas-to-write 1` and `min-replicas-max-lag 10` on the data nodes to stop an isolated old primary from accepting writes that will be discarded.
- Clients must be Sentinel-aware and ask `SENTINEL get-master-addr-by-name <name>` (or subscribe to `+switch-master`).
- Sentinel needs a writable config file; it rewrites it on discovery and failover.
- Docker port remapping breaks Sentinel discovery; use host networking or `sentinel announce-ip`/`announce-port`.

Minimal config:

```
port 26379
sentinel monitor mymaster 10.0.0.1 6379 2
sentinel down-after-milliseconds mymaster 10000
sentinel failover-timeout mymaster 180000
sentinel parallel-syncs mymaster 1
sentinel auth-user mymaster sentinel-user      # ACL user on data nodes
sentinel auth-pass mymaster <password>
```

Evidence:

```
redis-cli -p 26379 SENTINEL master mymaster      # flags, num-slaves, num-other-sentinels, quorum
redis-cli -p 26379 SENTINEL replicas mymaster
redis-cli -p 26379 SENTINEL sentinels mymaster
redis-cli -p 26379 SENTINEL ckquorum mymaster     # can the current set authorize a failover?
redis-cli -p 26379 INFO sentinel                  # 8.2+: sentinel_total_tilt
```

`flags` shows `s_down` (this Sentinel thinks it is down) or `o_down` (quorum agrees). TILT mode (time jumps, overloaded host) pauses Sentinel actions; frequent TILT means the host is unhealthy.

Test failover regularly: `SENTINEL FAILOVER mymaster` forces one without agreement from others; check that clients follow the new address within your recovery target.

## Cluster

Mechanism: 16384 hash slots, slot = CRC16(key) mod 16384, or CRC16 of the hash tag. Each primary owns a set of slots; replicas fail over for their primary. Clients receive `-MOVED <slot> <host:port>` when they address the wrong node and `-ASK` during a slot migration; cluster-aware clients cache the slot map from `CLUSTER SHARDS` (7.0+; `CLUSTER SLOTS` is deprecated).

Each node needs two ports open between all nodes: the client port and the cluster bus port (client port + 10000 unless `cluster-port` is set). NAT and port remapping are not supported; use host networking in containers.

Key parameters (8.12 image defaults):

| Parameter | Default | Meaning |
|---|---|---|
| `cluster-node-timeout` | 15000 ms | unreachable this long: primary fails over; a primary cut off from the majority this long stops accepting writes |
| `cluster-require-full-coverage` | `yes` | stop all writes if any slot is uncovered; `no` keeps serving the covered slots |
| `cluster-allow-reads-when-down` | `no` | `yes` serves reads during fail state |
| `cluster-replica-validity-factor` | 10 | a replica disconnected longer than timeout x factor will not fail over; 0 always tries |
| `cluster-migration-barrier` | 1 | replicas a primary keeps before one migrates to an orphaned primary |
| `cluster-allow-replica-migration` | `yes` | |
| `cluster-allow-pubsubshard-when-down` | `yes` | |
| `cluster-preferred-endpoint-type` | `ip` | what `MOVED` and `CLUSTER SHARDS` advertise (`ip`, `hostname`, `unknown-endpoint`) |
| `cluster-slot-stats-enabled` | `no` | 8.2+ (present on the 8.2 to 8.12 images): adds per-slot `memory-bytes`, `cpu-usec`, `network-bytes-in`, `network-bytes-out` to `CLUSTER SLOT-STATS`; `key-count` is reported either way. 8.2 and 8.4 take `yes`/`no` only. From 8.6 the value is a space-separated list of `cpu`, `net`, `mem` (`yes` = all three); `mem` can be enabled only at startup, so a runtime `CONFIG SET ... yes` fails with `memory tracking cannot be enabled at runtime` (8.12.0 `redis.conf`; 8.4.8 rejected `"cpu net"`, 8.6.8 to 8.12.0 accepted it and refused runtime `yes`) |
| `cluster-bus-port-protected-mode` | `yes` | `no` on the 8.2 to 8.10 images. On 8.12.0 a node with `cluster-enabled yes` and `tls-cluster no` refuses to start until you set `tls-cluster yes` or `cluster-bus-port-protected-mode no` |

Rules:

- Minimum three primaries; production layout three primaries with one replica each, in different failure domains.
- A primary and all its replicas failing together makes the cluster unavailable (with full coverage on).
- Multi-key commands, `MULTI`/`EXEC`, Lua, and Functions must touch one slot; otherwise `CROSSSLOT`. Design hash tags up front ([data modeling](data-modeling.md#key-design)).
- `SELECT` other than 0 is rejected.
- Pub/Sub `PUBLISH` is broadcast to every node over the bus; use sharded Pub/Sub (`SPUBLISH`/`SSUBSCRIBE`, 7.0+) at scale.

Create and check:

```
redis-cli --cluster create 10.0.0.1:6379 10.0.0.2:6379 10.0.0.3:6379 \
  10.0.0.4:6379 10.0.0.5:6379 10.0.0.6:6379 --cluster-replicas 1
redis-cli --cluster check 10.0.0.1:6379
redis-cli -c -h 10.0.0.1 CLUSTER INFO       # cluster_state:ok, cluster_slots_assigned:16384
redis-cli -h 10.0.0.1 CLUSTER SHARDS
redis-cli -h 10.0.0.1 CLUSTER KEYSLOT 'cart:{u123}:items'
redis-cli -h 10.0.0.1 CLUSTER SLOT-STATS ORDERBY KEY-COUNT LIMIT 10   # 8.2+
redis-cli -h 10.0.0.1 CLUSTER SLOT-STATS SLOTSRANGE 0 10
```

Both `SLOT-STATS` forms ran on 8.12.0 and return each slot with its counters. `ORDERBY CPU-USEC` returns `ERR Unrecognized sort metric for ORDERBY.` unless `cluster-slot-stats-enabled yes`. `CLUSTER KEYSLOT 'cart:{u123}:items'` and `CLUSTER KEYSLOT u123` both return 10594.

`CLUSTER INFO` on a non-cluster instance returns `ERR This instance has cluster support disabled` (observed on every image).

## Resharding

Two mechanisms:

| | Key-by-key (`MIGRATE`) | Atomic slot migration ([8.4](versions/8.6.md#changes-first-shipped-in-84)+) |
|---|---|---|
| Command | `redis-cli --cluster reshard` / `rebalance` (before 8.10) or `CLUSTER SETSLOT` + `MIGRATE` | `CLUSTER MIGRATION IMPORT <start> <end> [...]` on the destination primary; `redis-cli --cluster reshard`/`rebalance` use it from 8.10 |
| Client impact | `ASK` redirects per key; multi-key commands on a migrating slot can fail with `TRYAGAIN` | Short write pause at handoff (`cluster-slot-migration-write-pause-timeout` 10000 ms max; handoff when remaining stream < `cluster-slot-migration-handoff-max-lag-bytes`, default 1 MB) |
| Big keys | One `MIGRATE` per key blocks both nodes for the key's size | Snapshot plus incremental stream |
| Monitor | `redis-cli --cluster check` | `CLUSTER MIGRATION STATUS ALL` (8.12 reports phase progress); `write_pause_ms`, `last_error`, `retries` |

Atomic slot migration notes:

- Cancelling on the source does not stop the destination; run `CLUSTER MIGRATION CANCEL` on both.
- While importing or trimming, `KEYS`, `SCAN`, `RANDOMKEY`, `DBSIZE`, `CLUSTER GETKEYSINSLOT`, `CLUSTER COUNTKEYSINSLOT` may hide keys of unowned slots; `INFO keyspace` shows the real count.
- Search and time series multi-shard queries may return partial or duplicate results during migration (8.4 known limitation).
- 8.12 fixed key loss during migration when the destination rejected a command (for example `-NOREPLICAS` from `min-replicas-to-write`) (#16176). Use 8.12 or a patch that contains the fix before running migrations with `min-replicas-to-write` set.

Non-interactive key-by-key reshard:

```
redis-cli --cluster reshard 10.0.0.1:6379 --cluster-from <src-id> \
  --cluster-to <dst-id> --cluster-slots 1000 --cluster-yes
```

Find what to move: `CLUSTER SLOT-STATS` (8.2+) for per-slot keys, CPU, and network; `CLUSTER COUNTKEYSINSLOT <slot>`; `HOTKEYS` (8.6+) per node.

## Failover and Rolling Upgrades

Manual failover in Cluster: run `CLUSTER FAILOVER` on the replica to promote. The default form waits for the replica to catch up and switches clients without data loss. `FORCE` skips the handshake with the primary; `TAKEOVER` skips the cluster vote (use only when the majority is gone and you accept split-brain risk). A newly added replica must be known to a majority of primaries before it can win.

Standalone or Sentinel: `FAILOVER` on the primary (6.2+) coordinates a switch to a replica; `SENTINEL FAILOVER <name>` through Sentinel.

Rolling upgrade, Cluster: upgrade replicas one at a time; for each primary, `CLUSTER FAILOVER` from an upgraded replica, wait for the old primary to become a replica, upgrade it, optionally fail back. Same for Sentinel setups using `SENTINEL FAILOVER`. Version-specific blockers are in the [version files](versions/index.md).

After any failover check: `ROLE` on each node, `INFO replication` offsets, `CLUSTER INFO` `cluster_state:ok`, client error rate, and that the old primary rejoined as a replica (`master_link_status:up`).

Sources: https://redis.io/docs/latest/operate/oss_and_stack/management/replication/, https://redis.io/docs/latest/operate/oss_and_stack/management/sentinel/, https://redis.io/docs/latest/operate/oss_and_stack/management/scaling/, https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/, https://redis.io/docs/latest/commands/cluster-migration/, https://redis.io/docs/latest/commands/info/, release notes linked from [versions](versions/index.md) (checked 2026-11-27); image `redis:8.12` `CONFIG GET` output and statement runs (2026-11-27).
