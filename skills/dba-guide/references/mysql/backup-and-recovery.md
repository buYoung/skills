# MySQL Backup, Restore, and Point-in-Time Recovery

Checked: 2026-11-27. Applies to MySQL 8.0 through 26.10. `mysqlpump` was removed in 8.4; do not plan with it.

## Choose a Method

| Method | Type | Consistent without blocking writes | Restore speed | Cross-version restore | Notes |
|---|---|---|---|---|---|
| MySQL Shell `util.dumpInstance` / `util.loadDump` | logical, parallel, chunked | Yes for InnoDB (brief global read lock at start) | Medium; parallel load | Yes; the usual path for upgrades and migrations | Needs MySQL Shell. |
| `mysqldump --single-transaction` | logical, single-threaded | Yes for InnoDB | Slow for large data | Yes | Universally available; fine up to tens of GB. |
| Clone plugin (`CLONE LOCAL DATA DIRECTORY` or remote) | physical | Yes | Fast | Same series only | Copies InnoDB only; no incremental. |
| MySQL Enterprise Backup | physical, incremental | Yes | Fast | Same series | Commercial. |
| File-system or volume snapshot | physical | Needs `LOCK INSTANCE FOR BACKUP` or a crash-consistent snapshot of all InnoDB files at one instant | Fast | Same version | Snapshot must cover data, redo and undo at the same instant. |
| Binary logs | change stream | n/a | Replay speed | Same or newer version | Required for point-in-time recovery on top of any full backup. |

Rules:

- Every backup plan is a full backup plus continuous binary logs, unless losing everything since the last full backup is acceptable.
- Keep binary logs (or a binlog stream) at least back to the oldest full backup you would restore.
- A replica is not a backup: `DROP TABLE` replicates. Delayed replicas (`SOURCE_DELAY=3600`) give a rewind window for operator mistakes but are not a backup either.
- Take backups from a replica when possible, but verify the replica is not lagging or diverged.

## Logical Backups

mysqldump, consistent for InnoDB and with the binlog position recorded:

```bash
mysqldump --single-transaction --source-data=2 --routines --events --triggers \
  --set-gtid-purged=AUTO --all-databases > full.sql
# 8.0 servers before --source-data existed: --master-data=2
```

