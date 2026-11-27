# PostgreSQL Versions

Checked: 2026-11-27 against the PostgreSQL versioning policy page (https://www.postgresql.org/support/versioning/).

The community supports each major version for 5 years after its first release, then ships one final minor release and stops. Minor releases come at least every three months and contain only bug, security, and data-corruption fixes; the project recommends always running the current minor of your major. Since version 10 the first number is the major (`17`), the second is the minor (`17.12`).

## Support Status

| Series | Release type | First release (GA) | Current minor (2026-11-27) | End of community support (final release) | Amazon RDS end of standard support | RDS / Aurora Extended Support ends | File |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 19 | Major, 5-year support | 2026-11-19 | 19.0 | 2031-11-19 | Not yet offered on RDS or Aurora | — | [19](19.md) |
| 18 | Major, 5-year support | 2025-09-25 | 18.7 | 2030-11-14 | 2031-02-28 | 2034-02-28 | [18](18.md) |
| 17 | Major, 5-year support | 2024-09-26 | 17.12 | 2029-11-08 | 2030-02-28 | 2033-02-28 | [17](17.md) |
| 16 | Major, 5-year support | 2023-09-14 | 16.16 | 2028-11-09 | 2029-02-28 | RDS 2032-02-29; Aurora 2032-02-28 | [16](16.md) |
| 15 | Major, 5-year support | 2022-10-13 | 15.20 | 2027-11-11 | 2028-02-29 | 2031-02-28 | [15](15.md) |
| 14 | Major, end of life | 2021-09-30 | 14.25 (final) | 2026-11-12 | 2027-02-28 | 2030-02-28 | [14](14.md) |

The community has no LTS or innovation tracks: every major gets the same 5-year window. 14 is listed because it is the most recent series to reach end of life; use it only as an upgrade source. 13 reached end of life on 2025-11-13 and is outside the covered range.

RDS and Aurora dates come from the AWS release calendars (see [managed-services.md](../managed-services.md)). Aurora uses the same end-of-standard-support and Extended Support end dates as RDS for 14 through 18 on the 2026-11-27 calendars, except that the Aurora calendar ends 16's Extended Support on 2032-02-28 and the RDS calendar on 2032-02-29 (see [16](16.md)). RDS and Aurora do not offer 19 yet: RDS states it adds a new major within 30 days of the community `<major>.1` release, Aurora within 8 months of `<major>.1`, and 19.1 had not been released on the check date.

Container evidence: the official `postgres` images for tags 14, 15, 16, 17, 18, 19 reported 14.25, 15.20, 16.16, 17.12, 18.7, and 19.0 on 2026-11-27, matching the versioning page.

## Identify the Running Version

Run these on any server, including RDS and Aurora:

```sql
SELECT version();                 -- full string: version, build, platform
SHOW server_version;              -- e.g. 18.7 (Debian 18.7-1.pgdg13+5)
SHOW server_version_num;          -- 180007; compare numerically in scripts
SELECT current_setting('server_version_num')::int >= 170000 AS is_17_plus;
```

`server_version_num` is `major * 10000 + minor` for 10 and later (`190000` for 19.0, `140025` for 14.25). Use it, not string comparison, in version gates.

Distribution and flavor:

| Question | Command | How to read it |
| --- | --- | --- |
| Packaged build | `SELECT version();` | Debian/PGDG builds show `(Debian 18.7-1.pgdg13+5)`; source builds show only the version. |
| Aurora PostgreSQL | `SELECT aurora_version();` | Function exists only on Aurora. Returns `major.minor.patch`, e.g. `13.3.0`. On Aurora 13.3, 12.8, 11.13 and later, the first two parts match the PostgreSQL version. |
| RDS for PostgreSQL | `SELECT rolname FROM pg_roles WHERE rolname IN ('rds_superuser','rdsadmin');` | Present on RDS and Aurora; absent on self-hosted servers. |
| Managed engine version from outside | `aws rds describe-db-instances --db-instance-identifier <id> --query 'DBInstances[0].[Engine,EngineVersion]'` and `aws rds describe-db-clusters --db-cluster-identifier <id> --query 'DBClusters[0].[Engine,EngineVersion]'` | `Engine` is `postgres` for RDS and `aurora-postgresql` for Aurora. |
| Data checksums | `SHOW data_checksums;` | `on` by default for clusters created by `initdb` 18 or later; `off` by default before 18. pg_upgrade needs the same setting on both sides. |
| Cluster-level facts | `pg_controldata "$PGDATA"` (shell, self-hosted only) | Catalog version, checksum version, WAL segment size; in 19 also the effective WAL level. |

For compatibility gates inside SQL, test for the feature rather than the version where possible (`SELECT 1 FROM pg_settings WHERE name = 'io_method'`).

## Upgrade Paths

Minor upgrades (for example 17.9 to 17.12): stop the server, install the new binaries, start. No dump or pg_upgrade. Read every minor release note in between; some include post-install steps such as reindexing specific index types.

Major upgrades: the data directory format changes, so use one of three methods. You may jump directly across several majors (for example 14 to 18) with any of them, but read the release notes of every major in between.

| Method | Downtime | Rollback | Use when |
| --- | --- | --- | --- |
| `pg_upgrade` (copy, `--clone`, `--copy-file-range`, `--link`, `--swap` in 18+) | Minutes to tens of minutes; link, clone, and swap are fastest | Copy and clone keep the old cluster usable. Link: old cluster unusable once the new one starts. Swap: old cluster unusable once pg_upgrade reports it unsafe. Restore from backup otherwise. | Same host or same file system, the downtime fits a window |
| Logical replication to a new-version cluster, then switch clients | Seconds (the switchover) | Keep the old primary; reverse replication only if you built it | Downtime must be minimal, or you are also changing host, OS, or collation library |
| `pg_dump`/`pg_restore` (or `pg_dumpall`) | Proportional to data size | Old cluster untouched | Small databases, encoding or locale changes, removing bloat |

Required intermediate steps and version-specific constraints:

- pg_upgrade preserves logical replication slots and subscription state only when the old cluster is 17 or later. From 14, 15, or 16 you must drop logical slots (or let RDS/Aurora refuse the upgrade) and re-create subscriptions afterwards. See [17](17.md).
- pg_upgrade transfers optimizer statistics only when the new cluster is 18 or later. Upgrading into 15, 16, or 17 leaves the new cluster without statistics until you run `ANALYZE`. See [18](18.md).
- Checksums: clusters initialized by `initdb` 18 or later have checksums on by default; pg_upgrade requires matching settings, so initialize the new cluster with `initdb --no-data-checksums` when the old cluster has none, or enable checksums on the old cluster first with `pg_checksums --enable` (offline).
- Into 16 or later from 15 or older: pg_upgrade refuses clusters with `aclitem` columns in user tables. Any upgrade: pg_upgrade refuses user-table columns of `regcollation`, `regconfig`, `regdictionary`, `regnamespace`, `regoper`, `regoperator`, `regproc` and `regprocedure`, because those OIDs are not preserved; `regclass`, `regrole` and `regtype` are allowed (`check.c`, REL_16_0). `pg_upgrade --check` lists them.
- Into 19: pg_upgrade refuses clusters that have `btree_gist` indexes on `inet`/`cidr` columns, and clusters whose database, role, or tablespace names contain carriage returns or line feeds. Dumps taken with pre-19 `pg_dump` from servers running `standard_conforming_strings = off` do not load into 19. See [19](19.md).
- Aurora and RDS: read [managed-services.md](../managed-services.md#major-version-upgrades); the managed upgrade runs pg_upgrade for you with its own prechecks.
- Downgrade: no in-place major downgrade exists. Rolling back means returning to the old cluster (if the method kept it), restoring a backup, or replicating logically back to an old-version cluster that you prepared before the switch.

Generic procedure for a major upgrade:

1. Inventory: `SELECT version();`, extensions and versions (`SELECT extname, extversion FROM pg_extension;` in every database), replication slots (`SELECT slot_name, slot_type, active FROM pg_replication_slots;`), prepared transactions (`SELECT count(*) FROM pg_prepared_xacts;` must be 0), and checksum setting.
2. Read the "Migration to Version N" section of each release note between source and target. List every incompatibility that touches your schema or application.
3. Make sure the extension shared libraries for the target version are installed on the new binaries (for pg_upgrade) before you start.
4. Rehearse on a restored copy: restore the latest base backup or snapshot to a separate host, run `pg_upgrade --check` (add the mode flag you will use, such as `--link --check`), then run the real upgrade there. Time it.
5. On the rehearsal, run the application's critical queries and compare plans and latency with production (`EXPLAIN (ANALYZE, BUFFERS)`; pg_stat_statements top queries).
6. Production: stop writes, take or confirm a fresh backup, run pg_upgrade (or switch clients for the logical method), start the new server.
7. Post-checks: run the scripts pg_upgrade generated, update extensions (`ALTER EXTENSION ... UPDATE;`), regenerate statistics (`vacuumdb --all --analyze-in-stages --missing-stats-only` then `vacuumdb --all --analyze-only` on 18+ targets; `vacuumdb --all --analyze-in-stages` before 18), re-create physical standbys or rsync them as the pg_upgrade documentation describes, check `pg_stat_activity` for errors and the log for warnings.
8. Delete the old cluster only after the new one has run cleanly through at least one full backup cycle.

## Outside the Covered Range

- Older than 14 (13 and earlier): the server is unsupported and receives no community fixes. Read the release notes from your version up to the target at https://www.postgresql.org/docs/release/. Expect that these files' claims about views and columns (`pg_stat_io`, `pg_stat_checkpointer`, `pg_wait_events`, predefined roles such as `pg_read_all_data`, SCRAM as default), EXPLAIN options (`GENERIC_PLAN`, `SERIALIZE`, `MEMORY`), and commands (`MERGE`) do not hold. Before 12, recovery is configured in `recovery.conf`, not `postgresql.conf` plus signal files. On RDS and Aurora, 11 through 13 may still run under paid Extended Support (see [managed-services.md](../managed-services.md)).
- Newer than 19 (20 or later, or 19 beta builds): read the release notes and migration section of the newer release before relying on defaults listed here. Defaults that changed recently (JIT, TOAST compression, `max_locks_per_transaction`, I/O worker settings, autovacuum scheduling) are the most likely to move again.
- In every answer about a server outside 14 to 19, state the version gap explicitly and say which statements were not checked against that version.

## Sources

- PostgreSQL versioning policy and release table: https://www.postgresql.org/support/versioning/ — checked 2026-11-27
- Release notes index: https://www.postgresql.org/docs/release/ — checked 2026-11-27
- PostgreSQL 19.0 release notes: https://www.postgresql.org/docs/release/19.0/ — checked 2026-11-27
- PostgreSQL 18.0 release notes: https://www.postgresql.org/docs/release/18.0/ — checked 2026-11-27
- PostgreSQL 17.0 release notes: https://www.postgresql.org/docs/release/17.0/ — checked 2026-11-27
- PostgreSQL 16.0 release notes: https://www.postgresql.org/docs/release/16.0/ — checked 2026-11-27
- PostgreSQL 15.0 release notes: https://www.postgresql.org/docs/release/15.0/ — checked 2026-11-27
- PostgreSQL 14.0 release notes: https://www.postgresql.org/docs/release/14.0/ — checked 2026-11-27
- pg_upgrade (19): https://www.postgresql.org/docs/19/pgupgrade.html — checked 2026-11-27
- Routine vacuuming (19): https://www.postgresql.org/docs/19/routine-vacuuming.html — checked 2026-11-27
- Logical decoding concepts, slot synchronization (19): https://www.postgresql.org/docs/19/logicaldecoding-explanation.html — checked 2026-11-27
- REPACK (19): https://www.postgresql.org/docs/19/sql-repack.html — checked 2026-11-27
- WAIT (19): https://www.postgresql.org/docs/19/sql-wait.html — checked 2026-11-27
- Amazon RDS for PostgreSQL release calendar: https://docs.aws.amazon.com/AmazonRDS/latest/PostgreSQLReleaseNotes/postgresql-release-calendar.html — checked 2026-11-27
- Aurora PostgreSQL release calendar: https://docs.aws.amazon.com/AmazonRDS/latest/AuroraPostgreSQLReleaseNotes/aurorapostgresql-release-calendar.html — checked 2026-11-27
- Amazon RDS Extended Support: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/extended-support.html — checked 2026-11-27
- RDS for PostgreSQL major version upgrade process: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_UpgradeDBInstance.PostgreSQL.MajorVersion.Process.html — checked 2026-11-27
- RDS for PostgreSQL upgrade targets: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_UpgradeDBInstance.PostgreSQL.MajorVersion.html — checked 2026-11-27
- Aurora PostgreSQL major version upgrade: https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/USER_UpgradeDBInstance.PostgreSQL.MajorVersion.html — checked 2026-11-27
- Aurora `aurora_version()`: https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora_version.html — checked 2026-11-27
- RDS `rds_superuser` role: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Appendix.PostgreSQL.CommonDBATasks.Roles.rds_superuser.html — checked 2026-11-27
- Aurora high availability: https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Concepts.AuroraHighAvailability.html — checked 2026-11-27
- Aurora storage: https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.Overview.StorageReliability.html — checked 2026-11-27
- pg_upgrade checks (`aclitem`, `reg*`), tag REL_16_0: https://github.com/postgres/postgres/blob/REL_16_0/src/bin/pg_upgrade/check.c — checked 2026-11-27
- Routine Vacuuming, wraparound error text: https://www.postgresql.org/docs/14/routine-vacuuming.html, https://www.postgresql.org/docs/16/routine-vacuuming.html, https://www.postgresql.org/docs/17/routine-vacuuming.html — checked 2026-11-27
- RDS Multi-AZ DB instance deployments: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZSingleStandby.html — checked 2026-11-27
- RDS for PostgreSQL upgrades (minor upgrade downtime): https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_UpgradeDBInstance.PostgreSQL.html — checked 2026-11-27
- Aurora point-in-time restore: https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-pitr.html — checked 2026-11-27
- RDS for PostgreSQL logical replication: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/PostgreSQL.Concepts.General.FeatureSupport.LogicalReplication.html — checked 2026-11-27
- pgAudit on RDS and Aurora: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Appendix.PostgreSQL.CommonDBATasks.pgaudit.html, https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Appendix.PostgreSQL.CommonDBATasks.pgaudit.html — checked 2026-11-27
- RDS Multi-AZ DB clusters: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/multi-az-db-clusters-concepts.html — checked 2026-11-27
- RDS point-in-time restore: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PIT.html — checked 2026-11-27
- Container outputs from official `postgres` images 14, 15, 16, 17, 18, 19 (image digests in the coverage record, `updates/2026-11-27-initial-coverage.md`): `pg-<tag>-battery.txt`, `pg-<tag>-settings.tsv`, `pg-<tag>-log.txt`, `pg-<tag>-hba.txt`, `pg-<tag>-deadlock.txt` — checked 2026-11-27. That battery started the server with `-c shared_preload_libraries=pg_stat_statements -c log_lock_waits=on`, so those two settings show source `command line` there; they are not image defaults. Follow-up runs without these overrides (images 13 to 19) and a 19.0 `pg_upgrade --check` against an 18.7 cluster — run 2026-11-27
