# Couchbase Transactions and Durability

Checked: 2026-11-27 (sources at the end). Applies to Couchbase Server 7.2–8.0. Replica placement and failover mechanics are in [replication-and-xdcr.md](replication-and-xdcr.md).

## Consistency Model in One Table

| Operation | Guarantee | Notes |
|---|---|---|
| KV write to one document | Atomic. Immediately visible to KV reads, which go to the active vBucket | Acknowledged once the write is in the active node's memory, unless durability is requested |
| KV read | Reads the active copy. Replica reads are opt-in and may be stale | Since 7.6, Query can read replicas when actives are unavailable (`use_replica`) |
| GSI / Search / Analytics | Eventually consistent with KV | Use scan consistency (see [indexes-and-queries.md](indexes-and-queries.md)) |
| Multi-document transaction | Atomic. Read Committed, with Monotonic Atomic View for transactional reads | Lost updates prevented by CAS checks; no foreign keys |
| XDCR | Eventually consistent between clusters; conflict resolution per bucket policy | A target can receive a partial transaction if the link drops |

## Durability Levels

A durable write is synchronous: the server reports success only after the requirement is met. A failed durable write is rolled back on active and replicas.

| Level | Requirement | Bucket types |
|---|---|---|
| `none` | Acknowledged from active memory (regular asynchronous write) | All |
| `majority` | A majority of copies hold the mutation in memory | Couchbase, Ephemeral |
| `majorityAndPersistActive` | Majority in memory, and persisted on the active node | Couchbase only |
| `persistToMajority` | Persisted on a majority of copies | Couchbase only |

Majority by replica count: 0 replicas → 1 node; 1 replica → 2; 2 replicas → 2; 3 replicas → durability not supported (`EDurabilityImpossible`).

Where it is set:

- Per operation by the SDK (SDK default timeout 10 s).
- Per bucket as a floor: `durabilityMinLevel` (`none`, `majority`, `majorityAndPersistActive`, `persistToMajority`; Ephemeral only `none` or `majority`). It can be changed after creation. When client and bucket both set a level, the higher one applies.
- In SQL++: the request parameter `durability_level`. It takes the bucket level names. On both containers, `UPSERT` with `durability_level` `majority`, `majorityAndPersistActive`, and `persistToMajority` succeeded on a one-node bucket with `replicaNumber=0`, and `none` succeeded everywhere.

```sh
curl -s -X POST -u Administrator:password \
  http://127.0.0.1:8091/pools/default/buckets/app -d durabilityMinLevel=majority
curl -s -u Administrator:password http://127.0.0.1:8091/pools/default/buckets/app | jq .durabilityMinLevel
```

Decision rules:

- Use `majority` for data whose loss on a single-node failure is unacceptable. It costs one replication round trip.
- Use `persistToMajority` when you must survive the simultaneous loss of several nodes, for example a rack or zone power loss. It costs disk syncs on two nodes. Allocate enough writer threads if durable throughput is low (Data Settings).
- Keep regular writes for data that can be regenerated, such as caches and sensor streams.
- Use 1 or 2 replicas on buckets that take durable writes. With 3 replicas, durable writes fail.
- A bucket with 1 replica that loses one Data node cannot complete durable writes to the vBuckets that lived there until the node returns or a rebalance restores replicas.

Errors and ambiguity:

- `SYNC_WRITE_IN_PROGRESS`: another durable write on the same key is pending. Retry.
- Ambiguous result (timeout, active node failure, or a vBucket move during rebalance): the write may or may not have committed. Retry only idempotent writes. Otherwise read the document and compare before retrying.
- `DURABILITY_IMPOSSIBLE`: not enough nodes for the majority. Both containers (one node, bucket with `replicaNumber` 1) rejected `UPSERT ... durability_level=majority` with error 12009 and cause `DURABILITY_IMPOSSIBLE`. The same statement with `durability_level=none` succeeded. On a one-node development cluster, set `replicaNumber=0` on buckets used by transactions, or every durable write fails. A replica change on an existing bucket needs a rebalance.

### Keeping Durable Writes Available During Maintenance (8.0)

