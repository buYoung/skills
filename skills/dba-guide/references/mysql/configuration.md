# MySQL Server Configuration

Checked: 2026-11-27. Applies to MySQL 8.0 through 26.10. Many defaults changed in 8.4 and 9.x; check the version file before comparing two servers.

## How Settings Are Applied

| Mechanism | Persists across restart | Where it lives | Use for |
|---|---|---|---|
| Option file (`/etc/my.cnf`, `/etc/mysql/conf.d/*.cnf`) | yes | file | Baseline under configuration management. |
| `SET GLOBAL v = x` | no | memory | Immediate change you will also write to the option file. |
| `SET PERSIST v = x` | yes | `mysqld-auto.cnf` in the data directory | Change now and keep it; overrides option files at the next start. |
| `SET PERSIST_ONLY v = x` | yes, next start only | `mysqld-auto.cnf` | Read-only (startup) variables. |
| `RESET PERSIST [v]` | removes the persisted entry | | Undo a persisted value. The running global value stays until restart or `SET GLOBAL`. |

`SET GLOBAL` and `SET PERSIST` do not change the current session's copy of a variable that has session scope. `SELECT @@long_query_time` shows the session value; use `SELECT @@GLOBAL.long_query_time` to see what you set. Container check (all five images): `SET PERSIST long_query_time = 0.5` appears in `performance_schema.persisted_variables`, `RESET PERSIST long_query_time` removes it, and the session's `@@long_query_time` stayed 10 throughout. A second check on all five images: after `SET PERSIST innodb_io_capacity = 1500` and `SET PERSIST long_query_time = 0.5`, `variables_info.VARIABLE_SOURCE` is `DYNAMIC` until the restart and `PERSISTED` after it; `RESET PERSIST` then empties `persisted_variables` but leaves `@@GLOBAL.innodb_io_capacity` at 1500, `@@GLOBAL.long_query_time` at 0.5 and `VARIABLE_SOURCE` at `PERSISTED` until the next restart. On 8.0, `innodb_io_capacity` above `innodb_io_capacity_max` (2000 by default) is clamped with warning 1210.

Find where a running value came from:

```sql
SELECT VARIABLE_NAME, VARIABLE_SOURCE, VARIABLE_PATH, SET_TIME, SET_USER
  FROM performance_schema.variables_info WHERE VARIABLE_SOURCE <> 'COMPILED';
SELECT * FROM performance_schema.persisted_variables;
```

`mysqld-auto.cnf` wins over the option file without warning. When a configuration-managed value "does not stick", check it first. A persisted variable that a newer version removed stops the upgraded server from starting; clear it with `RESET PERSIST` before the upgrade.

## Memory

| Variable | Default (containers) | Guidance |
|---|---|---|
| `innodb_buffer_pool_size` | 128 MiB | Dedicated server: start at 60-75% of RAM, leaving room for connections, temp tables, the OS, and file cache for binlogs. Dynamic; resizes in `innodb_buffer_pool_chunk_size` (128 MiB) steps. Resizing a large pool takes time and briefly blocks access during its critical section; do it off-peak. |
| `innodb_dedicated_server` | OFF | ON sizes the buffer pool and redo capacity from host resources. In 8.4+ it no longer changes `innodb_flush_method`, and redo sizing is CPU-based. Explicit settings override it. |
| `innodb_buffer_pool_instances` | 1 for pools <= 1 GiB (8.4+) | Leave the default unless buffer pool mutex contention shows in `SHOW ENGINE INNODB STATUS`. |
| `temptable_max_ram` | 1 GiB in 8.0; 3% of RAM clamped to 1-4 GiB in 8.4+ | Internal temporary tables above it go to InnoDB on disk (mmap is off by default in 8.4+; `temptable_use_mmap` removed in 9.4.0). |
| `tmp_table_size` / `max_heap_table_size` | 16 MiB / 16 MiB | Per temporary table; raise only for known large `GROUP BY`. |
| `sort_buffer_size`, `join_buffer_size`, `read_rnd_buffer_size` | 256 KiB each | Per session, allocated as needed. Do not raise globally; use `SET_VAR` hints for specific statements. |
| `connection_memory_limit`, `global_connection_memory_limit` (8.0.28+) | unlimited | Set them to stop one runaway session from exhausting memory; the global limit needs `global_connection_memory_tracking=ON`. |
| `server_memory` (9.4.0+) | 0 | Caps the memory the server assumes when it derives memory-based defaults. |

