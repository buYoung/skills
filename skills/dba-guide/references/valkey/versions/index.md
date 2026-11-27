# Valkey Versions

Checked: 2026-11-27 against the Valkey support table at https://valkey.io/topics/releases/ (section "List of supported versions").

## Support Status

Valkey uses `major.minor.patch` semantic versioning. Each minor version gets maintenance support (bug and security fixes) for 3 years from its first release. The minor version the project picks as the last minor of each major gets extended security support for 5 years from first release; the project decides which minor that is once the next major ships. On 2026-11-27 every series ever released is still supported, so no "most recent end-of-support series" exists to cover.

| Series | Release type | First release | Maintenance support ends | Security support ends | Latest patch (2026-11-27) | File |
| --- | --- | --- | --- | --- | --- | --- |
| 9.2 | minor, latest stable | 2026-11-19 | 2029-11-19 | 2031-11-19 | 9.2.1 (2026-11-25) | [9.2](9.2.md) |
| 9.1 | minor | 2026-05-19 | 2029-05-19 | 2031-05-19 | 9.1.4 (2026-11-18) | [9.1](9.1.md) |
| 9.0 | major | 2025-10-21 | 2028-10-21 | 2028-10-21 | 9.0.8 (2026-11-18) | [9.0](9.0.md) |
| 8.1 | minor (last minor of 8.x) | 2025-03-31 | 2028-03-31 | 2030-03-31 | 8.1.12 (2026-11-18) | [8.1](8.1.md) |
| 8.0 | major | 2024-09-15 | 2027-09-15 | 2027-09-15 | 8.0.13 (2026-11-18) | [8.0](8.0.md) |
| 7.2 | first Valkey series (fork of Redis OSS 7.2.4) | 2024-04-16 | 2027-04-16 | 2029-04-16 | 7.2.16 (2026-11-18) | [7.2](7.2.md) |

Reading the table:

- 8.0 and 9.0 have no security-only tail. Plan to leave 8.0 before 2027-09-15 and 9.0 before 2028-10-21.
- 7.2 and 8.1 carry the extended security window for their major. After the maintenance end date only security fixes the project considers exploitable ship.
- Security patches have shipped on the supported lines on the same day (2026-11-18 for CVE-2026-130822: 7.2.16, 8.0.13, 9.0.8, 9.1.4 and the other lines). Other patches do not: 9.2.1 (2026-11-25) shipped alone. When a CVE is announced, look for a patch on your line and upgrade within the line.
- Do not use 8.0.8: the project revoked it (tag on a commit outside the 8.0 branch); go from 8.0.7 directly to 8.0.9 or later.
- 9.2.0 GA is dated 2026-11-18 in the release notes and 2026-11-19 in the support table; the table date is used here.

## Identify the Running Version

Run these before answering any version-dependent question:

```
valkey-cli INFO server
valkey-server --version
valkey-cli MODULE LIST
valkey-cli CONFIG GET cluster-enabled
```

Read `INFO server` this way (fields confirmed in the official images, 2026-11-27):

| Field | Meaning |
| --- | --- |
| `server_name:valkey` | The server is Valkey. Redis prints no such field. |
| `valkey_version:9.2.1` | The real Valkey version. Base every decision on this. |
| `redis_version:7.2.4` | Fixed compatibility value on every Valkey release. Never read it as the Valkey version. |
| `valkey_release_stage:ga` | Present from 8.1 on; shows release-candidate builds. |
| `server_mode:standalone` | 8.0 and later. 7.2 prints `redis_mode:` instead, and so do 8.0+ with `extended-redis-compatibility yes`. |
| `availability_zone:` | 8.0 and later; value of the `availability-zone` config. |

Tools that parse `redis_version` misidentify Valkey as Redis 7.2.4. If a tool or client breaks on the Valkey identity, `extended-redis-compatibility yes` (added in 8.0, scheduled to stop having an effect and be removed in a future version) makes Valkey present itself as Redis; treat it as a temporary workaround. In the 8.0 to 9.2 images it changes `HELLO 3` from `server valkey`, `version <valkey version>` to `server redis`, `version 7.2.4`, and `INFO server` `server_mode:` to `redis_mode:`; `server_name:valkey` and `valkey_version` stay. Valkey 7.2 answers `HELLO` with `server redis` and its own version (`7.2.16`).

Edition and packaging checks:

- `MODULE LIST` is empty on 7.2 to 9.0 builds. From 9.1 the Lua engine is a module and appears as `name lua`. The `valkey/valkey-bundle` image adds `json`, `bf`, `search` and `ldap` modules; plain `valkey/valkey` images return `ERR unknown command` for `JSON.SET`, `BF.ADD`, `FT._LIST` (confirmed on all six tags).
- Binaries: images ship `valkey-*` binaries plus `redis-*` names for the same programs.
- Lua scripts can read `SERVER_NAME`, `SERVER_VERSION` and `SERVER_VERSION_NUM` (per the migration guide).

Managed services:

```
# ElastiCache node-based
aws elasticache describe-replication-groups --replication-group-id my-rg
aws elasticache describe-cache-clusters --show-cache-node-info \
  --query 'CacheClusters[].[CacheClusterId,Engine,EngineVersion]'
# ElastiCache Serverless
aws elasticache describe-serverless-caches --serverless-cache-name my-cache
# Engine versions offered in the Region
aws elasticache describe-cache-engine-versions --engine valkey
# MemoryDB
aws memorydb describe-clusters --cluster-name my-cluster
aws memorydb describe-engine-versions --engine valkey
```

ElastiCache and MemoryDB expose one version per minor and manage the patch level. MemoryDB returns the full patch in `EnginePatchVersion`; ElastiCache returns the patch in `CacheEngineVersionDescription` of `describe-cache-engine-versions`. ElastiCache versions are not always upstream numbers: ElastiCache "8.2 for Valkey" is upstream 8.1 plus the valkey-search module. Run `INFO server` on the node as well and compare `valkey_version`. Serverless caches report `MajorEngineVersion` and `FullEngineVersion` (ElastiCache API reference, `ServerlessCache` data type, checked 2026-11-27). See [managed-services.md](../managed-services.md).

## Upgrade Paths

Compatibility contract (from the release policy page):

| Step | What the project promises | What to do |
| --- | --- | --- |
| Patch (9.1.3 → 9.1.4) | Bug fixes only; mixed patch versions in a replication group or cluster are safe. | Rolling restart, replicas first. |
| Minor (9.0 → 9.1) | Backward compatible with default config; new commands or types used on a newer node can break older nodes. | Upgrade all nodes, then start using new features. Do not run mixed minors longer than the rollout. |
| Major (8.1 → 9.0) | May change command behavior, remove deprecated commands, change defaults. Replication from primary to replica always uses a backward-compatible format. | Read every release note between the versions; upgrade replicas before primaries. |

Direct paths:

- Any Valkey version can move directly to any later Valkey version; the release notes name no mandatory intermediate step. Read the notes of each skipped series.
- Redis OSS 2.x to 7.2.x can move to any Valkey version: the RDB/AOF formats and protocol are compatible (Valkey 7.2.4 forked from Redis OSS 7.2.4).
- Redis Community Edition 7.4 and later cannot move to Valkey through RDB/AOF files: the official migration guide states its data files are not compatible. Use a logical copy (a migration tool, or application dual writes) and rehearse it. See [persistence-and-recovery.md](../persistence-and-recovery.md).
- Mixed 9.0 and 9.1 nodes: use 9.1.3 or later on the 9.1 side (9.2.0 includes the same fix); earlier 9.1 patches had a listpack encoding incompatibility that broke RDB load and replication for some entry lengths.

Downgrade and rollback limits:

| Files written by | RDB version | Readable by |
| --- | --- | --- |
| Redis OSS 7.2, Valkey 7.2, 8.0, 8.1 | 11 | Valkey 7.2 and later, Redis OSS 7.2 |
| Valkey 9.0, 9.1 | 80 (magic string `VALKEY`) | Valkey 9.0 and later. Valkey 8.1 with `rdb-version-check relaxed` if no new types were written (8.1.12 loaded a strings-only 9.0.8 file and refused one with a field-TTL hash) |
| Valkey 9.2 | 81 | Valkey 9.2; 9.0/9.1 with `rdb-version-check relaxed` if no 9.2-only types or compression were written |

(Source: `src/rdb.h` at tag 9.2.1.) `rdb-version-check` exists from 8.1; 7.2 and 8.0 refuse newer files. Types that make a relaxed load fail include hashes with field TTLs (9.0, RDB type 22) and Path Hash (9.2, type 23). Streaming-compressed RDB (`rdbcompression lz4|zstd`, 9.2) can be read only by 9.2 and later. Because rollback by file is fragile, keep the pre-upgrade nodes or a pre-upgrade RDB until the new version has run through a full business cycle, and prefer rollback by failing back to old-version replicas that never received new-format data.

Generic upgrade procedure:

1. Pre-checks: `INFO server` (`valkey_version`) on every node; `CONFIG GET *` saved to a file; `ACL LIST`; `MODULE LIST`; `INFO persistence` (`rdb_last_bgsave_status:ok`, `aof_last_write_status:ok`); `INFO replication` (all replicas `online`, small lag); for clusters `CLUSTER INFO` (`cluster_state:ok`) and `valkey-cli --cluster check host:port`.
2. Read the "Upgrading Into This Series" section of every series file between the current and target version, and the upstream release notes of the target patch.
3. Rehearse on a copy restored from a current RDB with the same config file: start the target binary, check the log for rejected directives, run the application test suite and a replay of real traffic, compare `INFO keyspace` counts and `MEMORY STATS`.
4. Switch: upgrade and restart replicas one by one, wait for `master_link_status:up` and `master_sync_in_progress:0`; then fail over (`FAILOVER` on a standalone primary with replicas, `CLUSTER FAILOVER` on the replica in cluster mode, or `SENTINEL FAILOVER <name>`) and upgrade the old primary last.
5. Post-checks: `INFO server` on every node, `INFO errorstats`, `LATENCY LATEST`, `COMMANDLOG GET 10 slow` (8.1 and later) or `SLOWLOG GET 10`, `INFO memory` fragmentation and peak, a `BGSAVE` that completes, client error rates.
6. Only after every node runs the target version, enable new features and config options.

