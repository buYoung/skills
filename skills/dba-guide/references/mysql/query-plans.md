# MySQL Query Plans and Tuning

Checked: 2026-11-27. Applies to MySQL 8.0 through 26.10.

## Find the Statements Worth Tuning

Start from the statement digest table, not from a single slow query someone noticed.

```sql
SELECT DIGEST, LEFT(DIGEST_TEXT, 120) AS stmt, COUNT_STAR,
       ROUND(SUM_TIMER_WAIT/1e12, 2)  AS total_s,
       ROUND(AVG_TIMER_WAIT/1e9, 2)   AS avg_ms,
       SUM_ROWS_EXAMINED, SUM_ROWS_SENT, SUM_NO_INDEX_USED,
       SUM_CREATED_TMP_DISK_TABLES, SUM_SORT_MERGE_PASSES
  FROM performance_schema.events_statements_summary_by_digest
 ORDER BY SUM_TIMER_WAIT DESC LIMIT 15;
-- formatted equivalent
SELECT * FROM sys.statement_analysis ORDER BY total_latency DESC LIMIT 15;
SELECT * FROM sys.statements_with_full_table_scans LIMIT 15;
```

Timer columns are picoseconds. Read the ratio `SUM_ROWS_EXAMINED / SUM_ROWS_SENT`: above roughly 100 for an OLTP statement usually means a missing or unusable index. `SUM_NO_INDEX_USED > 0` marks statements that did a full scan at least once. Rank by total time first (frequency x latency), then by average for user-facing paths. Since 9.5.0 the digest distinguishes statements that differ only in `ORDER BY`.

Get a real example of a digest with its literals (needed for `EXPLAIN`):

```sql
SELECT QUERY_SAMPLE_TEXT, QUERY_SAMPLE_SEEN
  FROM performance_schema.events_statements_summary_by_digest WHERE DIGEST = '<digest>';
```

## EXPLAIN Formats

| Form | Output | Notes |
|---|---|---|
| `EXPLAIN stmt` | Format from `explain_format`: TRADITIONAL in 8.0 and 8.4, TREE from 9.5.0 (containers: 9.7.4, 26.7.0, 26.10.0) | Set `explain_format` per session, or name the format, to keep scripts stable. |
| `EXPLAIN FORMAT=TRADITIONAL` | one row per table access: `type`, `key`, `rows`, `filtered`, `Extra` | Row order is join order. Does not show per-node cost, and shows a hash join only as `Using join buffer (hash join)`. |
| `EXPLAIN FORMAT=TREE` | iterator tree with estimated cost and rows per node | Easiest to read for joins and aggregation (8.0.18+). |
| `EXPLAIN FORMAT=JSON` | version 1 (`query_block` ...) or version 2 (`query_plan`, `inputs`, `operation`) per `explain_json_format_version` | Default 1 in 8.4, 2 from 9.5.0. The variable does not exist in 8.0 (container: error 1193). |
| `EXPLAIN ANALYZE stmt` | tree plus `actual time=first..last rows=N loops=L` per node | Executes the statement. |
| `EXPLAIN ANALYZE FORMAT=JSON INTO @v SELECT ...` | stores the JSON plan in a variable | 9.0.0+, needs JSON format version 2. |
| `EXPLAIN FOR CONNECTION <id>` | plan of a statement running in another session | Needs `PROCESS` for other users' sessions. |

Production safety: `EXPLAIN ANALYZE` runs the statement to completion, with the full cost of a bad plan. Run it on a replica or a restored copy. Do not run `EXPLAIN ANALYZE` on data-changing statements against production data. Plain `EXPLAIN` does not run the statement.

Same query in two formats (container output, 50,000-row table, index `ix_cust_created (customer_id, created_at)`):

