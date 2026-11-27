# MariaDB Versions

Checked: 2026-11-27 against the MariaDB Foundation maintenance policy (https://mariadb.org/about/#maintenance-policy) and the MariaDB Community Server release notes (https://mariadb.com/docs/release-notes/community-server).

## Support Status

MariaDB Community Server has two release types (release model from 11.3 on):

- Long-term support (LTS): one per year, the highest minor version of a major series (10.11, 11.4, 11.8, 12.3). Community binaries for 3 years after GA, plus 2 more years of source-only critical and security fixes. LTS releases up to 11.4 get community binaries for 5 years. MariaDB plc sells Enterprise (5 years) and Extended (8 years) support.
- Rolling releases: a new minor series every quarter (12.0, 12.1, 12.2, 13.0, 13.1, ...). A rolling series gets no patch releases after GA except emergency fixes; you are expected to move to the next rolling series. Do not put a rolling release in production unless you need one of its features and accept a quarterly upgrade cadence.

Version numbers: `a.b.c` = major (grows yearly from 12), minor (grows quarterly; the largest `b` of a major is the LTS), patch (bug and security fixes only). Major series may make backward-incompatible changes; minor and patch releases are meant to stay compatible.

| Series | Type | First GA | Community end | Enterprise end | Extended end | Latest on 2026-11-27 | File |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 13.1 | Rolling | 2026-11-23 (13.1.2) | Q1 2027 | n/a | n/a | 13.1.2 | [13.1](13.1.md) |
| 13.0 | Rolling | 2026-09-15 (13.0.2) | Q4 2026 | n/a | n/a | 13.0.2 | [13.0](13.0.md) |
| 12.3 | LTS | 2026-05-28 (12.3.2) | 2029-06-12 | 2031-11-03 | 2034-11-03 | 12.3.4 | [12.3](12.3.md) |
| 11.8 | LTS | 2025-06-04 | 2028-06-04 | 2030-10-22 | 2033-10-22 | 11.8.10 | [11.8](11.8.md) |
| 11.4 | LTS | 2024-05-29 | 2029-05-29 | 2030-01-16 | 2033-01-16 | 11.4.14 | [11.4](11.4.md) |
| 10.11 | LTS | 2023-02-16 | 2028-02-16 | 2028-02-16 | 2028-02-16 | 10.11.20 | [10.11](10.11.md) |
| 10.6 | LTS, community EOL | 2021-07-06 | 2026-07-06 (ended) | 2028-08-23 | 2029-08-23 | 10.6.28 | [10.6](10.6.md) |

Notes:

- 10.6 is covered only as the upgrade source. Community support ended on 2026-07-06; The release-notes page lists 10.6.28 (2026-08-13) as the most recent 10.6 release; since community support has ended, treat it as the last community release (inference). Amazon RDS keeps 10.6 in standard support until 2026-12-31 (see [managed services](../managed-services.md)).
- The Foundation table lists rolling-release "release dates" (13.0: May 2026, 13.1: Sep 2026) that are earlier than the GA dates in the release notes (13.0.2 GA 2026-09-15, 13.1.2 GA 2026-11-23). The table above uses the release-notes GA dates. Treat rolling end dates as quarter-level only.
- Rolling series between LTS releases (11.5-11.7, 12.0-12.2) are out of support; their changes are folded into the next LTS file (11.8 for 11.5-11.7, 12.3 for 12.0-12.2).
- Official container images checked on 2026-11-27 lag the latest patch: 10.6.28, 10.11.19, 11.4.13, 11.8.9, 12.3.3, 13.0.2; no GA `13.1` image existed on the check date, so 13.1 was not run.

## Identify the Running Version

Server version, build and distribution:

```sql
SELECT VERSION(), @@version_comment, @@version_compile_os, @@version_compile_machine;
-- 13.0.2-MariaDB-ubu2604 | mariadb.org binary distribution | debian-linux-gnu | aarch64   (official image)
SHOW GLOBAL VARIABLES LIKE 'version%';
SELECT @@version_source_revision;      -- git commit of the build
```

- The string `MariaDB` in `VERSION()` separates MariaDB from MySQL. The suffix (`-ubu2404`, `-log`, `-enterprise`) shows packaging, binary logging, or edition; read `@@version_comment` for the distributor. Enterprise Server version strings carry an extra build number such as `11.8.9-6` (format taken from Enterprise release-note names; confirm on the server).
- From the shell: `mariadbd --version` (server binary) and `mariadb --version` (client). Client and server versions can differ; diagnose the server.
- Series: the first two numbers of `VERSION()` (for example `11.8`). Compare against the table above to decide LTS or rolling.
- Galera: `SHOW GLOBAL STATUS LIKE 'wsrep_provider_version';` and `SELECT @@wsrep_on;`. `wsrep_on=OFF` with a provider path set means Galera is installed but not running.
- Features compiled in or loaded: `SELECT PLUGIN_NAME, PLUGIN_STATUS FROM information_schema.PLUGINS;` and `SELECT ENGINE, SUPPORT FROM information_schema.ENGINES;`.
- Deprecated variables in use (13.0 and later): `SELECT VARIABLE_NAME, DEPRECATED_REPLACEMENT FROM information_schema.SYSTEM_VARIABLES WHERE IS_DEPRECATED = 'YES';` (columns added in 13.0: 13.0.2 returns 19 rows, for example `tx_isolation` → `transaction_isolation`, `tx_read_only` → `transaction_read_only`; 12.3.3 returns `ERROR 1054 Unknown column 'IS_DEPRECATED'`).

Managed service (Amazon RDS for MariaDB):

```sh
aws rds describe-db-instances --db-instance-identifier mydb \
  --query 'DBInstances[0].[Engine,EngineVersion,AutoMinorVersionUpgrade]'
aws rds describe-db-engine-versions --engine mariadb \
  --query '*[].EngineVersion' --output text
aws rds describe-db-major-engine-versions --engine mariadb   # support dates per major
```

`SELECT VERSION()` on RDS returns the community version number; RDS-specific behavior (restricted privileges, `mysql.rds_*` procedures) is the reliable sign you are on RDS. Aurora has no MariaDB edition; an "Aurora" endpoint is MySQL- or PostgreSQL-compatible, not MariaDB.

## Upgrade Paths

Supported directions:

| From | To | Supported | Notes |
| --- | --- | --- | --- |
| Any older MariaDB | Any newer MariaDB | Yes, in place | The upgrade guide states any earlier version can be upgraded to the latest; official step-by-step notes exist only per LTS step (10.6→10.11→11.4→11.8→12.3). When skipping LTS releases, read every intermediate upgrade note. |
| MySQL 5.7 and earlier | MariaDB | Yes (in place or logical) | `mariadb-upgrade` handles data files from MySQL releases before 8.0. |
| MySQL 8.0 / 8.4 / 9.x | MariaDB | Logical only (dump/load or replication) | Binary formats differ (data dictionary, JSON storage, GTID). See [replication](../replication-and-ha.md#replicating-between-mysql-and-mariadb). |
| MariaDB | MySQL | Logical only | MySQL cannot replicate from a MariaDB primary. |
| Newer MariaDB | Older MariaDB | Not supported | No tested in-place downgrade; replication from a newer primary to an older replica is not supported either. |

Rolling releases: move 13.0 → 13.1 → next. An LTS user who adopts a rolling release can return to LTS only by moving forward to the next LTS (for example 13.x rolling → 13.3 LTS when it ships), never backward to 12.3.

Downgrade and rollback limits:

- In-place downgrade works only if `mariadb-upgrade` has not run and no new-version DDL was executed; even then it is unsupported. 10.6 rejects a newer redo log format (`InnoDB: Unsupported redo log format`).
- The reliable rollback is the physical backup taken immediately before the upgrade (discarding later writes), or a logical dump from the new version restored into the old one (rehearse; dumps from newer versions can contain syntax the older version rejects).
- 11.8 and later: system-versioned tables are rewritten for the extended TIMESTAMP range; downgrading with system-versioned tables is "not trivial" per the 11.8 notes.

Generic procedure:

1. Pre-checks on the source:
   - Read the upgrade note for every LTS step crossed and the version files here (`Upgrading Into This Series`).
   - Remove options that the target removed; the server refuses to start on unknown options. List what is set: `my_print_defaults --mysqld` and `SELECT VARIABLE_NAME, GLOBAL_VALUE FROM information_schema.SYSTEM_VARIABLES WHERE GLOBAL_VALUE_ORIGIN = 'CONFIG';`.
   - Check reserved words introduced by the target against your schema (12.3 adds `CONVERSION`, `TO_DATE`).
   - Check storage engines in use: `SELECT ENGINE, COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA NOT IN ('mysql','information_schema','performance_schema','sys') GROUP BY ENGINE;`.
   - Confirm `innodb_fast_shutdown` is not 2 and `innodb_force_recovery` is below 3 before stopping the old server.
2. Rehearse on a restored copy: restore the latest `mariadb-backup` backup to a scratch host, upgrade it with the target packages, run `mariadb-upgrade`, run the application test suite and the top queries by total time. Compare `EXPLAIN` for those queries before and after (plans change across 10.11→11.x because of the cost model).
3. Switch:
   - Replicated setups: upgrade one replica, verify, upgrade remaining replicas, promote an upgraded replica, then upgrade the old primary as a replica. Older primary → newer replica is the supported direction.
   - Galera: rolling upgrade node by node per the Galera upgrade guide; from 12.3.2 the Galera package (`mariadb-server-galera` or `MariaDB-server-galera`) must be installed separately; see [replication](../replication-and-ha.md).
   - Single server: take a fresh physical backup, stop the server cleanly, remove the old server package and install the new one (the official upgrade pages do this on Debian/Ubuntu, RHEL and SLES alike), start, run `mariadb-upgrade` (as `sudo mariadb-upgrade` when root uses `unix_socket`).
4. Post-checks: error log free of `obsolete option` and InnoDB warnings; `SELECT VERSION()`; replication threads running (`SHOW REPLICA STATUS\G`); compare latency and the slow log against the baseline; recheck `@@innodb_snapshot_isolation`, `@@binlog_format`, collation defaults, and auth plugins of application users.

## Outside the Covered Range

Older than 10.6 (10.5 and earlier, all community EOL): treat every default in this reference as unverified for that server. Read the release notes of each series from the running one up to the target, starting with "Upgrading from MariaDB 10.5 to MariaDB 10.6" (utf8 becomes an alias of utf8mb3, atomic DDL). Expect missing features cited here (SKIP LOCKED, JSON_TABLE, ignored indexes, sys schema arrive in 10.6; GTID-by-default `CHANGE MASTER` in 10.10). Recommend an upgrade path to a supported LTS rather than tuning advice, and state the version gap in the answer.

Newer than 13.1 (13.2 development, 13.3 LTS when released): read the "Changes & Improvements" page of each newer series at https://mariadb.com/docs/release-notes/community-server and the upgrade page for the new LTS. Claims most likely to drift: default values (binlog format, snapshot isolation, character set), the optimizer hint set, InnoDB-based binary log limitations (semi-sync support arrives in 13.2), PARSEC becoming the default auth plugin, and deprecated variable removals. Say which version this reference was checked against (13.1.2 on 2026-11-27).

Enterprise Server: version numbers look like `11.8.9-6` and include backports not in Community (for example `create_tmp_table_binlog_formats` in 11.8.9-6 with a different default). Check the Enterprise release notes for the exact build instead of assuming Community behavior.

## Sources

- MariaDB Foundation, About / Maintenance policy (LTS and rolling end dates, numbering, compatibility promise): https://mariadb.org/about/#maintenance-policy, checked 2026-11-27
- MariaDB docs, Release Model: https://mariadb.com/docs/release-notes/community-server/about/release-model, checked 2026-11-27
- MariaDB docs, Community Server Release Notes index: https://mariadb.com/docs/release-notes/community-server, checked 2026-11-27
- MariaDB 13.1 Changes & Improvements: https://mariadb.com/docs/release-notes/community-server/13.1/mariadb-13.1-changes-and-improvements, checked 2026-11-27
- MariaDB 13.1.2 Release Notes: https://mariadb.com/docs/release-notes/community-server/13.1/13.1.2, checked 2026-11-27
- MariaDB 13.0 Changes & Improvements: https://mariadb.com/docs/release-notes/community-server/13.0/mariadb-13.0-changes-and-improvements, checked 2026-11-27
- MariaDB 12.3 Changes & Improvements: https://mariadb.com/docs/release-notes/community-server/12.3/mariadb-12.3-changes-and-improvements, checked 2026-11-27
- MariaDB 12.3.1 Release Notes: https://mariadb.com/docs/release-notes/community-server/12.3/12.3.1, checked 2026-11-27
- MariaDB 12.0 Changes & Improvements: https://mariadb.com/docs/release-notes/community-server/old-releases/12.0/what-is-mariadb-120, checked 2026-11-27
- MariaDB 11.8 Changes & Improvements: https://mariadb.com/docs/release-notes/community-server/11.8/what-is-mariadb-118, checked 2026-11-27
- MariaDB 11.4 Changes & Improvements: https://mariadb.com/docs/release-notes/community-server/11.4/what-is-mariadb-114, checked 2026-11-27
- MariaDB 10.11 Changes & Improvements: https://mariadb.com/docs/release-notes/community-server/10.11/what-is-mariadb-1011, checked 2026-11-27
- MariaDB 10.6 Changes & Improvements: https://mariadb.com/docs/release-notes/community-server/10.6/what-is-mariadb-106, checked 2026-11-27
- Upgrading from MariaDB 11.8 to 12.3: https://mariadb.com/docs/server/server-management/install-and-upgrade-mariadb/upgrading/mariadb-community-server-upgrade-paths/upgrading-from-mariadb-11-8-to-mariadb-12-3, checked 2026-11-27
- Upgrading from MariaDB 11.4 to 11.8: https://mariadb.com/docs/server/server-management/install-and-upgrade-mariadb/upgrading/mariadb-community-server-upgrade-paths/upgrading-from-mariadb-11-4-to-mariadb-11-8, checked 2026-11-27
- Upgrading from MariaDB 10.11 to 11.4: https://mariadb.com/docs/server/server-management/install-and-upgrade-mariadb/upgrading/mariadb-community-server-upgrade-paths/upgrading-from-mariadb-10-11-to-mariadb-11-4, checked 2026-11-27
- Upgrading from MariaDB 10.6 to 10.11: https://mariadb.com/docs/server/server-management/install-and-upgrade-mariadb/upgrading/mariadb-community-server-upgrade-paths/upgrading-from-mariadb-10-6-to-mariadb-10-11, checked 2026-11-27
- Upgrade paths index: https://mariadb.com/docs/server/server-management/install-and-upgrade-mariadb/upgrading/mariadb-community-server-upgrade-paths, checked 2026-11-27
- Upgrading Between Major MariaDB Versions: https://mariadb.com/docs/server/server-management/install-and-upgrade-mariadb/upgrading/platform-specific-upgrade-guides/upgrading-on-linux/upgrading-between-major-mariadb-versions, checked 2026-11-27
- Downgrading between major versions: https://mariadb.com/docs/server/server-management/install-and-upgrade-mariadb/downgrading-between-major-versions-of-mariadb, checked 2026-11-27
- InnoDB System Variables: https://mariadb.com/docs/server/server-usage/storage-engines/innodb/innodb-system-variables, checked 2026-11-27
- Replication and Binary Log System Variables: https://mariadb.com/docs/server/ha-and-performance/standard-replication/replication-and-binary-log-system-variables, checked 2026-11-27
- InnoDB-Based Binary Log: https://mariadb.com/docs/server/server-management/server-monitoring-logs/binary-log/innodb-based-binary-log, checked 2026-11-27
- Amazon RDS, MariaDB on Amazon RDS versions: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/MariaDB.Concepts.VersionMgmt.html, checked 2026-11-27
- Global Transaction ID (GTID): https://mariadb.com/docs/server/ha-and-performance/standard-replication/gtid, checked 2026-11-27
- Semisynchronous Replication: https://mariadb.com/docs/server/ha-and-performance/standard-replication/semisynchronous-replication, checked 2026-11-27
- Galera Cluster Known Limitations: https://mariadb.com/docs/galera-cluster/reference/mariadb-galera-cluster-known-limitations, checked 2026-11-27
- Thread Pool in MariaDB: https://mariadb.com/docs/server/ha-and-performance/optimization-and-tuning/buffers-caches-and-threads/thread-pool/thread-pool-in-mariadb, checked 2026-11-27
- The Optimizer Cost Model from MariaDB 11.0: https://mariadb.com/docs/server/ha-and-performance/optimization-and-tuning/query-optimizer/the-optimizer-cost-model-from-mariadb-11-0, checked 2026-11-27
- System-Versioned Tables: https://mariadb.com/docs/server/reference/sql-structure/temporal-tables/system-versioned-tables, checked 2026-11-27
- mariadb-backup Overview: https://mariadb.com/docs/server/server-usage/backup-and-restore/mariadb-backup/mariadb-backup-overview, checked 2026-11-27
- Authentication plugins (parsec, unix_socket, ed25519): https://mariadb.com/docs/server/reference/plugins/authentication-plugins, checked 2026-11-27
- MySQL to MariaDB Compatibility Matrix: https://mariadb.com/docs/server/server-management/install-and-upgrade-mariadb/migrating-to-mariadb/moving-from-mysql/mysql-to-mariadb-compatibility-matrix, checked 2026-11-27
- Galera Cluster Status Variables: https://mariadb.com/docs/galera-cluster/reference/galera-cluster-status-variables, checked 2026-11-27. The RDS for MariaDB pages are listed in `managed-services.md`. The GTID system variables, incremental mariadb-backup, and MariaDB versus MySQL compatibility pages were also read on 2026-11-27 under the same documentation trees; their full addresses were not recorded
- Official container images `mariadb:10.6`, `10.11`, `11.4`, `11.8`, `12.3`, `13.0` (image digests in the coverage record, `updates/2026-11-27-initial-coverage.md`), variable dumps and batteries run 2026-11-27
