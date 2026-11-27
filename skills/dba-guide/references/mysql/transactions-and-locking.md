# MySQL Transactions, Isolation, and Locking

Checked: 2026-11-27. Applies to InnoDB on MySQL 8.0 through 26.10.

## Defaults

Confirmed on all five containers (8.0.46, 8.4.13, 9.7.4, 26.7.0, 26.10.0): `transaction_isolation=REPEATABLE-READ`, `autocommit=1`, `innodb_lock_wait_timeout=50`, `innodb_deadlock_detect=ON`, `innodb_print_all_deadlocks=OFF`, `innodb_autoinc_lock_mode=2`, `lock_wait_timeout=31536000` (metadata locks: one year).

## Isolation Levels

| Level | Plain `SELECT` | `SELECT ... FOR UPDATE/SHARE`, `UPDATE`, `DELETE` | Use when |
|---|---|---|---|
| REPEATABLE READ (default) | One snapshot for the whole transaction, taken at the first read | Next-key locks (row plus the gap before it) on every index record scanned, unless the search uses a unique index with a unique condition, which locks only the record | You need repeatable snapshots, or you rely on gap locks to block phantom inserts. |
| READ COMMITTED | A fresh snapshot for each statement | Record locks only; gaps are locked only for foreign key and duplicate-key checks. Locks on rows that do not match the `WHERE` are released after evaluation. `UPDATE` does a semi-consistent read of already-locked rows. | High-concurrency OLTP with many range updates; fewer deadlocks. Requires row-based binary logging. |
| SERIALIZABLE | With `autocommit=0`, plain reads become `FOR SHARE`; with `autocommit=1` each `SELECT` is a non-locking read | as REPEATABLE READ | Rarely; expect lock waits. |
| READ UNCOMMITTED | May read uncommitted versions | as READ COMMITTED | Avoid. |

Pitfalls:

- Under REPEATABLE READ, a plain `SELECT` sees the snapshot while a locking read or `UPDATE` in the same transaction sees and locks the latest committed rows. A transaction that reads plainly and then updates "the same" rows may act on different data. Use `SELECT ... FOR UPDATE` for read-modify-write.
- Switching to READ COMMITTED changes behavior that code may rely on (phantom protection). Change it per session first (`SET SESSION transaction_isolation = 'READ-COMMITTED'`) for one service, then globally.
- Under READ COMMITTED, locks are still taken on every row the chosen index scans before filtering. A missing index still locks many rows.

## MVCC, Undo, and Purge

InnoDB keeps old row versions in undo logs so snapshots can read them. Purge removes versions no active snapshot needs. One long-running transaction or an open snapshot (including an idle session that ran `START TRANSACTION` and a `SELECT`, and `mysqldump --single-transaction` runs) stops purge for everything newer, so undo grows and every read walks longer version chains.

Evidence:

```sql
-- History list length: unpurged transactions
SELECT NAME, COUNT FROM information_schema.INNODB_METRICS WHERE NAME = 'trx_rseg_history_len';
-- Oldest open transactions
SELECT trx_id, trx_mysql_thread_id, trx_state, trx_started,
       TIMESTAMPDIFF(SECOND, trx_started, NOW()) AS age_s,
       trx_rows_locked, trx_rows_modified, LEFT(trx_query, 80) AS q
  FROM information_schema.INNODB_TRX ORDER BY trx_started LIMIT 10;
-- What that session ran last (it may be idle now)
SELECT t.PROCESSLIST_ID, s.SQL_TEXT
  FROM performance_schema.threads t
  JOIN performance_schema.events_statements_history s USING (THREAD_ID)
 WHERE t.PROCESSLIST_ID = <trx_mysql_thread_id> ORDER BY s.EVENT_ID;
```

Read: a history list length that grows steadily for hours and an old `trx_started` point to the blocker. Kill it with `KILL <id>` after confirming with the owner. Killing a transaction that modified many rows starts a rollback that can take as long as the work done; `trx_rows_modified` estimates the cost. Since 26.10, the error log warns when the history list passes `innodb_max_purge_lag`.

