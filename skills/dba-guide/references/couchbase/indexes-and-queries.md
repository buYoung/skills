# Couchbase Indexes and SQL++ Queries

Checked: 2026-11-27 (sources at the end). Applies to Couchbase Server 7.2–8.0. Query monitoring keyspaces are in [monitoring.md](monitoring.md). Transactions run through SQL++ are in [transactions-and-durability.md](transactions-and-durability.md).

## Contents

- How a SQL++ query executes
- Index types and when to use them
- Creating, building, and placing indexes
- Scan consistency
- Reading EXPLAIN
- Profiling a single request
- ADVISE and the cost-based optimizer
- Hints and prepared statements
- Index maintenance and common mistakes

## How a SQL++ Query Executes

The Query Service (port 8093) parses and plans the statement. It asks the Index Service for qualifying document keys (or for the projected values, when the index covers the query), fetches documents from the Data Service by key, then filters, sorts, and projects. Each step has a cost:

- Index scan: depends on span selectivity and index residency in memory.
- Fetch: one KV get per qualifying key. This is usually the largest cost for `SELECT *`.
- Filter, sort, and group in the Query Service: memory-bound. From 7.6, ORDER BY and GROUP BY spill to disk when they exceed the query memory quota.

Indexes are updated asynchronously from the Data Service. A query sees index state as of its scan consistency, not necessarily the latest write.

## Index Types and When to Use Them

| Type | Syntax sketch | Use when | Cost or caveat |
|---|---|---|---|
| Composite secondary | `CREATE INDEX ix ON app.inv.orders(customerId, createdAt DESC)` | Equality predicates on leading keys, then range or sort keys | The leading key must appear in the predicate, or the index is not chosen. Documents missing the leading key are not indexed unless `INCLUDE MISSING`. |
| Partial | `... ON app.inv.orders(createdAt) WHERE status = "new"` | A frequent query targets a stable subset | The query predicate must imply the index `WHERE` clause. |
| Covering | Any index holding every field the query references | Hot read paths | No Fetch step. Check `covers` in the plan. Wider indexes use more memory and disk. |
| Array | `... ON c(DISTINCT ARRAY t FOR t IN tags END)` | Predicates of the form `ANY t IN tags SATISFIES t = $v END` or `UNNEST` | The query's `ANY ... SATISFIES` expression must match the index expression. |
| Functional | `... ON c(LOWER(email))` | Predicates on an expression | The query must use the identical expression. |
| `INCLUDE MISSING` leading key | `... ON airport(district INCLUDE MISSING, name)` | Queries that must find documents lacking the leading field | Allowed on the leading key only (non-vector). |
| Partitioned (EE) | `... PARTITION BY HASH(META().id)` | Very large indexes, or aggregates scanned in parallel | Inference, not stated in the documentation: a scan that cannot be narrowed by the partition key contacts every partition. |
| Primary | `CREATE PRIMARY INDEX ON c` | Development, ad-hoc exploration | Full keyspace scan. Avoid in production. |
| Sequential scan (7.6+) | No index. The planner shows `"index":"#sequentialscan"` | Small collections, admin one-offs | Needs role `query_use_sequential_scans` (admins already have it). Scans every document. |
| Vector (8.0) | `CREATE VECTOR INDEX` (Hyperscale), or a vector key in `CREATE INDEX` (Composite) | Similarity search with `APPROX_VECTOR_DISTANCE` | Codebook training samples the data. Batch builds of several vector indexes can run the indexer out of memory (MB-68626). |

Index storage mode is cluster-wide. Both containers report `"storageMode":"plasma"` (Standard GSI) after `cluster-init --index-storage-setting default`. Memory-optimized GSI is Enterprise-only: the `community-8.0.2` container rejected `cluster-init --index-storage-setting memopt` ("memopt option for --index-storage-setting can only be configured on enterprise edition") and accepts only `forestdb` as `storageMode`. Index replication and partitioning are Enterprise-only.

