# MongoDB Configuration

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)).

## Contents

- [Read the effective configuration](#read-the-effective-configuration)
- [WiredTiger cache](#wiredtiger-cache)
- [Compression, checkpoints, journal](#compression-checkpoints-journal)
- [Concurrency and admission control](#concurrency-and-admission-control)
- [Connections](#connections)
- [Query memory limits](#query-memory-limits)
- [Operating system](#operating-system)
- [Change settings safely](#change-settings-safely)

## Read the effective configuration

```javascript
db.adminCommand({ getCmdLineOpts: 1 }).parsed                 // config file + flags actually applied
db.adminCommand({ getParameter: "*" })                        // all server parameters (large)
db.adminCommand({ getParameter: 1, transactionLifetimeLimitSeconds: 1, enableFlowControl: 1 })
db.adminCommand({ getClusterParameter: "*" })                 // cluster parameters such as defaultMaxTimeMS (8.0+); returns clusterParameters: [ { _id, clusterParameterTime, ... } ]
db.serverStatus().wiredTiger.cache["maximum bytes configured"]
db.hostInfo().system.memLimitMB                               // memory limit WiredTiger sizes against
```

From 8.0, `getParameter` also accepts a `setAt` filter. The official Docker images start `mongod` with `net.bindIp: '*'`, which differs from the packaged default of `localhost`; do not copy container settings into production.

## WiredTiger cache

- Default size: the larger of 50% of (RAM − 1 GB) or 256 MB. Example: 4 GB RAM gives 1.5 GB of cache. All four images reported `maximum bytes configured` = 268435456 (256 MB), the floor value. The containers ran with `--memory 1g`: `db.hostInfo().system.memLimitMB` reported 1024 while `memSizeMB` reported 7835, so WiredTiger sized against the container limit and 50% of (1 GB − 1 GB) fell to the floor.
- The rest of RAM is still used: the OS filesystem cache holds compressed data files.
- Set the size explicitly when:
  - more than one `mongod` shares a host;
  - the process runs under a container or cgroup memory limit (WiredTiger may not account for it);
  - other processes need memory.
- Do not raise it above the default without evidence.

| Setting | Range | Notes |
| --- | --- | --- |
| `storage.wiredTiger.engineConfig.cacheSizeGB` / `--wiredTigerCacheSizeGB` | 0.256-10000 GB | fixed size |
| `storage.wiredTiger.engineConfig.cacheSizePct` / `--wiredTigerCacheSizePct` | up to 80% of RAM; result must be 0.256-10000 GB | 8.2+ (in 8.3, 9.0); follows vertical scaling; mutually exclusive with `cacheSizeGB` |

Cache facts:
- The cache is global to the process, not per database. It has no separate read and write areas, and documents cannot be pinned.
- In the cache, collection data is uncompressed and indexes keep prefix compression.

Evidence of cache pressure:

```javascript
const c = db.serverStatus().wiredTiger.cache;
[c["bytes currently in the cache"], c["maximum bytes configured"], c["tracked dirty bytes in the cache"]]
```

Sustained use near the maximum, a high dirty share, and application threads doing eviction (visible in the same section) mean the working set does not fit. Fix it with more RAM, fewer or smaller indexes, or smaller documents before you tune eviction. The exact eviction counter names vary by version; list `Object.keys(c)` on your version and pick the eviction and dirty counters from that list.

## Compression, checkpoints, journal

- Collections use `snappy` block compression by default; time series collections use `zstd`. Alternatives are `zlib`, `zstd`, and `none`.
  - Set the default with `storage.wiredTiger.collectionConfig.blockCompressor`, or per collection at creation.
  - Existing collections keep their compressor.
  - 8.2+ accepts zstd levels −7 to 22 (`zstdCompressionLevel`).
  - The 9.0 image log shows `block_compressor=snappy` for new collections.
- Indexes use prefix compression (`storage.wiredTiger.indexConfig.prefixCompression`). The journal uses snappy (`journalCompressor`).
- Checkpoints run every 60 s. The previous checkpoint stays valid until the new one completes. After a crash, recovery replays the journal from the last checkpoint.
- Journaling is always on (7.0+). No option turns it off. Durability of acknowledged writes depends on write concern: `w: "majority"` journals by default.

## Concurrency and admission control

Since 7.0 the storage engine dynamically adjusts the number of concurrent read and write transactions ("tickets"). The maximum is never more than 128 each.

- After upgrading to 7.0+, expect lower ticket usage. Low `available` tickets is not a sign of overload. Sustained queueing is.
- Where to look:
  - 8.0+: `db.serverStatus().queues.execution`, with `read` and `write` totals (`out`, `available`, `totalTickets`) and per-priority queue stats (`addedToQueue`, `queueLength`, `totalTimeQueuedMicros`).
  - 7.0: `db.serverStatus().wiredTiger.concurrentTransactions`.
- Observed values on the official images:

  | Image | `storageEngineConcurrencyAdjustmentAlgorithm` | `wiredTigerConcurrentRead/WriteTransactions` | `queues.execution` totals |
  | --- | --- | --- | --- |
  | 7.0.48 | `throughputProbing` | 0 / 0 | not present (renamed in 8.0) |
  | 8.0.38 | `throughputProbing` | 0 / 0 | read and write `totalTickets: 14` |
  | 8.3.17 | `throughputProbing` | 128 / 128 | present |
  | 9.0.8 | `throughputProbing` | 128 / 128 | read and write `totalTickets: 14`, plus `usesThroughputProbing: true`, `lowPriority`, `monitor.timesProbed*` |

  The parameter values differ between 8.0 and 8.3 while dynamic adjustment is active on both. The manual names `storageEngineConcurrentReadTransactions` / `storageEngineConcurrentWriteTransactions` as the caps for the dynamic maximum. On all four images the `storageEngine*` and `wiredTiger*` names always reported the same value, and setting one changed the other. With `throughputProbing`, a runtime `setParameter` of either name on 7.0 and 8.0 returns code 20 (`Cannot modify concurrent read transactions limit when it is being dynamically adjusted`), yet the value read back afterwards has changed (7.0.48 and 8.0.38 containers); 8.3 and 9.0 accept it without an error.
- Do not disable the dynamic algorithm on your own. The manual says to open a support case for that.
- Slow-query log lines (8.0+) include `queues.execution.totalTimeQueuedMicros`. Use it to tell queueing apart from execution time.
- 8.3+ adds deprioritization of long or background work (`heuristicDeprioritization`, `backgroundTasksDeprioritization` in `queues.execution`). 9.0 shows these enabled on the image.

## Connections

- `net.maxIncomingConnections` defaults on Linux to `(RLIMIT_NOFILE / 2) * 0.8` (changed in 8.1, 8.0.16, 7.0.31); larger values are capped to that. The 9.0 image showed `connections.available: 13102`.
- `serverStatus().connections` reports `current`, `available`, `rejected`, and `active`; 8.2+ also `queuedForEstablishment` and `establishmentRateLimit`.
- Ingress connection establishment rate limiting (8.2+):
  - `ingressConnectionEstablishmentRateLimiterEnabled` (default `false` on the images), `ingressConnectionEstablishmentRatePerSec`, `ingressConnectionEstablishmentBurstCapacitySecs`, `ingressConnectionEstablishmentMaxQueueDepth`.
  - Enable it when reconnect storms after a failover overload the server.
- Size driver pools (`maxPoolSize`) at 110-115% of typical concurrent requests (production notes). Many application instances times a large pool is the usual cause of connection exhaustion.
- Outbound pools from `mongos` and shards: `db.adminCommand({ connPoolStats: 1 })` reports `totalInUse`, `totalAvailable`, and `totalCreated`. 8.3+ FTDC collects these.

## Query memory limits

| Limit | Default | Version |
| --- | --- | --- |
| Per blocking stage (`$sort`, `$group`, ...) | 100 MB, then spill if allowed | all |
| `allowDiskUseByDefault` | `true` on all four images | 6.0+ |
| Per operation, `internalQueryMaxMemoryUsageBytesPerOperation` | greater of 1 GB or 20% of process memory (1073741824 on the 9.0 image with a 1 GB limit; unknown parameter on 7.0, 8.0, 8.3) | 9.0+ |
| Single expression, `internalQueryMaxSingleExpressionMemoryUsageBytes` | 100 MB | 9.0+ |
| `$text` TextOr stage | 100 MB | 8.3+ |
| `defaultMaxTimeMS` (cluster parameter, reads) | unset on the images | 8.0+ |

When 9.0 operations fail with `ExceededMemoryLimit`:
- Check `metrics.query.operationsFailedDueToMemoryLimit` and the log id `12932700`.
- Fix the query first: an earlier `$match`, a narrower projection, or an index that supports the sort.
- Raise the limit for one shape with query settings rather than globally.

## Operating system

From the production notes:

| Area | Setting |
| --- | --- |
| Filesystem | XFS strongly recommended for WiredTiger data; ext4 allowed; turn off `atime`; directory `fsync()` support required |
| Transparent Huge Pages | 8.0+: enable. 7.0: disable. PPC64LE/s390x: disable on any version |
| NUMA | disable in BIOS if possible; on Linux set `vm.zone_reclaim_mode=0` and start under `numactl --interleave=all`; `numad` off |
| Swap | `vm.swappiness` 1 (or 0); on RHEL cgroups also `vm.force_cgroup_v2_swappiness=1` |
| Open files | startup warning below 64000 |
| Readahead | between 8 and 32 for WiredTiger data volumes, unless testing shows a reliable gain from more |
| I/O scheduler | `none` for VMs and NVMe/SSD; `mq-deadline` for spinning disks |
| TCP keepalive | `net.ipv4.tcp_keepalive_time=120`; values above 300 s are overridden to 300 on mongod/mongos sockets; consider `tcp_retries2` 5 or lower |
| Clock | NTP/chrony/systemd-timesyncd on every host |
| RAID | RAID-10; avoid RAID-5/6 |
| Kernel | for 8.0/8.3/9.0, check the kernel 6.19-7.0.13 TCMalloc table in [8.0](versions/8.0.md#upgrading-into-this-series) |

Verify:

```bash
cat /sys/kernel/mm/transparent_hugepage/enabled
sysctl vm.swappiness vm.zone_reclaim_mode net.ipv4.tcp_keepalive_time
uname -r
ulimit -n
```

Also read the startup warnings in the `mongod` log after each change.

## Change settings safely

- Runtime parameters: `db.adminCommand({ setParameter: 1, <name>: <value> })`. These do not persist across restarts; also add them under `setParameter:` in the config file. Atlas blocks `setParameter` (see [managed-services](managed-services.md)).
- Cluster parameters (8.0+, such as `defaultMaxTimeMS` and `auditConfig`): `db.adminCommand({ setClusterParameter: { defaultMaxTimeMS: { readOperations: 5000 } } })`. On 8.0, 8.3, and 9.0 this returned `ok: 1`, and `getClusterParameter: "defaultMaxTimeMS"` then showed `readOperations: Long('5000')`. 7.0 rejects it with `Unknown server parameter: defaultMaxTimeMS`. These persist and replicate. An active `setClusterParameter` blocks FCV changes.
- Startup-only options (cache size, compressor defaults, `bindIp`, TLS) need a restart. Use a rolling restart: secondaries one at a time, then `rs.stepDown()` and the old primary. Record the old value so you can roll back the same way.
- Parameters starting with `internal` are not stable interfaces. Change them only on support advice or as the release notes direct.
