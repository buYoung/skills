# MariaDB Transactions and Locking

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)). Applies to InnoDB in MariaDB 10.6-13.1. Version-specific defaults are in the [version files](versions/index.md).

## Isolation Levels

Default isolation is `REPEATABLE-READ` in every covered series (container check, all tags).

```sql
SELECT @@global.tx_isolation, @@session.tx_isolation;          -- works in all covered versions
SELECT @@global.transaction_isolation;                          -- 11.1 and later only
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;                 -- next transaction only
```

`transaction_isolation` became a system variable in 11.1; on 10.6 and 10.11 `SELECT @@transaction_isolation` fails with `ERROR 1193 Unknown system variable`. `tx_isolation` is deprecated from 11.1 but still present in 13.0.

Decision rules:

| Workload | Level | Cost |
| --- | --- | --- |
| OLTP with short transactions, default app frameworks | `REPEATABLE READ` (default) | Gap and next-key locks on locking reads and writes; from 11.6.2 write-conflict errors (1020) under concurrency |
| High-concurrency writes on ranges, fewer gap-lock deadlocks wanted | `READ COMMITTED` | Non-repeatable reads inside a transaction; no gap locks for most searches. With statement-based binlogging, `READ COMMITTED` requires row or mixed format (writes to InnoDB fail with ERROR 1665 `Cannot execute statement: impossible to write to binary log since BINLOG_FORMAT = STATEMENT ...` on 10.6-13.0) |
| Reports that must see one consistent snapshot | `REPEATABLE READ` with `START TRANSACTION WITH CONSISTENT SNAPSHOT` | Holds back purge for the duration; history list grows |
| Strict serial behavior | `SERIALIZABLE` | Plain `SELECT` becomes a locking read (in autocommit-off transactions); many more lock waits |

## Snapshot Isolation and Error 1020

MariaDB InnoDB has a write/write conflict check controlled by `innodb_snapshot_isolation` (global and session, dynamic):

- Added in 10.6.18, 10.11.8, 11.0.6, 11.1.5, 11.2.4, 11.4.2 with default `OFF`.
- Default `ON` from 11.6.2, so `ON` in 11.8, 12.3, 13.0, 13.1 (containers: `OFF` on 10.6, 10.11, 11.4; `ON` on 11.8, 12.3, 13.0).

With `ON`, under `REPEATABLE READ`, an attempt to lock a record that is not visible in the transaction's read view (it was inserted, changed or deleted by a transaction that committed after the snapshot) raises `ERROR 1020 (HY000): Record has changed since last read in table '<table>'; try restarting transaction`, and the transaction is rolled back the same way as a deadlock. This prevents lost updates that the old behavior allowed.

A lost update on a stock counter, run on the official images (default `REPEATABLE READ`):

```sql
CREATE TABLE shop.stock (sku VARCHAR(20) PRIMARY KEY, qty INT NOT NULL);
INSERT INTO shop.stock VALUES ('A-100', 5);

-- Session 1: reads, then writes a value computed from what it read
BEGIN;
SELECT qty FROM shop.stock WHERE sku = 'A-100';        -- 5
-- Session 2 (autocommit), while session 1 is still open
UPDATE shop.stock SET qty = qty - 2 WHERE sku = 'A-100'; -- commits, qty = 3
-- Session 1
UPDATE shop.stock SET qty = 4 WHERE sku = 'A-100';      -- 5 - 1 from its snapshot
COMMIT;
```

| Image | Session 1's `UPDATE` | `qty` afterwards |
| --- | --- | --- |
| `mariadb:11.4` (11.4.13) | succeeds | 4: session 2's decrement is lost |
| `mariadb:11.8` (11.8.9) | `ERROR 1020 (HY000): Record has changed since last read in table 'stock'; try restarting transaction`, transaction rolled back | 3 |
| `mariadb:13.0` (13.0.2) | same error | 3 |
| `mariadb:11.8` with `SET SESSION innodb_snapshot_isolation=OFF` | succeeds | 4 |

