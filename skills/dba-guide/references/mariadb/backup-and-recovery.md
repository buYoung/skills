# MariaDB Backup and Recovery

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)). MySQL tools are not interchangeable here. The Galera SST page states that Percona XtraBackup is not supported in MariaDB, and its SST methods were removed. MariaDB's documentation does not cover MySQL Enterprise Backup against MariaDB or `mariadb-backup` against MySQL 8. Before relying on a cross-product combination, run a full backup, restore it to a scratch server, start it, and run `CHECK TABLE` on a sample of tables.

## Choosing a Method

| Method | Use when | Restore time | Consistency | Notes |
| --- | --- | --- | --- | --- |
| `mariadb-backup` full + incremental | Production datasets of any size; seeding replicas and Galera nodes | Copy-back speed of the files | Consistent for InnoDB; brief lock for non-InnoDB | Same major version on restore |
| `mariadb-dump --single-transaction` | Small databases, schema-only copies, cross-version or cross-product moves, single tables | Re-insert and re-index; slow on large data | Consistent for InnoDB tables only | Portable text; 13.1 changes generated-column and DEFINER output |
| `mariadb-dump --dir` / `mariadb-import --dir` (11.5+, so 11.8+) | Parallel logical copy of many databases | Faster than single-stream | Per-database | |
| Binary logs | PITR between backups | Replay time | Transactional | Retain long enough to cover the backup interval |
| Storage or volume snapshots | Very large datadirs with snapshot-capable storage | Fast | Crash-consistent only unless coordinated with `BACKUP STAGE` or `FLUSH TABLES WITH READ LOCK` | Test that InnoDB recovers from the snapshot |
| Managed snapshots (RDS) | RDS instances | Minutes to hours | Service-managed | See [managed services](managed-services.md) |

## mariadb-backup

Privileges for the backup user:

```sql
CREATE USER 'mariadb-backup'@'localhost' IDENTIFIED BY '...';
GRANT RELOAD, PROCESS, LOCK TABLES, BINLOG MONITOR ON *.* TO 'mariadb-backup'@'localhost';
-- add CONNECTION ADMIN if using --kill-long-queries-timeout without --no-lock
-- add REPLICA MONITOR (SLAVE MONITOR) for --slave-info or --galera-info
```

Full backup, prepare, restore:

```sh
# 1. Backup (target dir must be empty or absent)
mariadb-backup --backup --target-dir=/backup/full-2026-11-27 --user=mariadb-backup --password=...
# 2. Prepare: applies the redo log so files are consistent (run on the backup copy, not in the datadir)
mariadb-backup --prepare --target-dir=/backup/full-2026-11-27
# 3. Restore: stop the server, empty datadir, copy back, fix ownership, start
systemctl stop mariadb
mariadb-backup --copy-back --target-dir=/backup/full-2026-11-27     # --move-back consumes the backup
chown -R mysql:mysql /var/lib/mysql
systemctl start mariadb
```

Production safety: `--copy-back` requires an empty datadir. Never run it against the live datadir; restore to a new volume and swap, so the old data remains for rollback.

Incremental backups:

```sh
mariadb-backup --backup --target-dir=/backup/inc1 --incremental-basedir=/backup/full-2026-11-27 --user=... --password=...
mariadb-backup --backup --target-dir=/backup/inc2 --incremental-basedir=/backup/inc1 --user=... --password=...
# Prepare: base first, then each increment in order
mariadb-backup --prepare --target-dir=/backup/full-2026-11-27
mariadb-backup --prepare --target-dir=/backup/full-2026-11-27 --incremental-dir=/backup/inc1
mariadb-backup --prepare --target-dir=/backup/full-2026-11-27 --incremental-dir=/backup/inc2
```

- The checkpoints file is `mariadb_backup_checkpoints` (named `xtrabackup_checkpoints` in 11.0 and earlier); the binlog/GTID position of the backup is in `mariadb_backup_binlog_info` (renamed from `xtrabackup_*` in 11.1). A 13.0.2 backup directory still also contains `xtrabackup_binlog_pos_innodb`.
- With `--stream`, pass `--extra-lsndir` and use that directory as the next `--incremental-basedir`.
- `--history=name` records backups in `mysql.mariadb_backup_history` (10.11+; 10.10 and earlier use `PERCONA_SCHEMA.xtrabackup_history`) so increments can reference `--incremental-history-name`.
- Use the `mariadb-backup` package that matches the server's version. The pages checked do not state a rule for mixed versions, but the redo format changes between majors (for example 10.8). After any server upgrade, take a new full backup with the upgraded `mariadb-backup` and test-restore it.
- Non-InnoDB tables (Aria, MyISAM, CSV) and `.frm` files are copied under a short lock; `BACKUP STAGE` keeps that window small. `--no-lock` skips it and gives up consistency of non-InnoDB tables.
- 12.3 with `binlog_storage_engine=innodb`: binlog files are included and transactionally consistent; skip them with `--skip-binlog`.
- 13.0 `innodb_log_archive=ON`: `mariadb-backup` fails against the server. Do not enable log archiving on servers backed up with it.
- The deprecated `--innobackupex` mode (11.3+) should not be used in new scripts. It is not listed in `mariadb-backup --help` in any of the 10.6-13.0 images.

