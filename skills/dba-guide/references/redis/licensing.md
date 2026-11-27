# Redis Licensing and Engine Choice

Checked: 2026-11-27 (sources at the end). This is engineering guidance, not legal advice; for a decision with legal weight, have counsel read the license texts named here.

## License by Version

| Redis version | Product name | License |
|---|---|---|
| 7.2.x and earlier (includes 6.2) | Redis | BSD-3-Clause |
| 7.4.x | Redis Community Edition | RSALv2 or SSPLv1 (user's choice) |
| 8.0 and later | Redis Open Source | RSALv2, SSPLv1, or AGPLv3 (user's choice) |
| Redis Stack 6.2.6 and later | Redis Stack | RSALv2 or SSPLv1 |

Evidence in the source tree: the `7.2.17` tag carries a BSD-3-Clause `COPYING` file; the `8.12.0` tag carries `LICENSE.txt` stating the tri-license and that 7.2 and earlier remain under BSD. The Redis licensing page gives the same table and states that RediSearch, RedisJSON, RedisTimeSeries, and RedisBloom are part of Redis Open Source from 8.0 under the same tri-license, with module version numbers equal to the Redis version.

What each license requires, as summarized on the Redis licensing page:

- RSALv2 (source-available, not open source): use, copy, modify, distribute allowed; you may not commercialize the software or provide it to others as a managed service, and may not remove notices.
- SSPLv1 (source-available, not open source, copyleft): if you offer the software as a service, you must release your modifications and the source of the service's management layers under SSPL.
- AGPLv3 (OSI-approved open source, copyleft): if you modify the code and let users interact with it over a network, you must make the source of the modified version available to them.
- BSD-3-Clause (permissive): keep the copyright notice and disclaimer.

## What It Means in Practice

Interpretation of the summaries above and the Redis licensing FAQ; confirm against the license texts for any commercial decision.

| Situation | 7.2 / 6.2 (BSD) | 7.4 (RSALv2/SSPLv1) | 8.x (adds AGPLv3) |
|---|---|---|---|
| Internal application backend, unmodified binaries | Notices only | Allowed; the RSALv2 restriction targets offering Redis to others as a service | Allowed; the FAQ says users on 7.4 or Redis Stack, and 7.2 users running unmodified artifacts, are not affected |
| Internal use with patched source | Allowed | Allowed under RSALv2 | Under AGPLv3, network users must be offered the modified source (FAQ); or elect RSALv2 |
| Offering Redis as a hosted service to third parties | Allowed | RSALv2 forbids; SSPLv1 requires releasing the service stack | AGPLv3 permits with source obligations; RSALv2 forbids |
| Shipping Redis inside a distributed product | Allowed with notices | Check RSALv2 commercialization terms | AGPLv3 copyleft terms apply; review with counsel |

The practical risk sits with organizations that offer Redis-compatible services or ship modified builds. Ordinary self-hosting of official binaries for an internal backend is allowed under every option.

## Choosing Redis, Valkey, or a Managed Engine

| Option | License | Version line | Choose when |
|---|---|---|---|
| Redis Open Source 8.x | RSALv2 / SSPLv1 / AGPLv3 | 8.0 to 8.12 (8.2 Extended to 2030-09-01) | You want Redis 8 features: bundled Query Engine, JSON, time series, probabilistic types, vector sets, `BACKUP`, atomic slot migration, `HOTKEYS`, LRM eviction, `BLESS`; and AGPLv3 or RSALv2 terms are acceptable |
| Redis 7.2 | BSD-3-Clause | Extended support to 2029-12-01 | You need a permissive license from Redis Ltd. and can live without 7.4+ features |
| Valkey | BSD-3-Clause (Valkey `COPYING`: copyright Valkey contributors from 2024 and Redis Ltd. for 2006-2020) | Forked from the Redis 7.2 lineage; image tags 7.2 to 9.2 | You need a permissive license with continued development, or you will use AWS engines built on it. Its features diverge from Redis 8, often under different command names (`DELIFEQ` and `COMMANDLOG` exist in Valkey; Redis 8.12 rejects both as unknown). See [../valkey/versions/index.md](../valkey/versions/index.md) |
| ElastiCache / MemoryDB | AWS service terms | Redis OSS engines up to 7.1 (7.0-compatible); Valkey engines for anything newer | You want AWS to run it; Redis 7.2+ and Redis 8 features are not in the Redis OSS engines. See [managed services](managed-services.md) |
| Redis Cloud / Redis Software | Commercial (Redis Ltd.) | Redis Ltd. versions | Not covered here |

Migration notes:

- Redis 7.2 to Valkey: Valkey continues the 7.2 lineage; confirm RDB and replication compatibility for the exact versions in the Valkey reference before relying on it.
- Redis 7.4 or 8.x to Valkey: data features added after 7.2 (hash field TTL format in 7.4, Redis 8 data types, compact hashes, arrays) may not load. Do not assume RDB compatibility; plan a logical migration.
- Valkey to Redis 8: also a logical migration unless both projects document compatibility for the specific versions.

When running Redis 8, record the elected license in your architecture records: the binaries are the same, the obligations depend on the license you choose.

Sources: https://redis.io/legal/licenses/, https://raw.githubusercontent.com/redis/redis/8.12.0/LICENSE.txt, https://raw.githubusercontent.com/redis/redis/7.2.17/COPYING, https://raw.githubusercontent.com/redis/redis/7.4.0/00-RELEASENOTES, https://raw.githubusercontent.com/redis/redis/8.0.0/00-RELEASENOTES, https://raw.githubusercontent.com/valkey-io/valkey/unstable/COPYING, https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/engine-versions.html (checked 2026-11-27); image `redis:8.12` statement runs (`DELIFEQ`, `COMMANDLOG` unknown) and `valkey/valkey:9.2` `INFO` output (2026-11-27).