## Outside the Covered Range

- Older than 7.2 means the server is Redis OSS, not Valkey. Use the Redis reference ([../../redis/persistence-and-recovery.md](../../redis/persistence-and-recovery.md) and the other Redis files) and plan a move to a supported Valkey or Redis line.
- Newer than 9.2 (for example a 9.3 release candidate or 10.0): read `00-RELEASENOTES` on the matching branch in the valkey-io/valkey repository and the support table at https://valkey.io/topics/releases/. The release policy allows a major to change defaults and remove deprecated commands, so recheck every default quoted in these files, the RDB version table above, and any statement that a command or config exists "since" a version.
- In both cases state the version gap in the answer, name the release notes that were read, and mark which statements from this reference were not re-verified.

## Sources

- Valkey releases and versioning schema, support table — https://valkey.io/topics/releases/ — checked 2026-11-27
- Valkey download page, latest patch per line — https://valkey.io/download/ — checked 2026-11-27
- Valkey 9.2 release notes — https://raw.githubusercontent.com/valkey-io/valkey/9.2/00-RELEASENOTES — checked 2026-11-27
- Valkey 9.1 release notes — https://raw.githubusercontent.com/valkey-io/valkey/9.1/00-RELEASENOTES — checked 2026-11-27
- Valkey 9.0 release notes — https://raw.githubusercontent.com/valkey-io/valkey/9.0/00-RELEASENOTES — checked 2026-11-27
- Valkey 8.1 release notes — https://raw.githubusercontent.com/valkey-io/valkey/8.1/00-RELEASENOTES — checked 2026-11-27
- Valkey 8.0 release notes — https://raw.githubusercontent.com/valkey-io/valkey/8.0/00-RELEASENOTES — checked 2026-11-27
- Valkey 7.2 release notes — https://raw.githubusercontent.com/valkey-io/valkey/7.2/00-RELEASENOTES — checked 2026-11-27
- `src/rdb.h` at tag 9.2.1 (RDB version map) — https://raw.githubusercontent.com/valkey-io/valkey/9.2.1/src/rdb.h — checked 2026-11-27
- `valkey.conf` at branch 9.2 — https://raw.githubusercontent.com/valkey-io/valkey/9.2/valkey.conf — checked 2026-11-27
- `valkey.conf` at branch 8.0 — https://raw.githubusercontent.com/valkey-io/valkey/8.0/valkey.conf — checked 2026-11-27
- License file at branch 9.2 (BSD 3-Clause) — https://raw.githubusercontent.com/valkey-io/valkey/9.2/COPYING — checked 2026-11-27
- Migration from Redis to Valkey — https://valkey.io/topics/migration/ — checked 2026-11-27
- Atomic slot migration — https://valkey.io/topics/atomic-slot-migration/ — checked 2026-11-27
- Cluster specification — https://valkey.io/topics/cluster-spec/ — checked 2026-11-27
- Numbered databases in Valkey 9.0 (project blog) — https://valkey.io/blog/numbered-databases/ — checked 2026-11-27
- Valkey Bundle — https://valkey.io/topics/valkey-bundle/ — checked 2026-11-27
- ElastiCache engine versions — https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/engine-versions.html — checked 2026-11-27
- ElastiCache major version behavior differences for Valkey — https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/VersionManagementConsiderations-valkey.html — checked 2026-11-27
- ElastiCache cross-engine upgrades — https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/VersionManagement.HowTo.html — checked 2026-11-27
- ElastiCache upgrade considerations — https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/VersionManagement-upgrade-considerations.html — checked 2026-11-27
- ElastiCache engine parameters — https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/ParameterGroups.Engine.html — checked 2026-11-27
- ElastiCache supported and restricted commands — https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/SupportedCommands.html — checked 2026-11-27
- MemoryDB engine versions — https://docs.aws.amazon.com/memorydb/latest/devguide/engine-versions.html — checked 2026-11-27
- ElastiCache API reference, `ServerlessCache` data type (`MajorEngineVersion`, `FullEngineVersion`) — https://docs.aws.amazon.com/AmazonElastiCache/latest/APIReference/API_ServerlessCache.html — checked 2026-11-27
- MemoryDB Multi-Region prerequisites (Valkey engine version 7.3 and above) — https://docs.aws.amazon.com/memorydb/latest/devguide/multi-region.prereq.html — checked 2026-11-27
- Official images `valkey/valkey:7.2, 8.0, 8.1, 9.0, 9.1, 9.2` (image digests in the coverage record, `updates/2026-11-27-initial-coverage.md`): `CONFIG GET *`, `INFO`, and statement runs — run 2026-11-27
