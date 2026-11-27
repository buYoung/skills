# MongoDB Replication and Sharding

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)). Consistency settings are in [transactions-and-consistency](transactions-and-consistency.md).

## Contents

- [Replica set topology](#replica-set-topology)
- [Elections and failover](#elections-and-failover)
- [Oplog sizing and the oplog window](#oplog-sizing-and-the-oplog-window)
- [Replication lag and flow control](#replication-lag-and-flow-control)
- [Initial sync and member maintenance](#initial-sync-and-member-maintenance)
- [When to shard](#when-to-shard)
- [Choose a shard key](#choose-a-shard-key)
- [Evaluate a shard key before using it](#evaluate-a-shard-key-before-using-it)
- [Change a shard key: refine or reshard](#change-a-shard-key-refine-or-reshard)
- [Balancer, ranges, and placement](#balancer-ranges-and-placement)
- [Sharded cluster operations by version](#sharded-cluster-operations-by-version)

## Replica set topology

Limits: 50 members, of which at most 7 vote.

| Topology | Use when | Cost |
| --- | --- | --- |
| 3 data-bearing members (PSS) | default for production | 3× storage |
| 5 data-bearing members across 3 sites | must survive the loss of one site and one member | more replication traffic |
| PSA (primary, secondary, arbiter) | budget forces 2 data nodes | implicit write concern drops to `w: 1`; with a secondary down, `w: "majority"` writes stall; multi-shard transactions fail on arbiter shards |
| Hidden / delayed member (`priority: 0`, `hidden: true`, `votes: 0`, `secondaryDelaySecs`) | backups or protection against operator error | does not serve normal reads. Keep delayed members hidden and non-voting: a voting delayed member can hold `w: "majority"` acknowledgement for the delay period when another secondary is down, and the lagging commit point causes cache pressure (delayed members page) |

Rules:

- Use at most one arbiter. Since 5.3 a second arbiter is refused unless every node starts with `--setParameter allowMultipleArbiters=true`. Do not host an arbiter on a data-bearing member's machine.
- Steer which member becomes primary with `priority`, never with `votes`. Members with `votes: 0` must have `priority: 0`.
- Spread members across failure domains so a majority survives the loss of any one domain.

Defaults seen on the images (`rs.conf().settings` and `members[0]`):

```text
chainingAllowed: true, heartbeatIntervalMillis: 2000, heartbeatTimeoutSecs: 10,
electionTimeoutMillis: 10000, catchUpTimeoutMillis: -1, catchUpTakeoverDelayMillis: 30000
member: priority 1, votes 1, hidden false, buildIndexes true, secondaryDelaySecs 0
```

## Elections and failover

- Members exchange heartbeats every 2 s. A member that does not answer within 10 s is marked inaccessible. Secondaries call an election after `electionTimeoutMillis` (10 s) without contact with the primary.
- With default settings, the median time to elect a new primary should not typically exceed 12 s. No writes are accepted until the election completes. Secondary reads continue.
- A primary that can see only a minority of voters steps down.
- Planned failover:

  ```javascript
  rs.stepDown(60)        // primary steps down and is not re-electable for 60 s
  rs.status().members.map(m => [m.name, m.stateStr, m.optimeDate])
  ```

  `rs.stepDown()` is shown as an election trigger in the manual. Its arguments are `stepDownSecs` (how long the node stays ineligible; must exceed the catch-up period) and `secondaryCatchUpPeriodSecs` (default 10). If no electable secondary catches up in time, the primary does not step down and the method errors. Writes fail for at most catch-up period + `electionTimeoutMillis` (10 s + 10 s by default) (rs.stepDown page).
- Applications must retry. Drivers retry eligible reads and writes once. Transactions retry on `TransientTransactionError`.
- Test failover in staging after every topology or driver change.

## Oplog sizing and the oplog window

- Default oplog size for WiredTiger on Linux and Windows: 5% of free disk, at least 990 MB and at most 50 GB. On macOS it is 192 MB. On the images, `rs.printReplicationInfo()`-equivalent data showed `maxSize` of about 45 GB on a large host disk.
- The oplog may grow past its configured size so that the majority commit point is not deleted.
- Workloads that need a larger oplog:
  - multi-document updates (each document becomes its own oplog entry);
  - deletes roughly equal to inserts;
  - many in-place updates;
  - resharding.
- Check the window:

  ```javascript
  rs.printReplicationInfo()          // size, used, first/last event, time window
  rs.printSecondaryReplicationInfo() // per-secondary lag behind the primary
  ```
- Resize online, without a restart. The change does not persist, so also set `replication.oplogSizeMB` / `storage.oplogMinRetentionHours` in the config file:

  ```javascript
  db.adminCommand({ replSetResizeOplog: 1, size: 51200 })          // MB
  db.adminCommand({ replSetResizeOplog: 1, minRetentionHours: 48 }) // keep at least 48 h
  ```

  On all four images (single-node replica set) both commands returned `ok: 1`. `local.oplog.rs.stats().maxSize` became 53687091200 bytes, and `serverStatus().oplogTruncation.oplogMinRetentionHours` showed `48`. `oplogMinRetentionHours` defaults to 0 (truncate by size only).
- Decision rule: the oplog window must exceed the longest planned member outage plus the initial sync or restore time of a replacement member, with margin. A secondary that falls off the window needs a full resync.

## Replication lag and flow control

- Measure lag with `rs.printSecondaryReplicationInfo()`, or by comparing `optimeDate` across members in `rs.status()`.
  - Since 8.0, `replSetGetStatus` also reports `optimeWritten` and `lastWrittenWallTime`, because secondaries write and apply in parallel.
  - 8.3 adds `metrics.repl.network.oplogFetcherLagSeconds`.
- Flow control throttles the primary to keep majority-committed lag under `flowControlTargetLagSeconds`. It is enabled by default (`enableFlowControl: true`, target 10 s on the images). Time spent throttled shows as `waitingForFlowControl` and `flowControlStats` in `$currentOp`. Since 8.0 it is excluded from `workingMillis`.
- Common causes of lag:
  - an undersized secondary;
  - index builds on secondaries;
  - long-running secondary reads holding the cache;
  - network limits;
  - large multi-updates.

## Initial sync and member maintenance

- Logical initial sync copies data and builds indexes. File copy based initial sync is Enterprise-only (`initialSyncMethod: fileCopyBased`).
  - Known issue SERVER-136961 (8.3+, 9.0+): a node that shut down uncleanly and then restarts into file copy based initial sync crash-loops. Set `initialSyncMethod: logical`, or empty `dbPath` and retry.
- From 8.2, 8.0.13, and 7.0.26, index builds during initial sync use `initialSyncIndexBuildMemoryPercentage` of RAM (default 10%, bounded 200 MB-16 GB).
- 9.0 reports `initialSyncStatus.phase`, `totalAttempts`, and `bytesPerSecond` in `replSetGetStatus`.
- Running `setFeatureCompatibilityVersion` during an initial sync restarts the sync.
- Maintenance on one member: remove it from read traffic, shut it down cleanly, do the work, restart it, and wait for `SECONDARY` before touching the next member. Do the primary last, after `rs.stepDown()`.

## When to shard

Shard when one replica set cannot hold the working set or the write throughput, or when data placement rules require it (zones). Sharding adds:
- `mongos` routing;
- a config server replica set, either dedicated or embedded as a config shard (8.0+);
- balancer migrations;
- and constraints: unique indexes must have the shard key as a prefix, single-document writes without the shard key are expensive, and scatter-gather queries do not scale linearly.

Before sharding:
- Scale vertically.
- Fix indexes and the data model.
- Use `moveCollection` (8.0+) to spread whole unsharded collections across shards when individual collections are small enough.

## Choose a shard key

Evaluate a candidate on four properties:

| Property | Want | Failure mode |
| --- | --- | --- |
| Cardinality | many distinct values | at most one range per distinct value; few values cap the useful shard count (example: `continent` gives 7) |
| Frequency | values evenly common | a hot value creates a jumbo range that cannot split |
| Monotonicity | not steadily increasing or decreasing | all inserts go to the `MaxKey` (or `MinKey`) range on one shard |
| Query targeting | the key appears in common queries | queries without it are broadcast to all shards |

Decision rules:

- Low cardinality or a hot value: use a compound key that adds a high-cardinality field.
- Monotonic key (ObjectId, timestamp) with insert-heavy load: use hashed sharding on it, or a compound key that leads with a non-monotonic field. Hashed keys give up range-query targeting.
- Equality queries on tenant or customer: lead with that field, then add a field that spreads within a tenant.
- Shard key indexes cannot be descending, partial, geospatial, multikey, text, or wildcard.
- Shard key values can be updated except on `_id`. Changes that move a document to another shard need a retryable write or a transaction and cost a migration. Avoid keys that change often.

## Evaluate a shard key before using it

Available from 7.0:

```javascript
// 1. sample live queries for the collection (runs on mongos for sharded, or the replica set)
db.orders.configureQueryAnalyzer({ mode: "full", samplesPerSecond: 10 })   // returns newConfiguration; "off" also returns oldConfiguration
// 2. after enough traffic (the manual suggests possibly several days):
db.orders.analyzeShardKey({ customerId: 1, createdAt: 1 },
                          { keyCharacteristics: true, readWriteDistribution: true })
// 3. stop sampling
db.orders.configureQueryAnalyzer({ mode: "off" })
```

Read the output:

- `keyCharacteristics`:
  - `numDistinctValues` is the maximum number of ranges; high is good.
  - `mostCommonValues[].frequency` times `avgDocSizeBytes` estimates the largest range.
  - `monotonicity.type` should not be `"monotonic"`.
  - A large `numOrphanDocs` skews results; wait for cleanup before measuring.
  - Requires a supporting index that is not multikey, sparse, or partial and has simple collation. Without one, the command errors (keyCharacteristics only) or omits that section.
  - On the 7.0, 8.0, 8.3, and 9.0 images, `analyzeShardKey({ customerId: 1 })` on a replica set failed while the only index starting with `customerId` was `{ customerId: 1, createdAt: -1 }`: the descending field is not a valid shard key (`numerical fields must be set to a value of 1`, wording varies by version). After adding `{ customerId: 1 }` it returned `numDocsTotal: 50000`, `numDistinctValues: 500`, five `mostCommonValues`, and `monotonicity.type: 'not monotonic'`. Create an ascending supporting index for the candidate key first.
- `readDistribution` / `writeDistribution`:
  - Want high `percentageOfSingleShardReads`/`Writes`, low `percentageOfScatterGather*`, and low `percentageOfShardKeyUpdates`.
  - `percentageOfSingleWritesWithoutShardKey` flags expensive writes.
  - These are omitted, or 0, if sampling was not configured.
- The command does not block reads or writes. It needs `enableSharding` on the collection, or `clusterManager`. It is unavailable on standalones, Atlas Flex, time series, and Queryable Encryption collections.

The images expose the defaults `analyzeShardKeyCharacteristicsDefaultSampleSize: 10000000`, `analyzeShardKeyNumMostCommonValues: 5`, and `analyzeShardKeyNumRanges: 100` (9.0 parameters file).

## Change a shard key: refine or reshard

| Option | What it does | Cost | Use when |
| --- | --- | --- | --- |
| `refineCollectionShardKey` | appends suffix fields to the existing key | updates chunk and zone ranges to include the new fields without moving data; later splits and migrations follow routine balancing (refineCollectionShardKey page). Needs an index on the refined key first | the prefix is right but cardinality is too low |
| `reshardCollection` | rewrites the collection under a new key | full copy; about 2 s of blocked writes at the end; at least 5 min | the key is wrong |
| `reshardCollection` with `forceRedistribution: true` (8.0+) | redistributes on the same key | as above | data is badly distributed and range migration is too slow |

Resharding checklist (production impact: write-heavy, oplog-heavy, and a short write block):

1. Free space on each recipient shard of at least `((collection storage size + index size) * 2) / number of shards`. The database does not enforce this; running out can shut a node down. Keep I/O below 50% and CPU below 80%.
2. Size the oplog generously, or fix its size, so secondaries do not go stale.
3. The prerequisites:
   - `writeConcernMajorityJournalDefault` must be true;
   - no index builds may be in progress;
   - `_id` must be unique across the cluster;
   - unique indexes must be compatible with the new key;
   - the balancer must be stopped.
4. Only one of `reshardCollection`, `moveCollection`, `unshardCollection`, and `rewriteCollection` runs at a time. While resharding runs, `collMod`, `createIndexes`, `drop`, `dropIndexes`, and `renameCollection` on the collection are refused.
5. Start it on `mongos`:

   ```javascript
   db.adminCommand({ reshardCollection: "shop.orders", key: { customerId: 1, orderId: 1 } })
   ```
6. Monitor:

   ```javascript
   db.getSiblingDB("admin").aggregate([
     { $currentOp: { allUsers: true, localOps: false } },
     { $match: { type: "op", "originatingCommand.reshardCollection": "shop.orders" } }
   ])
   ```

   Read `totalOperationTimeElapsedSecs` and `remainingOperationTimeEstimatedSecs` (`-1` at the start; the estimate is pessimistic).
7. Roll back before the commit phase with `db.adminCommand({ abortReshardCollection: "<db>.<coll>" })` (or `sh.abortReshardCollection()`); after the commit phase it returns an error. Afterwards, rebuild Atlas Search indexes and re-enable the balancer.

## Balancer, ranges, and placement

- Since 6.x the balancer distributes ranges by data size and does not auto-split. The AutoMerger is enabled by default (7.0+). The default range size is 128 MB.
- Stop the balancer before backups and resharding, and restart it afterwards:

  ```javascript
  sh.stopBalancer(); sh.getBalancerState(); /* false */  sh.startBalancer()
  ```
- Restrict migrations to off-peak hours with the balancer `activeWindow`. 8.3 adds `activeBalancerWindowDOW` for day-of-week windows.
- Inspect placement with `db.getSiblingDB("admin").aggregate([{ $shardedDataDistribution: {} }])`. It replaces the deprecated `cleanupOrphaned` for checking orphans. From 8.0 it reports the primary shard only if it owns data.
- Run `db.adminCommand({ checkMetadataConsistency: 1 })` on `mongos` after topology changes and upgrades. 9.0 adds the `performStrictChunkChecksIfBelowThreshold` option and new inconsistency types.

## Sharded cluster operations by version

| Operation | 7.0 | 8.0 | 8.3 | 9.0 |
| --- | --- | --- | --- | --- |
| `moveCollection` / `unshardCollection` | — | yes | yes | yes |
| Config shard (embedded config server) | — | yes | direct conversion via `--replicaSetConfigShardMaintenanceMode` | yes |
| Remove a shard | `removeShard` | `removeShard` | `startShardDraining` → `shardDrainingStatus` → `commitShardRemoval` (`removeShard` deprecated) | same, plus `sh.shardDrainingStatus()` |
| DDL directly on a shard | allowed | only listed commands without `directShardOperations` | only via `mongos` | only via `mongos` |
| `fsyncLock` via `mongos` | 7.0.2+ | yes | yes | yes |

9.0 sharded clusters: before upgrading, apply the `ShardingTaskExecutorPoolMinSizeForConfigServers` advice in [9.0](versions/9.0.md#upgrading-into-this-series).
