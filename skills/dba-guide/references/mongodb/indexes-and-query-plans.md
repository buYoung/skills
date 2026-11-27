# MongoDB Indexes and Query Plans

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)). For finding slow queries see [monitoring](monitoring.md).

## Contents

- [Design compound indexes with ESR](#design-compound-indexes-with-esr)
- [Read explain output](#read-explain-output)
- [Plan selection, plan cache, and query settings](#plan-selection-plan-cache-and-query-settings)
- [Build indexes on a live deployment](#build-indexes-on-a-live-deployment)
- [Find and remove unused indexes](#find-and-remove-unused-indexes)
- [Index types and restrictions worth knowing](#index-types-and-restrictions-worth-knowing)

## Design compound indexes with ESR

Order the keys Equality, then Sort, then Range:

1. Equality fields first: exact matches such as `{status: "paid"}` or `$eq`. Their order among themselves does not matter for correctness. All of them must come before any sort or range key.
2. Sort fields next, in the same direction as the sort, or all reversed. An index serves a sort on a subset of its keys only when every key before the sort keys has an equality condition.
3. Range fields last: `$gt`, `$gte`, `$lt`, `$lte`, `$ne`, `$nin`, `$regex`.

Exceptions:

- If the range predicate is highly selective and an in-memory sort of the few remaining documents is acceptable, put the range before the sort (E-R-S). This scans fewer keys and sorts in memory.
- `$in` used alone acts as equality. With `.sort()`:
  - Under 201 array elements: the planner expands it into point scans merged in index order (`SORT_MERGE`), so it still behaves like equality.
  - 201 or more elements: it behaves like a range, and later index fields no longer provide the sort.
  - The manual says this 201-element threshold may change between versions.
- `$ne`, `$nin`, and `$regex` are range operators, not equality.

Example: for `find({ customerId: 42 }).sort({ createdAt: -1 }).limit(10)`, use `{ customerId: 1, createdAt: -1 }`.

```javascript
db.orders.createIndex({ customerId: 1, createdAt: -1 })   // returns 'customerId_1_createdAt_-1'
```

## Read explain output

Use verbosity `"executionStats"` to see real work done. `"allPlansExecution"` adds partial stats for the rejected candidates gathered during plan selection. `explain` does not use or populate the plan cache, so its timing includes plan selection.

```javascript
db.orders.find({ customerId: 42 }).sort({ createdAt: -1 }).limit(10).explain("executionStats")
db.orders.aggregate(pipeline).explain("executionStats")      // or db.orders.explain("executionStats").aggregate(pipeline)
```

Fields to read first:

| Field | Meaning | Healthy sign |
| --- | --- | --- |
| `queryPlanner.winningPlan` | stage tree (`stage`, `inputStage`, `inputStages`) | `IXSCAN` under `FETCH`, or `IXSCAN` with no `FETCH` (covered) |
| `executionStats.nReturned` | documents returned | — |
| `executionStats.totalKeysExamined` | index entries scanned | close to `nReturned` |
| `executionStats.totalDocsExamined` | documents fetched | close to `nReturned`; 0 for covered queries |
| `executionStats.executionTimeMillis` | includes plan selection | compare like with like |
| `SORT` stage present | in-memory sort | absent when the index provides order |
| `indexBounds` | ranges scanned per key | tight bounds on leading keys; `[MaxKey, MinKey]` means unbounded |
| `isMultiKey`, `multiKeyPaths` | an array field is indexed | affects which bounds can be combined |
| `queryShapeHash` (8.0+), `planCacheShapeHash` (8.0+, same as deprecated `queryHash`), `planCacheKey` | identifiers to correlate with logs, `$queryStats`, and query settings | — |

Observed on the official images: 50,000 `orders` documents, query `{customerId: 42}` with sort `{createdAt: -1}` and limit 10.

- Without an index:
  - The winning plan is `SORT` over `COLLSCAN` with `memLimit: 104857600`.
  - Stats: `n: 10`, `keys: 0`, `docs: 50000`. All four series show this.
- With `{customerId: 1, createdAt: -1}`:
  - The plan is `LIMIT` → `FETCH` → `IXSCAN`, with bounds `customerId: ['[42, 42]']` and `createdAt: ['[MaxKey, MinKey]']`.
  - Stats: `n: 10`, `keys: 10`, `docs: 10`.
- With `customerId: {$in: [1,2,3]}`, `status: "paid"`, sorted by `createdAt`, the plan is `FETCH` (filter `status: paid`) → `SORT_MERGE` over three `IXSCAN` point ranges. Stats: `n: 100`, `keys: 300`, `docs: 300`. A ratio like that means a non-indexed equality field (`status`) is filtering after the fetch. Adding `status` to the index (ESR: `{customerId: 1, status: 1, createdAt: -1}`) moves the filter into the index scan.

Engine and format differences:

- `explainVersion: "1"` with a `stages` array marks classic-engine aggregation output. The 7.0 image produced this for a `$group` pipeline.
- `explainVersion: "2"` with `queryPlan` and `slotBasedPlan` sections marks slot-based engine (SBE) output. The 8.0, 8.3, and 9.0 images produced this for the same pipeline. The manual does not tie the version numbers to engines explicitly; read the structure.
- 8.0 adds express stages (`EXPRESS_IXSCAN` and others) for simple point lookups.
- 8.2 standardizes spill fields: `spills`, `spilledBytes`, `spilledRecords`, `spilledDataStorageSize`.
- 8.3 adds `peakTrackedMemBytes`, and from 8.3.3 cost-based-ranker estimates: `costEstimate`, `cardinalityEstimate`, `estimatesMetadata`.
- 9.0 adds `expressionEvaluationPeakMemoryBytes` for classic-engine expression stages.

Sharded explain: `SHARD_MERGE` merges per-shard results, and `SHARDING_FILTER` removes orphan documents. Explain each shard's plan; a missing index on one shard shows up as a `COLLSCAN` only there.

Common mistakes:
- Comparing `executionTimeMillis` of a cold run against a warm one.
- Adding an index for a sort when the leading key is a range: the index still cannot supply the order.
- Reading only the winning plan and ignoring `totalDocsExamined`.

## Plan selection, plan cache, and query settings

- The multi-planner races candidate plans for a short trial and caches the winner per plan-cache shape. Since 8.3 the planner falls back to a cost-based ranker when the trial does not decide; serverStatus reports this under `metrics.query.cbr`.
- Inspect cached plans with `db.orders.aggregate([{ $planCacheStats: {} }])`. Clear them with `db.orders.getPlanCache().clear()`. Plans are evicted when indexes change. On all four images a query with a single candidate plan left no `$planCacheStats` entry; a query with two candidate indexes left one entry, and `clear()` brought the count back to `0`.
- Pin or block a plan without code changes, 8.0+:

  ```javascript
  db.adminCommand({
    setQuerySettings: { find: "orders", filter: { customerId: 1 }, $db: "dbaverify" },
    settings: { indexHints: { ns: { db: "dbaverify", coll: "orders" },
                              allowedIndexes: ["customerId_1_createdAt_-1"] } }
  })
  ```

  On 8.0, 8.3, and 9.0 the image returned the stored `queryShapeHash`, `settings.indexHints`, and `representativeQuery`. On 7.0: `no such command: 'setQuerySettings'`.
  - List settings with `db.getSiblingDB("admin").aggregate([{ $querySettings: {} }])`. On 7.0 the stage does not exist (`Unrecognized pipeline stage name: '$querySettings'`).
  - Remove them with `db.adminCommand({ removeQuerySettings: { find: "orders", filter: { status: "x" }, $db: "dbaverify" } })`, giving a query of the same shape.
  - Settings can also set `reject: true` to block a runaway query shape: `settings: { reject: true }`. On 8.0, 8.3, and 9.0 a query of the rejected shape failed with code `411` (`QueryRejectedBySettings`, "Query rejected by admin query settings"), and `removeQuerySettings` returned `ok: 1`.
  - 9.0 adds per-shape `maxTimeMS` and `queryKnobs`, and per-command `querySettings`.
- Index filters (`planCacheSetFilter`) are deprecated since 8.0. Migrate them to query settings.
- `hint()` in application code is the last resort. It survives index renames poorly and hides regressions.

## Build indexes on a live deployment

Behavior on replica sets and sharded clusters:

- Builds run on all data-bearing members at once. The collection takes an exclusive lock only at the start and end; in between the build yields to reads and writes. The final lock phase grows with the number of writes made during the build.
- The primary commits once `commitQuorum` members finish. The default is `"votingMembers"`, meaning all data-bearing voting members.
  - Production risk: if one voting data-bearing member is down, a default-quorum build hangs until it returns.
  - Set `commitQuorum` explicitly, or check member health first.
  - Change it for a running build with `setIndexCommitQuorum`.
- Memory: `maxIndexBuildMemoryUsageMegabytes` is 200 MB per `createIndexes` command, shared across the indexes in that command; beyond it the build spills to `_tmp` under `dbPath`. At most `maxNumActiveUserIndexBuilds` = 3 builds run at once. All four images show these defaults.
- `indexBuildMinAvailableDiskSpaceMB` (7.1+, so 8.0+ in the covered range) stops a build when disk runs low.
- Unique indexes: violations are checked at the end. Existing duplicates, or duplicates written during the build, fail the build after all the work. Check first:

  ```javascript
  db.users.aggregate([{ $group: { _id: "$email", n: { $sum: 1 } } }, { $match: { n: { $gt: 1 } } }, { $limit: 5 }],
                     { allowDiskUse: true })
  ```
- Monitor progress with `db.currentOp({ $or: [ { "command.createIndexes": { $exists: true } }, { msg: /^Index Build/ } ] })`; `msg` shows the percentage. Stop a build with `dropIndex` / `dropIndexes`, never `killOp`, on replica sets and sharded clusters.
- A clean shutdown checkpoints the build, and it resumes once. A crash restarts it from the beginning.
- Secondaries may pause replication while draining side writes, and write-heavy workloads slow both. Schedule large builds off-peak.

Rolling index builds (one member at a time, as a standalone, then rejoined) lower resiliency and need at least one election. Use them only when a replicated build's impact is unacceptable. Never mix rolling and replicated builds of the same index.

## Find and remove unused indexes

```javascript
db.orders.aggregate([{ $indexStats: {} }, { $project: { name: 1, "accesses.ops": 1, "accesses.since": 1 } }])
```

- `accesses.ops` counts uses since `accesses.since` (the process start or index creation). The counter is per node and resets on restart. Collect it from every member that serves reads, over a full business cycle, before concluding an index is unused.
- The images showed `customerId_1_createdAt_-1` with `ops: 2` and `_id_` with `ops: 0` after the test queries.
- Before dropping, hide the index: `db.orders.hideIndex("name")`. A hidden index stays maintained but is not used by the planner. Watch for regressions, then `dropIndex`, or `unhideIndex` to roll back. On all four images, hiding `customerId_1_createdAt_-1` changed the winning plan for `find({ customerId: 42 }).sort({ createdAt: -1 }).limit(10)` from `LIMIT` over an index scan to `SORT` over `COLLSCAN`, `getIndexes()` showed `hidden: true`, and `unhideIndex` restored the index plan. Both helpers return `hidden_old` and `hidden_new`.
- Each extra index costs write work, cache, and disk. A high write-to-read ratio is the main reason to remove marginal indexes.

## Index types and restrictions worth knowing

- Multikey: indexing an array field makes the index multikey, which limits bound combination. In 9.0, a query can fail with `QueryKilledError` if a field becomes multikey while the query runs.
- Compound wildcard indexes (7.0+) have stricter `wildcardProjection` validation from 8.3, 8.2.4, 8.0.18, and 7.0.29 onward.
- A shard key index cannot be descending, partial, geospatial, multikey, text, or wildcard (limits page).
- 2dsphere index version 4 is the default from 8.3; drop v4 indexes before downgrading FCV below 8.3. A new `2dsphere` index reported `2dsphereIndexVersion: 3` on the 7.0 and 8.0 images and `4` on 8.3 and 9.0.
- Text search: from 8.3, `$text` queries that use the text score are capped at 100 MB and spill only with `allowDiskUse`.
- Per-stage memory is 100 MB. `allowDiskUseByDefault` decides whether stages spill (the images show `true`). 9.0 also caps a whole operation at the greater of 1 GB or 20% of memory.
