# Valkey Memory and Configuration

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)).

`maxmemory`, eviction policies and sampling, `MEMORY STATS`/`MEMORY DOCTOR`, fragmentation and active defrag, Transparent Huge Pages, `CONFIG SET`/`CONFIG REWRITE` and protected configs behave as in Redis OSS 7.2. Read [../redis/memory-and-configuration.md](../redis/memory-and-configuration.md) for them.

## Defaults that differ between series (official images, 2026-11-27)

| Setting | 7.2 | 8.0 | 8.1 | 9.0 | 9.1 | 9.2 |
| --- | --- | --- | --- | --- | --- | --- |
| `lazyfree-lazy-user-del` | no | yes | yes | yes | yes | yes |
| `lazyfree-lazy-eviction` | no | yes | yes | yes | yes | yes |
| `lazyfree-lazy-expire`, `lazyfree-lazy-server-del`, `lazyfree-lazy-user-flush`, `replica-lazy-flush` | no | yes | yes | yes | yes | yes |
| `repl-backlog-size` | 1 MB | 10 MB | 10 MB | 10 MB | 10 MB | 10 MB |
| `hide-user-data-from-log` | absent | yes | yes | yes | yes | yes |
| `io-threads` | 1 | 1 | 1 | 1 | 1 | 1 |
| `maxmemory` / `maxmemory-policy` | 0 / noeviction | same | same | same | same | same |
| `maxclients` | 10000 | 10000 | 10000 | 10000 | 10000 | 10000 |
| `MODULE LIST` | empty | empty | empty | empty | `lua` | `lua` |

The 9.2 image also shows `lazyfree-lazy-expire yes`, `lazyfree-lazy-server-del yes`, `lazyfree-lazy-user-flush yes`, `replica-lazy-flush yes`, `jemalloc-bg-thread yes`, `disable-thp yes`, `activedefrag no`, `maxmemory-samples 5`, `maxmemory-eviction-tenacity 10`, `maxmemory-clients 0`, `client-query-buffer-limit 1gb`, `proto-max-bulk-len 512mb`, `hz 10`.

Container note: the official image runs without a config file and reports `protected-mode no` and `bind * -::*`. The shipped `valkey.conf` sets `bind 127.0.0.1 -::1` and `protected-mode yes`. Never deploy the image defaults on a reachable network without `requirepass` or ACL users; see [security.md](security.md).

## Lazy freeing (8.0 default change)

Since 8.0, `DEL`, eviction, expiration, server-side deletes (`RENAME` overwrite, `SET` overwrite) and replica flushes free memory in a background thread.

- Effect: deleting a large hash, set or sorted set no longer stalls the main thread. `used_memory` drops later; `INFO memory` `lazyfree_pending_objects` shows pending work and `lazyfreed_objects` the total.
- When to turn off: a job that deletes and immediately re-fills under a tight `maxmemory` can hit OOM before the background thread catches up. Set `lazyfree-lazy-user-del no` for that instance, or throttle the job.
- `FLUSHALL`/`FLUSHDB` without `SYNC`/`ASYNC` follow `lazyfree-lazy-user-flush` (`yes` from 8.0, `no` on 7.2).

## I/O threads

Valkey 8.0 rewrote I/O threading: I/O threads read and parse requests, write replies, poll for events and free objects; the main thread still executes every command. Settings:

| Item | Detail |
| --- | --- |
| `io-threads N` | total threads including the main thread; `1` disables (default) |
| Maximum | 256 (8.1+) |
| Runtime change | `CONFIG SET io-threads N` from 9.0; earlier series need a restart |
| `io-threads-do-reads` | deprecated in 8.1, no effect |
| Prefetching | `prefetch-batch-max-size 16` (9.2 default); 9.2 extends prefetch to hash/set/zset member lookups |

Decision rule: enable when `INFO cpu` shows the main thread near one full core (`used_cpu_sys_main_thread` + `used_cpu_user_main_thread` rising by about 1 second per second, or 9.1+ `used_active_time_main_thread`) and the workload is many small commands or many connections. The shipped `valkey.conf` suggests 2 or 3 I/O threads on 4 cores and 6 on 8 cores, and says to enable it only when there is a real performance problem. Idle I/O threads can show high CPU while busy-polling; judge by throughput and latency, not host CPU.