## Creating, Building, and Placing Indexes

`CREATE INDEX` starts a background task. It returns once the definition exists, and the build starts unless deferred. If the connection drops, the build continues. On the 5000-document test collection, both containers' `CREATE INDEX` responses already reported `"state":"online"` (7.6.13 took 2.66 s, 8.0.4 0.43 s). On large collections, poll `system:indexes` instead of relying on the response.

Building reads the whole keyspace, so batch builds:

```sql
CREATE INDEX ix_cust_created ON app.inv.orders(customerId, createdAt DESC)
  WITH {"defer_build": true};
CREATE INDEX ix_status ON app.inv.orders(status) WITH {"defer_build": true};
BUILD INDEX ON app.inv.orders(ix_cust_created, ix_status);
-- watch until both are online
SELECT name, state FROM system:indexes
WHERE bucket_id = "app" AND scope_id = "inv" AND keyspace_id = "orders";
```

In 7.6.2 and later, the default for `defer_build` can be changed with the indexer setting `indexer.settings.defer_build`. 8.0.4 shows `"deferBuild":false` in `GET /settings/indexes`.

Replicas (Enterprise Edition):

- `WITH {"num_replica": 1}` places one replica on another Index node. The replica count must be lower than the number of Index nodes, or lower than the length of a `nodes` list, or creation fails.
- `WITH {"nodes": ["n1:8091","n2:8091"]}` alone places the index on one node and a replica on each of the others.
- Cluster default for new indexes: `POST /settings/indexes -d numReplica=1`. Containers show `"numReplica":0`, so new indexes have no replica unless you ask. An explicit `num_replica` in the statement overrides the default.
- Replicas serve scans with load balancing, and keep the index available when an Index node fails. Without a replica, an index on a lost node is gone until rebuilt.
- Community Edition has no replicas. Create identically defined indexes with different names on different nodes using `nodes`.

Partitioned index sketch (EE):

```sql
CREATE INDEX ix_ord_part ON app.inv.orders(customerId, createdAt)
  PARTITION BY HASH(META().id) WITH {"num_partition": 8, "num_replica": 1};
```

Both containers accepted `WITH {"num_partition": 8}`. `system:indexes` then showed ``"partition":"HASH((meta().`id`))"``, and `GET :8091/indexStatus` showed `"partitioned":true,"numPartition":8`.

Production safety:

- Do not create or drop indexes while any Index node is down. Doing so can produce duplicate index names.
- A build reads the whole collection and competes with the workload. Build during low traffic, or defer and build in one batch.
- To replace an index without a plan gap, create the new one, verify that `EXPLAIN` picks it, then drop the old one. Prepared statements keep their plan until reprepared; see Hints and Prepared Statements.

## Scan Consistency

Set per request (`scan_consistency`) or in cbq (`\SET -scan_consistency "request_plus";`).

| Value | Meaning | Use |
|---|---|---|
| `not_bounded` (default) | Scan whatever the index holds now | Most reads. May miss very recent writes. |
| `at_plus` | Wait until the index has caught up to the timestamp of the last update (as supplied with the request) | Read-your-own-writes without waiting for all writes |
| `request_plus` | Wait until the index includes all mutations up to the request time | Correctness checks, reads after a bulk load, statements inside transactions (the default there) |
| `statement_plus` | Like `request_plus`, but each statement in the request gets its own current timestamp | Multi-statement work that needs each statement current |

Evidence: on 7.6.13, a `COUNT(*)` issued right after a 5000-document `INSERT ... SELECT` returned 3354 at default consistency, while 8.0.4 returned 5000. The difference is timing, not a version guarantee. After a Data failover, `request_plus` scans wait for a consistent index snapshot; `not_bounded` scans may briefly return stale rows.

## Reading EXPLAIN

`EXPLAIN <statement>` returns the plan without running it. It needs the same privileges as the statement. Example run on both containers against a collection with no secondary index:

