# Valkey Managed Services

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)).

Amazon ElastiCache for Valkey (node-based clusters and Serverless) and Amazon MemoryDB for Valkey. Shared ElastiCache/MemoryDB behavior for the Redis OSS engine (parameter groups, maintenance windows, snapshots, Multi-AZ, Global Datastore) is in [../redis/managed-services.md](../redis/managed-services.md).

## Version availability (2026-11-27)

| Service | Valkey versions offered | Notes |
| --- | --- | --- |
| ElastiCache (node-based and Serverless) | 7.2.6, 8.0, 8.1, 8.2, 9.0, 9.1 | "8.2" = upstream 8.1 + valkey-search; one version per minor, patch managed by AWS |
| ElastiCache Redis OSS engine | up to 7.1 | source engine for cross-engine upgrades |
| MemoryDB | 7.2.6 (Valkey), 7.3 (Multi-Region) | the Multi-Region prerequisites page calls 7.3 a Valkey engine version (checked 2026-11-27); no 8.x or 9.x listed; downgrade not supported |

Upstream 9.2 is not offered by either service on the check date. ElastiCache adds features that do not exist in upstream Valkey: Bloom filters (8.1+), vector search (8.2+), full-text and hybrid search (9.0+), durability with a Multi-AZ transactional log (9.0), public Serverless endpoints with IAM auth and TLS 1.3 (9.0), distributed KV caching on `cache.i8ge.48xlarge` (9.1). Code that depends on them does not port to self-hosted Valkey without the matching modules (`valkey/valkey-bundle` provides JSON, Bloom, Search and LDAP modules).

## What the service takes over and what it removes

| Area | ElastiCache node-based | ElastiCache Serverless |
| --- | --- | --- |
| `CONFIG`, `DEBUG`, `SAVE`, `BGSAVE`, `BGREWRITEAOF`, `SHUTDOWN`, `REPLICAOF`/`SLAVEOF`, `MIGRATE`, `PSYNC`, `SYNC` | blocked | blocked |
| `ACL SETUSER`, `ACL DELUSER`, `ACL LOAD`, `ACL SAVE` | blocked; manage users and user groups through the ElastiCache API | blocked; `ACL CAT/GENPASS/GETUSER/LIST/USERS/WHOAMI` work |
| `CLUSTER MEET/FORGET/SETSLOT/FAILOVER/ADDSLOTS/DELSLOTS/FLUSHSLOTS/BUMPEPOCH/LINKS` | blocked; resharding and failover through the API | blocked |
| `SLOWLOG`, `LATENCY`, `MEMORY`, `OBJECT`, `CLIENT LIST/KILL/INFO/PAUSE/TRACKING`, `MONITOR`, `KEYS`, `FUNCTION`, `FCALL`, `COMMANDLOG`, `WAIT`, `SWAPDB`, `MOVE`, `ACL LOG` | available | blocked |
| Parameters | custom parameter group, families `valkey7`, `valkey8`, `valkey9` | limited |
| `maxmemory` | fixed per node type, not modifiable | managed |

