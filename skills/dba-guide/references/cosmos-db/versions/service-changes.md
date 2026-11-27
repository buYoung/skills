# Azure Cosmos DB Service Changes, 2024-2026

Checked: 2026-11-27. Read when an account's behavior depends on when it was created or on a dated platform change (TLS, dynamic scaling, backup tiers, retired SDKs, vaulted backup). Cosmos DB has no consolidated release-notes page; each entry below comes from the feature page named.

## Lifecycle

Rolling managed service; no versions, no end-of-support dates for the service itself. Individual features move through preview to GA and can be retired with notice: SDK retirements get 12 months' notice (SDK page). Preview features have no SLA and often need a preview management API version.

Dated changes found:

| Date | Change | Source page |
| --- | --- | --- |
| 2024-08-31 | .NET SDK v2 retired (keeps working; no fixes or support) | sql-api-sdk-dotnet |
| 2024-09-25 | Dynamic scaling (per-region, per-partition autoscale) on by default for accounts created after this date | provision-throughput-autoscale |
| 2025-03-31 | TLS 1.3 enabled for Cosmos DB | self-serve-minimum-tls-enforcement |
| 2025-08-31 | TLS 1.0 and 1.1 retired; all accounts must use TLS 1.2 or higher | self-serve-minimum-tls-enforcement |
| 2025-11-18 | vCore-based Azure Cosmos DB for MongoDB renamed Azure DocumentDB, a separate service | documentdb/release-notes |
| 2026-05 | Azure Backup vaulted backup for Cosmos DB in preview | backup/whats-new |
| 2026-07-01 | Charges for vaulted backup start | backup/backup-azure-cosmos-db-overview |
| 2026-11 | Vaulted backup for Cosmos DB generally available | backup/whats-new |
| (date not found) | Continuous backup `Continuous35Days` tier added next to 7 and 30 days | continuous-backup-restore-introduction, ARM schema |
| (date not found) | Cosmos DB for PostgreSQL new deployments blocked; service on retirement path | postgresql/concepts-benefits-database-postgresql |

## Changed Defaults

- Accounts created after 2024-09-25: autoscale containers and databases scale per partition and per region (dynamic scaling), billed on the aggregated scaled RU/s. Older accounts keep uniform autoscale until the feature is enabled.
- `minimalTlsVersion` defaults to `Tls12` for new accounts; TLS below 1.2 is no longer accepted on any account after 2025-08-31. The ARM reference description still says the default is TLS 1.0 except for Cassandra and MongoDB; the TLS page supersedes it.
- `az cosmosdb update --backup-policy-type Continuous` without a tier migrates to `Continuous30Days`.
- Priority-based execution, once enabled, treats requests without a priority as High; Data Explorer requests run at Low.

## Removed or Deprecated

- .NET SDK v2 (retired 2024-08-31). Use .NET SDK v3.
- TLS 1.0 and 1.1 (retired 2025-08-31).
- Lazy indexing mode can't be chosen for new containers.
- Azure Synapse Link is labeled deprecated on the continuous-backup page; accounts that disabled it on a container can't migrate to continuous backup, and analytical store data isn't backed up. Microsoft points analytics to Fabric mirroring (documentation hub).
- The attachment feature is being deprecated (service-quotas page; 2 GB attachment limit per account).
- Cosmos DB for PostgreSQL: no new deployments.

## Worth Adopting

| Feature | Why it changes a decision | Status on the pages checked | Details |
| --- | --- | --- | --- |
| Continuous backup (7-day tier) | Self-service PITR with no backup storage charge; prerequisite for GSIs, all versions and deletes change feed, and vaulted backup | GA | [operations.md](../operations.md#backup-and-restore) |
| Vaulted backup (Azure Backup) | Retention up to 10 years, immutable, isolated from the account | GA 2026-11 | [operations.md](../operations.md#long-term-retention-with-azure-backup) |
| Dynamic scaling | Cheaper multi-region and skewed workloads on autoscale | GA; default since 2024-09-25 | [request-units-and-indexing.md](../request-units-and-indexing.md#capacity-modes) |
| Per-partition automatic failover | About 3-minute automatic recovery of affected partitions in single-write accounts | Documented without a preview label; billed as Business Critical tier | [consistency-and-replication.md](../consistency-and-replication.md#single-write-multi-region-accounts-and-failover) |
| Throughput buckets | Cap batch, ETL, or tenant workloads at a share of RU/s | Monitoring metrics labeled preview | [request-units-and-indexing.md](../request-units-and-indexing.md#workload-isolation-features) |
| Priority-based execution | Protect user traffic from background jobs | Best effort, no SLA | same |
| Global secondary indexes | Serve a second query pattern without re-partitioning | The concept page carries no preview label, but the how-to still enables and creates it with `api-version=2022-11-15-preview`. Check the account's Features pane in the portal for a preview tag before relying on it in production | [nosql-modeling-and-partitioning.md](../nosql-modeling-and-partitioning.md#synthetic-keys-and-global-secondary-indexes) |
| Hierarchical partition keys | Lift the 20 GB per-tenant ceiling | GA for supported SDKs | [nosql-modeling-and-partitioning.md](../nosql-modeling-and-partitioning.md#hierarchical-partition-keys) |
| Microsoft Entra ID with `disableLocalAuth` | Removes shared keys | GA | [operations.md](../operations.md#security) |
| Partition merge | Undo throughput fragmentation after a large scale-down | Preview; blocks unsupported SDKs | [request-units-and-indexing.md](../request-units-and-indexing.md#workload-isolation-features) |

## Upgrading Into This Series

Accounts created before 2024-09-25:

- Enable Dynamic Scaling (Features pane) and compare the Provisioned Throughput metric for a week. No downtime; doesn't affect manual-throughput resources.

Accounts on periodic backup:

- Migrate to continuous (one-way). Pre-check the API (not Cassandra), Synapse Link history, CMK default identity, and MongoDB unique indexes. Watch `backupPolicy.migrationState.status` until the type is `Continuous`.

Clients:

- Confirm no client negotiates TLS below 1.2. Use the cosmos-tls-scanner tool or client-side TLS logs, not a generic TLS scanner.
- Inventory SDK versions against the minimums in [rest-api-and-sdks.md](rest-api-and-sdks.md) before enabling PPAF, partition merge, priority-based execution, or throughput buckets.
- Applications on .NET SDK v2: migrate to v3 (the migrate-dotnet-v3 guide).

## Managed Service Notes

Feature enablement on the Features pane can take 15-20 minutes to propagate (burst capacity, partition merge), and up to 30 minutes for all versions and deletes change feed, during which no other account changes can be made. Plan enablement outside change freezes and confirm the property in `az cosmosdb show` afterwards.
