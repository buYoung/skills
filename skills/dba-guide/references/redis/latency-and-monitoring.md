# Redis Latency Diagnosis and Monitoring

Checked: 2026-11-27 (sources at the end).

## Triage Order

Redis executes commands on one main thread, so one slow command delays every client. Work through causes in this order:

1. Environment floor: `redis-cli --intrinsic-latency 100` run on the server host (not the client). Virtualized hosts can show milliseconds of latency that no Redis setting fixes.
2. Slow commands: `SLOWLOG GET 20`.
3. Latency events: enable the latency monitor and run `LATENCY DOCTOR`.
4. Fork cost: `latest_fork_usec` after a `BGSAVE` or rewrite.
5. Memory: swapping, transparent huge pages, eviction pressure.
6. Disk: AOF fsync on slow storage.
7. Expiration storms and big-key deletes.
8. Network and client side: pipelining, connection churn, output buffers.

## Slow Log

Records commands whose execution time (excluding network I/O) exceeds `slowlog-log-slower-than` microseconds (default 10000 = 10 ms), keeping `slowlog-max-len` entries (default 128).

```
CONFIG SET slowlog-log-slower-than 1000     # 1 ms while investigating
SLOWLOG GET 10
SLOWLOG LEN
SLOWLOG RESET
```

Entry fields: id, Unix timestamp, duration in microseconds, arguments, client address, client name; 7th field total argument count ([8.10](versions/8.10.md)+); 8th field CPU time in microseconds ([8.12](versions/8.12.md)+, `off-cpu-tracking yes` default). Observed field counts: 6 on 8.8.4, 7 on 8.10.3, 8 on 8.12.0. Duration much larger than CPU time means the command waited for CPU (host contention, swapping), not that it was expensive.

Since [8.8](versions/8.8.md), entries keep at most `slowlog-entry-max-argc` (32) arguments and `slowlog-entry-max-string-len` (128) bytes per argument. `INFO commandstats` gains `slowlog_count`, `slowlog_time_ms_sum`, `slowlog_time_ms_max` per command from 8.8.

Typical offenders: `KEYS`, `SMEMBERS`/`HGETALL`/`LRANGE 0 -1` on big keys, `SORT`, `ZUNIONSTORE` on large sets, `DEL` of large keys, long Lua scripts, `FLUSHALL` without `ASYNC`. Fix the access pattern: `SCAN` family, bounded ranges, `UNLINK`, smaller keys.

`COMMANDLOG` (slow, large-request, large-reply logs) is a Valkey command; Redis 8.12 returns `ERR unknown command 'COMMANDLOG'`.

## Latency Monitor

Off by default (`latency-monitor-threshold 0`); `LATENCY DOCTOR` says so when disabled (observed on all images).

```
CONFIG SET latency-monitor-threshold 50     # ms
LATENCY LATEST            # event, last time, last ms, max ms
LATENCY HISTORY fork      # time series for one event
LATENCY DOCTOR            # human-readable analysis
LATENCY RESET
LATENCY HISTOGRAM SET GET # 7.0+: per-command latency distribution
INFO latencystats         # 7.0+: p50/p99/p99.9 per command (latency-tracking yes)
```

Event names include `command`, `fast-command`, `fork`, `aof-write`, `aof-fsync-always`, `expire-cycle`, `eviction-cycle`, `eviction-del` (list from the latency monitor docs). On 8.12.0 with threshold 1 ms, `DEBUG SLEEP 0.1` produced a `command` event of 100 ms, and the image's bundled modules also produced `module-acquire-GIL`. No `fork` event appeared because the fork took less than the threshold (`latest_fork_usec:696` with 800000 keys).

## Fork and Copy-on-Write

`BGSAVE`, AOF rewrite, full replica sync, and `BACKUP START` ([8.10](versions/8.10.md)) fork. The fork itself blocks the main thread while the page tables are copied.

```
INFO stats        # latest_fork_usec, total_forks
INFO persistence  # current_cow_peak, rdb_last_cow_size, aof_last_cow_size, current_fork_perc
```

