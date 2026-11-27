# REST API Versions and SDK Majors

Checked: 2026-11-27. Read when a client sends raw REST calls, when an SDK version might lack a feature, or before enabling an account feature that blocks or requires specific SDK versions.

## Lifecycle

Data-plane REST API (`x-ms-version` header), from the REST reference:

| Version | Change introduced | Retired |
| --- | --- | --- |
| 2018-12-31 | Partitioned collections automatic migration | |
| 2018-09-17 | Composite and additional spatial indexing | |
| 2018-08-31 | Dynamic collection scaling improvements | |
| 2018-06-18 | Multi-region write support | |
| 2017-11-15 | Multi-region strong consistency | |
| 2017-05-03 | Large partition key | |
| 2017-02-22 | Consistent prefix | |
| 2017-01-19 | Lower minimum throughput for partitioned collections | |
| 2016-07-11 | Change feed | |
| 2015-12-16 | Partitioned collections (`x-ms-documentdb-partitionkey`) | |
| 2015-08-06 | Upsert | |
| 2015-06-03 | ORDER BY | |
| 2015-04-08 | DocumentDB GA | |
| 2014-08-21 | DocumentDB preview | 2016-02-29 |

The REST index says the latest version is used when `x-ms-version` is omitted; the common-headers page marks `x-ms-version` as required. Always send it.

Management (resource provider) API: versioned separately (`api-version` query parameter on `management.azure.com`). The ARM reference on 2026-11-27 showed `2026-04-01-preview` as the latest schema. Several features need preview API versions: all versions and deletes change feed (`2024-12-01-preview` or later), global secondary indexes (`2022-11-15-preview` in the how-to), partition merge (`2023-11-15-preview` in the merge page). `minimalTlsVersion` exists from `2022-11-15`.

SDKs: retirement is announced 12 months ahead through the portal, Azure Updates, and email to service administrators. After retirement, requests from the retired SDK are still served, but there are no fixes, features, or support. New features land only in the latest minor of the latest major.

| SDK | Current major | Retired majors found |
| --- | --- | --- |
| .NET (`Microsoft.Azure.Cosmos`) | v3 | v2 (`Microsoft.Azure.DocumentDB`), retired 2024-08-31 |
| Java (`com.azure:azure-cosmos`) | v4 | Sync v2 (`com.microsoft.azure:azure-documentdb`), retired 2024-02-29; Async v2, retired 2024-08-31 |
| Python (`azure-cosmos`) | 4.x | (none checked) |
| JavaScript (`@azure/cosmos`) | v4 | (none checked) |
| Go (`azcosmos`) | (version not checked) | |
| Rust | 1.x (PPAF page lists Rust SDK v1.0.0) | |

## Changed Defaults

Not applicable to REST versions on the pages checked. SDK defaults that matter operationally:

- SDKs retry 429 responses automatically (typically up to 9 times) and honor `x-ms-retry-after-ms`. Applications may never see 429s that metrics show.
- Index metrics are off by default (`PopulateIndexMetrics = false`).

## Removed or Deprecated

- .NET SDK v2: retired 2024-08-31. Migrate to v3 (migrate-dotnet-v3 guide).
- REST version 2014-08-21: retired 2016-02-29.

## Worth Adopting

Minimum SDK versions for features (from each feature page):

| Feature | .NET v3 | Java v4 | Python | JavaScript | Other |
| --- | --- | --- | --- | --- | --- |
| Hierarchical partition keys | 3.33.0 | 4.42.0 | 4.6.0 | 4.0.0 | Go `PartitionKeyKindMultiHash` |
| Index metrics | 3.21.0 | 4.19.0 | 4.6.0 | (not stated) | Go `PopulateIndexMetrics` |
| Priority-based execution | 3.38.0 | 4.45.0 | 4.14.2 (page also says preview from 4.6.0) | 4.0.0 | Spark 3.2 connector 4.19.0 |
| Throughput buckets | 3.63.0 | 4.83.0 | 4.16.4 | 4.8.0 | |
| Per-partition automatic failover | 3.62.0 | 4.79.0 | 4.16.0 | 4.7.0 | Rust 1.0.0 |
| Partition merge (clients allowed while enabled) | 3.27.0 | 4.42.0 | conflicting: the caution says "any Python SDK" is blocked, the SDK table lists 4.14.2+ | 4.3 | Spark connector 4.18.0; Go not allowed |

## Upgrading Into This Series

- Before enabling PPAF or partition merge, inventory every client (applications, Functions, Data Factory, Spark jobs) and upgrade them; unsupported clients fail (merge) or can fail writes during a failover (PPAF).
- When moving .NET v2 to v3, re-test session token handling, retry settings, and bulk options; behavior is SDK-specific.
- REST clients: send `x-ms-version: 2018-12-31` and `x-ms-documentdb-partitionkey` (JSON array) on document operations. For a hierarchical key send all levels, for example `["tenant1","user1"]`. The vNext emulator (EN20261123) accepted this format for create and point read and rejected a one-level value on a two-level key with 400 ("Length does not match the number of partition key paths in collection policy"); the format has not been checked against an Azure account.

## Managed Service Notes

The vNext emulator responds to REST calls without authentication and reported `x-ms-gatewayversion: 2.0.0-unknown`; it does not validate `x-ms-version` behavior differences (not tested). Test version-dependent REST behavior against an Azure account.