Check memory use:

```sql
SELECT * FROM sys.memory_global_total;
SELECT event_name, current_alloc FROM sys.memory_global_by_current_bytes LIMIT 15;
SELECT * FROM sys.memory_by_thread_by_current_bytes LIMIT 10;
```

Buffer pool effectiveness:

```sql
SELECT POOL_SIZE, FREE_BUFFERS, DATABASE_PAGES, MODIFIED_DATABASE_PAGES, HIT_RATE, PAGES_READ_RATE
  FROM information_schema.INNODB_BUFFER_POOL_STATS;
SHOW GLOBAL STATUS LIKE 'Innodb_buffer_pool_read%';
-- misses = Innodb_buffer_pool_reads; logical reads = Innodb_buffer_pool_read_requests
```

A low hit rate matters only together with read latency. Compare `Innodb_buffer_pool_reads` per second with the storage's IOPS budget.

## Durability and Redo

| Setting | Durable on crash | Cost |
|---|---|---|
| `innodb_flush_log_at_trx_commit=1`, `sync_binlog=1` (defaults) | Every acknowledged commit survives OS or power failure | Two fsyncs per group commit. |
| `innodb_flush_log_at_trx_commit=2` | Survives a mysqld crash; up to about 1 s lost on OS or power failure | Only on replicas you can rebuild, or with a written risk acceptance. |
| `innodb_flush_log_at_trx_commit=0` | Up to about 1 s lost even on a mysqld crash | Bulk loads into throwaway instances only. |
| `sync_binlog=0` or `N` | The binlog can lose transactions InnoDB kept; replicas and PITR diverge from the primary | Avoid on a primary. |

Redo log size: `innodb_redo_log_capacity` (8.0.30+, dynamic; 100 MiB default in all containers). The default is small for write-heavy servers. Size it so the checkpoint age stays well below capacity at peak:

```sql
SHOW GLOBAL STATUS LIKE 'Innodb_redo_log_capacity_resized';
SELECT NAME, COUNT, STATUS FROM information_schema.INNODB_METRICS
 WHERE NAME IN ('log_lsn_current','log_lsn_last_checkpoint');   -- disabled by default: SET GLOBAL innodb_monitor_enable = 'log_lsn_%' first
SET PERSIST innodb_redo_log_capacity = 8589934592;   -- 8 GiB, applied online
```

Alternatively compare `Log sequence number` and `Last checkpoint at` in `SHOW ENGINE INNODB STATUS`. `innodb_log_file_size` and `innodb_log_files_in_group` were removed in 9.3.0.

Do not disable the doublewrite buffer (`innodb_doublewrite`) unless the storage guarantees atomic 16 KiB writes. `ALTER INSTANCE DISABLE INNODB REDO_LOG` is for initial data loads only: a crash while redo logging is disabled can lose the instance.

## I/O

| Variable | Default 8.0 -> 8.4+ | Guidance |
|---|---|---|
| `innodb_flush_method` | `fsync` -> `O_DIRECT` (Linux) | Keep `O_DIRECT` on local and network block storage. |
| `innodb_io_capacity` / `_max` | 200/2000 -> 10000/20000 | Set near the sustained write IOPS of the volume. The 8.4 default is high for HDD or burst-limited cloud volumes. |
| `innodb_use_fdatasync` | OFF -> ON | |
| `innodb_flush_neighbors` | 0 | Leave 0 on SSD. |
| `innodb_change_buffering` | `all` -> `none` (8.4) -> `all` (9.5+) | |
| `innodb_adaptive_hash_index` | ON -> OFF (8.4+) | Enable only after measuring a benefit. |

## Connections and Threads

