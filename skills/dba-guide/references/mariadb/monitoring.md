# MariaDB Monitoring and Diagnosis

Checked: 2026-11-27 (sources at the end). MariaDB ships the Performance Schema disabled by default and has its own instrumentation (slow log verbosity, `userstat`, `SHOW EXPLAIN/ANALYZE FOR`, `information_schema` extensions) that MySQL lacks.

## Sources of Evidence

| Source | Default | Cost | Gives |
| --- | --- | --- | --- |
| Slow query log | off (`log_slow_query=OFF`, `log_slow_query_time=10`) | Low with sensible thresholds | Statement text, time, rows examined, optional plan details |
| `SHOW GLOBAL STATUS` | always | none | Counters |
| `SHOW ENGINE INNODB STATUS` | always | none | InnoDB internals, last deadlock, history list, checkpoint |
| `information_schema.PROCESSLIST` / `SHOW FULL PROCESSLIST` | always | none | Running statements, state, time, progress |
| Performance Schema | `performance_schema=OFF` (all images) | Memory and some CPU; needs restart to enable | Statement digests, waits, metadata locks, memory |
| `sys` schema (10.6+) | installed | none | Views over Performance Schema and `information_schema` |
| `userstat` | `OFF` | Low | `information_schema.USER_STATISTICS`, `CLIENT_STATISTICS`, `TABLE_STATISTICS`, `INDEX_STATISTICS` |
| Error log | on | none | Crashes, InnoDB warnings, replication errors, deadlocks if `innodb_print_all_deadlocks=ON` |
| Audit plugin | not installed | depends on events | Who did what (see [security](security.md)) |

## Slow Query Log

```ini
[mariadb]
log_slow_query          = ON           # alias slow_query_log
log_slow_query_time     = 0.5          # alias long_query_time
log_slow_query_file     = /var/log/mysql/slow.log
log_slow_verbosity      = query_plan,explain   # adds plan flags and EXPLAIN output
log_slow_rate_limit     = 1            # log every Nth qualifying query; raise on very busy servers
log_slow_admin_statements = ON         # default ON in the images
log_slow_always_query_time = 5         # 11.7+: always log above this, ignoring rate limit and row filters
```

