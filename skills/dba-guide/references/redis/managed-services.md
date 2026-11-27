# Redis on Managed Services: ElastiCache and MemoryDB

Checked: 2026-11-27 (sources at the end). Redis Cloud and Redis Software (Redis Ltd. products) are out of scope.

## Engine Availability

Neither service runs Redis Open Source 7.2, 7.4, or 8.x. Their Redis OSS engines stop at a 7.0-compatible release; newer features arrive through their Valkey engines. See [../valkey/managed-services.md](../valkey/managed-services.md) for the Valkey engines.

| Service | Redis OSS engines offered | Compatible with | Newer line |
|---|---|---|---|
| ElastiCache (node-based and Serverless) | 7.1, 7.0, 6.2, 6.0, 5.0.6, 4.0.10 (3.x and 2.x are past EOL) | 7.1 is compatible with Redis OSS 7.0 | Valkey 7.2.6, 8.0, 8.1, 8.2, 9.0, 9.1 |
| MemoryDB | 7.1, 7.0, 6.2 | 7.1 is compatible with Redis OSS 7.0 | Valkey 7.2.6, MemoryDB 7.3 (Multi-Region) |

Consequences:

- Commands from Redis 7.2+ (`WAITAOF`, `CLIENT NO-TOUCH`), 7.4+ (`HEXPIRE`), 8.0+ (`HSETEX`, bundled Redis JSON/Search), and 8.4+ (`SET ... IFEQ`, `CLUSTER MIGRATION`) are not in the Redis OSS engines. Some exist in Valkey engines under the same or different names (per the ElastiCache engine page: Valkey 8.1 added `SET ... IFEQ`, Valkey 9.0 added hash field expiration and `DELIFEQ`, Valkey 9.1 added `HGETDEL` and `MSETEX`). Check each command against the target engine's supported-command list.
- ElastiCache and MemoryDB JSON, vector search, and Bloom support are AWS or Valkey implementations, not Redis 8 components; behavior and command coverage differ.
- Moving self-hosted Redis 7.4/8.x data into these services: newer RDB formats are not expected to load on older engines (see [versions](versions/index.md#upgrade-paths)). Plan a logical migration (application dual-write, or a key-by-key copy tool).
- Both services can upgrade a Redis OSS cluster to the Valkey engine.

## Version Support and Extended Support

ElastiCache Redis OSS:

| Major | End of standard support | Extended Support (paid; premium rises each year) | End of Extended Support |
|---|---|---|---|
| v4 | 2026-01-31 | 2026-02-01 to 2029-01-31 | 2029-01-31 |
| v5 | 2026-01-31 | 2026-02-01 to 2029-01-31 | 2029-01-31 |
| v6 | 2027-01-31 | 2027-02-01 to 2030-01-31 | 2030-01-31 |

- Caches still on a version at end of standard support are enrolled in Extended Support automatically and charged; v4 and v5 were first moved to the latest patch (4.0.10, 5.0.6).
- Extended Support provides critical security and defect fixes only.
- The checked page publishes no end of standard support for Redis OSS v7.
- MemoryDB: the engine versions page lists no end-of-life or Extended Support dates as of 2026-11-27. Watch that page and the MemoryDB announcements before planning around a version's lifetime.

Version selection: from 6.0, both services offer one version per minor (`6.2`, `7.0`, `7.1`) and manage the patch; a request for a specific patch is rejected. Read the actual patch from `CacheEngineVersionDescription` (ElastiCache `describe-cache-engine-versions`) or `EnginePatchVersion` (MemoryDB `describe-clusters`).

## What the Service Takes Over and Restricts

ElastiCache restricted commands for Redis OSS (supported-commands page): `ACL SETUSER`, `ACL LOAD`, `ACL SAVE`, `ACL DELUSER`, `BGREWRITEAOF`, `BGSAVE`, `CLUSTER ADDSLOT`/`ADDSLOTSRANGE`/`DELSLOT`/`DELSLOTSRANGE`/`SETSLOT`/`BUMPEPOCH`/`FAILOVER`/`FLUSHSLOTS`/`FORGET`/`LINKS`/`MEET`, `CONFIG`, `DEBUG`, `MIGRATE`, `PSYNC`, `REPLICAOF`, `SAVE`, `SLAVEOF`, `SHUTDOWN`, `SYNC`. The separate "Restricted commands" page lists a shorter set (without the ACL and CLUSTER entries); treat the longer list as current.

MemoryDB restricted commands: `ACL DELUSER`, `ACL LOAD`, `ACL SAVE`, `ACL SETUSER`, `BGREWRITEAOF`, `BGSAVE`, `CLUSTER ADDSLOT`, `CLUSTER DELSLOT`, `CLUSTER SETSLOT`, `CONFIG`, `DEBUG`, `MIGRATE`, `MODULE`, `PSYNC`, `REPLICAOF`, `SAVE`, `SHUTDOWN`, `SLAVEOF`, `SYNC`.

ElastiCache Serverless additionally removes, among others: `ACL LOG`, most `CLIENT` subcommands (`CLIENT LIST`, `CLIENT KILL`, `CLIENT INFO`, `CLIENT PAUSE`, tracking), `FUNCTION`/`FCALL`, `KEYS`, `LASTSAVE`, `LATENCY *`, `MEMORY *`, `MONITOR`, `MOVE`, `OBJECT *`, `PSUBSCRIBE`, `SCRIPT KILL`, `SLOWLOG *`, `SWAPDB`, `WAIT`. `SCRIPT FLUSH` is a no-op there.

What replaces the self-hosted tasks:

| Self-hosted task | Managed replacement |
|---|---|
| `CONFIG SET` | Parameter groups (`aws elasticache modify-cache-parameter-group`; MemoryDB has its own parameter groups) |
| `ACL SETUSER` | ElastiCache RBAC users and user groups (the only access control on Serverless); MemoryDB ACLs managed through the service API |
| `BGSAVE`, file copy | Service snapshots (automatic and manual) |
| `REPLICAOF`, Sentinel | Service-managed replication and Multi-AZ automatic failover |
| `CLUSTER ADDSLOTS`/`SETSLOT`, `redis-cli --cluster reshard` | Online resharding through the service (cluster mode enabled) |
| `SLOWLOG`, `LATENCY`, `MEMORY`, `CLIENT LIST` | CloudWatch metrics and the service's log delivery (unavailable as commands on Serverless) |
| `rename-command` | ElastiCache `rename-commands` parameter; value `blocked` disables a command |
| `FLUSHALL` across a cluster | Node-based: send to every primary. Serverless: flushes all keys; not allowed inside a transaction |

## ElastiCache

- Durability: node-based Redis OSS caches rely on asynchronous replication and snapshots; `appendonly` and `appendfsync` have not been supported since 2.8.22. Inference, not stated in the documentation: writes after the last snapshot that had not reached a replica are lost when a node fails. Valkey 9.0 on ElastiCache adds optional durability through a Multi-AZ transaction log (synchronous or asynchronous); that is a Valkey engine feature.
- Failover: Multi-AZ with automatic failover promotes a replica; clients reconnect through the primary endpoint, or follow the topology in cluster mode.
- Cluster mode disabled: one shard, multiple databases. Cluster mode enabled: up to 500 shards, database 0 only, hash-slot rules as in [replication and cluster](replication-and-cluster.md#cluster).
- Serverless: no node or shard management; one virtual shard is exposed to clients (`CLUSTER SHARDS`, `CLUSTER SLOTS` return a single shard); RBAC is the only access control; TLS required (Serverless runs every engine in cluster mode and works only with TLS clients, "How ElastiCache works"). Heavy `SCAN` slows scaling; set a minimum capacity to keep headroom.
- Upgrades: engine version changes through modify operations; patch updates arrive as service updates; opt in to automatic minor upgrades with `AutoMinorVersionUpgrade`. Data tiering on nodes with local NVMe SSD is available from 6.2.

## MemoryDB

- Durability: successful writes are stored in a distributed Multi-AZ transaction log before the client gets the reply. Primary reads are strongly consistent, including across failover. Replica reads (`READONLY`) are eventually consistent and sequentially consistent per replica; lag is published to CloudWatch. This is the AWS option when acknowledged writes must survive node loss; expect higher write latency than ElastiCache (inference; no number on the checked pages).
- Cluster mode only; hash-slot rules apply.
- Upgrades: one operation per shard; replicas first, then primaries one at a time, each with a failover of a few seconds; reads stay available throughout. No downgrade: recreate the cluster on the older version instead. You can opt out of automatic minor upgrades, not patch upgrades. An engine upgrade is blocked while a scale-up is pending.
- MemoryDB 7.3 (Valkey-based) adds Multi-Region clusters.

## Diagnostics on Managed Services

- `INFO` works on node-based clusters; `INFO server` shows the compatible OSS version.
- Slow log and engine log: use log delivery to CloudWatch Logs or Amazon Data Firehose instead of `redis.log`. Slow log needs Redis OSS 6.0+ or Valkey 7.x+, engine log Redis OSS 6.2+ or Valkey 7.x+; serverless caches have no log delivery (log delivery page).
- CloudWatch metrics replace host-level checks (CPU per node, network, swap, replication lag). Map existing alerts to them before cutover.

## Choosing Self-Hosted vs Managed

- Need Redis 8 features (bundled Query Engine, `BACKUP`, atomic slot migration, `HOTKEYS`, LRM eviction, `BLESS`): self-host or use Redis Ltd.'s products; the AWS services do not offer them.
- Need durable acknowledged writes without running your own replication safeguards: MemoryDB, or ElastiCache Valkey 9.0 durability.
- Need full control of configuration, persistence files, and backups: self-host.
- Running Redis OSS v6 on ElastiCache: standard support ends 2027-01-31; after that it is billed as Extended Support. Plan the move to Redis OSS 7.x or Valkey.

Sources: https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/engine-versions.html, https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/extended-support-versions.html, https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/SupportedCommands.html, https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/ClientConfig.RestrictedCommands.html, https://docs.aws.amazon.com/memorydb/latest/devguide/engine-versions.html, https://docs.aws.amazon.com/memorydb/latest/devguide/restrictedcommands.html, https://docs.aws.amazon.com/memorydb/latest/devguide/consistency.html, https://docs.aws.amazon.com/cli/latest/reference/memorydb/describe-clusters.html, https://docs.aws.amazon.com/cli/latest/reference/elasticache/describe-serverless-caches.html (checked 2026-11-27).