```sql
EXPLAIN SELECT o.* FROM app.inv.orders AS o
WHERE o.customerId = 7 ORDER BY o.createdAt DESC LIMIT 10;
```

Plan before an index existed (abridged): `PrimaryScan3` with `"index":"#sequentialscan","using":"sequentialscan"` → `Fetch` → `Filter ((o.customerId) = 7)` → `InitialProject` → `Order` (sort_terms createdAt desc, `"limit":"10"`) → `Limit`.

After `CREATE INDEX ix_cust_created ON app.inv.orders(customerId, createdAt DESC)` (abridged from the 8.0.4 output; 7.6.13 is the same shape):

```json
{"cardinality":10,"cost":41.08,
 "plan":{"~children":[{"~children":[
   {"#operator":"IndexScan3","index":"ix_cust_created","using":"gsi",
    "spans":[{"exact":true,"range":[{"index_key":"`customerId`","low":"7","high":"7","inclusion":3}]}],
    "index_order":[{"desc":true,"keypos":1}],"limit":"10",
    "optimizer_estimates":{"cardinality":10,"cost":16.25}},
   {"#operator":"Fetch"}, {"#operator":"Filter"}, {"#operator":"InitialProject"}]},
  {"#operator":"Limit","expr":"10"}]}}
```

How to read it:

| Signal | Meaning | Action |
|---|---|---|
| `PrimaryScan3`, or `"index":"#sequentialscan"` | No usable secondary index; every document is read | Add an index whose leading key is in the predicate (`ADVISE` helps). |
| `IndexScan3` with `spans` | Index chosen. `low` and `high` bound the scan. The equality predicate above produced `inclusion` 3 (read as both bounds inclusive; inference) | Check that the span is narrow. A span with no bounds on the leading key means a full index scan. |
| `"exact": true` on a span | The span matches the predicate exactly (interpretation) | — |
| `index_order` present and no `Order` operator | ORDER BY is served by index order (container: `Order` disappears once the index exists) | Keep the index key order and direction matching the ORDER BY. |
| `"limit"` (or `"offset"`) inside `IndexScan3` | LIMIT/OFFSET pushed into the index scan | If absent, the Query Service reads all qualifying rows before limiting. |
| `covers` in `IndexScan3` and no `Fetch` | Covering index (container profile: `covers` listed, no Fetch) | Best case for hot reads |
| `Fetch` after the scan | One KV get per row | Narrow the projection or make the index covering. |
| `UnionScan` (OR across two indexed fields, both containers), `IntersectScan` (AND across two indexes; 8.0.4 produced it only with `use_cbo=false`, and the CBO chose a single index) | Several indexes combined | Often one composite index would serve better. |
| `NestedLoopJoin`, `HashJoin` | Join method | Index the inner side's join key for nested loop. |
| `optimizer_estimates`, top-level `cost` and `cardinality` | CBO produced the plan | Missing estimates mean rules-based planning (CBO off, Community Edition, or no statistics). Neither container showed estimates before the index existed. |

## Profiling a Single Request

Run the statement with `profile=timings` (request parameter, cbq `\SET -profile "timings";`, or the Workbench). The response adds:

- `phaseTimes`: time per phase (`parse`, `plan`, `indexScan.GSI`, `fetch`, `filter`, and others). The 8.0.4 container run spent 3.36 ms of 4.2 ms in `indexScan.GSI`.
- `phaseCounts`: rows per phase. A large gap between `indexScan` and the rows returned means the index is not selective enough, or the filter runs after the fetch.
- `executionTimings`: the plan annotated per operator with `#itemsIn`, `#itemsOut`, `execTime`, `kernTime`, and `servTime`.
- Top-level `cpuTime` on both versions. 8.0.4 also showed `ioTime` and `waitTime` there.

Reading rule (interpretation of the field names): high `servTime` on `IndexScan3` points to the indexer (residency, CPU, span width). High `servTime` on `Fetch` points to KV latency or disk fetches. High `kernTime` means the operator waited on its neighbors in the pipeline.

