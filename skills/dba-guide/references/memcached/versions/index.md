# Memcached Versions

Checked: 2026-11-27. The project publishes no lifecycle or support page. The evidence used is the release list at https://github.com/memcached/memcached/wiki/ReleaseNotes and the "latest stable" statement on https://memcached.org/.

## Support Status

Memcached has a single development line. memcached.org names one "latest stable" release; release notes give no end-of-support dates and no promise to back-port fixes to older releases. Treat only the newest 1.6.x patch as upstream-supported; older patches get fixes only through an OS vendor or a managed service.

| Series | Release type | First release | Latest release (2026-11-27) | End of support | File |
| --- | --- | --- | --- | --- | --- |
| 1.6 | single rolling stable line | 1.6.0, 2020-03-08 | 1.6.45, 2026-07-09 | not published; superseded patch by patch | [1.6](1.6.md) |
| 1.5 | previous line | 1.5.0, 2017-07-21 | 1.5.22, 2020-02-01 | not published; no release since 1.6.0 | none (see below) |

The official `memcached:1.6` image runs 1.6.45 (`version` → `VERSION 1.6.45`, 2026-11-27).

## Identify the Running Version

```
printf 'version\r\nquit\r\n' | nc host 11211      # VERSION 1.6.45
printf 'stats\r\nquit\r\n' | nc host 11211 | grep -E 'version|libevent|threads|max_connections'
printf 'stats settings\r\nquit\r\n' | nc host 11211
memcached -V                                       # on the host
memcached -h | head -1                             # also prints the version
```

- `stats` shows `version`, `libevent`, `pointer_size`, `threads`, `max_connections`.
- `stats settings` shows build and runtime features: `ssl_*` lines appear in TLS-capable builds, `ext_*` lines in extstore-capable builds, `proxy_enabled` reports the proxy. A build without a feature omits or nulls those lines; `stats extstore` returns only `END` when extstore is compiled but no `ext_path` is configured (official image).
- There are no editions. Distribution packages may lag the upstream patch.
- ElastiCache: `aws elasticache describe-cache-clusters --cache-cluster-id my-mc --show-cache-node-info` returns `Engine: memcached` and `EngineVersion` (for example `1.6.22`); `aws elasticache describe-cache-engine-versions --engine memcached` lists offered versions. On ElastiCache Serverless only `stats` and `stats reset` work. See [managed-services.md](../managed-services.md).

## Upgrade Paths

- Any 1.x release can be replaced by any later release; there is no on-disk format to migrate. The upgrade is a process restart, and the cache starts empty unless warm restart is in use.
- Warm restart (`-e <file on tmpfs or DAX>`, since 1.5.18): stop with `SIGUSR1`, start the new binary with the same `-e` file and compatible settings; the cache survives. Changing `-m`, `-I` (max item size), slab chunk sizes, CAS on/off or slab reassignment starts empty. Restart is not possible from versions older than 1.5.18. Warm restart does not work together with extstore.
- Downgrade is a restart with the older binary; the same warm-restart compatibility rules apply.

Generic procedure for a pool of servers:

1. Pre-checks: record `stats`, `stats settings`, `stats slabs`, `stats items` per node; note `get_hits`/`get_misses` and database load as the baseline.
2. Read the release notes of every patch between current and target; look for protocol output changes (for example 1.6.43 added an `OK` line to `lru_crawler metadump` and `mgdump`) and start-option changes.
3. Rehearse on one canary node with production traffic for at least a full TTL cycle; the project author explicitly advised canary rollout for 1.6.45.
4. Roll node by node, waiting for the hit ratio to recover before the next node. Each restarted node without warm restart is a full miss storm for its share of keys; with consistent hashing on clients the blast radius is about 1/N of keys. Schedule during low database load.
5. Post-checks: `version`, `stats settings` identical to the pre-check except intended changes, `listen_disabled_num` 0, hit ratio back to baseline.

## Outside the Covered Range

- 1.5.x and older: upgrade to the latest 1.6. Differences that matter: 1.6.0 compiled extstore by default, completed the meta protocol and deprecated the binary protocol; 1.6.0 cut idle connection memory from about 4.5 KB to 400–500 bytes. Read https://github.com/memcached/memcached/wiki/ReleaseNotes for each skipped release. Claims in [guide.md](../guide.md) about meta flags, proxy and the security fixes of 2026 do not hold for 1.5.
- Newer than 1.6.45 (a later 1.6 patch or a 1.7/2.0 line): read the release notes linked from memcached.org, recheck `memcached -h` and `stats settings` defaults against the tables in [guide.md](../guide.md).
- In both cases state the version gap in the answer.

## Sources

- memcached.org front page ("latest stable") — https://memcached.org/ — checked 2026-11-27
- Release notes index — https://github.com/memcached/memcached/wiki/ReleaseNotes — checked 2026-11-27
- Release notes 1.6.45, 1.6.44, 1.6.43, 1.6.42, 1.6.41, 1.6.40, 1.6.39, 1.6.0 — https://github.com/memcached/memcached/wiki/ReleaseNotes1645 (and ReleaseNotes1644, ReleaseNotes1643, ReleaseNotes1642, ReleaseNotes1641, ReleaseNotes1640, ReleaseNotes1639, ReleaseNotes160) — checked 2026-11-27
- Protocol specification at tag 1.6.45 — https://raw.githubusercontent.com/memcached/memcached/1.6.45/doc/protocol.txt — checked 2026-11-27
- LRU design notes — https://raw.githubusercontent.com/memcached/memcached/master/doc/new_lru.txt — checked 2026-11-27
- Configuring — https://docs.memcached.org/serverguide/configuring/ — checked 2026-11-27
- Maintenance — https://docs.memcached.org/serverguide/maintenance/ — checked 2026-11-27
- Meta text protocol — https://docs.memcached.org/protocols/meta/ — checked 2026-11-27
- Flash storage (extstore) — https://docs.memcached.org/features/flashstorage/ — checked 2026-11-27
- Built-in proxy — https://docs.memcached.org/features/proxy/ — checked 2026-11-27
- TLS support — https://docs.memcached.org/features/tls/ — checked 2026-11-27
- Binary SASL auth — https://docs.memcached.org/protocols/binarysasl/ — checked 2026-11-27
- Warm restart — https://docs.memcached.org/features/restart/ — checked 2026-11-27
- Overview and design philosophy — https://docs.memcached.org/ — checked 2026-11-27
- ElastiCache engine versions (Memcached section) — https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/engine-versions.html — checked 2026-11-27
- ElastiCache upgrade considerations — https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/VersionManagement-upgrade-considerations.html — checked 2026-11-27
- ElastiCache engine parameters (Memcached) — https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/ParameterGroups.Engine.html — checked 2026-11-27
- ElastiCache supported commands (Memcached Serverless) — https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/SupportedCommands.html — checked 2026-11-27
- Official image `memcached:1.6` (1.6.45; image digest in the coverage record, `updates/2026-11-27-initial-coverage.md`): `stats`, `stats settings`, `stats items`, `stats conns`, meta commands, `memcached -h` — run 2026-11-27