- `--single-transaction` uses a REPEATABLE READ snapshot; it does not protect against concurrent DDL. Avoid `ALTER TABLE` during the dump.
- The long-running snapshot holds back purge (history list grows); see [transactions-and-locking.md](transactions-and-locking.md#mvcc-undo-and-purge).
- `--source-data` briefly takes `FLUSH TABLES WITH READ LOCK`, which waits for long-running queries and blocks writes while it waits. Start dumps when no long queries run.
- Since 9.2.0 `--column-statistics` is off by default; since 9.3.0 `--users` dumps accounts as `CREATE USER`/`GRANT` (container: `--column-statistics` TRUE on 8.0.46 and 8.4.13, FALSE on 9.7.4 and 26.x; `--users`, `--add-drop-user`, `--include-user`, `--exclude-user` only from 9.7.4 among the images).
- `--master-data` is still accepted on every image through 26.10.0, with help text marking it deprecated in favor of `--source-data`.
- `mysqldump --output-as-version=BEFORE_8_2_0` (8.4+; present in 8.4.13 and later images, absent in 8.0.46) writes old replication syntax when the dump must load on an older replica.

MySQL Shell, parallel and chunked:

```js
// mysqlsh
util.dumpInstance('/backup/2026-11-27', {threads: 8, consistent: true})
util.dumpSchemas(['app'], '/backup/app', {threads: 8})
util.loadDump('/backup/2026-11-27', {threads: 8})   // target needs local_infile=ON during the load
```

`consistent: true` (default) takes `FLUSH TABLES WITH READ LOCK` (needs `RELOAD`; falls back to `LOCK TABLES`), starts a consistent snapshot in every thread, then switches to `LOCK INSTANCE FOR BACKUP` and releases the global lock. Without `BACKUP_ADMIN` it runs an extra consistency check and aborts an instance dump if the check fails. Minimum privileges: `EVENT`, `RELOAD`, `SELECT`, `SHOW VIEW`, `TRIGGER`; add `REPLICATION CLIENT` to record the binlog position. Use `dryRun: true` first to list incompatibilities. The `compatibility` option (for example `strip_definers`, `create_invisible_pks`, `target_has_mysql_native_password`) adapts a dump for a different target.

`local_infile` is OFF by default (all containers). Enable it on the target only for the load window, then disable it.

## Physical Backups

Clone to a local directory (same server, InnoDB only):

```sql
INSTALL PLUGIN clone SONAME 'mysql_clone.so';
CLONE LOCAL DATA DIRECTORY = '/backup/clone-2026-11-27';
```

The directory must not exist. The copy is a ready-to-start data directory for the same series. Non-InnoDB tables are not copied. Container check (all five images): the clone finished with `clone_status.STATE = Completed`, and the target held `mysql.ibd`, `ibdata1`, the undo tablespaces, `#innodb_redo` and one directory per schema.

Volume snapshot procedure:

```sql
LOCK INSTANCE FOR BACKUP;          -- blocks DDL and some admin operations, not DML (needs BACKUP_ADMIN)
SHOW BINARY LOG STATUS;            -- record file, position, Executed_Gtid_Set (8.0: SHOW MASTER STATUS)
-- take the snapshot of all volumes holding datadir, redo, undo, binlogs at once
UNLOCK INSTANCE;
```

The snapshot is crash-consistent: on restore InnoDB runs crash recovery. If datadir, redo and undo live on several volumes, the snapshots must be atomic across them; otherwise use `FLUSH TABLES WITH READ LOCK` held for the snapshot duration (blocks writes) or a backup tool.

Durability settings decide what a crash-consistent copy contains: with `innodb_flush_log_at_trx_commit=1` and `sync_binlog=1` (defaults), every acknowledged commit is in redo and binlog.

## Point-in-Time Recovery

Restore the full backup to a new server, then replay binary logs from the backup's position to just before the bad event.

The official `mysql` Docker images (8.0 through 26.10) do not include `mysqlbinlog`; their client tools are `mysql`, `mysqladmin`, `mysqldump`, `mysqlsh` and a few utilities. Run `mysqlbinlog` from a host or image that has it.

1. Find the stop point:
   ```bash
   mysqlbinlog --verbose --base64-output=DECODE-ROWS \
     --start-datetime='2026-11-27 09:00:00' binlog.000042 | grep -n -B5 'DROP TABLE'
   ```
   Note the GTID or end position of the last good transaction.
2. Restore the full backup to a separate instance (never over production).
3. Replay all needed files in one `mysqlbinlog` invocation, so temporary tables and multi-file transactions are handled in one session:
   ```bash
   # GTID-based (backup taken with GTIDs; the restored server's gtid_executed already covers the backup)
   mysqlbinlog --exclude-gtids='3e11fa47-71ca-11e1-9e33-c80aa9429562:1045' \
     binlog.000041 binlog.000042 | mysql -u root -p
   # or position-based
   mysqlbinlog --start-position=1441671 --stop-position=2997942 \
     binlog.000041 binlog.000042 | mysql -u root -p
   ```
   With GTIDs, transactions already in `gtid_executed` are skipped automatically, so start from the file containing the backup position.
4. Add `--binary-mode` to `mysql` if the output contains `\0` characters. Read encrypted binlogs through the server with `mysqlbinlog --read-from-remote-server`.
5. Verify, then copy the recovered rows (or the whole instance) back.

Continuous binlog backup off the server:

```bash
mysqlbinlog --read-from-remote-server --host=db1 --user=backup --password \
  --raw --stop-never --result-file=/binlog-archive/ binlog.000001
```

Run it under a supervisor and alert when it stops.

## Verify Restores

A backup counts only after a restore from it succeeded. Schedule, at least weekly:

1. Restore the latest full backup plus binlogs to a scratch instance of the same version.
2. Start it and check the error log.
3. Compare row counts and checksums for key tables against the source at the backup position:
   ```sql
   CHECKSUM TABLE app.orders;      -- full scan; compare only between identical versions and row formats
   SELECT COUNT(*), MAX(id) FROM app.orders;
   ```
4. Run `CHECK TABLE` on a sample of large tables (reads the whole table).
5. Record the elapsed restore time; it is your real recovery time objective.

## Common Mistakes

- Dumping with `mysqldump` without `--single-transaction` (locks or inconsistent snapshots) or without `--routines --events`.
- Assuming `--single-transaction` covers MyISAM tables. It does not.
- Restoring a GTID dump into a server that already has GTIDs (`gtid_purged` cannot be set when `gtid_executed` is not empty); `RESET BINARY LOGS AND GTIDS` on a fresh target first (8.4+; 8.0: `RESET MASTER`). This erases the target's binary logs.
- Binlog retention shorter than the backup interval.
- No restore test, so the backup lacks the `mysql` schema, users, or the keyring needed for encrypted tablespaces.
- Encrypted tablespaces (`default_table_encryption`, keyring components): back up the keyring separately. Without it, the restored data cannot be read.

## Sources

Checked 2026-11-27: MySQL 8.4 manual, Point-in-Time Recovery Using Binary Logs (https://dev.mysql.com/doc/refman/8.4/en/point-in-time-recovery-binlog.html); MySQL 8.4 manual, Cloning Remote Data (https://dev.mysql.com/doc/refman/8.4/en/clone-plugin-remote.html); MySQL Shell 26.10, Instance/Schema/Table Dump utilities (https://dev.mysql.com/doc/mysql-shell/26.10/en/mysql-shell-utilities-dump-instance-schema.html); MySQL 8.4 What Is New (mysqlpump removal, `--output-as-version`); Changes in MySQL 9.2.0 and 9.3.0 (mysqldump defaults and user options). `mysqldump` and `mysqlbinlog` option names (`--source-data`, `--set-gtid-purged`, `--exclude-gtids`, `--start-position`, `--raw --stop-never`) and `LOCK INSTANCE FOR BACKUP` follow the 8.4 manual program and statement pages. The `mysqldump` options were checked against `mysqldump --help` on all five images (2026-11-27); the `mysqlbinlog` options were not, because the images do not ship `mysqlbinlog`.
