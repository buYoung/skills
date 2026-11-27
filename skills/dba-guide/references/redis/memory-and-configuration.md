# Redis Memory and Configuration

Checked: 2026-11-27 (sources at the end).

## Size maxmemory

`maxmemory 0` (default on 64-bit) means no limit: Redis grows until the OS kills it. Set an explicit limit on every production instance.

Budget the host's RAM:

| Consumer | How to measure | Counted against `maxmemory`? |
|---|---|---|
| Dataset | `used_memory_dataset` | Yes |
| Per-key and structure overhead | `used_memory_overhead` | Yes |
| Client buffers | `mem_clients_normal`, `CLIENT LIST` `tot-mem` | Yes |
| Replication and AOF buffers | `mem_not_counted_for_evict`, `mem_total_replication_buffers`, `mem_aof_buffer` | No |
| Copy-on-write during `BGSAVE`/rewrite/full sync | `current_cow_peak`, `rdb_last_cow_size` | No (RSS) |
| Fragmentation and allocator overhead | `allocator_frag_bytes`, `allocator_rss_bytes` | No (RSS) |
| Lua/Functions VM | `used_memory_vm_total` | Lua VM counted in used memory from 7.4 |

Rules from the admin guide: with 10 GB free, set `maxmemory` to 8 to 9 GB; a write-heavy instance can need up to twice its normal memory while saving or rewriting, proportional to pages modified during the save. Replication causes RDB saves on the primary even with persistence off, unless replication is diskless (default since 7.0).

## Choose an Eviction Policy

`maxmemory-policy` default is `noeviction`: writes that need memory fail with `OOM command not allowed when used memory > 'maxmemory'.` (8.12.0, counted as `errorstat_OOM:count=1` in `INFO errorstats`), reads keep working, and replicas apply only what the primary sends.

| Policy | Candidates | Choose when |
|---|---|---|
| `noeviction` | none | Data store; the application must handle write errors |
| `allkeys-lru` | all keys | Cache with a hot subset; the docs' default suggestion |
| `allkeys-lfu` | all keys | Cache where frequency predicts reuse better than recency |
| `allkeys-lrm` ([8.6](versions/8.6.md)+) | all keys, by last modification | Keep recently written data; evict what has not changed, however often read |
| `allkeys-random` | all keys | Uniform access |
| `volatile-lru` / `volatile-lfu` / `volatile-lrm` / `volatile-random` | keys with TTL | Mixed cache and persistent keys in one instance (better: two instances) |
| `volatile-ttl` | keys with TTL, shortest remaining first | Application assigns TTL by value |

- `volatile-*` with no volatile keys behaves like `noeviction`.
- Sampling: `maxmemory-samples 5`; raise to 10 for closer-to-true LRU at more CPU. `maxmemory-eviction-tenacity 10` is the default on the 8.12 image.
- LFU tuning: `lfu-log-factor 10`, `lfu-decay-time 1` (minutes).
- `BLESS SET <key> NO-EVICT` ([8.12](versions/8.12.md)) excludes keys from eviction under any policy; with enough blessed keys, writes succeed until `used_memory` would pass 1.25 x `maxmemory`, then fail.
- `lazyfree-lazy-eviction yes` frees evicted values in a background thread (default `no`).
- A single command that adds a large value can overshoot `maxmemory` temporarily; eviction runs when the next command needs memory.

Evidence:

```
INFO stats     # evicted_keys, keyspace_hits, keyspace_misses, total_eviction_exceeded_time,
               # current_eviction_exceeded_time, evicted_clients, blessed_keys (8.12)
INFO memory    # used_memory, maxmemory, maxmemory_policy, mem_not_counted_for_evict
INFO commandstats   # cmdstat_<cmd>: ... rejected_calls=N,failed_calls=N
INFO errorstats     # errorstat_OOM:count=N
```

Hit ratio = `keyspace_hits / (keyspace_hits + keyspace_misses)`. Low hit ratio with high `evicted_keys` means memory is too small or the policy evicts the wrong keys. Low hit ratio with low evictions and high `expired_keys` means TTLs are too short.

Change and verify:

```
CONFIG SET maxmemory 8gb maxmemory-policy allkeys-lru   # several pairs in one call, 7.0+
CONFIG REWRITE                                         # persist, if started with a config file
CONFIG GET maxmemory*
```

Lowering `maxmemory` below `used_memory` on a cache triggers mass eviction; on `noeviction` all writes start failing. Lower it in steps and watch `evicted_keys` and latency.

## Client Memory and Limits

Defaults on the 8.12 image:

| Parameter | Default |
|---|---|
| `maxclients` | 10000 |
| `maxmemory-clients` | 0 (no total limit) |
| `client-output-buffer-limit` | `normal 0 0 0`, replica `256mb 64mb 60`, `pubsub 32mb 8mb 60` |
| `client-query-buffer-limit` | 1 GB |
| `proto-max-bulk-len` | 512 MB |
| `timeout` | 0 (idle clients never closed) |
| `tcp-keepalive` | 300 |

- `maxmemory-clients` (7.0+) drops clients when total client memory exceeds the limit (`evicted_clients`). Exempt admin connections with `CLIENT NO-EVICT on`. From 8.12, client memory also counts watched keys and Pub/Sub channel names.
- Pub/Sub subscribers that fall behind are disconnected at the pubsub output limit; `client_output_buffer_limit_disconnections` (7.4+) counts such disconnects.
- Find heavy clients: `CLIENT LIST`, sort by `tot-mem`, `omem`, `qbuf`; 8.2+ adds `tot-net-in`, `tot-net-out`, `tot-cmds`.

