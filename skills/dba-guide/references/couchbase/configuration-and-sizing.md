# Couchbase Configuration and Sizing

Checked: 2026-11-27 (sources at the end). Applies to Couchbase Server 7.2–8.0. Container defaults come from single-node runs of the `couchbase/server` 7.6.13 and 8.0.4 Enterprise images.

## Contents

- Services and node layout
- Memory quotas
- Storage engines
- Ejection, watermarks, and out-of-memory behavior
- Warmup and the access scanner
- Compaction and disk
- Migrating a bucket's storage engine
- Query and Index service settings
- OS-level settings

## Services and Node Layout

Services: Data (`kv`), Query (`n1ql`), Index, Search (`fts`), Analytics (`cbas`), Eventing, Backup. Every cluster needs Data on at least one node.

Decision rules:

- Production: separate Data from Index and Query once load grows, so a Query or Index spike does not take memory or CPU from KV. Only Data and Index health is monitored for auto-failover. A node running only Query, Search, Eventing, Analytics, or Backup is not auto-failed over while its cluster manager responds.
- Run each service on at least 2 nodes if you want auto-failover to cover it (service-specific minimum). Use index replicas for the Index Service.
- Add an arbiter node (no services, 7.6+) for two-zone layouts or for faster failover when the orchestrator's node fails.
- 8.0 can add or remove non-Data services on an existing node, followed by an automatic rebalance.
- Community Edition license limits: clusters up to five nodes, at most 4 cores per node. XDCR is not permitted.

Check the layout:

```sh
couchbase-cli server-list -c 127.0.0.1 -u Administrator -p password
curl -s -u Administrator:password http://127.0.0.1:8091/pools/default \
  | jq '.nodes[] | {hostname, services, status, clusterMembership, serverGroup}'
```

## Memory Quotas

Per-service quotas are cluster-wide. Each node running the service gets the same quota.

| Service | Minimum quota (MiB) | Container value after `cluster-init --cluster-ramsize 768 --cluster-index-ramsize 256` |
|---|---|---|
| Data | 256 | `memoryQuota` 768 |
| Index | 256 | `indexMemoryQuota` 256 |
| Search | 256 | `ftsMemoryQuota` 256 |
| Analytics | 1024 | `cbasMemoryQuota` 1024 |
| Eventing | 256 | `eventingMemoryQuota` 256 |
| Query | none required | `queryMemoryQuota` 0 (no limit) |
| Backup | none | — |

- Give Couchbase and its services no more than 90% of node RAM, or 80% on small nodes. The docs give the firm limit as `max(total_memory - 1, 80% × total_memory)` with memory in GiB.
- Bucket quotas come out of the Data quota on every Data node. The sum of bucket quotas cannot exceed it.
- Bucket quota sizing guidance: at least 10% of the expected per-node dataset for Couchstore, and at least 1% for Magma. These are minimum ratios; the working set and access pattern decide the real need.
- The Query service has a per-request `memory-quota` and a node quota (`node-quota`, with `node-quota-val-percent` 67 in the containers). Both are unlimited (0) by default. Set a per-request quota to stop one query from exhausting the node.

```sh
# Change service quotas (MiB)
couchbase-cli setting-cluster -c 127.0.0.1:8091 -u Administrator -p password \
  --cluster-ramsize 16384 --cluster-index-ramsize 8192
# Change one bucket's quota (MiB per node)
curl -s -X POST -u Administrator:password http://127.0.0.1:8091/pools/default/buckets/app -d ramQuota=4096
```

`setting-cluster --cluster-ramsize 800 --cluster-index-ramsize 256` returned `SUCCESS: Cluster settings modified` on both containers, and `memoryQuota` read back as 800.

## Storage Engines

| | Couchstore | Magma, 128 vBuckets (8.0+) | Magma, 1024 vBuckets |
|---|---|---|---|
| Edition | CE and EE (the only engine in CE) | EE | EE |
| Minimum bucket quota per node | 100 MiB | 100 MiB | 1 GiB |
| Minimum memory-to-data ratio | 10% | 1% | 1% |
| Maximum data per node | 3 TB | 10 TB, with a higher chance of data imbalance | 10 TB |
| Default ejection | value-only | full | full |
| Views (MapReduce) | Supported | Not supported | Not supported |
| Fragmentation threshold default | 30% | 50% | 50% |
| Default for a new EE bucket | 7.x | 8.0 | — |

Choose:

