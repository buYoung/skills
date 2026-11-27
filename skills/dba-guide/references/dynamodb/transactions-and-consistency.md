# DynamoDB Transactions and Consistency

Checked: 2026-11-27. Applies to the service as documented on that date.

Contents: read consistency; single-item atomicity and conditional writes; concurrency control choices; transactions; retries and ambiguous failures; batch operations; PartiQL transactions; common mistakes.

## Read Consistency

| Read target | Default | Strong available | Notes |
|---|---|---|---|
| Table (`GetItem`, `Query`, `Scan`) | Eventually consistent | Yes, `ConsistentRead=true`, double the read units | Strong reads reflect all prior successful writes |
| LSI | Eventually consistent | Yes (a `--consistent-read` LSI query in DynamoDB local 3.3.2 fetched a non-projected attribute from the table) | Fetched table attributes are consistent with the index |
| GSI | Eventually consistent | No; `ValidationException` (confirmed in DynamoDB local 3.3.2) | Propagation is usually under a second but can lag in failure cases |
| DynamoDB Streams | Eventually consistent | No | |
| MREC global table, other Region | Last writer wins, replicated typically within a second | A strong read is current only for writes made in the reading Region | |
| MRSC global table, any replica | — | Yes, returns the latest version from any Region | Higher write and strong-read latency |

All reads are read-committed: they never show a write that did not succeed. An HTTP 200 on a write means it is durable.

Decision rules:

- Use strongly consistent reads on the table (or LSI) for read-after-write in the same Region, for example when a request reads back what it just wrote, or for conditional logic done in the application.
- Do not route read-after-write paths through a GSI. If a GSI must be current, read the item from the table by its key after finding it in the index.
- After a transaction, use strongly consistent reads or `TransactGetItems` to see all of its effects at once.

## Single-Item Atomicity and Conditional Writes

`PutItem`, `UpdateItem`, and `DeleteItem` are atomic on one item and operate on its latest version. Read-modify-write sequences in the application need a condition to be safe.

Atomic counter without a read:

```bash
aws dynamodb update-item --table-name Orders \
  --key '{"PK":{"S":"CUST#1"},"SK":{"S":"ORDER#2026-01-01#1"}}' \
  --update-expression 'SET #t = #t + :one' \
  --expression-attribute-names '{"#t":"total"}' \
  --expression-attribute-values '{":one":{"N":"1"}}' \
  --return-values UPDATED_NEW
```

Insert only if absent:

```bash
aws dynamodb put-item --table-name Orders \
  --item '{"PK":{"S":"CUST#1"},"SK":{"S":"ORDER#2026-01-02#2"},"total":{"N":"20"}}' \
  --condition-expression 'attribute_not_exists(PK)' \
  --return-values-on-condition-check-failure ALL_OLD
```

On a duplicate, DynamoDB local 3.3.2 returned `ConditionalCheckFailedException: The conditional request failed` with the existing item attached (because of `ALL_OLD`). The failed write still consumes write units, and the `ConditionalCheckFailedRequests` metric counts it (it is not part of `UserErrors`). Do not retry a conditional failure unchanged; it is not transient.

Optimistic locking: store a `version` Number; update with `--condition-expression '#v = :expected'` and `SET #v = #v + :one`. On `ConditionalCheckFailedException`, re-read and retry. This does not protect against concurrent writes in different Regions of an MREC global table, where last writer wins without evaluating your condition against the other Region's version.

## Concurrency Control Choices

| Approach | Mechanism | Use when | Cost |
|---|---|---|---|
| Atomic update | `UpdateItem` with `SET`/`ADD` expressions | The new value depends only on the stored value | One write |
| Optimistic locking | Version attribute plus condition expression | Single item, rare conflicts, cheap retries | Failed attempts still charged |
| Transaction | `TransactWriteItems` with conditions | Several items must change together, or a write depends on another item's state | 2x units per item, conflicts cancel |
| Lock table | Lease item with expiry and heartbeat (lock client) | Long critical sections, coordinating external resources | Extra table and code |

## Transactions

`TransactWriteItems` groups up to 100 actions (`Put`, `Update`, `Delete`, `ConditionCheck`) on up to 100 distinct items, at most 4 MB total, across tables in one account and Region. `TransactGetItems` groups up to 100 `Get` actions under the same limits. All succeed or none do.

Constraints:

- Two actions on the same item in one transaction are rejected, including a `ConditionCheck` plus an `Update` of the same key (DynamoDB local 3.3.2: `ValidationException: Transaction request cannot include multiple operations on one item`).
- No transactions on indexes; no cross-account or cross-Region transactions.
- MRSC global tables reject transactions. On MREC global tables, a transaction is atomic only in the Region where it ran; other Regions can see partial results while replication catches up.
- Changes reach GSIs, streams, backups, and exports gradually after commit. Stream records from one transaction can appear at different times and interleave with other transactions; a restore or export taken mid-propagation can contain part of a transaction.

Isolation between a transaction and other operations:

| Other operation | Isolation |
|---|---|
| `GetItem`, `PutItem`, `UpdateItem`, `DeleteItem` | Serializable |
| Another transaction | Serializable |
| `BatchGetItem`, as a unit | Read-committed (each item serializable) |
| `BatchWriteItem`, as a unit | Not serializable (each item serializable) |
| `Query`, `Scan` | Read-committed |

Several `GetItem` calls racing one transaction can see a mix of old and new items; use `TransactGetItems` for a consistent multi-item read.

Conflicts and errors:

| Situation | Error |
|---|---|
| A condition in the transaction is false | `TransactionCanceledException`; `CancellationReasons` has one entry per action in request order with code `ConditionalCheckFailed` for the failing one and the literal string `None` for the others |
| Another transaction holds one of the items | `TransactionCanceledException` with code `TransactionConflict` ("Transaction is ongoing for the item") |
| An LSI item collection would exceed 10 GB | `TransactionCanceledException` with code `ItemCollectionSizeLimitExceeded` |
| Capacity exceeded for one item | `TransactionCanceledException` with code `ProvisionedThroughputExceeded`, or a throttling exception |
| A plain `PutItem`/`UpdateItem`/`DeleteItem` hits an item in an ongoing transaction | `TransactionConflictException` |
| Same client token, different parameters, within 10 minutes | `IdempotentParameterMismatchException` (DynamoDB local 3.3.2 returned it with an empty message) |

AWS SDKs do not retry `TransactionCanceledException`. A `GetItem` that overlaps a transaction does not conflict; both succeed. The `TransactionConflict` metric counts rejected item-level requests (Sum adds one per rejected item).

Capacity: every item costs two units (prepare and commit). A transaction writing three 500-byte items once per second needs 6 WCU; reading three such items needs 6 RCU. Canceled transactions consume the same. Default SDK behavior retries on `TransactionInProgressException`; plan read capacity for those retries.

Idempotency: pass `--client-request-token` (the SDKs add one automatically). A repeat within 10 minutes of the original finishing returns success without re-applying. After 10 minutes the same token is a new request.

In DynamoDB local 3.3.2 the example below (an `Orders` table with one `ALL`-projected GSI) reported 6.0 units (with `INDEXES`: `Table` 4.0, `GSI1` 2.0). A repeat with the same token reported 2.0 table units and left `total` unchanged. A failed `ConditionCheck` returned `TransactionCanceledException` with `CancellationReasons` `[{"Code":"None"},{"Code":"ConditionalCheckFailed","Message":"The conditional request failed."}]` and did not apply the update. The AWS CLI prints the reasons in full only with `--cli-error-format json`.

Example (the update aliases `total`, a reserved word; an unaliased version failed in DynamoDB local 3.3.2 with a reserved keyword `ValidationException`):

```bash
aws dynamodb transact-write-items --return-consumed-capacity TOTAL \
  --client-request-token order-1-total-inc-0001 \
  --transact-items '[
    {"Update":{"TableName":"Orders",
      "Key":{"PK":{"S":"CUST#1"},"SK":{"S":"ORDER#2026-01-01#1"}},
      "UpdateExpression":"SET #t = #t + :one",
      "ExpressionAttributeNames":{"#t":"total"},
      "ExpressionAttributeValues":{":one":{"N":"1"}}}},
    {"ConditionCheck":{"TableName":"Orders",
      "Key":{"PK":{"S":"CUST#1"},"SK":{"S":"ORDER#2026-01-02#2"}},
      "ConditionExpression":"attribute_exists(PK)"}}
  ]'
```

Best practices: keep transactions small; split them when correctness allows; group attributes that always change together into one item; avoid transactions for bulk loading (use `BatchWriteItem`, import from S3, or bulk put items). DynamoDB local never throws `TransactionConflictException`, so test conflict handling with mocks and on the service.

## Retries and Ambiguous Failures

| Error | Retry? |
|---|---|
| `ProvisionedThroughputExceededException`, `ThrottlingException`, `RequestLimitExceeded` | Yes, with backoff; SDKs retry automatically |
| `ReplicatedWriteConflictException` (MRSC) | Yes, once the other Region's write finishes |
| `ItemCollectionSizeLimitExceededException` | Documented as retryable, but succeeds only after the collection shrinks |
| `ConditionalCheckFailedException`, `ValidationException`, `ResourceNotFoundException`, `AccessDeniedException` | No; fix the request |
| `InternalServerError` (500), `ServiceUnavailable` (503) | Yes |
| `TransactionConflictException` | Retry after a backoff. The transactions page says SDKs do not retry `TransactionCanceledException` but is silent on this one; check your SDK's retryable error codes and add an application retry if it is not listed |

An HTTP 500 on a single-item write is ambiguous: the write may or may not have happened. Before retrying `PutItem`, `UpdateItem`, or `DeleteItem`, read the item or use a condition expression that makes the retry safe. `TransactWriteItems` can be retried safely because of its client token.

## Batch Operations

`BatchWriteItem` (up to 25 puts or deletes, 16 MB) and `BatchGetItem` (up to 100 items, 16 MB) are not atomic. Individual items are atomic; the batch is not. Unprocessed work comes back in `UnprocessedItems` (writes) or `UnprocessedKeys` (reads) for retry with exponential backoff; a throttling exception is returned only when nothing could be processed. The whole `BatchWriteItem` is rejected when a table does not exist, keys do not match the schema, the same item appears twice, there are more than 25 requests (DynamoDB local 3.3.2: `ValidationException: Too many items requested for the BatchWriteItem call`), an item exceeds 400 KB, or the request exceeds 16 MB. `BatchWriteItem` cannot update; use `UpdateItem` or a transaction.

## PartiQL Transactions

`ExecuteTransaction` and `BatchExecuteStatement` run PartiQL statements with transaction and batch semantics respectively. A PartiQL statement without partition key equality or `IN` becomes a scan, which is inappropriate inside latency-sensitive paths.

## Common Mistakes

- Reading from a GSI immediately after a write and treating a missing item as "not found".
- Expecting optimistic locking to work across MREC Regions.
- Expecting stream consumers to see a transaction as one unit.
- Retrying `TransactionCanceledException` blindly when the cause is a failed condition; inspect `CancellationReasons` first.
- Using transactions for every write "for safety" and paying double capacity.
- Treating `BatchWriteItem` success as "all written" without checking `UnprocessedItems`.
- Retrying a non-idempotent `UpdateItem` (counter increment) after a 500 without checking whether it applied.