## Fragmentation

Read `INFO memory`:

- `mem_fragmentation_ratio` = `used_memory_rss` / `used_memory`. It includes allocator overhead, code, and shared libraries, so it is meaningless for small instances: the empty 8.12 container showed 11.90 at 2 MB used. Look at `mem_fragmentation_bytes`; the docs say a high ratio with a few MB of difference is not an issue.
- `allocator_frag_ratio` = `allocator_active` / `allocator_allocated` is the true external fragmentation metric.
- `allocator_rss_ratio`: pages the allocator holds and will probably release to the OS.
- `used_memory` > `used_memory_rss`: part of Redis is swapped out; expect latency.
- `allocator_muzzy` (7.4+): freed memory still in RSS until the OS reclaims it.

Act:

| Observation | Action |
|---|---|
| `allocator_frag_bytes` in the GB range after mass deletes or value-size changes (threshold is a rule of thumb, not a documented value) | Enable active defragmentation: `CONFIG SET activedefrag yes` |
| High `allocator_rss_bytes` | `MEMORY PURGE` asks the allocator to release pages |
| RSS stays far above the working set after a one-off spike | Fail over to a freshly started replica (last resort) |

Active defrag defaults (8.12 image): `activedefrag no`, `active-defrag-ignore-bytes 100mb`, `active-defrag-threshold-lower 10` (%), `active-defrag-threshold-upper 100`, `active-defrag-cycle-min 1`, `active-defrag-cycle-max 25` (% CPU). It costs main-thread CPU; watch latency while it runs (`active_defrag_running`, `active_defrag_hits`, `total_active_defrag_time`). It works with jemalloc (`mem_allocator:jemalloc-5.3.0` on the 7.2 and later images; `jemalloc-5.1.0` on 6.2.24).

`MEMORY DOCTOR` and `MEMORY STATS` give a summary; `MEMORY DOCTOR` declines to analyze an almost empty instance (observed).

## Operating System Settings

- `vm.overcommit_memory = 1`; without it, `BGSAVE` fork can fail.
- Disable transparent huge pages (`echo never > /sys/kernel/mm/transparent_hugepage/enabled`); with THP, copy-on-write after fork copies huge pages and causes latency and memory spikes. Redis also has `disable-thp yes` (default; immutable since 7.0) for its own process.
- Swap: the admin guide recommends swap sized like RAM so an over-limit instance slows down instead of being OOM-killed; the latency guide shows swapped pages cause large latency. Keep swap as a safety net, alert on any swap use (`/proc/<pid>/smaps` `Swap:` lines, `vmstat` `si`/`so`), and size `maxmemory` so it is never needed.
- Persistence on network volumes (the admin guide names EBS) can see latency spikes; keep AOF on fast storage when `appendfsync everysec` matters.

## Threads

- `io-threads 1` (default). Since [8.0](versions/8.0.md) I/O threads handle reads and writes; `io-threads-do-reads` is ignored. Raise it only when the main thread is CPU-bound on network I/O with many clients (check `INFO threads`, `io_threaded_reads_processed`). Command execution stays on the main thread.
- AOF fsync (`everysec`) and lazy freeing run in background threads; `lazyfree_pending_objects` shows the lazy-free backlog.

## Configuration Management

- `CONFIG GET *` lists everything; `CONFIG SET` changes most parameters at runtime; `CONFIG REWRITE` writes running values back to the config file. The official image started without a config file (`config_file:` empty), so `CONFIG REWRITE` has nowhere to write there and returns `ERR The server is running without a config file` (8.12.0).
- Some parameters can only be set at startup, for example `disable-thp`, `backupdirname`, `preload-file`, `json-auto-create-deep-paths`.
- `enable-protected-configs no`, `enable-debug-command no`, `enable-module-command no` (defaults since 7.0) block runtime changes to the protected configs (`dir` and `dbfilename`; `PROTECTED_CONFIG` in `src/config.c`, 7.0.0 and 8.12.0) and the `DEBUG` and `MODULE` commands. Each also accepts `local` to allow only loopback and Unix-socket clients. Keep them off in production.
- Record a baseline: `redis-cli CONFIG GET '*' > config-$(date +%F).txt` before changes, and diff after.

Other defaults on the 8.12.0 image: `databases 16`, `hz 10` with `dynamic-hz yes`, `tcp-backlog 511`, `shutdown-timeout 10`, `lookahead 16` (8.4+), `jemalloc-bg-thread yes`, `latency-tracking yes`, `latency-tracking-info-percentiles 50 99 99.9`.

Sources: https://redis.io/docs/latest/operate/oss_and_stack/management/admin/, https://redis.io/docs/latest/develop/reference/eviction/, https://redis.io/docs/latest/commands/info/, https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency/, https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/, https://raw.githubusercontent.com/redis/redis/7.0.0/00-RELEASENOTES, https://raw.githubusercontent.com/redis/redis/7.4.0/00-RELEASENOTES, https://redis.io/docs/latest/develop/whats-new/8-12/ (checked 2026-11-27); image `redis:8.12` `CONFIG GET`, statement runs, and `INFO` output (2026-11-27).