- Magma/1024 when the working set exceeds memory and data per node reaches multiple terabytes, when transactions with persistence-level durability are heavy, when data will exceed Couchstore's 3 TB, or when the bucket must receive XDCR from a pre-8.0 cluster. It also gives better performance at scale when you can spare 1 GiB per node.
- Magma/128 (8.0+) for buckets under about 100 GiB, for working sets that do not fit in memory or exceed 20% of the dataset, and for test systems. It is available only once the whole cluster runs 8.0.
- Couchstore when the working set fits in memory and is under 20% of the data, on low-end hardware, on Community Edition, or for buckets that still use Views.
- Community Edition 8.0 (`community-8.0.2` container): `couchbase-cli bucket-create` without `--storage-backend` fails with "storageBackend - Magma is supported in enterprise edition only". With `--storage-backend couchstore` the bucket gets 1024 vBuckets and `valueOnly`. A REST create with no `storageBackend` succeeded but produced Couchstore with 128 vBuckets and `fullEviction`, which differs from the documented Couchstore defaults in the tables here. Set `storageBackend`, `numVBuckets`, and `evictionPolicy` explicitly on CE. (On 8.0.4 EE, `storageBackend=couchstore` alone gave 1024 vBuckets and `valueOnly`.)
- Magma prerequisites: SSD (NVMe preferred) and XFS on Linux for the data path. Set the Data Service reader and writer threads to "Disk i/o optimized" for high I/O concurrency. The flusher-to-compactor thread ratio is tunable if compaction spikes CPU.

vBucket count and storage engine are fixed per bucket, except through migration (below). vBucket count can only change through local XDCR into a new bucket.

## Ejection, Watermarks, and Out-of-Memory Behavior

| Bucket type | Policy | Behavior |
|---|---|---|
| Couchbase | `valueOnly` (Couchstore default) | Ejects values. Keys and metadata stay in memory, so key lookups and misses never touch disk. Needs more memory per item. |
| Couchbase | `fullEviction` (Magma default) | Ejects key, metadata, and value. Lowest memory. A lookup of a non-resident key can require a disk read. |
| Ephemeral | `noEviction` (default) | Refuses new writes when the quota is full |
| Ephemeral | `nruEviction` | Drops not-recently-used items. That data is gone, and an XDCR source configured like this may not replicate everything. |

- Watermarks: when bucket memory reaches `memoryHighWatermark` (default 85%), the Data Service ejects not-recently-used items until usage falls to `memoryLowWatermark` (default 75%). If ejection cannot free enough memory, it stops accepting data and returns errors to clients until memory frees up. 8.0 sets these per bucket over REST. Before 8.0 they are set with `cbepctl` (`set flush_param mem_high_wat` / `mem_low_wat`).
- The resident ratio is the percentage of items held in memory. Falling residency on a Couchstore bucket, together with rising disk fetches, means the bucket quota is too small for the working set.
- Changing the ejection policy of a Couchbase bucket restarts the bucket by default. That is downtime for that bucket: connections drop and the bucket warms up again. In 8.0, send `noRestart=true` to avoid the restart. The new policy then takes effect node by node after a swap rebalance, or after a graceful failover plus delta or full recovery and rebalance. 8.0 What's New lists this as new in 8.0. On 7.6.13 the call is rejected with HTTP 400 "noRestart option is not supported. Enable allow_online_eviction_policy_change to use this feature", and the policy stays unchanged, so on 7.x plan for the bucket restart. On Ephemeral buckets (8.0) the change takes effect immediately.

```sh
# 8.0: ejection change without a bucket restart
curl -s -X POST -u Administrator:password http://127.0.0.1:8091/pools/default/buckets/app \
  -d evictionPolicy=fullEviction -d noRestart=true
# then, per Data node: graceful failover + delta or full recovery + rebalance, or a swap rebalance
```

## Warmup and the Access Scanner

- After a node or bucket restart, persistent buckets reload data from disk.
- 8.0 `warmupBehavior` per bucket: `background` (default; available once metadata loads, the cache fills afterwards), `blocking` (pre-8.0 behavior; read-available early, fully available only after loading up to the low watermark), or `none` (no preload). `background` brings a bucket back sooner, with more disk fetches at first.
- The access scanner records hot keys every 24 h (10:00 GMT by default) when residency is below 95%, and warmup loads those keys first. It is CPU-intensive. 8.0 toggles it per bucket with `accessScannerEnabled` (default `true`). Before 8.0 it was a `cbepctl` setting.

## Compaction and Disk

Container defaults (`GET /settings/autoCompaction`, identical on 7.6.13 and 8.0.4): `databaseFragmentationThreshold` 30%, `magmaFragmentationPercentage` 50%, view fragmentation 30%, index compaction mode `circular` on all days, index fragmentation 30%, `purgeInterval` 3 (days; the tombstone purge interval), `parallelDBAndViewCompaction` false.

