# MySQL Versions

Checked: 2026-11-27 against the Oracle Lifetime Support Policy for Technology Products (https://www.oracle.com/assets/lifetime-support-technology-069183.pdf, effective 2026-11-13) and the MySQL release model page (https://dev.mysql.com/doc/refman/26.10/en/mysql-releases.html).

## Support Status

Oracle MySQL Server has two tracks. LTS series get 5 years of Premier Support and 3 years of Extended Support. Innovation releases are supported only until the next Innovation release. Since 26.7, releases use calendar versions (YY.M.P; update-aware interfaces add a fourth update component). 9.7 is the last sequentially numbered series.

| Series | Release type | GA | Premier Support ends | Extended Support ends | File |
|---|---|---|---|---|---|
| 26.10 | Innovation | 2026-10-20 (26.10.0) | When the next Innovation release ships (date not announced) | none | [26.10](26.10.md) |
| 26.7 | Innovation | 2026-07-28 (26.7.0) | Ended 2026-10-20, when 26.10.0 shipped | none | covered in [26.10](26.10.md) |
| 9.7 | LTS | 2026-04-21 (9.7.0) | Apr 2031 | Apr 2034 | [9.7](9.7.md) |
| 8.4 | LTS | 2024-04-30 (8.4.0) | Apr 2029 | Apr 2032 | [8.4](8.4.md) |
| 8.0 | Former LTS/bugfix series | Apr 2018 | Apr 2025 | Apr 2026 (Sustaining Support only, since 2026-04-21) | [8.0](8.0.md) |

Notes:

- 8.0 is covered as the most recent series to leave support, because most upgrades start from it. 8.0.46 is the final 8.0 release; Oracle's 8.0 release notes state that 8.0 reached end of life in April 2026. Sustaining Support gives access to existing fixes only.
- Newest builds on 2026-11-27: 8.0.46, 8.4.13, 9.7.4 (update 9.7.4.1 on 2026-11-24), 26.10.0 (update 26.10.0.1 on 2026-11-24).
- Within an LTS series Oracle adds or removes no features; that happens only in the first release of a new LTS series (8.4.0, 9.7.0). Bug fixes in an LTS patch can still change syntax or defaults: 8.4.11 and 9.7.2 made `MANUAL` and `PARALLEL` nonreserved, and 9.7.2 changed the `thread_pool_max_unused_threads` default. Read the notes of every patch you cross. Innovation releases may remove features and change behavior in any release.
- Managed-service dates differ from Oracle's dates. See [managed-services.md](../managed-services.md#version-availability-and-extended-support).

## Identify the Running Version

Run these on every server you advise on, and put the version in the answer.

```sql
SELECT VERSION(), @@version_comment, @@version_compile_os, @@version_compile_machine, @@license;
-- 8.4.13+, 9.7.4+, 26.10+ only: four-part release identity
SELECT VERSION_WITH_UPDATE(), @@version_with_update;
SELECT PLUGIN_NAME, PLUGIN_STATUS FROM information_schema.PLUGINS
 WHERE PLUGIN_NAME IN ('mysql_native_password','audit_log','thread_pool','group_replication','clone');
SELECT * FROM mysql.component;   -- loaded components (keyring, validate_password, ...)
SELECT VARIABLE_NAME, VARIABLE_SOURCE, VARIABLE_PATH
  FROM performance_schema.variables_info WHERE VARIABLE_SOURCE <> 'COMPILED';
```

How to read the output:

| Output | Meaning |
|---|---|
| `VERSION()` = `8.4.13`, `@@version_with_update` = `8.4.13.1` | 8.4.13 with its first separately delivered update (container output, 2026-11-27). `VERSION()`, `version` and `mysqld --version` stay three-part. |
| `@@version_comment` = `MySQL Community Server - GPL`, `@@license` = `GPL` | Oracle Community build; `GPL` is the documented default of `license`. Any other `version_comment` or `license` value means a different build (Enterprise, a vendor, or a managed service): check the build's own documentation before applying Community defaults. |
| `@@version` contains `MariaDB` | MariaDB, not MySQL. Use the MariaDB part of this skill (`../mariadb/versions/index.md`). |
| `@@version` has a distribution suffix (`-0ubuntu...`) | Distribution package. Upstream semantics apply; packaged option files may change defaults. |
| `SELECT @@aurora_version` succeeds | Amazon Aurora MySQL. Read the Aurora release from `AURORA_VERSION()`, not from `VERSION()`. |
| `variables_info.VARIABLE_SOURCE` | `DYNAMIC` = set at runtime; `PERSISTED` = from `mysqld-auto.cnf` (`SET PERSIST`); `GLOBAL`, `SERVER`, `EXPLICIT`, `EXTRA` = from an option file named in `VARIABLE_PATH`; `COMMAND_LINE` = startup flag. |

The data directory holds `mysql_upgrade_history` (8.4.0 and later). It is JSON and lists each version that started on this data directory, with `maturity` (`LTS` or `INNOVATION`; container: 8.4.13 and 9.7.4 write `LTS`, 26.7.0 and 26.10.0 write `INNOVATION`, 8.0.46 has no such file). Read it before an upgrade or downgrade: it shows whether the data directory ever ran an Innovation release.

```bash
cat /var/lib/mysql/mysql_upgrade_history
mysqld --version
mysqld --version-with-update      # 8.4.13+, 9.7.4+, 26.10+; see the warning below
mysqld --verbose --help | grep -A1 'Default options'   # option files read, in order
```

Run `mysqld --version-with-update` only where you know the option exists. On the 8.0.46 and 26.7.0 images it is not rejected as an unknown option: `mysqld` starts a second server on the default data directory, which fails with "Unable to lock ./ibdata1" while the real server runs (on 8.0.46 it retried for about 100 seconds before aborting). Use `mysqld --version` there.

Managed services:

```bash
# RDS for MySQL
aws rds describe-db-instances --db-instance-identifier <id> \
  --query 'DBInstances[0].[Engine,EngineVersion,AutoMinorVersionUpgrade]'
aws rds describe-pending-maintenance-actions
# Aurora MySQL: engine version such as 8.0.mysql_aurora.3.10.0 or 8.4.mysql_aurora.8.4.7
aws rds describe-db-clusters --db-cluster-identifier <id> \
  --query 'DBClusters[0].[Engine,EngineVersion]'
```

```sql
-- Aurora MySQL, any instance in the cluster
SELECT AURORA_VERSION(), @@aurora_version;   -- 3.05.2 style on version 3, 8.4.7 style on 8.4
```

## Upgrade Paths

Direct upgrades Oracle supports (Upgrade Paths page, 26.10 manual):

| From | To | Direct? | Methods |
|---|---|---|---|
| 8.0.x | later 8.0.x | yes | in-place, logical dump and load, replication, clone |
| 8.0.x | 8.4.x | yes | in-place, logical, replication |
| 8.0.x | 9.7.x | no: 8.0 -> 8.4 -> 9.7 | an LTS/bugfix series cannot be skipped |
| 8.4.x | later 8.4.x | yes | in-place, logical, replication, clone |
| 8.4.x | 9.7.x | yes | in-place, logical, replication |
| 8.4.x | 26.x | no: 8.4 -> 9.7 -> 26.x | only 9.7.x LTS can enter the first calendar-versioned lineage |
| 9.0-9.6 Innovation | 9.7.x | yes | in-place, logical, replication |
| 9.6.x | 26.7.0 | rejected at startup | source is not 9.7.x LTS |
| 9.7.x | 26.7.x or 26.10.x | yes | enters the lineage anchored by 9.7.0 |
| 26.7.x | 26.10.x | yes | same lineage |
| 5.7 | 8.4 | no: 5.7 -> 8.0 -> 8.4 | |

Calendar-version lineage rules (since 26.7.0; the server checks lineage metadata stored in the data dictionary at startup):

- An Innovation release can upgrade only to a later release in the same lineage, including the LTS release that closes the lineage.
- An LTS release can upgrade within its own line or into the next lineage. It cannot skip a lineage.
- The manual's examples use 28.4 as a future LTS. Treat that as an example, not an announced release.

Downgrade and rollback limits:

- Within an LTS series, in-place downgrade is supported (for example 8.4.2 to 8.4.0). Group Replication members can mix 8.4.x versions.
- Since 9.3.0, Innovation releases cannot be downgraded in place, not even within one series. Innovation downgrades need a logical dump and load.
- Since 26.7, direct downgrade is limited to qualifying patch downgrades within the same LTS YY.M line.
- Across series (8.0 -> 8.4, 8.4 -> 9.7, 9.7 -> 26.x) there is no in-place downgrade. Plan rollback as fail-back to a server still on the old version (an old-version replica of the new primary works only while the new primary writes nothing the old version cannot apply), or as restore of a pre-upgrade backup plus a logical reload of later writes.
- Clone copies between patch releases of one series and, from 26.7, from an LTS donor to the next LTS recipient only. It is not a cross-series rollback tool.

Generic procedure (version-specific blockers are in each version file):

1. Inventory: `VERSION()`, `mysql_upgrade_history`, the option files read, `SELECT * FROM performance_schema.persisted_variables`, plugins and components, and the authentication plugin of every account:
   ```sql
   SELECT user, host, plugin FROM mysql.user ORDER BY plugin, user;
   XA RECOVER;   -- must return no rows before an in-place upgrade; commit or roll back what it lists
   ```
2. Run the MySQL Shell upgrade checker, using a Shell release at least as new as the target:
   ```bash
   mysqlsh -- util check-for-server-upgrade root@db1:3306 \
     --target-version=8.4.13 --output-format=JSON --config-path=/etc/my.cnf
   ```
   Errors block the upgrade; warnings and notices need a decision. The account needs `PROCESS` and `SELECT`. Without `--config-path`, option-file checks cannot run. The target cannot be newer than the Shell release.
3. Remove settings the target rejects from option files and from `mysqld-auto.cnf` (`RESET PERSIST name`). A removed variable in an option file stops the server from starting.
4. Rehearse on a restored copy of production (a physical backup or clone of real data, not an empty instance). Run the upgrade there, replay the application tests or a captured workload, and compare plans and latency of the top statement digests (see [query-plans.md](../query-plans.md)).
5. Switch. Preferred for production: build a replica on the target version, let it catch up, verify data, stop writes, wait for zero lag, promote, repoint clients. Replicating from an older source to a newer replica is supported; the reverse is not.
   In-place: if you run `innodb_fast_shutdown=2`, set it to 1 (fast) or 0 (slow) first; shut down; replace binaries; start on the same data directory. The server upgrades the data dictionary, system schema, Performance Schema and `sys` at startup (`mysql_upgrade` was removed in 8.4). If that step fails, the server reverts its changes; fix the cause on the old version and retry. Keep the pre-upgrade backup until the post-checks pass.
6. Post-checks: no upgrade errors in the error log; all replicas healthy (`SHOW REPLICA STATUS`); every application account can log in (watch `mysql_native_password` accounts); top digests keep their plans and latency; `SELECT @@GLOBAL.gtid_mode, @@GLOBAL.explain_format, @@GLOBAL.innodb_change_buffering, @@GLOBAL.innodb_adaptive_hash_index` show the values you intend, because defaults change between series.

## Outside the Covered Range

Older than 8.0 (5.7 or earlier): not described here. Read the 8.0 upgrade chapter (https://dev.mysql.com/doc/refman/8.0/en/upgrading.html) and the 8.0 release notes. Do not assume the transactional data dictionary and atomic DDL, `caching_sha2_password`, roles, `SET PERSIST`, `performance_schema.data_locks`, `EXPLAIN ANALYZE`, instant DDL, invisible or descending indexes, CTEs and window functions, `innodb_redo_log_capacity`, or the clone plugin. Path: 5.7 -> 8.0 -> 8.4.

Innovation series 8.1-8.3 and 9.0-9.6: read the 8.4 release notes (8.1-8.3 changes) or the 9.7 release notes (https://dev.mysql.com/doc/relnotes/mysql/9.7/en/, which include 9.0.0-9.6.x). Behavior lies between the neighbouring LTS files. Upgrade to the next LTS first; these releases are out of support.

Newer than 26.10: read that series' release notes (https://dev.mysql.com/doc/relnotes/mysql/<series>/en/) and its "What Is New" and "Upgrade Paths" pages. Do not assume the 26.10 defaults or removal lists still hold.

Non-Oracle builds (Percona Server, distribution builds): defaults, bundled plugins and removals can differ; read that vendor's release notes.

In every answer about a server outside the covered range, state the gap ("this reference covers 8.0 to 26.10; the server runs X") and name the release notes used.

## Sources

All checked 2026-11-27.

- Oracle Lifetime Support Policy, Technology Products guide (effective 2026-11-13): https://www.oracle.com/assets/lifetime-support-technology-069183.pdf. MySQL Database 8.0, 8.4, 9.7 GA, Premier and Extended dates, read from the PDF downloaded directly on 2026-11-27 (8.0: Premier Apr 2025, Extended Apr 2026; 8.4: Apr 2029, Apr 2032; 9.7: Apr 2031, Apr 2034). Some fetch tools get HTTP 403 from this address; a plain HTTPS download worked.
- MySQL Product Support EOL Announcements: https://www.mysql.com/support/eol-notice.html (8.0 in Sustaining Support since 2026-04-21)
- MySQL 26.10 manual, MySQL Releases: Innovation and LTS: https://dev.mysql.com/doc/refman/26.10/en/mysql-releases.html (tracks, support terms, calendar versions, lineages)
- MySQL 26.10 manual, Upgrade Paths: https://dev.mysql.com/doc/refman/26.10/en/upgrade-paths.html
- MySQL 8.4 manual, Upgrading MySQL Binary or Package-based Installations: https://dev.mysql.com/doc/refman/8.4/en/upgrade-binary-package.html (in-place steps, XA RECOVER, fast shutdown)
- MySQL 8.0 release notes index: https://dev.mysql.com/doc/relnotes/mysql/8.0/en/ (8.0.46 final)
- MySQL 9.7 release notes index: https://dev.mysql.com/doc/relnotes/mysql/9.7/en/ (9.7.0 2026-04-21 through 9.7.4.1 2026-11-24)
- Changes in MySQL 9.3.0: https://dev.mysql.com/doc/relnotes/mysql/9.7/en/news-9-3-0.html (no Innovation downgrades)
- Changes in MySQL 26.7.0: https://dev.mysql.com/doc/relnotes/mysql/26.7/en/news-26-7-0.html (GA 2026-07-28)
- Changes in MySQL 26.10.0: https://dev.mysql.com/doc/relnotes/mysql/26.10/en/news-26-10-0.html (GA 2026-10-20, four-part version)
- Changes in MySQL 26.10.0.1: https://dev.mysql.com/doc/relnotes/mysql/26.10/en/news-26-10-0-1.html (2026-11-24 Critical Security Patch Update)
- MySQL 26.7 What Is New: https://dev.mysql.com/doc/refman/26.7/en/mysql-nutshell.html (lineage validation, clone rules)
- MySQL 8.4 What Is New: https://dev.mysql.com/doc/refman/8.4/en/mysql-nutshell.html (`mysql_upgrade_history`, version identity)
- MySQL Shell 26.10, Upgrade Checker Utility: https://dev.mysql.com/doc/mysql-shell/26.10/en/mysql-shell-utilities-upgrade.html
- Aurora MySQL version numbers: https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraMySQL.Updates.Versions.html
- Official Docker images mysql:8.0, 8.4, 9.7, 26.7, 26.10 (digests in the coverage record, `updates/2026-11-27-initial-coverage.md`), outputs dated 2026-11-27: version strings and `version_with_update`.
