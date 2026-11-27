# Redis Data Modeling

Checked: 2026-11-27 (sources at the end). Applies to Redis Open Source 6.2 to 8.12. Version-specific commands link to the version files.

## Choose a Type

| Need | Type | Notes |
|---|---|---|
| Opaque value, counter, flag, lock | String | `INCR`/`INCRBY` are atomic; `SET ... NX PX` for locks; compare-and-set with `SET ... IFEQ` since [8.4](versions/8.6.md#changes-first-shipped-in-84) |
| Object with fields, partial updates | Hash | Field TTLs since [7.4](versions/7.4.md); compact hashes for many hashes with the same fields since [8.10](versions/8.10.md) |
| Queue, recent-N list | List | `LMOVE`/`BLMOVE` for reliable queues (6.2+); `LMOVEM` since [8.10](versions/8.10.md) |
| Membership, dedup | Set | Member TTLs since [8.12](versions/8.12.md) |
| Ranking, time index, priority queue | Sorted set | `ZRANGE ... BYSCORE` (6.2+); atomic moves `ZMOVE` since [8.12](versions/8.12.md) |
| Event log with consumer groups | Stream | Bound growth with `XADD ... MAXLEN ~`/`MINID`; `XACKDEL`/`XDELEX` since [8.2](versions/8.2.md); idempotent `XADD` since [8.6](versions/8.6.md) |
| Bit flags per integer ID | Bitmap (string) | 100 million users fit in about 12 MB (memory optimization docs); Roaring-compressed bitmaps optional since [8.12](versions/8.12.md) |
| Approximate distinct count | HyperLogLog | Dense size about 12 KB per key: after 20000 `PFADD` elements, `STRLEN` 12304 and `MEMORY USAGE` 14358 bytes on 8.12.0 |
| Document with nested paths, secondary indexes, vectors | JSON + Query Engine | Bundled since [8.0](versions/8.0.md); separate modules (Redis Stack) on 7.x |
| Time series, Bloom/Cuckoo, top-k, t-digest, count-min | Bundled types | Since [8.0](versions/8.0.md) |
| Vector similarity without an index definition | Vector set | Beta in 8.0 |
| Indexable ordered collection | Array | Since [8.8](versions/8.8.md) |

Prefer one key per entity plus small secondary structures over one giant key per collection. A key lives on one shard and is served by one main thread: a 10-million-member hash cannot be spread across nodes, and deleting or migrating it blocks.

## Encodings and Memory

Small collections use compact encodings (up to 10 times less memory, 5 times on average, per the memory optimization docs); Redis converts them to the regular encoding when an element count or element size threshold is crossed.

| Type | Compact encoding | Threshold parameters (8.12 image defaults) | Regular encoding |
|---|---|---|---|
| Hash | `listpack` (`listpackex` with field TTLs) | `hash-max-listpack-entries 512`, `hash-max-listpack-value 64` | `hashtable` |
| Set of integers | `intset` | `set-max-intset-entries 512` | `listpack` or `hashtable` |
| Small set | `listpack` (7.2+) | `set-max-listpack-entries 128`, `set-max-listpack-value 64` | `hashtable` |
| Sorted set | `listpack` | `zset-max-listpack-entries 128`, `zset-max-listpack-value 64` | `skiplist`; `btree` for large sets in 8.12 (200 members: `btree` on 8.12.0, `skiplist` on 8.10.3) |
| List | `listpack` | `list-max-listpack-size -2` | `quicklist` |
| String | `int`, `embstr` | integer values; short strings | `raw` |

The `*-ziplist-*` names from 6.2 are aliases and still accepted on 8.12.

Observed on the official images (7.2.17 to 8.12.0): `HSET h f1 a f2 b` gives `listpack`; after `HEXPIRE h 100 FIELDS 1 f1` (7.4+) it gives `listpackex`; `SADD s 1 2 3` gives `intset`; `ZADD z 1 a 2 b` and `RPUSH l a b c` give `listpack`; `SET n 12345` gives `int`.

Inspect:

```
OBJECT ENCODING <key>
MEMORY USAGE <key> [SAMPLES 0]      # bytes incl. overhead; SAMPLES 0 = all elements
INFO keysizes                        # 8.0+: per-type size histograms
redis-cli --bigkeys                  # largest key per type, uses SCAN
redis-cli --memkeys                  # largest by MEMORY USAGE
redis-cli --keystats                 # 7.4+: both, with distributions
SCAN 0 MATCH user:* COUNT 1000 TYPE hash
```

Decisions:

- Compact encodings are linear structures: lookups inside them are O(N), kept cheap because N is small. Raising the thresholds trades CPU for memory; the docs advise benchmarking conversion time when you raise them for much larger collections. Measure hot-command latency (`INFO latencystats`, `LATENCY HISTOGRAM`) before and after.
- Group small related values into hashes instead of separate top-level keys; the docs measured an order of magnitude less memory for many tiny values bucketed into hashes of about 100 fields. The cost: fields have no per-field TTL before 7.4.
- With 8.10 compact hashes, objects sharing the same field set store field names once. Measure `used_memory_hash_templates` and `hash_template_keys` before and after (parameters in [8.10](versions/8.10.md)).
- Provision for peak memory: after deleting data, RSS usually stays near the peak because the allocator cannot always return pages.
- `MEMORY USAGE` reports approximate bytes; compare like with like on the same version (8.10 fixed over-reporting).

## Key Design

- Name keys `<entity>:<id>[:<facet>]`. Keep names short when there are hundreds of millions of keys; name bytes are stored per key.
- In Cluster, every key in one multi-key command, `MULTI`/`EXEC`, or script must map to one hash slot, or the server returns `CROSSSLOT`. Put related keys under one hash tag: `cart:{u123}:items`, `cart:{u123}:total`. Only the text inside the first non-empty `{...}` is hashed.
- Do not put a constant inside the tag (`{cache}:...`): every key lands in one slot and one shard.
- Cluster supports only database 0; `SELECT` is rejected. Use key prefixes instead of numbered databases if you might move to Cluster. `cluster-compatibility-sample-ratio` ([8.0](versions/8.0.md)) counts would-fail commands in `cluster_incompatible_ops` before the move.
- Since 8.0, `SCAN ... MATCH {tag}*` scans only that tag's slot when the tag has no wildcard and nothing precedes it.

## Expiration

- Expired keys are removed lazily on access and by an active cycle every 100 ms that samples keys with a TTL and repeats while more than 25% of a sample is expired. Many keys expiring in the same second make the active cycle use more CPU; `expired_time_cap_reached_count` and `expire_cycle_cpu_milliseconds` in `INFO stats` show it. Add jitter to TTLs set in bulk.
- Replicas do not expire keys on their own; the primary sends `DEL`. A replica hides logically expired keys from reads. TTLs replicate as absolute millisecond timestamps (since 7.0), so clock differences between hosts matter.
- `SET` without `KEEPTTL` removes an existing TTL (8.2.0 fixed a case where it did not). `PERSIST`, `HPERSIST`, and `SPERSIST` (8.12; the GA notes call it `SETPERSIST`, which the 8.12.0 image rejects as an unknown command) remove TTLs.
- Field-level TTLs (`HEXPIRE`, 7.4+) and member-level TTLs (`SEXPIRE`, 8.12) remove the need for one key per field. `INFO keyspace` shows `subexpiry`; `expired_subkeys` counts field expirations.
- Lists and sorted sets have no element TTL; use a sorted set scored by deadline and a periodic `ZREMRANGEBYSCORE`.

## Atomicity and Concurrency

| Mechanism | Guarantees | Cost and limits |
|---|---|---|
| Single command | Atomic | Long O(N) commands block all clients |
| `MULTI`/`EXEC` | Queued commands run in sequence with no interleaving | No rollback: a command that fails at execution does not undo the others; a syntax error at queue time aborts the transaction |
| `WATCH` + `MULTI` | Optimistic check-and-set; `EXEC` returns nil if a watched key changed | Retry loop under contention |
| `SET ... IFEQ`, `DELEX`, `DIGEST` ([8.4](versions/8.6.md#changes-first-shipped-in-84)) | Compare-and-set on one string key | 8.4+ only; Valkey uses different commands (`DELIFEQ` is unknown on Redis 8.12) |
| Lua (`EVAL`) / Functions (`FCALL`, 7.0+) | Script runs atomically | Blocks the server while running; after `busy-reply-threshold` (5000 ms default) other clients get `BUSY` replies. Only `SCRIPT KILL`, `FUNCTION KILL` and `SHUTDOWN NOSAVE` are accepted then; a script that has already written can be stopped only with `SHUTDOWN NOSAVE` (programmability docs) |

- In Cluster, all keys of a transaction or script must be in one slot; pass key names in `KEYS[]` rather than building them inside the script.
- Lua scripts sent with `EVAL` are cached and, since [7.4](versions/7.4.md), evicted by LRU; load reusable logic as a Function library (`FUNCTION LOAD`, 7.0+), which is persisted and replicated.

## Deleting and Rewriting Large Keys

- `DEL` of a large collection frees memory on the main thread and blocks. Use `UNLINK`, or set `lazyfree-lazy-user-del yes` so `DEL` frees in the background. All `lazyfree-*` parameters are `no` on every checked image.
- `FLUSHALL`/`FLUSHDB` are synchronous unless called with `ASYNC` or `lazyfree-lazy-user-flush yes` (6.2+). Both drop data; on production block them with ACLs (`-flushall -flushdb` or `-@dangerous`).
- Split a large key before migrating it in Cluster; with `MIGRATE`-based resharding a huge key blocks both nodes. Atomic slot migration ([8.4](versions/8.6.md#changes-first-shipped-in-84)) moves slots without per-key `MIGRATE`.

## Common Mistakes

- `KEYS *` in production: O(N) over the keyspace and blocks. Use `SCAN` with `COUNT`.
- Unbounded lists, streams, or sets used as logs. Cap with `LTRIM`, `XADD MAXLEN ~ n`, or TTLs.
- Hot key: one key receiving most traffic cannot be scaled by sharding. Find it with `HOTKEYS` ([8.6](versions/8.6.md)) or `redis-cli --hotkeys` (works only with an LFU `maxmemory-policy`) and split it or cache it client-side.
- Assuming `MULTI` rolls back.
- Assuming a write acknowledged by the primary survives failover; see [replication and cluster](replication-and-cluster.md#consistency).

Sources: https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/memory-optimization/, https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/, https://redis.io/docs/latest/operate/oss_and_stack/management/scaling/, https://redis.io/docs/latest/operate/oss_and_stack/management/replication/, https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency/, https://redis.io/docs/latest/develop/using-commands/transactions/, https://redis.io/docs/latest/develop/tools/cli/, https://redis.io/docs/latest/commands/flushall/, https://redis.io/docs/latest/commands/info/, release notes linked from [versions](versions/index.md) (checked 2026-11-27); images `redis:7.2` to `redis:8.12`, statement runs and `CONFIG GET` output (2026-11-27).