- Keep generous free disk. Couchstore compaction rewrites files, so it needs temporary space (inference; the fetched pages give no ratio).
- Magma's higher default fragmentation threshold uses more disk than Couchstore. Expect more disk use after migrating to Magma.
- 8.0.3 fixed Magma preallocation that left up to 25 GB per bucket of unreported disk use (MB-71423). On 8.0.0–8.0.2, compare `df` with the reported `magma_total_disk_usage` (on `/metrics` the 8.0.4 container exposes it as `kv_ep_magma_total_disk_usage_bytes`).
- 8.0 can stop Data Service writes at a filesystem usage limit (off by default). Turn it on so recovery is still possible when a disk fills.
- Bucket compression mode is `passive` by default (container). `active` compresses in the background at a CPU cost.

## Migrating a Bucket's Storage Engine (7.6+)

Online, per node. While a migration is pending, 7.6 lets you edit only `ramQuota` and `storageBackend`; 8.0 adds `evictionPolicy` (migrate-bucket pages for 7.6 and 8.0). Other parameters are refused: on both containers a `maxTTL` change returned 503 `Cannot update bucket while storage mode is being migrated`.

Ejection together with the backend differs by version (single-node containers, Couchstore/value-only bucket switched to Magma/full):

| Call | 7.6.13 | 8.0.4 |
|---|---|---|
| `storageBackend` + `evictionPolicy` + `noRestart=true` | 400 `noRestart option is not supported`; nothing changes | 200; node keeps its old backend and ejection until rewritten; no bucket restart |
| `storageBackend` + `evictionPolicy` | 200; the bucket restarts at once (`Restarting bucket "app" due to configuration change` in `info.log`) | 200 |
| `evictionPolicy` alone while pending | 400 `Eviction policy changes during storage mode migration require --no-restart option` | 200 with `noRestart=true` |

On 7.6, change ejection before or after the migration and accept the bucket restart.

```sh
# 1. Switch the bucket's backend; nodes keep an override until rewritten
curl -s -X POST -u Administrator:password http://127.0.0.1:8091/pools/default/buckets/app \
  -d storageBackend=magma
# 8.0 only: also change ejection without a restart
#   -d storageBackend=magma -d evictionPolicy=fullEviction -d noRestart=true
# 2. See which nodes still carry the old backend (null = migrated)
curl -s -u Administrator:password http://127.0.0.1:8091/pools/default/buckets/app \
  | jq '.nodes[] | .hostname, .storageBackend'
# 3. For each node: swap rebalance, OR graceful failover + FULL recovery + rebalance
curl -s -X POST -u Administrator:password http://127.0.0.1:8091/controller/startGracefulFailover -d 'otpNode=ns_1@node3.'
curl -s -X POST -u Administrator:password http://127.0.0.1:8091/controller/setRecoveryType -d 'otpNode=ns_1@node3.' -d recoveryType=full
curl -s -X POST -u Administrator:password http://127.0.0.1:8091/controller/rebalance -d 'knownNodes=ns_1@node1.,ns_1@node2.,ns_1@node3.'
```

Limits and pitfalls:

- Migrating to Magma always produces 1024 vBuckets. Changing between 128 and 1024 is impossible by migration; use local XDCR into a new bucket.
- The bucket must meet the target engine's minimum quota (1 GB for Magma/1024), or the REST call fails.
- When you change the ejection policy during a migration, use full recovery, not delta, and do not let the bucket restart.
- Without `noRestart=true`, an ejection change sent together with the backend change takes effect only when the migration finishes.
- Rollback: set `storageBackend` back. Disable history retention first (`historyRetentionCollectionDefault=false` on the bucket and `history=false` per collection). Then rewrite only the nodes that were already migrated.
- Rehearse on a restored copy and time one node's rewrite. Each node rewrite costs a full data copy for that node.

## Query and Index Service Settings

Container defaults, identical on 7.6.13 and 8.0.4 unless noted. Cluster-level values are from `GET /settings/querySettings` on 8091; node-level values from `GET :8093/admin/settings`.

