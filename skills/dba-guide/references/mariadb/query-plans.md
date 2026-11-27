# MariaDB Query Plans and Tuning

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)). MariaDB's optimizer has diverged from MySQL's: different `EXPLAIN` formats, engine-independent statistics and histograms, a time-based cost model from 11.0, and MySQL-style hints only from 12.0/12.3. Do not apply MySQL 8 plan advice (for example `EXPLAIN ANALYZE`, `FORMAT=TREE`, hash join flags) without checking.

## Getting a Plan

| Statement | What it gives | Runs the query |
| --- | --- | --- |
| `EXPLAIN SELECT ...` | Tabular estimated plan | No |
| `EXPLAIN FORMAT=JSON SELECT ...` | Estimated plan with conditions, `filtered`, and from 11.0 `cost` per table and block | No |
| `ANALYZE SELECT ...` | Tabular plan plus actual `r_rows`, `r_filtered` | Yes |
| `ANALYZE FORMAT=JSON SELECT ...` | Actual loops, rows, time per table (`r_table_time_ms`, `r_other_time_ms`), pages accessed (`r_engine_stats`), filesort details, optimizer time | Yes |
| `SHOW EXPLAIN FOR <conn_id>` / `SHOW ANALYZE [FORMAT=JSON] FOR <conn_id>` | Plan (and live counters) of a statement running in another connection | No (reads the running one) |
| `SET optimizer_trace='enabled=on'; <query>; SELECT * FROM information_schema.OPTIMIZER_TRACE;` | Why a plan was chosen | `EXPLAIN` or the query |

- `SHOW ANALYZE FOR` is a syntax error (ERROR 1064) on 10.6.28; the 10.11-13.0 images accept it. `SHOW EXPLAIN FOR` works on all covered images.
- `EXPLAIN FORMAT=TREE` and MySQL's `EXPLAIN ANALYZE` do not exist: `ERROR 1791 (HY000): Unknown EXPLAIN format name: 'TREE'` (all covered images).
- `ANALYZE` executes the statement, including `UPDATE`/`DELETE`. Run `ANALYZE UPDATE ...` only inside a transaction you roll back, or on a copy.
- `ANALYZE FORMAT=JSON` is the main tool: compare `rows` (estimate) with `r_rows` (actual per loop) and `filtered` with `r_filtered`. A large mismatch means bad statistics or a non-sargable predicate.

Example (13.0.2 image, 50,000-row `orders` table, index `ix_cust_created (customer_id, created_at)`):

```sql
ANALYZE SELECT * FROM orders WHERE customer_id = 42 ORDER BY created_at DESC LIMIT 10;
-- type=ref key=ix_cust_created rows=100 r_rows=10.00 filtered=100 r_filtered=100 Extra=Using where
```

`rows=100` is the estimate for `customer_id=42`; `r_rows=10` shows the `LIMIT` stopped after 10 rows read backward on the index, and no `Using filesort` appears because the index order satisfies `ORDER BY created_at DESC`.

```sql
ANALYZE FORMAT=JSON SELECT status, COUNT(*) FROM orders WHERE created_at >= '2026-01-10' GROUP BY status;
```

Relevant fields from the same run: `"access_type": "ALL"`, `"rows": 50000`, `"r_rows": 50000`, `"filtered": 73.99`, `"r_filtered": 74.08`, `"r_engine_stats": {"pages_accessed": 157}`, `"filesort": {... "temporary_table": ...}`. Reading: a full scan keeping three quarters of the rows; an index on `created_at` alone would not help much at 74% selectivity, while `(created_at, status)` makes the query index-only. The `"cost"` fields appear on 11.4 and later; 10.6 and 10.11 output has none.

## Access Types and Extra Flags