Seeding a replica from a backup: prepare, copy back, start, read the GTID from `mariadb_backup_binlog_info`, then `SET GLOBAL gtid_slave_pos='...'` and `CHANGE MASTER TO ... MASTER_USE_GTID=slave_pos` (see [replication](replication-and-ha.md#setting-up-a-replica)). With the InnoDB-based binlog, `CHANGE MASTER TO ..., MASTER_DEMOTE_TO_SLAVE=1` sets the position automatically from the included binlog.

## mariadb-dump

```sh
mariadb-dump --single-transaction --routines --triggers --events \
  --master-data=2 --gtid --databases app > app-2026-11-27.sql     # records binlog/GTID position as a comment
mariadb-dump --single-transaction --no-data --all-databases > schema.sql
mariadb-dump --dump-history --single-transaction app versioned_table > history.sql   # system-versioned history (10.11+)
```

- `--single-transaction` gives a consistent snapshot only for InnoDB; other engines are read as they change unless you lock them (`--lock-all-tables`). DDL on dumped tables during the dump can break the snapshot.
- `--master-data`/`--gtid` record the position for PITR or replica seeding (the option names follow MariaDB's client; `--source-data` is MySQL's name and is absent from `mariadb-dump --help` on 10.6-13.0).
- 11.8+: `--no-autocommit` is on by default in dumps, making reloads faster (one undo log per table).
- Dumping the `mysql` schema across major versions is not a reliable way to move users; prefer `SHOW CREATE USER` and `SHOW GRANTS` output, or `mariadb-dump --system=users,...` (`--system` accepts `all`, `users`, `plugins`, `udfs`, `servers`, `stats`, `timezones` in the 10.6-13.0 images).
- 13.1: generated columns are dumped as `DEFAULT` (or omitted with `--complete-insert`), and DEFINER clauses are no longer wrapped in version comments. Restore 13.1 dumps into older servers only after a rehearsal.
- Reload speed: `mariadb-import --innodb-optimize-keys` (11.8+, on by default) creates secondary indexes after loading.

## Point-in-Time Recovery

Prerequisites: `log_bin` on, binlogs retained since the last usable backup, and the backup's binlog/GTID position.

1. Restore the latest full (and incremental) backup to a recovery server, not the production datadir.
2. Read the start position from `mariadb_backup_binlog_info` (file, position, GTID).
3. Find the stop point: the GTID or time just before the bad event.

   ```sh
   mariadb-binlog --base64-output=decode-rows -vv --start-datetime='2026-11-27 09:00:00' mariadb-bin.000123 | grep -n -B5 'DROP TABLE'
   ```

4. Replay up to the stop point:

   ```sh
   mariadb-binlog --start-position=0-1-1000 --stop-position=0-1-5432 mariadb-bin.000120 mariadb-bin.000121 mariadb-bin.000122 mariadb-bin.000123 \
     | mariadb -u root -p
   ```

   GTID ranges in `--start-position/--stop-position` work from 10.8. Pass all files in one invocation so events that span files apply once.
5. Validate on the recovery server, then export the affected tables (`mariadb-dump`) or promote the recovery server.

Alternatives:

- Replay through a replica: point a restored server at a binlog source with `START SLAVE UNTIL master_gtid_pos='0-1-5432'`, which applies events with replica semantics and parallel apply.
- Undo recent row changes with `mariadb-binlog --flashback` (row-based binlogs, DML only, not DDL; not on Galera) to generate reverse statements; review before applying.
- RDS applied a PITR fix in 10.6.20, 10.11.10, 11.4.4 (reverting two community changes, MDEV-35528); keep self-hosted servers on patch levels that include the community fix (check the MDEV for fixed versions).

## Verifying Backups

A backup is verified only by a restore. Automate:

1. Restore the latest backup chain to a scratch host weekly (more often for critical systems).
2. Start the server; check the error log for InnoDB corruption or recovery errors.
3. Run `mariadb-check --all-databases --check` (or `CHECK TABLE` on critical tables).
4. Compare row counts or `CHECKSUM TABLE` of key tables with the primary at the backup's GTID (stop a replica at that GTID with `START SLAVE UNTIL`).
5. Replay binlogs to a recent point and run application smoke queries.
6. Record backup size, duration, restore duration, and the achieved RPO/RTO; alert when they drift.

## Crash Recovery

- InnoDB recovers automatically from the redo log on startup. Durability settings decide what is lost: `innodb_flush_log_at_trx_commit=1` plus `sync_binlog=1` (or the InnoDB-based binlog) lose no committed transactions on OS crash; `2` or `0` can lose about a second.
- Corruption: start with `innodb_force_recovery` values 1-6 only to dump data; never run production on a non-zero value. From 11.4.11/11.8.7, an 11.x server can start on 10.x data files with `innodb_force_recovery=6` for emergency extraction.
- Keep the error log; InnoDB prints the page and tablespace involved.
