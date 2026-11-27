# MariaDB Configuration

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)). Applies to MariaDB 10.6-13.1. Defaults below come from the official images (`mariadb:10.6` to `mariadb:13.0`) unless noted; the images add some settings through packaging config (for example `expire_logs_days=10`, `skip_name_resolve=ON`, `character_set_server=utf8mb4`, and in the 12.3.3 and 13.0.2 images `binlog_format=ROW` and `innodb_autoinc_lock_mode=2`; see [12.3](versions/12.3.md#changed-defaults) for where those two come from).

## See What Is in Effect

```sql
SELECT VARIABLE_NAME, GLOBAL_VALUE, DEFAULT_VALUE, GLOBAL_VALUE_ORIGIN
FROM information_schema.SYSTEM_VARIABLES
WHERE GLOBAL_VALUE_ORIGIN <> 'COMPILE-TIME' ORDER BY VARIABLE_NAME;   -- what someone changed
SHOW GLOBAL VARIABLES LIKE 'innodb_buffer_pool%';
```

The origin column misses character-set settings: in the 10.6-11.4 images `character_set_server` and `collation_server` come from `50-server.cnf` but report `COMPILE-TIME` (with that file removed, 11.4.13 starts with `latin1` / `latin1_swedish_ci`). Compare with `my_print_defaults --mysqld`.

```sh
my_print_defaults --mysqld          # options read from option files, in order
mariadbd --verbose --help | less    # compiled defaults merged with option files
mariadbd --no-defaults --verbose --help | grep -E '^binlog-format '   # compiled default only
```

Option files: `[mariadb]` and `[mariadbd]` groups are read by the server (MariaDB-only group names), along with `[mysqld]`; version-specific groups such as `[mariadb-11.8]` apply only to that series, which helps during upgrades (on 13.0.2, `max_connections=222` under `[mariadb-13.0]` took effect after a restart and the same option under `[mariadb-12.3]` was ignored). Unknown options stop the server at startup; after an upgrade the error log reports obsolete options.

`SET GLOBAL` changes are lost on restart; MariaDB has no `SET PERSIST`. Write every runtime change into the option file as well.

## Memory

| Variable | Default | Guidance |
| --- | --- | --- |
| `innodb_buffer_pool_size` | 128 MiB | Main cache. On a dedicated server with only InnoDB data, start around 70-80% of RAM minus per-connection memory and the OS page cache needs of binlogs. Resizable online. |
| `innodb_buffer_pool_size_max` | 8 TiB of reserved address space on 64-bit (10.11.17, 11.4.11, 11.8.7, 12.3.2 and later); before that, equal to the startup size | Upper bound for runtime growth. On older patch levels set it at startup if you plan to grow the pool online. |
| `innodb_buffer_pool_size_auto_min` | equals `innodb_buffer_pool_size_max` (memory-pressure shrinking disabled) | Linux only (10.11.12, 11.4.6, 11.8.2+): set lower to let the server shrink the pool on memory-pressure events instead of being OOM-killed. |
| `innodb_buffer_pool_chunk_size` | autosized; ignored from 10.11.12 / 11.4.6 / 11.8.2 | Remove from configs. |
| `innodb_log_buffer_size` | 16 MiB | Raise only for very large transactions. |
| `key_buffer_size` | 128 MiB | MyISAM index cache; lower to a few MiB if you have no MyISAM tables. |
| `aria_pagecache_buffer_size` | 128 MiB | Aria is used for internal on-disk temporary tables (`aria_used_for_temp_tables=ON`); keep tens of MiB, more if temp tables spill often. |
| `tmp_table_size`, `max_heap_table_size` | 16 MiB | In-memory temp table limit (the smaller wins). Spills go to Aria on disk. |
| `max_tmp_session_space_usage`, `max_tmp_total_space_usage` | 1 TiB (11.5+) | Cap disk used by temp files and tables per session and in total. |
| `sort_buffer_size` | 2 MiB | Per sort, per session. Do not raise globally; raise per session for a known batch. |
| `join_buffer_size` | 256 KiB | Per join buffer; `join_buffer_space_limit` 2 MiB caps total per query. |
| `query_cache_type` / `query_cache_size` | `OFF` / 1 MiB | Keep off; it serializes writes. Still available in MariaDB (removed in MySQL 8). |
| `max_session_mem_used` | very large | Set to bound runaway session memory (statement fails instead of the server swapping). |

Estimate memory: buffer pool + key buffer + Aria page cache + log buffer + (`max_connections` × per-session buffers actually used) + temp tables + Galera gcache if used. Watch `Memory_used` (global status) and RSS.

Online buffer pool resize:

```sql
SET GLOBAL innodb_buffer_pool_size = 64*1024*1024*1024;
SHOW GLOBAL STATUS LIKE 'Innodb_buffer_pool_resize_status';
```

Growing above `innodb_buffer_pool_size_max` fails with warning 1292. Shrinking evicts pages and can cause a temporary I/O spike; do it off-peak.

## Durability and I/O

| Variable | Default | Guidance |
| --- | --- | --- |
| `innodb_flush_log_at_trx_commit` | 1 | 1 for durability. 2 loses up to ~1 s of commits on OS crash, 0 also on server crash. 3 flushes at prepare and commit (rarely needed). With the InnoDB-based binlog (12.3+), this single setting controls binlog durability too. |
| `sync_binlog` | 0 | 1 on primaries with the classic binlog; with group commit the cost is moderate on SSD. |
| `innodb_log_file_size` | 96 MiB | Too small for write-heavy servers: checkpoints force flushing. Size for roughly an hour of peak redo, then check `Innodb_checkpoint_age` vs capacity in `SHOW ENGINE INNODB STATUS`. MariaDB uses a single redo file (`ib_logfile0`); `innodb_log_files_in_group` was removed in 10.6. Resizable at runtime with `SET GLOBAL` from 10.11 (10.11.19 to 13.0.2 images); read-only in 10.6 (10.6.28 returns ERROR 1238 `Variable 'innodb_log_file_size' is a read only variable`), so a change there needs a restart. |
| `innodb_flush_method` | `O_DIRECT` | Deprecated from 11.0 in favor of `innodb_log_file_buffering`, `innodb_data_file_buffering`, `innodb_log_file_write_through`, `innodb_data_file_write_through` (all `OFF` in the 13.0 image), which can be changed at runtime. |
| `innodb_doublewrite` | `ON` | Keep unless the storage guarantees atomic 16 KiB writes. |
| `innodb_io_capacity` / `innodb_io_capacity_max` | 200 / 2000 | Raise to the sustained write IOPS you can give background flushing (thousands on SSD/NVMe). |
| `innodb_adaptive_hash_index` | `OFF` | Off by default in MariaDB; enable only for read-mostly workloads after measuring. 13.1 adds per-table control. |
| `innodb_purge_threads` | 4 | Raise if the history list keeps growing under heavy DML. |
| `innodb_use_native_aio` | `ON` | On Linux MariaDB tries io_uring, then libaio. In containers io_uring is often blocked (`io_uring_queue_init() failed with EPERM ... falling back to libaio` in the 13.0 image log); harmless. |

Change buffering: the InnoDB change buffer was removed in 11.0 (disabled by default from 10.6.7). Secondary-index-heavy bulk inserts no longer get it; load data sorted by primary key and add indexes after the load.

## Connections and Threads

| Variable | Default | Guidance |
| --- | --- | --- |
| `max_connections` | 151 | Size to the pooled connection count of all clients plus headroom; very high values only help with the thread pool. |
| `extra_port`, `extra_max_connections` | 0, 1 | Configure an admin port so you can connect when `max_connections` is exhausted (and when the thread pool is saturated). |
| `thread_handling` | `one-thread-per-connection` (Unix) | `pool-of-threads` enables the built-in thread pool (in Community Server). MySQL documents its thread pool as Enterprise-only through 9.7 and in Community from 26.7.0; see [MySQL configuration](../mysql/configuration.md). |
| `thread_pool_size` | number of CPUs (14 in the test host) | Thread groups. |
| `thread_pool_stall_limit` | 500 ms | Time before a busy group gets another worker. |
| `thread_pool_max_threads` | 65536 | Cap. |
| `thread_cache_size` | 151 | Unused with the thread pool. |
| `wait_timeout` / `interactive_timeout` | 28800 s | Lower (for example 300-600) when clients leak idle connections. |
| `max_statement_time` | 0 | Set per session or role for ad-hoc and reporting users. |
| `skip_name_resolve` | `OFF` compiled; `ON` in the images | Turn on to avoid DNS lookups at connect; then grants must use IPs or `%` patterns, not host names. |

Thread pool decision: enable it for many short, CPU-bound OLTP queries and thousands of client connections. Avoid it, or keep an `extra_port`, when the workload has many long non-yielding queries, very bursty arrival, or global locks such as `FLUSH TABLES WITH READ LOCK`, which can block the whole pool. Monitor `Threadpool_threads`, `Threadpool_idle_threads`, and `information_schema.THREAD_POOL_GROUPS`, `THREAD_POOL_QUEUES`, `THREAD_POOL_STATS`, `THREAD_POOL_WAITS`. `thread_handling` is static: plan a restart.

## SQL Mode and Compatibility Settings

- `sql_mode` default: `STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION` (all images). Unlike MySQL 8, `ONLY_FULL_GROUP_BY` is not in the default; add it if you want MySQL-like `GROUP BY` checking.
- `explicit_defaults_for_timestamp`: `OFF` on 10.6, `ON` from 10.10.
- `old_mode`: `UTF8_IS_UTF8MB3` through 13.0; removed from the default in 13.1 (`utf8` = `utf8mb4`).
- `lower_case_table_names`: 0 on Linux images; set at datadir initialization and never change afterwards.
- `sql_mode=ORACLE` enables PL/SQL-compatible syntax per session or routine; do not set it globally on a MySQL-style application.

## Starting Points by Server Size

Illustrative values for a dedicated InnoDB server (adjust after measuring):

```ini
[mariadb]
# 64 GiB RAM, NVMe, OLTP
innodb_buffer_pool_size        = 48G
innodb_log_file_size           = 4G
innodb_io_capacity             = 2000
innodb_io_capacity_max         = 8000
innodb_flush_log_at_trx_commit = 1
sync_binlog                    = 1
log_bin                        = mariadb-bin
binlog_format                  = ROW
server_id                      = 11
gtid_strict_mode               = ON
log_slave_updates              = ON
max_connections                = 500
extra_port                     = 3307
extra_max_connections          = 10
key_buffer_size                = 8M
aria_pagecache_buffer_size     = 64M
log_slow_query                 = ON
log_slow_query_time            = 1
```

Verify after a restart: `SELECT VARIABLE_NAME, GLOBAL_VALUE FROM information_schema.SYSTEM_VARIABLES WHERE VARIABLE_NAME IN ('innodb_buffer_pool_size','innodb_log_file_size','binlog_format','gtid_strict_mode');` and the error log for warnings.

## Risky Changes and Rollback

| Change | Risk | Safer path |
| --- | --- | --- |
| `innodb_flush_log_at_trx_commit` to 0/2 | Committed transactions lost on crash | Use only on replicas or rebuildable data; record it |
| `innodb_snapshot_isolation=OFF` | Lost updates possible | Session scope for one job; fix retries instead |
| Changing `binlog_format` on a running primary | Replicas or Galera break | Change on replicas first; on Galera never at runtime |
| `innodb_force_recovery` > 0 | Read-only, limited; values ≥ 4 can lose data | Only to dump data; restore from backup afterwards |
| `thread_handling=pool-of-threads` | Pool stalls on long queries or global locks | Configure `extra_port` first; test with production concurrency |
| Lowering `innodb_buffer_pool_size` online | I/O spike, latency | Off-peak, in steps |
