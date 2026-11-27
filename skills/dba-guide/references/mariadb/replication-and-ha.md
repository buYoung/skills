# MariaDB Replication and High Availability

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)).

Contents:

- [Choosing a Topology](#choosing-a-topology)
- [Binary Log Basics](#binary-log-basics)
- [MariaDB GTID](#mariadb-gtid)
- [Setting Up a Replica](#setting-up-a-replica)
- [Parallel Replication](#parallel-replication)
- [Semi-Synchronous Replication](#semi-synchronous-replication)
- [Lag and Health](#lag-and-health)
- [Failover and Switchover](#failover-and-switchover)
- [Multi-Source Replication](#multi-source-replication)
- [Galera Cluster](#galera-cluster)
- [InnoDB-Based Binary Log (12.3 and Later)](#innodb-based-binary-log-123-and-later)
- [Replicating Between MySQL and MariaDB](#replicating-between-mysql-and-mariadb)
- [Mixed-Version Replication](#mixed-version-replication)

MariaDB replication shares the binlog and relay-log design with MySQL, but its GTID implementation, parallel apply, semi-sync and Galera integration differ. MySQL GTID advice (`gtid_mode`, `enforce_gtid_consistency`, UUID-based sets, `gtid_executed`) does not apply.

## Choosing a Topology

| Need | Choice | Cost and conditions |
| --- | --- | --- |
| Read scaling, backups off the primary, DR copy | Asynchronous replication with GTID | Replicas lag; failover can lose the last transactions |
| Reduce failover data loss without a cluster | Semi-synchronous replication, `AFTER_SYNC` | Commit latency adds one network round trip; falls back to async after `rpl_semi_sync_master_timeout` |
| Automatic failover with no committed-data loss inside one site, multi-writer capable | Galera Cluster (3+ nodes) | InnoDB only, primary keys required, write latency bound by the slowest node and network RTT, certification conflicts on hot rows, cluster-wide DDL pauses |
| Managed HA | RDS Multi-AZ (see [managed services](managed-services.md)) | No Galera on RDS; failover via DNS |
| Consolidating several primaries into one reporting server | Multi-source replication | One `gtid_domain_id` per source; not available on RDS |

Failover orchestration (choosing and promoting a replica, moving clients) is not built into the server; it needs an external tool or a proxy. Decide which one before you need it, and rehearse it.

## Binary Log Basics

| Variable | Default (images) | Recommendation |
| --- | --- | --- |
| `log_bin` | `OFF` | Enable on every server that may become a primary or that feeds PITR: `log_bin=/var/lib/mysql-binlog/mariadb-bin` |
| `server_id` | 1 | Unique per server, including replicas and Galera nodes |
| `binlog_format` | `MIXED` compiled default on all versions; `ROW` on the 12.3.3 and 13.0.2 images, set by the Galera package's `60-galera.cnf` | Use `ROW` (required by Galera; safest for replication). Set it explicitly. |
| `binlog_row_image` | `FULL` | `FULL_NODUP` (11.4+) saves space while keeping full before-images; `MINIMAL` only if every replica table has the same primary key and columns |
| `binlog_annotate_row_events` | `ON` | Keep: row events carry the original statement for diagnosis |
| `sync_binlog` | 0 | 1 on primaries that must not lose committed transactions on OS crash (with `innodb_flush_log_at_trx_commit=1`). Not needed with the InnoDB-based binlog. |
| `binlog_expire_logs_seconds` / `expire_logs_days` | 0 compiled default; images set `expire_logs_days=10` (864000 s) | Longer than the longest replica outage and your PITR window. Aliases of each other. |
| `max_binlog_total_size` (`binlog_space_limit`) | 0 (off) | 11.4+: cap binlog disk use; combine with `slave_connections_needed_for_purge` |
| `log_slave_updates` | `OFF` | `ON` on replicas that may be promoted or that feed other replicas |
| `binlog_checksum` | `CRC32` | Keep |

```sql
SHOW BINARY LOGS;                 -- needs log_bin; ERROR 1381 "You are not using binary logging" otherwise
SHOW BINLOG STATUS;               -- current file/position (also SHOW MASTER STATUS)
SHOW BINLOG EVENTS IN 'mariadb-bin.000042' LIMIT 20;
SELECT @@gtid_binlog_pos, @@gtid_current_pos, @@gtid_slave_pos;
```

```sh
mariadb-binlog --base64-output=decode-rows -vv mariadb-bin.000042 | less
mariadb-binlog --start-position=0-1-1000 --stop-position=0-1-2000 mariadb-bin.000042   # GTID range (10.8+)
```

## MariaDB GTID

Format: `domain_id-server_id-sequence_no`, for example `0-1-10`. The domain is a 32-bit replication stream id, the server id is where the event group was first binlogged, and the sequence number increases per event group. A position is a list with one GTID per domain: `0-1-100,1-20-55`.

| Variable | Meaning |
| --- | --- |
| `gtid_binlog_pos` | Last GTID written to this server's binlog, per domain |
| `gtid_slave_pos` | Last GTID applied by the replica threads, per domain (stored in `mysql.gtid_slave_pos`) |
| `gtid_current_pos` | Union of the two: last GTID executed here as primary or replica |
| `gtid_domain_id` | Domain for new GTIDs written by this server (default 0) |
| `gtid_strict_mode` | `OFF` by default. `ON` makes the server reject out-of-order or duplicate GTIDs within a domain and refuse a replica connect at a GTID missing from the primary's binlog |
| `gtid_ignore_duplicates` | Multi-source: apply only one copy of the same GTID arriving via different paths |
| `gtid_pos_auto_engines` | Create per-engine `gtid_slave_pos` tables to avoid cross-engine transactions |

Decisions:

- Use `MASTER_USE_GTID=slave_pos` (the default for `CHANGE MASTER` from 10.10 when the primary supports GTID). `current_pos` is not recommended: a local write on the replica that is binlogged becomes the start position and breaks replication.
- Turn on `gtid_strict_mode=ON` on all servers of a topology. It turns silent divergence (errant transactions) into immediate errors you can act on.
- Keep a single domain (0) for single-primary topologies. Give each independent writer its own `gtid_domain_id` (multi-source, multi-primary rings, writes made on a replica on purpose).
- Prevent local writes on replicas: `read_only=ON` (users with `READ_ONLY ADMIN` still write; 10.11 separated it from `SUPER`), and run maintenance with `SET SESSION sql_log_bin=0` when it must not replicate.
- `mysql.gtid_slave_pos` must be InnoDB for crash safety. Never edit it; set positions with `SET GLOBAL gtid_slave_pos='0-1-1'` while replica threads are stopped.

Read-your-writes on a replica: capture `@@last_gtid` after the commit on the primary, then on the replica run `SELECT MASTER_GTID_WAIT('0-1-12345', 2);` (returns 0 when applied, -1 on timeout).

## Setting Up a Replica

1. On the primary, create the replication user:

   ```sql
   CREATE USER 'repl'@'10.0.0.%' IDENTIFIED BY '...';
   GRANT REPLICATION SLAVE ON *.* TO 'repl'@'10.0.0.%';
   ```

2. Seed the replica from a physical backup (`mariadb-backup`, see [backup](backup-and-recovery.md)). The prepared backup records the GTID position in `mariadb_backup_binlog_info` (`xtrabackup_binlog_info` before 11.1).
3. On the replica:

   ```sql
   SET GLOBAL gtid_slave_pos = '0-1-123456';          -- from the backup info file
   CHANGE MASTER TO
     MASTER_HOST='10.0.0.10', MASTER_USER='repl', MASTER_PASSWORD='...',
     MASTER_USE_GTID=slave_pos, MASTER_SSL=1;
   START SLAVE;                                        -- START REPLICA also works
   SHOW REPLICA STATUS\G
   ```

   From 11.4, replication connections verify the primary's certificate by default (`MASTER_SSL_VERIFY_SERVER_CERT`). Provide `MASTER_SSL_CA` or the replica fails to connect to a primary with an unverifiable certificate.
4. Verify: `Slave_IO_Running: Yes`, `Slave_SQL_Running: Yes`, `Using_Gtid: Slave_Pos`, `Gtid_IO_Pos` advancing, `Seconds_Behind_Master` falling to 0.

Switching an existing file/position replica to GTID: `STOP SLAVE; CHANGE MASTER TO MASTER_USE_GTID=slave_pos; START SLAVE;` (the replica already tracks `gtid_slave_pos`).

## Parallel Replication

Defaults: `slave_parallel_threads=0` (single-threaded apply), `slave_parallel_mode=optimistic` (images).

- Enable on replicas that lag on write-heavy primaries: `STOP SLAVE SQL_THREAD; SET GLOBAL slave_parallel_threads=8; START SLAVE SQL_THREAD;` (alias `slave_parallel_workers`). Persist in the option file.
- `optimistic` applies transactions in parallel and retries on conflicts (`slave_transaction_retries=10`); commit order is preserved. `conservative` parallelizes only what group-committed together on the primary; raise `binlog_commit_wait_count`/`binlog_commit_wait_usec` on the primary to create larger groups at some latency cost. `aggressive` is for tests.
- Different GTID domains apply independently and out of order relative to each other.
- Verify: `SHOW ALL REPLICAS STATUS` or `information_schema.SLAVE_STATUS` (11.6+); lag falls; `Slave_retried_transactions` grows slowly, not explosively.

## Semi-Synchronous Replication

Built into the server (no plugin install).

```ini
# primary
rpl_semi_sync_master_enabled=ON
rpl_semi_sync_master_wait_point=AFTER_SYNC      # default AFTER_COMMIT
rpl_semi_sync_master_timeout=10000              # ms, default
# replica
rpl_semi_sync_slave_enabled=ON
```

- `AFTER_SYNC` waits for a replica acknowledgement before the commit becomes visible, so failover to an acknowledging replica is lossless. A crashed old primary may recover prepared transactions the replicas never saw; restart it with `--init-rpl-role=SLAVE` before rejoining (protection against truncating needed transactions applies from 10.6.19, 10.11.9, 11.4.3).
- `AFTER_COMMIT` (default) lets other clients see the commit before the acknowledgement; failover may lose data.
- On timeout the primary reverts to asynchronous replication (`Rpl_semi_sync_master_status=OFF`, error log `Semi-sync replication switched OFF`) and resumes when a replica catches up. Alert on `Rpl_semi_sync_master_no_times` increasing.
- Changing `rpl_semi_sync_slave_enabled` on a running replica needs `STOP SLAVE IO_THREAD; START SLAVE IO_THREAD;`.
- With the InnoDB-based binlog, semi-sync works only from 13.2 and only with `AFTER_COMMIT`.

## Lag and Health

```sql
SHOW REPLICA STATUS\G            -- or SHOW SLAVE STATUS; SHOW ALL REPLICAS STATUS for multi-source
SELECT * FROM information_schema.SLAVE_STATUS\G     -- 11.6+
```

Read:

- `Slave_IO_Running` / `Slave_SQL_Running`, `Last_IO_Error`, `Last_SQL_Error`, `Last_SQL_Errno`.
- `Gtid_IO_Pos` (received) vs `gtid_slave_pos` (applied): a gap with the I/O thread running means apply lag; no gap but lag means the network or primary is slow to deliver.
- `Seconds_Behind_Master`: its definition changed in 11.6 (so in 11.8) and three timing columns were added to `SHOW ALL REPLICAS STATUS`. Compare graphs across an upgrade with that in mind. For an exact check, compare `@@gtid_binlog_pos` on the primary with `@@gtid_slave_pos` on the replica, or write a heartbeat row.
- Long queries on a replica can block replication (metadata locks); `slave_abort_blocking_timeout` (11.7+, so 11.8) aborts them after a delay.

Common SQL-thread errors: 1062 (duplicate key) or 1032 (row not found) mean divergence. Do not skip with `sql_slave_skip_counter` as a routine fix; find the cause (writes on the replica, non-deterministic statements, non-transactional tables), then re-seed the replica if data differ. Compare tables with `CHECKSUM TABLE t;` on both sides at the same GTID before declaring it fixed.

## Failover and Switchover

Planned switchover (GTID, async or semi-sync):

1. Pick the most advanced replica: highest `gtid_slave_pos` per domain.
2. Stop writes on the primary: `SET GLOBAL read_only=ON;` and wait until each replica's `gtid_slave_pos` equals the primary's `gtid_binlog_pos` (`SELECT MASTER_GTID_WAIT('<pos>', 30);`).
3. On the new primary: `STOP SLAVE; RESET SLAVE ALL; SET GLOBAL read_only=OFF;`.
4. On the old primary and other replicas: `CHANGE MASTER TO MASTER_HOST='new-primary', MASTER_USE_GTID=slave_pos; START SLAVE;`. For an old primary that has its own binlogged transactions, use `CHANGE MASTER TO ..., MASTER_DEMOTE_TO_SLAVE=1` (10.10+), which moves its binlog position into `gtid_slave_pos`.
5. Move clients (proxy, DNS, VIP). Verify writes land only on the new primary.

Unplanned failover: same steps, but the old primary may hold transactions no replica received. With `gtid_strict_mode=ON`, rejoining it fails visibly instead of diverging silently. Compare its `gtid_binlog_pos` with the new primary; extract the missing transactions with `mariadb-binlog` if they must be kept, then rebuild it from a backup of the new primary.

Delayed replica for human-error recovery: `CHANGE MASTER TO MASTER_DELAY=3600;` keeps a replica an hour behind; stop it, then roll it forward with `START SLAVE UNTIL master_gtid_pos='...'` to just before the bad statement (`SQL_BEFORE_GTIDS`/`SQL_AFTER_GTIDS` forms from 11.3).

## Multi-Source Replication

```sql
CHANGE MASTER 'sales' TO MASTER_HOST='10.0.1.10', MASTER_USER='repl', MASTER_PASSWORD='...', MASTER_USE_GTID=slave_pos;
CHANGE MASTER 'billing' TO MASTER_HOST='10.0.2.10', MASTER_USER='repl', MASTER_PASSWORD='...', MASTER_USE_GTID=slave_pos;
START ALL SLAVES;
SHOW ALL REPLICAS STATUS\G
SET @@default_master_connection='sales'; SHOW REPLICA STATUS\G
```

- Each source must use a distinct `gtid_domain_id`, or positions collide.
- 10.7+ also accepts MySQL-style `FOR CHANNEL 'name'`.
- Not supported on RDS for MariaDB.

## Galera Cluster

Mechanism as far as it drives decisions: each commit is certified cluster-wide; conflicting concurrent writes to the same rows on different nodes fail at commit on one node (the client sees a deadlock-type error and must retry); DDL runs in Total Order Isolation by default, pausing the cluster for its duration.

Hard requirements and limits (Galera known-limitations page):

- InnoDB only; writes to other engines, including direct writes to `mysql.*` tables, are not replicated (account DDL such as `CREATE USER` is). `FLUSH PRIVILEGES` is not replicated.
- All tables need a primary key; `DELETE` on tables without one is unsupported.
- `binlog_format=ROW`; do not change it at runtime.
- `innodb_autoinc_lock_mode=2` (required by Galera per the InnoDB variable docs); `AUTO_INCREMENT` values have gaps (`wsrep_auto_increment_control=ON` by default). Installing the Galera package changes `binlog_format` and `innodb_autoinc_lock_mode` on a non-Galera server too (see [12.3](versions/12.3.md#changed-defaults)).
- No `LOCK TABLES`, `GET_LOCK()`, or `FLUSH TABLES t WITH READ LOCK`; `FLUSH TABLES WITH READ LOCK` (global) works.
- Transactions are limited by `wsrep_max_ws_rows` and `wsrep_max_ws_size` (2 GiB default per the limitations page; images show `wsrep_max_ws_size=2147483647`); large transactions use a lot of memory. Batch bulk changes.
- Cluster throughput is bounded by the slowest node.
- Reads are not causal by default: set `wsrep_sync_wait` (session) for read-after-write consistency on another node. Read-modify-write patterns need `SELECT ... FOR UPDATE`.
- Query logs must use `log_output=FILE`; Windows is not supported; flashback is not supported; gcache is not encrypted.
- From 12.3.2, Galera is no longer a dependency of the server packages; install `mariadb-server-galera` (Debian/Ubuntu) or `MariaDB-server-galera` (RHEL/SLES) explicitly. It depends on the provider library `galera-4`. The Galera upgrade guide says Galera is still in the MariaDB repositories, while the 12.3.1 notes say it is no longer included; if the package manager cannot find `galera-4`, obtain it separately. The InnoDB-based binlog cannot be used on Galera.

Minimal configuration (per node):

```ini
[galera]
wsrep_on=ON
wsrep_provider=/usr/lib/galera/libgalera_smm.so      # path in the official image
wsrep_cluster_name=prod-cluster
wsrep_cluster_address=gcomm://10.0.0.11,10.0.0.12,10.0.0.13
wsrep_node_address=10.0.0.11
wsrep_sst_method=mariabackup                        # image default is rsync
binlog_format=ROW
innodb_autoinc_lock_mode=2
default_storage_engine=InnoDB
```

The images default to `wsrep_sst_method=rsync`. With rsync SST the donor is blocked with a read lock during the transfer; the `mariadb-backup` SST method is non-blocking, so the donor keeps serving queries (Introduction to State Snapshot Transfers page). rsync needs no SST user; `mariadb-backup` needs `wsrep_sst_auth` before Community 11.6.

Health checks:

```sql
SHOW GLOBAL STATUS WHERE Variable_name IN
 ('wsrep_cluster_size','wsrep_cluster_status','wsrep_local_state_comment','wsrep_ready','wsrep_connected',
  'wsrep_flow_control_paused','wsrep_local_recv_queue_avg','wsrep_local_send_queue_avg',
  'wsrep_local_cert_failures','wsrep_local_bf_aborts','wsrep_last_committed');
```

| Signal | Healthy | Action when not |
| --- | --- | --- |
| `wsrep_cluster_status` | `PRIMARY` | `NON_PRIMARY` means quorum lost: the node refuses queries (`WSREP has not yet prepared node for application use`). Restore quorum; bootstrap only the most advanced node (highest `wsrep_last_committed`) as a last resort. |
| `wsrep_cluster_size` | expected node count | A node left; check its error log and SST state |
| `wsrep_ready` / `wsrep_connected` | `ON` | Do not route traffic to the node |
| `wsrep_flow_control_paused` | near 0 | A slow node throttles the cluster; find the node with high `wsrep_local_recv_queue_avg` |
| `wsrep_local_send_queue_avg` | near 0 | Network throughput problem |
| `wsrep_local_cert_failures`, `wsrep_local_bf_aborts` | low, flat | Hot-row conflicts from multi-node writes: write to one node per data set |

Operational rules:

- Write to a single node unless the application is designed for certification conflicts and retries.
- Run an odd number of voting members across failure domains so a single failure keeps quorum; a Galera Arbitrator (`garbd`) on a third machine counts as a voting member but stores no data and serves no clients, so two data nodes plus `garbd` keep quorum when one data node fails. Monitor `garbd`: if it fails, the two-node cluster loses automatic failover (Galera deployment variants page).
- Long DDL: TOI pauses the cluster; for backward-compatible changes apply it node by node with `SET SESSION wsrep_OSU_method='RSU'`.
- Size gcache so a restarted node can use IST instead of a full SST: `gcache.size` = peak write-set rate (bytes/s) x the longest node outage to absorb. The IST and GCache page's example is about 20 KB/s x 2 hours = about 140 MiB. Nodes that keep requesting SST mean the cache is too small. Set it in `wsrep_provider_options` (for example `gcache.size=2G`).
- 12.3 adds parallel async replication between two Galera clusters (`slave_parallel_threads`) and write-set apply retries (`wsrep_applier_retry_count`).

## InnoDB-Based Binary Log (12.3 and Later)

Enable with a bare `log_bin` and `binlog_storage_engine=innodb` (restart required). Binlog files become `binlog-NNNNNN.ibb` InnoDB-page files, pre-allocated to `max_binlog_size`, recovered with InnoDB, with no `.index` or GTID index files. Commit durability is controlled only by `innodb_flush_log_at_trx_commit`; `sync_binlog` is ignored, and the two-phase commit between binlog and InnoDB disappears.

Use it when: GTID replication only, no Galera, no tools reading binlog files directly, and commit latency or fsync load matters. `mariadb-backup` then includes binlog files consistently, and a restored backup can start replicating with `CHANGE MASTER TO ..., MASTER_DEMOTE_TO_SLAVE=1`.

Not available: file/offset positions, `MASTER_POS_WAIT()` (use `MASTER_GTID_WAIT()`), `BINLOG_GTID_POS()`, `RESET MASTER TO`, binlog encryption (`encrypt_binlog`), replication of `XA PREPARE`, savepoints inside triggers, `--init-rpl-role`, semi-sync before 13.2, Galera, Amazon RDS.

Migration (old binlog files become unusable; the formats are exclusive):

1. Standalone: stop, change `log-bin=name` to bare `log-bin`, add `binlog-storage-engine=innodb`, start (binlog starts empty), delete old binlog files after the next full backup.
2. Keep GTID state for connected replicas: stop writes, let replicas catch up, save `@@gtid_binlog_state`, restart with the new format, run `SET GLOBAL gtid_binlog_state='<saved>'` immediately.
3. Zero downtime: switch a 12.3+ replica to the new format, let it accumulate binlog, promote it, then convert the others one at a time.

All replicas must run 12.3 or later before the primary switches. PITR from old-format binlogs ends at the switch; take a full backup right after.

## Replicating Between MySQL and MariaDB

- MariaDB can replicate from a MySQL primary using file/position replication; MySQL cannot replicate from a MariaDB primary. GTID formats are incompatible, so hybrid setups use positions, not GTIDs.
- Standard binlog events are generally compatible, but check:
  - MySQL 8 default collation `utf8mb4_0900_ai_ci`: MariaDB 11.4.5+ includes alias collations for MySQL names.
  - MySQL's binary JSON columns: MariaDB stores JSON as text; the compatibility page advises text columns or statement-based replication for MySQL 5.7 sources. The compatibility matrix says JSON SQL functions are compatible but storage differs, and it does not describe row events from MySQL 8 binary JSON. Before relying on row-based replication of JSON columns, replicate a sample table and compare `JSON_EXTRACT` results on both sides.
  - Authentication of the replication user: MySQL 8.4 defaults to `caching_sha2_password`; MariaDB added a `caching_sha2_password` plugin in 12.3 (not loaded by default in the 12.3.3 and 13.0.2 images; `INSTALL SONAME 'auth_mysql_sha2'`). The pages checked do not say whether an older MariaDB replica can authenticate to a MySQL source with it. Before the migration, point the replica at a test MySQL source with the real replication account and check `Slave_IO_Running` and `Last_IO_Error` in `SHOW SLAVE STATUS`; otherwise create the replication user with a plugin both sides support.
- Replication from MySQL is the low-downtime migration path: seed MariaDB with a logical dump that records the binlog position (`mysqldump --single-transaction --source-data=2` on MySQL 8.x), load it, `CHANGE MASTER TO MASTER_LOG_FILE=..., MASTER_LOG_POS=...`, let it catch up, compare data, then cut over. In-place upgrade covers MySQL data files from releases before 8.0 only.

## Mixed-Version Replication

- Supported: older primary → newer replica, any newer version. Upgrade replicas first.
- Not supported: newer primary → older replica. Nothing enforces this; it fails late at the SQL or schema level (new collations, new syntax, `utf8` meaning `utf8mb4` from 13.1). Keep the period of a newer primary with older replicas at zero.
- Character-set defaults changed in 11.5/11.6; an 11.8+ primary replicating to 10.6-era replicas needs explicit `character_set_server`/`collation_server` settings as described in the character-set docs.
