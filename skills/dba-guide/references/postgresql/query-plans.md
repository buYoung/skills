# Query Plans and Tuning

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)).

## Getting the plan

| Command | Runs the query | Use |
| --- | --- | --- |
| `EXPLAIN query` | no | plan shape and estimates; safe on production |
| `EXPLAIN (ANALYZE, BUFFERS) query` | yes | actual rows, time, and buffer I/O per node. `BUFFERS` is automatic with `ANALYZE` on 18+ |
| `EXPLAIN (ANALYZE, BUFFERS, SETTINGS, WAL, VERBOSE)` | yes | adds non-default planner settings, WAL generated, output columns, query identifier |
| `EXPLAIN (GENERIC_PLAN) query with $1` | no | plan a prepared statement would use without parameter values (16+) |
| `EXPLAIN (ANALYZE, SERIALIZE)` | yes | include the cost of converting rows for the client (17+) |
| `EXPLAIN (MEMORY)` | optional | planner memory (17+) |
| `EXPLAIN (ANALYZE, IO)` | yes | asynchronous I/O activity (19) |
| `EXPLAIN (FORMAT JSON)` | either | machine-readable; use for tools and diffs |

Production safety: `EXPLAIN ANALYZE` executes the statement. For `INSERT`/`UPDATE`/`DELETE`/`MERGE`, wrap it:

```sql
BEGIN;
EXPLAIN (ANALYZE, BUFFERS) UPDATE orders SET status = 'paid' WHERE id = 5;
ROLLBACK;
```

The rollback undoes the data change but not side effects such as sequence increments, and the statement still takes its row locks for the duration.

Capture plans of slow statements automatically with `auto_explain` (contrib): `shared_preload_libraries = 'auto_explain'` (or `session_preload_libraries`), `auto_explain.log_min_duration = '500ms'`, `auto_explain.log_analyze = on`, `auto_explain.log_buffers = on`. `log_analyze` adds timing overhead to every query; set `auto_explain.log_timing = off` if overhead matters, and sample with `auto_explain.sample_rate`.

## Reading a plan

Container output, 18.7, table of 200,000 rows with index `(customer_id, created_at)`:

```
Limit  (cost=0.42..36.38 rows=10 width=29) (actual time=0.040..0.051 rows=10.00 loops=1)
  Buffers: shared hit=10 read=3
  ->  Index Scan Backward using ix_cust_created on orders  (cost=0.42..1435.39 rows=399 width=29) (actual time=0.028..0.038 rows=10.00 loops=1)
        Index Cond: (customer_id = 42)
        Index Searches: 1
        Buffers: shared hit=10 read=3
Planning Time: 0.037 ms
Execution Time: 0.057 ms
```

| Field | Meaning | What to check |
| --- | --- | --- |
| `cost=a..b` | startup and total cost in planner units | compare alternatives only within one query |
| `rows=` (estimate) vs `actual ... rows=` | estimated vs real rows per loop | a mismatch of 10x or more at a node is the usual root cause |
| `loops=` | executions of the node | actual totals are `rows * loops` and `time * loops` |
| `Buffers: shared hit/read/dirtied/written` | 8kB pages from shared buffers vs read from the OS | high `read` means cold cache or too much data touched |
| `temp read/written` | spill to temp files | sort or hash exceeded `work_mem` |
| `Rows Removed by Filter` | rows read then discarded | a large value means an index or better predicate is missing |
| `Heap Fetches` (Index Only Scan) | heap visits needed because pages are not all-visible | high values mean vacuum is behind on the visibility map |
| `Index Searches` (18+) | index descents per scan | more than 1 indicates skip scan or `IN`-list array lookups |
| `Sort Method: external merge  Disk: ...` | sort spilled | raise `work_mem` for that query or add an ordering index |
| `Batches: N` (Hash, HashAggregate) | hash spilled when N > 1 | raise `work_mem` or `hash_mem_multiplier` |
| `Workers Planned/Launched` | parallel query | Launched < Planned means `max_parallel_workers` or `max_worker_processes` exhausted |
| `Disabled: true` / `Disabled Nodes` (18+) | node chosen despite `enable_*=off` | a forced setting is in effect; check `SETTINGS` |
| `JIT:` block | JIT compilation time | on 14 to 18 JIT is on by default and can add hundreds of ms to medium queries; see below |

Format differences: 18+ prints fractional `rows=77680.50` for averaged per-loop counts; 14 to 17 print integers. Container confirms both.

## Diagnosis workflow

