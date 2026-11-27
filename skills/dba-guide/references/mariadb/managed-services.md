# MariaDB Managed Services

Checked: 2026-11-27 (sources at the end). Amazon RDS for MariaDB is the main hyperscaler offering covered here.

## Offerings

| Offering | Status on 2026-11-27 | Notes |
| --- | --- | --- |
| Amazon RDS for MariaDB | Available: 10.6 (until 2026-12-31), 10.11, 11.4, 11.8, 12.3 | Community engine with RDS restrictions |
| Amazon Aurora | No MariaDB edition | Aurora is MySQL- or PostgreSQL-compatible only. Moving MariaDB to Aurora MySQL is a migration to MySQL, with the incompatibilities in [replication](replication-and-ha.md#replicating-between-mysql-and-mariadb) |
| Azure Database for MariaDB | Retired | Retirement date 2025-09-19 (Microsoft lifecycle page lists 2025-09-20 06:59:59, i.e. end of 19 September US time); migration target was Azure Database for MySQL Flexible Server (MySQL, not MariaDB) |
| MariaDB plc / other providers | Not reviewed here | Check the provider's version list and restrictions before applying this reference |

## Amazon RDS for MariaDB

### Versions and Lifecycle

| Major | RDS release | RDS end of standard support | Minor versions offered (2026-11-27) |
| --- | --- | --- | --- |
| 12.3 | 2026-08-07 | June 2029 | 12.3.2, 12.3.3 (12.3.1 in the Database Preview environment) |
| 11.8 | 2025-08-25 | June 2028 | 11.8.3-11.8.9 (selected patches) |
| 11.4 | 2024-10-15 | May 2029 | 11.4.4-11.4.13 (selected patches) |
| 10.11 | 2023-08-21 | February 2028 | 10.11.10-10.11.19 (selected patches) |
| 10.6 | 2022-02-03 | 2026-12-31 | 10.6.20-10.6.28 (selected patches) |
| 10.5 | 2021-01-21 | 2026-08-31 (passed) | listed 10.5.27-10.5.29 |

- RDS commits to new majors within 3 months of the first community patch release, and minors within 30 days.
- Each minor version has its own end of standard support. Auto minor version upgrade moves instances forward in the maintenance window.
- RDS Extended Support (paid support past end of standard support) is offered for RDS for MySQL and RDS for PostgreSQL only; MariaDB instances on 10.6 must be upgraded before 2026-12-31.
- Rolling releases (13.0, 13.1) are not offered.
- The RDS calendar's "community release dates" for 11.4 (2024-08-08) and 11.8 (2025-08-06) differ from the Foundation GA dates (2024-05-29, 2025-06-04); use the Foundation dates for community lifecycle and the RDS dates for RDS support.

```sh
aws rds describe-db-engine-versions --engine mariadb --query '*[].EngineVersion' --output text
aws rds describe-db-major-engine-versions --engine mariadb
aws rds describe-db-engine-versions --engine mariadb --engine-version 11.8.9 \
  --query 'DBEngineVersions[0].ValidUpgradeTarget[].EngineVersion'
```

### What RDS Takes Over

- Host, OS, storage, minor patching, automated backups and snapshots, point-in-time restore, Multi-AZ failover, read replica creation, monitoring integration.
- Configuration through DB parameter groups (and option groups for plugins). There is no shell or file access.

### What RDS Removes or Restricts

From the RDS feature-support and users-and-privileges pages:

- No `SUPER`. The master user gets `ALTER, ALTER ROUTINE, CREATE, CREATE ROUTINE, CREATE TEMPORARY TABLES, CREATE USER, CREATE VIEW, DELETE, DROP, EVENT, EXECUTE, GRANT OPTION, INDEX, INSERT, LOCK TABLES, PROCESS, REFERENCES, RELOAD, REPLICATION CLIENT, REPLICATION SLAVE, SELECT, SHOW CREATE ROUTINE (11.4+), SHOW DATABASES, SHOW VIEW, TRIGGER, UPDATE`. `RELOAD` does not allow `FLUSH LOGS` or `FLUSH TABLES WITH READ LOCK`.
- Kill sessions with `CALL mysql.rds_kill(<id>)`, `mysql.rds_kill_query(<id>)`, `mysql.rds_kill_query_id(<query_id>)`; plain `KILL` is restricted.
- Reserved accounts: `rdsadmin` (cannot be changed), `rdsrepladmin` (cannot be dropped at any host from 12.3), `rdsproxyadmin` (12.3+, created when the instance becomes an RDS Proxy target).
- Not supported: Galera Cluster; multi-source replication; `unix_socket` and GSSAPI authentication; native MariaDB data-at-rest encryption for InnoDB and Aria and table/tablespace encryption (use RDS storage encryption); AWS KMS and Hashicorp key management plugins; S3, Spider, Sphinx, TokuDB, ColumnStore storage engines; HandlerSocket; `simple_password_check`/`cracklib_password_check` before 11.4; delayed replication and JSON table type before 10.6; the InnoDB-based binary log (`binlog_storage_engine`) on 12.3; global `PATH` on 12.3 (session only); `show_slave_auth_info` on 12.3; running two upgrades in parallel.
- Parameter defaults can differ from community: from RDS 11.8.3, `require_secure_transport=1`.

### Backups, PITR, Failover

- Automated backups plus binlogs give point-in-time restore to a new instance within the retention period. Restore always creates a new instance; plan endpoint changes.
- RDS fixed a community regression that broke PITR (MDEV-35528) by reverting two changes in RDS 10.6.20, 10.11.10, 11.4.4 (and 10.5.27). On self-managed servers of the same community versions, test PITR rather than assuming it works.
- Binlog retention for external replicas or CDC tools: `CALL mysql.rds_set_configuration('binlog retention hours', 24); CALL mysql.rds_show_configuration;` The default is NULL (binlogs removed as soon as RDS no longer needs them). The RDS procedure page states a 168-hour maximum for MySQL only. For MariaDB, set the value you need and read it back with `CALL mysql.rds_show_configuration;` before a CDC tool depends on it.
- Read replicas: up to 15 per source in a Region, cascading replicas supported, automated backups must be enabled on the source (retention > 0). Size replicas like the source. Promote a replica to make it a standalone writable instance (one-way). Delayed replication is supported for MariaDB 10.6 and higher, configured with `CALL mysql.rds_set_configuration('target delay', <seconds>);` before creating the replica, or on an existing replica `CALL mysql.rds_stop_replication; CALL mysql.rds_set_source_delay(3600); CALL mysql.rds_start_replication;`. For recovery, stop replication with `mysql.rds_stop_replication` before the bad change arrives, then promote. The RDS MariaDB delayed-replication page gives no maximum delay and no roll-forward-to-position procedure; check the procedure reference for your version before planning on one.
- Multi-AZ DB instance deployments fail over to a standby by DNS change; applications must reconnect and retry. Multi-AZ DB clusters (readable standbys) are not available for RDS for MariaDB (Multi-AZ DB cluster Regions and engines page).
- RDS Proxy can target RDS for MariaDB (the reserved `rdsproxyadmin` account exists for it on 12.3).

### Upgrades and Maintenance

- Minor upgrades: automatic in the maintenance window if auto minor version upgrade is on, or manual with `modify-db-instance --engine-version`.
- Major upgrades: `aws rds modify-db-instance --db-instance-identifier mydb --engine-version 11.8.9 --allow-major-version-upgrade --apply-immediately` (or in the window). Only the targets in `ValidUpgradeTarget` are allowed; some jumps need an intermediate major. The instance is unavailable during the upgrade; take a manual snapshot first. Rehearse on a snapshot restore. Blue/green deployments reduce downtime and are supported for RDS for MariaDB 12.3, 11.8, 11.4 and 10.x from 10.2 (blue/green Regions and engines page).
- Before a major upgrade, apply the same checks as self-hosted ([versions](versions/index.md#upgrade-paths)): removed parameters in the custom parameter group, reserved words, `innodb_snapshot_isolation` behavior when going to 11.8+, collation defaults.
- Rollback after a major upgrade is a restore from the pre-upgrade snapshot (data written afterwards is lost) or a logical copy.

### Diagnostics That Replace Self-Hosted Ones

| Self-hosted | On RDS |
| --- | --- |
| Error, slow, general logs on disk | Download via console/API, or publish to CloudWatch Logs: `aws rds modify-db-instance --cloudwatch-logs-export-configuration '{"EnableLogTypes":["error","slowquery"]}'` (types `audit`, `error`, `general`, `slowquery`). The slow log needs `slow_query_log=1` or `log_slow_query=1` and the general log `general_log=1` in a custom parameter group. |
| `KILL` | `mysql.rds_kill`, `mysql.rds_kill_query` |
| `SHOW ENGINE INNODB STATUS`, `SHOW PROCESSLIST`, `information_schema`, `sys` | Available (master user has `PROCESS`) |
| Performance Schema | Enable through the `performance_schema` parameter (static, reboot) |
| OS metrics (`iostat`, `top`) | CloudWatch metrics and Enhanced Monitoring |
| Audit plugin config in `my.cnf` | Custom option group with the `MARIADB_AUDIT_PLUGIN` option |
| Replication via `CHANGE MASTER` | `mysql.rds_*` replication procedures for external sources/targets (MySQL-oriented docs; confirm MariaDB support per procedure) |

## Sources

- Amazon RDS, MariaDB on Amazon RDS versions (calendar, minor versions, PITR revert note, 11.8.3 `require_secure_transport`): https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/MariaDB.Concepts.VersionMgmt.html, checked 2026-11-27
- Amazon RDS, MariaDB feature support (unsupported features): https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/MariaDB.Concepts.FeatureNonSupport.html, checked 2026-11-27
- Amazon RDS, MariaDB users and privileges (master user privileges, reserved users, `rds_kill`): https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/MariaDB.Concepts.UsersAndPrivileges.html, checked 2026-11-27
- Amazon RDS Extended Support versions (MySQL and PostgreSQL only): https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/extended-support-versions.html, checked 2026-11-27
- Amazon RDS, `mysql.rds_set_configuration`: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/mysql_rds_set_configuration.html, checked 2026-11-27
- Amazon RDS, MariaDB read replicas: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_MariaDB.Replication.ReadReplicas.html, checked 2026-11-27
- Amazon Aurora overview (MySQL- and PostgreSQL-compatible only): https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/CHAP_AuroraOverview.html, checked 2026-11-27
- Microsoft lifecycle, Azure Database for MariaDB: https://learn.microsoft.com/en-us/lifecycle/products/azure-database-for-mariadb, checked 2026-11-27
- MariaDB Foundation maintenance policy (community GA dates): https://mariadb.org/about/#maintenance-policy, checked 2026-11-27
