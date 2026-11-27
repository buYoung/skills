# DynamoDB Data Modeling

Checked: 2026-11-27. Applies to the service as documented on that date; dated changes are in [versions/index.md](versions/index.md).

Contents: access patterns first; primary keys; single-table or multiple tables; item size and types; secondary indexes; reading with Query, Scan, and PartiQL; time series and expiry; verifying a model; common mistakes.

## Access Patterns First

DynamoDB serves a request efficiently only when the request names a partition key value (and optionally a sort key condition) on the table or on an index. There are no joins, no ad hoc secondary access without an index, and a `Scan` reads every item and charges for every item evaluated. Write down every access pattern with its key inputs, expected rate, result size, and consistency need before choosing keys. A pattern that has no key path becomes a `Scan`, a new GSI, or work outside DynamoDB (export to S3, zero-ETL to Redshift or OpenSearch Service).

## Primary Keys

| Element | Rule | Limit |
|---|---|---|
| Partition key | Hashed to choose the partition; equality only in `KeyConditionExpression` | 1 to 2048 bytes |
| Sort key | Orders items within a partition key; supports `=`, `<`, `<=`, `>`, `>=`, `BETWEEN`, `begins_with` | 1 to 1024 bytes |
| Key types | String, Number, or Binary scalar, top-level attribute | No sets, lists, maps |
| Item collection | All items sharing a partition key value | No size limit unless the table has an LSI (then 10 GB) |

Choose the partition key so that requests spread over many values. Each partition serves at most 3,000 read units and 1,000 write units per second; adaptive capacity moves hot items to their own partition but cannot exceed those per-partition limits for a single key ([capacity-and-performance](capacity-and-performance.md)).

Decision rules:

- High-cardinality identifiers (customer ID, device ID, order ID) make good partition keys. Low-cardinality values (status, date, tenant with one dominant tenant) concentrate traffic.
- Put the hierarchy you query by into the sort key: `ORDER#2026-01-01#1` supports "all orders of a customer", "orders in January" (`begins_with(SK, :p)`), and ranges by date.
- When one key value must absorb more than 1,000 writes per second, shard it: append a random suffix (`2026-07-09.1` to `.200`) and query all suffixes on read, or a calculated suffix (a hash of an attribute you read by, modulo N) so single-item reads can compute the key. Both cost N queries to read the whole logical key.
- Do not use a monotonically increasing value (timestamp) as the sort key for an item collection that receives all the new writes: adaptive capacity cannot split such a collection usefully.

Example used across this reference (confirmed against DynamoDB local 3.3.2):

```bash
aws dynamodb create-table --table-name Orders \
  --attribute-definitions AttributeName=PK,AttributeType=S AttributeName=SK,AttributeType=S \
    AttributeName=GSI1PK,AttributeType=S AttributeName=GSI1SK,AttributeType=S \
  --key-schema AttributeName=PK,KeyType=HASH AttributeName=SK,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --global-secondary-indexes 'IndexName=GSI1,KeySchema=[{AttributeName=GSI1PK,KeyType=HASH},{AttributeName=GSI1SK,KeyType=RANGE}],Projection={ProjectionType=ALL}'

aws dynamodb query --table-name Orders \
  --key-condition-expression 'PK = :pk AND begins_with(SK, :p)' \
  --expression-attribute-values '{":pk":{"S":"CUST#1"},":p":{"S":"ORDER#2026-01"}}' \
  --return-consumed-capacity TOTAL
```

Declare in `--attribute-definitions` only the attributes used in the table and index key schemas; other attributes are schemaless. An extra definition is rejected; DynamoDB local 3.3.2 returned `ValidationException: The number of attributes in key schema must match the number of attributes defined in attribute definitions.`

## Single Table or Multiple Tables

| Factor | Single table (many entity types, shared keys) | Multiple tables (one entity type per table) |
|---|---|---|
| Reads across entity types | One `Query` returns the customer and their orders; one 4 KB eventually consistent read costs 0.5 RCU instead of two | Separate requests; join in the application |
| Backups, PITR, restore | All or nothing for the table | Per entity; critical data can have stricter retention |
| Encryption keys | One key for all entities; per-tenant keys need client-side encryption | Per-table keys possible |
| Table class (Standard-IA) | Less benefit when hot and cold data mix | Apply Standard-IA to history tables only |
| Streams | All changes in one stream; consumers filter | One stream per entity type |
| IAM | One table ARN; item-level control through `dynamodb:LeadingKeys` | Policy per table |
| Capacity and alarms | Traffic averages out; fewer alarms | Each table scaled and alarmed separately |
| Tooling | GraphQL resolvers and object mappers harder | Maps one-to-one to classes |

Use a single table when access patterns read several entity types together. Use multiple tables when entities have different retention, encryption, capacity, or stream-processing needs, or when no pattern crosses entities. Mixed designs are common: one table per bounded context.

