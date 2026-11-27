# Azure Cosmos DB Versions

Checked: 2026-11-27 against the Microsoft Learn pages listed under Sources. Azure Cosmos DB has no server releases or lifecycle page of its own. Lifecycle evidence comes from the MongoDB (RU) feature-support pages (end-of-support statements), the REST API reference (version table with retirement column), the SDK pages (retirement policy), and service change notes. Read when a behavior depends on when a feature shipped, on the MongoDB wire version of an account, or on the REST/SDK version in use.

## Support Status

| Track | Item | Type | Released | End of support | File |
| --- | --- | --- | --- | --- | --- |
| Service (all APIs) | Rolling service; dated feature changes 2024-2026 | Rolling, no versions | Continuous | n/a | [service-changes.md](service-changes.md) |
| Cosmos DB for MongoDB (RU) | Wire versions 3.2, 3.6, 4.0, 4.2, 5.0, 6.0, 7.0 | Engine-compatibility version per account | (dates not on the pages checked) | 3.2 and 3.6: "no current plans for end-of-support", at least three years' notice. Others: no end date published as of 2026-11-27; watch Azure Updates | [mongodb-ru-server-versions.md](mongodb-ru-server-versions.md) |
| Azure DocumentDB (formerly vCore) | MongoDB compatibility 5.0, 6.0, 7.0, 8.0 | Engine-compatibility version per cluster | 7.0: 2024-08-05; 8.0: 2025-05-05; 5.0 and 6.0 earlier (before the release notes start) | No lifecycle page published as of 2026-11-27 | [azure-documentdb.md](azure-documentdb.md) |
| Data-plane REST API | `x-ms-version` 2015-04-08 to 2018-12-31 | API version | 2018-12-31 is the newest listed | Only 2014-08-21 retired (2016-02-29) | [rest-api-and-sdks.md](rest-api-and-sdks.md) |
| NoSQL SDKs | .NET v3, Java v4, Python 4.x, JavaScript v4, Go `azcosmos`, Rust | SDK major versions | n/a | .NET v2 retired 2024-08-31; retirements announced 12 months ahead | [rest-api-and-sdks.md](rest-api-and-sdks.md) |
| Cosmos DB for PostgreSQL | Service | Retiring service | n/a | New deployments blocked; no retirement date found on an official page | [../apis.md](../apis.md#cosmos-db-for-postgresql) |
| Linux vNext emulator | `vnext-latest` image; release string `EN20261123` on 2026-11-27 | Container image | n/a | n/a | [../emulator.md](../emulator.md) |

The most recent item that reached end of support before 2026-11-27 is the .NET SDK v2 (2024-08-31); TLS 1.0 and 1.1 support ended 2025-08-31. Both are in the version files.

## Identify the Running Version

Account API, capacity mode, MongoDB wire version, consistency, backup mode, and feature flags (control plane):

```bash
az cosmosdb show -g <rg> -n <account> --query "{
  kind:kind,
  capabilities:capabilities[].name,
  mongoServerVersion:apiProperties.serverVersion,
  capacityMode:capacityMode,
  consistency:consistencyPolicy.defaultConsistencyLevel,
  multiWrite:enableMultipleWriteLocations,
  backup:backupPolicy.type,
  continuousTier:backupPolicy.continuousModeProperties.tier,
  minimalTls:minimalTlsVersion,
  disableLocalAuth:disableLocalAuth,
  dynamicScaling:enablePerRegionPerPartitionAutoscale,
  priorityExecution:enablePriorityBasedExecution,
  burst:enableBurstCapacity,
  partitionMerge:enablePartitionMerge,
  allVersionsAndDeletes:enableAllVersionsAndDeletesChangeFeed}"
```

Property names are from the `Microsoft.DocumentDB/databaseAccounts` ARM reference (2026-04-01-preview schema); some appear only in preview API versions, so a stable-version CLI may print `null` for them.

Data plane (any client with a key or Entra token, or the emulator without auth):

- `GET https://<account>.documents.azure.com/` returns `writableLocations`, `readableLocations`, `userConsistencyPolicy`, and `enableMultipleWriteLocations`.
- Response headers on every call include `x-ms-serviceversion` (service version) and `x-ms-schemaversion` per the REST reference. The vNext emulator returned `x-ms-gatewayversion: 2.0.0-unknown` and no `x-ms-serviceversion`.
- The REST version used is the `x-ms-version` request header the client sends.

SDK version: read it from the application's package manifest. The `UserAgent` column of `CDBDataPlaneRequests` holds only the suffix the application sets when it creates the client, and only in Direct mode (Azure Monitor table reference), so put the SDK version in that suffix if you want it in the logs.

MongoDB (RU): `apiProperties.serverVersion` above. The endpoint suffix also tells 3.2 (`.documents.azure.com`) from 3.6+ (`.mongo.cosmos.azure.com`).

Azure DocumentDB: the cluster's Overview page shows the MongoDB version, and the Upgrade button is disabled on the latest version. CLI: `az documentdb mongocluster show -g <rg> -n <cluster> -o json` (preview extension) and read the server version under `properties`; `--server-version` belongs to the Properties argument group, so `properties.serverVersion` is the likely path. From `mongosh`, compare `db.version()` with that value; no page documents its output on Azure DocumentDB.

Emulator: the first container log line (`Release Version: EN20261123`) and `docker run <image> --help`.

## Upgrade Paths

Service features: there is nothing to upgrade. New features arrive on the rolling service; many are opt-in per account (Features pane, `az cosmosdb update`, or ARM properties). Opt-in features with one-way effects:

| Change | Reversible | Pre-check |
| --- | --- | --- |
| Periodic to continuous backup | No | Not Cassandra; never disabled Synapse Link; CMK default identity set; MongoDB unique indexes created first |
| Serverless to provisioned | No | NoSQL only; no SLA on duration; no management operations during it |
| `EnableMongo16MBDocumentSupport`, `EnableMongoRoleBasedAccessControl`, other non-removable MongoDB capabilities | No | Not with CMK (16 MB); test on a copy |
| Partition merge (preview) | Feature can be disabled, merges can't be undone; account loses all versions and deletes eligibility | Every client on a supported SDK |
| PPAF | The configuration page describes enabling it and a fault simulation you can stop, but no way to turn PPAF off; ask support before enabling it in production | Every client on a supported SDK; supported consistency level |
| `disableLocalAuth` | Yes | No client uses keys |

MongoDB (RU) wire version: in-place through Features > Upgrade MongoDB server version (about 15 minutes, no downtime, no RU cost). Downgrade to 4.0 or 3.6 is possible through the same pane; 3.2 upgrades keep the old endpoint for rollback. See [mongodb-ru-server-versions.md](mongodb-ru-server-versions.md#upgrading-into-this-series).

Azure DocumentDB: in place through the portal Upgrade button to a newer MongoDB version. The upgrade page documents no downgrade; rehearse on a restored cluster.

SDK majors: follow the vendor migration guides (.NET v2 to v3). Feature-specific SDK minimums are listed in [rest-api-and-sdks.md](rest-api-and-sdks.md).

Generic procedure for any of the above:

1. Pre-check: read the current configuration with the commands above; list clients and their SDK or driver versions; read the target version file for blockers.
2. Rehearse: restore the account (continuous backup) or cluster into a new resource at a recent time, apply the change there, and run the application's integration tests and top queries against it. Record RU charges (Azure, not the emulator) before and after.
3. Switch: apply the change to production in a low-traffic period; for one-way changes, take a fresh restore point first and record the timestamp.
4. Post-check: verify the property in `az cosmosdb show`, watch 429 rate, latency, and error codes in Azure Monitor for at least one traffic cycle, and confirm application error logs are clean.

## Outside the Covered Range

- Older than covered (MongoDB 3.2 accounts, REST versions before 2018-12-31, SDKs below the feature minimums): read the 3.2 feature-support page, the REST version table, and the SDK changelog on GitHub for the SDK in use. Claims here about transactions, indexes, hierarchical keys, priority execution, throughput buckets, and PPAF don't hold for old SDKs, because those features need minimum SDK versions.
- Newer than covered (features after 2026-11-27, a new MongoDB wire version, a new Azure DocumentDB compatibility version): read the Azure DocumentDB release notes, the MongoDB (RU) feature-support page for that version, the Cosmos DB documentation pages for the feature, and Azure Updates. Limits, preview status, and defaults in this reference may have changed.
- Every answer for an account or SDK outside these ranges must state the gap (for example "this reference was checked on 2026-11-27; your account uses X").

## Sources

All checked 2026-11-27.

- Azure Cosmos DB documentation hub — https://learn.microsoft.com/en-us/azure/cosmos-db/ — checked 2026-11-27
- Service quotas and default limits — https://learn.microsoft.com/en-us/azure/cosmos-db/concepts-limits — checked 2026-11-27
- Microsoft.DocumentDB/databaseAccounts ARM reference — https://learn.microsoft.com/en-us/azure/templates/microsoft.documentdb/databaseaccounts — checked 2026-11-27
- Supported REST API versions — https://learn.microsoft.com/en-us/rest/api/cosmos-db/ — checked 2026-11-27
- Common REST request headers — https://learn.microsoft.com/en-us/rest/api/cosmos-db/common-cosmosdb-rest-request-headers — checked 2026-11-27
- Common REST response headers — https://learn.microsoft.com/en-us/rest/api/cosmos-db/common-cosmosdb-rest-response-headers — checked 2026-11-27
- .NET SDK v2 page (retirement) — https://learn.microsoft.com/en-us/azure/cosmos-db/sql-api-sdk-dotnet — checked 2026-11-27
- MongoDB (RU) upgrade version — https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/upgrade-version — checked 2026-11-27
- MongoDB (RU) 3.2 feature support — https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/feature-support-32 — checked 2026-11-27
- MongoDB (RU) 3.6 feature support — https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/feature-support-36 — checked 2026-11-27
- MongoDB (RU) 4.2 feature support — https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/feature-support-42 — checked 2026-11-27
- MongoDB (RU) 7.0 feature support — https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/feature-support-70 — checked 2026-11-27
- MongoDB (RU) capabilities — https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/how-to-configure-capabilities — checked 2026-11-27
- MongoDB (RU) error codes — https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/error-codes-solutions — checked 2026-11-27
- MongoDB (RU) consistency mapping — https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/consistency-mapping — checked 2026-11-27
- Azure DocumentDB release notes — https://learn.microsoft.com/en-us/azure/documentdb/release-notes — checked 2026-11-27
- Azure DocumentDB at a glance — https://learn.microsoft.com/en-us/azure/documentdb/at-a-glance — checked 2026-11-27
- Azure DocumentDB FAQ — https://learn.microsoft.com/en-us/azure/documentdb/faq — checked 2026-11-27
- Azure DocumentDB upgrade a cluster — https://learn.microsoft.com/en-us/azure/documentdb/how-to-upgrade-cluster — checked 2026-11-27
- Azure DocumentDB limitations — https://learn.microsoft.com/en-us/azure/documentdb/limitations — checked 2026-11-27
- Azure DocumentDB feature compatibility — https://learn.microsoft.com/en-us/azure/documentdb/compatibility-features — checked 2026-11-27
- Azure DocumentDB high availability — https://learn.microsoft.com/en-us/azure/documentdb/high-availability — checked 2026-11-27
- Reliability in Azure DocumentDB — https://learn.microsoft.com/en-us/azure/reliability/reliability-documentdb — checked 2026-11-27
- Cosmos DB for PostgreSQL overview — https://learn.microsoft.com/en-us/azure/cosmos-db/postgresql/introduction — checked 2026-11-27
- Migrate Cosmos DB for PostgreSQL to elastic clusters — https://learn.microsoft.com/en-us/azure/cosmos-db/postgresql/concepts-benefits-database-postgresql — checked 2026-11-27
- Cosmos DB for PostgreSQL product updates — https://learn.microsoft.com/en-us/azure/cosmos-db/postgresql/product-updates — checked 2026-11-27
- Linux vNext emulator — https://learn.microsoft.com/en-us/azure/cosmos-db/emulator-linux — checked 2026-11-27
- Partitioning — https://learn.microsoft.com/en-us/azure/cosmos-db/partitioning — checked 2026-11-27
- Hierarchical partition keys — https://learn.microsoft.com/en-us/azure/cosmos-db/hierarchical-partition-keys — checked 2026-11-27
- Global secondary indexes — https://learn.microsoft.com/en-us/azure/cosmos-db/global-secondary-indexes — checked 2026-11-27
- Configure global secondary indexes — https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-configure-global-secondary-indexes — checked 2026-11-27
- Consistency levels — https://learn.microsoft.com/en-us/azure/cosmos-db/consistency-levels — checked 2026-11-27
- Request units — https://learn.microsoft.com/en-us/azure/cosmos-db/request-units — checked 2026-11-27
- Autoscale and dynamic scaling — https://learn.microsoft.com/en-us/azure/cosmos-db/provision-throughput-autoscale — checked 2026-11-27
- Serverless — https://learn.microsoft.com/en-us/azure/cosmos-db/serverless — checked 2026-11-27
- Change from serverless to provisioned — https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-change-capacity-mode — checked 2026-11-27
- Throughput buckets — https://learn.microsoft.com/en-us/azure/cosmos-db/throughput-buckets — checked 2026-11-27
- Priority-based execution — https://learn.microsoft.com/en-us/azure/cosmos-db/priority-based-execution — checked 2026-11-27
- Burst capacity — https://learn.microsoft.com/en-us/azure/cosmos-db/burst-capacity — checked 2026-11-27
- Partition merge (preview) — https://learn.microsoft.com/en-us/azure/cosmos-db/merge — checked 2026-11-27
- Indexing policies — https://learn.microsoft.com/en-us/azure/cosmos-db/index-policy — checked 2026-11-27
- Index metrics — https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/index-metrics — checked 2026-11-27
- Change feed — https://learn.microsoft.com/en-us/azure/cosmos-db/change-feed — checked 2026-11-27
- Change feed modes — https://learn.microsoft.com/en-us/azure/cosmos-db/change-feed-modes — checked 2026-11-27
- Multi-region writes — https://learn.microsoft.com/en-us/azure/cosmos-db/multi-region-writes — checked 2026-11-27
- Conflict resolution policies — https://learn.microsoft.com/en-us/azure/cosmos-db/conflict-resolution-policies — checked 2026-11-27
- Reliability in Azure Cosmos DB for NoSQL — https://learn.microsoft.com/en-us/azure/reliability/reliability-cosmos-db-nosql — checked 2026-11-27
- Per-partition automatic failover — https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-configure-per-partition-automatic-failover — checked 2026-11-27
- Continuous backup — https://learn.microsoft.com/en-us/azure/cosmos-db/continuous-backup-restore-introduction — checked 2026-11-27
- Restore with continuous backup — https://learn.microsoft.com/en-us/azure/cosmos-db/restore-account-continuous-backup — checked 2026-11-27
- Latest restorable timestamp — https://learn.microsoft.com/en-us/azure/cosmos-db/get-latest-restore-timestamp — checked 2026-11-27
- Migrate to continuous backup — https://learn.microsoft.com/en-us/azure/cosmos-db/migrate-continuous-backup — checked 2026-11-27
- Periodic backup — https://learn.microsoft.com/en-us/azure/cosmos-db/periodic-backup-restore-introduction — checked 2026-11-27
- Modify periodic backup — https://learn.microsoft.com/en-us/azure/cosmos-db/periodic-backup-modify-interval-retention — checked 2026-11-27
- Azure Backup what's new — https://learn.microsoft.com/en-us/azure/backup/whats-new — checked 2026-11-27
- About Azure Cosmos DB vaulted backup — https://learn.microsoft.com/en-us/azure/backup/backup-azure-cosmos-db-overview — checked 2026-11-27
- RBAC with Microsoft Entra ID — https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-connect-role-based-access-control — checked 2026-11-27
- Minimum TLS enforcement — https://learn.microsoft.com/en-us/azure/cosmos-db/self-serve-minimum-tls-enforcement — checked 2026-11-27
- Diagnostic settings — https://learn.microsoft.com/en-us/azure/cosmos-db/monitor-resource-logs — checked 2026-11-27
- Troubleshoot 429 — https://learn.microsoft.com/en-us/azure/cosmos-db/troubleshoot-request-rate-too-large — checked 2026-11-27
- API for Cassandra support — https://learn.microsoft.com/en-us/azure/cosmos-db/cassandra/support — checked 2026-11-27
- API for Cassandra .NET quickstart (capability name) — https://learn.microsoft.com/en-us/azure/cosmos-db/cassandra/quickstart-dotnet — checked 2026-11-27
- API for Gremlin support — https://learn.microsoft.com/en-us/azure/cosmos-db/gremlin/support — checked 2026-11-27
- API for Table support — https://learn.microsoft.com/en-us/azure/cosmos-db/table/support — checked 2026-11-27
- API for Table FAQ — https://learn.microsoft.com/en-us/azure/cosmos-db/table/faq — checked 2026-11-27
- Container run of `mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:vnext-latest` (release EN20261123, arm64; same index digest `sha256:c274ac17c19a5f74dbadbc99f259bc49a8640a03f6789f54d7f76cbfc33ff6b6` as `vnext-preview`, which the runs used): REST requests, startup log, and `--help` output — run 2026-11-27
