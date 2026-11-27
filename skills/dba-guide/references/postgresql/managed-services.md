# Managed PostgreSQL: Amazon RDS and Aurora

Checked: 2026-11-27 against AWS documentation and release calendars for Amazon RDS for PostgreSQL and Aurora PostgreSQL-Compatible (sources in [versions/index.md](versions/index.md#sources)).

## Deployment options

| Option | Storage | Replication | Failover |
| --- | --- | --- | --- |
| RDS Single-AZ instance | instance-attached volume | read replicas optional (asynchronous) | no standby; automatic failover to another AZ needs a Multi-AZ deployment. Recovery is a restore or a replica promotion |
| RDS Multi-AZ instance | primary plus a standby in another AZ that cannot serve reads (Multi-AZ DB instance page) | managed by RDS | automatic to the standby |
| RDS Multi-AZ DB cluster | one writer and two readable readers in three AZs | semisynchronous: commit needs acknowledgment from at least one reader | automatic to the reader with the lowest lag, after it applies its backlog |
| Aurora PostgreSQL cluster | shared cluster volume, six copies across three AZs, independent of instance count | readers (up to 15) use the shared volume; replication to readers is asynchronous | promotes a reader by priority tier (0 highest to 15), then largest size; without readers, recovers the writer host |

Aurora cluster volumes grow automatically and shrink when data is dropped or truncated. Aurora PostgreSQL keeps temporary table data and temp files on instance-local storage, limited by instance class. Storage configurations: Aurora Standard (pay per I/O) or I/O-Optimized (no I/O charges; AWS says it can reduce cost when I/O is 25% or more of spend). You can switch to I/O-Optimized once every 30 days; switching on NVMe-based instances restarts the engine.

## What the service takes over and what it restricts

Taken over: OS and binaries, patching in maintenance windows, automated backups and PITR, storage, replica and Multi-AZ setup, failover.

Restricted:

- No real superuser. The master user (default name `postgres`) is created as `LOGIN NOSUPERUSER INHERIT CREATEDB CREATEROLE NOREPLICATION` and is a member of `rds_superuser`. `rds_superuser` can create extensions from the supported list, create roles and databases, grant `rds_superuser`, `rds_replication`, and `rds_password`, see all sessions in `pg_stat_activity`, and cancel or terminate any session.
- Internal roles you cannot change or drop: `rdsadmin`, `rdstopmgr`, `rds_reserved`. `rds_password` manages passwords; from 14 it cannot change passwords of `rds_superuser` members.
- No host access: you cannot edit `pg_hba.conf` or `postgresql.conf`, reach the data directory, or run OS-level tools (`pg_checksums`, `pg_controldata`, `pg_rewind`, `pg_upgrade`) against the instance. Server-side file access and physical `pg_basebackup` of the instance are therefore unavailable (inference from the absence of superuser and host access).
- Settings come from DB parameter groups (DB cluster parameter groups for Aurora and Multi-AZ DB clusters). Static parameters need a reboot. Check effective values with `SHOW` and `pg_settings`.
- Extensions: only those AWS supports for the engine version. Most extensions are not upgraded by an engine upgrade; run `ALTER EXTENSION ... UPDATE` afterwards. RDS 18 removed `plrust`.

## Version availability and Extended Support

| | RDS for PostgreSQL | Aurora PostgreSQL |
| --- | --- | --- |
| New major available | within 30 days of community `<major>.1` | within 8 months of community `<major>.1` |
| New minor available | within 7 days of community release | within 3 months; generally quarterly |
| Long-term minors | — | Aurora LTS minors (14.6, 15.10, 16.8, 17.7) supported to the major's end of standard support |
| Version numbers | community `major.minor`; Extended Support builds such as `13.23-rds.20260819` | `aurora_version()` returns `major.minor.patch`; from 13.3, 12.8, 11.13 the first two parts match community `major.minor` |
| 19 on 2026-11-27 | not available | not available |

End of standard support and Extended Support:

| Major | Community EOL | End of standard support | Extended Support year 1 pricing from | Year 3 pricing from | End of Extended Support |
| --- | --- | --- | --- | --- | --- |
| 18 | 2030-11-14 | 2031-02-28 | 2031-03-01 | 2033-03-01 | 2034-02-28 |
| 17 | 2029-11-08 | 2030-02-28 | 2030-03-01 | 2032-03-01 | 2033-02-28 |
| 16 | 2028-11-09 | 2029-02-28 | 2029-03-01 | 2031-03-01 | 2032-02-29 (RDS) / 2032-02-28 (Aurora) |
| 15 | 2027-11-11 | 2028-02-29 | 2028-03-01 | 2030-03-01 | 2031-02-28 |
| 14 | 2026-11-12 | 2027-02-28 | 2027-03-01 | 2029-03-01 | 2030-02-28 |
| 13 | 2025-11-13 | 2026-02-28 | 2026-03-01 | 2028-03-01 | 2029-02-28 |

Extended Support rules:

- Paid; available up to 3 years past end of standard support; provides fixes for critical and high CVEs and critical bugs, plus support cases.
- Enrollment is controlled by the `EngineLifecycleSupport` setting at create or restore time, or by modifying an existing instance or cluster (cluster level for Aurora and Multi-AZ DB clusters); the change takes effect immediately without downtime.
- If enrolled, an instance past end of standard support stays on its version and is charged. Disabling enrollment on an instance already past the date upgrades it automatically to the next supported major. After Extended Support ends, AWS upgrades the major automatically.
- Individual minors reach end of standard support before the major; RDS marks some minors `NO_CREATE` (no new instances).
- AWS documents viewing support dates per engine version through the CLI and RDS API (see "Viewing support dates for engine versions" in the RDS User Guide; exact command not re-checked).

Engine version and upgrade targets from outside the database:

```bash
aws rds describe-db-instances --db-instance-identifier mydb \
  --query 'DBInstances[0].[Engine,EngineVersion]'
aws rds describe-db-engine-versions --engine postgres --engine-version 16.14 \
  --query "DBEngineVersions[*].ValidUpgradeTarget[*].{EngineVersion:EngineVersion}" --output text
aws rds describe-db-engine-versions --engine aurora-postgresql --engine-version 16.8 \
  --query 'DBEngineVersions[].ValidUpgradeTarget[?IsMajorVersionUpgrade == `true`].{EngineVersion:EngineVersion}' --output text
```

Valid targets depend on the source minor: on the 2026-11-27 RDS table, a recent source minor (for example 16.15) can only go to equally recent target minors (17.11, 18.6). Upgrade the minor first when the target you want is not listed.

## Major version upgrades

Both services run pg_upgrade for you; you cannot choose its mode. Major upgrades are never applied automatically, except at the end of Extended Support or when you un-enroll past the standard-support date.

Prechecks to run yourself (both services refuse or fail otherwise):

```sql
SELECT count(*) FROM pg_catalog.pg_prepared_xacts;                  -- must be 0
SELECT datname FROM pg_database WHERE datconnlimit = -2;            -- invalid databases: drop them
SELECT slot_name, slot_type, active FROM pg_replication_slots;      -- logical slots: see below
SELECT count(*) FROM pg_largeobject_metadata;                       -- millions of large objects need memory
SELECT extname, extversion FROM pg_extension;                       -- unsupported on target: drop; PostGIS family: update first
SELECT datname, datistemplate FROM pg_database;                     -- Aurora: template0 and template1 must exist as templates
```

Also remove user-table columns of `reg*` types other than `regclass`/`regtype`, and `aclitem` columns when the target is 16 or later (AWS publishes detection queries). AWS recommends at least 32 GB of instance memory for 25 to 30 million large objects.

Logical replication slots:

| Source version | RDS | Aurora |
| --- | --- | --- |
| 14, 15, 16 | upgrade blocked while logical slots exist; drop them and re-create CDC afterwards | same |
| 17+ | slots on non-replica instances are retained; slots on read replicas are not; all changes must be consumed first or the upgrade fails | retained; disable subscriptions, consume all changes, set `rds.logical_replication = 1` in the target cluster parameter group; a slot with unconsumed changes fails the upgrade after the cluster went offline and the cluster returns to the source version |

Behavior during and after:

- RDS upgrades in-Region read replicas with the primary (not Multi-AZ DB cluster read replicas, whose replication becomes terminated). Promote or delete replicas you do not want upgraded; a replica that fails the upgrade must be recreated.
- RDS takes snapshots before and after the upgrade when backup retention is greater than 0. Aurora takes a `preupgrade-...` cluster snapshot and clones the volume to roll back a failed upgrade; rolling back a successful upgrade means restoring that snapshot to a new cluster.
- No PITR during the upgrade; afterwards PITR works to times before the upgrade began and after the post-upgrade backup completed. Aurora cannot restore a snapshot to a previous minor version.
- Precheck failures go to `pg_upgrade_precheck.log` (RDS); pg_upgrade's `pg_upgrade_internal.log` and `pg_upgrade_server.log` are available on both. Publish logs to CloudWatch Logs to keep them.
- Aurora readers have a brief outage each while they are upgraded after the writer.
- Aurora global database: all clusters upgrade together; reset `rds.global_db_rpo` before the upgrade.
- AWS instructs running `ANALYZE` in every database afterwards, saying optimizer statistics are not transferred. Community pg_upgrade into 18+ transfers them; on RDS and Aurora run `ANALYZE` anyway.
- Rehearse on a snapshot restore or PITR copy (RDS) or a clone (Aurora), and compare plans. Aurora's Query Plan Management extension (`apg_plan_mgmt`) can keep plans stable across a major upgrade.
- Lower-downtime alternatives (Blue/Green deployments, logical replication to a new-version instance) are not covered here; read the current AWS limitations before choosing one.

## Minor upgrades and maintenance

- Minor upgrades are applied in the maintenance window when automatic minor version upgrade is enabled, or when you apply them. They incur downtime: a Multi-AZ DB instance upgrades primary and standby together and can be unavailable for several minutes; a Multi-AZ DB cluster upgrades readers first and fails over, typically about 35 seconds. RDS also applies a minor upgrade without the option for critical security issues or end of support (RDS PostgreSQL upgrade pages). Upgrade read replicas before the source.
- RDS Proxy can reduce minor-upgrade downtime for Multi-AZ DB clusters to one second or less (AWS).
- Track per-minor end-of-support and `NO_CREATE` status on the release calendar.

## Failover and high availability

- Aurora: failover to a reader typically completes in under 60 seconds and often under 30 (AWS). Without readers, the writer host is recovered in the same AZ, typically in under 10 minutes. Connect writers through the cluster endpoint and readers through the reader endpoint; clients must reconnect and retry after failover. Set reader priorities deliberately and place readers in at least two other AZs. Modifying a priority does not trigger failover.
- RDS Multi-AZ DB cluster: failover time depends on the lowest replica lag of the two readers; monitor CloudWatch `ReplicaLag`. A flow-control extension throttles writer commits when reader lag exceeds `flow_control.target_standby_apply_lag` (default two minutes); it shows as `Extension` waits and in `get_flow_control_stats()`. Disable it by removing it from `shared_preload_libraries` and rebooting.
- RDS Proxy keeps client connections during failover and bypasses DNS caching (AWS cites up to 66% shorter failover for Aurora Multi-AZ).
- You cannot run your own failover manager against RDS or Aurora instances.

## Backups and PITR

- Automated backups within the retention period. RDS uploads transaction logs to S3 every five minutes, so the latest restorable time trails the present by up to about five minutes; read `LatestRestorableTime` from `aws rds describe-db-instances`.
- PITR creates a new instance or cluster; the source is not modified. Restored RDS instances get default parameter and option groups unless you specify others. Their volumes load data blocks from S3 in the background, so performance is reduced until initialization completes.
- Aurora restore to a point in time creates a new DB cluster. With the CLI or API you must then create the writer yourself with `aws rds create-db-instance --db-cluster-identifier <restored-cluster> ...`; the console creates it for you (Aurora PITR page).
- `pg_dump` from a client still works and is the way to move data out of the service or across platforms.
- Test restores the same way as self-hosted: restore to a new instance, run checks, record the duration.

## Replication and logical decoding

- Read replicas (RDS) and Aurora readers are managed; you do not configure `primary_conninfo` or physical slots for them.
- Logical replication and CDC need `rds.logical_replication = 1` in the parameter group (static on RDS for PostgreSQL: reboot after setting it, together with `wal_level`, `max_wal_senders`, `max_replication_slots`; RDS logical replication page). The `rds_replication` role lets non-`rds_superuser` users manage replication.
- Abandoned logical slots retain WAL and consume storage; monitor `pg_replication_slots` as on self-hosted servers.
- Aurora global database replicates asynchronously to secondary Regions for disaster recovery and local reads.

## Diagnostics that replace self-hosted ones

| Self-hosted | Managed replacement |
| --- | --- |
| OS tools (`top`, `iostat`, `vmstat`) | CloudWatch metrics; Enhanced Monitoring for OS and process metrics (agent on the instance, delivered to the `RDSOSMetrics` log group) |
| Log files on disk | console/CLI log download; publish PostgreSQL and upgrade logs to CloudWatch Logs |
| Wait-event sampling scripts | Performance Insights / CloudWatch Database Insights (DB load by wait event and SQL) |
| `pg_controldata`, `pg_waldump`, file-level checks | not available |
| Replication lag queries | still work in SQL on RDS replicas; plus CloudWatch `ReplicaLag` |

SQL-level diagnostics in the other files (`pg_stat_activity`, `pg_stat_statements` when added to `shared_preload_libraries` in the parameter group, `pg_locks`, `pg_stat_io`, `EXPLAIN`) work the same, within `rds_superuser` limits.
