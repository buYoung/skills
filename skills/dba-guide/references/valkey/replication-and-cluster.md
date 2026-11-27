# Valkey Replication and Cluster

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)).

Asynchronous primary-replica replication, PSYNC with a backlog, `WAIT`, Sentinel, the 16384-slot cluster with gossip and failover election, hash tags and `MOVED`/`ASK` redirects come from Redis OSS 7.2. Read [../redis/replication-and-cluster.md](../redis/replication-and-cluster.md) for them.

## Replication defaults (official images)

| Setting | 7.2 | 8.0 – 9.2 |
| --- | --- | --- |
| `repl-backlog-size` | 1 MB | 10 MB |
| `repl-diskless-sync` | `yes` | `yes` |
| `repl-diskless-load` | `disabled` | `disabled` |
| `dual-channel-replication-enabled` | – | `no` |
| `repl-compression` | – | `no` (9.2) |
| `repl-throttling-enabled` | – | `no` (9.2) |
| `client-output-buffer-limit` replica class | `256mb 64mb 60` | same |

Backlog sizing: the backlog must hold all writes made while a replica is disconnected, or the replica falls back to a full sync. Measure write volume with `INFO stats` `total_net_repl_output_bytes` over time (or `master_repl_offset` deltas) and size `repl-backlog-size` for the longest expected disconnect. An old config file with `repl-backlog-size 1mb` keeps the 1 MB value after an upgrade.

## Full sync options

| Option | Series | Use when | Cost |
| --- | --- | --- | --- |
| Disk-based (`repl-diskless-sync no`) | all | slow network, several replicas syncing at once | disk I/O on primary |
| Diskless (`repl-diskless-sync yes`, default) | all | fast network | fork on primary; replicas arriving late wait for the next transfer |
| Dual channel (`dual-channel-replication-enabled yes` on both sides) | 8.0+ | primary memory is tight during full sync | replica buffers the stream, so the replica needs headroom; requires `repl-diskless-sync yes` |
| Forkless full sync | 9.2 (`forkless-infrastructure-enabled yes` at startup) | fork copy-on-write is the problem | new code path; rehearse |
| Compressed replication (`repl-compression lz4`) | 9.2 | network bandwidth bound, cross-AZ | CPU; per-replica negotiation |

Evidence while a full sync runs: `INFO replication` on the replica (`master_sync_in_progress`, `master_sync_total_bytes`, `master_sync_read_bytes`), on the primary (`slaveN:...state=`), `INFO stats` `sync_full`, `sync_partial_ok`, `sync_partial_err`. On 9.2 `last_successful_sync_duration_ms` records the last full sync time.

Replica lag control (9.2): `repl-throttling-enabled yes` slows client writes when a replica falls behind instead of letting its output buffer hit `client-output-buffer-limit` and forcing a new full sync. Use it where a full sync is more harmful than a short write slowdown.

## Failover behavior differences

- 8.1: cluster elections are ordered by failed-primary rank to avoid split votes; manual and automatic failover votes are no longer limited to twice the node timeout.
- 9.0: a cluster primary can fail over to a replica before it shuts down. Select it with `shutdown-on-sigterm failover` and `shutdown-on-sigint failover`, or per call with `SHUTDOWN FAILOVER`; both configs default to `default` in the 9.0.8 image, and 8.1 rejects the `failover` value; `CLUSTER REPLICATE NO ONE` lets a replica become an empty primary; failover delay is relative to `cluster-node-timeout`.
- 9.1: a replica that is the best-ranked replica fails over at once; failing to write `nodes.conf` no longer exits the process.
- 9.2: `cluster-replica-priority` ranks replicas for automatic failover; `cluster-replica-no-failover if-empty` stops a replica that never received data from being promoted (prevents silent data loss after a replica restart); split-vote elections recover faster.
- All series: Sentinel accepts both the `master` and `primary` command names (`SENTINEL GET-PRIMARY-ADDR-BY-NAME` since 8.0).

Verify a failover setup: `CLUSTER NODES` (one primary per slot range, replicas `connected`), `CLUSTER INFO` `cluster_state:ok`, a planned `CLUSTER FAILOVER` on a replica during low traffic with client error rates recorded.

## Resharding: atomic slot migration (9.0+)

Legacy migration (`CLUSTER SETSLOT IMPORTING/MIGRATING`, `CLUSTER GETKEYSINSLOT`, `MIGRATE`) moves keys one batch at a time and clients see `ASK` redirects and `TRYAGAIN` on multi-key commands. Atomic slot migration snapshots the slots, streams later writes, pauses writes briefly, then transfers ownership:

```
# on the source primary
CLUSTER MIGRATESLOTS SLOTSRANGE 0 999 NODE <target-node-id>
CLUSTER GETSLOTMIGRATIONS          # poll on source or target
CLUSTER CANCELSLOTMIGRATIONS       # cancel all migrations sourced here
```

`valkey-cli --cluster` supports atomic slot migration from 9.1. Decision rules and checks:

- Use it on 9.0+ clusters for all planned resharding; keep legacy migration only for mixed-version clusters or modules that have not opted in to atomic slot migration (the feature is disabled in clusters loading such modules).
- The snapshot forks on the source (unless forkless applies) and accumulated writes count against the replica output buffer; raise the hard and soft limits of the `replica` class of `client-output-buffer-limit` before large migrations.
- On high write rates set `slot-migration-max-failover-repl-bytes` so the final pause can start while some bytes are still in flight.
- `FLUSHDB`/`FLUSHALL` on source or target fail the migration; retry afterwards.
- The target applies migrated data as `primaryuser`; grant `+@write ~* -@dangerous +ping +select +psync +replconf +cluster|syncslots -flushall -flushdb -restore -restore-asking`, or the target logs `-NOPERM` and the migration fails.
- 9.2: per-target `AUTH username password` in `CLUSTER MIGRATESLOTS`; credentials are redacted from slowlog and `MONITOR`.
- Importing slots are hidden from `KEYS`, `SCAN`, `DBSIZE` on the target until ownership moves.

## Numbered databases in cluster mode (9.0+)

`cluster-databases` (default 1, set at startup) enables `SELECT` in cluster mode. The `databases` setting is ignored in cluster mode. Modeling caveats are in [data-modeling.md](data-modeling.md). Operational points: `CLUSTER FLUSHSLOT` (9.0) removes keys in a slot from all databases; database-level ACLs exist from 9.1; atomic slot migration with `cluster-databases > 1` had a bug applying snapshot-period writes to the wrong database, fixed in 9.0.7 and 9.1.3.

## Cluster-wide scanning and routing

- `CLUSTERSCAN` (9.1) iterates keys across all nodes from one client. Cursors survive failover between nodes that share `hash-seed` (9.2 fix).
- `hash-seed` (9.1, immutable) gives every node the same hashtable seed, so `SCAN` order is consistent across restarts and failovers.
- 9.2: cluster replicas redirect keyless commands such as `SCAN` and `FLUSHDB` to the primary for clients that sent `CLIENT CAPA REDIRECT` and not `READONLY`.
- 9.1: `CLUSTER SHARDS`/`CLUSTER SLOTS` include `availability-zone`; strict client parsers may fail.

## Mixed-version clusters

Allowed only during a rolling upgrade. Do not use new commands or types until every node runs the new version. For 9.0 ↔ 9.1 mixes, use 9.1.3 or later. Upgrade replicas first, then fail over each shard one at a time.