| Setting (cluster / node) | Default | Meaning and when to change |
|---|---|---|
| `queryCompletedThreshold` / `completed-threshold` | 1000 ms | Requests slower than this go to `system:completed_requests`. Lower it temporarily for diagnosis. |
| `queryCompletedLimit` / `completed-limit` | 4000 | Entries kept per node |
| `queryCompletedStreamSize` / `completed-stream-size` | 0 (off) | MiB of completed requests streamed to disk. Node-level in 7.6.4+, cluster-level in 8.0. |
| `queryMemoryQuota` / `memory-quota` | 0 (unlimited) | Per-request memory cap |
| `queryNodeQuota` / `node-quota` | 0 | Node-wide Query memory cap |
| `queryTimeout` / `timeout` | 0 (none) | Server-side statement timeout. Set one cluster-wide to bound runaway queries. The value is in nanoseconds at both levels: after `queryTimeout=120000000000` (120 s), `/settings/querySettings` and the node's `timeout` both read back 120000000000 on both containers. |
| `queryTxTimeout` / `txtimeout` | `0ms` / `0s`; effective default 15 s | Transaction timeout |
| `queryMaxParallelism` / `max-parallelism` | 1 | Intra-query parallelism. Raise it for large scans on idle CPUs. |
| `queryTmpSpaceDir`, `queryTmpSpaceSize` | `/opt/couchbase/var/lib/couchbase/tmp`, 5120 | Size in MiB. 8.0: limit for Index Service backfill files and Query spill files (sort and similar); with both GSI and Search, disk use can reach three times this value. 7.6 documents it only for indexer backfill files ("MB"). `0` disables backfill, `-1` is unlimited (Query Settings REST pages) |
| `queryPreparedLimit` / `prepared-limit` | 16384 | Prepared statement cache size |
| `queryUseCBO` / `use-cbo` | true | Cost-based optimizer (EE) |
| `queryUseReplica` / `use-replica` | `unset` | Allow reads from replica vBuckets (7.6+) |
| `queryN1QLFeatCtrl` / `n1ql-feat-ctrl` | 76 | Feature bits. On 7.6.10+, auto-reprepare is bit 0x800000. |

```sh
# Cluster-wide: log requests slower than 500 ms on every Query node
curl -s -X POST -u Administrator:password http://127.0.0.1:8091/settings/querySettings \
  -d queryCompletedThreshold=500
# One node only (overwritten by the next cluster-level change)
curl -s -u Administrator:password http://127.0.0.1:8093/admin/settings \
  -H 'Content-Type: application/json' -d '{"completed-threshold": 500}'
```

Cluster-level query settings overwrite the node-level values on every Query node.

Index settings (`GET /settings/indexes`, both containers): `storageMode` `plasma`, `numReplica` 0, `indexerThreads` 0, `memorySnapshotInterval` 200, `stableSnapshotInterval` 5000, `maxRollbackPoints` 2, `enableShardAffinity` false, `redistributeIndexes` false. 8.0 adds `deferBuild` false.

## OS-Level Settings

- Swappiness 0 on every node. From 7.2.8 and 7.6.7, the installer sets it for the `couchbase-server` slice on cgroups v1 only. On cgroups v2, set it globally.
- Synchronize clocks with NTP on every node. Transactions and LWW conflict resolution need it.
- x86-64: AVX2 is required from 8.0.
- Transparent Huge Pages must be disabled: with THP on, performance can drop and the kernel can OOM-kill Couchbase (THP page).

## Verify a Configuration Change

- Bucket: `GET /pools/default/buckets/<b>`. Check `evictionPolicy`, `storageBackend`, `numVBuckets`, `replicaNumber`, `durabilityMinLevel`, `memoryLowWatermark`, `memoryHighWatermark`, `warmupBehavior` (8.0), and `basicStats.quotaPercentUsed`.
- Cluster: `GET /pools/default` (`memoryQuota` and the other quotas, `servicesNeedRebalance`, `balanced`). A `servicesNeedRebalance` entry means a rebalance is pending for that service. Fresh single-node containers showed `"services":["index"]` there.
- After a memory change: watch resident ratio, ejections, and temporary OOM errors for one traffic cycle; see [monitoring.md](monitoring.md).

Sources: Memory (https://docs.couchbase.com/server/current/learn/buckets-memory-and-storage/memory.html), Storage Engines 8.0, 7.6, and 7.2 (https://docs.couchbase.com/server/current/learn/buckets-memory-and-storage/storage-engines.html, https://docs.couchbase.com/server/7.6/learn/buckets-memory-and-storage/storage-engines.html, https://docs.couchbase.com/server/7.2/learn/buckets-memory-and-storage/storage-engines.html), Migrate a Bucket's Storage Backend (https://docs.couchbase.com/server/current/manage/manage-buckets/migrate-bucket.html), Creating and Editing Buckets (https://docs.couchbase.com/server/current/rest-api/rest-bucket-create.html), Automatic Failover, Manage and Monitor Queries, Couchbase Server Editions, Release Notes 7.2, 7.6, and 8.0, What's New 8.0, container outputs for 7.6.13 and 8.0.4, all checked 2026-11-27.