`durabilityImpossibleFallback` (bucket setting, REST only): `disabled` (default; container shows `"durabilityImpossibleFallback":"disabled"`) or `fallbackToActiveAck`. With `fallbackToActiveAck`, a durable write that cannot reach a majority is reported as successful once the active copy has it. This keeps transactions working during a graceful-failover upgrade of a 1-replica bucket, but durability during that window is no better than an asynchronous write.

```sh
# Before the maintenance window
curl -s -X POST -u Administrator:password \
  http://127.0.0.1:8091/pools/default/buckets/app -d durabilityImpossibleFallback=fallbackToActiveAck
# Immediately after every node is back and rebalanced
curl -s -X POST -u Administrator:password \
  http://127.0.0.1:8091/pools/default/buckets/app -d durabilityImpossibleFallback=disabled
```

The durability concept page says to set the option "to `true`", while the bucket REST reference lists `disabled | fallbackToActiveAck`. Use the REST reference values. 8.0.4 accepted both of those and rejected `true` with HTTP 400 "Durability impossible fallback must be either 'disabled' or 'fallbackToActiveAck'".

### Failover Can Lose Durable Writes

If every node in the majority that acknowledged a durable write fails over before the write reaches the remaining copies, the write is lost and the client has already seen success. Protect against this (Enterprise Edition):

- keep auto-failover `maxCount` below the durability majority (the default `maxCount` is 1), or
- enable "preserve durable writes" (`failoverPreserveDurabilityMajority`, false by default in both containers). This stops auto-failover from removing more Data nodes than the majority allows. It affects Data nodes only.
- When failing over manually, do not fail over more Data nodes at once than the majority permits.

Community Edition: `maxCount` is always 1 and the preserve option does not exist.

## CAS and Locking

- Every document has a CAS value. Its 64 bits hold a hybrid logical clock timestamp: the high 48 bits physical, the low 16 bits logical. Transactions prevent lost updates by checking CAS, which acts as an optimistic lock. Applications get the same protection outside transactions by sending the CAS they read with their replace or remove (SDK feature; exact API per SDK).
- Pessimistic locking (SDK get-and-lock) holds a document until unlock, a write carrying the lock's CAS, or the lock timeout. The lock lasts at most 30 s; a longer request falls back to the server default of 15 s. A plain get on a locked document succeeds but returns an invalid CAS (Java SDK concurrent document mutations page; other SDKs use the same server operation). Server behavior changes: since 7.2.4, after a lock timeout the CAS reverts to its original value (MB-59746). Since 7.6, unlocking a document that is not locked returns a "not locked" error instead of a temporary failure (MB-58088). Since 8.0, subdoc gets on a locked document succeed and return CAS `0xffffffffffffffff` (MB-66015).
- 8.0 (and 7.6.13) rejects SET and DELETE with-meta operations whose CAS is more than `hlc_max_future_threshold` (65 minutes) ahead (MB-61385). This prevents a faulty CAS from distorting the vBucket's `max_cas`, which XDCR LWW conflict resolution depends on.

## Distributed ACID Transactions

Mechanics that drive cost and troubleshooting:

- Each attempt writes an entry in an Active Transaction Record (ATR) document with key prefix `_txn:atr-`. By default ATRs live in the default collection of the bucket of the first mutated document. Configure a metadata collection if `_default` is dropped or RBAC must isolate it. For SQL++ transactions, use the `atrcollection` setting.
- Mutations are staged in the document's xattrs until commit. The staged change acts as a write lock against other transactions.
- Commit flips the ATR entry, which is the atomic commit point, then unstages each document. Non-transactional readers see documents change one by one after the commit point. Transactional readers see all or nothing.
- A cleanup process inside each application's `Transactions` object removes leftovers of failed attempts. If no application is running, that cleanup does not run. The Query Service has its own cleanup settings (`queryCleanupClientAttempts`, `queryCleanupLostAttempts`, window 60 s in the containers).
- Default transaction expiry is 15 s. The containers show `transactionRemainingTime` of about 15 s right after `BEGIN WORK`, with node setting `txtimeout` `"0s"` and cluster `queryTxTimeout` `"0ms"`. On transient conflicts the transaction retries until it expires, then rolls back.
- Transactions require NTP-synchronized clocks on all nodes.

Costs and rules:

