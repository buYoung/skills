# MongoDB Data Modeling

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)). For index design see [indexes-and-query-plans](indexes-and-query-plans.md). For shard keys see [replication-and-sharding](replication-and-sharding.md).

## Start from access patterns

The manual's core rule is "data that's accessed together should be stored together". Before choosing a shape, collect:

1. The top queries and their frequency, from `$queryStats`, the slow log, or the application.
2. Which fields each query reads and filters on.
3. Which writes must be atomic together.
4. Growth: how many children per parent, now and in three years.
5. The read/write ratio per entity.

A single-document write is atomic, including writes to several embedded subdocuments. If two pieces of data must change together and they fit in one document, embedding makes the operation atomic without a transaction. Multi-document transactions work, but the manual states they cost more than single-document writes and are "not a replacement for effective schema design" (see [transactions-and-consistency](transactions-and-consistency.md)).

## Embed or reference

| Embed when | Reference when |
| --- | --- |
| The relation is "has-a" or "contains" | The child side has high cardinality |
| The data is read together | The embedded part grows without bound |
| The data is updated together | Combined size wastes memory or network bandwidth |
| The data is archived together | Parts are written at different times in a write-heavy workload |
| — | The child can exist without the parent |
| — | Duplicated data would need frequent updates |

Rules that follow from this:

- Bound every embedded array. If the count of children has no hard upper limit (comments, events, log lines), reference them, or group them into bucket documents of N children each.
- Keep large, rarely read data out of the hot document. Larger documents use more cache and push the working set to disk. The manual's example keeps the 5 most recent reviews embedded and all reviews in a separate collection.
- Duplicate only data whose staleness you can tolerate or control. Choose a duplication type:
  - Immutable: safe to copy.
  - Temporal, such as the address at order time: copy on purpose.
  - Staleness-sensitive, such as a stock count: update with a transaction or trigger.
  - Staleness-tolerant: refresh with a background job.
- Joining with `$lookup` at read time is the alternative to duplication. It costs read work on every query; duplication costs write work on every change.

## Limits that shape documents

From https://www.mongodb.com/docs/manual/reference/limits/:

| Limit | Value |
| --- | --- |
| BSON document size | 16 MiB (use GridFS for larger) |
| Nesting depth | 100 levels |
| Namespace `<db>.<collection>` | 255 bytes unsharded, 235 bytes sharded |
| Database name | under 64 bytes |
| Indexes per collection | 64 |
| Fields in a compound index | 32 |
| Index keys generated per document | `indexMaxNumGeneratedKeysPerDocument` default 100000 |

Small documents carry fixed overhead per document. The manual suggests:
- Use a meaningful `_id` instead of an extra indexed key.
- Shorten field names. This saves document bytes, not index bytes.
- Embed tiny documents.

Each index takes at least 8 kB.

## Polymorphism and schema evolution

One collection may hold documents of different shapes. The schema can change without rewriting existing documents. A common convention is a version field per document, with read code that handles every live version; the pages checked do not name it as a documented pattern. Migrate lazily on write, or in batches. To find documents that need migration, use a validator in `warn` mode or `moderate` level (below).

## Schema validation

Validation rules are set with `validator` (`$jsonSchema` or query operators), at `create` time or later with `collMod`.

Levels (`validationLevel`):

| Level | Applies to | Notes |
| --- | --- | --- |
| `strict` (default) | all inserts and updates | existing invalid documents may remain |
| `moderate` | inserts, and updates to documents that already pass | lets old invalid documents be updated without fixing them |
| `off` | nothing | |
| `constraint` (9.0+) | all inserts and updates, and every stored document is guaranteed valid | `validationAction` must be `error` or `errorAndLog`; the validator cannot be changed while at this level; bypass is not allowed |

Actions (`validationAction`):

| Action | Behavior |
| --- | --- |
| `error` (default) | reject the write |
| `warn` | allow the write; log `Document would fail validation` (log id `20294`, component `STORAGE`, severity `W`) |
| `errorAndLog` (8.1+) | reject and log; the 7.0 and 8.0 images reject it at `createCollection` (`BadValue`), 8.3 and 9.0 accept it |