## ADVISE and the Cost-Based Optimizer

`ADVISE <SELECT|UPDATE|DELETE|MERGE statement>` returns current and recommended indexes and creates nothing. Container output (identical on both versions) for the statement above:

```json
{"recommended_indexes":{"indexes":[
  {"index_statement":"CREATE INDEX adv_customerId_createdAtDESC ON `default`:`app`.`inv`.`orders`(`customerId`,`createdAt` DESC)",
   "index_property":"ORDER pushdown, LIMIT pushdown"},
  {"index_statement":"CREATE INDEX adv_customerId ON `default`:`app`.`inv`.`orders`(`customerId`)",
   "recommending_rule":"Index keys follow order of predicate types: 2. equality/null/missing."}]}}
```

- The first entry is a covering-style recommendation with pushdown properties. Prefer it when the query sorts or limits.
- Names start with `adv_` and are not guaranteed unique. Rename them before creating.
- With CBO statistics present, the advisor uses the CBO first and may add an `update_statistics` statement. Otherwise it falls back to rules, in priority order: UNNEST array, equality/NULL/MISSING, IN, `<=`/BETWEEN/`>=`, `<`/`>`, join filters on the left side, IS NOT NULL/MISSING/VALUED, LIKE `%...`, non-static join predicates, partial index for a document flavor.
- For a whole workload, the `ADVISOR()` function analyzes several statements, for example those collected in `system:completed_requests`. It takes an array of statement strings: `SELECT ADVISOR(["SELECT o.* FROM app.inv.orders AS o WHERE o.status = 'paid'", "SELECT COUNT(*) FROM app.inv.orders WHERE customerId = 3"])` returned one object on both containers, with `current_used_indexes` and `recommended_indexes`. Each entry lists the statements it applies to (with `run_count`), and recommendations carry an `update_statistics` statement.

Cost-based optimizer (Enterprise Edition; on by default):

- Control: request `use_cbo`, node `use-cbo` (container: `true`), cluster `queryUseCBO` (container: `true`).
- Statistics: `UPDATE STATISTICS FOR app.inv.orders(customerId, status);` succeeded on both containers. `ANALYZE` is a synonym. Per-index forms `UPDATE STATISTICS FOR INDEX ix_cust_created ON app.inv.orders` and `UPDATE STATISTICS FOR app.inv.orders INDEX (ix_cust_created)` both succeeded on both containers, as did `ANALYZE INDEX ix_cust_created ON app.inv.orders`, `ANALYZE COLLECTION app.inv.orders(customerId)`, and `ANALYZE app.inv.orders(customerId)`. From 7.6, statistics are also gathered when an index is created or built. 8.0 adds Auto Update Statistics (opt-in, EE).
- On 7.6+ statistics live in `_system._query`. Flushing the bucket deletes them; rerun `UPDATE STATISTICS` afterwards.
- If statistics are missing for any step, the planner falls back to rules for the plan.
- Refresh statistics after bulk loads or large distribution changes, then compare `EXPLAIN` before and after.

## Hints and Prepared Statements

- Force an index: `SELECT ... FROM app.inv.orders AS o USE INDEX (ix_cust_created USING GSI) WHERE ...`, or the optimizer-hint comment form `SELECT /*+ INDEX(o ix_cust_created) */ ...`. Both containers followed it, and `EXPLAIN` reports ``"optimizer_hints":{"hints_followed":["INDEX(`o` `ix_cust_created`)"]}``. 8.0 What's New lists the negative hints `NO_INDEX`, `NO_INDEX_FTS`, `NO_USE_NL`, `NO_USE_HASH` as new, and allows hints in `UPDATE`, `DELETE`, and `MERGE`. The 7.6.13 container also accepted `/*+ NO_INDEX(o ix_cust_created) */`: it reported the hint under `hints_followed` and planned a sequential scan, as 8.0.4 did.
- Bypass the indexer for known keys: `SELECT ... FROM c USE KEYS ["order::1","order::2"]`.
- Prepared statements: `PREPARE p1 AS SELECT ...`, then `EXECUTE p1`. Inspect them with `SELECT *, meta().plan FROM system:prepareds;` and remove them with `DELETE FROM system:prepareds WHERE name = "p1";`. A prepared plan does not pick up a new index by itself. Auto-reprepare is opt-in in 7.6.10+ (feature-control bit 0x800000) and a feature in 8.0. Otherwise delete the prepared statement and prepare it again after index changes. Containers show `"auto-prepare":false` and `"prepared-limit":16384`.

