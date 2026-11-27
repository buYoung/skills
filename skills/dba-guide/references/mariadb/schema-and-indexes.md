# MariaDB Schema Design and Indexes

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)). Index B-tree mechanics are InnoDB's (clustered primary key, secondary indexes carry the primary key).

## Table Basics

| Setting | Default (images) | Decision |
| --- | --- | --- |
| `default_storage_engine` | InnoDB | Keep InnoDB for all application tables. Aria and MyISAM are not transactional and are not replicated by Galera. |
| `innodb_default_row_format` | `dynamic` | Keep. `COMPRESSED` works (writable again since 10.6.6) but costs CPU and buffer pool; prefer page compression or storage-level compression. |
| `innodb_page_size` | 16384 | Fixed at datadir creation. |
| `innodb_file_per_table` | `ON` | Keep (deprecated as a setting from 11.0.1 but still on). |
| `innodb_force_primary_key` | `OFF` | Set `ON` on Galera and wherever every table must have a primary key. |
| Character set | `utf8mb4` (compiled default from 11.6; the 10.6-11.4 images set it in `50-server.cnf`, whose compiled default is `latin1`) | Declare `CHARACTER SET utf8mb4` explicitly in DDL. |
| Collation | `utf8mb4_uca1400_ai_ci` from 11.5 (the 11.4 image also gets it through `character-set-collations` in `50-server.cnf`); `utf8mb4_general_ci` on the 10.6/10.11 images | Pin the collation per database to keep sort and uniqueness semantics stable across upgrades. |

Primary keys:

- Every InnoDB table needs a short, immutable primary key: secondary indexes store it, so a wide key enlarges every index.
- Without one, InnoDB uses a hidden row id; row-based replication then has to locate rows without a key, and Galera does not support `DELETE` on such tables.
- Monotonic keys (`AUTO_INCREMENT`, `UUID_v7()` from 11.7/11.8, sequences) insert at the right edge of the clustered index. Random UUIDv4 keys spread inserts over the whole index, causing page splits and a colder buffer pool.
- Store UUIDs in the `UUID` data type (10.7+; 10.6 returns `ERROR 4161 Unknown data type: 'UUID'`) instead of `CHAR(36)`.

Find tables without a primary key:

```sql
SELECT t.TABLE_SCHEMA, t.TABLE_NAME, t.ENGINE
FROM information_schema.TABLES t
LEFT JOIN information_schema.TABLE_CONSTRAINTS c
  ON c.TABLE_SCHEMA = t.TABLE_SCHEMA AND c.TABLE_NAME = t.TABLE_NAME AND c.CONSTRAINT_TYPE = 'PRIMARY KEY'
WHERE t.TABLE_TYPE = 'BASE TABLE' AND c.CONSTRAINT_NAME IS NULL
  AND t.TABLE_SCHEMA NOT IN ('mysql','information_schema','performance_schema','sys');
```

## MariaDB-Specific Types and Table Features

| Feature | Use when | Watch out |
| --- | --- | --- |
| `SEQUENCE` objects (`CREATE SEQUENCE s; SELECT NEXTVAL(s);`) | Several tables or the application need ids from one generator, or ids before insert | Sequences are tables (engine `SEQUENCE` appears in `ENGINES`); cached values are lost on restart, leaving gaps. 11.5+ allows `AS BIGINT UNSIGNED`. |
| `UUID`, `INET4`, `INET6` types | Storing identifiers and addresses compactly | Not MySQL-compatible; plan for it if the schema must run on both. |
| `JSON` | Semi-structured columns | In MariaDB `JSON` is `LONGTEXT` with a `JSON_VALID` check, not MySQL's binary format; values compare as strings. Index paths through virtual columns: `ALTER TABLE t ADD c_email VARCHAR(255) AS (JSON_VALUE(doc,'$.email')) VIRTUAL, ADD INDEX (c_email);`. 13.1 adds `->`/`->>`. |
| System-versioned tables (`WITH SYSTEM VERSIONING`) | Audit history, "as of" queries | History lives in the same table by default; see below. |
| Application-time periods (`PERIOD FOR`) | Validity ranges with `WITHOUT OVERLAPS` unique keys | MariaDB-only syntax. |
| Invisible columns (`INVISIBLE`) | Adding columns without breaking `SELECT *` or `INSERT` without column lists | 13.1 `mariadb-dump` turns on `--complete-insert` for such tables. |
| `VECTOR(n)` with `VECTOR INDEX` (11.7+, LTS 11.8) | Similarity search inside MariaDB | Index cache bounded by `mhnsw_max_cache_size` (16 MiB default); the images confirm `CREATE TABLE ... v VECTOR(3) NOT NULL, VECTOR INDEX (v)` on 11.8+ and `ERROR 4161 Unknown data type: 'VECTOR'` on 10.6-11.4. One vector index per table: a second `VECTOR INDEX` fails with `ERROR 1235 ... doesn't yet support 'multiple VECTOR indexes'` (11.8.9-13.0.2). |
| Column compression (`COMPRESSED` attribute) | Large text/blob columns rarely read | Syntax order changed in 11.5: `<type> COMPRESSED <charset clause>`. |

