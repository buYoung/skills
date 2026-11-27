# Azure DocumentDB MongoDB Compatibility Versions 5.0 to 8.0

Checked: 2026-11-27. Read when an Azure DocumentDB cluster (formerly vCore-based Azure Cosmos DB for MongoDB) must support a MongoDB feature tied to a wire version, or before upgrading a cluster's MongoDB version. Not Amazon DocumentDB (see `../documentdb/`), and not Cosmos DB for MongoDB (RU) ([mongodb-ru-server-versions.md](mongodb-ru-server-versions.md)).

## Lifecycle

| MongoDB compatibility | Released | End of support |
| --- | --- | --- |
| 5.0 | Before 2024-08-05; the release notes start later | Not published |
| 6.0 | Before 2024-08-05; the release notes start later | Not published |
| 7.0 | 2024-08-05 ("v7 released", release notes) | Not published |
| 8.0 | 2025-05-05 ("v8 released", release notes) | Not published |

Microsoft Learn has no lifecycle or end-of-support page for Azure DocumentDB versions as of 2026-11-27. Watch the [release notes](https://learn.microsoft.com/en-us/azure/documentdb/release-notes) and Azure Updates, and treat any retirement notice as the start of the upgrade plan.

Service milestones: engine open-sourced 2025-01-23; renamed to Azure DocumentDB 2025-11-18. The at-a-glance page (its facts marked as verified on 2026-11-05) lists wire versions 5.0, 6.0, 7.0, and 8.0 as supported.

Engine builds: release-note entries carry engine and infrastructure build tags (for example engine 1017 and API version `2025-09-01` in the 2025-10-10 release). The engine is the open-source DocumentDB project on PostgreSQL (`pg_documentdb`; a PostgreSQL 17 build was added 2025-02-12).

## Changed Defaults

From the release notes:

- 2024-09-16: large index keys enabled by default.
- 2024-10-14: index builds run in the background by default (unique index builds still run in the foreground and block writes, per the limitations page).
- 2025-10-10 (preview): TTL index deletes run continuously for up to 60 seconds instead of once every 60 seconds.

## Removed or Deprecated

Nothing found removed. The product name "Azure Cosmos DB for MongoDB (vCore)" was replaced by "Azure DocumentDB" on 2025-11-18; clusters, connection strings, and APIs were unchanged.

## Worth Adopting

| Release | Feature | Why |
| --- | --- | --- |
| 2025-02-12 | Autoscale GA; geo-replica promotion | Compute scaling without manual tier changes; regional DR |
| 2025-05-05 (v8) | `$toUUID`, `$convert` on binData, pipeline size enforcement, `$getField` with expressions | 8.0 application compatibility |
| 2025-08-29 | Index hints; CMK and Microsoft Entra ID GA (infrastructure 0909) | Force a plan when the planner picks badly; identity-based access |
| 2025-10-10 | API version `2025-09-01` with Data API, Entra ID, CMK and the option to disable native auth (the entry's summary repeats the GA wording); `$jsonSchema` validation (preview) | Disable native auth; schema enforcement |
| 2025-11-18 | Index Advisor (VS Code), migration extension, Premium SSD v2 (preview), reserved instances, RU-to-DocumentDB migration path | Query tuning and migration tooling |

## Upgrading Into This Series

1. Pre-check: run the compatibility assessment in the DocumentDB migration extension for VS Code against the workload; confirm drivers support the target wire version.
2. Rehearse: restore the cluster to a new cluster (PITR), upgrade the restored copy, and run integration tests and `explain()` on the top queries.
3. Switch: portal > cluster Overview > Upgrade > choose the MongoDB version > submit. The button is disabled if the cluster is already on the latest version.
4. Post-check: confirm the version on the Overview page; watch CPU, memory, and request metrics; re-run the top queries' `explain()`.

Rollback: the upgrade page (165 words) documents only upgrading, with no downgrade. Keep the pre-upgrade restore point and plan rollback as restore-to-new-cluster plus connection-string switch, which loses writes made after the restore time.

## Managed Service Notes

- Replica clusters inherit storage, shard count, and users from the primary and don't support PITR or in-region HA. The upgrade page does not mention replicas. After upgrading the primary, check each replica's version on its Overview page or with `az documentdb mongocluster show -g <rg> -n <replica> -o json`.
- Free tier and M10-M25 clusters have different HA and backup limits; see [../mongodb-compatibility.md](../mongodb-compatibility.md#azure-documentdb-operations).
- The release-notes page had no entries after 2025-11-18 on 2026-11-27; check it again for newer engine releases before answering version-specific questions.
