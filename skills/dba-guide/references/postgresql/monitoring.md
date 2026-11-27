# Monitoring and Latency Diagnosis

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)). View availability differs by version; the table below says where.

## View availability

| View or function | 14 | 15 | 16 | 17 | 18 | 19 | Answers |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `pg_stat_activity` | yes | yes | yes | yes | yes | yes | who is running what, waiting on what |
| `pg_stat_statements` (extension, needs `shared_preload_libraries`) | 1.9 | 1.10 | 1.10 | 1.11 | 1.12 | 1.13 | which statements cost the most |
| `pg_stat_io` | no | no | yes | yes (35 rows) | yes, bytes and WAL rows (79 rows) | yes | I/O by backend type, object, context |
| `pg_stat_checkpointer` | no | no | no | yes | adds `num_done`, `slru_written` | yes | checkpoint counts and timing |
| `pg_stat_bgwriter` | includes checkpoint columns | same | same | bgwriter only | bgwriter only | bgwriter only | background writer |
| `pg_stat_wal` | records, fpi, bytes, buffers_full, write/sync | same as 14 | same as 14 | same as 14 | write/sync columns removed | adds `wal_fpi_bytes` | WAL volume |
| `pg_wait_events` | no | no | no | yes | yes | yes | descriptions of wait events |
| `pg_stat_recovery_prefetch` | no | yes | yes | yes | yes | yes | recovery prefetch |
| `pg_aios` | no | no | no | no | yes | yes | in-flight async I/O |
| `pg_stat_lock`, `pg_stat_recovery`, `pg_stat_autovacuum_scores` | no | no | no | no | no | yes | lock statistics, recovery state, autovacuum priority |

Version and column facts in this table come from release notes and runs on the official images (all six versions checked).

## Baseline collection

Enable these on every production server:

```
shared_preload_libraries = 'pg_stat_statements'     # restart
compute_query_id = auto                             # default
track_io_timing = on                                # default off; adds timing to buffers and pg_stat_io
log_min_duration_statement = '1s'                   # adjust to your latency budget
log_lock_waits = on                                 # default on only from 19
log_temp_files = 0                                  # log every temp file
log_autovacuum_min_duration = '10min'               # default since 15
log_checkpoints = on                                # default since 15
```

Run `pg_test_timing` before enabling `track_io_timing` on unusual hardware; slow clocks make it expensive. On 19, `timing_clock_source` controls the clock.

Sample into your monitoring system every 10 to 60 seconds: `pg_stat_database`, `pg_stat_statements`, `pg_stat_activity` (counts by state and wait event), `pg_stat_replication`, `pg_replication_slots`, `pg_stat_archiver`, `pg_stat_io` (16+), checkpoint statistics, database and table XID ages. These views are cumulative counters: store deltas.

## Top statements

```sql
SELECT queryid, calls,
       round(total_exec_time::numeric, 0) AS total_ms,
       round(mean_exec_time::numeric, 2) AS mean_ms,
       rows, shared_blks_hit, shared_blks_read, temp_blks_written,
       left(query, 100) AS query
FROM pg_stat_statements
ORDER BY total_exec_time DESC LIMIT 20;
```

- Column names: 17+ uses `shared_blk_read_time`/`shared_blk_write_time` (14 to 16: `blk_read_time`/`blk_write_time`). 18 adds `wal_buffers_full`, `parallel_workers_to_launch`, `parallel_workers_launched`; 19 adds `generic_plan_calls`, `custom_plan_calls` (container).
- `pg_stat_statements.track = top` (default) ignores statements inside functions; set `all` to see them.
- `pg_stat_statements.max` (default 5000) entries; churn from unparameterized SQL evicts entries. 18+ groups `IN (...)` lists of different lengths together.
- Reset to measure an interval: `SELECT pg_stat_statements_reset();` (record `stats_since` on 17+ instead of resetting when several people use the data).

## Wait events

```sql
SELECT wait_event_type, wait_event, state, count(*)
FROM pg_stat_activity
WHERE backend_type = 'client backend'
GROUP BY 1, 2, 3 ORDER BY 4 DESC;
```

