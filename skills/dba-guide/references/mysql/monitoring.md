# MySQL Monitoring and Latency Diagnosis

Checked: 2026-11-27. Applies to MySQL 8.0 through 26.10.

## What Is On by Default

All five containers: `performance_schema=ON` with consumers `events_statements_current`, `events_statements_history`, `events_transactions_current/history`, `global_instrumentation`, `thread_instrumentation`, `statements_digest` enabled; stage and wait consumers off; `slow_query_log=OFF`, `long_query_time=10`; `log_error_verbosity=2`; `performance_schema_show_processlist=OFF`.

Turn on the slow log on every production server:

```sql
SET PERSIST slow_query_log = ON, long_query_time = 0.5, log_slow_extra = ON;
SET PERSIST log_slow_admin_statements = ON;   -- include ALTER, OPTIMIZE, ANALYZE
```

`log_queries_not_using_indexes=ON` floods the log on small lookup tables; if used, set `log_throttle_queries_not_using_indexes`.

## Triage Order for "The Database Is Slow"

1. What is running now:
   ```sql
   SELECT * FROM sys.processlist WHERE command <> 'Sleep' ORDER BY time DESC LIMIT 20;
   -- or, without the sys schema
   SELECT ID, USER, HOST, DB, COMMAND, TIME, STATE, LEFT(INFO, 100)
     FROM performance_schema.processlist WHERE COMMAND <> 'Sleep' ORDER BY TIME DESC;
   ```
   `SHOW PROCESSLIST` and `INFORMATION_SCHEMA.PROCESSLIST` (deprecated since 8.0.35) take a global mutex; prefer `performance_schema.processlist`. `SET PERSIST performance_schema_show_processlist = ON` makes `SHOW PROCESSLIST` use it.