- Each transactional write costs more writes than a plain write (ATR updates, staging, unstaging), all durable at the transaction's level (default `majority`). Prefer single-document atomicity when the model allows it.
- Keep transactions short and small. With SQL++ inside a transaction, every mutation grows a delta table in Query memory, limited by the query `memory-quota`. For bulk changes that need atomicity, use a single-statement implicit transaction (`tximplicit=true`), which keeps no delta table.
- Do not mix non-transactional writes with an in-flight transaction on the same documents. The non-transactional write can be overwritten, or can break the transaction's integrity.
- Only documents under 10 MB.
- Inside a transaction, SQL++ statements default to `request_plus` consistency. Use `not_bounded` only for `USE KEYS` lookups, data you know is not recently changed, or blind `INSERT`/`UPSERT`.

SQL++ transaction (cbq, or REST against port 8093). Each statement after `BEGIN` must carry the returned `txid`; cbq tracks it for you:

```sql
\SET -txtimeout "2m";
\SET -durability_level "majority";
BEGIN TRANSACTION;           -- BEGIN WORK also works (container)
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
UPDATE app.inv.orders SET total = total + 1 WHERE META().id = "order::1";
SAVEPOINT s1;
UPDATE app.inv.orders SET status = "paid" WHERE META().id = "order::1";
ROLLBACK TRANSACTION TO SAVEPOINT s1;
COMMIT TRANSACTION;          -- COMMIT WORK also works (container)
```

Container evidence (both versions, one node, `durability_level=none` on the request): `BEGIN WORK` returned `{"nodeUUID": "...", "txid": "..."}`. An `UPDATE ... txid=<id>` reported `mutationCount 1` and `transactionRemainingTime` about 14.9 s. `COMMIT WORK txid=<id>` succeeded.

Over REST, send `txid` in every request after `BEGIN`. The `BEGIN` response includes `nodeUUID`. Inference, not stated in the documentation: later statements must reach the same Query node, so a load balancer in front of port 8093 needs affinity.

RBAC: KV operations in a transaction need Data roles. Query statements need Query roles. Once a transaction runs a query statement, later KV operations in it run with the user's query permissions.

## Transactions and XDCR

- XDCR never ships uncommitted changes, but documents arrive one by one. A broken link can leave the target with part of a transaction.
- Document counts differ between source and target because transaction metadata documents are not replicated.
- Avoid active-active XDCR with transactions. If you must, partition document ownership by key between clusters, and retry a failed transaction on the same cluster.
- Use timestamp-based (LWW) conflict resolution for buckets used with transactions and XDCR, and follow the safe-failover wait in [replication-and-xdcr.md](replication-and-xdcr.md).

## Diagnose

- Durable write latency: the `kv_sync_write_commit_duration_seconds` histogram, the `kv_vb_sync_write_accepted_count`, `kv_vb_sync_write_committed_count`, and `kv_vb_sync_write_aborted_count` counters (both containers; 8.0.4 adds `kv_vb_sync_write_committed_not_durable_count`), and Data Service writer-thread saturation.
- Long or stuck SQL++ transactions: `system:transactions` and `system:active_requests`. On both containers, `SELECT * FROM system:transactions` listed an open transaction before `COMMIT WORK`, with `id` (the `txid`), `status`, `timeout` (`15s`), `expiryTime`, `lastUse`, `uses`, `durabilityLevel`, `scanConsistency`, and `usedMemory`.
- Leftover staged documents: documents with transaction xattrs and old ATR entries. Confirm that an application with a `Transactions` object, or a Query node with cleanup enabled, is running.
- Ambiguous outcomes during rebalance happen occasionally by design. Make retried writes idempotent.

Sources: Durability (https://docs.couchbase.com/server/current/learn/data/durability.html), Transactions (https://docs.couchbase.com/server/current/learn/data/transactions.html), SQL++ Transactions (https://docs.couchbase.com/server/current/n1ql/n1ql-language-reference/transactions.html), Creating and Editing Buckets (https://docs.couchbase.com/server/current/rest-api/rest-bucket-create.html), Automatic Failover (https://docs.couchbase.com/server/current/learn/clusters-and-availability/automatic-failover.html), XDCR Conflict Resolution (https://docs.couchbase.com/server/current/learn/clusters-and-availability/xdcr-conflict-resolution.html), Release Notes 7.2, 7.6, and 8.0, container outputs for 7.6.13 and 8.0.4, all checked 2026-11-27.
