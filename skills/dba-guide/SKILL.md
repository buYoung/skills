---
name: dba-guide
description: Database engine guidance for MySQL, MariaDB, PostgreSQL, MongoDB, Amazon DocumentDB, Azure Cosmos DB, Couchbase, Redis, Valkey, Memcached, and Amazon DynamoDB, including Amazon RDS, Aurora, ElastiCache, and MemoryDB as managed variants. Use for schema, document, key, and partition-key design; indexes, EXPLAIN output, and query tuning; transactions, isolation, locking, MVCC, and deadlocks; replication, failover, sharding, and consistency; backup, restore, and PITR; memory, storage, connection, and durability settings; authentication, privileges, TLS, and auditing; slow queries, latency, and monitoring; version upgrades and end-of-support planning; Cosmos DB API choice; and compatibility between engines, such as DocumentDB or Cosmos DB against MongoDB. Version-aware for each product's supported releases. Covers the engine's behavior, design, operation, and diagnosis; writing, converting, or type-checking Kysely TypeScript query code belongs to kysely-converter.
license: MIT
---

# DBA Guide

Give engine-specific judgment for designing, operating, and diagnosing databases. Base each answer on the product, deployment, and server version actually in use, and on evidence from that server when it is available.

## Establish the Target

1. Identify the product and deployment: self-managed, container, Amazon RDS, Aurora, ElastiCache, MemoryDB, MongoDB Atlas, Couchbase Capella, a Cosmos DB API or Azure DocumentDB, or an Amazon DocumentDB instance-based or elastic cluster. Managed services remove settings, privileges, and diagnostics that self-hosted advice assumes, so on any of them read the engine's `managed-services.md` before recommending a command or setting.
2. Establish the server version from the first available evidence: output from the user's server, then the engine version in infrastructure code or the managed console/API, then the user's statement. A driver, client, or ORM version is not the server version. Managed version labels do not always match the upstream series: Aurora MySQL version 3 is 8.0-compatible, ElastiCache 7.1 for Redis OSS is compatible with Redis OSS 7.0, and ElastiCache 8.2 for Valkey is upstream Valkey 8.1 plus valkey-search. Map the label through the product's index before choosing a version file. Ask for the command output below when the answer depends on it.
3. Open the product's `versions/index.md` and compare:
   - Covered series: read that series' file. For an upgrade, read every series file from source to target.
   - A release between covered series without a file of its own (for example MySQL 9.0 to 9.6 or 26.7, MariaDB rolling releases between long-term series, Redis 7.0 or 8.4): the index names the file that carries its changes and gives its support status. Where the index says nothing, treat facts from the neighboring files as unverified for that release.
   - Older than the covered range: say the series is outside the covered range and, where the index says so, out of support. Apply only version-independent guidance, name the official release notes to check, and lead with the upgrade path from the index. Do not attribute newer defaults to the older server.
   - Newer than the covered range: read the official release notes for the newer series before stating version-specific facts, and say that the references stop at the covered range. If the notes cannot be read, answer from the newest covered file and mark which statements are unverified for the user's version.
   - Unknown: answer the version-independent part, mark which conclusions depend on the version, and give the command that settles it.

   On a managed service, offered versions and support dates follow the provider's calendar. Take them from the index or `managed-services.md`, and give both dates when they differ from the vendor's. Support dates, newest patches, and offerings in the references are as of 2026-11-27; when the user's date or reported release is later, say so and name the lifecycle page from the index's Sources.
4. Collect the workload facts the decision depends on: data size and growth, read/write mix, latency and consistency requirements, RPO/RTO, change windows, and replication topology.

