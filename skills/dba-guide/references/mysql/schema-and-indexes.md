# MySQL Schema and Indexes

Checked: 2026-11-27. Applies to InnoDB on MySQL 8.0 through 26.10. Version differences link to the version files.

Contents: [Primary keys](#primary-keys) · [Data types](#data-types) · [Secondary indexes](#secondary-indexes) · [JSON](#json-columns) · [Foreign keys and constraints](#foreign-keys-and-constraints) · [Partitioning](#partitioning) · [Changing a live schema](#changing-a-live-schema) · [Finding bad indexes](#finding-unused-and-redundant-indexes)

## Primary Keys

InnoDB stores each table as a B-tree ordered by the primary key (the clustered index). Every secondary index entry stores the primary key columns as its row pointer. Consequences:

- A wide primary key (long strings, many columns) makes every secondary index wider.
- Inserts in key order append to the right edge of the tree. Random keys (random UUIDs, hashes) insert all over the tree, split pages, and make the working set the whole index.
- A lookup through a secondary index that needs non-indexed columns does a second B-tree descent on the primary key.

Decision rules:

| Situation | Choose | Cost |
|---|---|---|
| Default OLTP table | `BIGINT UNSIGNED AUTO_INCREMENT` (or `INT` if it can never pass 4.29 billion) | Hot right-edge page under very high concurrent inserts; values are guessable. |
| Keys generated outside the database | UUID stored as `BINARY(16)` via `UUID_TO_BIN(uuid, 1)`, which reorders the time fields of a version-1 UUID so values increase | Random (v4) UUIDs still insert randomly; `UUID_TO_BIN` only helps time-based UUIDs. |
| Natural key that is short, immutable and unique | The natural key | Changing a primary key value rewrites the row and every secondary entry. |
| Many-to-many link table | Composite `PRIMARY KEY (a_id, b_id)` plus `KEY (b_id, a_id)` if you look up from both sides | |

A table without a primary key uses its first `UNIQUE` index whose columns are all `NOT NULL`; if none exists, InnoDB adds a hidden 6-byte row ID that you cannot use for lookups or replication row matching. Row-based replicas then apply each update or delete by scanning, which causes lag. Group Replication rejects tables without a primary key.

Enforce primary keys:

```sql
-- Find tables without a primary key
SELECT t.table_schema, t.table_name
  FROM information_schema.tables t
  LEFT JOIN information_schema.table_constraints c
    ON c.table_schema = t.table_schema AND c.table_name = t.table_name
   AND c.constraint_type = 'PRIMARY KEY'
 WHERE t.table_type = 'BASE TABLE' AND c.constraint_name IS NULL
   AND t.table_schema NOT IN ('mysql','sys','performance_schema','information_schema');

SET PERSIST sql_require_primary_key = ON;            -- reject new tables without one
SET PERSIST sql_generate_invisible_primary_key = ON; -- or add an invisible my_row_id key (8.0.30+)
```

`sql_generate_invisible_primary_key` adds an invisible `my_row_id BIGINT UNSIGNED AUTO_INCREMENT` column. It is hidden from `SELECT *` but appears in `SHOW CREATE TABLE` while `show_gipk_in_create_table_and_information_schema=ON` (default ON in the 8.4-26.10 containers). Since 9.7.0 a `UNIQUE NOT NULL` key counts as primary-key-equivalent, so no invisible key is generated for such tables.

## Data Types

| Need | Use | Avoid and why |
|---|---|---|
| Money, exact decimals | `DECIMAL(p,s)` | `FLOAT`/`DOUBLE`: rounding. `AUTO_INCREMENT` on them is rejected from 8.4. |
| Text in any language | `utf8mb4` (server default; collation `utf8mb4_0900_ai_ci` in all tested versions) | `utf8`/`utf8mb3`: cannot store 4-byte characters. `utf8` still means `utf8mb3` unless the `INTERPRET_UTF8_AS_UTF8MB4` SQL mode (9.5.0+) is set. |
| Case- and accent-sensitive comparison | a `_as_cs` or `_bin` collation on that column | Comparing columns with different collations can stop index use. |
| Point in time | `DATETIME` (store UTC by convention) or `TIMESTAMP` | `TIMESTAMP` converts through the session `time_zone` and ends in 2038. |
| Status values | `TINYINT` with a lookup table, or `ENUM` | Changing `ENUM` members other than appending at the end rebuilds the table. |
| Large text or blobs | Keep them in a separate table if most queries do not need them | They make rows wider in the buffer pool when stored inline. |

Index key limits: 3072 bytes per index key for `DYNAMIC` (the default row format) and `COMPRESSED`; 767 bytes for `REDUNDANT` and `COMPACT`. A `VARCHAR(255)` in `utf8mb4` uses up to 1020 bytes.

## Secondary Indexes

How MySQL uses a composite index `(a, b, c)`:

- Equality on a leading prefix (`a = ?`, `a = ? AND b = ?`) seeks.
- A range on a column ends seeking at that column: in `a = ? AND b > ? AND c = ?`, `c` is only filtered (index condition pushdown can still filter it inside the index).
- `ORDER BY` avoids a sort when the order follows the index after the equality prefix: `WHERE a = ? ORDER BY b, c` uses the index; `ORDER BY c` does not.
- Skip scan can use `(a, b)` for `WHERE b = ?` when `a` has few distinct values; check `EXPLAIN` for "Using index for skip scan" (traditional) or a skip-scan node.

Rules:

1. Put equality columns first, then the one range or sort column.
2. Add columns the query selects to make the index covering when the query is hot and the columns are small. Container example (8.0.46-26.10.0): `COUNT(*) ... WHERE status = 'new'` on `ix_status` shows "Covering index lookup" (tree) or "Using index" (traditional).
3. Do not index low-selectivity columns alone (a boolean, a three-value status) unless queries also sort or count by them, as above.
4. An index needs to be maintained on every insert and on updates of its columns. Each one costs write I/O and buffer pool space.
5. A function on an indexed column (`WHERE DATE(created_at) = ...`) prevents index use. Rewrite as a range (`created_at >= '2026-01-10' AND created_at < '2026-01-11'`) or add a functional index:
   ```sql
   ALTER TABLE orders ADD INDEX ix_created_day ((CAST(created_at AS DATE)));  -- 8.0.13+
   ```
   The query must use the same expression.
6. Descending indexes (`KEY (customer_id, created_at DESC)`) help mixed-direction `ORDER BY a ASC, b DESC`. A single-direction `ORDER BY created_at DESC` already works with a normal index read backwards (container: "Backward index scan" in 8.0 traditional output, "(reverse)" in tree output).

Test an index drop without dropping:

```sql
ALTER TABLE orders ALTER INDEX ix_status INVISIBLE;   -- optimizer stops using it; index is still maintained
-- watch latency; to roll back instantly:
ALTER TABLE orders ALTER INDEX ix_status VISIBLE;
-- one session can still test with it:
SET SESSION optimizer_switch = 'use_invisible_indexes=on';
```

Container confirmation (all five images): an index created `INVISIBLE` is ignored by `EXPLAIN` until the session sets `use_invisible_indexes=on`. Unique and primary key constraints still apply on invisible indexes; a primary key cannot be made invisible.

Statistics: InnoDB samples `innodb_stats_persistent_sample_pages` (default 20) pages per index. For skewed columns that are not indexed, create a histogram:

```sql
ANALYZE TABLE orders UPDATE HISTOGRAM ON status WITH 16 BUCKETS;
SELECT * FROM information_schema.column_statistics WHERE table_name = 'orders';
ANALYZE TABLE orders DROP HISTOGRAM ON status;
```

8.4+ adds `AUTO UPDATE` so `ANALYZE TABLE` and automatic statistics recalculation refresh the histogram (see [8.4](versions/8.4.md#worth-adopting)).

## JSON Columns

Use JSON for attributes that vary per row and are read as a whole. Keep columns you filter, join, or sort on as real columns.

Index a scalar inside a document with a generated column or a functional key part:

```sql
ALTER TABLE events
  ADD COLUMN user_id BIGINT AS (doc->>'$.user_id') STORED,
  ADD INDEX ix_user (user_id);
```

Index arrays with a multi-valued index (8.0.17+):

```sql
CREATE TABLE j (id INT PRIMARY KEY, tags JSON,
  INDEX ix_tags ((CAST(tags->'$' AS UNSIGNED ARRAY))));
SELECT id FROM j WHERE 3 MEMBER OF (tags->'$');
SELECT id FROM j WHERE JSON_CONTAINS(tags->'$', '[3,4]');
SELECT id FROM j WHERE JSON_OVERLAPS(tags->'$', '[3,4]');
```

Only `MEMBER OF`, `JSON_CONTAINS` and `JSON_OVERLAPS` can use a multi-valued index, and only when the query names the same expression as the index (`tags->'$'` here). Container check (all five images, 20,000 rows): with the index on `CAST(tags->'$' AS UNSIGNED ARRAY)`, `7 MEMBER OF (tags)` is a table scan even with `FORCE INDEX`, while `7 MEMBER OF (tags->'$')` is an index lookup on `ix_tags` and `JSON_OVERLAPS`/`JSON_CONTAINS` on `tags->'$'` are index range scans. An index declared as `CAST(tags AS UNSIGNED ARRAY)` serves `MEMBER OF (tags)` directly.

## Foreign Keys and Constraints

- InnoDB requires an index on the referencing columns and creates one if missing.
- Since 8.4, a foreign key must reference a primary or unique key with all its columns; non-unique or partial references are rejected while `restrict_fk_on_non_standard_key=ON` (default; container 8.4-26.10).
- Since 9.0.0, an inline `col INT REFERENCES parent(id)` clause creates an enforced foreign key; earlier versions ignored it.
- Since 9.6.0, foreign key checks and cascades run in the SQL layer by default; `innodb_native_foreign_keys` (OFF in the 9.7 and 26.10 containers) restores InnoDB handling. The 9.6.0 notes describe this as backward compatible. `enable_cascade_triggers` (9.7.0, session, default OFF): when ON, `CASCADE` and `SET NULL` actions fire `BEFORE` and `AFTER` triggers on the affected child rows. The triggers run inside the initiating statement, a trigger error rolls back the statement and its cascaded changes, row-based replication records the trigger changes without re-running them, and statement-based replication uses the source's setting (9.7.0 notes).
- `CHECK` constraints are enforced (8.0.16+).
- Cascading deletes on large parents run as one transaction and lock every child row. Delete children in batches first when the child set is large.
- Bulk loads: `SET SESSION foreign_key_checks = 0` skips checks for that session; rows loaded this way are never re-validated. Use it only for data already known to be consistent, such as a reload of a dump.

## Partitioning

Partitioning splits one table into separately stored pieces. It helps when you drop old data by range or when nearly every query prunes to one partition. It does not make an indexed lookup faster by itself.

Rules:

- Every unique key, including the primary key, must contain all partitioning columns.
- Partitioned InnoDB tables cannot have foreign keys or be referenced by them.
- Only InnoDB (and NDB) support partitioning.
- Check pruning with `EXPLAIN`: the `partitions` column (traditional), or partition names in TREE/ANALYZE output from 26.10.

Retention by range:

```sql
CREATE TABLE metrics (
  id BIGINT NOT NULL AUTO_INCREMENT, ts DATETIME NOT NULL, v DOUBLE,
  PRIMARY KEY (id, ts)
) PARTITION BY RANGE COLUMNS (ts) (
  PARTITION p2026_10 VALUES LESS THAN ('2026-11-01'),
  PARTITION p2026_11 VALUES LESS THAN ('2026-12-01'),
  PARTITION pmax     VALUES LESS THAN (MAXVALUE));

ALTER TABLE metrics REORGANIZE PARTITION pmax INTO (
  PARTITION p2026_12 VALUES LESS THAN ('2027-01-01'),
  PARTITION pmax     VALUES LESS THAN (MAXVALUE));
ALTER TABLE metrics DROP PARTITION p2026_10;   -- drops data; fast, no row-by-row delete
```

`DROP PARTITION` deletes data irreversibly and takes an exclusive metadata lock briefly. Back up or exchange the partition first (`ALTER TABLE metrics EXCHANGE PARTITION p2026_10 WITH TABLE metrics_archive`) if the data may be needed. Since 26.10 `EXCHANGE PARTITION` enforces CHECK constraints even `WITHOUT VALIDATION`.

## Changing a Live Schema

Every `ALTER TABLE` needs an exclusive metadata lock (MDL) at least briefly at start and end. A long-running transaction or query holding a shared MDL on the table blocks the `ALTER`, and every later query on the table queues behind the waiting `ALTER`. This is the most common way an "online" change causes an outage.

Before any DDL on a busy table:

```sql
-- Long transactions that would block the ALTER
SELECT trx_mysql_thread_id, trx_started, TIMESTAMPDIFF(SECOND, trx_started, NOW()) AS age_s, trx_query
  FROM information_schema.innodb_trx ORDER BY trx_started LIMIT 10;
-- Fail fast instead of queueing everyone (default lock_wait_timeout is 31536000 s)
SET SESSION lock_wait_timeout = 5;
```

Request the algorithm explicitly so MySQL errors instead of silently copying the table:

```sql
ALTER TABLE orders ADD COLUMN note VARCHAR(20) NULL, ALGORITHM=INSTANT;
ALTER TABLE orders ADD INDEX ix_total (total), ALGORITHM=INPLACE, LOCK=NONE;
```

All five containers accepted both statements.

| Operation | Algorithm | Concurrent DML | Notes |
|---|---|---|---|
| Add or drop a column | INSTANT (default; any position in 8.0.29+) | yes | Limited row versions per table: 64, or 255 from 9.1.0. Check `information_schema.innodb_tables.TOTAL_ROW_VERSIONS`; a table rebuild resets it. On an empty table, 9.2.0+ uses INPLACE by default; the 8.0.46 and 8.4.13 containers behave the same (a default `ADD COLUMN` on an empty table leaves `TOTAL_ROW_VERSIONS` at 0, on a one-row table it goes to 1). |
| Rename column, set/drop default, append ENUM/SET member | INSTANT | yes | Append only; inserting in the middle copies the table. |
| Add secondary index | INPLACE, no rebuild | yes | Reads the whole table; uses `innodb_ddl_threads`/`innodb_ddl_buffer_size`. FULLTEXT and SPATIAL block DML. |
| Drop or rename index | INPLACE, metadata only | yes | |
| Add primary key | INPLACE with rebuild | yes | |
| Drop primary key alone, change a column's data type | COPY | no | Writes are blocked for the whole copy. |
| `OPTIMIZE TABLE`, `ALTER TABLE ... FORCE`, change `ROW_FORMAT` | INPLACE with rebuild | yes | Needs free disk for a full copy of the table. |

INSTANT is not allowed on `ROW_FORMAT=COMPRESSED` tables, tables with a FULLTEXT index, temporary tables, or system tables.

On replicas, an INPLACE operation that took an hour on the source takes about an hour on the replica's applier and delays later transactions. Schedule large rebuilds with replication lag in mind.

Verify after a change: `SHOW CREATE TABLE`, `EXPLAIN` of the queries the change targets, and `TOTAL_ROW_VERSIONS` for instant changes.

## Finding Unused and Redundant Indexes

```sql
SELECT * FROM sys.schema_unused_indexes WHERE object_schema = 'app';
SELECT * FROM sys.schema_redundant_indexes WHERE table_schema = 'app';
SELECT index_name, rows_selected, rows_inserted
  FROM sys.schema_index_statistics WHERE table_schema = 'app' AND table_name = 'orders';
```

`schema_unused_indexes` relies on Performance Schema counters since server start. A recently restarted server, or an index used only by a monthly job, appears unused. In the containers, all three secondary indexes of a freshly loaded table were reported unused even though `EXPLAIN` had chosen them, because `EXPLAIN` does not execute. Check uptime and replicas (they serve other queries), make the index invisible for a full business cycle, then drop it.

## Sources

Checked 2026-11-27: MySQL 8.4 manual, Online DDL Operations (https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html); MySQL 8.4 What Is New (https://dev.mysql.com/doc/refman/8.4/en/mysql-nutshell.html); 9.x release notes (https://dev.mysql.com/doc/relnotes/mysql/9.7/en/); 26.10.0 release notes; statement runs on the official mysql:8.0, 8.4, 9.7, 26.7, 26.10 images. Other mechanisms described here (clustered index, index merge rules, multi-valued indexes, histograms, partitioning rules) follow the MySQL 8.4 Reference Manual chapters on InnoDB indexes, optimization, and partitioning.