- `max_connections` default 151 (all containers). Each connection costs a thread and session buffers. Raising it to several thousand without a thread pool or a pooler in front degrades throughput.
- Use a connection pool in the application or a proxy. Check peak use with `SHOW GLOBAL STATUS LIKE 'Max_used_connections%'` and `Threads_running`.
- `thread_handling=one-thread-per-connection` (default). The thread pool plugin is documented as Enterprise in 8.0-9.7 and as Community from 26.7.0. The `mysql:9.7` Community image (9.7.4) already ships `thread_pool.so` and loads it with license GPL when started with `--plugin-load-add=thread_pool.so` (container); the 8.0 and 8.4 images do not ship it.
- Admin access when `max_connections` is exhausted: set `admin_address` and `admin_port` (33062 by default; `create_admin_listener_thread` OFF). Only accounts with `SERVICE_CONNECTION_ADMIN` can use it. The main port also admits one extra connection for `CONNECTION_ADMIN` holders.
- `wait_timeout` and `interactive_timeout` are 28800 s. Lower `wait_timeout` (for example 600) when idle pooled connections pile up, matching the pool's idle timeout.
- `back_log` is 151 in 8.4 and 10000 from 9.4.0; the OS `net.core.somaxconn` caps it.
- `skip_name_resolve=ON` and `host_cache_size=0` in the containers come from the official image's configuration (inference, not documented); a package install resolves host names by default. With name resolution on, a slow DNS server delays every new connection.

## SQL Behavior

- `sql_mode` default (all containers): `ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION`. Loosening it to accept legacy SQL hides data errors (truncation, invalid dates). Fix the application, or relax it per session for one job.
- `lower_case_table_names` can be set only when the data directory is initialized; a different value later prevents startup.
- `character_set_server=utf8mb4`, `collation_server=utf8mb4_0900_ai_ci` (all containers).
- `explicit_defaults_for_timestamp=ON`.

## Baseline Option File for a Dedicated 8.4/9.7 Primary

Example for 64 GiB RAM, SSD, mixed OLTP. Adjust after measurement.

```ini
[mysqld]
server_id                      = 101
gtid_mode                      = ON
enforce_gtid_consistency       = ON
binlog_expire_logs_seconds     = 604800
innodb_buffer_pool_size        = 44G
innodb_redo_log_capacity       = 8G
innodb_io_capacity             = 4000
innodb_io_capacity_max         = 8000
max_connections                = 800
wait_timeout                   = 600
slow_query_log                 = ON
long_query_time                = 0.5
log_slow_extra                 = ON
innodb_print_all_deadlocks     = ON
require_secure_transport       = ON
# set super_read_only = ON on every replica
```

Verify after a restart: `SELECT VARIABLE_NAME, VARIABLE_PATH FROM performance_schema.variables_info WHERE VARIABLE_SOURCE IN ('GLOBAL','SERVER','EXPLICIT','EXTRA')` lists values that came from option files; compare with the intended file.

## Safe Change Procedure

1. Check the variable's scope and whether it is dynamic in the server system variable reference for your version. In 9.x read limits from `performance_schema.variables_metadata` (the `MIN_VALUE`/`MAX_VALUE` columns of `variables_info` are deprecated since 9.0.0).
2. Change one variable at a time with `SET GLOBAL`, observe through a full peak, then persist it (`SET PERSIST`) or write it to the option file.
3. Roll back with `SET GLOBAL v = <old>` and `RESET PERSIST v`.
4. Startup-only variables (`innodb_buffer_pool_instances`) need a restart: change them on a replica first, then fail over to it. Initialization-only settings (`innodb_page_size`, `lower_case_table_names`) need a new data directory and a reload.

## Sources

Checked 2026-11-27: variable dumps and statement runs on the official images mysql:8.0, 8.4, 9.7, 26.7, 26.10; MySQL 8.4 What Is New (InnoDB default table, `innodb_dedicated_server` change); Changes in MySQL 9.0.0, 9.3.0, 9.4.0, 9.5.0 (`variables_metadata`, removed redo variables, `back_log`, `server_memory`, change-buffer defaults); 26.7 What Is New and 26.7.0 notes (thread pool in Community). Durability, memory and connection semantics follow the MySQL 8.4 manual InnoDB configuration and server system variable pages (https://dev.mysql.com/doc/refman/8.4/en/innodb-parameters.html, https://dev.mysql.com/doc/refman/8.4/en/server-system-variables.html).
