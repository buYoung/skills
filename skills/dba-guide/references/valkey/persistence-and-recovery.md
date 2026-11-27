# Valkey Persistence and Recovery

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)).

RDB snapshots, AOF (multi-part AOF with `appenddirname`), `appendfsync` choices, `stop-writes-on-bgsave-error`, restore by file copy and restore verification work as in Redis OSS 7.2. Read [../redis/persistence-and-recovery.md](../redis/persistence-and-recovery.md) for the mechanism.

## Defaults (all six series, official images)

| Setting | Value |
| --- | --- |
| `save` | `3600 1 300 100 60 10000` |
| `appendonly` | `no` |
| `appendfsync` | `everysec` |
| `aof-use-rdb-preamble` | `yes` |
| `rdbcompression` | `yes` (per-string LZF) |
| `rdbchecksum` | `yes` |
| `rdb-version-check` | `strict` (setting exists from 8.1) |
| `forkless-policy` | `require-fork` (9.2) |

The official container runs with `dir /data` and no config file. Mount `/data` on persistent storage or snapshots disappear with the container.

## RDB format versions decide restore and rollback

| Writer | RDB version | Magic |
| --- | --- | --- |
| Redis OSS ≤ 7.2, Valkey 7.2, 8.0, 8.1 | ≤ 11 | `REDIS` |
| Redis CE 7.4 and later | 12 and up (reserved as foreign in Valkey) | `REDIS` |
| Valkey 9.0, 9.1 | 80 | `VALKEY` |
| Valkey 9.2 | 81 | `VALKEY` |

Rules:

- A restore target must run the same or a newer Valkey version than the writer. `rdb-version-check relaxed` (8.1+) makes a best-effort attempt at newer files and aborts at the first unknown type (hash with field TTLs, Path Hash) or opcode. In the images, 8.1.12 with `relaxed` loaded a 9.0.8 file (magic `VALKEY080`) that held only strings (log: `Loading RDB produced by Valkey version 9.0.8`), and exited on a 9.0.8 file with a field-TTL hash (`Unknown RDB encoding type 22`); with `strict` it exits with `Can't handle RDB format version 80`. 7.2 and 8.0 have no relaxed mode.
- Valkey refuses Redis CE 7.4+ files (versions 12 to 79 are "foreign"). Move such data logically with a migration tool or by having the application rewrite it.
- `DUMP`/`RESTORE` payloads carry only the RDB version number, no magic string; the same version rules apply to `RESTORE` and `MIGRATE`, and `rdb-version-check` also applies to replication and `RESTORE`.
- Check a file before restoring: `valkey-check-rdb /path/dump.rdb`. For AOF directories run `valkey-check-aof --fix <manifest>` only on a copy (it truncates). Since the November 2026 patches (7.2.16, 8.0.13, 8.1.12, 9.0.8, 9.1.4, 9.2.0) a torn AOF annotation after a crash is treated as a short read that `aof-load-truncated yes` recovers.

## Forkless snapshots (9.2)

Fork-based saves duplicate every memory page written during the save (copy-on-write). On write-heavy primaries this sets the memory headroom you must reserve. 9.2 can save from a background thread instead:

```
# valkey.conf (startup only)
forkless-infrastructure-enabled yes     # immutable, +4 bytes per key
forkless-policy prefer-forkless         # runtime-changeable; prefer-forkless needs the line above at startup
```

- `prefer-forkless` falls back to fork when forkless is not possible; `require-fork` keeps the old behavior. Without the startup line, `CONFIG SET forkless-policy prefer-forkless` fails with `'prefer-forkless' can only be selected when the server was started with 'forkless-infrastructure-enabled yes'`.
- Full syncs to replicas can also run forkless.
- Watch the `INFO persistence` fields for the save method and progress (`rdb_last_bgsave_type:forkless` or `fork`, `forkless_estimated_seconds_remaining`); fallback counters (`forkless_fallbacks_*`) are in `INFO debug`.
- Risk: 9.2.0 and 9.2.1 contain many fixes for forkless saves (corrupted set members under concurrent `ZUNION`, `SWAPDB` during a save, crashes with module threads). Enable it first on a replica, run `valkey-check-rdb` and restore tests on forkless-written files, and keep `forkless-policy require-fork` as the rollback.

## Compression (9.2)

| Option | Effect | Compatibility |
| --- | --- | --- |
| `rdbcompression yes` / `lzf` | per-string LZF inside the RDB | all versions |
| `rdbcompression lz4` | whole-file LZ4 stream | readable by 9.2+ only |
| `rdbcompression zstd` | whole-file Zstandard stream (build with zstd) | readable by 9.2+ only |
| `repl-compression lz4` / `zstd` / `yes` | compress steady-state replication | negotiated per replica; older replicas get plaintext |

Since 9.2 the two settings are independent; disk-based full sync follows `rdbcompression`. Compressed full-sync RDBs can serve as AOF bases. Before enabling file compression, make sure every restore target (DR site, analytics loader, the `valkey-check-rdb` you use) runs 9.2.

## Save behavior changes to know

- 9.2: active expiration counts as a change for `save` points, so TTL-heavy datasets trigger snapshots more often.
- 8.1: `BGSAVE CANCEL` stops a running or scheduled save. Use it when a fork is about to push the host into swap.
- 9.0: replicas save the RDB to disk on a background thread.
- 9.1: replicas can reuse the RDB from a disk-based full sync as the AOF preamble.

## Backup and restore procedure (self-hosted)

1. Take the backup on a replica: `BGSAVE`, poll `INFO persistence` until `rdb_bgsave_in_progress:0` and `rdb_last_bgsave_status:ok`, then copy the file at `dir`/`dbfilename` with a checksum.
2. Record `valkey_version` with the backup; it sets the minimum restore version.
3. Verify: start a scratch server of the same version on the copy (`valkey-server --dir /restore --dbfilename dump.rdb --appendonly no --port 0 --unixsocket /tmp/r.sock`), compare `INFO keyspace` with the source at backup time, sample keys with `TYPE`, `TTL`, `MEMORY USAGE`.
4. Restore: stop the target, place the file, start with `appendonly no` when the AOF directory is empty or stale (otherwise the AOF wins), then `CONFIG SET appendonly yes` to build a new AOF from memory.

Production safety: `SAVE` blocks the server for the whole dump; run `BGSAVE` on replicas. A plain `FLUSHALL`/`FLUSHDB` follows `lazyfree-lazy-user-flush` (`yes` from 8.0, `no` on 7.2, see [memory-and-configuration.md](memory-and-configuration.md)); pass `ASYNC` explicitly on older or customized servers.

## Migration from Redis

| Source | Method |
| --- | --- |
| Redis OSS 2.x – 7.2.x standalone | copy RDB after `SAVE` (downtime), or `REPLICAOF redis-host port` then `REPLICAOF NO ONE` (near-zero downtime), or `MIGRATE ... COPY REPLACE KEYS` for a subset |
| Redis OSS ≤ 7.2 cluster | add Valkey nodes as replicas, `CLUSTER FAILOVER` on each, remove the Redis nodes |
| Redis CE 7.4+, Redis 8.x | no file or replication path; logical copy only |

Details and verification: https://valkey.io/topics/migration/ and [versions/7.2.md](versions/7.2.md). Disable AOF on the first Valkey start from a copied RDB.
