# Amazon DocumentDB Compatibility with MongoDB

Checked: 2026-11-27. Read this before you migrate an application from MongoDB, before you promise that a MongoDB feature works on DocumentDB, or when a query returns different results than on MongoDB.

Contents

- [Rules for compatibility answers](#rules-for-compatibility-answers)
- [API level per engine version](#api-level-per-engine-version)
- [Not supported on any engine version](#not-supported-on-any-engine-version)
- [Feature availability by version](#feature-availability-by-version)
- [Sessions, transactions, and retryable writes](#sessions-transactions-and-retryable-writes)
- [Write concern, read concern, and read preference](#write-concern-read-concern-and-read-preference)
- [Query and update behavior](#query-and-update-behavior)
- [Indexes and plans](#indexes-and-plans)
- [Admin, tooling, and operational commands](#admin-tooling-and-operational-commands)
- [Elastic clusters](#elastic-clusters)
- [Checking an application before migration](#checking-an-application-before-migration)
- [Documentation conflicts](#documentation-conflicts)
- [Sources](#sources)

## Rules for compatibility answers

- DocumentDB emulates MongoDB APIs on its own engine. "Compatible with MongoDB 8.0" means MongoDB 8.0 drivers can connect. It does not mean every MongoDB 8.0 feature is there. For every operator, stage, and command the application uses, check the per-version tables on the [supported APIs page](https://docs.aws.amazon.com/documentdb/latest/developerguide/mongo-apis.html).
- Commands that are internal or that do not apply to a managed service are left out of the supported list. Treat a command that is missing from the list as unsupported.
- Support often depends on a minor version or a patch (for example `Yes (8.0.2+)`). Read the cluster's minor version and patch with [versions/index.md](versions/index.md#identify-the-running-version) before you answer.
- Many differences are edge cases in query semantics: nested arrays, empty keys, sort stability, `$` projections. The only reliable test is to run the application's real queries on a DocumentDB cluster of the target version and diff the results against MongoDB.
- For MongoDB semantics, see [../mongodb/data-modeling.md](../mongodb/data-modeling.md) and [../mongodb/indexes-and-query-plans.md](../mongodb/indexes-and-query-plans.md). For Azure's MongoDB-compatible offerings, see [../cosmos-db/mongodb-compatibility.md](../cosmos-db/mongodb-compatibility.md).

## API level per engine version

| Engine | MongoDB drivers supported | Minimum driver | Notes |
| --- | --- | --- | --- |
| 3.6 | MongoDB 3.6 API | 3.6-compatible | Extended Support only |
| 4.0 | MongoDB 4.0 API | 4.0-compatible or later | At GA it lacked the MongoDB 4.0 type-conversion and string operators. AWS added several of them in later patches |
| 5.0 | MongoDB 5.0 API | 5.0-compatible or later | Not every MongoDB 5.0 feature is supported |
| 8.0 | MongoDB 8.0 API, plus applications built on API 6.0 and 7.0 | 5.0-compatible or later | AWS calls this "full wire protocol compatibility" with MongoDB 8.0, but feature coverage is still partial |
| Elastic clusters | MongoDB 5.0-compatible wire protocol | | Has its own column in every API table and is the most restricted |

Source: [compatibility page](https://docs.aws.amazon.com/documentdb/latest/devguide/compatibility.html).

## Not supported on any engine version

The [supported APIs page](https://docs.aws.amazon.com/documentdb/latest/developerguide/mongo-apis.html) lists these as No in every column:

| Area | Unsupported |
| --- | --- |
| Collections | Capped collections, `convertToCapped`, `cloneCollectionAsCapped`, `copydb`, `filemd5` |
| Diagnostics | `connPoolStats`, `dbHash`, `features` |
| Writes | `getLastError`, `getPrevError`, `resetError`, `parallelCollectionScan` |
| Sessions | `endSessions` (conflicting, see below), `killAllSessionsByPattern`, `refreshSessions`, `$listSessions`, `$listLocalSessions` |
| Query | `$where` |
| Geospatial | 2d indexes, `$box`, `$center`, `$centerSphere`, `$polygon`, `$uniqueDocs` |
| Indexes | Hashed indexes, 2d indexes, index compression |
| Aggregation | `$accumulator`, `$derivative`, `$expMovingAvg`, `$integral`, `$linearFill`, `$locf`, `$shift`, `$densify`, `$fill`, `$planCacheStats`, `$$CURRENT`, `$$REMOVE` |
| Cursor | `noCursorTimeout()`, `returnKey()`, `showRecordId()`, `tailable()` |
| Data types | DBPointer, DBRef, JavaScript, JavaScript with scope, Symbol, Undefined |
| Databases | The `admin` and `local` databases as application databases, `system.*` collections, `startup_log`. Users and roles are stored in `admin` |
| Replication internals | The oplog. Use change streams instead |
| Sharding commands | All except `enableSharding` and `shardCollection`, and those two work on elastic clusters only |

Change stream pre-images (`fullDocumentBeforeChange`) are not in the change streams page's list of supported operations. See [architecture-and-operations.md](architecture-and-operations.md#change-streams-operations) before migrating a consumer that reads them.

## Feature availability by version

Taken from the [features by version table](https://docs.aws.amazon.com/documentdb/latest/devguide/docdb-engine-version-supportability.html) and the API tables. "Elastic" is the elastic-cluster column.

| Feature | 3.6 | 4.0 | 5.0 | 8.0 | Elastic |
| --- | --- | --- | --- | --- | --- |
| Multi-document transactions | No | Yes | Yes | Yes | No |
| Retryable writes | No | No | No | 8.0.2+ | No |
| Change streams | Yes (primary only) | Yes (primary only) | Yes (replicas too) | Yes | No |
| Global clusters | No | Yes | Yes | Yes | No |
| Serverless instances | No | No | Yes | Yes | No |
| `$jsonSchema`, `$expr` | No | Yes | Yes | Yes | No |
| `$lookup` equality join | Yes | Yes | Yes | Yes | Yes |
| `$lookup` uncorrelated subquery | not in the release notes; test it | Yes (patch 2.0.10392) | Yes (patch 3.0.5721) | Yes | not in the release notes; test it |
| `$lookup` correlated subquery | No | No | No | 8.0.2+ | No |
| `$facet`, `$graphLookup`, `$bucketAuto`, `$setWindowFields` | No | No | No | 8.0.2+ | No |
| `$merge`, `$set`/`$unset` stages, `$bucket`, `$replaceWith` | No | No | No | Yes | No |
| `$unionWith` | No | No | No | 8.0.3+ | No |
| `$out` | Yes | Yes | Yes | Yes (cross-database under v3) | No |
| Views (`createView`), collation | No | No | No | Yes | No |
| `mapReduce` | No | No | No | Yes | No |
| `$text` search and text indexes | No | No | Yes (v1) | Yes (v2 for new indexes) | No |
| Vector search (`$search` with `vectorSearch`; `$vectorSearch` stage on 8.0) | No | No | Yes | Yes | No |
| Partial indexes | No | No | Yes | Yes | No |
| Wildcard indexes | No | No | No | 8.0.3+ | No |
| Hidden indexes | No | No | 5.0.2+ (see conflicts) | 8.0.1+ | No |
| Case-insensitive (collation) indexes | No | No | No | Yes | No |
| Document compression | No | No | LZ4 | Zstd, LZ4 | No |
| Client-side field level encryption | No | No | Yes | Yes | No |
| IAM authentication | No | No | Yes (instance-based) | Yes per features table (see conflicts) | No |
| `reIndex` | No | No | Yes | Yes | No |
| Plan cache filters (`planCacheSetFilter`) | No | No | Yes | Yes | No |
| Profiler | Yes | Yes | Yes | Yes | No |
| Performance Insights | Yes | Yes | Yes | Yes | No |
| Audit logs | Yes | Yes | Yes | Yes | Yes per features table, but the elastic page lists DDL/DML auditing as unsupported (conflict) |
| Custom RBAC roles | Yes | Yes | Yes | Yes | No |
| GridFS | Yes | Yes | Yes | Yes | No |
| `renameCollection` | Yes | Yes | Yes | Yes | No |

The functional-differences page says uncorrelated `$lookup` subqueries are supported without naming a version; only the 4.0 and 5.0 patches appear in the release notes. On 3.6 or an elastic cluster, test with `db.a.aggregate([{$lookup: {from: "b", pipeline: [{$limit: 1}], as: "x"}}])` before relying on it.

## Sessions, transactions, and retryable writes

- The functional-differences page contradicts itself here. Its "Implicit transactions" section says all CRUD statements "guarantee atomicity and consistency, even for operations that modify multiple documents". A few lines later it says the individual operations inside `updateMany` and `deleteMany` are atomic "but the entirety of the bulk operation is not atomic", and it recommends a transaction when `insertMany`, `updateMany` or `deleteMany` need ACID properties. Plan for the second reading: if a multi-document `updateMany`, `deleteMany` or `insertMany` must succeed or fail as a whole, run it in a transaction (4.0 and later). Source: [functional differences](https://docs.aws.amazon.com/documentdb/latest/devguide/functional-differences.html#functional-differences.implicit-transactions).
- Transactions (4.0 and later) need a 4.0-compatible driver. Their limits differ from MongoDB:

  | Limit | Value |
  | --- | --- |
  | Execution time | 1 minute, then the transaction is aborted (error 251, "Given transaction number ... does not match any in-progress transactions") |
  | Session idle timeout | 30 minutes |
  | Transaction log size | under 32 MB |
  | Document write-lock wait | 1 minute, not configurable |
  | Concurrent open transactions | per instance class (for example 200 on `r6g.large`, 50 on `t3.medium`) |
  | Cursors inside a transaction | Not supported |
  | Creating collections inside a transaction | Not supported. `insert` into a missing collection fails |
  | Unsupported inside a transaction | `$collStats`, `$currentOp`, `$indexStats`, `$listSessions`, `$out`; `$where`, `$near`, `$nearSphere` in counts |

- Isolation: the default read concern is `snapshot`. `local`, `available`, and `majority` are upgraded to `snapshot`. `linearizable` returns an error. A write concern below `majority` is upgraded to `majority`. Journaling cannot be turned off.
- Causal consistency is not supported. Start sessions with `causalConsistency: false`. Reads from the primary see your own writes; reads from replicas are eventually consistent.
- Retryable writes:
  - Before 8.0.2, any write that carries retryable-write fields fails with `{"ok":0,"errmsg":"Retryable writes are not supported","code":301}`. Most drivers turn retryable writes on by default, so set `retryWrites=false` on these versions.
  - From 8.0.2, single-document writes are retryable: `insertOne`, `insertMany` and `bulkWrite` (deduplicated per document), `updateOne`, `deleteOne`, and `findOneAnd*`. `commitTransaction` and `abortTransaction` are also retryable.
  - Not retryable: `updateMany`, `deleteMany`, writes inside transactions, inserts without `_id`, and any write on a cluster that runs planner 1.0.
  - Retries are deduplicated for 60 minutes. A retry that arrives later runs as a new write. Error 225 `TransactionTooOld` means the retry is stale.
  - Large `findOneAnd*` results are cached for deduplication, which adds write latency. Source: [retryable writes](https://docs.aws.amazon.com/documentdb/latest/devguide/retryable-writes.html).

For how this compares with MongoDB's transaction model, see [../mongodb/transactions-and-consistency.md](../mongodb/transactions-and-consistency.md). MongoDB tuning such as `transactionLifetimeLimitSeconds` does not carry over, because the 1-minute limit is fixed.

## Write concern, read concern, and read preference

| Setting | DocumentDB behavior |
| --- | --- |
| Write concern `w` | Ignored. Writes are always durable on a quorum of the six-way storage (4 of 6 copies across 3 AZs), comparable to `{w: 3, j: true}` on a three-member replica set. It cannot be lowered |
| `wtimeout` | Not supported, but accepted without error |
| `j: false` | No effect; journaling is always on |
| Read concern | Snapshot inside transactions. Reads return only durable data, so dirty reads cannot happen |
| Read preference | Honored only over the cluster endpoint in replica-set mode (`replicaSet=rs0`). Otherwise the behavior is undefined |
| Read preference tag sets | Not supported |
| `maxStalenessSeconds` | Not listed among the read preference options on the how-it-works page. If a driver sets it, test on the cluster endpoint in replica-set mode; watch `DBInstanceReplicaLag` instead (usually under 100 ms) |
| Write concern 0 | Not supported on elastic clusters |

Source: [how it works: read preference options](https://docs.aws.amazon.com/documentdb/latest/devguide/how-it-works.html#durability-consistency-isolation), [transactions](https://docs.aws.amazon.com/documentdb/latest/devguide/transactions.html#transactions-isolation-level).

## Query and update behavior

These differences from MongoDB change results. They come from the [functional differences page](https://docs.aws.amazon.com/documentdb/latest/devguide/functional-differences.html) unless another source is given.

| Area | DocumentDB behavior | Action |
| --- | --- | --- |
| Result order | No implicit order. `$sort` order survives only when `$sort` is the last stage. Before `$group`, `$sort` affects only `$first`/`$last` (and `$push` from 4.0) | Always add an explicit `sort()`. Sort again after `$group` |
| `$natural` | Forward scans only. `{$natural: -1}` raises `MongoServerError` | Sort on an indexed key instead |
| `cursor.maxTimeMS` | Resets on every `getMore`, and the sweeper checks only every 5 minutes. A cursor whose individual batches each finish under the limit never times out | Enforce total deadlines in the application |
| `$elemMatch` inside `$all` | Not supported | Rewrite as `$and` of `$elemMatch` clauses |
| `$`-prefixed fields in `$in`, `$nin`, `$all` within nested objects | Not supported, for example `{"field": {"$all": [{"$a": 1}]}}` | Avoid these field names where you query them |
| Empty key in a path (`x.`, `x..b`) against an array holding `{"": ...}` | The functional-differences page says only the first array element is read, because the empty key is converted to index 0. The compatibility page's 4.0 section says DocumentDB returns the document because it traverses every element. Both say the result differs from MongoDB | Do not use empty-string keys |
| `$vectorSearch` | The functional-differences page says to use `vectorSearch` inside `$search` and that `$vectorSearch` is not supported as an independent operator. The [vector search page](https://docs.aws.amazon.com/documentdb/latest/devguide/vector-search.html), the 8.0 API table, and the 8.0 release notes say the `$vectorSearch` stage is available from 8.0 | On 5.0, use `$search` with `vectorSearch`. On 8.0, either form. The functional-differences text appears stale (interpretation) |
| `$regex` index use | Planner v1 uses an index only with `hint()` by key pattern (`.hint({product: 1})`, not the index name), and only for prefix patterns without the `i`, `m`, or `o` options. Planner v2 and later use prefix regex indexes without a hint | Confirm with `explain()` |
| Sparse indexes | Planner v1 uses a sparse index only when the query has `$exists: true` on that field. v2 and later do not need it | |
| Partial indexes with inequalities | The partial index page says the index is used only when the query predicate matches the filter expression exactly and has the same data type. Planner v2 also uses it when the query range is narrower than the filter | Test with `explain()` on the planner you run |
| Unique sparse multikey | Uniqueness is not enforced when an array element lacks the field, for example a unique sparse index on `a.b` with `a: [{b: 2}, {c: 1}]` | Enforce uniqueness another way |
| `$lookup` algorithm | Hash with `allowDiskUse:false`, sort-merge with `allowDiskUse:true`, nested loop when the foreign field is indexed. Explain shows `HASH_LOOKUP`, `SORT_LOOKUP`, or `NESTED_LOOP_LOOKUP` | On planner v1 only, force an algorithm with `comment: "{\"lookupStage\": {\"planHint\": \"HASH\"}}"`. Planner v3 rejects `planHint` |
| `allowDiskUse` on `find` | Not supported; works only in `aggregate` | |
| Change stream `updateDescription` | A `$set` to the existing value is left out of `updatedFields`. MongoDB includes it | |
| `OpCountersCommand` metric | Excludes `find` and includes some internal commands | Do not compare directly with MongoDB `opcounters.command` |
| Planner v2 versus v1 and MongoDB | Edge cases differ: positional `$` in updates and projections, `nModified` on no-op updates, `$hint` to an unsuitable partial index (v2 raises an error), `$rename` of a missing field | See the [planner v2 page](https://docs.aws.amazon.com/documentdb/latest/devguide/query-planner.html#v2-planner-behavior-differences) |
| Planner v3 versus v1 | v1 emits `"field": 0` on empty input, ignores `$skip` when the input has fewer documents than the skip, and errors on `$lookup` to a missing collection. v3 behaves like MongoDB | See the [planner v3 page](https://docs.aws.amazon.com/documentdb/latest/devguide/query-planner-v3.html#planner-behavior-differences) |
| Dollar and dot in field names | Supported on 5.0 from patch 3.0.11051, except for the query limitation above | |

Behavior changes between DocumentDB versions are in [versions/4.0.md](versions/4.0.md#upgrading-into-this-series), [versions/5.0.md](versions/5.0.md#upgrading-into-this-series), and [versions/8.0.md](versions/8.0.md#upgrading-into-this-series).

## Indexes and plans

- A collection can have only one index build running at a time, whether it is a foreground or a background build. A concurrent `createIndex` or `dropIndex` on the same collection fails. Roll out indexes one per collection at a time.
- Index builds run in the foreground by default, as in MongoDB 4.0, and a foreground build blocks all other operations on the collection. Pass `{background: true}` on production collections. MongoDB 4.2 and later ignore that option, so MongoDB habits mislead here.
- A TTL index starts expiring documents only after its build completes. TTL deletes are best-effort and cost I/O.
- `explain()` output differs from MongoDB. It includes `plannerVersion` and DocumentDB stage names such as `COLLSCAN`, `IXSCAN`, `IXONLYSCAN`, `HASH_LOOKUP`, `SUBSCAN`, `SORT_AGGREGATE`, and `DISTINCT_SCAN`. `hint()` forces an index.
- Supported index types: single field; compound (up to 32 keys); multikey, including compound multikey on one array; 2dsphere; TTL; unique; sparse. Text, partial, and vector need 5.0 or later. Case-insensitive needs 8.0, and wildcard needs 8.0.3 or later. Hashed and 2d indexes are not supported. Index keys are limited to 2,048 bytes. Details are in [data-modeling-and-indexes.md](data-modeling-and-indexes.md).

## Admin, tooling, and operational commands

| Topic | DocumentDB behavior |
| --- | --- |
| Users and roles | Stored in `admin` and authenticated against `admin`. User and role commands run in `admin` whichever database is current. `serviceadmin` and the primary user always exist and cannot be dropped |
| `mongodump`/`mongorestore` | Use MongoDB Database Tools 100.11.0 or earlier. `admin` is not dumped or restored, so re-create users and roles on the target |
| Change streams | Off by default. Enable them per collection, database, or cluster with `db.adminCommand({modifyChangeStreams: 1, database: "...", collection: "...", enable: true})`, and list them with `$listChangeStreams` |
| `currentOp`, `killOp`, `top`, `serverStatus`, `collStats`, `dbStats`, `$indexStats` | Supported, with different output fields. DocumentDB adds `cacheStats`, `unusedStorageSize`, `MVCCIdStats`, `gcRuntimeStats`, `opCounter`, and `WaitState` (in `currentOp`) |
| `getEngineVersion` | DocumentDB-specific |
| `listCollections` with a `type` key in the filter | Not supported |
| `setParameter`, `getCmdLineOpts`, `replSetReconfig`, `fsync` | Not in the supported list. Configure through cluster parameter groups and the AWS API |
| Profiler | `db.setProfilingLevel()` does not apply. Set the `profiler`, `profiler_threshold_ms`, and `profiler_sampling_rate` cluster parameters and export to CloudWatch Logs |

## Elastic clusters

Elastic clusters hash-shard data on a shard key across 1 to 32 shards. Each shard has 2 to 64 vCPUs and 1 to 16 instances, and the cluster uses the MongoDB 5.0-compatible wire protocol. Choose them only when a single instance-based writer cannot absorb the write rate or the data size (128 TiB on 5.0 and earlier, 256 TiB on 8.0), and only when the application can do without everything below.

Not supported on elastic clusters ([elastic clusters page](https://docs.aws.amazon.com/documentdb/latest/devguide/docdb-using-elastic-clusters.html)):

| Category | Missing |
| --- | --- |
| Data features | ACID transactions, session commands, change streams, unique indexes, partial/text/vector indexes, document compression, `$jsonSchema`, `$expr` |
| Sharding | Range sharding, multi-field shard keys, changing the shard key, sharding an existing collection |
| Operations | Point-in-time restore, cloning, Performance Insights, profiler, parameter groups, AWS Backup, AWS Config, events and event subscriptions, DDL while scaling, custom port |
| Security | IAM authentication, custom RBAC roles, Secrets Manager, DDL/DML auditing |
| Engines | Not available on 8.0. Planner v2 and v3 are not used; elastic clusters fall back to v1 |
| Writes | `w: 0` |

Other differences from 4.0 instance-based clusters: `top` and `collStats` are reported per shard and reset when the shard count changes. The nested `$elemMatch`, `$` projection, `$regex`/`$options`, `$indexOfCP`, and `_id` subfield projection behaviors match 5.0. Collection names can be at most 54 bytes. A cluster holds at most 100 users, 1,000 sharded collections, and 10,000 databases ([quotas](https://docs.aws.amazon.com/documentdb/latest/devguide/limits.html#elastic.cluster.limits)).

Shard key: pick one field with high cardinality and even access. The key cannot change, and only hash sharding exists. For general shard-key reasoning see [../mongodb/replication-and-sharding.md](../mongodb/replication-and-sharding.md), but range-based key patterns do not apply here.

## Checking an application before migration

1. Inventory the commands, stages, operators, and index types the application uses, from the MongoDB profiler, the logs, or a code search. Compare them with the per-version columns on the [supported APIs page](https://docs.aws.amazon.com/documentdb/latest/developerguide/mongo-apis.html). The DMS upgrade page points to the `amazon-documentdb-tools` repository for index migration. Its `compat-tool` checks a running MongoDB 5.0+ server from `serverStatus` operator counters (`--uri`), or log files and source code by text match (`--file`, `--directory`). `--version` picks the target (`3.6`, `4.0`, `5.0.1`, `8.0.3`, `EC5.0` for elastic clusters; default `8.0.3`). File and directory scans exit with 1 when they find unsupported operators, so they fit in CI (compat-tool README).
2. Fix the connection string: TLS with the AWS CA bundle (`global-bundle.pem`), `replicaSet=rs0`, `readPreference=secondaryPreferred` where stale reads are acceptable, and `retryWrites=false` below 8.0.2.
3. Choose the engine from the feature table above: 8.0 for the broadest coverage, 5.0.0 for LTS or for parity with elastic clusters.
4. Load a representative data copy. AWS DMS does not copy secondary indexes: copy them with the Amazon DocumentDB Index Tool or create them on the target before the full load ([DMS upgrade page](https://docs.aws.amazon.com/documentdb/latest/devguide/docdb-migration.versions.html)). Run the query suite on both MongoDB and DocumentDB and diff the results, focusing on unsorted results, nested arrays, and `$` projections.
5. Re-baseline plans with `explain("executionStats")`. Add `hint()` or plan cache filters where the planner chooses badly.
6. Re-create users and roles; `mongodump` does not carry them.

## Documentation conflicts

These are conflicts between AWS pages as of 2026-11-27. Quote the conflict instead of picking a side, and test on the target version.

| Topic | Page A | Page B |
| --- | --- | --- |
| Hidden indexes on 5.0 | API index-properties table: Hidden on 5.0 = No | `collMod: hidden` on 5.0 = Yes (5.0.2+); 5.0.2 release notes add hidden indexes |
| `$dateToParts`/`$dateFromParts` on 8.0 | API table: 8.0 = No | 8.0 release notes (20 Apr 2026) and the planner v3 page say they are supported |
| `$vectorSearch` stage | Functional differences: not supported as an independent operator | Vector search page, 8.0 API table, release notes, and planner v3 page: available from 8.0 |
| `endSessions` | API table: No on every version | Transactions page: Yes |
| `reIndex` scope | Index management page: only 5.0, and not for partial indexes | API table: 8.0 = Yes; 8.0.2 release notes add `reIndex` on partial indexes |
| IAM authentication on 8.0 | IAM page: only instance-based 5.0 | Features table: 8.0 = Yes |
| Auditing on elastic clusters | Features table: Yes | Elastic clusters page: DDL/DML auditing not supported |
| Elastic clusters on 5.0 only | Features table "Engine status": elastic clusters only for v5.0 | The "Cluster types" table has an "Elastic clusters" column showing Yes for instance-based clusters, which looks like a layout artifact |
| Planner parameter name | Parameter reference: `planner_version` | Planner v2 and v3 pages: `plannerVersion` |
| Profiler threshold minimum | Parameter reference and profiler page: 50 | PITR page: 0 to INT_MAX |
| Change stream retention maximum | Parameter reference: 3600 to 604800 seconds (7 days) | An example output on the change streams page shows AllowedValues `3600-86400` (stale example) |
| Partial index with inequality | Partial index page: used only on an exact predicate match | Planner v2 page: used even when the query range differs from the filter |
| Atomicity of `updateMany`/`deleteMany` | Functional differences, "Implicit transactions": CRUD statements are atomic even when they modify multiple documents | Same page, a few lines later: the bulk operation as a whole is not atomic; use a transaction |
| Empty key in a path (`x.`) inside an array | Functional differences: only the first array element is read | Compatibility page, 4.0 section: every element is traversed and the document is returned |
| Cluster- and database-level change streams, `startAtOperationTime` | Compatibility page lists them as 4.0 features | Release notes: cluster- and database-level streams on 3.6 since 30 Oct 2020; `startAtOperationTime` on 3.6 from optional patch 1.0.208692 (27 Apr 2026) |

## Sources

- Amazon DocumentDB compatibility with MongoDB, https://docs.aws.amazon.com/documentdb/latest/devguide/compatibility.html, checked 2026-11-27
- Functional differences: Amazon DocumentDB and MongoDB, https://docs.aws.amazon.com/documentdb/latest/devguide/functional-differences.html, checked 2026-11-27
- Supported MongoDB APIs, operations, and data types, https://docs.aws.amazon.com/documentdb/latest/developerguide/mongo-apis.html, checked 2026-11-27
- Amazon DocumentDB features and configurations, https://docs.aws.amazon.com/documentdb/latest/devguide/docdb-engine-version-supportability.html, checked 2026-11-27
- Transactions in Amazon DocumentDB, https://docs.aws.amazon.com/documentdb/latest/devguide/transactions.html, checked 2026-11-27
- Retryable writes in Amazon DocumentDB, https://docs.aws.amazon.com/documentdb/latest/devguide/retryable-writes.html, checked 2026-11-27
- Amazon DocumentDB: how it works, https://docs.aws.amazon.com/documentdb/latest/devguide/how-it-works.html, checked 2026-11-27
- Query planner v2, https://docs.aws.amazon.com/documentdb/latest/devguide/query-planner.html, checked 2026-11-27
- Query planner v3, https://docs.aws.amazon.com/documentdb/latest/devguide/query-planner-v3.html, checked 2026-11-27
- Vector search for Amazon DocumentDB, https://docs.aws.amazon.com/documentdb/latest/devguide/vector-search.html, checked 2026-11-27
- Partial index, https://docs.aws.amazon.com/documentdb/latest/devguide/partial-index.html, checked 2026-11-27
- Using Amazon DocumentDB elastic clusters, https://docs.aws.amazon.com/documentdb/latest/devguide/docdb-using-elastic-clusters.html, checked 2026-11-27
- Amazon DocumentDB elastic clusters: how it works, https://docs.aws.amazon.com/documentdb/latest/devguide/elastic-how-it-works.html, checked 2026-11-27
- Amazon DocumentDB quotas, https://docs.aws.amazon.com/documentdb/latest/devguide/limits.html, checked 2026-11-27
- Database access using Role-Based Access Control, https://docs.aws.amazon.com/documentdb/latest/devguide/role_based_access_control.html, checked 2026-11-27
- Authentication using IAM identity, https://docs.aws.amazon.com/documentdb/latest/devguide/iam-identity-auth.html, checked 2026-11-27
- Managing Amazon DocumentDB indexes, https://docs.aws.amazon.com/documentdb/latest/devguide/managing-indexes.html, checked 2026-11-27
- Using change streams with Amazon DocumentDB, https://docs.aws.amazon.com/documentdb/latest/devguide/change_streams.html, checked 2026-11-27
- Cluster parameters reference, https://docs.aws.amazon.com/documentdb/latest/devguide/cluster_parameter_groups-list_of_parameters.html, checked 2026-11-27
- Release notes, https://docs.aws.amazon.com/documentdb/latest/devguide/release-notes.html, checked 2026-11-27