| `type` | Meaning | Usually |
| --- | --- | --- |
| `const` / `eq_ref` | One row by primary or unique key | Ideal |
| `ref` | Non-unique index equality | Good when selective |
| `range` | Index range | Good; check `rows` |
| `index_merge` | Several indexes combined | Often a sign a composite index is missing |
| `index` | Full index scan | OK only when covering and small |
| `ALL` | Full table scan | Investigate unless the table is small or most rows qualify |

`Extra` to watch: `Using filesort` (sort not satisfied by an index), `Using temporary` (temporary table for `GROUP BY`/`DISTINCT`), `Using index` (covering; from 11.0 not reported for scans of the clustered primary key), `Using index condition` (ICP), `Using where` (filter after reading), `Rowid-ordered scan`, `Using join buffer (...)`, `Using rowid filter`.

## Statistics

MariaDB has two statistics sources:

1. InnoDB persistent statistics (`innodb_stats_persistent=ON`, `innodb_stats_auto_recalc=ON`, 20 sample pages). Cheap, index cardinality only.
2. Engine-independent statistics (EITS) in `mysql.table_stats`, `mysql.column_stats`, `mysql.index_stats`, including histograms. Used because `use_stat_tables=PREFERABLY_FOR_QUERIES` (default in all images) and `optimizer_use_condition_selectivity=4`. They are not collected automatically.

```sql
ANALYZE TABLE orders;                                   -- InnoDB statistics
ANALYZE TABLE orders PERSISTENT FOR ALL;                -- EITS for all columns and indexes (full scan)
ANALYZE TABLE orders PERSISTENT FOR COLUMNS (status, created_at) INDEXES ();
SELECT * FROM mysql.column_stats WHERE table_name = 'orders'\G
```

- `PERSISTENT FOR ALL` reads the whole table (`analyze_sample_percentage`, default 100). On large tables, collect for selected columns, lower `analyze_sample_percentage` (for example 10) for the session, and run it off-peak or on a replica.
- Histogram type: `histogram_type=JSON_HB` in the 11.4, 11.8, 12.3 and 13.0 images; `DOUBLE_PREC_HB` on 10.6 and 10.11. `histogram_size=254`. JSON histograms (available from 10.8) are more precise for skewed data; on 10.11 set `histogram_type=JSON_HB` in the session before `ANALYZE`.
- Stale EITS is worse than none: after bulk loads or large deletes, re-run `ANALYZE ... PERSISTENT FOR` on the affected columns, or delete their rows from `mysql.column_stats`.
- Statistics are per server; replicas and Galera nodes may need their own `ANALYZE`.

## Cost Model (11.0 and later)

From 11.0, costs are in time units (1 = 1 ms of engine work; user-visible costs in microseconds) with engine-specific constants, assuming SSD storage. Several old heuristics were removed (10%-of-rows limit for key lookups, InnoDB 50% range cap, rule-based "aggregate distinct with index"). Consequences:

- Upgrading from 10.x changes plans. Most get better; some regress. Rehearse with production statistics.
- Engine costs are visible in `information_schema.OPTIMIZER_COSTS`; globals such as `optimizer_disk_read_cost` (10.24 µs per 4 KiB block), `optimizer_disk_read_ratio` (0.02, i.e. 98% cache hit assumed), `optimizer_where_cost` (0.032), `optimizer_scan_setup_cost` (10) appear in the 13.0 variable dump.
- When the working set does not fit the buffer pool, tell the optimizer: `SET GLOBAL innodb.optimizer_disk_read_ratio=0.20;` (80% hit), then `FLUSH TABLES` (engine-cost changes apply to newly opened tables only). Engine costs are global; `optimizer_where_cost` and `optimizer_scan_setup_cost` can be per session.
- There is no switch to restore the pre-11.0 model. Use hints (12.3+) or a per-statement `optimizer_switch` for regressions.

## Steering the Optimizer

In order of preference:

