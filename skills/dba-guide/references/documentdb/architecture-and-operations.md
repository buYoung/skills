# Amazon DocumentDB Architecture and Operations

Checked: 2026-11-27. Read this for questions about sizing, HA, failover, replicas, global clusters, backup and restore, maintenance, parameters, security, or monitoring on Amazon DocumentDB. Everything here is managed-service behavior from AWS documentation, because there is no self-hosted DocumentDB to compare against. For MongoDB-side equivalents see [../mongodb/managed-services.md](../mongodb/managed-services.md).

## Contents

- [What the service takes over and what it removes](#what-the-service-takes-over-and-what-it-removes)
- [Storage and instances](#storage-and-instances)
- [Endpoints and connection strings](#endpoints-and-connection-strings)
- [Replication, failover, and read scaling](#replication-failover-and-read-scaling)
- [Transactions and consistency](#transactions-and-consistency)
- [Global clusters](#global-clusters)
- [Serverless and elastic clusters](#serverless-and-elastic-clusters)
- [Backup, snapshots, PITR, and cloning](#backup-snapshots-pitr-and-cloning)
- [Change streams operations](#change-streams-operations)
- [Maintenance, patching, and stop/start](#maintenance-patching-and-stopstart)
- [Configuration: cluster parameter groups](#configuration-cluster-parameter-groups)
- [Security](#security)
- [Monitoring](#monitoring)
- [Garbage collection and MVCC ID exhaustion](#garbage-collection-and-mvcc-id-exhaustion)
- [Sources](#sources)

## What the service takes over and what it removes

| Area | DocumentDB |
| --- | --- |
| Durability and replication | The storage layer keeps six copies across three AZs. There is no replica-set configuration, oplog, arbiter, or election tuning |
| Superuser | The primary user and `serviceadmin` hold `root` in DocumentDB's role model. There is no OS, file system, or `mongod` access |
| Configuration | About ten cluster parameters (see [configuration](#configuration-cluster-parameter-groups)) replace `mongod.conf` and `setParameter` |
| Version | You choose from the engine versions AWS publishes. Required engine patches auto-apply, and minor and major upgrades are your action |
| Backups | Continuous backup to service-managed S3, retained 1 to 35 days. It cannot be disabled, and the backup files are not accessible |
| Diagnostics | CloudWatch metrics, profiler and audit logs in CloudWatch Logs, Performance Insights, `currentOp`, `collStats`, `$indexStats`. There are no server logs, `mongostat`, `mongotop`, or FTDC |
| Network | VPC only. Default port 27017; elastic clusters allow only 27017 |

## Storage and instances

- A cluster has exactly one cluster volume and 0 to 16 instances: one primary plus up to 15 replicas. The volume is SSD-backed with six copies across three AZs, repairs failed segments automatically, and grows on demand up to 256 TiB on 8.0 (128 TiB on earlier versions). From 4.0 on, the volume shrinks when you drop collections, indexes, or databases. On 3.6 it does not; see [versions/3.6.md](versions/3.6.md#behavior-specific-to-36).
- Compute and storage are separate. Instances in one cluster can have different classes. Adding a replica copies no data; it "usually" takes less than ten minutes.
- Durability does not depend on instance count: a single-instance cluster is as durable as a three-instance one. Availability does depend on it. With no replica, a failed primary is re-created in the same AZ on a best-effort basis.
- The page cache lives in a separate process and survives a database process restart ("survivable cache warming"). After an OS update or on a new instance the cache is cold, and `BufferCacheHitRatio` stays low until the working set is reloaded.
- Under memory pressure the engine throttles and queues operations, and queued operations can time out. Watch `LowMemThrottleQueueDepth`, `LowMemNumOperationsThrottled`, and `LowMemNumOperationsTimedOut`. Scale the instance up if they stay non-zero.

Storage configuration:

| Option | Use when | Versions |
| --- | --- | --- |
| Standard | I/O is a small part of the bill | All |
| I/O-Optimized (`--storage-type iopt1`) | I/O charges dominate. Instance and storage prices are higher, and there is no per-I/O charge | 5.0, 8.0 |

Instance classes (from the [features table](https://docs.aws.amazon.com/documentdb/latest/devguide/docdb-engine-version-supportability.html) and [quotas](https://docs.aws.amazon.com/documentdb/latest/devguide/limits.html)):

| Family | Versions | Notes |
| --- | --- | --- |
| `db.r8g` (Graviton4), up to `48xlarge` | 5.0, 8.0 | |
| `db.r6g`, `db.r6gd` (NVMe cache) | r6g 4.0 and later; r6gd 5.0 and later | |
| `db.r5` | All | |
| `db.r4` | 3.6 only | Blocks upgrades to 4.0 and later |
| `db.t3.medium`, `db.t4g.medium` | t3 all; t4g 4.0 and later | Burstable. Not supported in global clusters. Scale up before an MVU |
| `db.serverless` | 5.0, 8.0 | See [serverless](#serverless-and-elastic-clusters) |

Per-instance limits scale with the class. Examples for 4.0 and later: `r6g.large` allows 3,400 connections, 450 cursors, 200 open transactions, and 1,100 active connections; `r8g.16xlarge` allows 60,000 connections, 3,040 cursors, 6,400 transactions, and 4,500 active connections. Alarm on each usage metric against its limit metric: `DatabaseConnectionsMax` against `DatabaseConnectionsLimit`, `DatabaseCursorsMax` against `DatabaseCursorsLimit`, `TransactionsOpenMax` against `TransactionsOpenLimit`.

Cluster limits: 16 MiB documents, 200 nesting levels, 64 indexes per collection, 32 keys per compound index, 2,048-byte index keys, 32 TiB per collection and per index, 100,000 collections and 100,000 databases, 100,000 writes per batch, 500 aggregation stages, 1,000 users.

## Endpoints and connection strings

| Endpoint | Routes to | Use for |
| --- | --- | --- |
| Cluster endpoint (`<name>.cluster-<id>.<region>.docdb.amazonaws.com`) | Current primary; follows failover | All application traffic, in replica-set mode |
| Reader endpoint (`.cluster-ro-`) | Balances connections (not requests) across replicas; falls back to the primary if there are no replicas | Simple read-only clients. Load can end up uneven, so prefer the cluster endpoint with a read preference |
| Instance endpoint | One instance | Isolated analytics on a dedicated replica, or diagnostics such as per-node `currentOp`. Never use the primary's instance endpoint for production, because roles change on failover |

Recommended connection string:

```
mongodb://<user>:<password>@<cluster-endpoint>:27017/?tls=true&tlsCAFile=global-bundle.pem&replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false
```

- The replica set is always named `rs0`, and the name cannot be changed. Read preference is honored only in replica-set mode.
- `retryWrites=false` is required below 8.0.2 and optional from 8.0.2.
- With `directConnection=true` to the reader endpoint, writes fail.
- Applications must retry after a dropped connection, because failover flips a DNS CNAME.

## Replication, failover, and read scaling

Mechanism: the primary writes durably to the shared volume, then sends the state change to the replicas. Replicas do not apply writes themselves. Replica lag is usually under 100 ms and grows with the write rate. Replicas return data in the primary's write order.

Failover:

- Failover is automatic. The cluster CNAME moves to a promoted replica, typically within 30 seconds. With no replica, the primary is re-created in place, best effort.
- The target is chosen by failover tier (0 to 15, lower wins). Within a tier, the replica closest in size to the old primary wins. Give failover targets the same instance class as the primary, and put heavy analytics replicas in a high tier. Set the tier with `--promotion-tier` on `create-db-instance` or `modify-db-instance`.
- Test failover with `--target-db-instance-identifier`, which overrides tiers:

  ```
  aws docdb failover-db-cluster --db-cluster-identifier mycluster \
    --target-db-instance-identifier mycluster-2
  ```

  This causes a short write outage. Run it in a test window first and confirm the application reconnects. Verify with `aws docdb describe-db-clusters --db-cluster-identifier mycluster --query 'DBClusters[0].DBClusterMembers[].[DBInstanceIdentifier,IsClusterWriter,PromotionTier]'`.
- Changing a tier does not trigger a failover.

HA rules:

- Recommendation (derived from the failover and patching docs): run at least two instances in different AZs for production. Run at least two replicas if clients use `secondary` read preference and must keep reading during reader patching.
- On 5.0 and 8.0, readers are patched in three groups while the writer is briefly offline. Reads stay available only if the read preference can fall back:

  | Read preference | Writer patching | Reader patching | Minimum readers for zero read downtime |
  | --- | --- | --- | --- |
  | `primary` | read and write downtime | no impact | n/a |
  | `primaryPreferred` | write downtime | no impact | 1 |
  | `secondary` | write downtime | read downtime if only one reader | 2 |
  | `secondaryPreferred` | write downtime | no impact | 1 |
  | `nearest` | write downtime | no impact | 1 |

- From 5.0 patch 3.0.11800, readers keep serving reads during a writer restart.

Read preference semantics: `primary` gives read-after-write consistency but fails without a primary. `secondaryPreferred` reads eventually consistent data from replicas and frees the writer. `nearest` routes by measured latency. Tag sets are not supported.

## Transactions and consistency

- The functional-differences page both calls multi-document CRUD statements atomic and says a whole `updateMany`/`deleteMany`/`insertMany` is not atomic. Use a transaction (4.0 or later) when such a statement must succeed or fail as a whole. See [compatibility.md](compatibility.md#sessions-transactions-and-retryable-writes).
- Isolation is snapshot. If a failover happens between a write and a read on the primary, the read can briefly be not strongly consistent.
- Every write is acknowledged by a storage quorum. Write concern cannot be lowered, and acknowledged writes are never rolled back.
- Reads see only data that was durable when the query started, never uncommitted data.
- Limits (1-minute transactions, 30-minute sessions, 32 MB transaction log, no cursors or collection creation inside a transaction) and the retryable-write rules are in [compatibility.md](compatibility.md#sessions-transactions-and-retryable-writes).
- Monitor `TransactionsOpen`, `TransactionsOpenMax`, `TransactionsAborted`, `TransactionsCommitted`, `TransactionsStarted`, and their `DatabaseTransactions*` cluster variants. `currentOp` shows `lsid`, `transactionThreadId`, and an `idle transaction` state, and `serverStatus` has transaction counters.
- Long transactions and long-running cursors hold back garbage collection; see [garbage collection](#garbage-collection-and-mvcc-id-exhaustion).

## Global clusters

- One primary Region and up to 10 read-only secondary Regions. Replication runs on dedicated infrastructure with lag typically under a second. A secondary cluster can have up to 16 read instances.
- Supported on 4.0, 5.0, and 8.0, but not on 3.6, on `db.t3`/`db.t4g`/`db.r4`, in São Paulo, Milan, Beijing, or Ningxia, or on elastic clusters.
- Change streams can be read from a secondary cluster (5.0 and later).
- When the primary Region's writer restarts or fails over, secondary replicas restart and stay unavailable until they resynchronize. 5.0.1 removed this secondary reboot ("Global Survivable Read Only").
- Secondary clusters cannot be stopped, and neither can a primary that has secondaries.
- In-place MVU is not supported; see [versions/index.md](versions/index.md#limits).
- Use the same planner version in every Region.

DR operations ([disaster recovery page](https://docs.aws.amazon.com/documentdb/latest/devguide/global-clusters-disaster-recovery.html)):

| Operation | Command | Data loss | Notes |
| --- | --- | --- | --- |
| Switchover (planned) | `aws docdb switchover-global-cluster --region <primary-region> --global-cluster-identifier <id> --target-db-cluster-identifier <secondary-arn>` | None; waits for full sync | Brief unavailability, up to a few minutes. The old primary becomes a secondary |
| Managed failover (unplanned) | `aws docdb failover-global-cluster --region <secondary-region> --global-cluster-identifier <id> --target-db-cluster-identifier <secondary-arn> --allow-data-loss` | Unreplicated writes are lost | Choose the secondary with the lowest `GlobalClusterReplicationLag`. Once its Region recovers, the old primary rejoins as a secondary after a best-effort snapshot named `rds:docdb-unplanned-global-failover-...`; copy that snapshot to a manual one to keep it. The new primary does not inherit the old parameter group or alarms |
| Manual detach and promote | Remove the chosen secondary from the global cluster, then remove the others to avoid split-brain | Unreplicated writes are lost | Works when engine versions differ |

- Switchover and managed failover need the same engine patch level in every Region and no pending modifications or maintenance on the target. Otherwise they fail with "The target DB cluster specified is running an engine version with a different patch level than the source DB cluster". Patch the secondaries first, then the primary.
- The 22 Aug 2024 release notes limit switchover and managed failover to 4.0 and 5.0, and no later note mentions 8.0; the disaster-recovery page sets no version limit. Before you rely on it on 8.0, run `aws docdb switchover-global-cluster --global-cluster-identifier <id> --target-db-cluster-identifier <secondary-arn>` on a test 8.0 global cluster (see [versions/8.0.md](versions/8.0.md#managed-service-notes)).
- Tunable RPO (8.0.1 and later): set `global_db_rpo` (20 to 2,147,483,647 seconds, dynamic) in the primary's parameter group. Commits on the primary block when every secondary lags beyond the RPO. With only two Regions, keep the default in the secondary's group, or a failover can pause transactions.

## Serverless and elastic clusters

Serverless (5.0 and 8.0):

- Capacity is measured in DCUs (about 2 GiB of memory plus matching CPU and network each). Set `ServerlessV2ScalingConfiguration` (`MinCapacity`, `MaxCapacity`) before you add `db.serverless` instances. Connection, cursor, and transaction limits follow the current capacity.
- Raise `MinCapacity` when you use Performance Insights, for the primary Region of a global cluster, and before you create or restore serverless instances on a large volume. Too low a minimum leads to out-of-memory errors.
- Parallel index builds need at least 32 DCUs minimum capacity and get about `min_DCU / 8` workers. A change to the minimum takes effect after a restart.
- Platform version 4 gives up to 35% more throughput than version 3. Upgrade through the `serverless-platform-version-update` maintenance action.
- An MVU needs a maximum capacity of at least 3 DCU.

Elastic clusters: hash-sharded, 5.0 wire protocol, with many features missing; see [compatibility.md](compatibility.md#elastic-clusters). Operationally they have no PITR, cloning, parameter groups, profiler, or Performance Insights. They do have automatic snapshot backups, snapshot copy, and start/stop. Scale out by adding shards (data redistributes automatically) and scale up by raising vCPUs per shard. DDL is blocked while scaling. Metrics are in the `AWS/DocDB-Elastic` namespace, and `BufferCacheHitRatio` and `DBInstanceReplicaLag` are published per shard only.

## Backup, snapshots, PITR, and cloning

| Mechanism | Scope | Retention | Restore result | Notes |
| --- | --- | --- | --- | --- |
| Continuous backup (automatic) | Cluster volume | 1 to 35 days (default 1); cannot be disabled | PITR to any point in the window, into a new cluster | No performance impact |
| Automatic snapshot | Taken daily in the backup window | Same retention; deleted with the cluster | New cluster | Cannot be shared; copy it to a manual snapshot first |
| Manual snapshot | Full backup on demand | Until you delete it; survives cluster deletion | New cluster at snapshot time | 100 per Region. Shareable, and copyable across Regions and accounts |
| Clone | Copy-on-write volume | Independent cluster | Immediate | No extra storage until data diverges. Best for upgrade rehearsals and testing. Not on elastic clusters |
| `mongodump`/`mongorestore` | Logical | Yours | Any target | Database Tools 100.11.0 or earlier. No users or roles. Incurs I/O charges. The only way to reset the 3.6 storage high-water mark |
| AWS Backup | Cluster | Backup plan | New cluster | Not on elastic clusters |

Restore rules:

- Every restore creates a new cluster. A CLI restore creates no instances; add them with `create-db-instance` once the cluster is `available`.
- The restored cluster gets the default parameter group. Re-attach the custom group, or TLS, audit, and profiler settings fall back to defaults without warning.
- Other configuration comes from the source. Choose the storage type with `--storage-type standard|iopt1`.

PITR example:

```
aws docdb restore-db-cluster-to-point-in-time \
  --source-db-cluster-identifier prod \
  --db-cluster-identifier prod-restore-0315 \
  --restore-to-time 2026-11-20T03:15:00Z

aws docdb create-db-instance --db-cluster-identifier prod-restore-0315 \
  --db-instance-identifier prod-restore-0315-1 \
  --db-instance-class db.r6g.large --engine docdb

aws docdb modify-db-cluster --db-cluster-identifier prod-restore-0315 \
  --db-cluster-parameter-group-name prod-params --apply-immediately
```

Use `--use-latest-restorable-time` instead of `--restore-to-time` to restore to the latest point. Read the restorable window from `EarliestRestorableTime` and `LatestRestorableTime` in `describe-db-clusters`. PITR cannot change the engine version.

Restore verification on every drill:

1. Wait until the cluster and its instances show `Status: available`. If parameters show `pending-reboot`, reboot each instance; `tls` is static.
2. Compare `db.collection.countDocuments({})` and key aggregates with values recorded on the source at the target time. Live source numbers keep changing.
3. Check `db.collection.getIndexes()` on important collections, and run representative queries with `explain()` to confirm index use.
4. Run `show users`. Inference, not stated in the documentation: users live in the cluster volume, so a snapshot restore or PITR should bring them back, while `mongorestore` does not.
5. Confirm change streams are enabled where consumers expect them: `aggregate([{$listChangeStreams: 1}])`.
6. Measure the time to "available and warm cache". That is your real RTO.

## Change streams operations

- Off by default. Enable per namespace with `modifyChangeStreams` (see [compatibility.md](compatibility.md#admin-tooling-and-operational-commands)). A collection is enabled if it, its database, or the whole cluster is enabled. A dropped and re-created collection stays enabled while its database is enabled.
- Retention is set by `change_stream_log_retention_duration`: 3,600 to 604,800 seconds, default 10,800 (3 hours), dynamic. Expired entries are deleted only once the log exceeds 51,200 MB. Size retention to cover the longest consumer outage plus any DMS migration.
- Change streams add read and write I/O and storage, visible in `ChangeStreamLogSize` (part of `VolumeBytesUsed`).
- On 3.6 and 4.0, open change streams on the primary with `primary` read preference. On 5.0 and later they can also run on replicas, and resume tokens work across instances.
- Resume options: a resume token; `startAtOperationTime` (4.0 and later, and 3.6 from patch 1.0.208692); `postBatchResumeToken` (5.0 patch 3.0.11800 and later). Resuming from an old regular token makes the server scan everything since that point and can spike CPU, so persist each batch's `postBatchResumeToken`.
- An event larger than 16 MB fails the read. On 8.0.2 and later, add `$changeStreamSplitLargeEvent` as the last stage. Otherwise keep documents and `fullDocument` lookups smaller.
- A long `updateMany` or `deleteMany` can stall change stream writes until it completes.
- `fullDocument: 'updateLookup'` returns the document as of the lookup, not as of the update.
- The change streams page lists full document lookup for updates among supported operations and does not mention pre-images (`fullDocumentBeforeChange`, `changeStreamPreAndPostImages`). Inference, not stated in the documentation: plan as if pre-images are unavailable, and have a consumer that needs the previous value record it itself (for example in an outbox document written in the same transaction). Test on the target engine version before deciding.

## Maintenance, patching, and stop/start

- Each cluster and each instance has a weekly 30-minute maintenance window. Engine work uses the cluster window. If you do not set one, AWS assigns a random window inside a Regional 8-hour block.
- Every engine patch takes the cluster offline briefly. On 5.0 and 8.0, with replicas and a fallback read preference, reads continue. On 3.6 and 4.0, both reads and writes stop, for longer.
- Patch categories: optional, required, forced. Required patches auto-apply in the window after `AutoAppliedAfterDate` (about 30 days after release); defer them by moving the window before that date. Forced patches apply after `ForcedApplyDate`, even outside the window. Minor versions never auto-apply. Required and forced patches are announced in AWS Health Dashboard and by email; optional patches and minor versions appear only in the release notes.
- OS updates run through the cluster-level `os-upgrade` action: rolling, a few instances at a time, primary last (with a failover). An instance-level `system-update` and an `os-upgrade` cannot be scheduled at the same time. Subscribe to `RDS-EVENT-0230` for new optional OS updates.
- A single-instance cluster is fully offline during an OS update. Add a temporary replica for the update and remove it afterward.
- To find and apply pending actions:

  ```
  aws docdb describe-pending-maintenance-actions --filters Name=db-cluster-id,Values=mycluster
  aws docdb apply-pending-maintenance-action \
    --resource-identifier arn:aws:rds:us-east-1:123456789012:cluster:mycluster \
    --apply-action system-update --opt-in-type next-maintenance
  ```

  `--opt-in-type immediate` cannot be undone. `undo-opt-in` cancels a `next-maintenance` opt-in.
- For automation, the EventBridge events are `AWS_DOCDB_DB_PATCH_UPGRADE_MAINTENANCE_SCHEDULED` and `AWS_DOCDB_DB_PATCH_UPGRADE_MAINTENANCE_CANCELLED`.
- Stop and start with `aws docdb stop-db-cluster` and `aws docdb start-db-cluster`. A stopped cluster restarts automatically after 7 days. While it is stopped you pay only for storage, manual snapshots, and backup storage, no automated backups run, and the cluster cannot be modified. PITR still works.

## Configuration: cluster parameter groups

Default groups (`default.docdb3.6` through `default.docdb8.0`) cannot be changed. Create a custom group in the matching family, attach it with `modify-db-cluster --db-cluster-parameter-group-name`, and reboot for static parameters.

| Parameter | Default | Values | Apply | Notes |
| --- | --- | --- | --- | --- |
| `tls` | `enabled` | `enabled`, `disabled`, `fips-140-3`, `tls1.2+`, `tls1.3+` | Static (reboot) | `tls1.2+`/`tls1.3+` from 4.0 patch 2.0.10980 and 5.0 patch 3.0.11051. `fips-140-3` from 5.0 patch 3.0.3727, in six Regions |
| `audit_logs` | `disabled` (`none`) | `ddl`, `dml_read`, `dml_write`, `all`, `none`, and combinations; legacy `enabled`/`disabled` | Dynamic | Also needs the `audit` log export |
| `profiler` | `disabled` | `enabled`, `disabled` | Dynamic | Also needs the `profiler` log export |
| `profiler_threshold_ms` | 100 | 50 to 2,147,483,646 | Dynamic | Start at 500 on busy clusters |
| `profiler_sampling_rate` | 1.0 | 0.0 to 1.0 | Dynamic | |
| `change_stream_log_retention_duration` | 10800 | 3600 to 604800 seconds | Dynamic | |
| `default_collection_compression` | 5.0 `disabled`; 8.0 `zstd` | 5.0 `enabled`/`disabled`; 8.0 `zstd`/`lz4`/`disabled` | Dynamic | Affects new collections only |
| `planner_version` | 3.0 in the reference (the 8.0 default); 5.0 defaults to v1 | 1.0, 2.0, 3.0 | Dynamic | 2.0 needs 5.0 patch 3.0.15902 or later. Change it in low traffic, because error rates can rise during the switch |
| `ttl_monitor` | `enabled` | `enabled`, `disabled` | Dynamic | Suggestion, not from the documentation: pause it during bulk loads if TTL deletes compete for I/O |
| `global_db_rpo` | (unset) | 20 to 2,147,483,647 | Dynamic | 8.0.1 and later, global clusters |

Inspect current values:

```
aws docdb describe-db-cluster-parameters \
  --db-cluster-parameter-group-name my-params \
  --query 'Parameters[?Source==`user`].[ParameterName,ParameterValue,ApplyType]'
```

`describe-db-clusters` shows each member's `DBClusterParameterGroupStatus` (`in-sync` or `pending-reboot`) under `DBClusterMembers`.

There are no settings for cache size, the storage engine, connection pools, or journaling. Instance class is the only memory lever.

## Security

Network:

- Clusters sit in a VPC subnet group behind security groups on port 27017, and there is no public endpoint. Dual-stack IPv4/IPv6 is available on 4.0 (patch 2.0.11747 and later), 5.0 (patch 3.0.15902 and later), and 8.0.

Encryption in transit:

- TLS is enabled by default on new clusters. While it is enabled, only TLS connections are accepted. Clients need the AWS CA bundle (`global-bundle.pem`).
- 8.0, and 5.0.1 and later, accept TLS 1.2 and newer only. On older engines, set `tls1.2+` to enforce it.
- CA rotation without a reboot needs 3.6 patch 1.0.208662, 4.0 patch 2.0.10179, or 5.0 patch 3.0.4780 or later.
- 8.0.3 adds hybrid post-quantum key exchange (`X25519MLKEM768` preferred) for TLS 1.3 clients whose TLS library supports ML-KEM (OpenSSL 3.5 or later, Go 1.24 or later, Node.js 24.5 or later, among others). Its ClientHello is larger (1.2 to 1.5 KB), and old firewalls or TLS-inspecting proxies can reset it. If clients fail after the upgrade, fix the middlebox or limit the client to classical groups. To check one connection:

  ```
  openssl s_client -connect <endpoint>:27017 -groups X25519MLKEM768 -CAfile global-bundle.pem
  ```

  A post-quantum connection prints `Negotiated TLS1.3 group: X25519MLKEM768`.
- `tls` is a static parameter, so a change needs a reboot of every instance. Disabling TLS breaks clients that require it.

Encryption at rest:

- Encryption at rest is chosen at creation with an AWS KMS key. The console default is encryption with the `aws/rds` key. It cannot be enabled or disabled on an existing cluster; to change it, move the data into a new cluster. It covers the volume, indexes, logs, automated backups, and snapshots ([encryption at rest](https://docs.aws.amazon.com/documentdb/latest/devguide/encryption-at-rest.html)).

Authentication:

| Method | Versions | Notes |
| --- | --- | --- |
| Username and password (SCRAM) | All | The user-management page and release notes don't say which SCRAM mechanism a connection uses when the client doesn't choose one. To pin it, set `authMechanism=SCRAM-SHA-256` in the connection string on the patches in the next row and test the login; leave it unset on older patches |
| SCRAM-SHA-256 | 5.0.1 (patch 3.0.21138) and 8.0.1 (patch 4.0.8864), since 11 Aug 2026 | |
| IAM (`MONGODB-AWS`, `authSource=$external`) | Instance-based 5.0; 8.0 per the features table (conflict) | Create the user in `$external` with the IAM user or role ARN as its name. Not available for the primary user. Depends on AWS STS; on STS throttling exceptions, lower the connection rate. Monitor `StsGetCallerIdentityCalls`. Node.js drivers need 6.13.1 or later. Expiring IAM credentials do not drop existing connections |
| AWS Secrets Manager integration | Instance-based (features table) | Primary user only. DocumentDB generates the password, stores it in Secrets Manager and rotates it every seven days by default; the schedule can be changed. Not supported for clusters in a global cluster or for cross-Region read replicas. Deleting the cluster deletes the secret (Secrets Manager page) |

Authorization (RBAC):

- Built-in roles: `read`, `readWrite`, `dbAdmin`, `dbOwner`, `readAnyDatabase`, `readWriteAnyDatabase`, `dbAdminAnyDatabase`, `userAdminAnyDatabase`, `clusterMonitor`, `clusterManager`, `hostManager`, `clusterAdmin`, `backup`, `restore`, `root`.
- User-defined roles can grant specific actions on specific collections. They are not available on elastic clusters.
- Limits: 1,000 users, 100 user-defined roles, 1,000 roles per user, 100 resources per privilege.
- Users created before 26 Mar 2020 were given `dbAdminAnyDatabase`, `readWriteAnyDatabase`, and `clusterAdmin`. Review old users.
- Change-stream permissions: `listChangeStreams` is cluster-wide, and `modifyChangeStreams` applies at database or cluster level.
- Least-privilege example (AWS examples pass `pwd` as a literal; use a secret from your secret store):

  ```
  use admin
  db.createUser({user: "app", pwd: "<secret>", roles: [{role: "readWrite", db: "orders"}]})
  db.createRole({role: "ordersReader", privileges: [
    {resource: {db: "orders", collection: "invoices"}, actions: ["find"]}], roles: []})
  db.grantRolesToUser("reporting", ["ordersReader"])
  ```

Auditing:

- Enabling audit takes two steps, and skipping either one means nothing is logged:
  1. Set `audit_logs` (for example `ddl,dml_write`) in a custom parameter group.
  2. Enable the export with `modify-db-cluster --cloudwatch-logs-export-configuration '{"EnableLogTypes":["audit"]}'`.
- Events cover authentication, `authCheck` (result code 13 for unauthorized attempts), DDL, user and role management, and DML reads and writes. DML values are truncated at 1 KB. TTL deletes are not audited.
- Use `setAuditConfig`/`getAuditConfig` (4.0 and later) to filter DML events instead of logging everything. CloudWatch Logs charges apply.
- To find IAM logins, use the CloudWatch Logs pattern `{ $.param.mechanism = "MONGODB-AWS" }`.
- CloudTrail separately records control-plane API calls and is always on.

## Monitoring

Primary signals (CloudWatch namespace `AWS/DocDB`):

| Question | Metrics or commands | How to read |
| --- | --- | --- |
| Is the instance saturated? | `CPUUtilization`, `FreeableMemory`, `LowMemNumOperationsThrottled`, `DatabaseConnectionsMax` against `DatabaseConnectionsLimit`, active connections (`DatabaseConnectionsActiveMax`) | Sustained throttling or high CPU: scale up, or find the expensive queries with the profiler or Performance Insights |
| Is the working set cached? | `BufferCacheHitRatio`, `IndexBufferCacheHitRatio`; `cacheStats` in `db.coll.stats()` and `$indexStats` | A falling ratio on a steady workload suggests the instance is too small or an index is missing. `IndexBufferCacheHitRatio` can briefly exceed 100% after a drop |
| Are replicas behind? | `DBInstanceReplicaLag`, `DBClusterReplicaLagMaximum` (ms); `GlobalClusterReplicationLag` for global clusters | Short rises during write bursts are expected. Sustained lag points to an undersized replica |
| Storage and I/O cost | `VolumeBytesUsed`, `VolumeReadIOPs`, `VolumeWriteIOPs` (billed I/O per 5 minutes), `ChangeStreamLogSize`, `TotalBackupStorageBilled` | High billed reads together with a low cache hit ratio means the instance is too small for the working set |
| Per-command latency (5.0.1 and later; 8.0 from the April 2026 patch) | Command-level metrics for `find`, `insert`, `update`, `delete`, `aggregate`, `count`, `distinct`, `getMore`, `findAndModify`, `commitTransaction`, `abortTransaction`, with `AvgDuration`, `P100Duration`, `MaxConcurrent` | Use these for latency SLOs. Not available on elastic clusters |
| MVCC and garbage collection | `AvailableMVCCIds`, `LongestActiveGCRuntime` | See below |
| TLS key exchange (8.0.3) | `TLSHandshakesPostQuantum`, `TLSHandshakesClassical` | |

Slow queries:

1. Enable the profiler (`profiler=enabled`, `profiler_threshold_ms`, `profiler_sampling_rate`, plus the `profiler` log export). It covers `aggregate`, `count`, `delete`, `distinct`, `find`, `findAndModify`, `insert`, and `update`, writes to CloudWatch Logs on a best-effort basis, and can be queried with CloudWatch Logs Insights.
2. An operation is logged only if its whole result fits in one batch under 16 MB. Raise `batchSize` for the query you are investigating.
3. A 50 ms threshold on a high-throughput cluster can itself hurt performance. Start at 500 ms and lower it gradually.

Live diagnosis (on an instance endpoint):

```
db.adminCommand({aggregate: 1, pipeline: [
  {$currentOp: {}},
  {$match: {$or: [{secs_running: {$gt: 10}}, {WaitState: {$exists: true}}]}},
  {$project: {_id: 0, opid: 1, secs_running: 1, ns: 1, op: 1}}], cursor: {}})

db.adminCommand({killOp: 1, op: <opid>})
db.runCommand("listCursors")
```

`killOp` ends the user operation, and the client gets an error, so check the `opid` before you run it. `currentOp` also shows garbage-collection activity and, on 5.0 and later, index build progress.

Performance Insights:

- Shows database load by wait, query, host, and application, with 7 days of history. Available on instance-based 3.6 through 8.0, but not in GovCloud or on elastic clusters. Queries longer than 1,024 bytes are not aggregated.
- AWS announced end of life for Performance Insights on 31 Jul 2026 and moved its users to CloudWatch Database Insights. The Database Insights page lists only Aurora and RDS engines, while the DocumentDB PI page still describes PI as available. Neither page says what happens to DocumentDB PI. Before you recommend PI, open the cluster's Monitoring tab in the console and see whether it still offers Performance Insights or Database Insights.

## Garbage collection and MVCC ID exhaustion

- Every write consumes an MVCC ID from a finite counter, which starts from a maximum of 1.8 billion. Garbage collection (GC) recycles IDs from dead versions. If `AvailableMVCCIds` reaches zero, the cluster goes read-only until GC recycles IDs.
- Alarm when `AvailableMVCCIds` drops below 900 million on 5.0 and later, or below 1.3 billion on 3.6 and 4.0.
- Long-running transactions, queries, and open cursors hold back GC. Find them with `$currentOp`, end them, and close idle cursors. Since an April 2023 patch, 4.0 cancels long-running cursors that impede GC.
- Per collection, `db.coll.stats()` reports:
  - `MVCCIdStats.MVCCIdScale`: keep it below 0.3.
  - `gcRuntimeStats`: two months of history for runs longer than 5 minutes.
  - `documentFragmentStats` (5.0.1 and later).
  - `unusedStorageSize`.

  `LongestActiveGCRuntime` shows the longest GC run in progress.
- Bloat: `unusedStorageSize` (collections) and `$indexStats` (indexes) show space that new writes can reuse but that is not returned to storage. `reIndex` (5.0 and later; per the index page not for text, geospatial, vector, or partial indexes) rebuilds an index in the background. The garbage-collection, index-management and supported-APIs pages have no collection-level compaction command (`compact` appears on none of them).
- Bulk deletes create a burst of dead versions. Prefer dropping time-partitioned collections to a mass `deleteMany`, and spread large deletes out over time.

## Sources

- Amazon DocumentDB: how it works, https://docs.aws.amazon.com/documentdb/latest/devguide/how-it-works.html, checked 2026-11-27
- Amazon DocumentDB failover, https://docs.aws.amazon.com/documentdb/latest/devguide/failover.html, checked 2026-11-27
- Maintaining Amazon DocumentDB, https://docs.aws.amazon.com/documentdb/latest/devguide/db-instance-maintain.html, checked 2026-11-27
- Overview of Amazon DocumentDB global clusters, https://docs.aws.amazon.com/documentdb/latest/devguide/global-clusters.html, checked 2026-11-27
- Global clusters disaster recovery, https://docs.aws.amazon.com/documentdb/latest/devguide/global-clusters-disaster-recovery.html, checked 2026-11-27
- Backing up and restoring in Amazon DocumentDB, https://docs.aws.amazon.com/documentdb/latest/devguide/backup_restore.html, checked 2026-11-27
- Comparing automatic and manual snapshots, https://docs.aws.amazon.com/documentdb/latest/devguide/backup_restore-compare_automatic_manual_snapshots.html, checked 2026-11-27
- Restoring to a point in time, https://docs.aws.amazon.com/documentdb/latest/devguide/backup_restore-point_in_time_recovery.html, checked 2026-11-27
- Using change streams with Amazon DocumentDB, https://docs.aws.amazon.com/documentdb/latest/devguide/change_streams.html, checked 2026-11-27
- Stopping and starting a cluster, https://docs.aws.amazon.com/documentdb/latest/devguide/db-cluster-stop-start.html, checked 2026-11-27
- Cluster parameters reference, https://docs.aws.amazon.com/documentdb/latest/devguide/cluster_parameter_groups-list_of_parameters.html, checked 2026-11-27
- Encrypting data in transit, https://docs.aws.amazon.com/documentdb/latest/devguide/security.encryption.ssl.html, checked 2026-11-27
- Encrypting Amazon DocumentDB data at rest, https://docs.aws.amazon.com/documentdb/latest/devguide/encryption-at-rest.html, checked 2026-11-27
- Authentication using IAM identity, https://docs.aws.amazon.com/documentdb/latest/devguide/iam-identity-auth.html, checked 2026-11-27
- Database access using Role-Based Access Control, https://docs.aws.amazon.com/documentdb/latest/devguide/role_based_access_control.html, checked 2026-11-27
- Auditing Amazon DocumentDB events, https://docs.aws.amazon.com/documentdb/latest/devguide/event-auditing.html, checked 2026-11-27
- Profiling Amazon DocumentDB operations, https://docs.aws.amazon.com/documentdb/latest/devguide/profiling.html, checked 2026-11-27
- Monitoring with Performance Insights, https://docs.aws.amazon.com/documentdb/latest/devguide/performance-insights.html, checked 2026-11-27
- CloudWatch Database Insights, https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Database-Insights.html, checked 2026-11-27
- Monitoring Amazon DocumentDB with CloudWatch, https://docs.aws.amazon.com/documentdb/latest/devguide/cloud_watch.html, checked 2026-11-27
- Troubleshooting performance and resource utilization, https://docs.aws.amazon.com/documentdb/latest/devguide/user_diagnostics.html, checked 2026-11-27
- Garbage collection in Amazon DocumentDB, https://docs.aws.amazon.com/documentdb/latest/devguide/garbage-collection.html, checked 2026-11-27
- Amazon DocumentDB quotas, https://docs.aws.amazon.com/documentdb/latest/devguide/limits.html, checked 2026-11-27
- Requirements and limitations for DocumentDB serverless, https://docs.aws.amazon.com/documentdb/latest/developerguide/docdb-serverless-limitations.html, checked 2026-11-27
- Managing Amazon DocumentDB indexes, https://docs.aws.amazon.com/documentdb/latest/devguide/managing-indexes.html, checked 2026-11-27
- Amazon DocumentDB elastic clusters: how it works, https://docs.aws.amazon.com/documentdb/latest/devguide/elastic-how-it-works.html, checked 2026-11-27
- Amazon DocumentDB features and configurations, https://docs.aws.amazon.com/documentdb/latest/devguide/docdb-engine-version-supportability.html, checked 2026-11-27