## Item Size and Types

- Maximum item size is 400 KB, counting attribute names and values (UTF-8 bytes). With an LSI, the 400 KB limit covers the item plus its entries in all LSIs. Oversized writes fail with `ValidationException: Item size has exceeded the maximum allowed size` (container output).
- Short attribute names save storage and capacity on every item.
- Read units round each item (`GetItem`, `BatchGetItem`) or the whole result (`Query`) up to 4 KB; write units round each item up to 1 KB. `UpdateItem` charges the larger of the before and after images, so updating one attribute of a 300 KB item costs 300 write units.
- Keep large blobs in Amazon S3 and store the object identifier in the item; the primary key can go into the object's S3 metadata as a link back. No transaction spans S3 and DynamoDB, so the application must clean up orphaned objects ([large items best practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-use-s3-too.html)).
- Number: up to 38 digits of precision; pass high-precision values as strings in SDKs to avoid float conversion.
- Empty String and Binary values are allowed on non-key attributes; empty sets are not; empty lists and maps are allowed. Nesting depth up to 32 levels.
- Dates: store ISO-8601 strings for sortable keys, or epoch seconds as Number when the attribute drives TTL.
- Reserved words (`total`, `status`, `name`, `views`, `region`, many more) cannot appear directly in expressions; use `ExpressionAttributeNames`. DynamoDB local 3.3.2 rejected `SET total = total + :one` with `Invalid UpdateExpression: Attribute name is a reserved keyword; reserved keyword: total`; write `SET #t = #t + :one` with `--expression-attribute-names '{"#t":"total"}'`.

Expression limits: expression string 4 KB, 300 operators or functions per expression, 100 operands for `IN`, 255 bytes per placeholder name or value, 2 MB total substitution values.

## Secondary Indexes

| Characteristic | GSI | LSI |
|---|---|---|
| Key | Any scalar attributes; partition key and optional sort key; since 2026 up to four attributes each (multi-attribute keys) | Same partition key as the table, different sort key |
| When created | At table creation or later with `UpdateTable` | Only at table creation; cannot be added or deleted |
| Per table | 20 (adjustable; vector indexes count toward it) | 5 (fixed) |
| Consistency | Eventually consistent only; `ConsistentRead` on a GSI returns `ValidationException: Consistent reads are not supported on global secondary indexes` (container output) | Eventual or strong |
| Capacity | Own read and write capacity (provisioned) or own request units | Uses the base table's capacity |
| Size per partition key value | Unlimited | 10 GB item collection including the table items |
| Non-projected attributes | Not available | Fetched from the table at extra read cost and latency |
| Key uniqueness | Not required; many items can share index key values | Not required |

Projection choice: `KEYS_ONLY` for indexes used to find keys, `INCLUDE` with the attributes the query returns (at most 100 user-specified projected attributes summed over all indexes), `ALL` when the index serves full items. Every projected attribute is copied on every write that touches it, so `ALL` roughly doubles storage and index write cost.

Write cost per GSI on a table write:

| Change to the item | GSI writes |
|---|---|
| New item has the index key attribute | 1 |
| Index key value changes | 2 (delete plus put) |
| Index key attribute removed | 1 |
| Only projected non-key attributes change | 1 |
| Neither index keys nor projected attributes change | 0 |
| Item absent from the index before and after | 0 |

Sparse indexes: items without the index key attribute are not written to a GSI. Set the attribute only on items you want to find ("open orders") and remove it when they leave the set.

GSI back-pressure (provisioned mode): if a GSI lacks write capacity, writes to the base table are throttled. Provision GSI write capacity at least equal to the table's, or use on-demand.

Multi-attribute GSI keys (documented 2026-04-16; DynamoDB local 3.3.0 and later): list several `HASH` and `RANGE` entries in the index `KeySchema`:

```json
"KeySchema": [
  {"AttributeName": "tournamentId", "KeyType": "HASH"},
  {"AttributeName": "region", "KeyType": "HASH"},
  {"AttributeName": "round", "KeyType": "RANGE"},
  {"AttributeName": "bracket", "KeyType": "RANGE"}
]
```

Queries must use equality on every partition key attribute and constrain sort key attributes left to right without gaps. In DynamoDB local 3.3.2 an index with `tournamentId` and `region` as `HASH` and `round` as `RANGE` answered `tournamentId = :t AND #r = :r`, and a query on `tournamentId` alone failed with `ValidationException: HASH key attributes region must have equality conditions specified in the query`.

### Adding a GSI to a Live Table

Production safety: building a GSI reads the whole table and writes the index. Writes to the base table can be throttled if index writes during the build exceed index capacity or concentrate on few index key values.

