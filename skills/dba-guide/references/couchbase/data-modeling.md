# Couchbase Data Modeling

Checked: 2026-11-27 (sources at the end). Applies to Couchbase Server 7.2–8.0 and Capella. Storage-engine and memory choices are in [configuration-and-sizing.md](configuration-and-sizing.md). Index design is in [indexes-and-queries.md](indexes-and-queries.md).

## Containers and What Each One Controls

The hierarchy is cluster → bucket → scope → collection → document. Pick the level by the settings it owns, not by naming habit.

| Level | Owns | Limits and notes |
|---|---|---|
| Bucket | Memory quota per node, storage engine (Couchstore or Magma), vBucket count, replica count, ejection policy, minimum durability level, conflict-resolution policy (fixed at creation), bucket `maxTTL`, compression, flush, XDCR source/target, encryption-at-rest key | `/pools/default` reports `"maxBucketCount":30` on both 7.6.13 and 8.0.4 containers. Each bucket takes a fixed memory share on every Data node. |
| Scope | A namespace for collections. RBAC can be granted per scope. Scope-level UDFs and sequences live here. | 1 to 251 characters; `A-Z a-z 0-9 _ - %`; cannot start with `_` or `%`; case sensitive; cannot be renamed. |
| Collection | Document type or entity set. Collection `maxTTL`, history retention (Magma), RBAC per collection, the unit that GSI indexes and XDCR mappings target | Same naming rules. Docs say up to 1000 scopes and 1000 collections per cluster. Both containers report `maxScopeCount` and `maxCollectionCount` of 1200, and both accepted more than 1000 collections in one bucket: creation stopped at 1200 collections outside `_default` and `_system`, with HTTP 429 "Maximum number of collections (1200) for this bucket has been reached". |
| Document | Key (id), value (JSON or binary), metadata (`rev`, `expiration`, `flags`, `type`, xattrs, CAS) | Value up to 20 MiB. Key up to 246 bytes in named collections, 250 bytes in `_default`. |

Bucket types:

- Couchbase bucket ("Memory and Disk" in Capella): persisted, can eject from memory.
- Ephemeral bucket ("Memory Only" in Capella): never persisted. With `nruEviction` it drops data when full; with `noEviction` (default) it rejects new writes when full. A restart loses data unless replicas exist.
- Memcached bucket: removed in 8.0. Replace with Ephemeral before upgrading.

Decision rules:

- Use one bucket per workload whose memory quota, storage engine, durability, replica count, or XDCR topology differs. Several buckets with tiny quotas waste memory and multiply per-bucket overhead. Couchstore has a 100 MiB floor, Magma/1024 a 1 GiB floor per node, Magma/128 a 100 MiB floor.
- Use scopes for tenants or applications that need separate RBAC but share bucket settings. Set the query context to the scope (`query_context=default:bucket.scope`) so statements use short collection names.
- Use one collection per document type instead of a `type` field in one keyspace. Indexes, TTL, RBAC, backup filters (`--include-data bucket.scope.collection`), and XDCR mappings all work per collection, and a query on one collection does not scan the others.
- Do not plan to keep data in `_default._default`. The default collection can be dropped, but once dropped it cannot be recreated, and some legacy tools (and pre-7.0 SDKs) only see `_default`. Data upgraded from before 7.0 lands there. Move it with XDCR migration mode (Enterprise) or `cbbackupmgr restore --map-data`.
- Do not write to `_system` (`_system._mobile`, `_system._query`, 7.6+). Couchbase services own it, its structure can change without notice, and it cannot be dropped.

## Create Scopes and Collections

```sql
CREATE SCOPE app.inv;
CREATE COLLECTION app.inv.orders;
-- 7.6+: collection TTL in seconds at creation
CREATE COLLECTION app.inv.sessions WITH {"maxTTL": 3600};
```

Container check: `CREATE SCOPE app.inv` and `CREATE COLLECTION app.inv.orders` succeeded on 7.6.13 and 8.0.4. So did `CREATE COLLECTION app.inv.sessions WITH {"maxTTL": 3600}`, after which `/pools/default/buckets/app/scopes` listed the collection with `"maxTTL":3600`.

List what exists:

```sql
SELECT RAW name FROM system:scopes WHERE `bucket` = "app";
SELECT `bucket`, `scope`, name FROM system:keyspaces WHERE `bucket` = "app";
```

Both statements returned rows on 7.6.13 and 8.0.4. Collection rows in `system:keyspaces` carry `bucket`, `scope`, and `name`; bucket-level rows have only `name` and no `bucket` or `scope`. Escape reserved words with backticks: on both containers, selecting a bare `using` column from `system:indexes` failed with syntax error 3000 ("using (reserved word)").

REST equivalent (useful in automation that has no Query node):

```sh
curl -s -u Administrator:password \
  http://127.0.0.1:8091/pools/default/buckets/app/scopes | jq '.scopes[] | {name, collections: [.collections[].name]}'
```

Production safety: `DROP COLLECTION` and `DROP SCOPE` delete every document in them immediately, with no recycle bin. Take a `cbbackupmgr` backup filtered to that keyspace first (`--include-data app.inv.orders`).

## Key Design

Facts that drive key choice:

- The key is hashed with CRC32 to one of the bucket's vBuckets. Scopes and collections do not affect placement. A KV get by key goes straight to the node holding the active vBucket, with no index involved.
- Keys are immutable and unique within a collection. To "rename" a key you insert a new document and delete the old one, which a transaction can make atomic.
- Keys may be any bytes, but use UTF-8 without spaces so every service accepts them.