Undo tablespaces are truncated automatically when `innodb_undo_log_truncate=ON` (default ON in all containers) and they exceed `innodb_max_undo_log_size` (1 GiB default).

## Lock Types You Will See

| Lock | Taken by | Notes |
|---|---|---|
| Record lock (`X,REC_NOT_GAP` / `S,REC_NOT_GAP`) | Locking reads and DML on a unique match | |
| Gap lock (`X,GAP`) | Range scans under REPEATABLE READ | Blocks inserts into the gap only. Gap locks do not conflict with each other. |
| Next-key lock (`X`) | Range scans under REPEATABLE READ | Record plus gap before it. |
| Insert intention (`X,GAP,INSERT_INTENTION`) | `INSERT` waiting on a gap lock | The usual cause of insert deadlocks. |
| Table intention (`IX`, `IS`) | Any row lock | Normally harmless. |
| AUTO-INC | Inserts into tables with `AUTO_INCREMENT` | With `innodb_autoinc_lock_mode=2` (default since 8.0) there is no table-level lock for simple inserts; requires row-based or mixed binary logging for safety. |
| Metadata lock (MDL) | Every statement on a table; DDL takes exclusive | Held until the transaction ends, not the statement. |

## Diagnosing Lock Waits

```sql
SELECT * FROM sys.innodb_lock_waits\G
-- columns: waiting_pid, waiting_query, blocking_pid, blocking_query, wait_age, sql_kill_blocking_query

SELECT ENGINE_TRANSACTION_ID, OBJECT_NAME, INDEX_NAME, LOCK_TYPE, LOCK_MODE, LOCK_STATUS, LOCK_DATA
  FROM performance_schema.data_locks WHERE OBJECT_SCHEMA = 'app';
SELECT * FROM performance_schema.data_lock_waits;

-- Metadata locks (DDL stuck "Waiting for table metadata lock")
SELECT * FROM sys.schema_table_lock_waits\G
SELECT OBJECT_SCHEMA, OBJECT_NAME, LOCK_TYPE, LOCK_STATUS, OWNER_THREAD_ID
  FROM performance_schema.metadata_locks WHERE OBJECT_SCHEMA = 'app';
```

`blocking_query` is often NULL: the blocker is idle inside an open transaction. Find its last statement through `events_statements_history` as above. Fix the application path that leaves transactions open (missing commit on an error path, connection pool returning connections mid-transaction).

Since 9.1.0, `data_locks` and `data_lock_waits` may list only part of a transaction's locks. Do not use them as a complete lock inventory on 9.x and 26.x.

## Deadlocks

InnoDB detects a cycle immediately (with `innodb_deadlock_detect=ON`) and rolls back the transaction with less work (fewer rows changed). The client gets:

```text
ERROR 1213 (40001): Deadlock found when trying to get lock; try restarting transaction
```

The whole transaction is rolled back. The application must retry it from the beginning.

Read the last deadlock:

```sql
SHOW ENGINE INNODB STATUS\G   -- section LATEST DETECTED DEADLOCK
SET PERSIST innodb_print_all_deadlocks = ON;   -- write every deadlock to the error log
```

Container output (26.10.0) for two sessions updating `acct` rows 1 and 2 in opposite order:

```text
*** (1) TRANSACTION:
TRANSACTION 2077, ACTIVE 3 sec starting index read
UPDATE acct SET bal=bal+1 WHERE id=2
*** (1) HOLDS THE LOCK(S):
... index PRIMARY of table `dbaverify`.`acct` trx id 2077 lock_mode X locks rec but not gap
*** (1) WAITING FOR THIS LOCK TO BE GRANTED:
... index PRIMARY of table `dbaverify`.`acct` trx id 2077 lock_mode X locks rec but not gap waiting
*** (2) TRANSACTION:
TRANSACTION 2078, ACTIVE 2 sec starting index read
UPDATE acct SET bal=bal+1 WHERE id=1
...
*** WE ROLL BACK TRANSACTION (2)
```

