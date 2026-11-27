# Valkey Latency and Monitoring

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)).

`INFO` sections, `SLOWLOG`, the `LATENCY` monitor and `LATENCY DOCTOR`, `INFO commandstats`/`latencystats`/`errorstats`, `--bigkeys`/`--memkeys`, intrinsic latency tests and fork cost analysis work as in Redis OSS 7.2. Read [../redis/latency-and-monitoring.md](../redis/latency-and-monitoring.md) for the diagnosis method.

## Default thresholds (all series unless noted)

| Setting | Default | Note |
| --- | --- | --- |
| `slowlog-log-slower-than` | 10000 µs | |
| `slowlog-max-len` | 128 | |
| `latency-monitor-threshold` | 0 (off) | `LATENCY DOCTOR` then only reports that monitoring is disabled |
| `latency-tracking` | `yes` | per-command percentiles in `INFO latencystats` (`p50`, `p99`, `p99.9`) |
| `commandlog-execution-slower-than` | 10000 µs | 8.1+ |
| `commandlog-request-larger-than`, `commandlog-reply-larger-than` | 1048576 bytes | 8.1+; accept units such as `10mb` from 9.2 |

## COMMANDLOG (8.1+)

One log for three problems: slow execution, large requests, large replies.

```
COMMANDLOG GET 10 slow
COMMANDLOG GET 10 large-request
COMMANDLOG GET 10 large-reply
COMMANDLOG LEN slow
COMMANDLOG RESET large-reply
```

Use `large-reply` to find `HGETALL`, `LRANGE 0 -1` or `SMEMBERS` on big keys that saturate the network or client output buffers without being slow on the server, and `large-request` for oversized `MSET`/`HSET` batches. `SLOWLOG` remains and corresponds to the `slow` type. From 9.2 a whole `MULTI/EXEC` is logged when its total time crosses the threshold. On ElastiCache Serverless neither `COMMANDLOG` nor `SLOWLOG` is available.

## Hot keys (9.2)

```
CONFIG SET hotkeys-top-k 20
CONFIG SET hotkeys-sampling-percentage 1     # 1..100
HOTKEYS GET
HOTKEYS RESET
CONFIG SET hotkeys-top-k 0                    # off
```

`HOTKEYS GET` reports the last completed window (`hotkeys-window-seconds`, default 1), one entry per key with `key`, `db` and `qps`; at the default 1% sampling a short test can return nothing. Raise sampling only for short investigations on busy servers. On older versions use `valkey-cli --hotkeys` (needs an LFU `maxmemory-policy`) or short `MONITOR` samples, which cost much more. `valkey-cli --hotkeys-count` (9.0+) sets how many keys it prints.

## Per-slot metrics (8.0+)

```
CONFIG SET cluster-slot-stats-enabled yes
CLUSTER SLOT-STATS ORDERBY cpu-usec LIMIT 10
CLUSTER SLOT-STATS SLOTSRANGE 0 100
```

Use it to find the slots (and through `CLUSTER COUNTKEYSINSLOT`/`CLUSTER GETKEYSINSLOT`, the keys) behind an unbalanced shard before resharding. `key-count` needs no config; `cpu-usec`, `network-bytes-in` and `network-bytes-out` appear in the output only after `CONFIG SET cluster-slot-stats-enabled yes` (default `no`). These are the `ORDERBY` names; others fail with `ERR Unrecognized sort metric for ORDERBY.` (9.0 and 9.2 images).

## INFO fields added by Valkey

| Field (section) | Series | Use |
| --- | --- | --- |
| `server_name`, `valkey_version` (server) | 7.2 | version inventory |
| `valkey_release_stage` (server) | 8.1 | catch release-candidate builds |
| `io_threads_active` (server), `io_threaded_reads_processed`, `io_threaded_writes_processed` (stats) | 8.0 (I/O threading rewrite) | I/O thread effect |
| `mem_overhead_db_hashtable_rehashing` (memory) | 8.0 | rehash memory spikes |
| `client_query_buffer_limit_disconnections`, `client_output_buffer_limit_disconnections` (stats) | 8.0 | clients dropped by buffer limits |
| `pubsub_clients`, `watching_clients`, `total_watched_keys` (clients) | 8.0 | |
| `paused_reason`, `paused_actions`, `paused_timeout_milliseconds` (clients) | 8.1 | why writes are paused (failover, `CLIENT PAUSE`) |
| `eventloop_cycles`, `eventloop_duration_sum`, `eventloop_duration_cmd_sum`, `instantaneous_eventloop_duration_usec` (stats) | 7.2 (all six images); 9.2 adds `eventloop_priority_cycles`, `eventloop_priority_duration_sum`, `eventloop_priority_duration_cmd_sum` | main-loop saturation |
| `used_active_time_main_thread` (cpu) | 9.1 | true main-thread busy time; I/O thread counterparts also added |
| `# Scripting Engines`, TLS certificate expiry fields | 9.1 | |
| `expired_fields` (stats) | 9.0 (absent on 8.1) | hash field expiration rate |
| `connected_priority_clients` (clients), `rejected_priority_connections`, `acl_access_denied_db` (stats) | 9.2 | admin reservation, database ACL |
| `forkless_estimated_seconds_remaining`, `slot_migration_fork_in_progress` (persistence) | seen in the 9.2 image | forkless saves, slot migration |
| `last_successful_sync_duration_ms` (replication) | 9.2 | full-sync duration |

`INFO keysizes` (a Redis 8 section) returns nothing on Valkey (empty output in all six images).

## Latency triage order

1. `INFO stats` `instantaneous_ops_per_sec` and `instantaneous_eventloop_duration_usec`; `INFO cpu` main-thread time. Main thread saturated → expensive commands or a case for I/O threads.
2. `COMMANDLOG GET 20 slow` (or `SLOWLOG GET 20`) and `INFO commandstats` sorted by `usec_per_call` → expensive commands.
3. `COMMANDLOG GET 20 large-reply` → big keys and full-collection reads.
4. `CONFIG SET latency-monitor-threshold 100`, wait, then `LATENCY LATEST` and `LATENCY DOCTOR` → fork, AOF fsync, expire cycles, eviction (`LATENCY LATEST` includes sum and count from 8.1).
5. `INFO persistence` `current_cow_size` and `INFO stats` `latest_fork_usec`; on 9.2 consider forkless saves.
6. `INFO stats` `evicted_keys`, `total_eviction_exceeded_time`; `INFO memory` `lazyfree_pending_objects` → memory pressure.
7. `CLUSTER SLOT-STATS` and `HOTKEYS GET` → imbalance.

Reset counters before a measurement window with `CONFIG RESETSTAT` (from 9.2 it also resets I/O prefetch and ACL denial counters).

## Logs

- `log-format legacy|logfmt|json` (logfmt 8.1, json 9.1) and `log-timestamp-format legacy|iso8601|milliseconds` (8.1) make logs machine-parsable; switch only after log pipelines are updated.
- With `hide-user-data-from-log yes` (default since 8.0), crash reports omit keys and values.