Rules:

1. Make the primary access path a key lookup. Build keys from the identifier the application already holds: `order::2026-000123`, `user::42`, `user::42::cart`. A query by a predictable key costs one KV operation. The same lookup through SQL++ costs an index scan plus a fetch.
2. Keep keys short. Value-only ejection keeps every key and its metadata in memory (see [configuration-and-sizing.md](configuration-and-sizing.md)), so key length multiplies across all documents.
3. Do not rely on key prefixes for range reads. vBucket hashing scatters adjacent keys. Use a GSI index on a field, or `META().id` with an index, for range scans. KV range scan (7.6+) exists, but the 7.6 What's New notes that an index-backed query performs better.
4. For counters and high-write singletons, spread hot keys (for example `pageviews::2026-11-27::shard07`) when one document becomes a bottleneck. All writes to one key serialize on one active vBucket.
5. When keys contain user input, enforce a length cap below 246 bytes in the application.

## Document Shape

- A single-document write is atomic without a transaction. Group fields that must change together into one document. Transactions need several extra writes per document (ATR entries, staged xattrs, unstaging); see [transactions-and-durability.md](transactions-and-durability.md).
- Embed child data that is read with the parent and bounded in size. Reference (store keys) when children grow without bound, are shared, or change independently. Large arrays inflate every read, every replication over DCP, and every index on the array.
- Stay well below the 20 MiB value limit. Transactions should only touch documents under 10 MB.
- Use the Sub-Document API (`lookupIn`/`mutateIn` in the SDKs) to read or change a path without moving the whole document.
- Binary values can only be fetched by key. They cannot be indexed, queried, or filtered by body in XDCR.
- Extended attributes (xattrs) hold system metadata (transactions, Sync Gateway, XDCR versioning) and optional user metadata. 8.0 lets SQL++ `INSERT`, `UPSERT`, and `UPDATE` set up to 15 xattrs per statement. On 7.6, KV subdoc operations can touch several xattr keys in one call.

Inspect the actual shape before indexing or migrating:

```sql
INFER app.inv.orders WITH {"sample_size": 1000};
```

`INFER` returns field names, types, sample values, and the share of sampled documents that have each field (`#docs`, `%docs`). It returns one schema per document flavor: in the containers, the order documents and a batch of 100 differently shaped test documents in the same collection came back as two schemas. Fields present in a small fraction of documents are candidates for partial indexes.

## Expiration (TTL)

- Document expiry is set per write by the SDK, or by default from the collection `maxTTL`, then the bucket `maxTTL`. `maxTTL` acts as both a default and an upper limit. A change applies only to documents created or mutated afterwards.
- 7.6+: `maxTTL` on a collection can be changed after creation, and `-1` exempts the collection from a non-zero bucket `maxTTL`.
- The expiry pager runs every 600 s by default (`expiryPagerSleepTime`, bucket REST setting in 8.0). It deletes expired items and leaves tombstones. Tombstones are purged after the metadata purge interval. Containers show `"purgeInterval":3` (days) in `/settings/autoCompaction`.
- A read of an expired document returns not-found even before the pager runs.
- XDCR replicates expirations as deletes by default; see [replication-and-xdcr.md](replication-and-xdcr.md).
- Backups and TTL: `cbbackupmgr restore --replace-ttl all --replace-ttl-with 0` clears document TTLs on restore but does not override a target collection or bucket `maxTTL`.

## Common Mistakes

- Creating one bucket per tenant. The bucket cap (30 in the containers) and per-bucket memory floors make this fail at scale. Use scopes.
- Keeping a `type` field in `_default` and indexing `WHERE type = "x"` everywhere, instead of collections.
- Using SQL++ for lookups by known key. Use KV `get`, or `USE KEYS` in SQL++ when a statement must run.
- Writing scripts that create buckets without `storageBackend` and `numVBuckets`. The defaults changed in 8.0.
- Flushing a bucket on 7.6+ without recreating scope-level UDFs, sequences, and CBO statistics stored in `_system._query`.

## Verify a Model Change

1. Confirm the keyspaces: `SELECT * FROM system:keyspaces WHERE ...` and `/pools/default/buckets/<b>/scopes`.
2. Confirm item counts per collection after a migration, either with `SELECT COUNT(*) FROM app.inv.orders` and `scan_consistency=request_plus`, or with the `kv_collection_item_count` metric (present on both containers' `/metrics`, labeled by `bucket`, `scope`, and `collection`).
3. Confirm memory: `basicStats.memUsed` and `quotaPercentUsed` in `/pools/default/buckets/<b>`.
4. On 7.6.13, a `COUNT(*)` issued right after inserting 5000 documents returned 3354 at the default `not_bounded` consistency; 8.0.4 returned 5000. Do not validate a migration with an unbounded count. Use `request_plus`.

Sources: Scopes and Collections (https://docs.couchbase.com/server/current/learn/data/scopes-and-collections.html), Data (https://docs.couchbase.com/server/current/learn/data/data.html), vBuckets (https://docs.couchbase.com/server/current/learn/buckets-memory-and-storage/vbuckets.html), Memory (https://docs.couchbase.com/server/current/learn/buckets-memory-and-storage/memory.html), Transactions (https://docs.couchbase.com/server/current/learn/data/transactions.html), Creating and Editing Buckets (https://docs.couchbase.com/server/current/rest-api/rest-bucket-create.html), What's New 7.6 and 8.0, container outputs for 7.6.13 and 8.0.4, all checked 2026-11-27.
