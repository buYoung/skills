# Transactions, MVCC, and Locking

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)). For vacuum and wraparound see [vacuum-and-maintenance.md](vacuum-and-maintenance.md).

## MVCC in one paragraph

Every `UPDATE` writes a new row version and marks the old one dead (`xmax`); `DELETE` only marks. Readers see the versions visible to their snapshot and never block writers; writers block only writers of the same row. Dead versions stay until no snapshot can see them, then `VACUUM` reclaims the space. Consequences that drive decisions:

- A long-running transaction, an idle-in-transaction session, a stale replication slot, or a standby with `hot_standby_feedback = on` and a long query holds back the removal horizon for the whole cluster, so tables bloat everywhere, not only the one being read.
- `UPDATE` of a single column still writes a whole new row. Heap-only tuple (HOT) updates avoid index writes when no indexed column changes and the page has free space; see [schema-and-indexes.md](schema-and-indexes.md#hot-updates-and-fillfactor).
- `count(*)` must check visibility; it cannot read a stored counter.

## Isolation levels

Default is `read committed` (container: `SHOW default_transaction_isolation` on 14 to 19).

| Level | Snapshot | Anomalies prevented | Error to retry | Use for |
| --- | --- | --- | --- | --- |
| `READ UNCOMMITTED` | behaves as `READ COMMITTED` | dirty reads | — | never needed |
| `READ COMMITTED` | new snapshot per statement | dirty reads | none from isolation; deadlocks still possible | most OLTP; combine with `SELECT ... FOR UPDATE` or atomic `UPDATE ... SET x = x + 1` |
| `REPEATABLE READ` | one snapshot for the transaction | non-repeatable reads, phantoms | `40001` could not serialize access due to concurrent update | consistent reports, multi-statement reads |
| `SERIALIZABLE` | snapshot plus predicate-lock (SSI) tracking | all serialization anomalies, including write skew | `40001` | invariants across rows (on-call rosters, balances across accounts) without explicit locks |

Decision rules:

- Choose `SERIALIZABLE` only if every writer that touches the protected data also runs `SERIALIZABLE`, and the application retries the whole transaction on SQLSTATE `40001`. Keep these transactions short; SSI raises false-positive aborts as transactions grow. Mark read-only ones `READ ONLY` (and `DEFERRABLE` for long reports so they never abort).
- In `READ COMMITTED`, an `UPDATE` that waits for a concurrent writer re-evaluates its `WHERE` against the new row version after the lock is granted. A check-then-act sequence in separate statements (`SELECT` then `UPDATE`) is not safe without `FOR UPDATE` or a constraint.
- Use constraints (unique, exclusion, foreign keys) as the primary integrity mechanism; isolation is the second line.

Check and set:

```sql
SHOW transaction_isolation;
BEGIN ISOLATION LEVEL REPEATABLE READ;
-- or for a role or database:
ALTER ROLE reporting SET default_transaction_isolation = 'repeatable read';
```

## Row locks

| Clause | Blocks | Typical use |
| --- | --- | --- |
| `FOR UPDATE` | other `FOR UPDATE`, `FOR NO KEY UPDATE`, `FOR SHARE`, `FOR KEY SHARE`, `UPDATE`, `DELETE` | read-modify-write of a row whose key may change or which will be deleted |
| `FOR NO KEY UPDATE` | same as above except `FOR KEY SHARE` | plain `UPDATE` that does not change key columns takes this lock implicitly |
| `FOR SHARE` | updates and deletes | rarely needed |
| `FOR KEY SHARE` | deletes and key updates only | taken by foreign-key checks on the referenced row |

- `SKIP LOCKED` builds job queues: `SELECT id FROM jobs WHERE state = 'ready' ORDER BY id LIMIT 10 FOR UPDATE SKIP LOCKED;`
- `NOWAIT` fails immediately with SQLSTATE `55P03`. On 18 and later, `log_lock_failures = on` logs these failures.
- Multiple lockers on one row create a multixact; heavy `FOR SHARE` or foreign-key traffic consumes multixact IDs, which also need freezing (see [vacuum-and-maintenance.md](vacuum-and-maintenance.md#multixact-wraparound)).

## Table lock modes

Each statement takes a table-level lock; two transactions conflict when their modes conflict.

| Mode | Taken by | Conflicts with |
| --- | --- | --- |
| `ACCESS SHARE` | `SELECT` | `ACCESS EXCLUSIVE` |
| `ROW SHARE` | `SELECT ... FOR UPDATE/SHARE` | `EXCLUSIVE`, `ACCESS EXCLUSIVE` |
| `ROW EXCLUSIVE` | `INSERT`, `UPDATE`, `DELETE`, `MERGE` | `SHARE`, `SHARE ROW EXCLUSIVE`, `EXCLUSIVE`, `ACCESS EXCLUSIVE` |
| `SHARE UPDATE EXCLUSIVE` | `VACUUM` (not `FULL`), `ANALYZE`, `CREATE INDEX CONCURRENTLY`, `REINDEX CONCURRENTLY`, `ALTER TABLE ... VALIDATE CONSTRAINT`, most of `REPACK (CONCURRENTLY)` (19) | itself, `SHARE` and stronger |
| `SHARE` | `CREATE INDEX` (non-concurrent) | `ROW EXCLUSIVE`, `SHARE UPDATE EXCLUSIVE`, `SHARE ROW EXCLUSIVE`, `EXCLUSIVE`, `ACCESS EXCLUSIVE` (not itself, so two non-concurrent `CREATE INDEX` on one table can run together) |
| `SHARE ROW EXCLUSIVE` | `CREATE TRIGGER`, some `ALTER TABLE` forms | `ROW EXCLUSIVE` and stronger |
| `EXCLUSIVE` | `REFRESH MATERIALIZED VIEW CONCURRENTLY` | everything except `ACCESS SHARE` |
| `ACCESS EXCLUSIVE` | `DROP`, `TRUNCATE`, most `ALTER TABLE`, `VACUUM FULL`, `CLUSTER`, `REPACK` without `CONCURRENTLY`, `REINDEX` (non-concurrent), `LOCK TABLE` default | everything, including `SELECT` |

### The lock queue problem

Lock requests queue in arrival order. An `ALTER TABLE` waiting for `ACCESS EXCLUSIVE` behind one long `SELECT` blocks every new `SELECT` and `INSERT` that arrives after it, even though they do not conflict with the running `SELECT`. A five-second-long query plus a waiting DDL becomes a five-second outage.

Rule: every DDL on a hot table runs with a short `lock_timeout` and a retry loop.

```sql
SET lock_timeout = '2s';         -- give up instead of queueing indefinitely
SET statement_timeout = '30s';   -- bound the work once the lock is held
ALTER TABLE orders ADD COLUMN note text;  -- metadata-only change
-- on SQLSTATE 55P03 (lock_not_available): wait, retry; do not raise the timeout blindly
```

`lock_timeout` and `statement_timeout` default to 0 (disabled) on 14 to 19 (container). Set them per session for migrations, not globally.

## Find blockers

```sql
-- who blocks whom, with ages
SELECT a.pid,
       pg_blocking_pids(a.pid) AS blocked_by,
       a.state, a.wait_event_type, a.wait_event,
       now() - a.xact_start AS xact_age,
       now() - a.query_start AS query_age,
       left(a.query, 120) AS query
FROM pg_stat_activity a
WHERE cardinality(pg_blocking_pids(a.pid)) > 0
ORDER BY xact_age DESC;

-- lock detail for one relation
SELECT l.pid, l.mode, l.granted, l.waitstart, a.state, left(a.query, 80)
FROM pg_locks l JOIN pg_stat_activity a USING (pid)
WHERE l.relation = 'orders'::regclass
ORDER BY l.granted DESC, l.waitstart;
```

Reading the output:

- `wait_event_type = 'Lock'` with `wait_event = 'relation'` is a table-lock wait; `transactionid` or `tuple` is a row-lock wait.
- The root blocker is the pid that appears in `blocked_by` but is not itself blocked. Often it is `idle in transaction`: an application opened a transaction and stopped.
- `pg_locks.waitstart` (14+) shows when the wait began.

Resolve: `SELECT pg_cancel_backend(pid);` cancels the current query; `SELECT pg_terminate_backend(pid);` ends the session (rolls back its transaction). Cancel first. On RDS and Aurora `rds_superuser` can do both.

Prevent: set `idle_in_transaction_session_timeout` (for example `'5min'`) for application roles; on 17+ set `transaction_timeout` for roles whose transactions must never run long. Container: both default to 0.

## Deadlocks

PostgreSQL checks for a deadlock after a lock wait reaches `deadlock_timeout` (default 1s) and aborts one participant with SQLSTATE `40P01`. The server log shows both statements. Container output from 19.0 (two sessions updating `acct` rows 1 and 2 in opposite order):

```
ERROR:  deadlock detected
DETAIL:  Process 118 waits for ShareLock on transaction 682; blocked by process 125.
        Process 125 waits for ShareLock on transaction 681; blocked by process 118.
        Process 118: BEGIN; UPDATE acct SET bal=bal-1 WHERE id=1; ...
        Process 125: BEGIN; UPDATE acct SET bal=bal-1 WHERE id=2; ...
HINT:  See server log for query details.
CONTEXT:  while updating tuple (0,2) in relation "acct"
```

With `log_lock_waits = on` (default from 19; set it explicitly on 14 to 18) the log also records `process N still waiting for ShareLock ... after 1000 ms` before the deadlock is detected.

Fixes, in order of preference:

1. Touch rows in a consistent order (sort keys before a batch update: `UPDATE ... WHERE id = ANY($1)` does not guarantee order; use `SELECT ... ORDER BY id FOR UPDATE` first).
2. Keep transactions short; do not hold locks across network calls.
3. Retry on `40P01` in the application.
4. Do not raise `deadlock_timeout` to hide deadlocks; raise it only if detection overhead itself is measurable.

## Safe DDL patterns

| Goal | Unsafe on a busy table | Safer pattern |
| --- | --- | --- |
| Add index | `CREATE INDEX` (blocks writes for the whole build) | `CREATE INDEX CONCURRENTLY` (not in a transaction block; on failure leaves an `INVALID` index to drop with `DROP INDEX CONCURRENTLY`) |
| Rebuild index | `REINDEX` | `REINDEX INDEX CONCURRENTLY idx` |
| Add column with default | — | `ADD COLUMN c int DEFAULT 0` is metadata-only for non-volatile defaults; a volatile default (`DEFAULT random()`, `clock_timestamp()`) rewrites the table |
| Add `NOT NULL` | `ALTER COLUMN c SET NOT NULL` scans under `ACCESS EXCLUSIVE` | `ADD CONSTRAINT c_nn CHECK (c IS NOT NULL) NOT VALID;` then `VALIDATE CONSTRAINT c_nn;` (`SHARE UPDATE EXCLUSIVE`), then `SET NOT NULL` uses the valid check to skip the scan, then drop the check. On 18+, `NOT NULL` constraints can also be added `NOT VALID` directly. |
| Add foreign key | `ADD FOREIGN KEY` validates under locks on both tables | `ADD CONSTRAINT ... FOREIGN KEY ... NOT VALID;` then `VALIDATE CONSTRAINT` |
| Change column type | `ALTER COLUMN TYPE` rewrites table and indexes (except binary-compatible changes such as `varchar(n)` to larger `n` or `text`) | add new column, backfill in batches, swap in a short transaction |
| Remove bloat | `VACUUM FULL`, `CLUSTER` | `REPACK (CONCURRENTLY)` on 19; earlier, an external tool (out of scope) or a planned window |
| Detach partition | `DETACH PARTITION` | `DETACH PARTITION ... CONCURRENTLY` (14+, not in a transaction block) |

Always rehearse DDL on a restored copy with realistic size, and run it with `lock_timeout`.

Verify after the change:

```sql
SELECT indexrelid::regclass, indisvalid, indisready FROM pg_index WHERE NOT indisvalid;  -- leftovers from failed CONCURRENTLY builds
SELECT conname, convalidated FROM pg_constraint WHERE conrelid = 'orders'::regclass;
```

## Advisory locks

`pg_advisory_lock(key)` / `pg_advisory_xact_lock(key)` give application-defined mutexes (for example, one migration runner at a time). Prefer the `_xact_` variants: they release at transaction end. Session-level advisory locks survive `COMMIT` and break with transaction-pooling connection poolers.

## Prepared (two-phase) transactions

`max_prepared_transactions` defaults to 0 (container). A forgotten prepared transaction holds locks and the xmin horizon indefinitely and blocks major upgrades. Check `SELECT gid, prepared, owner FROM pg_prepared_xacts;` and `COMMIT PREPARED` or `ROLLBACK PREPARED` stale ones.
