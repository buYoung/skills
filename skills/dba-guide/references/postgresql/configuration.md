# Configuration: Memory, WAL, Durability, Connections

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)). Managed-service parameter handling is in [managed-services.md](managed-services.md).

## How settings take effect

```sql
SELECT name, setting, unit, context, source, sourcefile, pending_restart
FROM pg_settings WHERE name IN ('shared_buffers','work_mem','max_connections','wal_level');
```

| `context` | Change takes effect | How |
| --- | --- | --- |
| `postmaster` | after restart | edit `postgresql.conf` or `ALTER SYSTEM`, then restart |
| `sighup` | after reload | `SELECT pg_reload_conf();` or `pg_ctl reload` |
| `superuser` / `user` | per session, role, or database | `SET`, `ALTER ROLE ... SET`, `ALTER DATABASE ... SET` |
| `internal` | never (compile or initdb time) | — |

- `ALTER SYSTEM` writes `postgresql.auto.conf`, which overrides `postgresql.conf`. On 17+, `allow_alter_system = off` disables it where config management owns the files.
- After a reload, check `pending_restart = true` rows and errors in `pg_file_settings`: `SELECT name, setting, error FROM pg_file_settings WHERE error IS NOT NULL;`
- `SHOW config_file; SHOW data_directory; SHOW hba_file;` locate the files.
- An unrecognized parameter in the config file (for example `io_workers` on 19, `old_snapshot_threshold` on 17+) prevents the server from starting. Remove obsolete names before an upgrade.

## Shipped defaults (official images, 2026-11-27)

| Setting | 14 | 17 | 18 | 19 | Notes |
| --- | --- | --- | --- | --- | --- |
| `shared_buffers` | 128MB | 128MB | 128MB | 128MB | initdb picked 128MB in the container |
| `work_mem` | 4MB | 4MB | 4MB | 4MB | per sort/hash node per process |
| `maintenance_work_mem` | 64MB | 64MB | 64MB | 64MB | vacuum, index builds |
| `effective_cache_size` | 4GB | 4GB | 4GB | 4GB | planner hint only |
| `max_connections` | 100 | 100 | 100 | 100 | |
| `wal_level` | replica | replica | replica | replica | 19 adds read-only `effective_wal_level` |
| `max_wal_size` / `min_wal_size` | 1GB | 1GB | 1GB / 80MB | 1GB / 80MB | |
| `checkpoint_timeout` | 5min | 5min | 5min | 5min | |
| `synchronous_commit` | on | on | on | on | |
| `jit` | on | on | on | off | |
| `default_toast_compression` | pglz | pglz | pglz | lz4 | |
| `data_checksums` (initdb) | off | off | on | on | |
| `io_method` | — | — | worker | worker | 18+ |
| `huge_pages` | try | try | try | try | `huge_pages_status` (17+) shows whether they were obtained; container: `off` |
| `max_locks_per_transaction` | 64 | 64 | 64 | 128 | lock table sizing changed in 19; double explicit values from older releases (19.0 notes) |
| `password_encryption` | scram-sha-256 | scram-sha-256 | scram-sha-256 | scram-sha-256 | |

The official image sets `listen_addresses = '*'` and appends a `host all all all scram-sha-256` rule; a package or source install defaults to `listen_addresses = 'localhost'` (container `boot_val`).

## Memory

Decision rules (guidelines, not from the documentation; measure against your workload):

- `shared_buffers`: start at about 25% of RAM on a dedicated Linux server; going much higher rarely helps because the OS cache also caches data. Restart required. Check hit rates in `pg_stat_database` (`blks_hit` vs `blks_read`) and `pg_stat_io` (16+).
- Huge pages: with `shared_buffers` of several GB, configure Linux huge pages and set `huge_pages = on` so startup fails rather than silently falling back. Size them with `postgres -D $PGDATA -C shared_memory_size_in_huge_pages` (15+) before starting.
- `work_mem`: total use can reach `work_mem * nodes per query * parallel workers * active connections` (hash nodes up to `hash_mem_multiplier`, default 2 since 15). Keep the global value modest and raise it per role or session for reporting queries. Watch `temp_files`/`temp_bytes` in `pg_stat_database` and `log_temp_files` to find spills.
- `maintenance_work_mem`: 1 to 2 GB speeds index builds and vacuum on large tables. Each autovacuum worker can use `autovacuum_work_mem` (default -1 = `maintenance_work_mem`); from 17 vacuum can actually use more than 1GB.
- Leave memory for the OS cache and per-connection overhead; a few hundred idle connections cost real memory.

