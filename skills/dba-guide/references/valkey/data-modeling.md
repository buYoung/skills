# Valkey Data Modeling

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)).

Key design, data type choice, small-encoding thresholds, expiration semantics, transactions and scripting behave as in Redis OSS 7.2, from which Valkey forked. Read [../redis/data-modeling.md](../redis/data-modeling.md) for those mechanisms.

## Command availability by series

Results from the official `valkey/valkey` images (2026-11-27). "ERR" means `ERR unknown command` or `ERR syntax error`; for `EXEC IFEQ` before 9.2 the transaction is aborted with `EXECABORT ... wrong number of arguments for 'exec' command`.

| Feature | 7.2 | 8.0 | 8.1 | 9.0 | 9.1 | 9.2 |
| --- | --- | --- | --- | --- | --- | --- |
| `SET k v IFEQ old` | ERR | ERR | OK | OK | OK | OK |
| `SET k v IFNE old`, `DELEX k IFEQ old` | ERR | ERR | ERR | ERR | ERR | OK, 1 |
| `DELIFEQ k v` | ERR | ERR | ERR | 1 | 1 | 1 |
| `HEXPIRE`, `HTTL`, `HSETEX`, `HGETEX` | ERR | ERR | ERR | yes | yes | yes |
| `HGETDEL`, `MSETEX`, `CLUSTERSCAN` | ERR | ERR | ERR | ERR (`HGETDEL`) | yes | yes |
| `INCREX`, `EXEC IFEQ` | ERR | ERR | ERR | ERR | ERR | yes |
| Path Hash (`PH*`) | ERR | ERR | ERR | ERR | ERR | commands present (`PHSET` known); behavior per release notes, not exercised |
| `JSON.*`, `BF.*`, `FT.*` in the plain image | ERR | ERR | ERR | ERR | ERR | ERR |
| `VADD` (vector sets) | ERR | ERR | ERR | ERR | ERR | ERR |

Redis 8.x data types and commands that Valkey does not have in core: JSON, Bloom, search, time series and vector sets are not built in. Valkey ships JSON, Bloom, Search and LDAP as separate modules (the `valkey/valkey-bundle` image). Command names can match Redis but behavior and RDB encoding are separate implementations; treat a Redis 7.4+ or 8.x application as needing a compatibility test, not as a drop-in.

## Hash field expiration (9.0 and later)

Use it when one entity has fields with different lifetimes (session attributes, per-feature flags, rate counters per window) and you would otherwise create one key per field.

```
HSET user:42 name ana token t1
HEXPIRE user:42 3600 FIELDS 1 token        # 1 = TTL set
HTTL user:42 FIELDS 2 token name           # 3600, -1 (no TTL)
HSETEX user:42 EX 600 FIELDS 1 otp 123456  # set field and TTL in one call
HGETEX user:42 PERSIST FIELDS 1 token      # read and remove the TTL
HGETDEL user:42 FIELDS 1 otp               # 9.1+: read and delete
```

Decision rules:

- The `FIELDS numfields` keyword is mandatory; since 9.0.6 `HTTL` and friends return a syntax error without it.
- `HTTL` returns `-1` for a field without TTL and `-2` for a missing field (9.0 and 9.2 images).
- Memory: on 9.0 and 9.1 any field TTL converts the hash to `hashtable` encoding. The images show a 3-field hash with one field TTL at 256 bytes on 9.0 and a 2-field one at 248 bytes on 9.1, versus 72 bytes on 9.2 where small hashes with field TTLs stay `listpack`. On 9.0/9.1, millions of small hashes with field TTLs cost several times the memory of plain small hashes; prefer key-level TTLs or move to 9.2.
- Expired fields are reaped by a background job. Until reaped, they still count in `MEMORY USAGE` (fixed in 9.0.8/9.1.4/9.2 to count them) and replicas see deletions as propagated `HDEL`.
- `HGETEX` needs write permission (9.0.6, 9.1.2): read-only ACL users can no longer change field TTLs.
- Redis CE 7.4+ also has `HEXPIRE`; data with field TTLs cannot move between Redis and Valkey through RDB files.

## Conditional string writes

Use them instead of `WATCH`/`MULTI` or Lua for single-key compare-and-set:

```
SET lock:job7 owner-a NX PX 30000   # acquire
SET lock:job7 owner-a IFEQ owner-a PX 30000   # 8.1+: extend only if still the owner
DELIFEQ lock:job7 owner-a           # 9.0+: release only if still the owner (1 = deleted)
DELEX lock:job7 IFEQ owner-a        # 9.2+: same, also IFNE
```

`SET ... IFEQ` returns `OK` when it wrote and nil when the value did not match, and combines with `PX`/`EX` (8.1 and 9.2 images). On 9.2 `SET ... IFNE` returns nil when the value matches, and `DELEX` returns 1 when it deleted, 0 when the condition failed. For multi-key conditions on 9.2 use `EXEC` conditions (`MULTI`, queued commands, then `EXEC IFEQ key value`, `EXEC IFNE key value`, `EXEC NX key` or `EXEC XX key`, several allowed; a failed condition returns nil and runs nothing); on earlier versions keep `WATCH` or a Lua function.

## Numbered databases in cluster mode (9.0 and later)

`cluster-databases N` (default 1) lets clients `SELECT` 0..N-1 in a cluster. Each slot contains all databases; the key still decides the slot. Before using it:

- Many client libraries forbid `SELECT` in cluster mode or keep a pooled connection on the last selected database. Test the client.
- `FLUSHDB`, `SCAN`, `DBSIZE` act on the current database of the connected node only.
- Databases share memory and CPU with no isolation or per-database metrics; noisy-neighbor risk is the same as on a standalone instance.
- Restrict access per database with ACL `db=` rules on 9.1+ only; on 9.0 any user that can `SELECT` reaches all databases.
- Changing `cluster-databases` on ElastiCache is not possible after creation.

Prefer key prefixes plus ACL key patterns (`~tenant1:*`) for tenant separation; use numbered databases mainly to lift standalone applications that already use `SELECT` into a cluster.

## Encodings and memory per type

Encoding thresholds (`hash-max-listpack-entries 512`, `hash-max-listpack-value 64`, `set-max-intset-entries 512`, `set-max-listpack-entries 128`, `zset-max-listpack-entries 128`, `list-max-listpack-size -2`) are the Redis 7.2 values in every series (9.2 image). What changed underneath:

- 8.0: key embedded in the dictionary entry. 8.1: new hashtable for the keyspace, sets, hashes and sorted sets. 9.1: strings up to 128 bytes embedded (was 64). 9.2: large sorted sets use a B+ tree (`btree`). Each step lowers per-key overhead; recompute capacity after an upgrade instead of reusing Redis-era numbers.
- Check a representative key with `MEMORY USAGE key SAMPLES 0` and `OBJECT ENCODING key` on the target version, not the source version.

## Path Hash (9.2)

A radix-tree type for paths with longest-prefix matching (request routing, autocomplete). Commands were renamed between RC and GA (`PHPATHEXISTS`, `PHPREFIXES`, `PHPATHCOUNT`, `PHPATHDEL`). Data in this type makes RDB files unreadable for 9.1 and earlier; adopt it only when rollback below 9.2 is no longer required.
