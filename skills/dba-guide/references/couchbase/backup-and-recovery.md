# Couchbase Backup and Recovery

Checked: 2026-11-27 (sources at the end). Applies to Couchbase Server 7.2–8.0. Capella's managed backups are in [managed-services.md](managed-services.md).

## Tools and When to Use Each

| Tool | Edition | Use |
|---|---|---|
| `cbbackupmgr` (CLI) | Both; scope- and collection-level filters are EE-only | Scripted backups to local disk or object storage (S3 and others via `--obj-*`), restores, merges, and inspection. Also ships in a standalone tools package (7.2+). |
| Backup Service (cluster service `backup`) | EE (the `community-8.0.2` container's `allowedServices` is `kv`, `n1ql`, `index`, `fts`) | Scheduled plans and repositories managed from the UI or REST. 8.0 adds retention periods and prune tasks, and blocks deleting backups that incrementals depend on unless overridden. |
| XDCR to a standby cluster | EE | Continuous copy for disaster recovery. Not a backup: deletes and bad writes replicate too. |
| `cbexport` / `cbimport` | — | Logical JSON or CSV export and import of documents. No index, user, or settings metadata. |

`cbbackup` and `cbrestore` were removed in 7.6. Do not use them.

Hardware for `cbbackupmgr`: at least 4 cores and 8 GiB RAM. 16 cores, 16 GiB RAM, and SSD are recommended.

## What a Backup Contains

`cbbackupmgr` uses an archive (top directory, with `logs/backup.log`) holding repositories (one per cluster and backup configuration), each holding backups. All backups after the first are incremental, based on vBucket sequence numbers. Per bucket it saves, in order: bucket settings, view definitions, GSI definitions, Search index definitions, then key-value data.

Also included when the user has the roles: Eventing functions (`eventing_admin`), Search aliases (`fts_admin`), Analytics metadata (`analytics_admin`), Query UDFs, and the `_system` scope on 7.6+. `data_backup` alone cannot read these. Users and groups are included only when the repository is configured with `--enable-users` (7.6+); passwords are stored hashed.

Not included: encryption-at-rest settings (the saved bucket config omits them), XDCR replications and remote references, and cluster settings such as auto-failover, security, and memory quotas. Record those separately with REST dumps of `/settings/*` and `/pools/default`.

Consistency: each document is backed up consistently, but there is no consistency across documents and no point-in-time snapshot of the whole cluster. EE's `--consistency-check <seconds>` (developer preview) warns when the backup's consistency window is wider than the given number of seconds.

## Back Up

```sh
# One-time: create the repository
cbbackupmgr config --archive /backups/cb --repo prod
#   options: --enable-users (7.6+), --include-data / --exclude-data bucket[.scope[.collection]],
#            --disable-analytics, --disable-eventing, ... ; --capella for Capella clusters

# Each run: incremental by default
cbbackupmgr backup --archive /backups/cb --repo prod \
  --cluster couchbases://10.0.0.1 --username backup_user --password '***' \
  --cacert /etc/cb/ca.pem --threads 4 --no-progress-bar

# Force a new full backup into the same repository
cbbackupmgr backup ... --full-backup

# After a failed run: continue, or discard the partial backup (not both)
cbbackupmgr backup ... --resume
cbbackupmgr backup ... --purge
```

Container evidence (both versions): `cbbackupmgr config --archive /tmp/bk --repo r1`, then `backup ... --cluster couchbase://127.0.0.1 --no-progress-bar`, reported 5003 mutations received, 0 errored, 0 skipped. `info --archive /tmp/bk` then listed the repository. The 7.6.13 repository table had a "Point in Time" column; the 8.0.4 table had "Default Retention" in its place.

Settings:

- `--threads`: default 1. Do not exceed the CPU count of the backup host, and account for the number of cluster nodes.
- `--value-compression`: `compressed` (default), `uncompressed`, or `unchanged`.
- Object storage: `--archive s3://bucket/path` plus `--obj-staging-dir` on local disk. Do not use `/tmp` for the staging directory, and do not delete individual subdirectories of it.
- Encryption: encrypted repositories are GA in 7.6 (`--passphrase` or `--km-*` key-management options).
- Required role: Data Backup & Restore (`data_backup`) on the buckets, plus the service admin roles above to include their metadata. Full Admin covers everything.
- Do not run a backup or restore while changing major cluster configuration, such as the TLS mode. Runs during a rebalance are supported.

Retention and merges: incrementals accumulate. `cbbackupmgr merge` collapses a range of backups into one and removes duplicate versions. `cbbackupmgr merge -h` on both images lists required `--archive` (`-a`) and `--repo` (`-r`), and optional `--start`, `--end`, and `--date-range` (`30-01-2019,30-03-2019` in the help example). From 8.0, removing a backup that later incrementals depend on is blocked unless `--disable-safe-remove-check` (MB-60337). With the Backup Service in 8.0, set a repository retention period and schedule prune tasks.

## Inspect

```sh
cbbackupmgr info --archive /backups/cb                 # archive: repos, size
cbbackupmgr info --archive /backups/cb --repo prod     # backups in the repo
```

After each run, check that the newest backup exists, that per-bucket mutation counts are plausible, that the "Errored" counts are 0, and that `logs/backup.log` shows no failures.

## Restore

```sh
cbbackupmgr restore --archive /backups/cb --repo prod \
  --cluster couchbases://10.2.0.1 --username restore_user --password '***' --cacert /etc/cb/ca.pem \
  --start oldest --end latest --threads 4
```

Behavior that decides outcomes:

- Conflict resolution is on by default. The restore replays backups in time order and applies the target bucket's conflict resolution, so an item that is newer in the cluster is not overwritten (reported as "Skipped"). `--force-updates` overwrites regardless. It is also the only way to restore into a bucket with a different conflict-resolution policy.
- Expired documents: if the cluster still holds unpurged newer versions or tombstones, the restore skips those documents even with `--replace-ttl`, unless you add `--force-updates`. That flag applies to everything restored, so combine it with `--filter-keys` when possible. `--replace-ttl` does not override a collection or bucket `maxTTL`; adjust `maxTTL` or use `--preserve-collection-settings`.
- Indexes: GSI definitions are restored, but built only when restored to the same index node they came from. Otherwise they are created round-robin across Index nodes and left unbuilt. Place them, then run `BUILD INDEX` (see [indexes-and-queries.md](indexes-and-queries.md)). `--disable-gsi-indexes` skips them.
- Buckets: the target bucket must exist unless `--auto-create-buckets` is used. Restored bucket settings never include encryption at rest.
- Users: `--enable-users` (7.6+) restores users and groups but skips existing ones unless `--overwrite-users` is also given. A pre-8.0 backup restored into 8.0 needs the role fixes in [security.md](security.md) (MB-70629).
- Range: `--start` and `--end` take a 1-based index, a `day-month-year` date, a backup name, or `oldest`/`latest`. Each backup is the state as of when it was taken. There is no PITR to an arbitrary timestamp.
- Filtering and remapping: `--include-data`/`--exclude-data` (scope and collection level is EE-only), `--filter-keys '<RE2 regex>'`, `--filter-values`, and `--map-data 'src=dst,...'` (for example `app=app_restore` or `bucket3.scope1=bucket3.scope2`). Mapping a whole bucket into a collection restores only Data Service data.
- Failed restore: `--resume` continues, `--purge` restarts from zero. Neither deletes backup data.
- 8.0: `--auto-resolve-conflicts` remaps scopes and collections by name when their IDs clash with existing ones. Use it only when the names refer to the same data.

Production safety: a restore writes into a live bucket. Restore into a new bucket (`--map-data app=app_restore_20261127`) or a scratch cluster first, verify, then copy forward selectively. Use `--force-updates` only when you intend to roll documents back to older versions.

## Cross-Version Restores

| From → to | Note |
|---|---|
| 7.2 or older → 7.6+ | The `_system` scope can clash with an existing scope ID, with error `scope '<name>' with id 0x8 exists with a different name/id on the cluster, a manual remap using '--map-data' is required`. Fix with `--map-data bucket.scope=bucket.scope`. |
| pre-8.0 users → 8.0 | Users holding `security_admin_local`, `security_admin_external`, or `ro_admin` need manual correction after the restore (MB-70629) |
| 8.0 `cbbackupmgr` → 7.6 or earlier cluster with `--auto-create-buckets` | Broken in 8.0.0 because of a new setting; fixed in 8.0.1 (MB-70235) |
| 7.6.0–7.6.10 with CBO statistics on indexes whose keys contain `::` | Restore could fail; fixed in 7.6.11 and 8.0.3 (MB-70745) |
| Backups from `cbbackupmgr` before 6.5 (ForestDB format) | Not supported. Restore or merge them with `cbbackupmgr` 6.5.x–7.1.x first. |
| Self-managed → Capella | Use `--capella` (7.6+ tools) or the explicit `--disable-*` set; see [managed-services.md](managed-services.md) |
| Collection-aware backup → collection-unaware cluster | Only `_default._default` is restored |

## Verify a Restore

Run this on every restore drill, and regularly for each repository:

1. Restore into a scratch cluster or a mapped bucket.
2. Compare counts per collection. On the restored side, use `SELECT COUNT(*) FROM b.s.c` with `scan_consistency=request_plus`. Compare against the mutations reported by the backup and the source's per-collection item count. Unbounded counts can lag; see [data-modeling.md](data-modeling.md).
3. Spot-check documents by key, including recently changed ones near the backup time.
4. Build the restored indexes and confirm `system:indexes` shows every one `online`. Run `EXPLAIN` for the top application queries.
5. If users were restored, check them with `GET /settings/rbac/users`.
6. Record elapsed time. Restore duration, not backup duration, determines recovery time.

## Recovery Without a Backup

- Lost node with replicas present: fail over and rebalance. No restore needed.
- Every copy of some vBuckets lost and an XDCR target exists: `cbrecovery` copies the missing data back from the XDCR target.
- Logical damage replicated by XDCR (bad deploy, mass delete): XDCR does not help. Restore from `cbbackupmgr` into a side bucket and copy the affected keys back.

Sources: cbbackupmgr (https://docs.couchbase.com/server/current/backup-restore/cbbackupmgr.html), cbbackupmgr backup (https://docs.couchbase.com/server/current/backup-restore/cbbackupmgr-backup.html), cbbackupmgr restore (https://docs.couchbase.com/server/current/backup-restore/cbbackupmgr-restore.html), What's New 7.2, 7.6, and 8.0, Release Notes 7.6 and 8.0, XDCR Overview (https://docs.couchbase.com/server/current/learn/clusters-and-availability/xdcr-overview.html), Capella Backup and Restore (https://docs.couchbase.com/cloud/clusters/backup-restore.html), container outputs for 7.6.13 and 8.0.4, all checked 2026-11-27.
