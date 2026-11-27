# Cross-Engine Routing

Checked: 2026-11-27. Use when a symptom could come from the database, the network, the connection pool, or the application, when a system uses more than one of the covered products, or when moving data or applications from one product to another.

## Separate the Layers First

Before reading an engine file, find out where the time or the error arises:

1. Compare the latency the application measures with the duration the server records for the same operation (slow query log, `pg_stat_statements`, the MongoDB profiler or slow-operation log, `SLOWLOG`, CloudWatch or Azure Monitor latency metrics). A large gap points to pool waits, network, TLS handshakes, client-side retries, or serialization in the application rather than to the engine.
2. Check whether errors are rejections (throttling, connection limits, memory limits, admission control) or failures of the work itself (lock timeouts, deadlocks, write conflicts, validation errors). The two lead to different files.
3. Note what changed: deployment, data volume, traffic shape, engine version or parameters, schema or index, client library. A regression that starts at an upgrade belongs to the version files first.

| Symptom | Read first |
|---|---|
| A query or request became slow | `query-plans.md` and `monitoring.md` (MySQL, MariaDB, PostgreSQL); MongoDB `indexes-and-query-plans.md` and `monitoring.md`; Couchbase `indexes-and-queries.md`; Redis or Valkey `latency-and-monitoring.md`; DynamoDB `capacity-and-performance.md`; Cosmos DB `request-units-and-indexing.md`; DocumentDB `data-modeling-and-indexes.md` and the monitoring section of `architecture-and-operations.md` |
| Lock waits, deadlocks, write conflicts, serialization failures | `transactions-and-locking.md` (SQL engines); `transactions-and-consistency.md` (MongoDB, DynamoDB); Couchbase `transactions-and-durability.md`; DocumentDB [transaction limits](documentdb/compatibility.md#sessions-transactions-and-retryable-writes); Cosmos DB [transactions and concurrency](cosmos-db/nosql-modeling-and-partitioning.md#transactions-and-concurrency) |
| Throttling or rate rejections on a managed service | DynamoDB `capacity-and-performance.md`; Cosmos DB `operations.md` and `request-units-and-indexing.md`; the engine's `managed-services.md` for RDS, Aurora, ElastiCache, MemoryDB, or Atlas limits |
| Replicas behind, stale reads, failover took too long | `replication-and-ha.md` (SQL engines); MongoDB `replication-and-sharding.md`; Couchbase `replication-and-xdcr.md`; Redis or Valkey `replication-and-cluster.md`; DynamoDB `global-tables-and-streams.md`; Cosmos DB `consistency-and-replication.md`; DocumentDB `architecture-and-operations.md` |
| Connection limit reached, connection storms | `configuration.md` and `monitoring.md` (SQL engines, MongoDB); Redis or Valkey `memory-and-configuration.md` (`maxclients`) and `latency-and-monitoring.md`; Memcached `guide.md` (`-c`); Couchbase `monitoring.md`; `managed-services.md` for limits that the service sets |
| Memory pressure, evictions, out-of-memory kills | `configuration.md` (SQL engines, MongoDB); Redis or Valkey `memory-and-configuration.md`; Memcached `guide.md`; Couchbase `configuration-and-sizing.md` |
| Storage keeps growing | PostgreSQL `vacuum-and-maintenance.md` for bloat, `backup-and-recovery.md` for a failing WAL archive, `replication-and-ha.md` for WAL held by slots; MySQL or MariaDB `replication-and-ha.md` for binary log retention; MongoDB `replication-and-sharding.md` for oplog size; Redis or Valkey `persistence-and-recovery.md` for AOF growth |
| Behavior changed after an upgrade | The product's `versions/index.md`, then every version file between the old and new series |

## Same Words, Different Guarantees

Isolation and consistency names do not mean the same thing across products. Before porting retry logic, locking assumptions, or read-after-write expectations, read the target product's transactions or consistency file.

| Product | Default observed or documented | Where the semantics are explained |
|---|---|---|
| MySQL (InnoDB) | `REPEATABLE-READ` (`transaction_isolation` on the official 8.0, 8.4, 9.7, 26.7, and 26.10 images) | [MySQL transactions](mysql/transactions-and-locking.md) |
| MariaDB (InnoDB) | `REPEATABLE-READ` (`tx_isolation` on 10.6 and 10.11, `transaction_isolation` on 11.4 to 13.0 images) | [MariaDB transactions](mariadb/transactions-and-locking.md) |
| PostgreSQL | `read committed` (`default_transaction_isolation` on the 14 to 19 images) | [PostgreSQL transactions](postgresql/transactions-and-locking.md) |
| MongoDB replica set | Read concern `local`, write concern `majority` (implicit defaults from `getDefaultRWConcern` on the 7.0, 8.0, 8.3, and 9.0 images, single-node replica set without arbiters) | [MongoDB transactions and consistency](mongodb/transactions-and-consistency.md) |
| Amazon DocumentDB | Documentation only | [DocumentDB architecture](documentdb/architecture-and-operations.md), [compatibility](documentdb/compatibility.md) |
| Azure Cosmos DB | Account-level setting; the emulator advertises a different default from a new Azure account | [Cosmos DB consistency](cosmos-db/consistency-and-replication.md), [emulator](cosmos-db/emulator.md) |
| Couchbase | Per-request durability level and per-query scan consistency | [Couchbase transactions and durability](couchbase/transactions-and-durability.md) |
| Redis, Valkey | Asynchronous replication; `WAIT` does not make it synchronous | [Redis replication](redis/replication-and-cluster.md), [Valkey replication](valkey/replication-and-cluster.md) |
| DynamoDB | Per-request read consistency; global secondary indexes are eventually consistent | [DynamoDB transactions and consistency](dynamodb/transactions-and-consistency.md) |

`REPEATABLE READ` is the clearest trap: InnoDB and PostgreSQL both accept the name, but they differ in what a locking read sees and in when a concurrent update raises an error. Their transactions files describe each engine's behavior.

## Moving Between Products

| Move | Read |
|---|---|
| MySQL and MariaDB in either direction, or replication between them | [MariaDB replication with MySQL](mariadb/replication-and-ha.md#replicating-between-mysql-and-mariadb), then the version files of both products |
| MongoDB to Amazon DocumentDB | [DocumentDB compatibility](documentdb/compatibility.md) and the target engine version file |
| MongoDB to Azure Cosmos DB for MongoDB (RU) or Azure DocumentDB | [Cosmos DB MongoDB compatibility](cosmos-db/mongodb-compatibility.md#migration-paths). Azure DocumentDB, the renamed vCore offering, is a Microsoft service and is unrelated to Amazon DocumentDB. |
| Redis to Valkey | [Valkey migration from Redis](valkey/persistence-and-recovery.md#migration-from-redis), [Valkey versions](valkey/versions/index.md), and [Redis licensing](redis/licensing.md) |
| ElastiCache or MemoryDB from the Redis OSS engine to Valkey | [Valkey managed services](valkey/managed-services.md) |
| Self-managed to Amazon RDS, Aurora, ElastiCache, MemoryDB, MongoDB Atlas, or Couchbase Capella | The engine's `managed-services.md`, then its `versions/index.md` for the versions the service offers |
| Memcached to Redis or Valkey | [Memcached guide](memcached/guide.md) for the current semantics and [Redis data modeling](redis/data-modeling.md) for the target; the eviction, persistence, and replication models differ |
