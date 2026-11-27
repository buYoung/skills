# Cosmos DB for MongoDB (RU) Server Versions 3.2 to 7.0

Checked: 2026-11-27. Read when an Azure Cosmos DB for MongoDB (RU) account's `apiProperties.serverVersion` decides whether a command, index, or driver works, or before changing that version. Not for Azure DocumentDB ([azure-documentdb.md](azure-documentdb.md)).

## Lifecycle

| Server version | Endpoint | End of support | Source |
| --- | --- | --- | --- |
| 3.2 | `<account>.documents.azure.com` | No current plans; at least three years' notice | feature-support-32 |
| 3.6 | `<account>.mongo.cosmos.azure.com` | No current plans; at least three years' notice | feature-support-36 |
| 4.0, 4.2, 5.0, 6.0, 7.0 | `<account>.mongo.cosmos.azure.com` | No end date published as of 2026-11-27 | ARM `serverVersion` enum; feature-support pages |

Release dates of each wire version were not found on the pages checked. Microsoft's RU pages now recommend Azure DocumentDB for MongoDB migrations; no retirement of the RU offering was found.

## Changed Defaults

- Moving from 3.2 to 3.6 or later: multi-field sorts require a compound index; a sort without one fails with error 2 `BadValue`.
- 4.0 and later store BSON in an optimized internal format for documents written through a 4.0+ endpoint; older documents keep the old format until rewritten.
- Operation execution limit: 15 seconds for 3.2, 60 seconds for 3.6 and 4.0 (service-quotas page). The service-quotas page gives no limit for 4.2 and later, and the error-codes page describes 60 seconds generally. Plan for 60 seconds and set `maxTimeMS` below it.
- Query memory limit of 40 MB applies only to 3.2 (error 16501 `ExceededMemoryLimit`).

## Removed or Deprecated

Nothing found removed between versions. Features that remain unsupported on 7.0 (the newest) are listed in [../mongodb-compatibility.md](../mongodb-compatibility.md#ru-offering-unsupported-or-different); earlier versions support a subset of 7.0's list, so check the account's own feature-support page (`feature-support-32`, `-36`, `-40`, `-42`, `-50`, `-60`, `-70`).

## Worth Adopting

- 3.6+ endpoint (`*.mongo.cosmos.azure.com`) for compound indexes and current drivers.
- 4.0+ for multi-document transactions (single unsharded collection, 5 seconds) and the BSON storage improvement.
- Account capabilities independent of version: `EnableMongoRetryableWrites`, `DisableRateLimitingResponses` (server-side retry), `EnableMongo16MBDocumentSupport` (new collections only), `EnableMongoRoleBasedAccessControl`.

## Upgrading Into This Series

Pre-checks:

1. Driver versions: upgrade drivers to versions that support the target wire version before the account (upgrade-version page).
2. From 3.2: list every multi-field sort and create compound indexes; inventory connection strings, because 3.2 apps use `*.documents.azure.com`.
3. Read the target version's feature-support page for commands the app uses.

Procedure:

1. Rehearse on a dev/test account with the same version and data shape.
2. Portal > account > Features > Upgrade MongoDB server version > pick the target. Status shows Pending; about 15 minutes; no downtime, no RU consumption, data and indexes untouched.
3. From 3.2: copy the new connection string from Overview and switch every application. Only connections to the new endpoint get the new features. The old endpoint keeps running 3.2.
4. Post-check: `az cosmosdb show --query apiProperties.serverVersion`; run the application's integration tests; watch error codes 2, 115, and 16500 in diagnostics.

Rollback: downgrade to 4.0 or 3.6 through the same pane. After an upgrade from 3.2, switch applications back to the `*.documents.azure.com` connection string.

Blocker: the upgrade page warns that only qualifying 3.2 accounts can currently be upgraded to 3.6 and higher, and that accounts without the upgrade option need a support ticket. The page's steps stop at selecting 4.2, 4.0 or 3.6. For 4.x to 5.0 and later, open the account's Features pane and check whether `Upgrade MongoDB server version` offers the target; if not, file a support ticket.

## Managed Service Notes

- The version is an account property, not a server binary. All collections in the account follow it.
- Changing capabilities isn't supported through ARM for this API; use `az cosmosdb update --capabilities` with the full list.
- Migration to Azure DocumentDB is an alternative to upgrading when the application needs features the RU engine lacks (cross-collection transactions, `$lookup` pipelines, text indexes).