## WAL and checkpoints

- `max_wal_size` sets when a checkpoint is forced by WAL volume. If `pg_stat_checkpointer.num_requested` (17+; `checkpoints_req` in `pg_stat_bgwriter` before 17) is large relative to `num_timed`, checkpoints are driven by WAL volume: raise `max_wal_size` (for example to 8 to 32GB on write-heavy systems) so checkpoints follow `checkpoint_timeout`. The log line `checkpoints are occurring too frequently` (`checkpoint_warning`, 30s) says the same.
- Longer intervals reduce full-page writes after each checkpoint (less WAL) but lengthen crash recovery.
- `checkpoint_completion_target = 0.9` (default since 14) spreads writes; leave it.
- `wal_compression` (`off` default) reduces full-page-image WAL at CPU cost; choose `lz4` or `zstd` (15+).
- `full_page_writes = on` must stay on unless the storage guarantees atomic 8kB writes.
- `log_checkpoints = on` (default since 15) reports write/sync times and distance; long `sync` times point at storage.

## Durability

| Setting | Safe value | Turning it off |
| --- | --- | --- |
| `fsync` | on | data corruption after OS crash or power loss; never off in production |
| `synchronous_commit` | on | `off` loses the last few hundred ms of commits on crash but no corruption; acceptable per transaction for low-value writes |
| `full_page_writes` | on | torn pages after crash |
| `wal_sync_method` | platform default (`fdatasync` on Linux, container) | test with `pg_test_fsync` before changing |

`commit_delay` and `commit_siblings` can group commits under very high concurrency; rarely needed.

## Connections

- Each connection is a process. Hundreds of active connections cause contention well before `max_connections` is reached. Put a connection pooler in front for many clients (external tool; transaction pooling breaks session state such as session-level advisory locks, `SET`, and temporary tables).
- `superuser_reserved_connections` (default 3) and `reserved_connections` with `pg_use_reserved_connections` (16+) keep admin slots free.
- Timeouts to set for application roles: `idle_in_transaction_session_timeout`, `statement_timeout`, 14+ `idle_session_timeout`, 17+ `transaction_timeout`. All default to 0 (off). Set them with `ALTER ROLE app SET ...`.
- `tcp_keepalives_idle` and `client_connection_check_interval` (14+) detect dead clients so their queries and locks end.

## Asynchronous I/O (18+)

- `io_method = worker` (default) uses background I/O workers; `sync` reproduces pre-18 behavior; `io_uring` is available on Linux builds compiled with liburing; the official 18.7 and 19.0 images are (`io_method` accepts `sync`, `worker`, `io_uring`).
- 18: `io_workers` (default 3) fixes the worker count. 19: workers scale between `io_min_workers` (2) and `io_max_workers` (8); `io_workers` no longer exists.
- `effective_io_concurrency` and `maintenance_io_concurrency` default to 16 on 18+.
- Watch `pg_aios` (18+) and `pg_stat_io` for I/O behavior; on 19 `EXPLAIN (ANALYZE, IO)`.

## Parallel query

Defaults: `max_worker_processes = 8`, `max_parallel_workers = 8`, `max_parallel_workers_per_gather = 2`, `max_parallel_maintenance_workers = 2`. Raise `max_parallel_workers_per_gather` for analytical workloads on many cores; keep OLTP at the default. `max_worker_processes` needs a restart and also caps logical replication workers, autovacuum parallel workers (19), and extensions' background workers.

## Verify a configuration change

1. Record the old value (`SELECT name, setting, source FROM pg_settings WHERE name = '...';`).
2. Apply (`ALTER SYSTEM SET ...;` then reload or restart as `context` requires).
3. Confirm the running value with `SHOW` and that `pending_restart` is false.
4. Compare the target metric (checkpoint counts, temp bytes, latency in `pg_stat_statements`) over a comparable period.
5. Roll back with `ALTER SYSTEM RESET name;` plus reload or restart.
