# Redis Persistence, Backup, and Recovery

Checked: 2026-11-27 (sources at the end).

## Choose a Persistence Mode

| Mode | Data loss on crash | Cost | Use when |
|---|---|---|---|
| None (`save ""`, `appendonly no`) | Everything | No fork, no disk I/O | Pure cache that can be rebuilt; never with auto-restart on a primary that has replicas (see below) |
| RDB only | Writes since last snapshot (minutes) | Periodic fork + full write | Losing minutes is acceptable; fastest restart; compact backups |
| AOF `everysec` (+ RDB preamble) | About 1 second | Continuous append, background fsync, periodic rewrite fork | Default choice when data matters |
| AOF `always` | Only writes not yet replied to | fsync before every reply batch; much lower throughput | Rare; consider a managed durable store instead ([MemoryDB](managed-services.md#memorydb)) |
| RDB + AOF | AOF bound | Both | The docs' recommendation for "PostgreSQL-like" safety; RDB files remain the easy backup artifact |

Defaults on every official image checked (7.2 to 8.12): `save 3600 1 300 100 60 10000`, `appendonly no`, `appendfsync everysec`, `aof-use-rdb-preamble yes`, `stop-writes-on-bgsave-error yes`, `rdbcompression yes`, `rdbchecksum yes`. The image runs with `dir /data`.

When both RDB and AOF exist at startup, Redis loads the AOF, since it is the more complete. With `preload-file` set ([8.10](versions/8.10.md)), it loads only that file.

## Primaries Without Persistence

A primary with persistence off that auto-restarts comes back empty, and its replicas then sync to the empty dataset and lose their copy too. Sentinel can miss a fast restart. If a primary must run without persistence, disable automatic restart of the process, or make sure failover happens before it restarts.

## RDB

Mechanism: `BGSAVE` forks; the child writes a temporary file and renames it over `dump.rdb` when complete. The parent keeps serving; memory grows by copy-on-write pages touched during the save.

- `SAVE` blocks the server for the whole write. Do not run it on a live primary; use `BGSAVE`.
- A finished RDB is never modified, so copying `dump.rdb` while the server runs is safe.
- `stop-writes-on-bgsave-error yes` makes the primary reject writes after a failed background save. Keep it on and alert on it; turning it off hides a broken backup.
- Fork time scales with RSS and page-table size; see `latest_fork_usec` in [latency](latency-and-monitoring.md#fork-and-copy-on-write).

Evidence:

```
INFO persistence
# rdb_last_bgsave_status:ok        last result
# rdb_last_save_time:<epoch>       last success
# rdb_changes_since_last_save:N    writes at risk
# rdb_last_cow_size, current_cow_peak   copy-on-write cost
# rdb_saves, rdb_saves_consecutive_failures (8.x image)
LASTSAVE
```

## AOF and Multi-Part AOF

Since 7.0, AOF is a directory (`appenddirname`, default `appendonlydir`) with one base file (RDB or AOF format), one or more incremental files, and a manifest (`appendonly.aof.manifest`). A rewrite forks a child to write a new base while the parent opens a new incremental file; the manifest switch is atomic.

| `appendfsync` | Behavior |
|---|---|
| `always` | fsync after each batch before replying; group commit across parallel clients |
| `everysec` (default) | fsync once per second in a background thread; up to about 1 s lost |
| `no` | leave flushing to the kernel (about 30 s on Linux by default) |

Rewrite triggers: `auto-aof-rewrite-percentage 100` and `auto-aof-rewrite-min-size 67108864` (64 MB) on the 8.12 image. `BGREWRITEAOF` forces one. `no-appendfsync-on-rewrite no` keeps fsync during rewrites (safer, more latency on slow disks).

Turn AOF on for a server that has only RDB:

1. Back up the latest `dump.rdb` off the host.
2. `CONFIG SET appendonly yes` on the running server. This starts a rewrite that writes the current dataset to the new AOF.
3. Wait until `INFO persistence` shows `aof_rewrite_in_progress:0`, `aof_rewrite_scheduled:0`, `aof_last_bgrewrite_status:ok`.
4. Persist the setting in `redis.conf` (or `CONFIG REWRITE`).

Data loss trap: the persistence docs warn that just changing the config and restarting "can result in data loss". The likely mechanism (inference): with `appendonly yes` and no AOF yet, the server starts from an empty AOF instead of loading `dump.rdb`.

Truncated or corrupt AOF:

- Truncated last command: loaded anyway while `aof-load-truncated yes` (default). The log shows `AOF loaded anyway because aof-load-truncated is enabled`.
- Corruption in the middle: startup aborts. Copy the AOF directory first, run `redis-check-aof` without `--fix` to see the offset, then decide. `--fix` discards everything from the bad offset to the end.
- `aof-load-corrupt-tail-max-size` ([8.4](versions/8.6.md#changes-first-shipped-in-84)) allows automatic repair of a corrupted tail up to the given size; default 0 (off) on the 8.12 image.

## Backups

### RDB file copy (all versions)

```
redis-cli BGSAVE
# wait until rdb_bgsave_in_progress:0 and rdb_last_bgsave_status:ok
cp /data/dump.rdb /backup/dump-$(date +%Y%m%dT%H%M).rdb
sha256sum /backup/dump-*.rdb
```

Or pull a copy over the network from any node: `redis-cli -h <host> --rdb /backup/dump.rdb` (uses a replication sync; check the exit code). `redis-cli --functions-rdb` fetches only Function libraries.

### AOF directory copy (7.0+, before 8.10)

Copying the directory during a rewrite can produce an inconsistent set. Procedure:

1. `CONFIG SET auto-aof-rewrite-percentage 0` and do not run `BGREWRITEAOF`.
2. Wait for `aof_rewrite_in_progress:0`.
3. Copy or hard-link all files in `appenddirname`.
4. Restore the previous `auto-aof-rewrite-percentage`.

Hard links in step 3 keep the rewrite pause short, since Redis only appends to or replaces files in that directory.

### BACKUP command (8.10+)

`BACKUP` produces BASE (RDB snapshot) + INCR (writes after it) + manifest, whether or not AOF is enabled, without pausing rewrites by hand.

```
BACKUP START          # fork, write BASE, start pinning INCR
BACKUP LIST           # absolute paths of pinned files; copy BASE now
BACKUP SEAL           # freeze: hard-link INCR, write manifest
BACKUP LIST           # now includes INCR and manifest; copy them
BACKUP CLEANUP        # release files after the copy is verified
BACKUP STATUS         # any time
BACKUP ABORT          # cancel before SEAL
```

- Files go to `backupdirname` (default `backupdir`, relative to `dir`, startup-only).
- `backup-sealed-ttl 0` (default) keeps sealed files until `BACKUP CLEANUP`; disk fills if cleanup never runs.
- The restored state is the state at `SEAL`, not at `START`.
- In Cluster, start backups on nodes at different times so they do not all fork at once, then seal each.
- Replies on 8.10.3 and 8.12.0 with default settings: `START`, `SEAL`, `CLEANUP`, and `ABORT` reply `OK`. `STATUS` returns `state`, `error`, `start_time`, `end_time`; `state` is `incrementing` after `START`, `sealed` after `SEAL`, `idle` after `CLEANUP`, and `failed` with error `aborted by user` after `ABORT`. `LIST` returns `/data/backupdir/appendonly.aof.1.base.rdb` before `SEAL`, and that file plus `appendonly.aof.1.incr.aof` and `appendonly.aof.manifest` after it; `CLEANUP` deletes them and `LIST` is then empty. A second `START` returns `ERR A backup is already in progress, ABORT it first`; `ABORT` with nothing running returns `ERR No backup in progress`.

### Schedule and retention

Keep hourly snapshots for about two days and daily ones for one to two months, with timestamps in names, and copy at least one per day off the host and off the provider. Record size and checksum after transfer, and alert when a fresh backup does not arrive.

## Restore

Self-hosted, RDB or AOF directory, all versions:

1. Stop the target server (`SHUTDOWN NOSAVE` if its current data must not overwrite the file you are about to place; plain `SHUTDOWN` saves first).
2. Place the files in `dir`: `dump.rdb`, or the full `appenddirname` directory with its manifest. If AOF is enabled in the config, Redis loads the AOF directory and ignores `dump.rdb`; to restore from an RDB on an AOF-enabled server, start with `appendonly no`, then enable AOF online as above.
3. Start the server and wait for `loading:0` in `INFO persistence`.

8.10+: set `preload-file aof:/restore/appendonly.aof.manifest` or `preload-file rdb:/restore/dump.rdb` in the config. Redis loads only that target, skips the normal files, and aborts startup if the target cannot be loaded. Remove the setting from the config after the restore so the next restart uses normal persistence files; it cannot be cleared at runtime (`CONFIG SET preload-file` returns `can't set immutable config`). Observed on 8.12.0: a sealed `BACKUP` set copied to `/restore` and loaded with `--preload-file aof:/restore/appendonly.aof.manifest` returned both the key written before `START` and the one written before `SEAL`. The files must be readable by the server's user (`redis` in the official image); otherwise startup fails with `Fatal error: can't open the AOF manifest file /restore/appendonly.aof.manifest for reading: Permission denied`.

Point-in-time recovery: AOF supports timestamp annotations (`aof-timestamp-enabled`, default `no`, since 7.0). With it on, an AOF can be truncated to a timestamp before loading (`redis-check-aof --truncate-to-timestamp <ts>`; 8.12.0 usage line: `redis-check-aof [--fix|--truncate-to-timestamp $timestamp] <file.manifest|file.aof>`. `redis-check-aof --help` treats `--help` as a file name; run it without arguments to see the usage). Without AOF, the recovery point is the last RDB.

`FLUSHALL` also clears the RDB file and, when `save` is configured, writes an empty RDB. After an accidental `FLUSHALL` with AOF enabled and no rewrite since, stop the server, remove the trailing `FLUSHALL` from the last incremental AOF file, and restart; disable rewrites first if the server is still running. Protect `FLUSHALL`/`FLUSHDB` with ACLs.

## Verify a Restore

```
redis-check-rdb /restore/dump.rdb                        # structure and checksum
redis-check-aof /restore/appendonlydir/appendonly.aof.manifest   # multi-part set
redis-cli INFO keyspace          # compare key counts per db with the source
redis-cli DBSIZE
redis-cli --scan --count 1000 | head    # spot-check key names
redis-cli INFO persistence       # rdb_last_load_keys_loaded, rdb_last_load_keys_expired
```

Compare `INFO keyspace` of the restored instance with values recorded at backup time. `rdb_last_load_keys_expired` counts volatile keys that expired between backup and load; a large number after an old backup is expected, not corruption. Run application smoke reads against the restored copy before redirecting traffic.

## Common Mistakes

- Backing up only `dump.rdb` while AOF is enabled; on restore Redis prefers the AOF directory.
- Copying the AOF directory mid-rewrite (before 8.10, without the procedure above).
- Leaving `BACKUP` sealed files pinned (8.10+) until the disk fills.
- Running `SAVE` or `DEBUG RELOAD` on a production primary.
- Restoring a newer server's RDB into an older version; formats are not backward compatible (see [versions](versions/index.md#upgrade-paths)).
- Disk full: `aof_last_write_status:err` and `rdb_last_bgsave_status:err` stop writes; alert on both.

Sources: https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/, https://redis.io/docs/latest/operate/oss_and_stack/management/replication/, https://redis.io/docs/latest/commands/info/, https://redis.io/docs/latest/commands/flushall/, https://redis.io/docs/latest/develop/tools/cli/, https://raw.githubusercontent.com/redis/redis/7.0.0/00-RELEASENOTES, https://redis.io/docs/latest/develop/whats-new/8-4/, https://redis.io/docs/latest/develop/whats-new/8-10/ (checked 2026-11-27); images `redis:7.2` to `redis:8.12` config output (2026-11-27).