Verify: `INFO server` `io_threads_active:1` under load; `INFO stats` `io_threaded_reads_processed`, `io_threaded_writes_processed` increasing; compare p99 latency before and after with `valkey-benchmark --threads` matching the server threads. Rollback: `CONFIG SET io-threads 1` (9.0+) or restart with the old value.

## Memory efficiency per series

| Series | Change | DBA consequence |
| --- | --- | --- |
| 8.0 | key embedded in dict entry | fewer bytes per key |
| 8.1 | new hashtable for keyspace, hashes, sets, sorted sets; embedded hash values | lower overhead for many small keys; re-baseline capacity |
| 9.1 | strings up to 128 bytes embedded (was 64); zset element embedded in skiplist | smaller small strings |
| 9.2 | sorted sets on B+ tree; small hashes with field TTLs stay listpack; shared WATCH/pubsub pattern objects | smaller large zsets and TTL'd small hashes |

Single-sample evidence from the images (`HSET h f1 a f2 b`, then `MEMORY USAGE h`): 72 bytes on 7.2, 64 on 8.0, 48 on 8.1. Measure your own keys: run `MEMORY USAGE <key> SAMPLES 0` on the same data loaded into each version; `INFO memory` `used_memory_dataset` gives the total.

## Script and client memory limits

- `maxmemory-scripts` (9.2): limit memory used by cached `EVAL` scripts, absolute (`100mb`) or percent of `maxmemory` (`5%`). Default 0 (off). The count-based limit still applies: at most 500 `EVAL` scripts stay cached, oldest evicted first (`LRU_LIST_LENGTH 500` in `src/eval.c`, 9.2 branch). A non-zero value below 128 KB is raised to 128 KB. `SCRIPT LOAD` scripts are not evicted by this limit but now fail with OOM under `maxmemory`.
- `maxmemory-clients` (Redis 7 feature, default 0): cap total client memory and evict the largest clients. A use-after-free in client eviction was fixed in the 2026-11-18 patches (CVE-2026-130822): if you use `maxmemory-clients`, run 7.2.16, 8.0.13, 8.1.12, 9.0.8, 9.1.4 or 9.2.x.
- 9.2 counts watched keys and pubsub channel names in client memory (`CLIENT INFO` `tot-mem`), so `maxmemory-clients` may start evicting clients that were under the limit before.

## Connection limits (9.2)

`maxclients` stays the hard ceiling. To keep operators and monitoring able to connect when applications exhaust it:

```
priority-subnets "10.20.0.0/24"
maxclients-reserved 64
```

Normal clients are capped at `maxclients - maxclients-reserved`; clients from the subnets can use the full `maxclients`. `INFO clients` `connected_priority_clients` and `INFO stats` `rejected_priority_connections` show the effect. Raising the reservation at runtime does not disconnect existing clients; new normal connections are rejected until enough disconnect.

## Configuration workflow

- `CONFIG INFO <pattern>` (9.2) returns type, flags, allowed values and ranges; use it before `CONFIG SET` on an unfamiliar parameter.
- `CONFIG GET *` output is sorted from 9.0, which makes diffs between nodes straightforward: `valkey-cli -h a CONFIG GET '*' > a.txt; valkey-cli -h b CONFIG GET '*' > b.txt; diff a.txt b.txt`.
- Immutable at runtime (set in the config file, restart needed): `forkless-infrastructure-enabled`, `hash-seed`, `cluster-databases`, `databases`, and protected configs such as `dir` and `dbfilename` unless `enable-protected-configs` allows them.
- `CONFIG REWRITE` quotes the `replicaof` host and preserves module load order from 9.2; on older versions inspect the rewritten file.
- Settings deprecated or removed: `io-threads-do-reads` and `dynamic-hz` (8.1), `sanitize-dump-payload` (no-op since the mid-2026 patches). `extended-redis-compatibility` (8.0+) is temporary.