1. Check the distribution of the new key: enable Contributor Insights on the table; sample values on a restored copy.
2. Prefer a low-traffic window. For tables over 50 TB, request allowlisting first.
3. Create: `aws dynamodb update-table --table-name Orders --attribute-definitions AttributeName=status,AttributeType=S --global-secondary-index-updates '[{"Create":{"IndexName":"status-idx","KeySchema":[{"AttributeName":"status","KeyType":"HASH"}],"Projection":{"ProjectionType":"KEYS_ONLY"}}}]'`
4. Watch `IndexStatus` (`CREATING`, then `ACTIVE`) and `Backfilling` in `describe-table`, `OnlineIndexPercentageProgress`, and the base table's `WriteThrottleEvents` and `ThrottledRequests`. `OnlineIndexConsumedWriteCapacity` and `OnlineIndexThrottleEvents` report 0 during backfill. Raising the index's write capacity does not shorten the build.
5. Roll back by deleting the index while it backfills: `--global-secondary-index-updates '[{"Delete":{"IndexName":"status-idx"}}]'`. One GSI can be deleted per `UpdateTable` call. During backfill you cannot add or delete other indexes or delete the table.
6. Items whose index key attribute has the wrong type are rejected after the backfill; run the documented violation detector if the attribute was written loosely.

`DescribeTable` sizes and item counts for indexes refresh about every six hours. The CreateTable reference contradicts itself on tables with secondary indexes: its description says to create them sequentially (only one in `CREATING` at a time), while its `LimitExceededException` entry allows up to 250 such requests at once. Create them one at a time as the safe default, and treat `LimitExceededException` as a signal to slow down.

### LSI Cautions

Choose an LSI only when you need strongly consistent reads on an alternate sort key and every item collection will stay under 10 GB. When a collection reaches 10 GB, writes that grow it fail with `ItemCollectionSizeLimitExceededException`. Monitor with `ReturnItemCollectionMetrics=SIZE` on writes and alert below 10 GB (for example at 8 GB). An LSI also stops adaptive capacity from splitting an item collection across partitions, and LSIs are not supported on MRSC global tables.

## Reading: Query, Scan, PartiQL

- `Query` and `Scan` return at most 1 MB per call, measured before any `FilterExpression`. A filter does not reduce read units; it only trims the response. Design keys so that filters discard little.
- A non-empty `LastEvaluatedKey` means a page boundary was reached, not that more matching items exist. Keep paging until it is absent.
- `Count` is items returned after the filter; `ScannedCount` is items evaluated. A large gap means wasted reads.
- Reading a nonexistent item still consumes read units; `Select=COUNT` costs the same as reading the items.
- `Scan` returns partition keys in arbitrary order and sorts items by sort key within each partition key. Parallel scan (`Segment`, `TotalSegments`) spreads load across partitions; a single sequential scan can hit key-range throttling at 3,000 read units per second per key range. On DynamoDB local, see [dynamodb-local.md](dynamodb-local.md) for how it treats segments.
- PartiQL `SELECT` becomes a full table scan unless the `WHERE` clause has equality or `IN` on the partition key. `SELECT * FROM Orders WHERE total > 5` ran as a scan in DynamoDB local 3.3.2. IAM can deny full-scan PartiQL statements (see [security-and-monitoring](security-and-monitoring.md)).

## Time Series and Expiry

- Put recent, hot data in one table and move older periods to tables with the Standard-IA table class, where storage dominates cost. All indexes use the table's class. The class can be changed later.
- Use TTL (Number attribute, epoch seconds) to delete expired items without write cost; deletion happens typically within a few days, so filter expired items on read. Details in [global-tables-and-streams](global-tables-and-streams.md).

## Verify a Model

1. Load representative data into a test table (import from S3 creates a new table without consuming write capacity).
2. Run every access pattern with `--return-consumed-capacity INDEXES` and record capacity per call. In DynamoDB local 3.3.2, a put touching the table and one GSI reported `Table 1.0`, `GSI1 1.0`, total 2.0; an eventually consistent GSI query of a small item reported 0.5.
3. Compare `Count` with `ScannedCount` for each query.
4. Enable Contributor Insights in accessed-and-throttled mode during a load test and look for dominant keys.
5. Repeat on the service: DynamoDB local does not model partitions, throttling, or index-size accounting the same way ([dynamodb-local](dynamodb-local.md)).

## Common Mistakes

- Modeling tables like a relational schema and planning to "add an index later" for every new query; LSIs cannot be added later, and every GSI multiplies write cost.
- Using `Scan` with filters as the main read path.
- Low-cardinality GSI partition keys (`status`), which create hot index partitions and throttle base-table writes in provisioned mode.
- Large items updated frequently; every update pays for the full item size.
- Assuming GSI reads see the latest write.
- Relying on the order of `Scan` results across partition keys.