- The `log_slow_query*` names exist from 10.11 (10.6 uses `slow_query_log`, `long_query_time`, `slow_query_log_file`; the old names remain as aliases).
- `log_slow_filter` restricts which slow queries are written; the default in the images lists all categories (`full_scan`, `filesort_on_disk`, `tmp_table_on_disk`, `full_join` and others).
- `log_slow_min_examined_row_limit` skips cheap queries.
- 13.1: `log_slow_max_query_length` skips (does not truncate) statements longer than the limit.
- Changes are dynamic: `SET GLOBAL log_slow_query_time = 0.2;`. Revert after an investigation if you lowered thresholds; a busy server can write gigabytes per hour at `0`.
- Summarize with `pt-query-digest` or similar tools (third-party; verify they parse MariaDB's extra fields).

## Performance Schema

Enable at startup only:

```ini
[mariadb]
performance_schema = ON
performance-schema-instrument = 'stage/%=ON'          # optional: stages for progress
performance-schema-consumer-events-statements-history = ON
```

Then:

```sql
-- Top statements by total latency
SELECT DIGEST_TEXT, COUNT_STAR, ROUND(SUM_TIMER_WAIT/1e12,1) AS total_s,
       ROUND(AVG_TIMER_WAIT/1e9,2) AS avg_ms, SUM_ROWS_EXAMINED, SUM_ROWS_SENT
FROM performance_schema.events_statements_summary_by_digest
ORDER BY SUM_TIMER_WAIT DESC LIMIT 10;

SELECT * FROM sys.statement_analysis LIMIT 10;
SELECT * FROM sys.schema_unused_indexes;
SELECT * FROM performance_schema.metadata_locks;     -- needs the mdl instrument enabled
```

From 13.0, digests use XXH3 instead of MD5, so digest values change across that upgrade; rebaseline dashboards keyed on digest. Expect a few percent overhead and a noticeable memory footprint with autosized defaults (`performance_schema_*_size=-1`) (overhead figures are general guidance, not measured here).

## Per-Object Statistics without the Performance Schema

```sql
SET GLOBAL userstat = ON;
SELECT * FROM information_schema.TABLE_STATISTICS ORDER BY ROWS_READ DESC LIMIT 10;
SELECT * FROM information_schema.INDEX_STATISTICS WHERE TABLE_SCHEMA = 'app';
SELECT * FROM information_schema.USER_STATISTICS\G
FLUSH TABLE_STATISTICS; FLUSH INDEX_STATISTICS;   -- reset (10.6-13.0 images)
```

Indexes that never appear in `INDEX_STATISTICS` over a full business cycle are drop candidates; mark them `IGNORED` first (see [schema](schema-and-indexes.md#index-design)). 11.5+ adds a `QUERIES` column to `INDEX_STATISTICS` and more columns to the table, client and user statistics.

## Key Status Counters

```sql
SHOW GLOBAL STATUS WHERE Variable_name IN (
 'Threads_connected','Threads_running','Max_used_connections','Aborted_connects','Aborted_clients',
 'Questions','Com_commit','Com_rollback','Slow_queries',
 'Innodb_buffer_pool_read_requests','Innodb_buffer_pool_reads','Innodb_buffer_pool_wait_free',
 'Innodb_row_lock_waits','Innodb_row_lock_time_avg','Innodb_deadlocks',
 'Created_tmp_disk_tables','Created_tmp_tables','Select_full_join','Sort_merge_passes',
 'Handler_read_rnd_next','Binlog_cache_disk_use','Memory_used');
```

| Signal | Interpretation |
| --- | --- |
| `Threads_running` high and rising | Contention or slow queries; look at the processlist states |
| `Innodb_buffer_pool_reads` / `read_requests` above ~1% sustained | Working set exceeds the buffer pool (rule of thumb) |
| `Innodb_buffer_pool_wait_free` > 0 | Flushing cannot keep up; raise `innodb_io_capacity` or check storage |
| `Innodb_row_lock_waits` rising, high `Innodb_row_lock_time_avg` | Row lock contention; see [transactions](transactions-and-locking.md#diagnosing-blocking-now) |
| `Created_tmp_disk_tables` / `Created_tmp_tables` high | Temp tables spill (BLOB/TEXT columns, size limits) |
| `Select_full_join` > 0 | Joins without usable indexes |
| `Binlog_cache_disk_use` / `Binlog_cache_use` high | Transactions bigger than `binlog_cache_size` |
| `Aborted_connects` rising | Auth failures, TLS mismatch, `max_connections` |
| `Memory_used` (global) | Server-tracked memory; compare with RSS to spot untracked growth. Per session: `SHOW SESSION STATUS LIKE 'Memory_used'`; cap with `max_session_mem_used` |
| `Threadpool_threads`, `Threadpool_idle_threads` | Meaningful only with `thread_handling=pool-of-threads`; with the default `one-thread-per-connection` they exist and read 0 (10.6-13.0 images); see [configuration](configuration.md) |

Counters are cumulative since startup; sample twice and compute rates. `FLUSH GLOBAL STATUS` (11.5+) resets global counters; avoid it if a monitoring system computes deltas.

## Live Diagnosis

```sql
SHOW FULL PROCESSLIST;
SELECT ID, USER, HOST, DB, COMMAND, TIME, STATE, PROGRESS, LEFT(INFO,120) AS q
FROM information_schema.PROCESSLIST WHERE COMMAND <> 'Sleep' ORDER BY TIME DESC;

SHOW EXPLAIN FOR 1234;                   -- plan of a running query
SHOW ANALYZE FORMAT=JSON FOR 1234;       -- plan with live counters (10.9+, so 10.11+)
SHOW ENGINE INNODB STATUS\G
```

- `PROGRESS` and `STAGE`/`MAX_STAGE` columns (MariaDB-specific) show progress for `ALTER TABLE`, `LOAD DATA` and some other long statements; `progress_report_time=5` sends progress to the `mariadb` client.
- Processlist states to recognize: `Waiting for table metadata lock` (DDL blocked by an open transaction), `Sending data`/`Sending to client` (reading, or client too slow), `Creating sort index`, `Copying to tmp table on disk`, `Waiting for semi-sync ACK from slave`, `Commit` stalls (fsync latency), `Killed` (rolling back).
- `SHOW ENGINE INNODB STATUS` sections: `TRANSACTIONS` (history list length, active transactions and their locks), `LOG` (LSN, last checkpoint: checkpoint age close to capacity means the redo log is too small), `BUFFER POOL AND MEMORY` (free buffers, modified pages), `ROW OPERATIONS`, `LATEST DETECTED DEADLOCK`.
- History list length growing for minutes: find the oldest transaction in `INNODB_TRX` (see [transactions](transactions-and-locking.md#mvcc-purge-and-history-length)).

## Latency Triage

1. Is it the server? Compare client-observed latency with the `Questions` rate and slow-log timings. If the server is fast, look at the network, proxy, or connection pool.
2. One query or everything? One query: [query plans](query-plans.md). Everything: check `Threads_running`, CPU, I/O wait, `Innodb_buffer_pool_wait_free`, fsync latency (`Commit` state), semi-sync waits, Galera flow control (`wsrep_flow_control_paused`).
3. Locks: processlist states, `INNODB_TRX`, `sys.innodb_lock_waits`, metadata locks.
4. Recent change? Compare `SELECT VERSION()`, changed variables (`GLOBAL_VALUE_ORIGIN`), and plan output with the baseline. After upgrades into 11.x expect plan changes (cost model); into 11.8 expect error 1020 retries ([snapshot isolation](transactions-and-locking.md#snapshot-isolation-and-error-1020)).
5. Verify the fix by the same metric that showed the problem (digest average, application p95, `Threads_running`).

## Replication and Cluster Monitoring

See [replication](replication-and-ha.md#lag-and-health) for `SHOW REPLICA STATUS` fields and [Galera](replication-and-ha.md#galera-cluster) for `wsrep_*` signals. Alert on: SQL or I/O thread stopped, lag above the RPO, `Rpl_semi_sync_master_status=OFF`, `wsrep_cluster_status <> PRIMARY`, `wsrep_cluster_size` below expected.

## Disk and Files

- InnoDB tablespace growth: `SELECT TABLE_SCHEMA, TABLE_NAME, ROUND((DATA_LENGTH+INDEX_LENGTH)/1024/1024) AS mb, ROUND(DATA_FREE/1024/1024) AS free_mb FROM information_schema.TABLES ORDER BY mb DESC LIMIT 20;`
- 13.1: `innodb_tablespace_size_warning_threshold` writes error-log warnings as tablespaces approach a size.
- Binlog disk: `SHOW BINARY LOGS;` sizes; cap with `max_binlog_total_size` (11.4+).
- Temp space: `max_tmp_total_space_usage` (11.5+) protects the volume; watch `tmpdir` free space during large sorts and `ALTER`.
- Undo: with separate undo tablespaces (`innodb_undo_tablespaces>0`, default 3 from 11.0) and `innodb_undo_log_truncate=ON`, undo shrinks after long transactions end.

## Sources

- MariaDB 10.11 Changes & Improvements (renamed slow-log variables): https://mariadb.com/docs/release-notes/community-server/10.11/what-is-mariadb-1011, checked 2026-11-27
- MariaDB 11.8 Changes & Improvements (11.5-11.7 changes: `log_slow_always_query_time`, `FLUSH GLOBAL STATUS`, `max_tmp_total_space_usage`, extended `userstat` columns): https://mariadb.com/docs/release-notes/community-server/11.8/what-is-mariadb-118, checked 2026-11-27
- MariaDB 13.0 Changes & Improvements (XXH3 digests): https://mariadb.com/docs/release-notes/community-server/13.0/mariadb-13.0-changes-and-improvements, checked 2026-11-27
- MariaDB 13.1 Changes & Improvements (`log_slow_max_query_length`, tablespace size warnings): https://mariadb.com/docs/release-notes/community-server/13.1/mariadb-13.1-changes-and-improvements, checked 2026-11-27
- Galera Cluster status variables: https://mariadb.com/docs/galera-cluster/reference/galera-cluster-status-variables, checked 2026-11-27
- Thread pool in MariaDB: https://mariadb.com/docs/server/ha-and-performance/optimization-and-tuning/buffers-caches-and-threads/thread-pool/thread-pool-in-mariadb, checked 2026-11-27
- Official container images, variable dumps and statement runs, 2026-11-27 (`performance_schema=OFF`, `userstat=OFF`, slow-log defaults)
- Status variable names (`Memory_used`, `Innodb_deadlocks`, `Innodb_checkpoint_age`, `Innodb_buffer_pool_resize_status`, `Threadpool_*`, `Rpl_semi_sync_master_status`), the `PROGRESS` column and `FLUSH TABLE_STATISTICS`/`FLUSH INDEX_STATISTICS`: official images 10.6.28, 10.11.19, 11.4.13, 11.8.9, 12.3.3, 13.0.2, run 2026-11-27
