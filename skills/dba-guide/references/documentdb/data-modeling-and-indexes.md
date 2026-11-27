# Amazon DocumentDB Data Modeling, Indexes, and Query Plans

Checked: 2026-11-27. Read this when you design documents or indexes for DocumentDB, read a DocumentDB `explain()`, or tune a slow query. General document-modeling reasoning (embed or reference, bounded arrays) is the same as for MongoDB; see [../mongodb/data-modeling.md](../mongodb/data-modeling.md). The sections below are limited to the places where DocumentDB's engine changes the decision.

Contents

- [Modeling decisions that differ from MongoDB](#modeling-decisions-that-differ-from-mongodb)
- [Index types and limits](#index-types-and-limits)
- [Building and maintaining indexes](#building-and-maintaining-indexes)
- [Query planners](#query-planners)
- [Reading explain output](#reading-explain-output)
- [Steering the planner](#steering-the-planner)
- [Index usage review](#index-usage-review)
- [Sources](#sources)

## Modeling decisions that differ from MongoDB

| Factor | DocumentDB behavior | Decision |
| --- | --- | --- |
| MVCC versions | Every update writes a new version of the document and of each affected index entry. Old versions stay until garbage collection removes them, and each write consumes an MVCC ID ([GC](https://docs.aws.amazon.com/documentdb/latest/devguide/garbage-collection.html)) | Frequent small updates to large documents cost more than in an in-place engine. Split hot, frequently updated fields into a small document when the rest is large and static |
| Page size and extended storage | Documents that fit in an 8 KB page live in the base segment. Larger ones go to an extended segment with its own GC | Keep frequently read documents under 8 KB where you can. Watch `storageSizeStats.storageSegmentExtended` in `collStats` |
| Billed I/O | Standard storage bills per read and write I/O against the volume | Wide documents fetched only for a few fields cost I/O. Use projections that an index can cover (`IXONLYSCAN`), or I/O-Optimized storage |
| Index maintenance cost | Every index is updated on every write. 8.0 avoids rewriting index entries when indexed values do not change and the document fits its page (April 2026 patch) | Keep only indexes that queries use. Up to 64 per collection |
| TTL | Best-effort deletes that cost I/O, and the TTL monitor is optimized for removing a small fraction of a collection | For high-volume expiry, use time-bucketed collections and drop whole collections. Before you add a TTL index to an existing collection, delete the already-expired documents |
| Bulk deletes | Mass `deleteMany` produces dead versions, a GC burst, and possibly change stream stalls | Prefer dropping a collection. Otherwise batch deletes and watch `AvailableMVCCIds` and `LongestActiveGCRuntime` |
| Compression | 5.0: LZ4, threshold 2,032 bytes, off by default. 8.0: Zstd by default, threshold 128 bytes. Only documents above the threshold are compressed. `collMod` affects only documents written afterward | Enable it for documents larger than a few KB. Expect more CPU on reads that hit the cache. Check `size / storageSize` in `collStats` |
| Schema validation | `$jsonSchema` validators on 4.0 and later, instance-based only. `bypassDocumentValidation` is supported | Use validators instead of application-only checks where you can |
| Limits | 16 MiB documents, 200 nesting levels (100 on elastic), 32 TiB per collection | Same order as MongoDB except the elastic nesting limit |
| Ordering | No natural order. Results without `sort()` can come back in any order | Never depend on insertion order |
| `_id` | Required for retryable inserts (8.0.2 and later) | Generate `_id` client-side for idempotent writes |

Elastic clusters add shard-key constraints: one field only, hash only, chosen before data is loaded and never changeable. Unique indexes are not available, so uniqueness must come from `_id` or from the application. See [compatibility.md](compatibility.md#elastic-clusters).

## Index types and limits

| Type | Syntax | Versions | Notes |
| --- | --- | --- | --- |
| Single field / compound | `createIndex({a: 1, b: -1})` | All | Up to 32 keys. Keys are limited to 2,048 bytes |
| Multikey | automatic on arrays | All | Compound indexes over multiple keys in the same array are supported for index version `v: 3` (indexes created after April 2020). Recreate older indexes to get it |
| Unique | `{unique: true}` | All, not elastic | Unique plus sparse on multikey fields does not enforce uniqueness when an array element lacks the field |
| Sparse | `{sparse: true}` | All | Planner v1 uses it only when the query has `$exists: true` on the field |
| TTL | `{expireAfterSeconds: N}` | All | Change it with `collMod`. Can be combined with a partial filter |
| 2dsphere | `createIndex({loc: "2dsphere"})` | All | 2d indexes and legacy shapes (`$box`, `$center`, `$polygon`) are not supported |
| Partial | `{partialFilterExpression: {...}}` | 5.0 and later, not elastic | Allowed in the filter: `$eq`, `$exists`, top-level `$and`, `$gt`/`$gte`/`$lt`/`$lte`. Not allowed: `$or`, `$not`, `$nor`, `$all`, `$mod`, array values. Can be unique, compound, or TTL. Before upgrading 5.0 to 8.0, check for `$type` in partial filters ([versions/8.0.md](versions/8.0.md#upgrading-into-this-series)) |
| Text | `createIndex({f: "text"})` | 5.0 (v1), 8.0 (v2 for new indexes) | Not elastic. `reIndex` is not supported |
| Vector | `createIndex({emb: "vector"}, {vectorOptions: {type: "hnsw", dimensions: 768, similarity: "cosine", m: 16, efConstruction: 64}})` | 5.0 and later instance-based | Cannot be compound, sparse, or partial. Up to 2,000 indexed dimensions. Some shells reject `vectorOptions` in `createIndex`; use `runCommand({createIndexes: ...})` |
| Wildcard | `createIndex({"$**": 1})` (MongoDB syntax) | 8.0.3 and later | The supported-APIs page gives only the version (8.0.3+). Create the index on a test cluster and read it back with `db.<coll>.getIndexes()` before relying on MongoDB wildcard options such as `wildcardProjection` |
| Case-insensitive (collation) | `createIndex({name: 1}, {collation: {locale: "en", strength: 2}})` | 8.0 | Works under planner v3; `cursor.collation()` is 8.0 only (supported-APIs page). The page lists only "Case Insensitive". Create the index on a test 8.0 cluster and confirm with `explain()` that a query with the same collation uses it |
| Hidden | `collMod` with `hidden` | 8.0.1 and later; 5.0.2 and later per `collMod` table (conflict) | Planner v2 and later |
| Hashed, 2d | not supported | | |

Vector query, 5.0 and later:

```
db.docs.aggregate([{ $search: { vectorSearch: {
  vector: [0.12, 0.33, ...], path: "emb", similarity: "cosine", k: 10, efSearch: 40 } } }])
```

On 8.0 the `$vectorSearch` stage is also accepted (`queryVector`, `path`, `limit`, `numCandidates`, `index`, `exact`). Vector indexes give approximate results. Raising `efSearch` (HNSW) or `probes` (IVFFlat) improves recall at the cost of latency. Without an index the search is exact. Load the data before you build an IVFFlat index, because it trains on the existing data.

## Building and maintaining indexes

- One build per collection at a time. A second `createIndex` or `dropIndex` on the same collection fails while a build runs.
- Foreground is the default, and a foreground build blocks all other operations until it finishes. On a live collection, run:

  ```
  db.runCommand({createIndexes: "orders", indexes: [
    {key: {customerId: 1, orderDate: -1}, name: "cust_date", background: true, workers: 4}]})
  ```

  The index-management page shows `workers` inside the index spec but no `background` example. Check that the build really runs in the background with `db.currentOp({"command.createIndexes": {$exists: true}})`: per that page a background build has eight stages (nine for unique), a foreground build five (six for unique).
- Parallel workers apply to 4.0, 5.0, and 8.0, on 2xlarge and larger instances. The maximum is half the primary's vCPUs, and the default is 2. Workers speed up only the collection-scan stage. They consume CPU and read I/O on the primary, so add them only when the primary has headroom. Elastic clusters do not support parallel builds. On serverless, parallel builds need at least 32 DCUs.
- Progress on 5.0 and later:

  ```
  db.currentOp({"command.createIndexes": {$exists: true}})
  ```

  Read `msg` (stage and percent) and `progress.done`/`progress.total`. A background build has 8 stages (9 if unique), a foreground build 5 (6 if unique). 4.0 does not show `msg` or `progress`.
- Bloat: `db.coll.aggregate([{$indexStats: {}}])` reports `unusedStorageSize.unusedSizePercent` per index. Rebuild an index online with `db.runCommand({reIndex: "orders", index: "cust_date", workers: 4})`. That needs 5.0 or later and does not work for text, geospatial, vector, or partial indexes; 8.0.2 adds partial (conflict noted in [compatibility.md](compatibility.md#documentation-conflicts)). The old index keeps serving queries during the rebuild. `reIndex` cannot run at the same time as `createIndexes`, `dropIndexes`, `collMod`, or `renameCollection` on that collection.
- Dropping an index is immediate and changes plans at once. On 8.0.1 and later, hide the index first, watch the latency metrics, and drop it only if nothing regresses. Rollback: unhide it, or recreate it, which needs a full build.

## Query planners

| Planner | Where | Scope | Notes |
| --- | --- | --- | --- |
| v1 | Default on 3.6, 4.0, 5.0; the only planner on elastic clusters | All commands | `planHint` comment selects the `$lookup` algorithm. Sparse and partial indexes need an exact `$exists` or predicate match. `$regex` index use needs `hint()` by key pattern |
| v2 | 5.0 from patch 3.0.15902 (opt in with `planner_version=2.0`) | `find`, `update`, `delete`, `findAndModify`. Aggregation and `distinct` fall back to v1 | Index use for `$ne`, `$nin`, `$not`, `$type`, nested `$elemMatch`, prefix `$regex` without a hint, and partial or sparse indexes without exact matches. Plan cache filters. Some result differences, see [compatibility.md](compatibility.md#query-and-update-behavior) |
| v3 | 8.0 default | Everything including aggregation and `distinct` | `$match` pushdown, `$lookup`+`$unwind` coalescing, `DISTINCT_SCAN`, `IXONLYSCAN`, incremental sort (8.0.2). Required for views, collation, and `$merge`. `planHint` is not allowed |

Switch planners with the `planner_version` cluster parameter. It is dynamic; choose "Apply immediately". The planner pages warn that error rates can rise while the switch takes effect, so do it in a low-traffic window. Before you switch production, compare `explain("executionStats")` for the top queries on a clone. To roll back, set the previous value. Keep the same value in every Region of a global cluster.

## Reading explain output

```
db.orders.find({customerId: 42}).sort({orderDate: -1}).explain("executionStats")
```

| Field / stage | Meaning | Action |
| --- | --- | --- |
| `queryPlanner.plannerVersion` | Planner used (1, 2, 3) | If it is not the version you expect, check the parameter group and the command type (v2 does not handle aggregation) |
| `COLLSCAN` | Full collection scan | Add or fix an index. For tiny collections the planner may choose a scan on purpose |
| `IXSCAN` with `indexName` | Index scan followed by a fetch | Check that the index is the intended one |
| `IXONLYSCAN` | Covered by the index, no document fetch | Best case. Multi-field covering for `find` and `$group` needs 8.0.2 and later |
| `SORT` | In-memory sort | Add the sort key to the index in the right order |
| `HASH_LOOKUP`, `SORT_LOOKUP`, `NESTED_LOOP_LOOKUP` | `$lookup` algorithm | Nested loop suits a foreign collection under about 1 GB with an index on `foreignField`. Hash suits a foreign collection under about 1 GB that fits in memory. Sort-merge suits no index and data that does not fit in memory |
| `DISTINCT_SCAN` | v3 distinct over a low-cardinality index | |
| `executionStats.docsExamined` (8.0 April 2026 patch, 5.0.1) | Documents read | Compare with returned documents. A high ratio means the index is not selective enough |
| `indexFilterSet` / `indexFilterApplied` | A plan cache filter exists, or was used | `Set: true, Applied: false` means the filter's indexes do not cover the query, do not exist, or the regex is not anchored |
| `serverInfo.version` | Reported API version string | Do not use it to identify the DocumentDB version; use `getEngineVersion` |

Elastic clusters wrap shard plans in `SINGLE_SHARD` or `SHARD_MERGE` and `PARTITION_MERGE` stages, with `elasticPlannerVersion` at the top. A `SHARD_MERGE` across all shards for a query on the shard key means the filter is not an equality on the key.

## Steering the planner

1. `hint()`: `db.c.find(q).hint({a: 1})` or `.hint("a_1")`. With planner v1 and `$regex`, hint by key pattern only. Planner v2 raises an error when the hint names an index that cannot answer the query, such as a non-matching partial index.
2. Plan cache filters (index filters), on planner v2 and later. They are set server-side, so they are the fastest mitigation for a plan regression when you cannot change application code:

   ```
   db.runCommand({planCacheSetFilter: "orders",
     query: {status: "SHIPPED"}, sort: {orderDate: 1},
     indexes: ["status_1_orderDate_1"]})
   db.runCommand({planCacheListFilters: "orders"})
   db.runCommand({planCacheClearFilters: "orders", query: {status: "SHIPPED"}, sort: {orderDate: 1}})
   ```

   - Values are normalized, so the filter applies to every value with that query shape and sort. Each sort, including no sort, is a separate shape.
   - Filters persist across restarts and patching. Dropping the collection removes them. A dropped index is skipped, and becomes eligible again if it is recreated with the same name.
   - A filter overrides a `hint()` that names an index outside the filter.
   - Coverage: `find` and `count` from 5.0.0 and 8.0.0. `update`, `delete`, and `findAndModify` from 5.0.2 and 8.0.2. `distinct` needs v3. `aggregate` (leading `$match` plus `$sort`) and `$lookup` foreign collections need v3 on 8.0.2.
   - Shapes that use `$jsonSchema`, `$expr`, `$sampleRate`, `$regex` inside `$in`/`$nin`/`$all`, or a `{$natural: 1}` sort cannot be filtered (error 303).
   - Confirm a filter with `indexFilterApplied` in explain output. The plan-cache-filter page says filters persist across restarts and patching but not whether they reach replica instances. After setting a filter, run the explain on each instance endpoint that serves the query and look for `indexFilterApplied`.
3. `$lookup` `planHint` (planner v1 only): pass `comment: "{\"lookupStage\": {\"planHint\": \"HASH\"}}"` as an aggregate option. Compare runs with `explain("executionStats")` for `HASH`, `SORT`, and `NESTED_LOOP`.
4. Index selectivity: AWS advises indexing a field for `$regex` only if each value occurs in less than about 1% of documents. Low-cardinality indexes add write and GC cost for little benefit. 5.0 and later handle low-cardinality index maintenance better, which is another reason to `reIndex` after an upgrade from 3.6 or 4.0.

## Index usage review

```
db.orders.stats()                                  // collScans, idxScans, cacheStats, opCounter
db.orders.aggregate([{$indexStats: {}}])           // per index: accesses.ops, cacheStats, unusedStorageSize
```

- `accesses.ops` stays at 0 for an index that queries do not use. These counters reset when the cluster starts or stops and when the instance is scaled, so compare them only over a long enough steady period. Collect them on every instance, because counters are per instance and replicas serve their own reads.
- A high `collScans` count relative to `idxScans` on a large collection points to a missing index. Confirm with the profiler, looking for repeated slow `COLLSCAN` plans.
- Use `cacheStats.collHitRatio` and `idxHitRatio` (`100 * hits / (hits + reads)`) to separate a cache-size problem from a plan problem.

For MongoDB's own explain format and index strategy (ESR ordering and similar), see [../mongodb/indexes-and-query-plans.md](../mongodb/indexes-and-query-plans.md). Apply that reasoning here only after you confirm that the DocumentDB plan behaves the same way in `explain()`.

## Sources

- Functional differences: Amazon DocumentDB and MongoDB, https://docs.aws.amazon.com/documentdb/latest/devguide/functional-differences.html, checked 2026-11-27
- Supported MongoDB APIs, operations, and data types (indexes and index properties), https://docs.aws.amazon.com/documentdb/latest/developerguide/mongo-apis.html, checked 2026-11-27
- Managing Amazon DocumentDB indexes, https://docs.aws.amazon.com/documentdb/latest/devguide/managing-indexes.html, checked 2026-11-27
- Partial index, https://docs.aws.amazon.com/documentdb/latest/devguide/partial-index.html, checked 2026-11-27
- Vector search for Amazon DocumentDB, https://docs.aws.amazon.com/documentdb/latest/devguide/vector-search.html, checked 2026-11-27
- Query planner v2, https://docs.aws.amazon.com/documentdb/latest/devguide/query-planner.html, checked 2026-11-27
- Query planner v3, https://docs.aws.amazon.com/documentdb/latest/devguide/query-planner-v3.html, checked 2026-11-27
- Plan cache filters, https://docs.aws.amazon.com/documentdb/latest/devguide/plan-cache-filter.html, checked 2026-11-27
- Troubleshooting performance and resource utilization, https://docs.aws.amazon.com/documentdb/latest/devguide/user_diagnostics.html, checked 2026-11-27
- Garbage collection in Amazon DocumentDB, https://docs.aws.amazon.com/documentdb/latest/devguide/garbage-collection.html, checked 2026-11-27
- Managing collection-level document compression, https://docs.aws.amazon.com/documentdb/latest/devguide/doc-compression.html, checked 2026-11-27
- Amazon DocumentDB: how it works (TTL deletes), https://docs.aws.amazon.com/documentdb/latest/devguide/how-it-works.html, checked 2026-11-27
- Amazon DocumentDB quotas, https://docs.aws.amazon.com/documentdb/latest/devguide/limits.html, checked 2026-11-27
- Release notes, https://docs.aws.amazon.com/documentdb/latest/devguide/release-notes.html, checked 2026-11-27
