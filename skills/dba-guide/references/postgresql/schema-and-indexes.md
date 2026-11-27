# Schema Design and Indexes

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)). For DDL locking see [transactions-and-locking.md](transactions-and-locking.md#safe-ddl-patterns).

## Keys

| Choice | Use when | Cost |
| --- | --- | --- |
| `bigint GENERATED ALWAYS AS IDENTITY` | default for surrogate keys | 8 bytes; sequence values are not gap-free and not transactional |
| `uuid` from `uuidv7()` (18+) | keys generated outside the database or merged across systems | 16 bytes; time-ordered, so B-tree inserts stay near the right edge |
| `uuid` from `gen_random_uuid()` / `uuidv4()` | unpredictable IDs required | random insert positions spread writes over the whole index: more page splits, larger working set, more WAL full-page images |
| natural key | stable, short, truly unique business value | changing it cascades to every foreign key |

- Use `GENERATED ALWAYS` rather than `serial`: it prevents accidental manual inserts and ties the sequence to the column. Container shows `GENERATED ALWAYS AS IDENTITY` working on 14 to 19.
- `int` keys overflow at about 2.1 billion. Check headroom: `SELECT last_value FROM pg_sequences WHERE sequencename = 'orders_id_seq';`. Converting `int` to `bigint` rewrites the table (see the type-change pattern in the locking file).
- Index every foreign key column on the referencing side unless the parent is never deleted or updated on its key; otherwise each parent delete scans the child table and takes long row locks.

## Data types

- Use `timestamptz` for points in time; `timestamp` without time zone silently drops offsets.
- Use `text` with a `CHECK (length(c) <= n)` or `varchar(n)` where a limit is a business rule; there is no performance difference between `text` and `varchar`.
- Use `numeric` for money; `float8` for measurements.
- `jsonb` (not `json`) for semi-structured data you query; index it with GIN (`jsonb_path_ops` for containment-only queries, smaller and faster). Promote frequently filtered keys to real columns.
- Generated columns: on 18+ `GENERATED ALWAYS AS (expr)` defaults to virtual (computed on read); add `STORED` to persist. On 14 to 17 only `STORED` exists and the bare form is a syntax error (container).
- `enum` types are cheap but adding values needs `ALTER TYPE ... ADD VALUE`, and removing values is not supported; use a lookup table when the list changes often.
- Large values are compressed and moved out of line (TOAST). The default compression is `pglz` on 14 to 18 and `lz4` on 19; per column: `ALTER TABLE t ALTER COLUMN body SET COMPRESSION lz4;` (affects new values only).

## Constraints

- Prefer constraints over application checks: `NOT NULL`, `CHECK`, `UNIQUE`, foreign keys, exclusion constraints (`EXCLUDE USING gist (room WITH =, during WITH &&)` with `btree_gist`).
- 15+: `UNIQUE NULLS NOT DISTINCT` treats NULLs as equal.
- 18+: `PRIMARY KEY (id, valid_period WITHOUT OVERLAPS)` and `FOREIGN KEY (..., PERIOD valid_period)` for temporal data; `NOT ENFORCED` for `CHECK` and foreign keys documents a rule without enforcing it (the planner does not rely on it).
- Add constraints to existing large tables `NOT VALID`, then `VALIDATE CONSTRAINT` separately.

## Index types

| Type | Supports | Use when | Avoid when |
| --- | --- | --- | --- |
| B-tree (default) | `=`, `<`, `>`, `BETWEEN`, `IN`, `IS NULL`, sorting, `LIKE 'abc%'` with C collation or `text_pattern_ops` | almost everything | — |
| Hash | `=` only | very long keys compared only by equality | you need ordering or uniqueness |
| GIN | containment and membership: `jsonb @>`, arrays, full text, `pg_trgm` similarity and `LIKE '%x%'` | many keys per row | write-heavy tables with low query benefit (pending list costs; `gin_pending_list_limit` 4MB) |
| GiST | ranges, geometry, nearest-neighbor `ORDER BY <->`, exclusion constraints | overlap and distance queries | plain equality |
| SP-GiST | partitioned spaces: IP prefixes, quadtrees, text prefixes | non-balanced data | — |
| BRIN | min/max (or bloom, multi-minmax since 14) per block range | huge append-only tables where the column correlates with physical order (timestamps) | randomly ordered data; check `pg_stats.correlation` near 1 or -1 |

Variants:

- Multicolumn B-tree: put equality columns first, then the range or `ORDER BY` column. Container: `(customer_id, created_at)` serves `WHERE customer_id = 42 ORDER BY created_at DESC LIMIT 10` with `Index Scan Backward` and no sort. 18+ skip scan can use the index even without a condition on the leading column, but a dedicated index is still faster when that query is hot.
- Covering index: `CREATE INDEX ON orders (customer_id) INCLUDE (status, total);` enables index-only scans without adding the columns to the key.
- Partial index: `CREATE INDEX ON jobs (created_at) WHERE state = 'ready';` keeps the index small when queries always filter on the same predicate. The query predicate must imply the index predicate.
- Expression index: `CREATE INDEX ON users (lower(email));` the query must use the same expression.
- Unique index vs unique constraint: equivalent for enforcement. A foreign key can reference a primary key, a unique constraint, or the columns of a non-partial unique index (Constraints page). Only a constraint can be named in `ON CONFLICT ON CONSTRAINT`; a unique index can still be inferred from the `ON CONFLICT (columns)` list.

Build indexes on live tables with `CREATE INDEX CONCURRENTLY` (two table scans, waits for existing transactions, cannot run inside a transaction block). Check for invalid leftovers after any failure: `SELECT indexrelid::regclass FROM pg_index WHERE NOT indisvalid;`. Raise `maintenance_work_mem` for the session to speed builds; 17+ builds BRIN in parallel and 18+ builds GIN in parallel (B-tree since 11), up to `max_parallel_maintenance_workers` (default 2).

## Index hygiene

Unused indexes cost writes, WAL, vacuum time, and cache.

```sql
SELECT s.relname, s.indexrelname, s.idx_scan, s.last_idx_scan,
       pg_size_pretty(pg_relation_size(s.indexrelid)) AS size
FROM pg_stat_user_indexes s
JOIN pg_index i ON i.indexrelid = s.indexrelid
WHERE NOT i.indisunique AND NOT i.indisprimary
ORDER BY s.idx_scan, pg_relation_size(s.indexrelid) DESC;
```

- Counters are per server: check every standby before dropping an index that only reporting replicas use.
- `last_idx_scan` exists on 16+. On older versions, snapshot `idx_scan` and compare after a full business cycle.
- Statistics reset on crash recovery and when `pg_stat_reset()` runs; check `stats_reset` in `pg_stat_database` (and per table on 19) before trusting a zero.
- Find duplicates: indexes whose column list is a prefix of another index with the same type and predicate.
- Drop with `DROP INDEX CONCURRENTLY idx;` Keep the `CREATE INDEX` statement (`SELECT pg_get_indexdef('idx'::regclass);`) so you can rebuild it.

## HOT updates and fillfactor

An update is heap-only (HOT) when no indexed column changes and the new version fits on the same page. HOT updates skip index maintenance and let pruning reclaim space without vacuum.

```sql
SELECT relname, n_tup_upd, n_tup_hot_upd,
       round(100.0 * n_tup_hot_upd / nullif(n_tup_upd, 0), 1) AS hot_pct,
       n_tup_newpage_upd              -- 16+
FROM pg_stat_user_tables ORDER BY n_tup_upd DESC LIMIT 20;
```

- Low `hot_pct` on a heavily updated table: check whether an index covers a frequently updated column (remove or change it), and lower `fillfactor` (for example `ALTER TABLE t SET (fillfactor = 85);`) so pages keep room for new versions. Fillfactor applies to newly written pages; existing pages change only after a rewrite.
- 16+: updates of columns covered only by BRIN indexes can still be HOT.

## Partitioning

Use declarative partitioning (`PARTITION BY RANGE | LIST | HASH`) when at least one of these holds:

- you need to drop or archive old data in bulk (`DETACH PARTITION ... CONCURRENTLY` then `DROP TABLE`, instead of `DELETE`);
- the table is too large to vacuum or reindex within acceptable time as a whole;
- most queries filter on the partition key, so pruning reduces work.

Costs and rules:

- Primary keys and unique constraints must include the partition key.
- Queries that do not filter on the key scan every partition; thousands of partitions raise planning time and lock-table use (`max_locks_per_transaction`; default 64 through 18 and 128 on 19, where lock table sizing changed, so double any explicit value carried over from 18 or older).
- Create future partitions ahead of time (a scheduled job); a `DEFAULT` partition catches strays but makes adding a new overlapping partition scan the default partition.
- Autovacuum does not analyze the partitioned parent; run `ANALYZE parent;` after large loads.
- 17+: identity columns and exclusion constraints on partitioned tables; 18+: `NOT VALID` foreign keys on partitioned tables; unlogged partitioned tables are disallowed on 18+.

Verify pruning with `EXPLAIN`: only matching partitions appear, or `Subplans Removed: N` for run-time pruning.

## Collations and indexes

Text indexes depend on the collation library. When the OS C library or ICU version changes (OS upgrade, new container base image, restoring a physical backup on a different OS release), the sort order of existing B-tree indexes on text can silently become wrong.

- 15+: `SELECT datname, datcollversion, pg_database_collation_actual_version(oid) FROM pg_database;` shows a mismatch; the server also warns at connection.
- Fix: `REINDEX` affected indexes (concurrently), then `ALTER DATABASE db REFRESH COLLATION VERSION;`.
- 17+: the builtin provider (`C`, `C.UTF-8`) does not depend on the OS library; use it when code-point ordering is acceptable.
- Logical replication or dump/restore to the new OS avoids the problem because indexes are rebuilt.
