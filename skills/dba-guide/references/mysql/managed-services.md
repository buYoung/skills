# Managed MySQL: Amazon RDS for MySQL and Amazon Aurora MySQL

Checked: 2026-11-27 against the AWS documentation listed under Sources.

Contents: [What the service takes over](#what-the-service-takes-over) · [Restrictions](#restrictions) · [RDS stored procedures](#rds-stored-procedures-replacing-admin-statements) · [High availability and failover](#high-availability-and-failover) · [Backups and PITR](#backups-pitr-backtrack-and-cloning) · [Upgrades and maintenance](#upgrades-and-maintenance) · [Version availability](#version-availability-and-extended-support) · [Diagnostics](#diagnostics-that-replace-self-hosted-ones)

## What the Service Takes Over

| Area | RDS for MySQL | Aurora MySQL |
|---|---|---|
| Storage | EBS volumes per instance; you size and grow them | Shared cluster volume copied across three AZs (six storage nodes); grows automatically, up to 256 TiB on supported versions |
| Replication for HA | Multi-AZ DB instance (one non-readable standby) or Multi-AZ DB cluster (two readable standbys, semisynchronous) | Storage-level replication; up to 15 Aurora Replicas read the same volume |
| Backups | Automated snapshots plus transaction logs, PITR | Continuous backup of the cluster volume, PITR, Backtrack, cloning |
| Patching | Minor upgrades in the maintenance window if enabled | Same |
| Configuration | DB parameter groups (and option groups) | DB cluster and DB instance parameter groups |

You keep: schema and index design, query tuning, connection management, capacity choices, privilege design, and upgrade testing.

## Restrictions

- No OS or file system access: no `my.cnf`, no data directory, no `mysqld` startup flags. Configure through parameter groups. `PERSIST_RO_VARIABLES_ADMIN` is disallowed on every RDS for MySQL version (dynamic privileges page), so read-only variables cannot be persisted. For a dynamic variable, check the master user's grants with `SHOW GRANTS` before relying on `SET PERSIST`, and make lasting changes in the parameter group.
- No `SUPER`. The RDS for MySQL master user (8.0.36 and higher, 8.4, 9.7) gets a fixed list of static privileges plus `rds_superuser_role`. The published list does not include `SUPER`, `FILE` or `SHUTDOWN`. Before 8.0.36 there is no role. The master user name cannot be changed; restore lost master privileges by setting a new master password.
- Administrative statements that need `SUPER`-level privileges (`KILL` of another account's thread, `CHANGE REPLICATION SOURCE TO`, binlog retention) are replaced by stored procedures (next section).
- Plugins and components: only those the service offers through option groups or parameters.
- Binary log retention is controlled by `mysql.rds_set_configuration`, not `binlog_expire_logs_seconds`.
- Authentication on RDS for MySQL: 8.0.34 and later 8.0 versions use `mysql_native_password` as the default plugin, and `default_authentication_plugin` cannot be changed. 8.4 defaults to `caching_sha2_password` but keeps `mysql_native_password` working (community 8.4 ships it disabled); change the default through `authentication_policy` in a custom parameter group. 9.7 does not support `mysql_native_password`, and accounts that still use it block the 8.4 to 9.7 upgrade; find them with `SELECT user, host FROM mysql.user WHERE plugin = 'mysql_native_password';` and convert them first.
- Aurora MySQL 8.4 keeps `mysql_native_password` enabled and the setting cannot be changed (community 8.4 disables it). Fast insert is not available in Aurora 8.4. From Aurora 8.4.7, automatic histogram updates are disabled and `AUTO UPDATE` is treated as `MANUAL UPDATE`.
- Aurora MySQL 8.4 sets `require_secure_transport` to `ON` by default and supports only TLS 1.2 and 1.3 (v3 to 8.4 comparison page). The page does not say whether a cluster upgraded from version 3 gets the same value; check `require_secure_transport` in the cluster parameter group after the upgrade.

## RDS Stored Procedures Replacing Admin Statements

The master user runs these (for 8.4+ the docs say "the administrative user").

| Task | Self-hosted | RDS for MySQL |
|---|---|---|
| Kill a session / a query | `KILL id` / `KILL QUERY id` | `CALL mysql.rds_kill(id);` / `CALL mysql.rds_kill_query(id);` |
| Binlog retention | `binlog_expire_logs_seconds` | `CALL mysql.rds_set_configuration('binlog retention hours', 24);` (default NULL = binlogs not retained; maximum 168) |
| Show settings | | `CALL mysql.rds_show_configuration;` |
| Delayed replica | `CHANGE REPLICATION SOURCE TO SOURCE_DELAY=n` | `CALL mysql.rds_set_configuration('source delay', 3600);` (limit 86400 s on that page) or `CALL mysql.rds_set_source_delay(3600);` (8.4+; its page states up to 259200 s) |
| Replicate from an external MySQL | `CHANGE REPLICATION SOURCE TO ...` | 8.4+: `CALL mysql.rds_set_external_source_with_auto_position(host, port, user, pwd, ssl, delay);` 8.0: `mysql.rds_set_external_master_with_auto_position(...)` |
| Start/stop replication | `START/STOP REPLICA` | `CALL mysql.rds_start_replication;` / `CALL mysql.rds_stop_replication;` |
| Skip one apply error | empty transaction with `SET GTID_NEXT` | `CALL mysql.rds_skip_repl_error;` (run on the replica) |
| Stop replicating from an external source | `RESET REPLICA ALL` | 8.4+: `CALL mysql.rds_reset_external_source;` 8.0: `mysql.rds_reset_external_master` |

`autocommit` must be 1 for the reset and set-external procedures. With `caching_sha2_password` replication users (default on 8.4+), pass SSL encryption = 1.

## High Availability and Failover

RDS for MySQL:

- Multi-AZ DB instance: one standby in another AZ, not readable. Failover moves the endpoint to the standby.
- Multi-AZ DB cluster: one writer and two readers in three AZs, semisynchronous replication (a commit completes once at least one reader acknowledges it). Readers serve reads. Failover time depends on the readers' replica lag, because a reader applies its backlog before promotion. Flow control (`rpl_semi_sync_master_target_apply_lag`, default 120 s) throttles the writer when readers fall behind; check `SHOW GLOBAL STATUS LIKE '%flow_control%'`. Only specific instance classes are supported (for example `db.r6gd`, `db.m6gd`, `db.r8gd`). AWS recommends a primary key on every table.

Aurora MySQL:

- Failover promotes an Aurora Replica by promotion tier (0 highest to 15 lowest), then by largest size. Service is typically restored in under 60 seconds, often under 30. Without a replica, Aurora recreates the primary, typically in under 10 minutes. After five failed failover attempts, tiers are no longer considered.
- Put at least one replica in a second AZ; if all instances share one AZ, an AZ outage needs manual recovery.
- The cluster endpoint follows the writer. RDS Proxy avoids DNS caching delays (AWS states up to 66% shorter failover for Aurora Multi-AZ).
- Aurora Global Database: one primary Region and up to 10 secondary Regions, storage-level replication typically under a second behind. Switchover (planned) moves the primary with no data loss; failover (unplanned) recovers from a Region outage with a non-zero RPO. Managed switchover/failover require matching engine versions. Backtrack is not supported on global databases.

Durability parameters: Aurora sends redo records to the cluster volume and does not flush log files on the instance. `innodb_flush_log_at_trx_commit` still relaxes durability. On version 3, `0` stops waiting for the volume to confirm the redo write, and `1` or `2` both wait; on version 2, `0` or `2` stop waiting. Version 3 accepts a value other than 1 only after `innodb_trx_commit_allow_data_loss=1`. Any value other than 1 can lose committed transactions on failover or restart; AWS recommends 1 (Aurora MySQL feature recommendations page).

## Backups, PITR, Backtrack, and Cloning

RDS for MySQL:

- Backup retention: 0-35 days for DB instances (0 disables automated backups), 1-35 days for Multi-AZ DB clusters. Default 1 day through API/CLI, 7 days through the console. Changing retention between 0 and non-zero causes an outage.
- Transaction logs are uploaded every five minutes, so `LatestRestorableTime` trails by up to about five minutes.
- PITR creates a new DB instance with the default parameter and option groups unless you name others in the CLI/API call. Attach the right groups and security groups before cutting over.
  ```bash
  aws rds describe-db-instances --db-instance-identifier prod --query 'DBInstances[0].LatestRestorableTime'
  aws rds restore-db-instance-to-point-in-time --source-db-instance-identifier prod \
    --target-db-instance-identifier prod-pitr --restore-time 2026-11-27T09:14:00Z \
    --db-parameter-group-name prod-mysql84
  ```
- Snapshots cover the whole instance. Up to 100 manual snapshots per Region.
- Logical dumps (`mysqldump`, MySQL Shell) still work and are the way to move data out or across versions.

Aurora MySQL:

- Backtrack rewinds the whole cluster in place to an earlier time within the backtrack window (target up to 72 hours). It must be enabled at cluster creation or snapshot restore. It briefly disrupts the instances; stop applications first. Backtracking a cluster with binary logging enabled fails unless forced, and forcing it breaks binlog replicas and blue/green deployments. After an in-place major upgrade you cannot backtrack to before it. It does not replace backups.
- Cloning creates a copy-on-write cluster that shares pages with the source; storage is charged only for pages that diverge. Up to 15 copy-on-write clones per source; the next one is a full copy. Same Region only.
  ```bash
  aws rds restore-db-cluster-to-point-in-time --source-db-cluster-identifier prod \
    --db-cluster-identifier prod-clone --restore-type copy-on-write --use-latest-restorable-time
  aws rds create-db-instance --db-cluster-identifier prod-clone --db-instance-identifier prod-clone-1 \
    --db-instance-class db.r6g.large --engine aurora-mysql
  ```
  Use clones for upgrade rehearsals and restore tests.

## Upgrades and Maintenance

- RDS for MySQL: automatic minor version upgrades (if enabled) run in the maintenance window. Major upgrades never happen automatically. Supported major paths: 5.7 -> 8.0, 8.0 -> 8.4, 8.4 -> 9.7.
- RDS targets new minors within 30 days of the community release and new majors within 6 months of the community `<major>.1` release. Minors usually get about a year of standard support (8.4.13: released 2026-11-17, supported to 2027-11-17), with exceptions; a minor can expire before its major.
- Aurora: majors within 12 months of the community LTS `<major>.1`, minors within 3 months of the community release, an Aurora LTS minor within 12 months of each major; minors are generally quarterly.
- Aurora 8.4 upgrade paths: in-place from version 3, blue/green deployment, snapshot restore, or migration with AWS DMS or Percona XtraBackup. Aurora runs automated prechecks before taking the cluster offline.
- Rehearse every major upgrade on a clone (Aurora) or a restored snapshot (RDS) and run the MySQL Shell upgrade checker against it; managed prechecks do not test application SQL.

## Version Availability and Extended Support

RDS for MySQL (RDS versions page):

| Major | Community release | RDS release | RDS end of standard support | Extended Support year 1 pricing from | Year 3 pricing from | End of Extended Support |
|---|---|---|---|---|---|---|
| 9.7 | 2026-04-21 | 2026-11-18 | 2031-07-31 | 2031-08-01 | 2033-08-01 | 2034-07-31 |
| 8.4 | 2024-04-30 | 2024-11-21 | 2029-07-31 | 2029-08-01 | 2031-08-01 | 2032-07-31 |
| 8.0 | 2018-04-19 | 2018-10-23 | 2026-07-31 | 2026-08-01 | 2028-08-01 | 2029-07-31 |
| 5.7 | 2015-10-21 | 2016-02-22 | 2024-02-29 | 2024-03-01 | 2026-03-01 | 2029-06-30 |

- 8.0 and 5.7 are available only under RDS Extended Support. AWS ships RDS-built patch releases named like `8.0.46-RDS.20260908` (released 2026-09-23, supported to 2027-09-30). Extended Support does not apply to individual minor versions.
- Charges begin the day after the end of standard support, also apply to Multi-AZ standbys, and stop when you upgrade to a version in standard support or delete the database. Rates are on the RDS for MySQL pricing page (not checked here).
- Opt out at creation only through the CLI/API: `--engine-lifecycle-support open-source-rds-extended-support-disabled` (API `EngineLifecycleSupport`). Disabling enrollment on an instance already past standard support upgrades it automatically to the next supported major version: an unplanned major upgrade. Rehearse first.
- At the end of Extended Support (8.0: 2029-07-31; 8.4: 2032-07-31), RDS automatically upgrades any instance still on that major version (Extended Support page). Plan the major upgrade before then.
- Innovation releases are offered only in the RDS Database Preview environment (26.10 at present; endpoint `rds-preview.us-east-2.amazonaws.com`): instances and snapshots are deleted after 60 days, no AWS Support, no snapshot copy to production, no cross-Region replicas or RDS Proxy.

Aurora MySQL (release calendar):

| Major | MySQL compatibility | End of standard support | Extended Support | Latest minor (2026-11-27) |
|---|---|---|---|---|
| 8.4 | 8.4 | April 2032 | to be determined | 8.4.12 (2026-11-20, supported to 2028-05-31); first minor 8.4.7; launched 2026-05-21 |
| version 3 | 8.0 | 2028-04-30 | year 1 from 2028-05-01; ends 2029-07-31 | 3.14 (MySQL 8.0.46, 2026-10-26); LTS 3.10 (to 2028-04-30) |
| version 2 | 5.7 | 2024-10-31 | ends 2029-06-30 (2.11 and 2.12 eligible) | 2.12 |

No Aurora MySQL version compatible with 9.7 or 26.x is listed.

Version strings: Aurora version 3 `8.0.mysql_aurora.3.10.0`; Aurora 8.4 `8.4.mysql_aurora.8.4.7` (no customer-visible patch level). `SELECT AURORA_VERSION()` returns `3.05.2` style or `8.4.7` style.

## Diagnostics That Replace Self-Hosted Ones

| Self-hosted | Managed replacement |
|---|---|
| Reading the error, slow and general log files | Download through the console or `aws rds download-db-log-file-portion`, or publish to CloudWatch Logs with `aws rds modify-db-instance --cloudwatch-logs-export-configuration '{"EnableLogTypes":["error","slowquery"]}'` (log types `audit`, `error`, `general`, `slowquery`; the change applies immediately). The general log needs `general_log=1` in a custom parameter group; the audit log needs the `MARIADB_AUDIT_PLUGIN` option. Enable the slow log in the parameter group (`slow_query_log`, `long_query_time`, `log_output`). |
| `iostat`, `top` on the host | CloudWatch instance metrics; Enhanced Monitoring for OS-level metrics, delivered to the `RDSOSMetrics` CloudWatch Logs group (30-day default retention). |
| `SHOW ENGINE INNODB STATUS`, Performance Schema, `sys` | Same SQL; Performance Schema must be on in the parameter group. |
| `SHOW REPLICA STATUS` for Aurora readers | Aurora Replicas do not use binlog replication; use the CloudWatch metric `AuroraReplicaLag` on each reader (milliseconds), or `AuroraReplicaLagMaximum` on the writer. Binlog replicas of Aurora still use `SHOW REPLICA STATUS`. |
| Disk free | RDS: `FreeStorageSpace` (bytes). Aurora MySQL: `AuroraVolumeBytesLeftTotal` for space left before the volume limit; `VolumeBytesUsed` is the billed size and AWS calls it less reliable for that purpose. |
| Multi-AZ DB cluster semisync lag | `Rpl_semi_sync_master_flow_control_current_delay` (microseconds) and the `semi_sync_flow_control_delay_cond` wait event. |

## Sources

All checked 2026-11-27.

- RDS for MySQL known issues and limitations (default authentication plugin per version, `mysql_native_password` on 8.4 and 9.7): https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/MySQL.KnownIssuesAndLimitations.html — checked 2026-11-27
- MySQL on Amazon RDS versions: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/MySQL.Concepts.VersionMgmt.html (major/minor dates, Extended Support dates, Preview environment, upgrade paths, release targets)
- RDS Extended Support charges: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/extended-support-charges.html (charge start, opt-out, automatic upgrade on disabling enrollment)
- Aurora MySQL release calendars: https://docs.aws.amazon.com/AmazonRDS/latest/AuroraMySQLReleaseNotes/AuroraMySQL.release-calendars.html
- Aurora MySQL version 8.4: https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraMySQL.MySQL84.html
- Aurora MySQL 8.4 announcement (2026-05-21): https://aws.amazon.com/about-aws/whats-new/2026/05/amazon-aurora-mysql/8-4/
- Checking Aurora MySQL version numbers: https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraMySQL.Updates.Versions.html
- Master user account privileges: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.MasterAccounts.html
- RDS MySQL stored procedures: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/mysql-stored-proc-configuring.html, https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/mysql-stored-proc-ending.html, https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/mysql-stored-proc-replicating.html
- Backup retention period: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_WorkingWithAutomatedBackups.BackupRetention.html
- Point-in-time recovery: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PIT.html
- Multi-AZ deployments: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZ.html; Multi-AZ DB cluster concepts: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/multi-az-db-clusters-concepts.html
- Aurora storage: https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.Overview.StorageReliability.html
- Aurora high availability: https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Concepts.AuroraHighAvailability.html
- Aurora Backtrack: https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraMySQL.Managing.Backtrack.html
- Aurora cloning: https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.Managing.Clone.html
- Aurora Global Database: https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-global-database.html