How to read it: for each transaction, the statement shown is the one waiting, not every statement it ran. `HOLDS THE LOCK(S)` and `WAITING FOR` name the index and lock mode. `locks rec but not gap` is a record lock; `locks gap before rec` is a gap lock; `lock_mode X` alone is a next-key lock; `insert intention` marks an insert blocked by a gap lock. The hex in `0: len 4; hex 80000001` is the key value (signed INT 1 with the sign bit flipped).

Fixes by pattern:

| Pattern | Fix |
|---|---|
| Two transactions update the same rows in different order | Access rows in a consistent order (sort keys before updating). |
| Range `UPDATE`/`DELETE` plus concurrent `INSERT` into the range | Use READ COMMITTED for that workload, or an index that narrows the range. |
| `SELECT ... FOR UPDATE` on a missing row, then `INSERT` (both sessions) | Gap locks are compatible, insert intentions are not: use `INSERT ... ON DUPLICATE KEY UPDATE`, or insert first and handle the duplicate-key error. |
| Unique secondary index plus concurrent inserts of the same value | Expected; retry. |
| Foreign key checks on parent rows | Shared locks on parents; keep parent updates short. |

Do not set `innodb_deadlock_detect=OFF` except for very high-concurrency single-row hot spots where detection itself costs CPU; then waits end only by `innodb_lock_wait_timeout`.

## Lock Wait Timeout

`ERROR 1205 (HY000): Lock wait timeout exceeded` rolls back only the statement unless `innodb_rollback_on_timeout=ON` (default OFF). The transaction stays open and still holds its earlier locks. Applications that catch 1205 and continue risk committing half a transaction. Roll back explicitly on 1205. Container check (all five images, `innodb_lock_wait_timeout = 2`): the blocked `UPDATE` failed with 1205 after 2 seconds, `INNODB_TRX.trx_state` stayed `RUNNING`, and the session still held the row lock from its earlier `UPDATE` until `ROLLBACK`.

Lower the timeout for interactive paths: `SET SESSION innodb_lock_wait_timeout = 5`. Use `NOWAIT` or `SKIP LOCKED` (8.0+; confirmed on all containers) for queue consumers:

```sql
START TRANSACTION;
SELECT id FROM jobs WHERE state = 'ready' ORDER BY id LIMIT 10 FOR UPDATE SKIP LOCKED;
-- process, update state, then
COMMIT;
```

`SKIP LOCKED` returns an inconsistent view by design. Use it only for work queues.

## Transaction Hygiene Checklist

- Keep transactions short; never wait for user input or remote calls inside one.
- Commit large batch changes in chunks of a few thousand rows, keyed by primary key ranges, so undo, lock count and replica lag stay bounded.
- Set `SET SESSION lock_wait_timeout = 5` before DDL so a blocked `ALTER` gives up instead of blocking every query behind it.
- XA transactions in `PREPARED` state hold locks across restarts. List them with `XA RECOVER` and resolve them.
- Monitor: history list length, oldest transaction age, `Innodb_row_lock_waits` and `Innodb_row_lock_time` deltas, deadlock count (`SELECT COUNT FROM information_schema.INNODB_METRICS WHERE NAME = 'lock_deadlocks'`).

## Sources

Checked 2026-11-27: MySQL 8.4 manual, Transaction Isolation Levels (https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html); Changes in MySQL 9.1.0 (https://dev.mysql.com/doc/relnotes/mysql/9.7/en/news-9-1-0.html) for incomplete `data_locks`; Changes in MySQL 26.10.0 for purge-lag warnings; deadlock reproductions and statement runs on the official mysql:8.0 to 26.10 images. Lock types, deadlock handling and `innodb_rollback_on_timeout` follow the MySQL 8.4 manual sections on InnoDB locking and deadlocks (https://dev.mysql.com/doc/refman/8.4/en/innodb-locking.html, https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlocks.html).