2. Is it waiting on locks? `SELECT * FROM sys.innodb_lock_waits;` and `sys.schema_table_lock_waits` (metadata locks). See [transactions-and-locking.md](transactions-and-locking.md#diagnosing-lock-waits).
3. Which statements consume time overall: digest summary (see [query-plans.md](query-plans.md#find-the-statements-worth-tuning)).
4. Is the server saturated? Threads, I/O, buffer pool, redo, purge, below.
5. Is a replica lagging? See [replication-and-ha.md](replication-and-ha.md#monitoring-replication).
6. Host level: CPU steal, disk latency (`iostat -x`), memory pressure and swapping. From 26.10, the Health Monitor component exposes host CPU, memory and disk metrics and disk forecasts through Performance Schema in Community Edition.

## Key Status Counters

Take two samples a known interval apart and compute rates; absolute values since startup mislead.

```sql
SELECT VARIABLE_NAME, VARIABLE_VALUE FROM performance_schema.global_status
 WHERE VARIABLE_NAME IN (
  'Threads_running','Threads_connected','Max_used_connections','Aborted_connects','Aborted_clients',
  'Questions','Com_commit','Com_rollback','Slow_queries',
  'Innodb_buffer_pool_reads','Innodb_buffer_pool_read_requests','Innodb_buffer_pool_wait_free',
  'Innodb_row_lock_waits','Innodb_row_lock_time','Innodb_data_fsyncs','Innodb_os_log_written',
  'Created_tmp_disk_tables','Created_tmp_tables','Select_full_join','Sort_merge_passes',
  'Connection_errors_max_connections');
```

| Signal | Interpretation |
|---|---|
| `Threads_running` persistently above CPU core count | CPU saturation or lock/IO waits; look at what they wait on. |
| `Innodb_buffer_pool_wait_free` > 0 and rising | Flushing cannot keep up; check `innodb_io_capacity` and storage. |
| `Innodb_row_lock_waits` rate up | Contention; find hot rows via `sys.innodb_lock_waits`. |
| `Created_tmp_disk_tables` / `Created_tmp_tables` high | Large internal temp tables; index the GROUP BY/ORDER BY. |
| `Select_full_join` > 0 | Joins without an index on the inner table. |
| `Connection_errors_max_connections` > 0 | Pool misconfiguration or connection leak. |
| `Aborted_clients` rising | Clients drop connections without closing (timeouts, crashes). |

InnoDB internals:

```sql
SHOW ENGINE INNODB STATUS\G
```

Read: `History list length` (purge backlog), `Log sequence number` vs `Last checkpoint at` (checkpoint age against `innodb_redo_log_capacity`), `Pending normal aio reads/writes` (I/O queueing), `Buffer pool hit rate`, `LATEST DETECTED DEADLOCK`, and the `SEMAPHORES` section (long waits indicate internal contention).

## Wait Analysis

Enable wait instruments temporarily when CPU and lock views do not explain latency:

```sql
UPDATE performance_schema.setup_instruments SET ENABLED='YES', TIMED='YES'
 WHERE NAME LIKE 'wait/io/file/innodb/%' OR NAME LIKE 'wait/synch/%/innodb/%';
UPDATE performance_schema.setup_consumers SET ENABLED='YES' WHERE NAME LIKE 'events_waits_%';
SELECT * FROM sys.waits_global_by_latency LIMIT 15;
SELECT * FROM sys.io_global_by_file_by_latency LIMIT 10;
-- revert afterwards (changes are not persisted; a restart also reverts)
UPDATE performance_schema.setup_consumers SET ENABLED='NO' WHERE NAME LIKE 'events_waits_%';
```

Instrumentation has CPU overhead; enable it for minutes, not permanently, on busy primaries.

## Table and Index Usage

```sql
SELECT * FROM sys.schema_table_statistics WHERE table_schema = 'app' ORDER BY total_latency DESC LIMIT 10;
SELECT * FROM sys.schema_index_statistics WHERE table_schema = 'app' ORDER BY rows_selected DESC LIMIT 10;
SELECT table_schema, table_name, ROUND(data_length/1024/1024) AS data_mb,
       ROUND(index_length/1024/1024) AS index_mb, ROUND(data_free/1024/1024) AS free_mb
  FROM information_schema.TABLES WHERE table_schema = 'app' ORDER BY data_length DESC LIMIT 10;
```

`information_schema.TABLES` sizes are cached for `information_schema_stats_expiry` seconds (86400 by default); run `ANALYZE TABLE` or set the session variable to 0 for fresh numbers.

## Error Log

- `log_error=stderr` in the container; packages write to a file. `log_timestamps=UTC`.
- `SELECT * FROM performance_schema.error_log ORDER BY LOGGED DESC LIMIT 50;` reads recent entries through SQL.
- Messages to act on: `[ERROR]` lines at startup (removed variables after an upgrade), `InnoDB: page_cleaner: ... loop took` (flushing behind), long semaphore waits, `Aborted connection`, and from 26.10 purge-lag warnings.
- 9.4.0+ logs the detected logical CPU count and memory at startup. The 26.10 container log shows `MySQL Server has access to 14 logical CPUs` and a warning that container restrictions are ignored while `container_aware=OFF`.

## Metrics to Alert On

| Metric | Source | Alert when |
|---|---|---|
| Availability | connect + `SELECT 1` | fails |
| Replication | `Replica_IO_Running`, `Replica_SQL_Running`, applier lag | not Yes, or lag above SLO |
| Connections | `Threads_connected` / `max_connections` | > 80% |
| Running threads | `Threads_running` | sustained above cores |
| Purge backlog | `trx_rseg_history_len` | growing for > 1 h |
| Oldest transaction | `INNODB_TRX.trx_started` | older than your longest expected job |
| Deadlocks | `lock_deadlocks` metric | step change |
| Disk | data, binlog, tmp volumes | < 20% free; binlogs grow when replicas or binlog readers stall |
| Slow queries | `Slow_queries` rate | step change |
| Backups | job result and last restore test | failed or stale |

## Sources

Checked 2026-11-27: statement runs on the official mysql:8.0 to 26.10 images (Performance Schema consumers, slow log defaults, `sys` views output, error log lines); MySQL 8.4 What Is New (`INFORMATION_SCHEMA.PROCESSLIST` deprecation and usage counters); Changes in MySQL 9.4.0 (CPU and memory logged at startup); Changes in MySQL 26.10.0 (Health Monitor in Community, purge-lag warnings). Status variables, `sys` views and `SHOW ENGINE INNODB STATUS` sections follow the MySQL 8.4 manual chapters on the Performance Schema, sys schema, and InnoDB monitors (https://dev.mysql.com/doc/refman/8.4/en/performance-schema.html, https://dev.mysql.com/doc/refman/8.4/en/sys-schema.html).