| `wait_event_type` | Typical events | Meaning and next step |
| --- | --- | --- |
| (null) with `state = active` | — | running on CPU; check top statements and plans |
| `Lock` | `relation`, `transactionid`, `tuple` | heavyweight lock waits; find the blocker ([transactions-and-locking.md](transactions-and-locking.md#find-blockers)) |
| `LWLock` | `WALWrite`, `BufferMapping`, `LockManager`, SLRU locks | internal contention; `LockManager` with many partitions or relations per query, SLRU with many subtransactions or multixacts |
| `IO` | `DataFileRead`, `WalSync`, `WalWrite` | storage latency or too much data read; check `pg_stat_io` and plans |
| `Client` | `ClientRead` | waiting for the application; with `idle in transaction` it holds locks |
| `IPC` | `SyncRep` | commits waiting for a synchronous standby |
| `BufferPin` (14 to 18) / `Buffer` (19) | `BufferPin` / `BufferCleanup` | vacuum waiting for a pinned page; on 19 also `BufferShared`, `BufferExclusive` |
| `Extension` | — | extension-defined waits; on RDS Multi-AZ DB clusters, flow control throttling shows here |

17+: `SELECT * FROM pg_wait_events WHERE name = 'WalSync';` gives the description.

## Triage: "the database is slow"

1. Is it the database? Compare application latency with `pg_stat_statements` mean times for the same calls; check connection counts against `max_connections` and pooler queues.
2. What are sessions doing now? Wait-event breakdown above; count `idle in transaction`.
3. Blocking? `pg_blocking_pids` query; long `xact_start`.
4. Which statements changed? Diff `pg_stat_statements` snapshots: calls, mean time, `shared_blks_read`, `temp_blks_written`. A plan change shows as a jump in buffers per call.
5. Resource saturation? CPU and I/O from the OS (or managed metrics); `pg_stat_io` reads and `read_time` (with `track_io_timing`); checkpoint frequency; WAL rate from `pg_stat_wal`.
6. Maintenance or replication? Running autovacuum or index builds (`pg_stat_progress_*`), synchronous replication waits (`SyncRep`), replication slots retaining WAL (disk).
7. Fix the specific cause, then verify by comparing the same metrics.

## I/O and cache

```sql
SELECT datname, blks_hit, blks_read,
       round(100.0 * blks_hit / nullif(blks_hit + blks_read, 0), 2) AS hit_pct,
       temp_files, pg_size_pretty(temp_bytes) AS temp, deadlocks, conflicts
FROM pg_stat_database WHERE datname IS NOT NULL;

-- 16+: who reads from disk
SELECT backend_type, object, context, reads, read_time, writes, write_time, evictions
FROM pg_stat_io WHERE reads > 0 OR writes > 0 ORDER BY reads DESC;
```

A hit percentage on its own says little; a drop compared with the baseline, or `client backend` writes with high `evictions` in `pg_stat_io` (backends writing dirty pages themselves), are actionable: raise `shared_buffers`, tune the background writer, or reduce the data touched.

## Checkpoints and WAL

```sql
-- 17+
SELECT num_timed, num_requested, write_time, sync_time, buffers_written FROM pg_stat_checkpointer;
-- 14 to 16
SELECT checkpoints_timed, checkpoints_req, checkpoint_write_time, checkpoint_sync_time FROM pg_stat_bgwriter;
SELECT wal_records, wal_fpi, wal_bytes, wal_buffers_full FROM pg_stat_wal;
```

Many requested checkpoints: raise `max_wal_size`. High `wal_fpi` relative to records: checkpoints too frequent, or random-UUID index inserts. Non-zero growing `wal_buffers_full`: raise `wal_buffers` (default -1 auto-sizes; container shows 512 pages = 4MB).

## Progress views

`pg_stat_progress_vacuum`, `pg_stat_progress_analyze`, `pg_stat_progress_create_index`, `pg_stat_progress_cluster` (19: `pg_stat_progress_repack` also covers `CLUSTER` and `VACUUM FULL`), `pg_stat_progress_basebackup`, `pg_stat_progress_copy` (14+). Join them with `pg_stat_activity` on `pid`.

## Logs

- Slow statements: `log_min_duration_statement`, or sampling with `log_min_duration_sample` and `log_statement_sample_rate`.
- Plans of slow statements: `auto_explain` (see [query-plans.md](query-plans.md#getting-the-plan)).
- Lock waits after `deadlock_timeout`: `log_lock_waits`.
- Temp spills: `log_temp_files`.
- 19: `log_min_messages` per process type, for example `SET log_min_messages = 'warning,autovacuum:info';` (container 19.0 accepts it; `SHOW` returns `warning, autovacuum:info`).

## Health checks to alert on

| Check | Query source | Alert when |
| --- | --- | --- |
| XID age | `age(datfrozenxid)` | above your threshold (for example 500 million) |
| Replication lag | `pg_stat_replication`, `replay_lag` | above the failover RPO |
| Inactive slots | `pg_replication_slots WHERE NOT active` | any, for longer than minutes; retained bytes growing |
| Archiver failures | `pg_stat_archiver.failed_count` | increasing |
| Long transactions | `pg_stat_activity.xact_start` | older than your longest legitimate job |
| Idle in transaction | `state = 'idle in transaction'` | over a few minutes |
| Connection use | `count(*)` vs `max_connections` | above 80% |
| Disk | `pg_wal` and data volume free space | trend toward full |
| Invalid indexes | `pg_index WHERE NOT indisvalid` | any |
| Checksum failures | `pg_stat_database.checksum_failures` | any |
