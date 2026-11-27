# Couchbase Replication, Failover, Rebalance, and XDCR

Checked: 2026-11-27 (sources at the end). Applies to Couchbase Server 7.2–8.0. Durability interactions are in [transactions-and-durability.md](transactions-and-durability.md).

## Contents

- vBuckets and replicas
- Rebalance
- Failover types and when to use each
- Automatic failover settings
- Recovery after failover
- XDCR: setup, topology, conflict resolution, compatibility
- XDCR monitoring and verification

## vBuckets and Replicas

- Each bucket is split into a fixed number of vBuckets: 1024 for Couchstore; 128 or 1024 for Magma (chosen at creation, 8.0+; Magma is 1024 before 8.0); 64 on macOS. The count never changes after creation. To change it, replicate into a new bucket with local XDCR (one cluster as both source and target).
- Keys map to vBuckets by CRC32 (`"hashAlgorithm":"CRC"` in the bucket's `vBucketServerMap`). The cluster map tells clients which node holds each active vBucket. The active copy and each replica are always on different nodes.
- `replicaNumber` is 0–3 (default 1). Changing it on an existing bucket takes effect after a rebalance. Durable writes support at most 2 replicas.
- Server groups place replicas across groups (racks or zones). Auto-failover of a whole group requires a quorum among the remaining nodes and `maxCount` at least the group size. With two equal groups, add an arbiter node in a third location so the survivors keep a majority.
- Replication inside a cluster uses DCP and is asynchronous unless a durable write waits for it.

Evidence:

```sh
curl -s -u Administrator:password http://127.0.0.1:8091/pools/default/buckets/app \
  | jq '{storageBackend, numVBuckets, replicaNumber, map: .vBucketServerMap.numReplicas,
         servers: .vBucketServerMap.serverList}'
# vBucketMap entries are [active_index, replica_index...]; -1 means no replica assigned.
# A one-node container shows [0,-1] for every vBucket: replica configured but nowhere to place it.
```

## Rebalance

Rebalance moves vBuckets, index partitions, and service work to match the current set of nodes. Applications keep running during it. Rebalance is needed after adding or removing nodes, after a failover, after a replica-count change, and to finish a storage-engine migration.

Facts:

- Stages run per service: Data, Query, Index, Search, Eventing, Backup, Analytics.
- Data moves are sequential per vBucket. A stopped rebalance can be restarted and continues from where it stopped.
- Concurrent vBucket moves per node: default 4, range 1–64. Higher values finish sooner but compete with the workload for CPU, disk, and network.
- Bucket `rank` (7.6+, 0–1000) orders buckets in the rebalance.
- Rebalance retries on failure: up to 3, configurable.
- Reports: the last five are kept under `/opt/couchbase/var/lib/couchbase/logs/rebalance/rebalance_report_<time>.json`. They are also available through `GET /pools/default/tasks` and the UI.
- Query nodes being removed wait for in-flight requests and transactions. Late requests can get error 1181 `E_SERVICE_SHUT_DOWN` or HTTP 503; retry them on another Query node.
- The Backup Service scheduler pauses during a rebalance.
- Index rebalance either rebuilds indexes over DCP or moves index files (file-based rebalance, 7.6+). 8.0 docs say on-premises clusters keep file-based rebalance off by default.
- Swap rebalance (as many nodes in as out, same services) moves data only between the swapped nodes. It is the lowest-impact way to replace or upgrade nodes.

Commands:

```sh
# Add a node, then rebalance
couchbase-cli server-add -c 10.0.0.1:8091 -u Administrator -p password \
  --server-add 10.0.0.4:8091 --server-add-username Administrator \
  --server-add-password password --services data
couchbase-cli rebalance -c 10.0.0.1:8091 -u Administrator -p password
# Remove a node safely (replicas are re-created on the remaining nodes)
couchbase-cli rebalance -c 10.0.0.1:8091 -u Administrator -p password --server-remove 10.0.0.3:8091
# Progress and status
curl -s -u Administrator:password http://10.0.0.1:8091/pools/default/rebalanceProgress
curl -s -u Administrator:password http://10.0.0.1:8091/pools/default/tasks | jq '.[] | select(.type=="rebalance")'
```

`couchbase-cli server-add -h` lists `--server-add`, `--server-add-username`, `--server-add-password`, `--group-name`, and `--services` on both images. 7.6.13 marks the username and password as required, and 8.0.4 makes them optional and adds `--use-client-cert`. `rebalance -h` lists `--server-remove` on both, and 8.0.4 adds per-service flags such as `--index-add` and `--query-remove` with `--update-services`. In the containers, `--help` tries to open a man page that the minimized image lacks; use `-h`.

Removal versus failover: removal (rebalance out) re-creates the replicas that would be lost, so redundancy stays intact. Failover promotes replicas but does not re-create them until the next rebalance, so the cluster runs with fewer copies in between. To retire a healthy node, remove it. Do not fail it over.

## Failover Types and When to Use Each

| Type | When | Effect | Command |
|---|---|---|---|
| Graceful | A responsive Data node must leave quickly, for maintenance or upgrade | Replicas are brought up to date, then promoted. No data loss. Data Service nodes only. | `couchbase-cli failover -c host:8091 -u ... -p ... --server-failover node:8091` (graceful is the default) |
| Hard | The node is unresponsive or already down | Immediate replica promotion. Writes not yet replicated are lost. | `... --server-failover node:8091 --hard` |
| Hard, forced | Most nodes are gone and no quorum exists | Overrides the quorum requirement. Risk of divergent state. | `... --hard --force`. Last resort only. |
| Automatic | The cluster manager detects an unresponsive node or an unhealthy Data or Index service | Always a hard failover, subject to the safety checks below | Configured with `setting-autofailover` |

Do not hard-fail over a responsive node. It disrupts in-flight writes and replication; use graceful failover or removal. After any failover, rebalance to restore the active-to-replica ratio and redundancy.

REST equivalents (controllers listed in `/pools/default` in both containers): `/controller/startGracefulFailover`, `/controller/failOver`, `/controller/setRecoveryType`, `/controller/rebalance`, `/controller/reAddNode`, `/controller/ejectNode`.

```sh
curl -X POST -u Administrator:password http://10.0.0.1:8091/controller/startGracefulFailover \
  -d 'otpNode=ns_1@10.0.0.3'
```

## Automatic Failover Settings

Defaults on both 7.6.13 and 8.0.4 containers (`GET /settings/autoFailover`): `"enabled":true,"timeout":120,"maxCount":1,"count":0`, `failoverOnDataDiskIssues` off (period 120 s), `failoverPreserveDurabilityMajority` false, `canAbortRebalance` true. 8.0 adds `failoverOnDataDiskNonResponsiveness` (off, 120 s) and `allowFailoverEphemeralNoReplicas` (false).

| Setting | Range and default | Decide |
|---|---|---|
| Timeout | 120 s default; REST minimum 1 s on 7.6+ (5 s in the UI); maximum 3600 s | Lower values fail over sooner but trigger on short network blips. Below 5 s, the 7.6 UI can no longer edit cluster settings (MB-60062). |
| `maxCount` (EE) | Default 1; CE fixed at 1 | Set it to at least the size of a server group if a whole group may fail. Keep it below the durability majority if you do not use preserve-durable-writes. |
| `count` | Failovers since the last reset | A rebalance resets it to 0. While `count` equals `maxCount`, no further auto-failover happens. Do not reset it by hand except under Support guidance. |
| Disk issues | Off; period 1–3600 s | Fails over when at least 60% of the period consists of disk read/write errors |
| Disk non-responsiveness (8.0) | Off | Fails over on hung disk I/O even without errors |
| Preserve durable writes (EE) | Off | Blocks auto-failovers that could lose durably written data. Data nodes only. |
| Ephemeral without replicas (EE, 8.0) | Off | Allows failover of nodes holding unreplicated Ephemeral buckets. Their data on that node is lost and empty vBuckets replace it. |

Auto-failover does not happen when:

- the remaining nodes cannot form a majority quorum (18 nodes need 10; 17 need 9),
- `count` has reached `maxCount`,
- the node holds a bucket with no replicas, Couchbase or Ephemeral (unless the 8.0 Ephemeral option is on),
- the service-specific minimum is not met: Data, Query, Index, Search, Analytics, and Eventing each need the service running on at least 2 nodes. Data Service preference lets a Data node fail over even when a co-located service is below its minimum,
- preserve-durable-writes forbids it.

Only Data and Index health is monitored. A node running only Query, Search, Eventing, Analytics, or Backup is not auto-failed over while its cluster manager keeps sending heartbeats.

```sh
curl -s -u Administrator:password http://127.0.0.1:8091/settings/autoFailover | jq .
couchbase-cli setting-autofailover -c 127.0.0.1:8091 -u Administrator -p password \
  --enable-auto-failover 1 --auto-failover-timeout 120 --max-failovers 2 \
  --can-abort-rebalance 1
```

On both containers this returned `SUCCESS: Auto-failover settings modified`, and `GET /settings/autoFailover` then showed `"maxCount":2`. `--enable-failover-of-server-groups` does not exist in either image (`ERROR: unrecognized arguments: --enable-failover-of-server-groups 1`). `setting-autofailover -h` has no separate server-group flag. 8.0.4 adds `--enable-failover-on-data-disk-non-responsive`, `--failover-data-disk-non-responsive-period`, and `--allow-failover-for-ephemeral-without-replica`.

`couchbase-cli setting-autofailover --get` does not exist. Both containers returned `ERROR: unrecognized arguments: --get`. Read the settings with the REST call.

Auto-failover of the orchestrator node can take significantly longer, because timeouts must expire before the other nodes elect a new orchestrator (automatic failover page; no duration given). The 10 s in the `terseClusterInfo` docs is a different case: after the orchestrator node is rebalanced out, `orchestrator` reads `"undefined"` for 10 s until a new one is elected. An arbiter node (no services, 7.6+) gives faster failover. Find the orchestrator with `GET /pools/default/terseClusterInfo`.

## Recovery After Failover

A failed-over node can be removed (rebalance out) or recovered (added back with a rebalance).

| Recovery | What happens | Use when |
|---|---|---|
| Delta | Keeps the node's data and streams only the mutations it missed | The node is healthy, was failed over (normally gracefully), and the topology has not changed |
| Full (CLI default) | Deletes the node's data and copies it fresh. GSI indexes on the node are kept and caught up. | After a hard failover, after topology changes, when finishing a storage-engine migration, or when the node's data is suspect |

```sh
couchbase-cli recovery -c 10.0.0.1:8091 -u Administrator -p password \
  --server-recovery 10.0.0.3:8091 --recovery-type delta
couchbase-cli rebalance -c 10.0.0.1:8091 -u Administrator -p password
```

Delta falls back to full, or fails, when the topology changed, when the node was hard-failed over and marked for removal, when nodes in and out are unequal in the same rebalance, when bucket operations ran while delta was pending, or when a node crashes during recovery. For very large datasets far beyond the bucket memory quota, full recovery can be faster than delta.

Indexes can serve `not_bounded` scans as soon as they warm up during recovery. Other scans error until a consistent snapshot exists, so clients can try replicas.

## XDCR

XDCR pushes mutations over DCP from a source bucket to a target bucket on another cluster, or on the same cluster with a different bucket. It runs independently of intra-cluster replication. It replicates data only: indexes, views, users, and bucket settings must be created on the target separately.

Edition: the editions page says the Community Edition license now disallows XDCR. Explicit collection mapping and migration mode are Enterprise-only in any case.

### Setup

```sh
# 1. Remote cluster reference (full TLS: data and credentials encrypted)
couchbase-cli xdcr-setup -c 10.0.0.1:8091 -u Administrator -p password --create \
  --xdcr-cluster-name dr --xdcr-hostname 10.1.0.1 \
  --xdcr-username xdcr_user --xdcr-password '***' \
  --xdcr-secure-connection full --xdcr-certificate /path/dr-root-ca.pem
# 2. Replication
couchbase-cli xdcr-replicate -c 10.0.0.1:8091 -u Administrator -p password --create \
  --xdcr-cluster-name dr --xdcr-from-bucket app --xdcr-to-bucket app --priority High
# 3. List and pause
couchbase-cli xdcr-replicate -c 10.0.0.1:8091 -u Administrator -p password --list
```

`--xdcr-secure-connection` accepts `none` (default), `half`, or `full`. `half` protects only the password, with SCRAM-SHA. Use `full` across untrusted networks. 7.6 adds a connection pre-check before you create the reference. The target user needs the XDCR inbound role (`replication_target`) on the target bucket. The source user needs `replication_admin`.

### Topology and Mapping

- Unidirectional for disaster recovery. Bidirectional (two unidirectional replications) for active-active. Rings and other shapes are built from the same pieces.
- Collections: implicit mapping when `scope.collection` names match. Explicit mapping and migration from `_default` to named collections are EE-only. Migration combined with deletion filters can lose data.
- Filters: a regular expression on keys or an expression on body or xattrs. Binary documents can be included or excluded (7.6+). Deletion and expiration filters control whether deletes propagate. 7.6.10 adds `filterDeletionsWithExpression` and `filterExpirationsWithExpression`. Changing a filter restarts the replication, and a race could skip documents (MB-66649, MB-66140). If the UI raises the "stale checkpoints" alert, delete and recreate the replication. Do not pause and resume it.
- Priority: High (default, no throttling), Medium (throttled during the initial copy when competing), Low (throttled whenever competing).
- Flush: flushing a source bucket is blocked while it replicates. Flushing a target suspends the replication. To flush either side, delete the replication, flush, and recreate it.
- Non-UTF-8 document IDs are not replicated. The source logs `xdcr_error.*`.

### Conflict Resolution

Each bucket has a conflict-resolution policy fixed at creation. Source and target must match, or the replication cannot be created.

| Policy | Winner | Tie-breakers | Choose for |
|---|---|---|---|
| Sequence number (`seqno`, default) | The document with more mutations (`rev`) | CAS, then TTL, then flags | Counter-like documents where the most-updated copy is most useful |
| Timestamp / last write wins (`lww`) | The more recent HLC timestamp (in CAS) | seqno, TTL, flags | Most active-active designs, transactions with XDCR, and newer features. The docs prefer it generally. |

LWW requires NTP on every node in every cluster. Monitor drift.

Safe application failover with LWW: redirect traffic from cluster A to B only after the larger of (a) the replication latency A→B and (b) the absolute clock skew between A and B. Wait the same period when failing back.

Target-side conflict metrics: `kv_conflicts_resolved{op="set|del",result="accepted|rejected_behind|rejected_identical"}`, plus `xdcr_docs_failed_cr_source_total` and `xdcr_docs_failed_cr_target_total`. 8.0 adds conflict logging to a collection for active-active pairs.

### Version and vBucket Compatibility

| Source → target | Rule |
|---|---|
| pre-8.0 → 8.0 | Buckets must have the same vBucket count. Create the 8.0 target with `storageBackend=couchstore`, or `magma` with `numVBuckets=1024`. A Magma/128 target is impossible. |
| 8.0 → pre-8.0 | Counts may differ, but a mismatched pair cannot be bidirectional |
| 8.0 ↔ 8.0 | Any counts |
| ECCV (`enableCrossClusterVersioning`, 7.6.6+) | If it is enabled on one bucket in a topology, enable it on every bucket in that topology. Buckets on releases before 7.6.6 cannot join an ECCV topology. Once on, it cannot be turned off; the only undo is backup, new bucket, and `cbbackupmgr restore --disable-hlv`. XDCR does not validate ECCV consistency. Check it by hand (`jq .enableCrossClusterVersioning` on each bucket). |

### XDCR and Recovery

- `cbrecovery` copies lost vBuckets back from an XDCR target when the source lost every copy (multiple simultaneous node failures).
- A DR cluster kept on the previous version is also the documented fallback for a finalized major upgrade that must be rolled back.

## XDCR Monitoring and Verification

- Replication status and errors: `couchbase-cli xdcr-replicate --list` and the UI XDCR tab. 8.0 also lists incoming replications on the target.
- Backlog: watch `xdcr_changes_left_total` (gauge since 7.0.0; sequence numbers this node's vBuckets still have to process, XDCR metrics reference). It should trend to 0 under steady load.
- Content check: `xdcrDiffer` (bundled in `/opt/couchbase/bin` from 8.0, built from source before) compares source and target documents and metadata.
- Counts differ legitimately because of transaction ATR documents, filters, and binary-document exclusion.

Verify a failover-to-DR plan:

1. `changes_left` is near 0 and steady.
2. Wait at least max(replication latency, clock skew) after stopping writes on A (LWW).
3. Point applications at B. Create indexes on B beforehand; they are not replicated.
4. Keep the reverse replication paused until A is healthy, then resume and let it drain before failing back.

Sources: vBuckets (https://docs.couchbase.com/server/current/learn/buckets-memory-and-storage/vbuckets.html), Rebalance (https://docs.couchbase.com/server/current/learn/clusters-and-availability/rebalance.html), Failover (https://docs.couchbase.com/server/current/learn/clusters-and-availability/failover.html), Automatic Failover (https://docs.couchbase.com/server/current/learn/clusters-and-availability/automatic-failover.html), Recovery (https://docs.couchbase.com/server/current/learn/clusters-and-availability/recovery.html), couchbase-cli failover (https://docs.couchbase.com/server/current/cli/cbcli/couchbase-cli-failover.html), couchbase-cli recovery (https://docs.couchbase.com/server/current/cli/cbcli/couchbase-cli-recovery.html), XDCR Overview (https://docs.couchbase.com/server/current/learn/clusters-and-availability/xdcr-overview.html), XDCR Conflict Resolution (https://docs.couchbase.com/server/current/learn/clusters-and-availability/xdcr-conflict-resolution.html), couchbase-cli xdcr-setup (https://docs.couchbase.com/server/current/cli/cbcli/couchbase-cli-xdcr-setup.html), couchbase-cli xdcr-replicate (https://docs.couchbase.com/server/current/cli/cbcli/couchbase-cli-xdcr-replicate.html), Couchbase Server Editions (https://docs.couchbase.com/server/current/introduction/editions.html), Release Notes 7.6 and 8.0, container outputs for 7.6.13 and 8.0.4, all checked 2026-11-27.