- `latest_fork_usec` grows with RSS. The latency docs measured 10 ms per GB on "Linux VM on EC2, new instance types (Xen)", 239 ms per GB on old EC2 instance types (Xen) and 424 ms per GB on Linode (Xen); physical machines and VMware were 9–13 ms per GB. The same page recommends modern HVM-based EC2 instances. Use such instances, keep each instance's dataset moderate (shard instead of growing one node), and avoid forks during peaks (schedule `save` points, stagger `BACKUP START` across nodes).
- Transparent huge pages turn copy-on-write into copying huge pages and cause large latency and memory spikes after fork. Disable THP on the host; Redis also defaults `disable-thp yes`.
- Copy-on-write memory adds to RSS; size the host for it (see [memory](memory-and-configuration.md#size-maxmemory)).

## Swapping

```
redis-cli INFO server | grep process_id
grep -E '^(Swap|Size)' /proc/<pid>/smaps
vmstat 1          # si/so columns non-zero = swapping now
```

Anything beyond sporadic 4 kB `Swap:` entries means Redis pages are on disk. Reduce memory pressure: lower `maxmemory`, move other processes off the host, add RAM.

## Disk and AOF

- `appendfsync everysec`: fsync runs in a background thread. While an fsync is in progress, Redis delays the next `write(2)` to the AOF for up to two seconds; if the fsync takes longer, it performs the write anyway and that write can block the main thread. Slow or shared disks show up here. `aof_delayed_fsync` in `INFO persistence` counts it.
- `no-appendfsync-on-rewrite yes` skips fsync during rewrites to lower disk pressure, trading durability during the rewrite window.
- `appendfsync always` makes every write wait for the disk.
- Trace slow fsync: `sudo strace -f -p $(pidof redis-server) -T -e trace=fdatasync,write`.

## Expiration and Deletion

- Many keys expiring in the same second make the active expire cycle run longer; watch `expired_time_cap_reached_count`, `expire_cycle_cpu_milliseconds`, and the `expire-cycle` latency event. Add random jitter to bulk TTLs.
- Freeing a large key on expiry or `DEL` happens on the main thread unless `lazyfree-lazy-expire` / `lazyfree-lazy-user-del` are `yes` (both `no` by default). Turn them on for workloads with large collections.

## Big and Hot Keys

```
redis-cli --bigkeys -i 0.01        # sleep 0.01 s per 100 SCAN calls to reduce load
redis-cli --memkeys
redis-cli --keystats               # 7.4+
INFO keysizes                      # 8.0+: histograms, no scan needed
HOTKEYS START METRICS 2 CPU NET COUNT 10   # 8.6+, one session at a time
HOTKEYS GET
HOTKEYS STOP
HOTKEYS RESET
redis-cli --hotkeys                # only with an LFU maxmemory-policy
CLUSTER SLOT-STATS ...             # 8.2+: per-slot key count, CPU, network
```

Run scans against a replica when possible.

## Clients and Network

- Connection churn: rate of `total_connections_received`; use pooling. `max-new-connections-per-cycle` (7.4+, default 10) and `max-new-tls-connections-per-cycle` (default 1) cap accepts per event-loop cycle during reconnect storms.
- Pipelining: the 8.12 image reports `avg_pipeline_length` in `INFO stats` and `avg-pipeline-len-*` per client. Batching with pipelines or `MGET`/`MSET` cuts round trips.
- Output buffers: `CLIENT LIST` `omem`; `client_output_buffer_limit_disconnections`.
- Client-side measurement: `redis-cli --latency`, `--latency-history`, `--latency-dist`; `--latency-percentiles` (8.10+).

## What to Monitor

| Metric (INFO section) | Why | Alert idea |
|---|---|---|
| `used_memory`, `maxmemory` (memory) | Headroom | > 90% of `maxmemory` |
| `evicted_keys`, hit ratio (stats) | Cache effectiveness | Sudden rise in evictions |
| `mem_fragmentation_bytes`, `allocator_frag_bytes` (memory) | Wasted RSS | Sustained GB-level fragmentation |
| `connected_clients`, `blocked_clients` (clients), `rejected_connections` (stats) | Saturation | `rejected_connections` > 0 |
| `instantaneous_ops_per_sec`, `INFO commandstats` | Load and command mix | Deviation from baseline |
| `INFO latencystats` p99 per command | Latency target | p99 above target |
| `rdb_last_bgsave_status`, `aof_last_write_status`, `aof_last_bgrewrite_status` (persistence) | Durability broken | Not `ok` |
| `rdb_last_save_time` (persistence) | Stale backups | Older than the recovery point objective |
| `latest_fork_usec` (stats) | Fork stalls | Above your latency budget |
| `master_link_status`, `master_last_io_seconds_ago`, replica `lag` (replication) | Replica health | Link down; lag of several seconds |
| `sync_full` (stats) | Backlog too small | Increasing |
| `cluster_state` (`CLUSTER INFO`) | Cluster health | Not `ok` |
| `acl_access_denied_*` (stats) | Misconfiguration or attack | Spikes |
| `errorstat_*` (errorstats) | OOM, NOPERM, CROSSSLOT rates | Any OOM |
| `expired_time_cap_reached_count` (stats) | Expiry backlog | Rising |

Collect `INFO` sections at a fixed interval; `SLOWLOG` and `LATENCY` must be pulled, they do not push.

Sources: https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency/, https://redis.io/docs/latest/commands/slowlog-get/, https://redis.io/docs/latest/commands/info/, https://redis.io/docs/latest/commands/hotkeys/, https://redis.io/docs/latest/develop/tools/cli/, https://redis.io/docs/latest/operate/oss_and_stack/management/admin/, release notes linked from [versions](versions/index.md) (checked 2026-11-27); images `redis:7.2` to `redis:8.12`, statement runs and `CONFIG GET` output (2026-11-27).