## Index Maintenance and Common Mistakes

Maintenance facts (container defaults on 7.6.13 and 8.0.4):

- Index compaction mode `circular`, fragmentation threshold 30%. Data fragmentation thresholds: Magma 50%, Couchstore 30%.
- The Index Service memory quota is cluster-wide per node (container `indexMemoryQuota` 256 MiB). When index residency falls, scans read from disk. 7.2+ can alert on low Index residency.
- Two index snapshots are kept on disk by default (`maxRollbackPoints` 2 in the containers).

Mistakes and fixes:

- Production queries relying on a primary index or sequential scan. Fix: `ADVISE`, then a composite or partial index.
- Leading index key not in the predicate, for example an index on `(status, customerId)` for `WHERE customerId = 7`. Fix: reorder keys, putting equality keys first, then range, then sort.
- `SELECT *` on large documents where three fields would do. Fix: project the fields and make the index covering.
- Large `OFFSET` pagination. Fix: keyset pagination on the indexed sort key (`WHERE createdAt < $last ORDER BY createdAt DESC LIMIT 50`).
- `LIKE "%abc"`: cannot use a range span (advisor rule 8 still suggests an index on the field). Consider the Search Service.
- Expecting `not_bounded` reads to see the write just made. Use `at_plus` or `request_plus`.
- Unescaped reserved words in queries against system keyspaces. Both containers rejected a bare `using` column with error 3000. Use backticks.

Verify an index change:

1. `SELECT name, state FROM system:indexes WHERE name = "ix_cust_created";`: `state` must be `online`. 7.6 added replica counts to `system:indexes`. Both containers report them as `metadata.num_replica`, and a top-level `num_replica` column comes back empty. 8.0.4 also shows `with.num_replica` and `with.num_partition`.
2. `EXPLAIN` shows `IndexScan3` on the new index, with the expected spans and pushdowns.
3. `profile=timings` on a representative request shows lower `servTime` and smaller `phaseCounts`.
4. `system:completed_requests` stops listing the statement above the threshold (1000 ms by default).

Rollback: drop the new index, or keep both and force the old one with `USE INDEX` while you investigate. Never drop the only index serving a hot path before its replacement is `online`, because a rebuild is a full scan.

Sources: CREATE INDEX (https://docs.couchbase.com/server/current/n1ql/n1ql-language-reference/createindex.html), Index Replication (https://docs.couchbase.com/server/current/indexes/index-replication.html), EXPLAIN (https://docs.couchbase.com/server/current/n1ql/n1ql-language-reference/explain.html), ADVISE (https://docs.couchbase.com/server/current/n1ql/n1ql-language-reference/advise.html), ADVISOR (https://docs.couchbase.com/server/current/n1ql/n1ql-language-reference/advisor.html), Cost-Based Optimizer (https://docs.couchbase.com/server/current/n1ql/n1ql-language-reference/cost-based-optimizer.html), Update Statistics for Index Expressions (https://docs.couchbase.com/server/current/n1ql/n1ql-language-reference/statistics-expressions.html), Manage and Monitor Queries (https://docs.couchbase.com/server/current/n1ql/n1ql-manage/monitoring-n1ql-query.html), Scopes and Collections (`_system._query`), What's New 7.6 and 8.0, Release Notes 7.6 and 8.0, container outputs for 7.6.13 and 8.0.4, all checked 2026-11-27.
