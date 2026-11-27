# Azure Cosmos DB APIs and Related Services

Checked: 2026-11-27. Read this first when a user says "Cosmos DB". Find out which API, and which service, they actually run before you answer anything else.

## Contents

- [Identify the API before answering](#identify-the-api-before-answering)
- [API and service map](#api-and-service-map)
- [What applies to which API](#what-applies-to-which-api)
- [Choosing an API for new work](#choosing-an-api-for-new-work)
- [API for Cassandra](#api-for-cassandra)
- [API for Gremlin](#api-for-gremlin)
- [API for Table](#api-for-table)
- [Cosmos DB for PostgreSQL](#cosmos-db-for-postgresql)
- [Common mistakes](#common-mistakes)

## Identify the API before answering

One Cosmos DB account exposes exactly one API, fixed when the account is created. Read it from the control plane:

```bash
az cosmosdb show -g <rg> -n <account> \
  --query "{kind:kind, capabilities:capabilities[].name, serverVersion:apiProperties.serverVersion, capacityMode:capacityMode}"
```

How to read the result:

| Output | Meaning |
| --- | --- |
| `kind: GlobalDocumentDB`, no API capability | API for NoSQL |
| `kind: MongoDB`, capability `EnableMongo`, `serverVersion` set | Azure Cosmos DB for MongoDB (RU). `serverVersion` selects the MongoDB wire-protocol feature set (`3.2` to `7.0`) |
| capability `EnableCassandra` | API for Apache Cassandra |
| capability `EnableGremlin` | API for Apache Gremlin |
| capability `EnableTable` | API for Table |
| `capacityMode: Serverless` | Serverless account: no provisioned RU/s, one region |

The `kind` values (`GlobalDocumentDB`, `MongoDB`, `Parse`), the `capacityMode` values (`Provisioned`, `Serverless`), and the capability names come from the ARM resource reference; `kind` can only be set at creation.

These are not Cosmos DB accounts, and `az cosmosdb show` does not find them:

- Azure DocumentDB (formerly vCore-based Azure Cosmos DB for MongoDB). Managed with the `az documentdb mongocluster` command group (documentdb extension, Azure CLI 2.75.0 or later, preview; Azure CLI reference). See [mongodb-compatibility.md](mongodb-compatibility.md).
- Azure Cosmos DB for PostgreSQL: a Citus-based PostgreSQL cluster service.
- Azure Managed Instance for Apache Cassandra: open-source Cassandra clusters operated by Azure.

## API and service map

| Offering | Engine and billing model | Resource hierarchy | Status on 2026-11-27 | Where to read |
| --- | --- | --- | --- | --- |
| Azure Cosmos DB for NoSQL | Cosmos DB engine; request units (manual, autoscale, or serverless) | Account > database > container > item | Current; the docs point high-scale new work here | All topic files |
| Azure Cosmos DB for MongoDB (RU) | Cosmos DB engine behind a MongoDB wire-protocol layer; request units | Account > database > collection | Current; the docs now point MongoDB migrations to Azure DocumentDB | [mongodb-compatibility.md](mongodb-compatibility.md), plus RU and consistency files |
| Azure DocumentDB (formerly vCore-based Azure Cosmos DB for MongoDB) | Open-source DocumentDB engine on PostgreSQL; billed by cluster tier (vCores, memory) and storage; no RUs | Cluster > physical shards (nodes) | Separate Azure service since the rename on 2025-11-18 | [mongodb-compatibility.md](mongodb-compatibility.md) |
| Azure Cosmos DB for Apache Cassandra | Cosmos DB engine behind CQL Binary Protocol v4; request units | Account > keyspace > table | Current; the docs point Cassandra lift-and-shift to Managed Instance for Apache Cassandra | This file, RU and consistency files |
| Azure Cosmos DB for Apache Gremlin | Cosmos DB engine with a TinkerPop Gremlin layer; request units | Account > database > graph | Current; the docs point OLAP graph and Gremlin migrations to Graph in Microsoft Fabric | This file |
| Azure Cosmos DB for Table | Cosmos DB engine behind the Azure Table Storage API; request units | Account > table | Current | This file |
| Azure Cosmos DB for PostgreSQL | PostgreSQL with the Citus extension; node-based | Cluster (coordinator and workers) | Retirement path; new deployments blocked; existing clusters supported | This file; engine behavior in `../postgresql/` |

Azure DocumentDB is not Amazon DocumentDB. The skill's `../documentdb/` files describe the AWS service. Azure DocumentDB is also unrelated to the 2014-2017 Azure service named DocumentDB, which became Cosmos DB (source: Azure DocumentDB FAQ).

## What applies to which API

The RU-based APIs share the Cosmos DB engine: request units, logical and physical partitions, the 20 GB logical-partition limit, five consistency levels, multi-region replication, periodic backup, and Azure Monitor metrics. Exceptions per API:

| Capability | NoSQL | MongoDB (RU) | Cassandra | Gremlin | Table |
| --- | --- | --- | --- | --- | --- |
| Hierarchical partition keys | Yes | No | No | No | No |
| Item size limit | 2 MB | 2 MB; 16 MB after enabling `EnableMongo16MBDocumentSupport` (cannot be disabled) | 2 MB per row; no column-count limit (Cassandra support page) | 2 MB per vertex or edge item | 2 MB engine limit; FAQ warns binary encoding reduces usable size |
| Continuous backup (PITR) | Yes | Yes | No | Yes | Yes |
| Change feed | Latest version and all versions and deletes modes | Change streams | Change feed through CQL query with predicate | Supported in .NET, Java, Python, JavaScript per the change-feed support table | No |
| Custom conflict resolution (merge procedure) | Yes | No; LWW on `_ts` | No; LWW on `_ts` | No; LWW on `_ts` | No; LWW on `_ts` |
| Native data-plane RBAC with Entra ID | Yes | Native Mongo users and roles via `EnableMongoRoleBasedAccessControl` | No CRUD roles; keys only | Not described on the Gremlin security page, which covers keys and managed identities for other Azure services | Yes; built-in Data Reader `...0001` and Data Contributor `...0002`, no `notDataActions` (Table data plane security reference) |
| Per-partition automatic failover | Yes (single-write accounts) | No | No | No | No |
| Global secondary indexes | Yes (requires continuous backup) | No | No | No | No |
| Burst capacity | Yes | Yes | Yes | Yes | Yes |
| Serverless | Yes | not listed | not listed | not listed | Yes |

Serverless for MongoDB, Cassandra and Gremlin: the serverless and service-quota pages name no APIs. Check whether the portal's create flow for that API offers Serverless under Capacity mode.

Sources for the table: hierarchical-partition-keys (NoSQL only), continuous-backup-restore-introduction ("API for Cassandra isn't supported now"), change-feed and change-feed-modes, conflict-resolution-policies, how-to-configure-per-partition-automatic-failover ("Core (SQL) API"), burst-capacity requirements, table/support (serverless on Table), mongodb/how-to-configure-capabilities, cassandra/support (2 MB entity limit), table/reference-data-plane-security, gremlin/security, Azure Backup Cosmos DB support matrix.

## Choosing an API for new work

1. New application with no wire protocol to preserve: API for NoSQL. NoSQL-only features include hierarchical partition keys, PPAF, global secondary indexes, the all versions and deletes change feed, and custom conflict resolution.
2. Existing MongoDB application that needs MongoDB query semantics, multi-document transactions across collections, `$lookup` with `let`/`pipeline`, or no RU capacity planning: Azure DocumentDB. The RU offering supports transactions only inside one unsharded collection with a fixed 5-second timeout and rejects `$lookup` with `let`/`pipeline`.
3. Existing MongoDB application that needs multi-region writes or the RU engine's autoscale, and fits the RU offering's command gaps: Cosmos DB for MongoDB (RU). Run the gap check in [mongodb-compatibility.md](mongodb-compatibility.md) first.
4. Existing Cassandra application that relies on logged batches, roles and `GRANT`, UDFs or UDAs, `COPY`, or Cassandra's own consistency semantics: Azure Managed Instance for Apache Cassandra. API for Cassandra accepts unlogged batches only and rejects those commands.
5. Graph workloads on API for Gremlin: use TinkerPop 3.4.x drivers; the support page lists known compatibility issues with 3.5.x and 3.6.x drivers.
6. Azure Table Storage application that needs indexes on all properties, global distribution, or latency SLAs: API for Table. If the app mostly stores and rarely reads, Table Storage costs less, because API for Table bills provisioned capacity from the moment a table exists.
7. Distributed PostgreSQL: do not plan on Cosmos DB for PostgreSQL. Use Azure Database for PostgreSQL elastic clusters.

## API for Cassandra

Mechanism: CQL Binary Protocol v4, compatible with CQL 3.11 and backward compatible with 2.x. The Cosmos DB engine manages replication, compaction, and consistency, so keyspace replication settings are ignored.

Differences from Apache Cassandra that change a decision (source: cassandra/support):

| Area | Behavior |
| --- | --- |
| `CREATE KEYSPACE` | Accepted; replication settings ignored. `ALTER KEYSPACE` not applicable |
| `BATCH` | Unlogged batches only |
| Lightweight transactions (`IF EXISTS`, `IF NOT EXISTS`, conditions) | Supported, except on accounts with multi-region writes |
| `CREATE ROLE`, `GRANT`, `REVOKE`, `LIST ROLES` | Not supported; access through account keys, and Azure RBAC on the control plane |
| UDF, UDA, `CREATE CUSTOM INDEX (SASI)`, triggers | Not supported |
| Secondary indexes | Supported on all types except frozen collections, decimal, and varint |
| cqlsh `TRACING`, `CONSISTENCY`, `COPY` | Not applicable or not supported; use diagnostic logs and the consistency mapping |
| Aggregates on clustering columns | Not supported |
| `USING TTL`, custom timestamps | Applied per row, not per cell |
| Throughput | `cosmosdb_provisioned_throughput` option on `CREATE KEYSPACE`, `CREATE TABLE`, `ALTER TABLE` |

Throughput example from the support page:

```sql
CREATE KEYSPACE sampleks WITH REPLICATION = {'class':'SimpleStrategy'}
  AND cosmosdb_provisioned_throughput=2000;
CREATE TABLE sampleks.t1(user_id int PRIMARY KEY, lastname text)
  WITH cosmosdb_provisioned_throughput=2000;
ALTER TABLE sampleks.t1 WITH cosmosdb_provisioned_throughput=10000;
```

Supported drivers listed: DataStax Java 3.5+, C# 3.5+, Node.js 3.5+, Python 3.15+, C++ 2.9, PHP 1.3, and gocql. Configure the retry policy the support page describes, because rate-limited requests fail rather than queue. Continuous backup is not available for this API; recovery relies on periodic backup (restore by support request) Azure Backup vaulted backup is not an option: its support matrix covers only NoSQL and MongoDB (RU) accounts in continuous mode.

## API for Gremlin

- Use the TinkerPop 3.4.13 drivers (.NET, Java, Python, Node.js, console) listed on the support page.
- Vertices and edges are items in a partitioned container; the item ID can't be the partition key for this API (partitioning page note).
- Traversal cost is measured in RUs on the shared engine; size throughput as for NoSQL.

## API for Table

Differences from Azure Table Storage (source: table/faq, table/support):

- Billing starts when a table is created; a table created without a throughput setting gets 400 RU/s. Serverless mode is available.
- All properties are indexed by default; tune the indexing policy under Scale & Settings.
- Query results are not sorted by PartitionKey and RowKey.
- RowKey is limited to 255 bytes, PartitionKey to 1 KB, batches to 2 MB.
- Table names are case-sensitive.
- Property names `ID`, `rid`, `etag`, and `ResourceId` are reserved.
- JSON only (no ATOM). CORS, service properties and stats, and table ACL endpoints are not supported.
- The FAQ gives Bounded Staleness as the Table client default; a request can't ask for stronger consistency than the table setting.
- SDKs `Azure.Data.Tables` (.NET), `azure-data-tables` (Python, Java), `@azure/data-tables` (JavaScript), and `aztables` (Go) target both services.
- Rapid table creation is throttled; keep it under about 5 tables per minute.

## Cosmos DB for PostgreSQL

- Status: on a retirement path; new deployments are blocked; existing clusters, including read replicas, remain supported.
- No retirement date was confirmed on an official Microsoft page on the check date. Check Azure Updates before planning around one.
- Migration target: Azure Database for PostgreSQL elastic clusters. Rehearse with the migration service dry run, or with a PITR copy as the test environment.
- For PostgreSQL engine behavior use `../postgresql/` files; Citus specifics are outside this reference.

## Common mistakes

- Answering a MongoDB-compatibility question without knowing whether the user runs the RU offering or Azure DocumentDB. Transactions, indexes, and command support differ completely.
- Applying Azure DocumentDB documentation to Amazon DocumentDB, or the reverse.
- Treating `serverVersion` on a RU account as a MongoDB server version. Microsoft does not run MongoDB; the value selects the wire-protocol feature set.
- Recommending a NoSQL-only feature (hierarchical partition keys, PPAF, GSIs, all versions and deletes change feed) to a MongoDB, Cassandra, Gremlin, or Table account.
- Planning to change the API of an existing account. Migrate the data to a new account instead.