### System-Versioned Tables

```sql
CREATE TABLE price (id INT PRIMARY KEY, amount DECIMAL(10,2)) WITH SYSTEM VERSIONING;
SELECT * FROM price FOR SYSTEM_TIME AS OF TIMESTAMP '2026-11-01 00:00:00';
SELECT * FROM price FOR SYSTEM_TIME ALL WHERE id = 1;
DELETE HISTORY FROM price BEFORE SYSTEM_TIME '2026-01-01';     -- needs DELETE HISTORY privilege
```

- Every `UPDATE` that names a versioned column writes a history row, even if the value does not change. Exclude hot, unimportant columns with `WITHOUT SYSTEM VERSIONING`.
- Partition history so current-row queries do not read it: `PARTITION BY SYSTEM_TIME INTERVAL 1 MONTH AUTO` (AUTO from 10.9) or `LIMIT n AUTO`. You cannot drop the current partition or the only history partition.
- `ALTER TABLE` is rejected while `system_versioning_alter_history=ERROR` (default in all images). `KEEP` allows it, but history then shows the new structure. `TRUNCATE` is not supported.
- The primary key implicitly includes `row_end`; re-applied binlog events or retried statements on a replica can hit duplicate-key errors. The system-versioning docs recommend `secure_timestamp=YES` on replicas.
- Back up history with `mariadb-dump --dump-history` (10.11+); default dumps skip history rows.
- Upgrading to 11.8 rewrites all system-versioned rows (extended TIMESTAMP range); time it on a copy.
- Transaction-precise history (`BIGINT UNSIGNED` row start/end columns) uses `mysql.transaction_registry` and cannot be partitioned by `SYSTEM_TIME`.

## Index Design

- Composite index column order: equality columns first, then the range or sort column. `(customer_id, created_at)` serves `WHERE customer_id = ? ORDER BY created_at DESC LIMIT n` without a sort (verified with `ANALYZE` in the 13.0 image).
- Covering indexes avoid the clustered-index lookup; the primary key is already part of every secondary index.
- Descending key parts (`INDEX (a, b DESC)`) exist from 10.8 (so in 10.11); on 10.6, mixed-direction `ORDER BY` needs a filesort.
- Prefix indexes on long `VARCHAR`/`TEXT` cannot cover and cannot fully serve `ORDER BY`.
- Long unique constraints: MariaDB accepts `UNIQUE` on columns too long for a B-tree key by storing a hidden hash (10.6-13.0 images: `UNIQUE (body)` on a `TEXT` column is accepted, `SHOW CREATE TABLE` shows ``UNIQUE KEY `body` (`body`) USING HASH``, and a duplicate 5000-character value fails with ERROR 1062). It enforces uniqueness but does not support range scans.
- Indexes on virtual columns replace function indexes.
- Unused indexes cost write I/O. Find them with `userstat`/`INDEX_STATISTICS` (see [monitoring](monitoring.md)), then mark them `IGNORED` for a full business cycle before dropping:

```sql
ALTER TABLE orders ALTER INDEX ix_status IGNORED;       -- optimizer stops using it, still maintained
EXPLAIN SELECT COUNT(*) FROM orders WHERE status='new'; -- possible_keys no longer lists ix_status
ALTER TABLE orders ALTER INDEX ix_status NOT IGNORED;   -- instant rollback
```

