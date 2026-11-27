# Redis Versions

Checked: 2026-11-27 against the Redis Open Source version management page (https://redis.io/docs/latest/operate/oss_and_stack/install/version-mgmt/).

Redis Open Source uses MAJOR.MINOR.PATCH. Within a major version there are two release types:

- Standard: the first minor of a major (8.0) and the intermediate minors (8.4, 8.6, ...). Security and critical fixes for 6 months after the next minor ships.
- Extended: the second minor of a major (8.2) and the final minor of a major. Security and critical fixes for 5 years from release.

The lifecycle table on the page is authoritative where it differs from that rule (8.0 is listed with an end date of 2026-12-01). The docs recommend running the newest version.

## Support Status

| Series | Release type | GA | End of support | Newest patch seen | File |
|---|---|---|---|---|---|
| 8.12 | Standard | 2026-11-22 | TBD | 8.12.0 (image) | [8.12](8.12.md) |
| 8.10 | Standard | 2026-07-29 | TBD | 8.10.3 (image) | [8.10](8.10.md) |
| 8.8 | Standard | 2026-05-25 | 2027-01-29 | 8.8.4 (image) | [8.8](8.8.md) |
| 8.6 | Standard | 2026-02-10 | 2026-11-25 (ended) | 8.6.8 (image) | [8.6](8.6.md) |
| 8.4 | Standard | 2025-11-18 | 2026-08-10 (ended) | 8.4.8 (image) | [8.6, 8.4 section](8.6.md#changes-first-shipped-in-84) |
| 8.2 | Extended | 2025-08-04 | 2030-09-01 | 8.2.11 (image) | [8.2](8.2.md) |
| 8.0 | Standard | 2025-05-02 | 2026-12-01 | 8.0.6 (image) | [8.0](8.0.md) |
| 7.4 | Extended | 2024-07-29 | 2029-12-01 | 7.4.12 (image) | [7.4](7.4.md) |
| 7.2 | Extended | 2023-08-15 | 2029-12-01 | 7.2.17 (image) | [7.2](7.2.md) |
| 6.2 | Extended | 2021-02-22 | 2027-04-01 | 6.2.24 (image; released 2026-08-17) | [6.2](6.2.md) |

GA dates come from the `00-RELEASENOTES` file at each GA tag; end dates come from the version management page. 8.6 is the most recent series past end of support. 8.4 is also past end of support; its changes are kept in the 8.6 file because every upgrade from 8.2 to 8.6 or later crosses them.

Plan now for: 8.0 ends 2026-12-01 (move to 8.2 for a long-lived line, or to 8.10/8.12); 8.8 ends 2027-01-29; 6.2 ends 2027-04-01.

License by series (details in [licensing](../licensing.md)): 7.2 and earlier BSD-3-Clause; 7.4 RSALv2 or SSPLv1; 8.0 and later RSALv2, SSPLv1, or AGPLv3 at the user's choice.

## Identify the Running Version

Self-hosted:

```
redis-cli INFO server          # redis_version, redis_mode, executable, config_file
redis-cli MODULE LIST          # 8.x: bundled bf, timeseries, search, ReJSON, vectorset
redis-cli INFO keysizes        # section exists from 8.0; empty reply on 7.x
redis-server --version         # without connecting: Redis server v=8.12.0 sha=00000000:1 malloc=jemalloc-5.3.0 bits=64 build=...
redis-cli --version            # redis-cli 8.12.0 (the client's version, not the server's)
```

Read the output:

- `redis_version:8.12.0` gives the series and patch. `redis_mode` is `standalone`, `cluster`, or `sentinel`.
- `server_name:valkey` and `valkey_version:` present means Valkey, not Redis. Valkey 9.2.1 reports `redis_version:7.2.4` for client compatibility, so never decide on `redis_version` alone. See [Valkey versions](../../valkey/versions/index.md).
- `MODULE LIST` on Redis 8 lists `bf`, `timeseries`, `search`, `ReJSON` with a `ver` that encodes the Redis version (8.12.0 image: `81200`; `search` `81201`) and `vectorset` with `ver 1` and no path. On the 6.2, 7.2, and 7.4 official images the list is empty; a 7.x server that lists `search` or `ReJSON` is Redis Stack or has modules loaded by hand.
- The RDB file format version is in the first 9 bytes of a dump: `head -c 9 dump.rdb`. Observed on the official images (`SAVE` of a plain string): 6.2.24 `REDIS0009`, 7.2.17 `REDIS0011`, 7.4.12, 8.0.6, 8.2.11, and 8.4.8 `REDIS0012`, 8.6.8 `REDIS0013`, 8.8.4 `REDIS0014`, 8.10.3 `REDIS0015`, 8.12.0 `REDIS0017`. `redis-check-rdb <file>` prints the writer's version as `AUX FIELD redis-ver = '8.12.0'`. Read both from a backup to see which server wrote it.

Managed services:

```
aws elasticache describe-cache-clusters --show-cache-node-info \
  --query 'CacheClusters[].[CacheClusterId,Engine,EngineVersion]'
aws elasticache describe-serverless-caches \
  --query 'ServerlessCaches[].[ServerlessCacheName,Engine,MajorEngineVersion,FullEngineVersion]'
aws memorydb describe-clusters \
  --query 'Clusters[].[Name,Engine,EngineVersion,EnginePatchVersion]'
```

`INFO server` also works on ElastiCache and MemoryDB node-based clusters; the reported version is the compatible open-source version, not the managed version label (ElastiCache 7.1 for Redis OSS is compatible with Redis OSS 7.0). See [managed services](../managed-services.md).

## Upgrade Paths

Supported paths, from the 8.0 GA release notes: upgrade to 8.x by replication or by persistence from earlier Redis versions with or without the RediSearch, RedisJSON, RedisTimeSeries, and RedisBloom modules, and from Redis Stack 7.2 or 7.4. No intermediate series is required; the version files list what changes along the way.

Downgrade limits:

- A newer server writes RDB files that an older server cannot load. 7.0 moved to RDB format 10 and 7.2 to format 11, each documented as incompatible with older versions. Observed: the server refuses at startup any RDB with a higher format number than its own, even one holding only a plain string, and exits (`Can't handle RDB format version 12` then `Fatal error loading the DB, check server logs. Exiting.` for a 7.4.12 file on 7.2.17; `... version 17` for an 8.12.0 file on 8.2.11). 7.4 through 8.4 share format 12: 7.4.12 loaded 8.2.11 and 8.4.8 files containing a string and a hash with a field TTL. Files with data types the older server lacks were not tested.
- A replica can replicate from an older primary, not the reverse: full sync sends an RDB in the primary's format. Rollback after the switch means restoring a pre-upgrade backup, or keeping an old-version node that you stopped replicating before the switch; you cannot re-point an old node at the new primary.
- Data types that do not exist in the old series (hash field TTLs from 7.4, vector sets and bundled JSON from 8.0, arrays from 8.8, compact hashes from 8.10, set member TTLs from 8.12) make a downgrade lossy or impossible. Once applications use them, the upgrade is one-way.

Generic procedure:

1. Pre-checks: record `INFO server`, `INFO persistence`, `INFO replication`, `CONFIG GET *`, `ACL LIST`, `MODULE LIST`, `FUNCTION LIST`. Read the "Upgrading Into This Series" section of every version file between the current and target series. Check client library support for the target version (RESP3, new error replies).
2. Rehearse on a restored copy: start the target version with a copy of the production RDB or AOF directory, compare `DBSIZE` and `INFO keyspace`, replay a traffic sample, and check `ACL LOG` and `INFO errorstats` for new `NOPERM` or syntax errors. This catches ACL category changes (8.0) and removed commands.
3. Switch, standalone or Sentinel: add a replica on the target version, wait for `master_link_status:up` and matching offsets, then fail over (`SENTINEL FAILOVER <name>`, or `FAILOVER` on the primary since 6.2). Upgrade the old primary last.
4. Switch, Cluster: upgrade replicas first; for each primary run `CLUSTER FAILOVER` on an upgraded replica, wait for the role change, then upgrade the old primary. One node at a time. Mixed-version clusters are a transition state only.
5. Post-checks: `INFO server` version on every node, `INFO replication` offsets, `CLUSTER INFO` `cluster_state:ok`, `latest_fork_usec` after the first `BGSAVE`, `INFO errorstats`, `SLOWLOG GET`, and client error rates. Keep the pre-upgrade backup until new data types are in use.

## Outside the Covered Range

Older than 6.2 (for example 6.0, 5.0): end of life upstream. Read `00-RELEASENOTES` on the 6.2, 7.0, and 7.2 branches of https://github.com/redis/redis before planning; expect RDB format, ACL default, and AOF layout changes (multi-part AOF from 7.0). Claims in this reference about ACL selectors, multi-part AOF, `WAITAOF`, listpack encodings, and Functions do not hold.

7.0 (not covered; ended before this check): treat as 6.2-to-7.2 territory and use [7.2](7.2.md), which lists the 7.0 changes.

Newer than 8.12 (for example 8.14 or 9.x): read https://redis.io/docs/latest/develop/whats-new/ and the GitHub release notes for each series after 8.12. Defaults, eviction and persistence features, and ACL categories in this reference may have changed; a new major version may break compatibility.

Redis Stack, Redis Software, Redis Cloud: different products. Module versions in Redis Stack do not follow the Redis version; Redis Software has its own lifecycle. This reference covers Redis Open Source only.

Every answer about a server outside the covered range must state the version gap and name the release notes it relied on.

## Sources

- Redis Open Source version management (support table, release types) — https://redis.io/docs/latest/operate/oss_and_stack/install/version-mgmt/ — checked 2026-11-27
- Redis licensing overview — https://redis.io/legal/licenses/ — checked 2026-11-27
- 00-RELEASENOTES at tag 8.12.0 (GA 2026-11-22) — https://raw.githubusercontent.com/redis/redis/8.12.0/00-RELEASENOTES — checked 2026-11-27
- 00-RELEASENOTES at tag 8.10.0 (GA 2026-07-29) — https://raw.githubusercontent.com/redis/redis/8.10.0/00-RELEASENOTES — checked 2026-11-27
- 00-RELEASENOTES at tag 8.8.0 (GA 2026-05-25) — https://raw.githubusercontent.com/redis/redis/8.8.0/00-RELEASENOTES — checked 2026-11-27
- 00-RELEASENOTES at tag 8.6.0 (GA 2026-02-10) — https://raw.githubusercontent.com/redis/redis/8.6.0/00-RELEASENOTES — checked 2026-11-27
- 00-RELEASENOTES at tag 8.4.0 (GA 2025-11-18) — https://raw.githubusercontent.com/redis/redis/8.4.0/00-RELEASENOTES — checked 2026-11-27
- 00-RELEASENOTES at tag 8.2.0 (GA 2025-08-04) — https://raw.githubusercontent.com/redis/redis/8.2.0/00-RELEASENOTES — checked 2026-11-27
- 00-RELEASENOTES at tag 8.0.0 (GA 2025-05-02, upgrade paths) — https://raw.githubusercontent.com/redis/redis/8.0.0/00-RELEASENOTES — checked 2026-11-27
- 00-RELEASENOTES at tag 7.4.0 (GA 2024-07-29) — https://raw.githubusercontent.com/redis/redis/7.4.0/00-RELEASENOTES — checked 2026-11-27
- 00-RELEASENOTES at tag 7.2.0 (GA 2023-08-15, RDB format 11) — https://raw.githubusercontent.com/redis/redis/7.2.0/00-RELEASENOTES — checked 2026-11-27
- 00-RELEASENOTES at tag 7.0.0 (RDB format 10, breaking changes) — https://raw.githubusercontent.com/redis/redis/7.0.0/00-RELEASENOTES — checked 2026-11-27
- 00-RELEASENOTES on branch 6.2 (6.2.0 GA 2021-02-22, 6.2.24 on 2026-08-17) — https://raw.githubusercontent.com/redis/redis/6.2/00-RELEASENOTES — checked 2026-11-27
- What's new pages for 8.0 to 8.12 — https://redis.io/docs/latest/develop/whats-new/ — checked 2026-11-27
- Scale with Redis Cluster (rolling upgrade procedure) — https://redis.io/docs/latest/operate/oss_and_stack/management/scaling/ — checked 2026-11-27
- Redis administration (upgrade without downtime) — https://redis.io/docs/latest/operate/oss_and_stack/management/admin/ — checked 2026-11-27
- Amazon ElastiCache engine versions — https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/engine-versions.html — checked 2026-11-27
- AWS CLI describe-serverless-caches — https://docs.aws.amazon.com/cli/latest/reference/elasticache/describe-serverless-caches.html — checked 2026-11-27
- AWS CLI memorydb describe-clusters — https://docs.aws.amazon.com/cli/latest/reference/memorydb/describe-clusters.html — checked 2026-11-27
- Official image runs (`redis:6.2` to `redis:8.12`, arm64; digests in the coverage record, `updates/2026-11-27-initial-coverage.md`): `redis-<tag>-battery.txt`, `redis-<tag>-config.txt`, `redis-<tag>-binaries.txt`; `valkey-9.2-info.txt` for the Valkey identification fields; RDB header, downgrade-load, and `--version` checks — run 2026-11-27