| Product | Version evidence | Directory |
|---|---|---|
| MySQL | `SELECT VERSION(), @@version_comment;` Aurora: `SELECT AURORA_VERSION();` | [mysql](references/mysql/versions/index.md) |
| MariaDB | `SELECT VERSION();` (the string contains `MariaDB`) | [mariadb](references/mariadb/versions/index.md) |
| PostgreSQL | `SHOW server_version_num;` or `SELECT version();` Aurora: `SELECT aurora_version();` | [postgresql](references/postgresql/versions/index.md) |
| MongoDB | `db.version()` and `db.adminCommand({getParameter: 1, featureCompatibilityVersion: 1})` on every member | [mongodb](references/mongodb/versions/index.md) |
| Amazon DocumentDB | `EngineVersion` from `aws docdb describe-db-clusters`; patch level from `db.runCommand({getEngineVersion: 1})`. Do not read compatibility from `db.version()` or `buildInfo` | [documentdb](references/documentdb/versions/index.md) |
| Azure Cosmos DB | API, capacity mode, and the MongoDB (RU) `apiProperties.serverVersion` from `az cosmosdb show`. Azure DocumentDB (formerly vCore-based Cosmos DB for MongoDB) is a separate cluster service that `az cosmosdb show` does not find; its MongoDB version is on the cluster's Overview page. Neither is Amazon DocumentDB | [cosmos-db](references/cosmos-db/versions/index.md) |
| Couchbase | `GET /pools` on port 8091 (`implementationVersion`) or `SELECT RAW DS_VERSION();`; during an upgrade, `clusterCompatVersion` from `/pools/default/terseClusterInfo` | [couchbase](references/couchbase/versions/index.md) |
| Redis | `INFO server` (`redis_version`); a `server_name:valkey` line means the server is Valkey | [redis](references/redis/versions/index.md) |
| Valkey | `INFO server` (`valkey_version`; `redis_version` stays at the compatibility value `7.2.4`) | [valkey](references/valkey/versions/index.md) |
| Memcached | `version` or `stats` (`version`) | [memcached](references/memcached/versions/index.md) |
| Amazon DynamoDB | No server version. Record the global tables version and capacity settings from `describe-table`, the CLI or SDK release, and for DynamoDB local the `Version:` line of its startup log | [dynamodb](references/dynamodb/versions/index.md) |

Each index also shows how to read the engine version on the managed services and how to interpret the output.

## Route by Topic

Read the product's topic file for the question, then the version file when a default, syntax, or removal matters. Topic files live in `references/<directory>/`:

| Question | MySQL, MariaDB, PostgreSQL | MongoDB, Couchbase | Redis, Valkey |
|---|---|---|---|
| Schema, document, or key design | `schema-and-indexes.md` | `data-modeling.md` | `data-modeling.md` |
| Indexes, execution plans, query tuning | `query-plans.md`, `schema-and-indexes.md` | MongoDB `indexes-and-query-plans.md`; Couchbase `indexes-and-queries.md` | `latency-and-monitoring.md` (slow commands, big keys) |
| Transactions, isolation, locks, deadlocks | `transactions-and-locking.md` | MongoDB `transactions-and-consistency.md`; Couchbase `transactions-and-durability.md` | `data-modeling.md` (atomicity, `MULTI`, scripts) |
| Replication, HA, failover, sharding | `replication-and-ha.md` | MongoDB `replication-and-sharding.md`; Couchbase `replication-and-xdcr.md` | `replication-and-cluster.md` |
| Backup, restore, PITR | `backup-and-recovery.md` | `backup-and-recovery.md` | `persistence-and-recovery.md` |
| Memory, storage, connections, durability settings | `configuration.md` | MongoDB `configuration.md`; Couchbase `configuration-and-sizing.md` | `memory-and-configuration.md` |
| Authentication, privileges, TLS, auditing | `security.md` | `security.md` | `security.md` |
| Monitoring, slow queries, latency | `monitoring.md` | `monitoring.md` | `latency-and-monitoring.md` |
| Managed service differences | `managed-services.md` | `managed-services.md` | `managed-services.md`; Redis licensing in `licensing.md` |

