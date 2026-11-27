# Operations: Backup, Restore, Security, Monitoring

Checked: 2026-11-27. Read when configuring or testing backups, restoring after data loss, hardening access, or diagnosing throttling, latency, and errors on an Azure Cosmos DB account. Cosmos DB is a managed service only; there is no self-hosted server, no superuser, no configuration file, and no maintenance window to schedule. For Azure DocumentDB operations see [mongodb-compatibility.md](mongodb-compatibility.md#azure-documentdb-operations).

## Contents

- [Backup and restore](#backup-and-restore)
- [Restore procedures](#restore-procedures)
- [Long-term retention with Azure Backup](#long-term-retention-with-azure-backup)
- [Security](#security)
- [Monitoring](#monitoring)
- [Diagnose 429 rate limiting](#diagnose-429-rate-limiting)
- [Diagnostic logs](#diagnostic-logs)
- [Control-plane limits](#control-plane-limits)
- [Common mistakes](#common-mistakes)

## Backup and restore

Every account has one native backup mode:

| | Periodic | Continuous |
| --- | --- | --- |
| What | Full backup every 4 hours by default, 2 copies kept | Continuous backup of every mutation, asynchronously within about 100 seconds |
| Retention | Interval 1-24 hours; retention at least 2 x interval, at most 720 hours; 2 copies free, more charged | Tier `Continuous7Days` (no storage charge), `Continuous30Days`, or `Continuous35Days` (both charged for storage); every restore is charged |
| Where | Write region only; backup storage geo-redundant by default where the region supports it (configurable to LRS or ZRS) | Every region of the account; LRS, or ZRS where the region has zones; redundancy can't be changed |
| Restore | Open a support ticket; restores into a new account in the source write region | Self-service: new account (account, databases, containers) or deleted databases and containers back into the existing account; to the second |
| APIs | All RU APIs | NoSQL, MongoDB, Gremlin, Table. Not Cassandra |
| Deleted containers | Snapshots kept 30 days after deletion | Restorable within retention |

Accounts use periodic mode unless continuous mode is configured (online backup and restore page). Read the mode from `backupPolicy.type`; the same page gives an Azure Resource Graph query that lists the mode for every account.

Migration from periodic to continuous is one-way. Without a tier the CLI migrates to `Continuous30Days`. Accounts that ever disabled Synapse Link on a container can't migrate. On API for MongoDB, unique indexes can't be added to existing collections after the account is continuous; create them with the collection.

```bash
az cosmosdb update -g <rg> -n <account> --backup-policy-type Continuous --continuous-tier Continuous7Days
az cosmosdb show -g <rg> -n <account> --query backupPolicy   # migrationState.status InProgress -> type Continuous
```

Periodic settings:

```bash
az cosmosdb update -g <rg> -n <account> --backup-interval 480 --backup-retention 24   # minutes, hours
```

Changing periodic backup storage redundancy applies only to future backups, can take up to twice the interval, and removes access to older backups immediately. Configuring redundancy requires the Cosmos DB Operator role at subscription level.

Decision rules:

- Use continuous backup for production NoSQL, MongoDB, Gremlin, and Table accounts. It is required for the all versions and deletes change feed, for global secondary indexes, and for Azure Backup vaulted backup.
- Choose 7 days when restores are for quickly noticed mistakes and cost matters; 30 or 35 days when detecting bad writes can take weeks. Switching to a shorter tier drops backups beyond the new window.
- Cassandra accounts stay on periodic; keep enough retention and practice the support-ticket restore.
- Continuous backups are stored per region with LRS or ZRS and aren't geo-disaster resistant on their own; add another region to the account for resilience (continuous-backup limitations). Periodic backups are geo-redundant by default.

What a restore does not bring back:

- Firewall, VNet, and private endpoint settings; data-plane RBAC; Azure RBAC assignments.
- Stored procedures, triggers, UDFs.
- All regions (periodic restores into one region; continuous restores into a chosen region where backups existed).
- A subset of containers inside a shared-throughput database (only the whole database).
- Periodic only: account keys (new keys are generated), TTL-expired documents, analytical store data, materialized views.
- Continuous: throughput as of the restore point might not be restored; indexes may still be rebuilding (`IndexTransformationProgress`).

## Restore procedures

Periodic mode, accidental delete or corruption:

1. Immediately raise retention to at least 7 days, ideally within 8 hours of the event, so the backup that predates the mistake isn't overwritten.
2. Open a support request with the account, database, container, and the UTC time before the mistake.
3. Validate the restored account, then copy data back or repoint the application.

Continuous mode:

```bash
# Accounts (live and deleted) that can be restored, with their instance IDs and regions
az cosmosdb restorable-database-account list --account-name <source-account>

# Find the deletion or change time from the event feeds (live accounts)
az cosmosdb sql restorable-database list --instance-id <instance-id> --location "<region>"
az cosmosdb sql restorable-container list --instance-id <instance-id> --database-rid <ownerResourceId> --location "<region>"

# Latest restorable time for one container in one region
az cosmosdb sql retrieve-latest-backup-time -g <rg> -a <account> -d <db> -c <container> -l <region>

# Restore into a NEW account; disable TTL so restored data isn't expired on arrival
az cosmosdb restore -g <rg> \
  --account-name <source-account> \
  --target-database-account-name <restored-account> \
  --restore-timestamp 2026-11-20T08:15:00+0000 \
  --location "<region>" \
  --public-network-access Disabled \
  --disable-ttl True \
  --databases-to-restore name=app collections=orders
```

- Without `--public-network-access Disabled` the restored account is reachable from the public network (disabling needs azure-cli 2.52.0 or later).
- Without `--disable-ttl True`, the restore keeps container TTL, and items older than their TTL are deleted after restore.
- Restoring deleted databases or containers into the existing account avoids data transfer. The commands are `az cosmosdb sql database restore -g <rg> -a <account> -n <db> [--restore-timestamp <time>] [--disable-ttl True]` and `az cosmosdb sql container restore -g <rg> -a <account> -d <db> -n <container> [--restore-timestamp <time>] [--disable-ttl True]` (Azure CLI reference, GA).
- Multi-write accounts restore only hub-confirmed writes; custom conflict policies revert to last writer wins.
- Restore permissions can be limited to specific principals (continuous-backup-restore-permissions page).

Verify a restore: compare item counts per container (`SELECT VALUE COUNT(1) FROM c`), spot-check the damaged items, re-create network rules, RBAC assignments, stored procedures, triggers, and UDFs, then run the application's read path against the restored account before switching.

Test restores on a schedule; a backup that has never been restored is unverified.

## Long-term retention with Azure Backup

Azure Backup vaulted backup for Cosmos DB: preview in May 2026, generally available in November 2026 (Azure Backup what's new).

- Requires native continuous backup on the account.
- Policy: weekly full plus daily incremental backups (1-day RPO); incremental-only policies are not allowed. Backups are at account level and include all databases and containers.
- Retention up to 10 years in a Backup vault with LRS, ZRS, or GRS; soft delete, WORM immutability, multi-user authorization, cross-region restore, and item-level restore.
- Restores go from the vault to a Cosmos DB account.
- Charges from 2026-07-01: protected-instance fee, vault storage, and restore volume.
- Supported regions, APIs, and limitations are on the backup-azure-cosmos-db-support-matrix page (not reviewed; check it before promising support for an API).

## Security

Authentication options for the data plane:

| Method | Use | Notes |
| --- | --- | --- |
| Microsoft Entra ID with native data-plane RBAC (NoSQL) | Default for applications; managed identities | Built-in roles Cosmos DB Built-in Data Reader and Cosmos DB Built-in Data Contributor (`00000000-0000-0000-0000-000000000002`); custom roles from `dataActions`; `notDataActions` isn't supported. Up to 100 custom role definitions and 2,000 assignments per account |
| Account keys (read-write and read-only) | Tools without Entra support | Disable with `disableLocalAuth` once all clients use Entra |
| Resource tokens (users and permissions) | Per-user scoped access | Lifetime 10 minutes to 24 hours by default; permissions can't target a hierarchical-key prefix |
| API for MongoDB native users and roles | Mongo-style users | Capability `EnableMongoRoleBasedAccessControl` (can't be removed) |
| API for Cassandra | Keys only | No `CREATE ROLE` or `GRANT` |

Creating data-plane role definitions and assignments needs control-plane permissions (`Microsoft.DocumentDB/databaseAccounts/sqlRoleDefinitions/*`, `sqlRoleAssignments/*`).

```bash
# Grant the built-in Data Contributor role on the whole account to a managed identity
az cosmosdb sql role assignment create -g <rg> -a <account> \
  --role-definition-id 00000000-0000-0000-0000-000000000002 \
  --principal-id <object-id> --scope "/"

# After every client uses Entra ID: disable key-based auth
az resource update -g <rg> -n <account> \
  --resource-type "Microsoft.DocumentDB/databaseAccounts" \
  --set properties.disableLocalAuth=true
```

Rollback for `disableLocalAuth`: set it back to `false`. Before enabling it, search application settings and connection strings for `AccountKey=`; any client still using a key fails immediately.

Other controls:

- `disableKeyBasedMetadataWriteAccess`: blocks creating or changing databases, containers, and throughput with keys, forcing those changes through Azure RBAC and ARM.
- TLS: since 2025-08-31 all accounts must use TLS 1.2 or higher; TLS 1.3 is enabled since 2025-03-31. `minimalTlsVersion` defaults to `Tls12` for new accounts. Conventional TLS scanners are unreliable because enforcement is at the application layer; use the cosmos-tls-scanner tool or read the property:

  ```bash
  az cosmosdb show -g <rg> -n <account> --query minimalTlsVersion
  ```

- Network: IP firewall rules, VNet service endpoints, private endpoints, `publicNetworkAccess`. Restores don't copy these.
- Encryption at rest is always on; customer-managed keys use Azure Key Vault with a default identity on the account.
- Built-in Data Reader is `00000000-0000-0000-0000-000000000001` (read metadata, read items, execute queries, read change feed); Built-in Data Contributor is `...0002` (data plane security reference). List definitions with `az cosmosdb sql role definition list -g <rg> -a <account>`.

The vNext emulator does not enforce authentication even with `--key-file`. Test RBAC and key behavior only on an Azure account (see [emulator.md](emulator.md)).

## Monitoring

Platform metrics (Azure Monitor):

| Metric | Use |
| --- | --- |
| Total Requests (split by status code, operation, region, `ThroughputBucket`) | 429 rate, error codes, regional traffic |
| Total Request Units | RU consumption; split by operation to find the costly operation type |
| Normalized RU Consumption (split by `PartitionKeyRangeId`, region) | Hot partitions; whether autoscale `Tmax` is right. Consistently 100% with 429s means more RU/s or a better key |
| Provisioned Throughput | Billed RU/s per hour (delayed; don't use for scaling decisions) |
| Autoscaled RU | Per-partition, per-region scale with dynamic scaling |
| Physical Partition Throughput (split by `PhysicalPartitionId`) | RU/s per physical partition; merge candidates |
| Data and index usage (Insights > Storage) | Index size relative to data |
| Metadata Requests (Insights > System) | Control-plane throttling |
| Probabilistically Bounded Staleness, replication latency | Consistency in practice |
| Global Secondary Index Propagation Latency in Seconds | GSI lag |
| `PartitionWriteGlobalStatus` | PPAF write partitions per region |

Account health: set Azure Resource Health and Service Health alerts; Microsoft does not otherwise notify you that a region is down.

SDK side: capture the SDK diagnostics for slow or failed requests and log `x-ms-activity-id` to correlate with diagnostic logs and support cases.

## Diagnose 429 rate limiting

1. Measure the rate. Insights > Requests > Total Requests by Status Code. A 1-5% 429 rate with acceptable latency is healthy use of provisioned RU/s, assuming evenly loaded partitions. SDKs retry 429s (typically up to 9 times) honoring `x-ms-retry-after-ms`, so 429s in metrics may never reach the application.
2. Check for a hot partition: Normalized RU Consumption by PartitionKeyRangeId. One range consistently at 100% while others are at 30% or less means a hot key.
3. Find the key and operation with diagnostic logs (resource-specific tables):

   ```kusto
   CDBPartitionKeyRUConsumption
   | where TimeGenerated >= ago(24h)
   | where CollectionName == "orders"
   | where isnotempty(PartitionKey)
   | summarize sum(RequestCharge) by PartitionKey, OperationName, bin(TimeGenerated, 1s)
   | order by sum_RequestCharge desc
   ```

   ```kusto
   CDBDataPlaneRequests
   | where TimeGenerated >= ago(24h)
   | summarize throttled = dcountif(ActivityId, StatusCode == 429), total = dcount(ActivityId),
               ru = sum(RequestCharge)
     by DatabaseName, CollectionName, OperationName, RequestResourceType, bin(TimeGenerated, 1m)
   | extend fraction429 = 1.0 * throttled / total, ruPerOp = 1.0 * ru / total
   | order by fraction429 desc
   ```

4. Fix by cause:

| Cause | Fix |
| --- | --- |
| Writes too costly | Exclude unused index paths |
| Queries too costly | Add composite indexes, filter on the partition key, project fewer fields |
| Even load, not enough RU/s | Raise RU/s or `Tmax` (stay under the instant-scale ceiling, or plan the asynchronous scale-up) |
| Hot partition | Long term: new partition key (new container or GSI). Short term: more RU/s, throughput redistribution (preview), burst capacity |
| Autoscale at 100% but not scaled to `Tmax` | Momentary spikes; autoscale goes to max only after sustained 100% in 5-second intervals |
| Background job starving the app | Priority-based execution (Low for the job) or a throughput bucket |
| "high rate of metadata requests" | One client instance per process; cache database and container references. Raising RU/s doesn't help |
| "transient service error" | Retry; open a ticket if it persists for minutes. Raising RU/s doesn't help |
| `TXN_WAIT_FOR_TRANSACTION_END` | Concurrent transactions on one logical partition key; shorten, back off, spread keys |

API for MongoDB returns error 16500 `TooManyRequests` instead of HTTP 429; the `DisableRateLimitingResponses` capability retries on the service side.

## Diagnostic logs

- Send diagnostic settings to a Log Analytics workspace in resource-specific mode (`--export-to-resource-specific true`, or `logAnalyticsDestinationType: Dedicated`) for all APIs except Table. Tables used above: `CDBDataPlaneRequests`, `CDBPartitionKeyRUConsumption`. Query statistics land in `CDBQueryRuntimeStatistics` (category `QueryRuntimeStatistics`), with `QueryText`, `ActivityId` (joins to `CDBDataPlaneRequests`) and `PartitionKeyRangeId` (Azure Monitor table reference).
- Log Analytics bills by ingested volume; enable only the categories you need for a bounded investigation, then turn them off.
- The portal prompts to enable full-text query for more detailed query logging; the account property is `diagnosticLogSettings.enableFullTextQuery`. Without it, `QueryText` holds the query with its text and parameters obfuscated. Enabling it logs the deobfuscated query for all requests, adds logging cost, and Microsoft recommends turning it off after troubleshooting (diagnostic settings page).
- Before deleting, renaming, or moving an account, delete its diagnostic settings; a re-created resource with the same name can resume sending logs to the old destination.

```bash
az monitor diagnostic-settings create --name cosmos-diag \
  --resource $(az cosmosdb show -g <rg> -n <account> --query id -o tsv) \
  --workspace <log-analytics-workspace-id> \
  --export-to-resource-specific true \
  --logs '[{"category":"DataPlaneRequests","enabled":true},{"category":"PartitionKeyRUConsumption","enabled":true},{"category":"QueryRuntimeStatistics","enabled":true}]'
```

## Control-plane limits

Per account, per 5 minutes (service-quotas page): 500 list/get keys, 500 create database or container, 500 get/list database or container, 25 throughput updates, 500 other operations; 10 regional failovers per hour. The account's metadata partition serves 240 RU/s for metadata operations and can't be raised. Sustained excess can throttle or fail management operations. Use one long-lived SDK client per process and cache keys and container references.

## Common mistakes

- Running production on periodic backup without knowing that a restore needs a support ticket and that only two 4-hourly copies exist by default.
- Not raising periodic retention immediately after an incident, letting the good backup age out.
- Restoring without `--disable-ttl True` and losing old items to TTL.
- Forgetting that restored accounts have no firewall, private endpoint, or RBAC settings, and are publicly reachable unless disabled.
- Enabling `disableLocalAuth` before every client and tool has moved to Entra ID.
- Treating a few percent of 429s as an incident.
- Leaving diagnostic logs on indefinitely at full volume.