```text
-- 8.0.46, EXPLAIN (traditional)
| type | key             | ref   | rows | filtered | Extra               |
| ref  | ix_cust_created | const |  100 |   100.00 | Backward index scan |

-- 26.10.0, EXPLAIN ANALYZE
-> Limit: 10 row(s)  (cost=35 rows=10) (actual time=0.212..0.215 rows=10 loops=1)
    -> Index lookup on orders using ix_cust_created (customer_id = 42) (reverse)  (cost=35 rows=100) (actual time=0.211..0.213 rows=10 loops=1)
```

The tree output prints the condition as `customer_id = 42` on 9.7+ and `customer_id=42` on 8.0. Do not match plan text exactly across versions.

## Reading the Plan

Read the tree from the innermost (most indented) node outward; children feed their parent.

| You see | Meaning | Usual fix |
|---|---|---|
| `Table scan on t` (tree) / `type: ALL` | Every row read | Index the filter, or accept it for small tables and reports. |
| `Index scan on t using ix` / `type: index` | Whole index read in order | Often an `ORDER BY ... LIMIT` without a usable filter. |
| `Index range scan` / `type: range` | Range on an index | Fine when the range is narrow. |
| `Index lookup` / `type: ref`, `eq_ref` | Seek on equality | Expected for joins and point queries. |
| `Covering index ...` / `Extra: Using index` | No row lookup needed | |
| `Filter: (...)` above a scan | Rows read, then discarded | The predicate cannot use an index (function on the column, type or collation mismatch, leading wildcard `LIKE '%x'`). |
| `Sort` / `Using filesort` | Explicit sort | Index matching the `ORDER BY` after the equality prefix. |
| `Aggregate using temporary table` / `Using temporary` | Temporary table for GROUP BY or DISTINCT | Index on the grouping columns; check `Created_tmp_disk_tables`. |
| `Inner hash join` / `Using join buffer (hash join)` | Hash join (8.0.18+), used when no index serves the join condition | Index the join column on the inner table if the join is selective. |
| `Nested loop inner join` with `Index lookup` inside | Index nested-loop join | Normal for OLTP joins. |
| estimated `rows=` far from `actual ... rows=` | Bad statistics or correlated predicates | `ANALYZE TABLE`, histograms on filtered non-indexed columns, then re-check. |
| `loops=N` large on an inner node | Inner side executed N times | Cost = per-loop time x loops. |

In `EXPLAIN ANALYZE`, `actual time=a..b` is milliseconds to the first row and to the last row, averaged per loop.

Container example where a scan is correct (26.10.0, `GROUP BY status` with `WHERE created_at >= '2026-01-10'` and no index led by `created_at`):

```text
-> Table scan on <temporary>  (actual time=13.3..13.3 rows=3 loops=1)
    -> Aggregate using temporary table  (actual time=13.3..13.3 rows=3 loops=1)
        -> Filter: (orders.created_at >= TIMESTAMP'2026-01-10 00:00:00')  (cost=5048 rows=16690) (actual time=1.46..7.93 rows=37041 loops=1)
            -> Table scan on orders  (cost=5048 rows=50076) (actual time=0.0836..5.84 rows=50000 loops=1)
```

The filter estimate (16,690) is off by more than 2x from the actual 37,041 rows. It does not matter here: 74% of the rows match, so a scan is the right plan and an index on `created_at` would not help.

## Why the Optimizer Did Not Use an Index

Check in this order:

1. The predicate is not sargable: `WHERE YEAR(ts) = 2026`, `WHERE col + 1 = 5`, `WHERE varchar_col = 123` (a string column compared with a number converts every row), different collations on the two sides of a join.
2. The index's leading column is not constrained.
3. The optimizer estimates that the range covers a large share of the table and a scan is cheaper. Compare with `FORCE INDEX` under `EXPLAIN ANALYZE` on a copy.
4. Statistics are stale after a bulk load or a large delete: run `ANALYZE TABLE t`. It reads `innodb_stats_persistent_sample_pages` pages per index; read the `ANALYZE TABLE` page of your version for its locking behavior before running it on a hot table during peak.
5. The index is invisible.
6. Large `IN (...)` lists: beyond `eq_range_index_dive_limit` (default 200) the optimizer estimates from index statistics instead of index dives, which can misestimate skewed data.