PostgreSQL adds `vacuum-and-maintenance.md`. Valkey topic files cover what differs from Redis OSS 7.2 and link to the Redis file for the shared mechanism, so a Valkey question usually needs both.

The other products have their own file sets:

| Product | Files |
|---|---|
| Amazon DocumentDB | `compatibility.md` (MongoDB API support per engine version, transaction limits), `data-modeling-and-indexes.md` (indexes, planners, explain), `architecture-and-operations.md` (instances, endpoints, failover, backup, parameter groups, security, monitoring) |
| Azure Cosmos DB | `apis.md` (which API and offering; read first), `nosql-modeling-and-partitioning.md` (partition keys, transactions, concurrency), `request-units-and-indexing.md`, `consistency-and-replication.md`, `operations.md` (backup, security, monitoring, 429s), `mongodb-compatibility.md` (RU offering and Azure DocumentDB), `emulator.md` |
| Amazon DynamoDB | `data-modeling.md`, `capacity-and-performance.md`, `transactions-and-consistency.md`, `global-tables-and-streams.md`, `backup-and-recovery.md`, `security-and-monitoring.md`, `dynamodb-local.md` |
| Memcached | `guide.md`, `managed-services.md` |

For Amazon DocumentDB, Cosmos DB for MongoDB (RU), and Azure DocumentDB, start from `documentdb/compatibility.md` or `cosmos-db/mongodb-compatibility.md`; MongoDB's version files and defaults do not apply to these services, and the MongoDB topic files hold only the shared semantics. For symptoms that could come from several layers, or systems that combine products, start with [cross-engine routing](references/cross-engine.md).

## Work from Evidence

- Diagnose before changing anything. Collect the plan, waits, locks, and metrics the topic file names, connect them to the mechanism, and say what each piece of evidence rules in or out.
- Prefer read-only commands when inspecting a production system. Mark any statement that takes locks, rewrites a table, restarts a process, triggers a failover, or deletes data, and give the safer alternative or rehearsal.
- For a change, state its expected effect, the cost (locking, replication lag, I/O, memory, failover time), how to verify it, and how to roll it back.
- Keep these kinds of statement apart: documented guarantees, defaults of a specific version, results observed on official images, results from the user's system, and your own inference. Claim a performance improvement only from comparable before/after measurements.
- Carry the references' markers into the answer when a conclusion rests on them: where a reference gives a way to check (a command, a console item, or an official page) instead of a fact, pass that check to the user rather than stating an outcome; "inference" and "guideline" are reasoning or thresholds the vendor does not state; "container" results were observed on an official image on the check date, not on the user's server. Attribute them to the reference ("the guide records this on the official 8.4.13 image"); do not present them as a test you ran. Results from the Cosmos DB emulator or DynamoDB local are not service behavior.
- When a fact needed for the answer is not in the references and cannot be confirmed from official documentation, say so instead of filling the gap.

## Boundaries

- Kysely query code (writing, converting from SQL, refactoring, type errors) belongs to `kysely-converter`. When a slow or failing Kysely query needs engine work, use this guide for the plan, indexes, locks, and settings, and `kysely-converter` for the TypeScript change.
- Application, ORM, and driver code are in scope only where they change what the server does: transaction boundaries, isolation, connection pooling, retries, and read preference.
- For a move between products, such as MySQL to MariaDB, MongoDB to DocumentDB or Cosmos DB, or Redis to Valkey, find the target's compatibility section in the [move table](references/cross-engine.md#moving-between-products), then read the target's version files.

## Coverage Record

Reference facts were checked against official sources on 2026-11-27; each `versions/index.md` ends with its sources, and many topic files list their own. [The coverage record](updates/2026-11-27-initial-coverage.md) lists the official images that were run, with digests, and what rests on documentation only: Amazon DocumentDB, Cosmos DB and DynamoDB service behavior, the managed services, and multi-node behavior such as elections, rebalancing, and failover.