Example. This exact snippet ran on the 7.0, 8.0, 8.3 and 9.0 images: `createCollection` returned `ok: 1` and the invalid insert failed with code `121`, `Document failed validation`.

```javascript
db.createCollection("customers", {
  validator: { $jsonSchema: {
    bsonType: "object",
    required: ["email", "createdAt"],
    properties: {
      email:     { bsonType: "string" },
      createdAt: { bsonType: "date" }
    } } },
  validationLevel: "strict",
  validationAction: "error"
})
db.customers.insertOne({ email: 42 })   // fails: Document failed validation (code 121)
```

Adding validation to an existing collection safely:

1. Measure first by running the rule as a query: `db.customers.countDocuments({ $nor: [ { $jsonSchema: <schema> } ] })`. On all four images the form is accepted (it returned `0` on the empty collection).
2. Apply it with `validationAction: "warn"` and watch the log for id 20294 hits from live traffic.
3. Fix or migrate the violating documents. Then switch to `error`, or to `moderate` if old documents must stay as they are.
4. On 9.0, to reach `constraint` on an existing collection:

   ```javascript
   db.runCommand({ collMod: "customers", validationLevel: "strict" })            // if not already strict
   db.runCommand({ collMod: "customers", prepareConstraintValidationLevel: true })
   db.runCommand({ collMod: "customers", validationLevel: "constraint", validationAction: "error" })
   ```

   On the 9.0.8 image all three commands returned `ok: 1`, and `getCollectionInfos` then showed `validationLevel: 'constraint'`. A single `collMod` that adds a validator to an unvalidated collection and sets `constraint` failed with `validationLevel can only be changed to 'constraint' from 'strict'`; `createCollection` accepts `validationLevel: "constraint"` directly. 8.3.17 rejects `prepareConstraintValidationLevel` as an unknown field and the level itself with `Validation level 'constraint' is not supported with current FCV`; 7.0 and 8.0 reject `constraint` as an invalid enumeration value.

   The last step scans every document and fails if any violates the rule. On large collections this is expensive; run it off-peak. To change the rules later: drop back to `strict`, modify, then upgrade again. You cannot change `validator` in the same `collMod` that sets `constraint`.

Pitfalls:
- Validation does not run on documents already stored, except under `constraint`.
- `bypassDocumentValidation` (in `strict`/`moderate`) lets privileged writers skip rules.
- `errorAndLog`, `constraint`, and validators that use newer expressions block downgrades until removed (see [8.3](versions/8.3.md#upgrading-into-this-series) and [9.0](versions/9.0.md#upgrading-into-this-series)).
- Error output detail is meant for humans and may change. Do not parse it in scripts.

## TTL and lifecycle

- A TTL index removes documents after a date field plus `expireAfterSeconds`. A background monitor does the deletion, so it is not instantaneous. On all four images the monitor runs every 60 seconds (`ttlMonitorSleepSecs`) and `ttlMonitorEnabled` is `true`.
- Example (on all four images this created a TTL index named `lastSeen_1`):

  ```javascript
  db.sessions.createIndex({ lastSeen: 1 }, { expireAfterSeconds: 1800 })
  ```
- On 8.3+, monitor TTL work with `serverStatus().metrics.ttl` (`deletedKeys`, `durationMicros`, `examinedDocuments`, `examinedKeys`).
- Capped collections suit FIFO, insertion-ordered data.

## Time series collections

Use them for measurements keyed by time and a metadata field (device, sensor). They store data compressed in buckets; zstd is the default block compressor for time series collections.

```javascript
db.createCollection("metrics", {
  timeseries: { timeField: "ts", metaField: "device", granularity: "minutes" },
  expireAfterSeconds: 2592000
})
```

This exact snippet returned `ok: 1` on all four images, and `getCollectionInfos` reported type `timeseries`.

Version differences:
- 9.0 stores a time series collection as a single namespace rather than a view over `system.buckets.*`, and allows `renameCollection`.
- 8.3 rejects an index named `_id_` and a `timeField` starting with `$`.
- 8.0.10+ can reshard time series collections.
- On 7.0, custom bucketing (`bucketMaxSpanSeconds`, `bucketRoundingSeconds`) is a backward-incompatible feature; remove it before any downgrade to 6.0.

See the version files before upgrading clusters with many time series collections.