MemoryDB publishes its own restricted-command list; the list checked for its Redis OSS engine is in [Redis managed services](../redis/managed-services.md#what-the-service-takes-over-and-restricts). The MemoryDB restricted-commands page is a single list with no engine split (ACL changes, `CONFIG`, `DEBUG`, `MODULE`, `SAVE`/`BGSAVE`, `REPLICAOF`, `SHUTDOWN` and similar), so expect it on Valkey clusters too; confirm a command on your cluster with `COMMAND INFO <name>`.

Serverless specifics: `FLUSHDB`/`FLUSHALL` always flush all keys in the cache and cannot be used inside a transaction; `SCRIPT FLUSH` is a no-op because the service manages the script cache. On node-based cluster-mode caches, send flush commands to every primary.

ElastiCache parameter defaults that differ from upstream Valkey 8.0+: `maxmemory-samples` default 3 (upstream 5), `extended-redis-compatibility` default `yes` (upstream `no`), and the `lazyfree-lazy-*`/`replica-lazy-flush` parameters are not in the `valkey8` group. On `valkey9`, `cluster-databases` is set at creation and cannot be changed (documented range 1–10,000, documented default 0; upstream default 1). Check `INFO server` on a node before assuming the Valkey identity fields look as they do self-hosted; self-hosted, `extended-redis-compatibility yes` makes `HELLO` report `server redis`, `version 7.2.4` and `INFO server` print `redis_mode:` (see [versions/index.md](versions/index.md)). On ElastiCache, run `HELLO 3` and `INFO server` on a node to see which identity it reports before scripting against those fields.

## Failover, backups and durability

- ElastiCache node-based: Multi-AZ automatic failover promotes a replica; backups are snapshots, and restoring creates a new cache. The snapshot page describes only snapshots restored into a new cache, with no point-in-time restore; treat data written after the last snapshot and not replicated as lost on a total failure.
- ElastiCache 9.0+ durability: writes go to a Multi-AZ transactional log. Synchronous mode gives zero data loss with single-digit millisecond write latency; asynchronous mode gives microsecond latency with up to 10 seconds of writes at risk. Use synchronous mode only when the cache is the system of record. Setup steps: https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/Durability.GettingStarted.html (page not checked).
- MemoryDB stores writes in a durable Multi-AZ transaction log. Its write acknowledgment and read consistency, as described on the MemoryDB consistency page, are summarized in [Redis managed services](../redis/managed-services.md#memorydb); the consistency page makes no engine distinction (strongly consistent primaries, eventually consistent but sequentially consistent replica reads), so it applies to Valkey clusters as well. Engine downgrade is not supported: to use an older version, delete and recreate the cluster.

## Upgrades and maintenance

- AWS manages patch versions and may patch on its own for critical security issues. Request minor and major upgrades with `aws elasticache modify-replication-group --engine-version`, `aws elasticache modify-serverless-cache --major-engine-version`, or a MemoryDB cluster update. MemoryDB applies patches through service updates; auto minor version upgrade can be turned off, patch upgrades cannot.
- Node-based ElastiCache upgrade mechanics: per shard, new nodes on the new version sync from the primary, a failover promotes a new node, old nodes are removed; shards are processed in parallel and primary failovers run one at a time. Existing client connections are terminated; clients need retries with exponential backoff and must tolerate errors from new replicas still loading.
- MemoryDB upgrade mechanics: in each shard replicas are processed before the primary; primaries are upgraded one at a time.
- A pending scale-up blocks an immediate engine upgrade; apply both with `--apply-immediately` in one request, or schedule the upgrade for the maintenance window with `--no-apply-immediately`.
- Parameter groups are not interchangeable across major families: Valkey 8 groups are incompatible with Redis OSS 7.2.4 groups, `valkey9` groups with 8.x and Redis OSS.
- Cluster mode disabled → enabled is not an in-place change: back up, seed a new cluster-mode cache with one shard from the backup, delete the old one, then scale shards.
- With encryption enabled, the target version must support encryption.

## Cross-engine upgrade: ElastiCache Redis OSS → Valkey

```
aws elasticache modify-replication-group \
  --replication-group-id my-rg --engine valkey --engine-version 9.0 \
  --cache-parameter-group-name my-valkey9-params    # only if a custom group is used
aws elasticache modify-serverless-cache \
  --serverless-cache-name my-cache --engine valkey --major-engine-version 9
```

- Endpoint DNS names stay; node IPs change on node-based clusters. From Redis OSS 5.0.6 or later the cache stays readable throughout and writable except during a failover of a few seconds; from older engines expect 30 to 60 seconds of failover time during DNS propagation.
- A custom Redis OSS parameter group must be replaced by a custom Valkey group with the same static parameter values.
- Single-node Redis OSS (cluster mode disabled) caches must first be converted to a replication group.
- Requires AWS CLI v1 1.35.2 or later, or v2 2.18.2 or later.
- Rollback: only Valkey 7.2 → Redis OSS 7.1, in place or by restoring a Valkey 7.2 snapshot as a new Redis OSS 7.1 cache; users and user groups must have engine type `REDIS`. After moving to Valkey 8.0 or later there is no documented path back to Redis OSS. Rehearse by restoring a snapshot into a test cache on the target engine first.
- MemoryDB also supports upgrading a Redis OSS cluster to the Valkey engine; it cannot downgrade.

Pre-checks for the switch: client tolerance of `server_name:valkey` and of error text without "Redis" (8.0+), nested `MULTI` aborting (8.0+), `NOAUTH` before unknown-command errors (9.0+), strict `CLUSTER SHARDS`/`CLUSTER SLOTS` parsing (9.1+), and scripts or tools that read `redis_version`. Per-version lists: [versions/index.md](versions/index.md).

## Diagnostics that replace self-hosted tools

| Self-hosted | ElastiCache / MemoryDB |
| --- | --- |
| `INFO` | available (not on the restricted lists); use it for `valkey_version`, memory, replication |
| `SLOWLOG`, `COMMANDLOG`, `LATENCY`, `MEMORY USAGE` | node-based: available; Serverless: blocked, use CloudWatch metrics |
| host CPU, memory, swap, network | `AWS/ElastiCache` host metrics per node: `CPUUtilization`, `EngineCPUUtilization` (use it on nodes with 4+ vCPUs), `FreeableMemory`, `SwapUsage`, `NetworkBytesIn`/`Out`. Serverless: `BytesUsedForCache`, `ElastiCacheProcessingUnits`, `SuccessfulRead`/`WriteRequestLatency`, dimension `clusterId` (host-level and serverless metrics pages) |
| config review | `aws elasticache describe-cache-parameters --cache-parameter-group-name <group>` |
| version inventory | `describe-replication-groups`, `describe-serverless-caches`, `aws memorydb describe-clusters` (see [versions/index.md](versions/index.md)) |