1. Find the statement: `pg_stat_statements` ordered by `total_exec_time` (see [monitoring.md](monitoring.md#top-statements)). Optimize what costs the most total time, not the slowest single call.
2. Get `EXPLAIN (ANALYZE, BUFFERS, SETTINGS)` with representative parameter values. For prepared statements also look at `GENERIC_PLAN` (16+): after five executions the plan cache may switch to a generic plan whose estimates ignore actual values. `plan_cache_mode = force_custom_plan` for the session tests whether that is the problem.
3. Walk the plan bottom-up and find the first node where estimated and actual rows diverge widely. Fix the estimate before anything else.
4. Then look at where time and buffers concentrate.

## Fixing bad estimates

| Cause | Evidence | Fix |
| --- | --- | --- |
| Stale statistics | `last_analyze`/`last_autoanalyze` old in `pg_stat_user_tables`, large `n_mod_since_analyze` | `ANALYZE table;` then tune per-table `autovacuum_analyze_scale_factor` |
| Skewed column | `pg_stats.most_common_vals` misses frequent values | `ALTER TABLE t ALTER COLUMN c SET STATISTICS 1000; ANALYZE t;` |
| Correlated columns (city and zip) | product of selectivities far too small | `CREATE STATISTICS s (dependencies, ndistinct, mcv) ON city, zip FROM t; ANALYZE t;` |
| Expression in `WHERE` (`lower(email) = ...`) | default selectivity guesses | expression index (also gathers statistics) or `CREATE STATISTICS ... ON (lower(email)) FROM t` (14+) |
| Partitioned parent never analyzed | autovacuum does not analyze partitioned parents | `ANALYZE parent;` after loads and periodically |
| After major upgrade into 15 to 17 | no statistics at all | `vacuumdb --all --analyze-in-stages`; into 18+ most statistics are carried over |
| Temporary tables | autovacuum cannot see them | `ANALYZE tmp_table;` in the session after filling it |

Inspect statistics:

```sql
SELECT attname, null_frac, n_distinct, most_common_vals, correlation
FROM pg_stats WHERE tablename = 'orders' AND attname IN ('customer_id','status');
```

## Fixing slow nodes

- Seq Scan with a selective filter: add an index that matches the predicate; see [schema-and-indexes.md](schema-and-indexes.md). For multi-column filters, put equality columns first, then the range or sort column.
- Index Scan with many `Heap Fetches` on an index-only candidate: vacuum the table (`VACUUM (VERBOSE) orders;`) so the visibility map is set; container shows `Heap Fetches: 1` after vacuum.
- Nested Loop with a large outer side: usually a row-estimate error on the outer input. Fix the estimate; do not disable nested loops globally.
- Sort or Hash spilling to disk: raise `work_mem` for the session or role running the query (`SET work_mem = '256MB'`), not globally. Each sort or hash node in each parallel worker may use `work_mem` (hash nodes up to `work_mem * hash_mem_multiplier`).
- Many partitions scanned: confirm pruning; the predicate must reference the partition key with a stable expression. Container (`PARTITION BY RANGE (at)`, filter on `at`) shows only `events_2026_01` scanned. Pruning with parameters happens at execution time and shows as `Subplans Removed: N`.
- `OFFSET` pagination: cost grows with the offset; switch to keyset pagination (`WHERE (created_at, id) < ($1, $2) ORDER BY created_at DESC, id DESC LIMIT 50`) with a matching index.
- `NOT IN (subquery)` with nullable columns: rewrite as `NOT EXISTS`. 19 can convert `NOT IN` to an anti-join only when it can prove no NULLs.

## Planner settings

Defaults in containers 14 to 19: `random_page_cost = 4`, `seq_page_cost = 1`, `effective_cache_size = 4GB`, `default_statistics_target = 100`, `max_parallel_workers_per_gather = 2`, `work_mem = 4MB`, `jit_above_cost = 100000`.

- On SSD or NVMe storage with most data cached, `random_page_cost` between 1.1 and 2 often matches reality better than 4 (guideline, not from the documentation; measure). Change it for one session first and compare plans of top queries.
- Set `effective_cache_size` to roughly the memory available for caching (shared buffers plus OS cache). It affects only cost estimates, not allocation.
- `enable_seqscan = off` and similar are diagnostic switches. Use them in a session to see what alternative plan costs, never as a fix in production configuration.
- JIT: default `on` through 18, `off` in 19. On 14 to 18, if OLTP queries show a `JIT:` block with significant `Timing`, set `jit = off` (or raise `jit_above_cost`) for that role or database.
- On 19, `pg_plan_advice` (contrib) can pin specific planner choices per query when a plan regresses and statistics cannot fix it. Treat as a last resort and record why.

## Verify a fix

- Compare `EXPLAIN (ANALYZE, BUFFERS)` before and after on the same data and parameters; look at buffers as well as time, because time depends on cache state.
- After deploying, reset or snapshot `pg_stat_statements` and compare `mean_exec_time` and `shared_blks_read` for the statement over a comparable period.
- New indexes: confirm use with `SELECT idx_scan, last_idx_scan FROM pg_stat_user_indexes WHERE indexrelname = '...';` (`last_idx_scan` 16+).
- Roll back a planner-setting change with `ALTER ROLE ... RESET param;` or `ALTER SYSTEM RESET param; SELECT pg_reload_conf();`.

## Common mistakes

- Running `EXPLAIN ANALYZE` on a DML statement outside a transaction that is rolled back.
- Testing with literal values when the application sends parameters (different plans after the generic-plan switch).
- Judging by a single warm-cache run.
- Adding an index per slow query without checking write amplification and existing multicolumn indexes.
- Raising global `work_mem` until the server swaps under concurrency.