1. Fix the index or the predicate (see [schema and indexes](schema-and-indexes.md)).
2. Refresh statistics (above).
3. Per-statement hints:
   - All versions: `FORCE INDEX`, `USE INDEX`, `IGNORE INDEX`, `STRAIGHT_JOIN`.
   - 12.3 (from 12.0 rolling): MySQL-style `/*+ ... */` hints: `JOIN_ORDER`, `JOIN_PREFIX`, `JOIN_SUFFIX`, `JOIN_FIXED_ORDER`, `[NO_]INDEX`, `[NO_]JOIN_INDEX`, `[NO_]GROUP_INDEX`, `[NO_]ORDER_INDEX`, `[NO_]INDEX_MERGE`, `[NO_]ROWID_FILTER`, `NO_RANGE_OPTIMIZATION`, `NO_ICP`, `[NO_]MRR`, `[NO_]BKA`, `[NO_]BNL`, `[NO_]MERGE`, `[NO_]DERIVED_CONDITION_PUSHDOWN`, `[NO_]SPLIT_MATERIALIZED`, `SEMIJOIN`, `SUBQUERY`, `QB_NAME`, `MAX_EXECUTION_TIME(ms)`. 13.0 adds implicit query-block names for views, CTEs and derived tables.
   - Any version: `SET STATEMENT optimizer_switch='rowid_filter=off' FOR SELECT ...` scopes a switch change to one statement.
4. Session `optimizer_switch` or `optimizer_search_depth` for a job.
5. Global `optimizer_switch` changes last, after testing the whole workload.

Example (12.3+):

```sql
SELECT /*+ JOIN_ORDER(c, o) NO_RANGE_OPTIMIZATION(o ix_total) */ c.id, SUM(o.total)
FROM customers c JOIN orders o ON o.customer_id = c.id
WHERE c.region = 'EU' GROUP BY c.id;
```

Default `optimizer_switch` flags that differ across versions (images): `hash_join_cardinality` off on 10.6/10.11, on from 11.4; `cset_narrowing` on from 11.8; `sargable_casefold` from 11.4; `duplicateweedout` and `reorder_outer_joins=off` appear in 12.3/13.0; `engine_condition_pushdown` gone from 11.4; `mrr`, `mrr_cost_based`, `mrr_sort_keys`, `not_null_range_scan`, `index_merge_sort_intersection` off by default.

## Optimizations Worth Knowing

- Index condition pushdown, rowid filters, table elimination, split-materialized derived tables, condition pushdown into derived tables and subqueries are on by default.
- Subquery cache (`subquery_cache=on`) and semi-join strategies; 11.1+ applies semi-join strategies to single-table `UPDATE`/`DELETE`.
- Sargable rewrites: `DATE(col) = const`, `YEAR(col) = const` (11.1+), `UPPER(col) = const` with case-insensitive collations (11.3+, `sargable_casefold`), `SUBSTR(col,1,n) = const` (11.8). On 10.x rewrite such predicates into ranges yourself.
- Indexes on virtual columns can serve matching expressions (11.8) and `GROUP BY`/`ORDER BY` (12.3).
- `in_predicate_conversion_threshold=1000`: long `IN (...)` lists become a derived-table join; check plans for very long lists.
- `eq_range_index_dive_limit=200`: above that many equality ranges, estimates come from statistics instead of index dives.

## Workflow for a Slow Query

1. Get the statement and its frequency from the slow log or Performance Schema digests (see [monitoring](monitoring.md)).
2. `ANALYZE FORMAT=JSON` it on a replica or copy. Locate the table with the most `r_table_time_ms` or `pages_accessed`.
3. Compare estimates with actuals. Mismatch → statistics; match but many rows read → index or rewrite.
4. Test an added index on a copy first and compare `ANALYZE` output. To test removing an index, mark it `IGNORED` (`ALTER TABLE t ALTER INDEX ix IGNORED`; revert with `NOT IGNORED`) instead of dropping it; the index stays maintained, so reverting is instant.
5. Verify after deploy: the digest's average latency and rows examined drop; `Handler_read_rnd_next` grows more slowly.
