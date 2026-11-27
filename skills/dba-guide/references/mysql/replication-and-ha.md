# MySQL Replication and High Availability

Checked: 2026-11-27. Applies to MySQL 8.0 through 26.10. Statement names below are the 8.4+ forms; 8.0.22+ accepts them too. The `MASTER`/`SLAVE` forms are syntax errors from 8.4 (container: `SHOW MASTER STATUS` -> ERROR 1064 on 8.4-26.10).

Contents: [Choosing a topology](#choosing-a-topology) · [Binary log settings](#binary-log-settings) · [GTIDs](#gtids) · [Setting up a replica](#setting-up-a-replica) · [Monitoring replication](#monitoring-replication) · [Parallel apply](#parallel-apply) · [Semisynchronous replication](#semisynchronous-replication) · [Group Replication and InnoDB Cluster](#group-replication-and-innodb-cluster) · [Failover](#failover) · [Sharding](#sharding)

## Choosing a Topology

| Need | Option | Data loss on primary failure | Automatic failover |
|---|---|---|---|
| Read scaling, backups off the primary, DR copy | Asynchronous replication | Transactions not yet received by the replica | No (external tooling or manual) |
| Bound loss to zero received-but-unapplied | Semisynchronous replication (`AFTER_SYNC`) | None acknowledged, unless the wait times out and falls back to async | No |
| Automatic primary election in one region | Group Replication, usually through InnoDB Cluster (MySQL Shell AdminAPI + MySQL Router) | None for a majority-certified commit | Yes, while a majority is reachable |
| Cross-region DR for an InnoDB Cluster | InnoDB ClusterSet (asynchronous between clusters) | Async lag | Manual or scripted region switch |
| Managed | RDS Multi-AZ, Aurora | see [managed-services.md](managed-services.md) | Yes |

Group Replication needs 3 or more members to tolerate one failure (a majority must remain), InnoDB tables with primary keys, row-based logging, and GTIDs. Writes in a single-primary group pay one network round trip for certification. Members across regions add that latency to every commit.

## Binary Log Settings

Defaults in all five containers: `log_bin=ON`, `binlog_format=ROW`, `sync_binlog=1`, `binlog_row_image=FULL`, `binlog_expire_logs_seconds=2592000` (30 days), `log_replica_updates=ON`, `server_id=1`.

- Keep `binlog_format=ROW`. `STATEMENT` and `MIXED` are needed only for legacy cases; READ COMMITTED and `innodb_autoinc_lock_mode=2` require row-based logging for safety.
- `binlog_row_image=MINIMAL` reduces binlog size for wide tables but removes the before-image columns that change-data-capture tools and some recovery procedures need. Keep `FULL` unless volume forces it.
- `binlog_transaction_compression=ON` (zstd) cuts binlog and network volume at CPU cost; replicas and `mysqlbinlog` decompress transparently.
- Retention: set `binlog_expire_logs_seconds` longer than the oldest point you may need for point-in-time recovery plus the longest replica outage you tolerate.
- Every server in a topology needs a unique `server_id`. The default `1` collides as soon as you add a replica.

Inspect:

```sql
SHOW BINARY LOGS;
SHOW BINARY LOG STATUS;      -- 8.2+; 8.0 uses SHOW MASTER STATUS
SHOW BINLOG EVENTS IN 'binlog.000002' FROM 4 LIMIT 20;
```

```bash
mysqlbinlog --verbose --base64-output=DECODE-ROWS binlog.000002 | less
```

## GTIDs

GTID format `server_uuid:N` (and from 8.4 `server_uuid:tag:N`). With GTIDs, a replica knows which transactions it has (`gtid_executed`) and finds its position on any source automatically (`SOURCE_AUTO_POSITION=1`). Use GTIDs for every new topology.

Defaults: `gtid_mode=OFF` in 8.0 and 8.4, `ON` from 9.5.0 (containers: OFF on 8.0.46/8.4.13, ON on 9.7.4/26.x). Set it explicitly in the option file on every server.

`enforce_gtid_consistency=ON` rejects statements that cannot be logged as a single GTID transaction, such as updates of transactional and non-transactional tables in one transaction.

Enable GTIDs on a running 8.0/8.4 topology without downtime. Do each step on every server before the next step:

```sql
SET PERSIST enforce_gtid_consistency = WARN;   -- run the workload; fix anything that logs warnings
SET PERSIST enforce_gtid_consistency = ON;
SET PERSIST gtid_mode = OFF_PERMISSIVE;
SET PERSIST gtid_mode = ON_PERMISSIVE;
-- wait until every server shows 0 here:
SHOW GLOBAL STATUS LIKE 'Ongoing_anonymous_transaction_count';
-- and every replica has applied all anonymous transactions, then:
SET PERSIST gtid_mode = ON;
-- on each replica
STOP REPLICA; CHANGE REPLICATION SOURCE TO SOURCE_AUTO_POSITION = 1; START REPLICA;
```

Container check (8.4.13, single server without replicas): every `SET PERSIST` step succeeded in this order, `Ongoing_anonymous_transaction_count` was 0, and the server ended with `gtid_mode=ON`, `enforce_gtid_consistency=ON`.

Rollback while still in a `*_PERMISSIVE` state: step back one state at a time in reverse order.

Errant transactions: a write applied directly on a replica gets the replica's UUID. If that replica is promoted, other replicas try to fetch that GTID and fail when it is already purged. Check before any promotion:

```sql
-- on the candidate, with the old primary's set pasted in
SELECT GTID_SUBTRACT(@@GLOBAL.gtid_executed, '<primary gtid_executed>') AS errant;
```

Keep replicas `super_read_only=ON` to prevent this.

## Setting Up a Replica

Fastest path for a new replica of an existing InnoDB server: the clone plugin (8.0.17+). The recipient's data is replaced.

```sql
-- donor
INSTALL PLUGIN clone SONAME 'mysql_clone.so';
CREATE USER 'clone'@'10.0.0.%' IDENTIFIED BY '...';
GRANT BACKUP_ADMIN ON *.* TO 'clone'@'10.0.0.%';
-- recipient (empty or disposable), same series, OS and platform
INSTALL PLUGIN clone SONAME 'mysql_clone.so';
SET GLOBAL clone_valid_donor_list = 'db1:3306';
CLONE INSTANCE FROM 'clone'@'db1':3306 IDENTIFIED BY '...';   -- replaces all data, restarts
-- after restart
CHANGE REPLICATION SOURCE TO SOURCE_HOST='db1', SOURCE_USER='repl', SOURCE_PASSWORD='...',
  SOURCE_AUTO_POSITION=1, SOURCE_SSL=1;
START REPLICA;
```

Clone requirements: same server series (patch releases may differ from 8.4; from 26.7, LTS to next LTS is allowed), same OS and platform, same character set, `innodb_page_size` and `innodb_data_file_path`, `max_allowed_packet` >= 2 MB on both (the default is 67108864 on all five images), the recipient needs `CLONE_ADMIN`, only InnoDB data is copied, and automatic restart needs a supervisor (systemd or the container entrypoint); otherwise you get ERROR 3707 and must start the server yourself.

Alternatives: a MySQL Shell dump and load (logical, slower, works across versions), or a physical backup tool.

Replication user:

```sql
CREATE USER 'repl'@'10.0.0.%' IDENTIFIED BY '...' REQUIRE SSL;
GRANT REPLICATION SLAVE ON *.* TO 'repl'@'10.0.0.%';
```

The privilege name is still `REPLICATION SLAVE` (RDS 8.4+ docs and the 8.4 privilege list use it). With `caching_sha2_password`, the replica must use TLS (`SOURCE_SSL=1`) or fetch the server's RSA key (`GET_SOURCE_PUBLIC_KEY=1`). From 9.5.0 `SOURCE_SSL` defaults to 1.

## Monitoring Replication

```sql
SHOW REPLICA STATUS\G
```

Fields to read:

| Field | Healthy | If not |
|---|---|---|
| `Replica_IO_Running` | Yes | `Connecting`: network, credentials, TLS; read `Last_IO_Error`. |
| `Replica_SQL_Running` | Yes | No: apply error in `Last_SQL_Error`; details per worker in `performance_schema.replication_applier_status_by_worker`. |
| `Seconds_Behind_Source` | small, stable | Compares the event's original timestamp with the replica clock. It is 0 when the I/O thread is behind but the applier is idle, and NULL when the SQL thread is stopped. |
| `Retrieved_Gtid_Set` vs `Executed_Gtid_Set` | converging | The gap is the backlog in relay logs. |
| `Source_Log_File` / `Read_Source_Log_Pos` vs `Relay_Source_Log_File` / `Exec_Source_Log_Pos` | close | Distinguishes network lag from apply lag. |

Better lag measures (8.0+):

```sql
SELECT CHANNEL_NAME, WORKER_ID, LAST_APPLIED_TRANSACTION,
       TIMESTAMPDIFF(MICROSECOND, LAST_APPLIED_TRANSACTION_ORIGINAL_COMMIT_TIMESTAMP,
                     LAST_APPLIED_TRANSACTION_END_APPLY_TIMESTAMP)/1e6 AS lag_s,
       LAST_ERROR_NUMBER, LAST_ERROR_MESSAGE
  FROM performance_schema.replication_applier_status_by_worker;
SELECT * FROM performance_schema.replication_connection_status\G
```

On the source: `SHOW REPLICAS` (lists replicas that set `report_host`), and `SHOW PROCESSLIST` for `Binlog Dump GTID` threads.

Common apply errors and safe handling:

- 1062 duplicate key / 1032 row not found: the replica's data has diverged. Do not skip blindly. Find the cause (writes on the replica, a non-deterministic statement, a restore at the wrong position). With GTIDs, skip one known transaction by committing an empty one:
  ```sql
  STOP REPLICA;
  SET GTID_NEXT = 'uuid:12345'; BEGIN; COMMIT; SET GTID_NEXT = 'AUTOMATIC';
  START REPLICA;
  ```
  then verify the table against the source. Rebuild the replica if divergence is broad.
- Lag from a single huge transaction: wait, or rebuild; splitting future batches is the fix.
- Lag on tables without primary keys: add primary keys.

## Parallel Apply

Defaults (8.0.27+, all containers): `replica_parallel_workers=4`, `replica_preserve_commit_order=ON`. From 8.4 the source always records writeset-based dependencies; `binlog_transaction_dependency_tracking` is gone. From 9.3.0 the minimum worker count is 1.

- Raise `replica_parallel_workers` (for example 8-16) when `replication_applier_status_by_worker` shows all workers busy and lag grows. More workers do not help a workload that serialises on the same rows.
- Keep `replica_preserve_commit_order=ON` so replicas never expose a commit order the source never had.
- 26.7+ offers the Change Stream Applier per channel (`APPLIER_VERSION = 2`); see [26.10](versions/26.10.md#worth-adopting) for its requirements.

## Semisynchronous Replication

The source waits after the binlog sync for at least `rpl_semi_sync_source_wait_for_replica_count` replicas to acknowledge receipt (not apply). Use the `semisync_source` and `semisync_replica` plugins; the `semisync_master`/`semisync_slave` plugin names were removed in 9.5.0.

```sql
-- source
INSTALL PLUGIN rpl_semi_sync_source SONAME 'semisync_source.so';
SET PERSIST rpl_semi_sync_source_enabled = ON, rpl_semi_sync_source_timeout = 10000;
-- replica
INSTALL PLUGIN rpl_semi_sync_replica SONAME 'semisync_replica.so';
SET PERSIST rpl_semi_sync_replica_enabled = ON;
STOP REPLICA IO_THREAD; START REPLICA IO_THREAD;
```

If no acknowledgment arrives within `rpl_semi_sync_source_timeout` ms, the source silently continues asynchronously. Monitor `Rpl_semi_sync_source_status` and `Rpl_semi_sync_source_no_tx`. Semisync without automated failover only narrows the loss window.

## Group Replication and InnoDB Cluster

Deploy with MySQL Shell's AdminAPI rather than by hand:

```js
// mysqlsh, connected to the first instance
dba.configureInstance('admin@db1:3306')
var c = dba.createCluster('prod')
c.addInstance('admin@db2:3306', {recoveryMethod: 'clone'})
c.addInstance('admin@db3:3306', {recoveryMethod: 'clone'})
c.status()
```

Then bootstrap MySQL Router (`mysqlrouter --bootstrap admin@db1:3306`) so applications connect to Router's read-write and read-only ports instead of to members.

Defaults that matter:

| Variable | 8.0 | 8.4+ | Effect |
|---|---|---|---|
| `group_replication_consistency` | EVENTUAL | BEFORE_ON_PRIMARY_FAILOVER (container) | A newly elected primary holds new transactions until it has applied its backlog. Use `AFTER` or `BEFORE` per session for read-your-writes on secondaries, at a latency cost. |
| `group_replication_exit_state_action` | READ_ONLY | OFFLINE_MODE | Expelled members disconnect clients. |
| `group_replication_communication_stack` | XCOM | XCOM until 9.7; MYSQL from 26.7 | |

Health checks:

```sql
SELECT MEMBER_HOST, MEMBER_STATE, MEMBER_ROLE, MEMBER_VERSION
  FROM performance_schema.replication_group_members;
SELECT MEMBER_ID, COUNT_TRANSACTIONS_IN_QUEUE, COUNT_TRANSACTIONS_REMOTE_IN_APPLIER_QUEUE
  FROM performance_schema.replication_group_member_stats;
```

Pitfalls: large transactions can exceed `group_replication_transaction_size_limit` and roll back; multi-primary mode produces certification conflicts on hot rows; a two-member group cannot survive the loss of either member; DDL and DML on the same objects from different members conflict in multi-primary mode.

## Failover

Asynchronous topologies have no built-in automatic failover. A controlled switchover:

1. On the old primary: `SET PERSIST super_read_only = ON;` (blocks writes, including from accounts with `SUPER`-level privileges).
2. Wait until the candidate's `Executed_Gtid_Set` contains the old primary's `gtid_executed`:
   ```sql
   SELECT WAIT_FOR_EXECUTED_GTID_SET('<old primary gtid_executed>', 60);  -- 0 = done
   ```
3. On the candidate: `STOP REPLICA; RESET REPLICA ALL; SET PERSIST super_read_only = OFF, read_only = OFF;`
4. Repoint other replicas: `CHANGE REPLICATION SOURCE TO SOURCE_HOST='db2', SOURCE_AUTO_POSITION=1; START REPLICA;`
5. Make the old primary a replica of the new one, then move client traffic (DNS, proxy, or Router).

Unplanned failover: choose the replica with the largest `Executed_Gtid_Set`, check it for errant GTIDs, accept that transactions not received are lost (unless semisync acknowledged them), and keep the failed primary from accepting writes when it returns (fence it).

Replicas can fail over between sources themselves with asynchronous connection failover (`SOURCE_CONNECTION_AUTO_FAILOVER=1` plus `asynchronous_connection_failover_add_source()`, 8.0.22+). In 8.4 the default `SOURCE_RETRY_COUNT` is 10, so a replica stops retrying a dead source after about 10 minutes.

## Sharding

MySQL has no built-in sharding for InnoDB. Options: application-level sharding by a key with a directory table; partitioning within one server for retention (see [schema-and-indexes.md](schema-and-indexes.md#partitioning)); NDB Cluster for a different storage engine with automatic sharding (out of scope here). Choose a shard key that every hot query includes, and plan cross-shard queries and resharding before choosing.

## Sources

Checked 2026-11-27: MySQL 8.4 What Is New (removed replication statements, `binlog_transaction_dependency_tracking`, GR defaults, `SOURCE_RETRY_COUNT`); Changes in MySQL 9.3.0 and 9.5.0 (worker minimum, GTID and replication TLS defaults, semisync plugin removal); 26.7 What Is New and 26.7.0 notes (CSA, communication stack default); MySQL 8.4 manual, Cloning Remote Data (https://dev.mysql.com/doc/refman/8.4/en/clone-plugin-remote.html); RDS replication procedures page for the `REPLICATION SLAVE` privilege and `SOURCE_SSL=1` with `caching_sha2_password`; statement runs on the official images (binary log defaults, `SHOW BINARY LOG STATUS`, `SHOW REPLICAS`, GR consistency default). GTID online-enable steps, `SHOW REPLICA STATUS` fields and Performance Schema replication tables follow the MySQL 8.4 manual Replication chapter (https://dev.mysql.com/doc/refman/8.4/en/replication.html).