Optimizer trace for one statement, when the reason is not obvious:

```sql
SET SESSION optimizer_trace = 'enabled=on';
SELECT ...;   -- the statement
SELECT TRACE FROM information_schema.OPTIMIZER_TRACE\G
SET SESSION optimizer_trace = 'enabled=off';
```

Look at `rows_estimation` and `considered_execution_plans` for the cost of each alternative. Since 26.10, values of `optimizer_trace` and `optimizer_switch` must be spelled out exactly (`enabled=on`, not `enabled=o`).

## Steering the Plan

Fix the schema or the query first. When you must steer, use optimizer hints; they apply to one statement and are visible in code review:

```sql
SELECT /*+ INDEX(o ix_cust_created) */ * FROM orders o WHERE customer_id = 42;
SELECT /*+ JOIN_ORDER(c, o) */ ... FROM customers c JOIN orders o ON ...;
SELECT /*+ NO_BNL(p) */ ...;                     -- no hash join into table p (name the inner table)
SELECT /*+ MAX_EXECUTION_TIME(2000) */ ...;      -- SELECT only, milliseconds
SELECT /*+ SET_VAR(sort_buffer_size = 16777216) */ ...;
```

Container check (all five images) on `orders o JOIN orders p IGNORE INDEX (ix_total) ON p.total = o.total WHERE o.customer_id = 1`: the plan is `Inner hash join` with `Using join buffer (hash join)` on `p`; `NO_BNL(p)` turns it into a nested loop, while `NO_BNL(o)` (the build-side table) and `NO_HASH_JOIN(p)` leave the hash join in place. With an index on `p.total` the optimizer already chooses a nested loop with index lookups.

Index hints (`USE INDEX`, `FORCE INDEX`, `IGNORE INDEX`) also work. Hints that name an index stop having an effect when the index is renamed or dropped (`FORCE INDEX` on a missing index raises an error). Record each hint with the reason and the version it was tested on, and re-test after upgrades.

To test the hypergraph optimizer (Community from 9.7.0), set `optimizer_switch='hypergraph_optimizer=on'` in one session and compare `EXPLAIN ANALYZE`. Leave it off globally unless a full regression run passes.

## Plan Regression After an Upgrade

1. Before the upgrade, save `EXPLAIN FORMAT=JSON` for the top 20-50 digests (by total time) using their `QUERY_SAMPLE_TEXT`. Record the JSON format version you used.
2. On the rehearsal copy, run the same statements and compare access types, chosen indexes and join order. Request the format explicitly: the default `explain_format` and JSON version change in 9.5.0.
3. After the switch, compare per-digest latency in `events_statements_summary_by_digest` with the pre-upgrade snapshot. Truncate the table at the switch (`TRUNCATE TABLE performance_schema.events_statements_summary_by_digest`) so the numbers cover only the new version.

## Sources

Checked 2026-11-27: statement runs on the official images (mysql:8.0, 8.4, 9.7, 26.7, 26.10) for EXPLAIN output and `explain_format` defaults; Changes in MySQL 9.5.0 (https://dev.mysql.com/doc/relnotes/mysql/9.7/en/news-9-5-0.html) for TREE and JSON v2 defaults and digest changes; Changes in MySQL 9.0.0 (https://dev.mysql.com/doc/relnotes/mysql/9.7/en/news-9-0-0.html) for `EXPLAIN ANALYZE ... INTO`; Changes in MySQL 9.7.0 (https://dev.mysql.com/doc/relnotes/mysql/9.7/en/news-9-7-0.html) for the hypergraph optimizer in Community; Changes in MySQL 26.10.0 for strict `optimizer_switch` parsing and Note 1003. EXPLAIN semantics, hints and the optimizer trace follow the MySQL 8.4 manual, Optimization chapter (https://dev.mysql.com/doc/refman/8.4/en/optimization.html).
