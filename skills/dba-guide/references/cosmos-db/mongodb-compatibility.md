# MongoDB Compatibility: Cosmos DB for MongoDB (RU) and Azure DocumentDB

Checked: 2026-11-27. Read when a MongoDB application runs on, or is moving to, Azure. Two unrelated engines carry MongoDB compatibility on Azure; identify which one first. For MongoDB server semantics use `../mongodb/` files (for example [data modeling](../mongodb/data-modeling.md), [transactions](../mongodb/transactions-and-consistency.md), [indexes](../mongodb/indexes-and-query-plans.md)); for Amazon DocumentDB use [../documentdb/compatibility.md](../documentdb/compatibility.md).

## Contents

- [Which offering is this](#which-offering-is-this)
- [Side-by-side](#side-by-side)
- [Cosmos DB for MongoDB (RU)](#cosmos-db-for-mongodb-ru)
- [RU offering: unsupported or different](#ru-offering-unsupported-or-different)
- [RU offering: capabilities](#ru-offering-capabilities)
- [RU offering: errors](#ru-offering-errors)
- [Azure DocumentDB](#azure-documentdb)
- [Azure DocumentDB operations](#azure-documentdb-operations)
- [Migration paths](#migration-paths)
- [Common mistakes](#common-mistakes)

## Which offering is this

| Signal | Cosmos DB for MongoDB (RU) | Azure DocumentDB |
| --- | --- | --- |
| Former name | Azure Cosmos DB API for MongoDB | vCore-based Azure Cosmos DB for MongoDB (renamed 2025-11-18) |
| Host name | `<account>.mongo.cosmos.azure.com` (3.6+); `<account>.documents.azure.com` (3.2) | Copy the connection string from the cluster's Connection strings page, or `az documentdb mongocluster list-connection-strings -g <rg> -n <cluster>` |
| Control plane | `az cosmosdb show` returns it; `kind: MongoDB`, `apiProperties.serverVersion` | Not a Cosmos DB account; cluster resource with tiers M10-M200 |
| Billing | Request units | vCores, memory, storage |
| Engine | Cosmos DB engine with a MongoDB wire-protocol layer; Microsoft doesn't run MongoDB | Open-source DocumentDB engine (MIT license) on PostgreSQL; doesn't run MongoDB code, so SSPL doesn't apply |

The rename didn't change existing clusters, connection strings, or APIs (Azure DocumentDB FAQ). Microsoft's MongoDB (RU) pages now open with a note pointing MongoDB migrations and MQL-dependent apps to Azure DocumentDB, and high-scale apps to Cosmos DB for NoSQL.

## Side-by-side

| Area | Cosmos DB for MongoDB (RU) | Azure DocumentDB |
| --- | --- | --- |
| Wire versions | `3.2`, `3.6`, `4.0`, `4.2`, `5.0`, `6.0`, `7.0` (ARM `serverVersion` enum) | 5.0, 6.0, 7.0, 8.0 |
| Multi-document transactions | Only within one unsharded collection; fixed 5-second timeout | Supported (ACID); maximum transaction lifetime 30 seconds |
| `$lookup` | Partial: no `let`/`pipeline` (uncorrelated subqueries) | Supported (all 181 aggregation operators and 58 of 60 stages per the at-a-glance page) |
| Sharding | Automatic; shard key = partition key fixed at collection creation; no manual sharding commands | Shard existing collections online; unsharded collections up to 32 TiB; up to 10 physical shards |
| Document size | 2 MB; 16 MB with `EnableMongo16MBDocumentSupport` | 16 MB |
| Write concern | Ignored; all writes quorum, governed by account consistency | Not described on the limitations page. The reliability page says HA replicates synchronously from each primary shard to its standby; without HA there is no standby. Check that HA is enabled on the cluster's High availability page before relying on acknowledged writes surviving a node failure |
| Users and roles | Keys and Azure RBAC; native Mongo RBAC through `EnableMongoRoleBasedAccessControl` | Native users (up to 100 users/roles per cluster; roles at cluster level only) and Microsoft Entra ID |
| Multi-region | Any number of regions, multi-region writes, five consistency levels | One secondary region (replica cluster); promotion or service-managed failover |
| Backup | Periodic or continuous (7, 30, or 35 days) | Automatic; 35 days for active clusters, 7 days for burstable and deleted clusters |
| Throttling | Error 16500 when RU/s exceeded | No RUs; limits are the tier's CPU, memory, and IOPS |
| Text search | `text` indexes and `$text` not supported | `text` indexes (one per collection); full-text search indexes (preview) |
| Vector search | (not covered here) | DiskANN and HNSW on M30 and larger |

## Cosmos DB for MongoDB (RU)

Version facts:

- Accounts on 3.6 or later use the `*.mongo.cosmos.azure.com` endpoint. 3.2 accounts use `*.documents.azure.com`.
- The 3.2 and 3.6 feature-support pages say those versions have no current plans for end of support and that the minimum notice for a future end of support is three years.
- 4.0 and later store BSON more efficiently; documents written before an upgrade benefit only after they are rewritten through the new endpoint.

Upgrade procedure (upgrade-version page):

1. Upgrade drivers to versions compatible with the target wire version first. Test on dev/test accounts.
2. Portal > account > Features > Upgrade MongoDB server version > choose the target. The upgrade takes about 15 minutes, doesn't interrupt availability, and doesn't consume RU/s or change data or indexes.
3. From 3.2: switch every application to the new `*.mongo.cosmos.azure.com` connection string; only connections through the new endpoint get the new features. Create compound indexes for any multi-field sort first, because 3.6+ requires them.
4. Downgrade: back to 4.0 or 3.6 through the same Features pane. An account upgraded from 3.2 returns to 3.2 by using the old `*.documents.azure.com` connection string, which stays active.

The same page warns that only qualifying 3.2 accounts can currently be upgraded to 3.6 and higher, and to file a support ticket otherwise; its steps also mention upgrading from 3.6 and selecting 4.0 or 4.2. The page describes no self-service path beyond 4.2. Open the account's Features pane: if `Upgrade MongoDB server version` does not offer the target version, file a support ticket as the page says.

Read the configured version:

```bash
az cosmosdb show -g <rg> -n <account> --query "{kind:kind, serverVersion:apiProperties.serverVersion, capabilities:capabilities[].name}"
```

In `mongosh`, `buildInfo` and `hello` are supported commands; `serverStatus` is not. No page says what `db.version()` reports on a RU account. Compare it with `az cosmosdb show -g <rg> -n <account> --query apiProperties.serverVersion` and trust the ARM value.

## RU offering: unsupported or different

From the 7.0 feature-support page (earlier versions support less; check the page for the account's version):

| Area | Not supported or limited |
| --- | --- |
| Commands | `eval`, `getPrevError`, `parallelCollectionScan`, `resetError`, `collMod`, `connectionStatus`, `convertToCapped`, `copydb`, `killOp`, `renameCollection`, `serverStatus`, `top`, `profiler`, `listCommands`, `dbHash`, `dataSize`, `connPoolStats`, `mapReduce` |
| Aggregation stages | `$bucket`, `$bucketAuto`, `$graphLookup`, `$collStats`, `$currentOp`, `$indexStats`, `$listSessions`; `$lookup` partial; `$meta` not supported |
| Indexes | No text, 2d, or hashed indexes; no sparse or case-insensitive indexes; partial only for unique indexes |
| Query operators | No `$jsonSchema`, `$text`, `$where`; `$regex` uses the index only when left-anchored without `i` or `m`; no `$center`, `$centerSphere`, `$box`, `$polygon`; no `$bitsAllSet` family |
| Transactions | Single unsharded collection only; fixed 5-second timeout (error 2 "Transaction isn't active" when exceeded) |
| Sessions | Server-side session commands not supported |
| Sort | `findOneAndUpdate` sorts on one field only. Multi-field sorts need a compound index (error 2 `BadValue` otherwise) |
| Replication and sharding commands | Not supported; the service manages both |
| Write concern | Ignored; consistency follows the account level ([consistency-and-replication.md](consistency-and-replication.md)) |
| Client-side field-level encryption | Explicit encryption supported; automatic encryption not; don't run `mongocryptd` |
| Execution time | 60 seconds per operation for 3.6 and 4.0 (error 50 `ExceededTimeLimit`) |
| Idle connections | Closed server-side after 30 minutes; the Azure load balancer drops idle TCP at 4 minutes. Set the driver idle timeout to 1-3 minutes (`maxIdleTimeMS=120000`) |

TTL: either the `_ts`-based TTL, or one custom TTL field per collection after enabling `EnableTtlOnCustomPath` (can't be combined with `_ts`; not available with continuous backup). Create it with `db.coll.createIndex({"expireAt": 1}, {expireAfterSeconds: 10})`.

Retryable writes (capability `EnableMongoRetryableWrites`): updates and deletes on sharded collections must then include the shard key, or fail with `ShardKeyNotFound` (61). Bulk unordered writes aren't supported with retryable writes; use ordered bulk writes.

## RU offering: capabilities

Set with `az cosmosdb update --capabilities` and always list every capability to keep (the list replaces the current one). ARM templates can't change capabilities for this API.

| Capability | Effect | Removable |
| --- | --- | --- |
| `DisableRateLimitingResponses` | Server-side retry of rate-limited requests up to the max request timeout | Yes |
| `EnableMongoRetryableWrites` | Retryable writes | Yes |
| `EnableMongoRoleBasedAccessControl` | Native MongoDB users and roles | No |
| `EnableMongo16MBDocumentSupport` | 16 MB documents (new collections only; not with CMK) | No |
| `EnableUniqueCompoundNestedDocs` | Compound and unique indexes on non-array nested fields | No |
| `EnableTtlOnCustomPath` | One custom TTL field per collection (not with continuous backup) | No |
| `EnablePartialUniqueIndex` | Unique partial indexes | No |

```bash
az cosmosdb show -g <rg> -n <account> --query "capabilities[].name"
az cosmosdb update -g <rg> -n <account> --capabilities EnableMongo DisableRateLimitingResponses
```

Risk: the list passed to `--capabilities` replaces the account's list. Read the current list first and include `EnableMongo` and every capability you keep.

The 7.0 feature page still says users and roles are not supported, while the capabilities page lists `EnableMongoRoleBasedAccessControl`. Treat native RBAC as available through the capability and test it.

## RU offering: errors

| Code | Name | Meaning and fix |
| --- | --- | --- |
| 2 | BadValue | Sort on an unindexed or excluded path, or no matching compound index; create the index |
| 2 | Transaction isn't active | Transaction exceeded 5 seconds; shrink it |
| 13 | Unauthorized | Wrong key or missing permission |
| 50 | ExceededTimeLimit | Over 60 seconds; often too few RU/s or too large a request. Retrying a write can duplicate it |
| 61 | ShardKeyNotFound | Shard key missing from the document or filter |
| 66 | ImmutableField | Attempt to change `_id` or the shard key |
| 67 | CannotCreateIndex | Over 500 single-field indexes, or over 8 fields in a compound index |
| 112 | WriteConflict | Conflicting transaction; retry |
| 115 | CommandNotSupported | Unsupported command |
| 11000 | DuplicateKey | Shard key plus `_id`, or unique index, violated |
| 16500 | TooManyRequests | RU/s exceeded; retry, raise RU/s, or enable server-side retry |
| 16501 | ExceededMemoryLimit | 3.2 only; narrow the query |

The error-codes page still describes the implementation as wire versions 4.0, 3.6, and 3.2, older than the version list elsewhere; read it for codes, not for version support.

## Azure DocumentDB

Version and release facts (service release notes, at-a-glance page):

| Date | Change |
| --- | --- |
| 2024-08-05 | MongoDB 7.0 compatibility ("v7") released |
| 2025-01-23 | Engine open-sourced (github.com/documentdb) |
| 2025-02-12 | Autoscale GA; geo-replica promotion; `pg_documentdb` build for PostgreSQL 17 |
| 2025-05-05 | "v8" released (MongoDB 8.0 compatibility) |
| 2025-08-29 | Index hints supported; CMK and Microsoft Entra ID GA (infrastructure 0909) |
| 2025-10-10 | API version `2025-09-01` (Data API, Entra ID, CMK, option to disable native auth); `$jsonSchema` validation (preview) |
| 2025-11-18 | Renamed to Azure DocumentDB; Index Advisor, migration extension; RU-to-DocumentDB migration path |

The release-notes page lists nothing after 2025-11-18 as of 2026-11-27.

Upgrade: portal > cluster Overview > Upgrade, then choose the target MongoDB version; the button is disabled when the cluster is on the latest version. That page describes only upgrading; it mentions no downgrade, rollback or replica clusters. Rehearse on a restored copy of the cluster first. Details in [versions/azure-documentdb.md](versions/azure-documentdb.md).

Unsupported or limited (compatibility-features and limitations pages):

- Time series, capped, and clustered collections.
- `$planCacheStats`, `$listSearchIndexes`, `$listSampledQueries`, `$shardedDataDistribution`.
- Replication commands, most sharding commands (you keep `getShardMap`, `balancerStart`, `balancerStatus`, `balancerStop`), and administration, diagnostic, and monitoring commands are handled by the service; use Azure Monitor and Log Analytics.
- `$killAllSessionsByPattern` and `$killSessions` are restricted.
- Indexes: compound up to 32 fields; default 64 indexes per collection (configurable to 300); index path 256 bytes; one index build at a time per collection; unique index builds run in the foreground and block writes on the collection; use `currentOp` to watch long builds.
- The limitations page says sorting is done in memory and isn't pushed down to the index, while release notes describe `$sort` index pushdown in preview. Check `explain()` output for the query in question.
- Geospatial: no BigPolygons; `$geoWithin` without holes; `key` required in `$geoNear`.
- Query defaults: 120-second execution limit (override with `maxTimeMS`), cursor lifetime 10 minutes, transaction lifetime 30 seconds, 25,000 writes per batch, 16 MB documents, query memory by tier (about 150 MiB on M80); cross-node data in a sharded query capped at 1 GB.
- `explain()` adds modes `allShardsQueryPlan` and `allShardsExecution` for multi-shard plans.

## Azure DocumentDB operations

Tiers and topology:

- M10, M20, M25: one physical shard, no in-region HA, storage 32/64/128 GiB, for dev/test. After scaling to M30 or higher you can't scale back to them.
- Maximum M200 (64 vCores, 256 GiB RAM per shard); up to 10 physical shards. Storage can grow but not shrink. Up to 32 TB per node (at-a-glance page).
- Free tier: 32 GB, one per subscription; no HA, Entra ID, backup, diagnostic logs, or HNSW/DiskANN; paused after 60 days without connections; upgradeable in place to a paid tier but not back.

High availability:

- HA keeps a synchronous standby for each primary shard; failover loses no data and the connection string doesn't change. Reads continue during the switch; writes may see internal retries.
- `highAvailability.targetMode`: `ZoneRedundantPreferred` (recommended; falls back to same-zone when zones aren't available) or `SameZone` (not in the portal).
- HA can be enabled or disabled on an existing cluster without downtime.
- SLA: the HA page says 99.99% per shard with HA; the FAQ says 99.995% for highly available configurations. Quote the SLA document, not either page.

Cross-region replication:

- One secondary region (replica cluster). Storage, shard count, and users are inherited and can't be changed on the replica; the replica has no PITR and no in-region HA. Not available on burstable or free clusters.
- Graceful promotion needs the primary reachable to drain the replication queue; use forced promotion or service-managed failover when the primary region is down. Service-managed failover is opt-in and must be enabled before an outage.

Backup and restore:

- Automatic continuous backups, stored in three zones where available; can't be exported. Retention: 35 days for active clusters, 7 days for burstable (M10, M20, M25) clusters and for deleted clusters (reliability guide).
- Restore creates a new cluster at a chosen point in time; then complete the post-restore tasks (network rules, users) from the restore how-to.
- The FAQ says PITR up to 35 days applies to production tiers (M30 and larger), and the limitations page says backup and restore start at M25; the reliability guide gives 7 days for M10-M25. Use the reliability guide figures and confirm for the tier.

Security: native users plus Microsoft Entra ID (no Entra groups); native auth can be disabled (the portal Quick start shell then doesn't work); TLS enforced; firewall rules and Private Link. CMK must be chosen at creation (switch by creating a replica or restoring with the other mode) and blocks adding physical shards.

Monitoring: Azure Monitor metrics (CPU, memory, storage, IOPS, requests) and diagnostic logs to Log Analytics (paid tiers); `explain()` and Index Advisor in the VS Code extension for query tuning.

## Migration paths

| From | To | Tool | Notes |
| --- | --- | --- | --- |
| MongoDB (Atlas, VMs, on-premises), Amazon DocumentDB | Azure DocumentDB | DocumentDB migration extension for VS Code (assessment plus online or offline), Azure Database Migration Service, `mongodump`/`mongorestore` | Online migration needs change streams on the source and enough oplog for the window |
| Cosmos DB for MongoDB (RU) | Azure DocumentDB | Integrated migration path listed in the 2025-11-18 release notes | Run the compatibility assessment; the target supports more features, not fewer |
| MongoDB | Cosmos DB for MongoDB (RU) | Azure Database Migration Service | Check the unsupported-features table above against the app first |

Generic procedure: run the compatibility assessment; restore a copy and run the integration tests against a test cluster; migrate online; compare counts and sample documents per collection; cut over; keep the source intact until rollback is no longer needed.

## Common mistakes

- Treating Azure DocumentDB as Amazon DocumentDB because of the name.
- Expecting cross-collection transactions, `$lookup` pipelines, `$text`, or `serverStatus` on the RU offering.
- Setting `writeConcern` on the RU offering to get durability; it is ignored.
- Forgetting the RU offering's 60-second operation limit and 5-second transaction limit in batch jobs.
- Assuming a free-tier or M10-M25 cluster has HA or the same backup retention as production tiers.
- Dropping capabilities by passing a partial list to `az cosmosdb update --capabilities`.
