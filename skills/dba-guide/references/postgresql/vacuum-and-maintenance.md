# Vacuum, Wraparound, Bloat, and Maintenance

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)).

Vacuum removes dead row versions, keeps the visibility map current for index-only scans, freezes old transaction IDs before wraparound, and (with `ANALYZE`) refreshes statistics. Autovacuum does this automatically; most problems come from autovacuum being blocked or too slow, not from it being off.

## What autovacuum does and when

A table is vacuumed when one of these holds (19 docs; formula shape the same on 14 to 19 except the cap, which is 18+):

- dead tuples since last vacuum > `min(autovacuum_vacuum_max_threshold, autovacuum_vacuum_threshold + autovacuum_vacuum_scale_factor * reltuples)`;
- inserted tuples since last vacuum > insert threshold (`autovacuum_vacuum_insert_threshold` + `autovacuum_vacuum_insert_scale_factor` * reltuples, adjusted for the unfrozen fraction in recent versions);
- `age(relfrozenxid)` > `autovacuum_freeze_max_age`, or multixact age > `autovacuum_multixact_freeze_max_age`: an anti-wraparound vacuum, which runs even with `autovacuum = off` and is not cancelled by conflicting lock requests.

Analyze runs when inserted + updated + deleted tuples since last analyze > `autovacuum_analyze_threshold + autovacuum_analyze_scale_factor * reltuples`.

Defaults (container 19.0; same on 18 except where noted): `autovacuum_vacuum_threshold = 50`, `autovacuum_vacuum_scale_factor = 0.2`, `autovacuum_vacuum_max_threshold = 100000000` (18+), `autovacuum_vacuum_insert_threshold = 1000`, `autovacuum_vacuum_insert_scale_factor = 0.2`, `autovacuum_analyze_threshold = 50`, `autovacuum_analyze_scale_factor = 0.1`, `autovacuum_freeze_max_age = 200000000`, `autovacuum_multixact_freeze_max_age = 400000000`, `autovacuum_max_workers = 3`, `autovacuum_naptime = 60s`, `autovacuum_vacuum_cost_delay = 2ms`, `autovacuum_vacuum_cost_limit = -1` (uses `vacuum_cost_limit = 200`), `vacuum_freeze_min_age = 50000000`, `vacuum_freeze_table_age = 150000000`, `vacuum_failsafe_age = 1600000000`.

Things autovacuum never does: `VACUUM FULL`; vacuum or analyze of temporary tables; analyze of partitioned parent tables (run `ANALYZE parent;` yourself); analyze of foreign tables.

## Why autovacuum falls behind

| Cause | Evidence | Fix |
| --- | --- | --- |
| Old snapshot holding the horizon | `VACUUM VERBOSE` reports "N are dead but not yet removable"; `removable cutoff ... which was N XIDs old` is large | find the holder (query below) and end it |
| Too few workers | all `autovacuum_max_workers` busy for long periods in `pg_stat_activity` (`backend_type = 'autovacuum worker'`) | raise `autovacuum_max_workers`; on 18+ up to `autovacuum_worker_slots` without restart, before 18 a restart is needed |
| Throttled by cost delay | workers present but slow; `pg_stat_progress_vacuum` advances slowly | raise `autovacuum_vacuum_cost_limit` (for example to 1000 to 2000) or lower `autovacuum_vacuum_cost_delay`; storage must have headroom |
| Large table, scale factor too high | `n_dead_tup` in the millions before a vacuum starts | per-table `ALTER TABLE big SET (autovacuum_vacuum_scale_factor = 0.01, autovacuum_vacuum_threshold = 10000);` (or rely on the 18+ max threshold) |
| Lock conflicts cancel it | log: `canceling autovacuum task`; repeated short runs | stop frequent `LOCK TABLE`, `ALTER`, or manual `ANALYZE` on the table; anti-wraparound runs are not cancelled |
| Insert-only table never frozen early | high `age(relfrozenxid)`, then a sudden large anti-wraparound vacuum | the insert threshold triggers vacuums; lower per-table `autovacuum_freeze_min_age` for append-only tables |
| Parallel vacuum budget (19) | parallel vacuum slower after upgrade | leader and workers now share the cost limit; raise it deliberately |

Find what holds back cleanup:

```sql
-- oldest transactions and snapshots
SELECT pid, usename, state, backend_xid, backend_xmin,
       age(backend_xmin) AS xmin_age, now() - xact_start AS xact_age, left(query, 80)
FROM pg_stat_activity
WHERE backend_xmin IS NOT NULL OR backend_xid IS NOT NULL
ORDER BY greatest(age(backend_xmin), age(backend_xid)) DESC NULLS LAST
LIMIT 10;

-- replication slots holding xmin or catalog_xmin
SELECT slot_name, slot_type, active, age(xmin) AS xmin_age, age(catalog_xmin) AS catalog_xmin_age
FROM pg_replication_slots ORDER BY greatest(age(xmin), age(catalog_xmin)) DESC NULLS LAST;

-- prepared transactions
SELECT gid, prepared, age(transaction) AS xid_age FROM pg_prepared_xacts;
```