The [11.4 to 11.8 upgrade page](https://mariadb.com/docs/server/server-management/install-and-upgrade-mariadb/upgrading/mariadb-community-server-upgrade-paths/upgrading-from-mariadb-11-4-to-mariadb-11-8) describes the same change.

What to do:

1. Treat 1020 like 1213: retry the whole transaction from the start. Check that the driver or ORM retry logic matches on error 1020, not only 1213 and 1205.
2. Shorten the gap between the first read and the write. Read with `SELECT ... FOR UPDATE` when the transaction will modify what it read; the lock is taken at read time, so there is no stale snapshot to conflict with.
3. If you cannot fix the application before an upgrade to 11.8 or later, set `innodb_snapshot_isolation=OFF` in the option file (or per session for the affected job). This restores the pre-11.6 behavior, including the lost-update anomaly. Record it as technical debt.

`SERIALIZABLE` sessions get blocked earlier instead, so the error may move to another transaction or disappear.

## Locking Reads and Queue Patterns

```sql
SELECT * FROM jobs WHERE state = 'ready' ORDER BY id LIMIT 10 FOR UPDATE SKIP LOCKED;  -- 10.6+
SELECT * FROM orders WHERE id = 1 FOR UPDATE NOWAIT;      -- fail at once if locked
SELECT * FROM orders WHERE id = 1 FOR UPDATE WAIT 5;      -- wait at most 5 s
SELECT * FROM orders WHERE id = 1 LOCK IN SHARE MODE;     -- shared lock
```

- `SKIP LOCKED` is InnoDB only and returns an inconsistent view by design; use it only for work-queue claiming.
- `NOWAIT` and `WAIT n` also apply to DDL and `LOCK TABLES`, giving a bounded metadata-lock wait (`ALTER TABLE t WAIT 5 ADD COLUMN ...`).
- An index on the predicate columns keeps locks narrow. Without an index, `FOR UPDATE` and `UPDATE ... WHERE` lock every scanned row, effectively the whole table under `REPEATABLE READ`.
- 13.1 adds `innodb_table_lock_on_full_scan` to take one table lock for locking full scans; see [13.1](versions/13.1.md).

## Timeouts

| Variable | Default (images) | Applies to | Notes |
| --- | --- | --- | --- |
| `innodb_lock_wait_timeout` | 50 s | InnoDB row locks | Rolls back the statement, not the transaction, unless `innodb_rollback_on_timeout=ON` (static). Error 1205. Values ≥ 100000000 mean infinite |
| `lock_wait_timeout` | 86400 s | metadata locks (DDL, `LOCK TABLES`) | Set low in sessions that run DDL so a blocked `ALTER` does not queue every other query behind it |
| `max_statement_time` | 0 (off) | whole statement, seconds | MariaDB-specific; per session or `SET STATEMENT max_statement_time=5 FOR SELECT ...` |
| `idle_transaction_timeout`, `idle_write_transaction_timeout`, `idle_readonly_transaction_timeout` | 0 (off) | idle sessions inside an open transaction | Kills forgotten open transactions that hold locks and block purge |

`SET STATEMENT var=value [, ...] FOR <statement>` applies variable values to one statement only and is MariaDB syntax (not in MySQL).

## Deadlocks

InnoDB detects deadlocks immediately (`innodb_deadlock_detect=ON`) and rolls back the transaction with the smaller undo, returning `ERROR 1213 (40001): Deadlock found when trying to get lock; try restarting transaction`.

Evidence:

```sql
SHOW ENGINE INNODB STATUS\G          -- section LATEST DETECTED DEADLOCK
SET GLOBAL innodb_print_all_deadlocks = ON;   -- every deadlock to the error log
SHOW GLOBAL STATUS LIKE 'Innodb_deadlocks';   -- counter (present in 10.6-13.0)
```

Reading the output (13.0.2 container, two sessions updating rows 1 and 2 in opposite order):

```
*** (1) TRANSACTION:
TRANSACTION 87, ACTIVE 2 sec starting index read
MariaDB thread id 8, OS thread handle ..., query id 86 127.0.0.1 root Updating
UPDATE acct SET bal=bal+1 WHERE id=1
*** WAITING FOR THIS LOCK TO BE GRANTED:
RECORD LOCKS space id 13 page no 3 n bits 320 index PRIMARY of table `dbaverify`.`acct` trx id 87 lock_mode X locks rec but not gap waiting
*** CONFLICTING WITH:
RECORD LOCKS ... trx id 86 lock_mode X locks rec but not gap
*** (2) TRANSACTION:
...
UPDATE acct SET bal=bal+1 WHERE id=2
*** WE ROLL BACK TRANSACTION (1)
```

- `MariaDB thread id` is the connection id you can find in `SHOW PROCESSLIST` and the general or audit log.
- `index PRIMARY` and `locks rec but not gap` mean single-row locks on the primary key: the fix is a consistent access order. `lock_mode X` without `rec but not gap` (next-key) or `locks gap before rec` point at range scans or missing indexes: add an index or use `READ COMMITTED`.
- `CONFLICTING WITH` (MariaDB format) names the holder directly.
- Only the statements that were waiting are shown, not the whole transaction; correlate with the application log.

Fixes in order of preference: same row order in every code path; shorter transactions; an index that turns a range lock into a point lock; `READ COMMITTED` for the workload; retries for the remainder. Do not disable `innodb_deadlock_detect` unless deadlock detection itself is the measured bottleneck under very high concurrency; then lower `innodb_lock_wait_timeout` to compensate.

## Diagnosing Blocking Now

```sql
-- Who holds open transactions, oldest first
SELECT trx_id, trx_state, trx_started, trx_mysql_thread_id, trx_rows_locked, trx_query
FROM information_schema.INNODB_TRX ORDER BY trx_started;

-- Waits (InnoDB row locks)
SELECT * FROM information_schema.INNODB_LOCK_WAITS;
SELECT * FROM information_schema.INNODB_LOCKS;      -- present in 10.6-13.0 images

-- sys schema view (10.6+)
SELECT * FROM sys.innodb_lock_waits\G
```

- `INNODB_LOCKS` and `INNODB_LOCK_WAITS` exist in MariaDB (they were removed from MySQL 8.0); container checks confirm `INNODB_LOCKS` and `INNODB_TRX` on 10.6-13.0.
- Metadata locks: install the `metadata_lock_info` plugin (`INSTALL SONAME 'metadata_lock_info';`) and query `information_schema.METADATA_LOCK_INFO`, or use `performance_schema.metadata_locks` when the Performance Schema is enabled (it is `OFF` by default in MariaDB). A `Waiting for table metadata lock` state in `SHOW PROCESSLIST` behind an `ALTER` usually means an older idle transaction touched the table: find it in `INNODB_TRX` and end it.
- Kill a blocker: `KILL QUERY <id>` stops the statement; `KILL <id>` ends the connection and rolls back its transaction. A large rollback continues after the kill; watch `trx_state = 'ROLLING BACK'`.

## MVCC, Purge and History Length

Long-running transactions and consistent-snapshot reports keep old row versions alive. Symptoms: growing `History list length` in `SHOW ENGINE INNODB STATUS`, larger undo tablespaces, slower reads.

- Find the oldest transaction in `INNODB_TRX` (`trx_started`).
- `innodb_max_purge_lag` (0 = no throttling) can delay DML when the history grows; leave it at 0 unless purge cannot keep up and you prefer slower writes to unbounded undo.
- Undo truncation: `innodb_undo_log_truncate=ON` with separate undo tablespaces (`innodb_undo_tablespaces` is 3 by default from 11.0; 0 on 10.6 and 10.11, where undo lives in the system tablespace and cannot shrink). On 10.6 the number of undo tablespaces is fixed when the datadir is created. From 10.11.1 it can be changed on an existing datadir: run `SET GLOBAL innodb_fast_shutdown=0`, shut down, set `innodb_undo_tablespaces`, and restart (InnoDB variable docs, MDEV-19229).

## Autocommit and Implicit Commits

- `autocommit=1` by default. DDL statements commit implicitly; atomic DDL (10.6+) makes the DDL itself crash-safe but does not make it transactional with surrounding DML.
- `completion_type=NO_CHAIN` by default.
- Non-transactional tables (Aria, MyISAM, MEMORY) in a transaction cannot be rolled back and break consistency of mixed transactions and replication. Check with `SELECT TABLE_SCHEMA, TABLE_NAME, ENGINE FROM information_schema.TABLES WHERE ENGINE <> 'InnoDB' AND TABLE_SCHEMA NOT IN ('mysql','information_schema','performance_schema','sys');`.

## XA

XA transactions are supported on InnoDB. On 12.3 with the InnoDB-based binary log, `XA PREPARE` is not replicated, so prepared transactions cannot be rescued by failing over to a replica.
