# MongoDB Backup and Recovery

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)). Atlas backups are in [managed-services](managed-services.md#backups-and-restore).

## Choose a method

| Method | Consistency | PITR | Impact | Use when |
| --- | --- | --- | --- | --- |
| Atlas Cloud Backup (snapshots, plus continuous backup for PITR) | managed | yes, within the restore window | managed | Atlas clusters |
| Ops Manager / Cloud Manager backup | guaranteed, including sharded clusters with the balancer and transactions running | yes | low | self-managed Enterprise Advanced (Ops Manager) or Enterprise Server (Cloud Manager) |
| Filesystem / volume snapshots (LVM, EBS, SAN) | consistent per node if journal and data share the volume, else needs `fsyncLock` | no (pair with oplog capture) | low per snapshot; sharded needs coordinated snapshots | large data sets, fast restores |
| `cp`/`rsync` of `dbPath` | only with writes stopped | no | high | small systems without snapshot support |
| `mongodump` / `mongorestore` | point-in-time only with `--oplog` on a replica set member | limited (dump plus its oplog slice) | reads all data through the cache; slow restore with index rebuilds | small deployments, logical exports, single collections |

The manual calls `mongodump` a tool for small deployments and rates its RTO and RPO as high. For anything large or sharded, use snapshots or Ops Manager/Atlas.

## mongodump and mongorestore

What is and is not in a dump:
- Documents, collection options, and index definitions (`<coll>.metadata.json`). Index data is not dumped; `mongorestore` rebuilds the indexes.
- Views are dumped as metadata only, unless you pass `--viewsAsCollections`.
- Collections using CSFLE or Queryable Encryption cannot be dumped meaningfully: `mongodump` does not decrypt.
- Restore into the same major version or FCV as the source.

Replica set dump at a single point in time:

```bash
mongodump --uri "mongodb://backup@host1,host2,host3/?replicaSet=rs0&authSource=admin" \
  --readPreference=secondary --oplog --gzip --archive=/backups/rs0-$(date +%F).archive
```

- `--oplog` needs a full-instance dump. It fails with `--db`, `--collection`, `--query`, or `--dumpDbUsersAndRoles`.
- The dump fails if any of the following run during it:
  - `renameCollection`;
  - `$out`;
  - `mapReduce`;
  - user, role, or privilege changes;
  - cluster-wide settings changes such as `setDefaultRWConcern`.
- `--oplog` has no effect against `mongos`.
- `--numParallelCollections` defaults to 4. `--readPreference` defaults to `primary`; read from a secondary to protect the primary's cache. `maxStalenessSeconds` must be at least 90.
- With time series collections, do not change FCV between 8.x and 9.0 while the dump runs. Database Tools 100.18.0+ fail the dump instead of producing an unrestorable one.

Restore:

```bash
mongorestore --uri "mongodb://restore@target/?authSource=admin" --gzip \
  --archive=/backups/rs0-2026-11-27.archive --oplogReplay
```

- `--oplogReplay` applies the captured oplog slice so the restore matches the dump's end time. It cannot replay across a time series format conversion.
- When restoring a sharded-cluster dump into a replica set, exclude config: `mongorestore --nsExclude='config.*' /path`.
- Index rebuilds dominate restore time on large collections. Measure them in rehearsal.
- Destructive option: `--drop` drops each target collection before restoring it. Use it only against a target you intend to overwrite. On the 7.0, 8.0, 8.3, and 9.0 images (Database Tools 100.20.1 ship in the image), `mongorestore --nsFrom='dbaverify.*' --nsTo='restored.*' --drop` restored `restored.orders` with 50000 documents and left the source `dbaverify.orders` untouched.
- Renaming and oplog replay do not combine: adding `--oplogReplay` to a restore with `--nsFrom`/`--nsTo` fails with `cannot use --oplogReplay with namespace renames specified` (Database Tools 100.20.1).

## Filesystem snapshots

Requirements for a usable snapshot of a running `mongod`:

- Every write acknowledged before the snapshot must be on disk, in the journal or the data files. WiredTiger data files reflect the last checkpoint (every 60 s; the snapshot tutorial says "every 2 GB of data or every minute"), and the journal covers the rest.
- If the journal is on the same volume as the data files, one snapshot of that volume is crash-consistent; no lock is needed.
- If the journal is on a separate volume, or the data spans several volumes, you must stop writes. Run `db.fsyncLock()`, snapshot all the volumes, then run `db.fsyncUnlock()`. Do this on a hidden secondary that serves no reads.

Note on sources: the backup overview says the journal must be on the same logical volume. The snapshot tutorial says WiredTiger data and journal no longer have to share a volume, provided you lock as above. Both lead to the same rule.

LVM example (run as root; `--size` reserves space for changes made during the snapshot's life, and an overflowing snapshot becomes unusable):

```bash
lvcreate --size 100M --snapshot --name mdb-snap01 /dev/vg0/mongodb
umount /dev/vg0/mdb-snap01 2>/dev/null; dd if=/dev/vg0/mdb-snap01 | gzip > /backups/mdb-snap01.gz
```

Restore: write the image to a new logical volume, mount it at the `dbPath`, remove the stale `mongod.lock` (mandatory if the snapshot was taken under `fsyncLock`), and start `mongod`. Never block-copy a mounted filesystem.

Encrypted storage engine (Enterprise): a restore from a hot backup rolls the database key over automatically. After a restore from a cold copy, start once with `--eseDatabaseKeyRollover`.

## Sharded clusters

Snapshots or dumps of a sharded cluster must capture every shard and the config server at about the same moment, with migrations stopped:

1. Pick a window with no migrations, resharding, or DDL.
2. `sh.stopBalancer()` on `mongos`. Wait until `sh.isBalancerRunning().mode` is `"off"`.
3. `db.getSiblingDB("admin").fsyncLock()` on `mongos` (7.0.2+). This blocks writes cluster-wide. Confirm the lock on `mongos` and on the config server primary. It needs the `fsync` privilege, for example through `hostManager`.
4. Take the backup: `mongodump` against `mongos`, or snapshots of every shard plus the config server.
5. `db.getSiblingDB("admin").fsyncUnlock()`. Confirm on both.
6. `sh.startBalancer()`. Check that `sh.getBalancerState()` is `true`.

Production impact: steps 3 to 5 stop all writes. For live sharded clusters with transactions, the manual points to Atlas, Cloud Manager, or Ops Manager, which back up without stopping the balancer.

## Point-in-time recovery

- Atlas: enable Continuous Cloud Backup. The restore window cannot exceed the hourly snapshot retention. Restore by date/time (one-minute precision) or by oplog timestamp (one-second precision).
- Ops Manager / Cloud Manager: snapshot plus oplog, managed by the tool.
- Self-managed without those tools: restore the last snapshot or dump, then replay oplog entries from a surviving member or an archived oplog up to the target timestamp. `mongorestore --oplogReplay --oplogLimit <time_t>:<ordinal>` does this; `--oplogFile` points at an oplog file outside the dump directory. Sharded clusters do not support `--oplogReplay`, and it fails with `--db`, `--collection` or `--nsInclude` (mongorestore page). Rehearse it. Keep the oplog window longer than your snapshot interval, or archive the oplog continuously.

## Verify restores

A backup is unproven until a restore from it has been checked:

1. Restore to an isolated host or cluster with the same major version and FCV.
2. Start it. Check the log for recovery messages and errors.
3. Compare per-collection counts against the source at the backup time: `db.getCollectionNames().map(c => [c, db[c].estimatedDocumentCount()])`.
4. Run `db.<coll>.validate({ full: true })` on critical collections. It takes an exclusive `W` lock on the collection and blocks reads and writes until it finishes (validate page); run it only on the restored copy. On 8.3+ it no longer turns on `checkBSONConformance` automatically; add it if needed. It also reports documents over 16 MB.
5. Run the application's smoke queries and compare a sample of documents.
6. Record the restore duration as the measured RTO.

Common mistakes:
- Dumping from the primary at peak.
- Assuming a `cp` of a running `dbPath` is usable.
- Forgetting users and roles: a full-instance `mongodump` always includes them; a `--db` dump needs `--dumpDbUsersAndRoles` (mongodump page).
- Restoring into a different FCV.
- Never timing a restore.