A standby with `hot_standby_feedback = on` reports its oldest query snapshot to the primary through its physical slot or connection; long standby queries then show up as the slot's or walsender's `xmin`.

## Watching vacuum

```sql
-- per-table state
SELECT relname, n_live_tup, n_dead_tup, n_mod_since_analyze,
       last_autovacuum, last_autoanalyze, autovacuum_count
FROM pg_stat_user_tables ORDER BY n_dead_tup DESC LIMIT 20;

-- running vacuums
SELECT p.pid, p.relid::regclass, p.phase, p.heap_blks_total, p.heap_blks_scanned,
       p.heap_blks_vacuumed, p.index_vacuum_count
FROM pg_stat_progress_vacuum p;
```

- 18+: `pg_stat_all_tables.total_vacuum_time`, `total_autovacuum_time`, `total_analyze_time`, `total_autoanalyze_time`; `track_cost_delay_timing = on` adds delay time to progress views.
- 19: `pg_stat_progress_vacuum.started_by` (shows `autovacuum_wraparound` for anti-wraparound runs) and `mode`; `pg_stat_autovacuum_scores` shows the priority order autovacuum will use.
- Logging: `log_autovacuum_min_duration` defaults to 10min from 15 (container 18, 19: 600000 ms). Set it to `0` temporarily on a problem table via `ALTER TABLE t SET (log_autovacuum_min_duration = 0);` to see every run. On 19, auto-analyze logging moved to `log_autoanalyze_min_duration`.

Reading `VACUUM (VERBOSE)` (container, 18.7):

```
pages: 0 removed, 1607 remain, 1607 scanned (100.00% of total), 0 eagerly scanned
tuples: 0 removed, 200000 remain, 0 are dead but not yet removable
removable cutoff: 758, which was 0 XIDs old when operation ended
new relfrozenxid: 754, which is 1 XIDs ahead of previous value
visibility map: 1606 pages set all-visible, 0 pages set all-frozen (0 were all-visible)
index scan bypassed: 1 pages from table (0.06% of total) have 1 dead item identifiers
```

"dead but not yet removable" greater than zero means something holds the horizon. "index scan bypassed" means vacuum skipped index cleanup because few dead items existed (14+ `INDEX_CLEANUP auto`). The output format changed in 15 and again in 18 and 19 (19 adds memory usage and parallel-worker lines); 14 prints the older "found N removable, M nonremovable row versions" form.

## Transaction ID wraparound

XIDs are 32-bit and compared modulo 2^32: a row version older than about 2 billion transactions would appear to be in the future. Vacuum freezes old rows to prevent this. The server warns when a database comes within 40 million XIDs of the limit on 14 to 18 and within 100 million on 19, and stops assigning XIDs when fewer than 3 million remain. The error text differs by version, so alert on both forms:

```
-- 17 and later
ERROR:  database is not accepting commands that assign new transaction IDs to avoid wraparound data loss in database "mydb"
HINT:  Execute a database-wide VACUUM in that database.
-- 14 to 16
ERROR:  database is not accepting commands to avoid wraparound data loss in database "mydb"
HINT:  Stop the postmaster and vacuum that database in single-user mode.
```

On 14 to 16, do not follow that hint: the same documentation says stopping the postmaster or entering single-user mode is neither necessary nor desirable. Use the recovery steps below.

Monitor continuously:

```sql
SELECT datname, age(datfrozenxid) AS xid_age, mxid_age(datminmxid) AS mxid_age
FROM pg_database ORDER BY xid_age DESC;

SELECT c.oid::regclass AS table_name,
       greatest(age(c.relfrozenxid), age(t.relfrozenxid)) AS xid_age,
       pg_size_pretty(pg_total_relation_size(c.oid)) AS size
FROM pg_class c LEFT JOIN pg_class t ON c.reltoastrelid = t.oid
WHERE c.relkind IN ('r', 'm')
ORDER BY xid_age DESC LIMIT 20;
```

Alert well before `autovacuum_freeze_max_age` matters: for example warn at 500 million and page at 1 billion (guideline, not from the documentation). `vacuum_failsafe_age` (1.6 billion) makes vacuum skip index work and cost delays to finish freezing quickly.

Recovery when the server already refuses XIDs (19 docs; applies to 14+):

