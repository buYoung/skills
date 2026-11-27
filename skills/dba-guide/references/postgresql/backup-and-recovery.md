# Backup, Restore, and Point-in-Time Recovery

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)). Managed-service backups are in [managed-services.md](managed-services.md#backups-and-pitr).

## Choosing a method

| Method | Granularity | Restore point | Restore speed | Use for |
| --- | --- | --- | --- | --- |
| `pg_dump` / `pg_restore` | one database, selected tables | time of dump | slow (rebuilds indexes) | small databases, migrations across versions or platforms, per-table recovery |
| `pg_dumpall` | whole cluster incl. roles | time of dump | slow | small clusters; `--globals-only` to capture roles and tablespaces alongside per-database dumps |
| `pg_basebackup` + WAL archive | whole cluster | any moment covered by WAL (PITR) | fast (file copy + replay) | production recovery objective |
| Incremental `pg_basebackup` (17+) | whole cluster | as above | combine + replay | large clusters where full backups are too slow or big |
| Storage snapshots | whole volume | snapshot time, or PITR with archived WAL | fast | only if the snapshot is atomic across data and WAL directories |

A dump is not a substitute for PITR: it loses everything after the dump started.

## Logical backups

```bash
# custom format, compressed, restorable selectively and in parallel
pg_dump -Fc -d app -f app.dump
# directory format, parallel dump
pg_dump -Fd -j 4 -d app -f app.dir
# roles, tablespaces (not in per-database dumps)
pg_dumpall --globals-only -f globals.sql

# restore
psql -d postgres -f globals.sql
createdb -T template0 app
pg_restore -d app -j 4 --exit-on-error app.dump
```

- `pg_dump` takes a consistent snapshot without blocking writes, but it holds `ACCESS SHARE` locks on every dumped table for the whole run: concurrent `ALTER TABLE`, `DROP`, `TRUNCATE` on those tables wait, and the lock queue then blocks others (see [transactions-and-locking.md](transactions-and-locking.md#the-lock-queue-problem)). Schedule DDL away from dump windows.
- A long dump is a long transaction: it holds back vacuum cluster-wide. Run large dumps from a standby if possible (conflicts with replay may cancel it; see `max_standby_streaming_delay`).
- Use the `pg_dump` of the target (newer) version when dumping for an upgrade. On 19, dumps from older pg_dump of servers with `standard_conforming_strings = off` do not load.
- 18+: `pg_dump --statistics` includes optimizer statistics (avoids a slow `ANALYZE` after restore); `--no-policies` skips RLS policies. 19 adds extended statistics to dumps.
- Non-superuser dumps: grant `pg_read_all_data` (14+); on 19 it also covers large objects.
- After restoring: `vacuumdb --all --analyze-in-stages` unless statistics were included.

## Physical backups and WAL archiving

Enable archiving (restart required for `archive_mode`):

```
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /archive/%f && cp %p /archive/%f'   # example only: not durable, no fsync, local disk
# or 15+: archive_library = '<module>'   (cannot be set together with archive_command on 16+)
archive_timeout = 60s    # bounds data loss when traffic is low
```

The example command is the documented minimal pattern; production archiving must copy to separate storage, fsync, refuse to overwrite a different file with the same name, and return non-zero on any failure. Use a maintained archiving tool or module.

Take a base backup:

```bash
pg_basebackup -h db1 -U backup -D /backups/base-2026-11-27 \
  -Ft -z --wal-method=stream --checkpoint=fast --progress --manifest-checksums=SHA256
pg_verifybackup /backups/base-2026-11-27     # tar format verification needs 18+
```

- The `backup` role needs `REPLICATION` and a `replication` line in `pg_hba.conf`.
- `--wal-method=stream` includes the WAL needed to make the backup consistent; you still need the archive for PITR beyond the backup end.
- Server-side compression (15+): `--compress=server-zstd`.
- Custom tools using the low-level API call `pg_backup_start()` / `pg_backup_stop()` (15+ names; 14 uses `pg_start_backup()` / `pg_stop_backup()` and still has the removed exclusive mode).

Monitor archiving:

```sql
SELECT archived_count, last_archived_wal, last_archived_time,
       failed_count, last_failed_wal, last_failed_time
FROM pg_stat_archiver;
```

A growing `failed_count` with `pg_wal` filling up means the archive command fails; the server keeps WAL until it succeeds, so a broken archive eventually fills the disk.

## Incremental backups (17+)

1. Set `summarize_wal = on` (reload; default `off`, container 17 to 19). WAL summaries are kept for `wal_summary_keep_time` (default 10 days, container shows 14400 min).
2. Take a full backup with a manifest (default).
3. Take incrementals against the previous backup's manifest:

```bash
pg_basebackup -D /backups/incr-1 --incremental=/backups/full/backup_manifest
pg_basebackup -D /backups/incr-2 --incremental=/backups/incr-1/backup_manifest
```

4. Restore by combining the chain into a full data directory:

```bash
pg_combinebackup /backups/full /backups/incr-1 /backups/incr-2 -o /restore/data
```

Rules: every backup in the chain must exist and be in order; losing one breaks all later ones. `pg_combinebackup --link` (18+) hard-links unchanged files, so do not use the combined output and the source backups independently afterwards. On 19, `pg_stat_progress_basebackup.backup_type` shows `full` or `incremental`.

## Point-in-time recovery

1. Stop the server if running. Move the damaged data directory aside; do not delete it until recovery is verified.
2. Restore the base backup (or combined incremental) into an empty data directory; remove any WAL files copied from the old `pg_wal`.
3. Configure recovery in `postgresql.conf` (or `postgresql.auto.conf`):

```
restore_command = 'cp /archive/%f %p'
recovery_target_time = '2026-11-27 09:14:00+00'
recovery_target_action = 'pause'      # default; inspect before promoting
```

Other targets: `recovery_target_lsn`, `recovery_target_xid`, `recovery_target_name` (created with `pg_create_restore_point('before_migration')`), `recovery_target = 'immediate'` (end of backup). `recovery_target_inclusive` defaults to `on`.

4. Create `recovery.signal` in the data directory (`standby.signal` instead to build a standby). Start the server.
5. When it pauses at the target, connect and check the data. If correct: `SELECT pg_wal_replay_resume();` with `recovery_target_action = 'pause'` ends recovery and promotes. If you need a later target, stop, change the target, and start again (only forward).
6. After promotion the server is on a new timeline. Take a new base backup; old backups remain usable for the old timeline.

Common failures:

- `requested timeline ... is not a child of this server's history`: the archive mixes timelines; set `recovery_target_timeline` explicitly.
- Recovery stops early with "could not open file" from `restore_command`: a WAL segment is missing from the archive; recovery cannot pass the gap.
- Target time before the end of the base backup: choose an older base backup.

## Restore verification

A backup that has not been restored is unverified.

- Automate: restore the latest base backup and WAL to a scratch host on a schedule, recover to a recent point, start it, and run checks.
- Checks: `pg_verifybackup` on the backup; on the restored server, `SELECT count(*)` on critical tables compared with production at the recovery point; `amcheck` for B-tree consistency (`CREATE EXTENSION amcheck; SELECT bt_index_check(index => c.oid) FROM pg_index i JOIN pg_class c ON c.oid = i.indexrelid WHERE c.relam = (SELECT oid FROM pg_am WHERE amname = 'btree') LIMIT 100;`); `pg_checksums --check` on a stopped restored copy when checksums are enabled.
- Record recovery duration; it is your actual RTO.
- Logical dumps: restore with `pg_restore --exit-on-error` and compare row counts.

## Data checksums

Checksums detect storage corruption on read. `initdb` 18+ enables them by default; older clusters default to off (container: `data_checksums` off on 14 to 17 images, on for 18 and 19). Enable on an existing cluster with `pg_checksums --enable -D $PGDATA` while the server is stopped (time proportional to data size; rehearse). pg_upgrade requires both clusters to match.

## Common mistakes

- Backing up the data directory with `cp`/`rsync` while the server runs, without the backup API.
- Keeping backups on the same storage as the database.
- Monitoring that the backup job ran, not that a restore works.
- Forgetting `pg_dumpall --globals-only`: restored databases lack roles and grants.
- Retaining WAL archive for less time than the oldest base backup you might restore.