`CREATE INDEX ix ON t (c) IGNORED` builds an index the optimizer does not use yet (all covered images: `possible_keys` is `NULL` afterwards).

## Online Schema Changes

`ALTER TABLE` chooses the cheapest algorithm unless you request one. Request it explicitly in production so an unexpected full copy fails instead of running:

| Clause | Effect | Typical operations |
| --- | --- | --- |
| `ALGORITHM=INSTANT` | Metadata only | Add, drop or reorder columns (`innodb_instant_alter_column_allowed=add_drop_reorder`), change defaults, rename, extend `VARCHAR` within the same length-byte class |
| `ALGORITHM=NOCOPY` | No clustered-index rebuild | Add or drop secondary indexes |
| `ALGORITHM=INPLACE` | May rebuild in place | Add primary key, change row format, some type changes |
| `ALGORITHM=COPY` | Full copy | Anything else; from 11.2 (in 11.4) usually with `LOCK=NONE`, allowing concurrent DML |
| `LOCK=NONE` / `SHARED` / `EXCLUSIVE` | Concurrency requested | The statement fails if the requested level is impossible |

```sql
ALTER TABLE orders ADD COLUMN note VARCHAR(20) NULL, ALGORITHM=INSTANT;           -- all images
ALTER TABLE orders DROP COLUMN note, ALGORITHM=INSTANT;                            -- all images
ALTER TABLE orders ADD INDEX ix_total (total), ALGORITHM=NOCOPY, LOCK=NONE;        -- all images
ALTER TABLE orders WAIT 5 ADD INDEX ix_x (customer_id, status), ALGORITHM=NOCOPY, LOCK=NONE;
```

Production safety:

- Every `ALTER` needs an exclusive metadata lock at the start and end, even `INSTANT`. An open transaction on the table blocks it, and the waiting `ALTER` then blocks all new queries on the table. Use `WAIT n`/`NOWAIT` or a low session `lock_wait_timeout`, and check `INNODB_TRX` for old transactions first.
- Instant add/drop puts the table into a non-canonical format; `innodb_instant_alter_column_allowed=never` keeps tables compatible with old versions at the cost of rebuilds.
- Replication: by default a replica starts a big `ALTER` only after the primary finishes, so lag equals its duration. Set `binlog_alter_two_phase=ON` (10.8+) on the primary so replicas start it in parallel. Galera runs DDL with Total Order Isolation (`wsrep_OSU_method=TOI`, a cluster-wide pause for the DDL) unless you switch the session to `RSU` and apply it node by node.
- Disk: rebuilding `INPLACE` and `COPY` operations need free space of about the table size plus the online change log (`innodb_online_alter_log_max_size`, 128 MiB default).
- Rehearse on a restored copy to measure duration; abort with `KILL QUERY`.

## Partitioning

- Use partitioning for data lifecycle (drop old partitions instantly), not as a substitute for indexes. Each query should prune to few partitions: `EXPLAIN PARTITIONS SELECT ...` lists the partitions read.
- Unique keys, including the primary key, must contain all partitioning columns.
- `ALTER TABLE t CONVERT PARTITION p TO TABLE t_old` and `ALTER TABLE t CONVERT TABLE t_new TO PARTITION p VALUES ...` (10.7+) move data out and in without copying. `EXCHANGE PARTITION` validates rows by default from 11.4 (`WITH VALIDATION`).
- 13.1: `PARTITION BY RANGE COLUMNS (...) INTERVAL (...)` adds partitions automatically.
- InnoDB foreign keys are not supported on partitioned tables: `CREATE TABLE ... FOREIGN KEY ... PARTITION BY ...` and `ALTER TABLE <partitioned> ADD FOREIGN KEY` both fail with `ERROR 1506 (HY000): Partitioned tables do not support FOREIGN KEY` (10.6-13.0 images).

## Foreign Keys

- Supported on InnoDB and checked row by row; every child insert takes a shared lock on the parent row, a common deadlock source under concurrency.
- From 12.1 (so in 12.3), constraint names must be unique per table, not per database. Schemas created on 12.3 with repeated names cannot be loaded into 11.8 or older.
- `SET foreign_key_checks=0` for bulk loads skips validation; violations loaded that way are not detected later.