1. Commit or roll back old prepared transactions (`pg_prepared_xacts`).
2. End long-running transactions (`age(backend_xid)` or `age(backend_xmin)` large in `pg_stat_activity`).
3. Drop stale replication slots (`age(xmin)` or `age(catalog_xmin)` large). A replica that still uses a dropped slot must be rebuilt.
4. Run `VACUUM` in the affected database, oldest tables first. Do not use `VACUUM FULL` (it needs an XID) or `VACUUM FREEZE` (more work than needed). Single-user mode is not required and removes safeguards; avoid it.
5. Fix autovacuum configuration afterwards.

### Multixact wraparound

Multixact IDs (shared row locks, foreign-key checks under concurrency) are also 32-bit and need freezing. Monitor `mxid_age(relminmxid)` per table and `mxid_age(datminmxid)` per database. On 19, `pg_get_multixact_stats()` reports multixact counts and member storage size. Replication slots do not hold back multixact cleanup.

## Bloat

Bloat is free space inside table and index files that normal operation will not reuse soon. Plain `VACUUM` makes space reusable within the file but rarely shrinks it (only trailing empty pages, if it can briefly get an exclusive lock and `vacuum_truncate` is on).

Measure:

```sql
CREATE EXTENSION IF NOT EXISTS pgstattuple;
SELECT * FROM pgstattuple_approx('orders');      -- approximate, uses the visibility map
SELECT * FROM pgstatindex('orders_pkey');        -- avg_leaf_density, leaf_fragmentation
```

`pgstattuple()` (exact) reads the whole relation; run it off-peak on large tables.

Decide:

| Situation | Action |
| --- | --- |
| Table bloated but steady-state (space reused) | nothing; tune autovacuum so it stays steady |
| Index bloated | `REINDEX INDEX CONCURRENTLY idx;` (12+; needs disk for a full new index) |
| Table bloated after a one-off mass delete or update | 19: `REPACK (CONCURRENTLY) table;` 14 to 18: `VACUUM FULL` or `CLUSTER` in a maintenance window (both hold `ACCESS EXCLUSIVE` for the whole rewrite) |
| Periodic full-table delete | use `TRUNCATE` or drop partitions instead of `DELETE` |

`REPACK` (19) notes: without `CONCURRENTLY` it holds `ACCESS EXCLUSIVE` throughout. With `CONCURRENTLY` it captures concurrent changes via logical decoding and takes `ACCESS EXCLUSIVE` only to swap files; it ran with `wal_level = replica` and no logical slots in the 19.0 container. It needs a primary key or index-based replica identity, cannot run on partitioned, unlogged, or catalog tables or inside a transaction block, consumes a slot from `max_repack_replication_slots`, needs free disk for a full copy of table and indexes, and is not MVCC-safe for transactions whose snapshot predates it. It counts as one long transaction for the purposes of the xmin horizon on other tables, so monitor `pg_stat_activity.backend_xid` of the repack process. Do not use it to fix wraparound; plain `VACUUM` is faster for that. Progress: `pg_stat_progress_repack`.

Rehearse every rewrite on a restored copy of the table to measure duration and disk use.

## Manual maintenance commands

| Command | Lock | Notes |
| --- | --- | --- |
| `VACUUM (VERBOSE, ANALYZE) t;` | `SHARE UPDATE EXCLUSIVE` | safe online |
| `VACUUM (FREEZE) t;` | same | freezes aggressively; use on static tables after bulk load |
| `VACUUM (INDEX_CLEANUP OFF) t;` | same | emergency: skip index work to advance relfrozenxid faster |
| `VACUUM (PARALLEL 4) t;` | same | parallel index vacuuming; only for tables with 2+ indexes over `min_parallel_index_scan_size` |
| `VACUUM ONLY parent;` (18+) | same | parent without children; `VACUUM (ONLY) parent;` is a syntax error (container 18.7, 19.0) |
| `vacuumdb --all --analyze-in-stages --jobs=4` | per table | fast statistics after restore or upgrade |
| `VACUUM FULL t;` | `ACCESS EXCLUSIVE` | rewrites; production risk |
| `REINDEX INDEX CONCURRENTLY i;` | `SHARE UPDATE EXCLUSIVE` | not in a transaction block |

Verify after a change: re-run the `pg_stat_user_tables` and age queries; `n_dead_tup` should drop and `age(relfrozenxid)` should fall to roughly `vacuum_freeze_min_age` after an aggressive vacuum.

## Common mistakes

- Turning autovacuum off for a table because it "uses I/O"; the table then needs an anti-wraparound vacuum at the worst time.
- Running nightly `VACUUM FULL` jobs.
- Leaving logical replication slots without a consumer; they pin `catalog_xmin` and WAL.
- Forgetting to `ANALYZE` partitioned parents and temporary tables.
- Killing an anti-wraparound autovacuum repeatedly; it restarts and the age keeps growing.
