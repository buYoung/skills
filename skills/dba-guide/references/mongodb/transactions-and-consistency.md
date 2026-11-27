# MongoDB Transactions and Consistency

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)). Ticket-based admission control is in [configuration](configuration.md#concurrency-and-admission-control).

## Concurrency model

- WiredTiger uses MVCC: each operation reads a point-in-time snapshot taken at its start.
- Writes use document-level concurrency with optimistic control. Global, database, and collection levels take only intent locks.
- When two writes conflict on the same document, one gets a `WriteConflict`. Outside transactions the server retries it transparently. Inside a transaction the transaction aborts with `TransientTransactionError` (below).
- Some operations still take strong locks:
  - Index builds hold an exclusive collection lock at start and end.
  - `renameCollection` across databases needs database locks. In 9.0 on replica sets it also holds exclusive locks on both collections for the whole operation.
  - The release notes and the FAQ mention other global-lock operations; check before running DDL on a busy system.
- `minSnapshotHistoryWindowInSeconds` (300 on the images) sets how long snapshot history is kept for snapshot reads. Raising it grows `WiredTigerHS.wt` and cache pressure.

There are no deadlocks in the SQL sense for single-document writes. Contention shows up as write-conflict retries:
- 9.0 adds `metrics.operation.writeConflictRetryLimitHit` and `writeConflictRetryWaiters`.
- `serverStatus().metrics.operation.writeConflicts` is listed in the serverStatus reference without a version note, so it is the counter to use before 9.0.

## Defaults on the covered versions

`db.adminCommand({ getDefaultRWConcern: 1 })` on the 7.0, 8.0, 8.3, and 9.0 images (single-node replica set, no arbiter) returned the same result:

```text
defaultReadConcern: { level: 'local' }
defaultWriteConcern: { w: 'majority', wtimeout: 0 }
defaultReadConcernSource: 'implicit', defaultWriteConcernSource: 'implicit'
```

The implicit default write concern is `w: "majority"`, except in replica sets with arbiters. There, when the number of data-bearing voting members is not greater than the voting majority, the default is `w: 1`.

| Data-bearing | Arbiters | Voting | Majority | Implicit default |
| --- | --- | --- | --- | --- |
| 3 | 0 | 3 | 2 | `majority` |
| 2 | 1 | 3 | 2 | `w: 1` |
| 4 | 1 | 5 | 3 | `majority` |

A PSA (primary-secondary-arbiter) set therefore defaults to `w: 1`, and writes acknowledged there can be rolled back after failover. Set a cluster-wide default explicitly instead of relying on the implicit one:

```javascript
db.adminCommand({ setDefaultRWConcern: 1,
                  defaultWriteConcern: { w: "majority", wtimeout: 0 },
                  defaultReadConcern: { level: "local" } })
```

Verify with `getDefaultRWConcern`; the `...Source` fields change from `implicit` to `global`. All four images showed `defaultWriteConcernSource: 'global'` and `defaultReadConcernSource: 'global'` after this command.

## Choose read concern, write concern, read preference

| Need | Write concern | Read concern | Read preference |
| --- | --- | --- | --- |
| Acknowledged writes that survive failover | `w: "majority"` (journaled by default via `writeConcernMajorityJournalDefault`) | — | — |
| Read only data that cannot be rolled back | — | `majority` | any |
| Read-your-own-writes across members | `majority` | `majority`, inside a causally consistent session | any |
| Latest data, may be rolled back | — | `local` (default) | `primary` |
| Multi-shard point-in-time read | — | `snapshot` (in transactions, or with `atClusterTime`) | — |
| Read from secondaries for analytics | — | `local` or `majority` | `secondary` / `secondaryPreferred` with `maxStalenessSeconds` |

Facts that change the decision:

- Since 8.0, a `w: "majority"` acknowledgment means a majority has written the oplog entry, not yet applied it. A read on a secondary right after the acknowledgment, outside a causally consistent session, may not see the write. Use causal consistency (majority read and write concern in a session) when the application reads from secondaries after writing. See [8.0](versions/8.0.md#changed-defaults).
- Causal consistency is guaranteed only when the session uses both `majority` read concern and `majority` write concern.
- `w: 1` writes can be rolled back when the primary fails before replicating them. Rolled-back documents are written as BSON files under `<dbpath>/rollback/<collectionUUID>/` on the old primary (`removed.<timestamp>.bson`); read them with `bsondump`. Rolled-back drops and deletions are not written (rollbacks page).
- Database-, collection-, and operation-level read/write concerns are ignored inside transactions. Set them on the transaction.

## Multi-document transactions

Requirements and limits:

- Transactions need a replica set or a sharded cluster; standalones do not support them.
- Runtime limit: `transactionLifetimeLimitSeconds` defaults to 60 on all four images. A cleanup process aborts expired transactions. On sharded clusters, change the value on every shard member.
- Lock wait: `maxTransactionLockRequestTimeoutMillis` defaults to 5 ms on all four images. After that the transaction aborts instead of waiting for a lock. Raising it reduces aborts from brief DDL contention but delays aborting deadlocked work. `-1` uses the operation's own timeout.
- Concurrency limit: `maxConcurrentMultiDocumentTransactions` (9.0, and from patches 7.0.48, 8.0.30, 8.3.7 through SERVER-108215) defaults to 10000 open transactions server-wide for external clients. Beyond it, new transactions fail with `TooManyOpenTransactions` (code 509). `0` disables the limit. Containers 7.0.48 and 8.0.38 with the limit set to 1: the second open transaction failed with `cannot start a new multi-document transaction; there are already 1 open transactions, which meets or exceeds the limit of 1`; with `0` it succeeded. Idle transactions left open by an application count against the limit.
- Size: a transaction can use many oplog entries, so there is no 16 MB limit on the total. Each oplog entry still must fit in 16 MB.
  - An uncommitted transaction that causes cache pressure aborts with a write conflict.
  - One that can never fit in the cache fails with `TransactionTooLargeForCache`, which the server does not retry (6.2+).
  - 8.3 adds `cachePressureQueryPeriodMilliseconds`: under cache pressure the oldest transaction is aborted.
- Reads inside a transaction must use read preference `primary`, and all operations route to the same member.
- Not allowed inside a transaction:
  - writes to capped collections or `system.*`;
  - any access to the `config`, `admin`, or `local` databases;
  - `count` (use `countDocuments` or `$count`);
  - `listCollections`, `listIndexes`, `createUser`, `getParameter`, `explain`, and parallel operations;
  - `$graphLookup` or `distinct` on sharded collections.
- Collections can be created inside a transaction unless it is a cross-shard write transaction. Indexes can be created only on new, empty collections. Explicit creation requires read concern `local`.
- Arbiters:
  - A shard key cannot be changed in a transaction on a replica set with an arbiter.
  - A multi-shard write transaction aborts if it touches a shard that has an arbiter.
  - Transactions are refused on shards with `writeConcernMajorityJournalDefault: false`.

Write concern and read concern inside transactions:

- `w: "majority"` on commit is what makes `majority` or `snapshot` reads inside the transaction meaningful. With `w: 1`, a committed transaction can be rolled back on failover.
- Setting write concern on individual operations inside a transaction returns an error.

### Error handling and retries

The images reproduce a write conflict: a write to a document already modified in another open transaction returns:

```text
{ code: 112, codeName: 'WriteConflict', labels: [ 'TransientTransactionError' ] }
```

- `TransientTransactionError`: retry the whole transaction from the start.
- `UnknownTransactionCommitResult` on commit: retry `commitTransaction`. The driver applies `w: "majority"` to commit retries.
- The drivers' callback API (`withTransaction`) retries both automatically. With the core API you must code the retry loop.
- Server errors such as `DuplicateKey` can end the transaction without an explicit abort. From 8.1, an upsert inside a transaction does not retry on a duplicate key error.

### Sizing transactions

- Keep transactions short, and touch documents in a consistent order to reduce conflicts. Abort on any error rather than continuing.
- DDL interplay:
  - A pending `createIndex` or `drop` on a namespace waits behind open transactions that use it.
  - New transactions on that namespace then abort after `maxTransactionLockRequestTimeoutMillis`.
  - Issue `create` and `drop` with `w: "majority"` before a transaction that uses the collection.
- Stale reads inside a transaction are possible. To lock a single document for read-modify-write, update it inside the transaction, for example with `findOneAndUpdate` setting a lock field.
- The transaction production-considerations page gives no document-count limit. Size transactions by testing with production-like data against the 60-second lifetime and the per-entry 16 MB limit above.

Verify a transaction setup:

```javascript
const s = db.getMongo().startSession();
s.startTransaction({ readConcern: { level: "snapshot" }, writeConcern: { w: "majority" } });
const c = s.getDatabase("dbaverify").accounts;
c.updateOne({ _id: 1 }, { $inc: { balance: -10 } });
c.updateOne({ _id: 2 }, { $inc: { balance: 10 } });
s.commitTransaction(); s.endSession();
```

This exact snippet ran on all four images (single-node replica set) and left balances `90` and `10`.

## Retryable writes and failover

- Compatible drivers enable retryable writes by default. A single retry covers a primary failover during an election (median below about 12 s with default settings).
- In-progress transactions do not survive an election; the application retries them on `TransientTransactionError`.
- During resharding, retryable writes can be retried for up to 5 minutes. After that they may fail with `IncompleteTransactionHistory`.
