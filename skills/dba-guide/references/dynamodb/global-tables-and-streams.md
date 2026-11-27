# DynamoDB Global Tables, Streams, and TTL

Checked: 2026-11-27. Applies to global tables version 2019.11.21; for legacy 2017.11.29 tables see [versions/global-tables-2017.11.29.md](versions/global-tables-2017.11.29.md). MRSC dates are in [versions/2025.md](versions/2025.md); multi-account global tables and replica disassociation in [versions/2026.md](versions/2026.md).

Contents: choosing a consistency mode; creating and changing global tables; settings synchronization; capacity and quotas; failover and testing; DynamoDB Streams; Kinesis Data Streams; TTL; zero-ETL and analytics feeds; common mistakes.

## Choosing a Consistency Mode

| Property | MREC (default) | MRSC |
|---|---|---|
| Replication | Asynchronous, typically within a second | Synchronous to at least one other Region before success |
| Regions | Any Region, as many as the partition has | Exactly three: three replicas, or two replicas and a witness, from the supported list (15 Regions on 2026-11-27, including us-east-1, us-east-2, us-west-2, eu-west-1, ap-northeast-1) |
| Concurrent writes to one item | Last writer wins per item (internal timestamp) | Second writer gets `ReplicatedWriteConflictException`; retry succeeds once the other write finishes |
| Strong reads | Current only for writes made in the same Region | Latest version in every replica |
| Conditional writes | Evaluated against the local Region's version | Evaluated against the latest version |
| RPO on Region loss | Replication delay, usually seconds | Zero |
| Latency | Lower | Higher writes and strong reads; depends on Region distance |
| Creation | Add a replica to an existing table with data | Convert an empty table; no writes during conversion |
| Changing membership | Add or remove replicas any time; disassociate a replica to keep it as a standalone table | Cannot add replicas or remove a single replica or witness; removing two members converts the last to a single-Region table |
| TTL | Supported, synchronized, deletes replicated | Not supported |
| LSIs | Supported | Not supported (GSIs supported, eventually consistent) |
| Transactions | Atomic only in the Region that ran them | Rejected with an error |
| Streams | Enabled on every replica, cannot be disabled; records can differ between replicas | Optional; identical on every replica |
| `ReplicationLatency` metric | Published | Not published |
| Default quota | — | 400 MRSC global tables per account |

The mode is chosen at creation and cannot be changed. All replicas share one mode. Global tables carry a 99.999% availability SLA versus 99.99% for single-Region tables.

Choose MRSC when the application needs strongly consistent reads across Regions or an RPO of zero, and can live without TTL, LSIs, and transactions. Choose MREC otherwise, and design the application for last-writer-wins (for example, route writes for one item to one Region, or make writes commutative).

## Creating and Changing Global Tables

MREC, adding a Region to an existing table (production safety: backfill reads the source and writes the new replica; schedule it, and confirm quotas first):

```bash
aws dynamodb update-table --table-name Orders \
  --replica-updates '[{"Create":{"RegionName":"eu-west-1"}}]' --region us-east-2
aws dynamodb describe-table --table-name Orders --region us-east-2 \
  --query 'Table.{Version:GlobalTableVersion,Replicas:Replicas[*].{R:RegionName,S:ReplicaStatus}}'
```

MRSC, from an empty table:

```bash
aws dynamodb update-table --table-name Orders \
  --replica-updates '[{"Create":{"RegionName":"us-east-1"}}]' \
  --global-table-witness-updates '[{"Create":{"RegionName":"us-west-2"}}]' \
  --multi-region-consistency STRONG --region us-east-2
aws dynamodb describe-table --table-name Orders --region us-east-2 \
  --query 'Table.{Mode:MultiRegionConsistency,Replicas:Replicas[*],Witness:GlobalTableWitnesses[*]}'
```

The witness is managed by DynamoDB and does not appear in your account.

Rules and limits:

- The table-level write throughput quota must match in every replica Region before you add a replica; otherwise creation fails with a "exceeds your current account limit" error. Global table throughput quotas must be at least the per-table quotas.
- Backfilling new replicas is limited to 10 TB per destination Region per day by default.
- A table used as the source for a new replica cannot be deleted for 24 hours after the replica is created.
- Adding a replica copies the source Region's provisioned capacity to the new replica regardless of what an infrastructure template says.
- When a Region is disabled, its replicas become single-Region tables permanently after 20 hours.
- Multi-account global tables require a resource-based policy on each replica allowing the replication service.
- Remove a replica with `"Delete"` in `--replica-updates` (production safety: this deletes that Region's table and data; for MREC, disassociate instead if you want to keep it).

## Settings Synchronization

| Always synchronized | Synchronized, overridable per replica | Never synchronized |
|---|---|---|
| Capacity mode; table and GSI provisioned write capacity and write auto scaling; key schema; GSI definitions; SSE type; streams definition (MREC); TTL; warm throughput; on-demand maximum write throughput | Table and GSI provisioned read capacity and read auto scaling; table class; on-demand maximum read throughput | Deletion protection; PITR; tags; Contributor Insights (table and GSI); Kinesis Data Streams destination; resource-based policies; streams definition (MRSC) |

An override is replaced when the same setting is changed on another replica: if us-east-1 goes from 200 to 300 RCU, a us-west-2 override of 100 RCU becomes 300. Enable PITR, deletion protection, and Contributor Insights in every Region separately.

## Capacity and Quotas

- Replication consumes write units on every replica. In provisioned mode, application writes plus replicated writes must fit the replica's write capacity.
- `ConsumedWriteCapacityUnits` has a `Source` dimension: `Customer` for writes you make, `GlobalTable` for replication writes.
- For global tables, limit stream readers per shard to one.
- TTL deletes are free in the Region where they expire, but the replicated deletes are charged in every other Region and can throttle provisioned replicas.
- Writes to replicas bypass DAX in other Regions; DAX caches there serve stale data until their TTL expires.

## Failover and Testing

DynamoDB does not move application traffic. The application or routing layer (DNS, client configuration) decides which Region to use.

1. Monitor `ReplicationLatency` per `ReceivingRegion` for MREC. A rising value means updates are not propagating; move traffic to a healthy Region.
2. For MREC, data written in the impaired Region but not yet replicated arrives when the Region recovers; expect last-writer-wins reconciliation of items written in both Regions meanwhile.
3. For MRSC, a Region that comes back after a full outage catches up automatically. Until then, writes and strongly consistent reads sent to that Region return errors and eventually consistent reads return what has propagated so far; the other Regions work normally ("Using DynamoDB global tables", updated 2026-04-16). The page names no error code, so route writes and strong reads to another Region and log what the SDK returns.
4. Rehearse with AWS Fault Injection Service actions that pause replication to and from a replica; during the experiment, table setting updates are not allowed. Alarm on `FaultInjectionServiceInducedErrors` to separate injected errors from real `SystemErrors`.

## DynamoDB Streams

Enable or change:

```bash
aws dynamodb update-table --table-name Orders \
  --stream-specification StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES
aws dynamodb describe-table --table-name Orders --query 'Table.{Spec:StreamSpecification,Arn:LatestStreamArn}'
```

| View type | Record contains |
|---|---|
| `KEYS_ONLY` | Key attributes |
| `NEW_IMAGE` | Item after the change |
| `OLD_IMAGE` | Item before the change |
| `NEW_AND_OLD_IMAGES` | Both |

Behavior that drives design:

- Records are kept 24 hours; older records can be trimmed at any time. A consumer down for more than a day loses data; use Kinesis Data Streams or exports when longer retention is needed.
- Each record appears exactly once. Ordering is guaranteed per item (per primary key), not across items or across an item collection.
- Each open shard corresponds to one table partition; shards split and close as partitions change. Process parent shards before children (the Kinesis adapter and Lambda do this).
- At most two readers per shard for single-Region tables, one for global tables; more readers throttle.
- `StreamViewType` cannot be changed. Disable and re-enable to change it; that creates a new stream with a new ARN, and the old stream stays readable for 24 hours. Repoint consumers.
- A `PutItem` or `UpdateItem` that changes nothing writes no record.
- Lambda reads each shard with one function instance in sequence-number order; `ParallelizationFactor` up to 10 adds concurrency per shard while keeping per-item order.
- Read API: `ListStreams`, `DescribeStream` (with `ShardFilter` for child shards, at most 10 calls per second), `GetShardIterator`, `GetRecords`, on the separate Streams endpoint. SDKs now use account-based Streams endpoints; allow them in egress filters ([versions/2026.md](versions/2026.md)).
- Stream records are encrypted at rest with the table's key.

Inspect a stream (CLI service name `dynamodbstreams`):

```bash
ARN=$(aws dynamodb describe-table --table-name Orders --query Table.LatestStreamArn --output text)
aws dynamodbstreams describe-stream --stream-arn "$ARN" --query 'StreamDescription.Shards[*].ShardId'
IT=$(aws dynamodbstreams get-shard-iterator --stream-arn "$ARN" --shard-id <shard-id> \
  --shard-iterator-type TRIM_HORIZON --query ShardIterator --output text)
aws dynamodbstreams get-records --shard-iterator "$IT" --limit 10
```

Against DynamoDB local 3.3.2 (add `--endpoint-url` to each call), the stream had one shard and one `UpdateItem` produced one record with `eventName` `MODIFY` and both `dynamodb.OldImage` and `dynamodb.NewImage`.

## Kinesis Data Streams for DynamoDB

| Property | DynamoDB Streams | Kinesis Data Streams destination |
|---|---|---|
| Retention | 24 hours | Kinesis retention settings (longer) |
| Ordering and duplicates | Exactly once, ordered per item | Records can be out of order and duplicated; use `ApproximateCreationDateTime` (millisecond or microsecond precision) to order and deduplicate |
| Consumers | Two per shard | Kinesis fan-out, Firehose, Managed Service for Apache Flink |
| Destinations | One stream per table | One Kinesis stream per table, same account and Region |
| Binary values | Base64 once | Base64-encoded twice; decode twice |
| Billing | Read requests | Change data capture units (1 KB of the larger image per item) plus Kinesis charges |

```bash
aws dynamodb enable-kinesis-streaming-destination --table-name Orders \
  --stream-arn arn:aws:kinesis:us-east-1:123456789012:stream/orders-cdc \
  --enable-kinesis-streaming-configuration ApproximateCreationDateTimePrecision=MICROSECOND
aws dynamodb describe-kinesis-streaming-destination --table-name Orders
```

The precision can be changed at most three times per 24 hours. Disabling is asynchronous; a few in-flight records may still arrive until the status is `DISABLED`. Monitor `AgeOfOldestUnreplicatedRecord`, `FailedToReplicateRecordCount`, and `ThrottledPutRecordCount`; size the Kinesis stream for the table's write rate.

## TTL

```bash
aws dynamodb update-time-to-live --table-name Orders \
  --time-to-live-specification Enabled=true,AttributeName=expiresAt
aws dynamodb describe-time-to-live --table-name Orders
```

- The attribute must be a Number holding epoch seconds. Items whose TTL attribute is another type are ignored.
- Expired items are deleted typically within a few days, without consuming write capacity. Until then they are returned by reads; filter them (`#e > :now`).
- You can still update an expired item before deletion; changing or removing its TTL value saves it. Use a condition expression so the update does not recreate an item that was just deleted.
- TTL deletes appear in streams with `userIdentity.type = "Service"` and `userIdentity.principalId = "dynamodb.amazonaws.com"`. Filter on these in Lambda event source mappings to archive expired items. On global tables, only the Region where TTL ran carries `userIdentity`.
- TTL deletes remove index entries like normal deletes and are counted by `TimeToLiveDeletedItemCount`. CloudTrail does not log TTL deletions.
- `UpdateTimeToLive` allows one enable or disable per table per hour and takes up to an hour to process; calling it again (or enabling when already enabled) returns `ValidationException`. `DescribeTimeToLive` is limited to 10 requests per second.
- Not supported on MRSC global tables. On legacy 2017.11.29 global tables TTL is per Region and not replicated.

## Zero-ETL and Analytics Feeds

| Target | Mechanism | Prerequisites | Freshness |
|---|---|---|---|
| Amazon Redshift | Full export, then incremental exports | PITR on the table; resource-based policy granting Redshift access | Every 15 to 30 minutes |
| SageMaker Lakehouse | Zero-ETL integration (2024-12-03) | See the integration page | Typically within 15 to 30 minutes; no table capacity consumed |
| Amazon OpenSearch Service | OpenSearch Ingestion pipeline (2023-11-28) | See the integration page | Initial snapshot through export to S3 (needs PITR), then Streams in near real time |
| S3 | Export to S3 (full, incremental, filtered) | PITR | Asynchronous; no completion SLA |

None of these consume table read capacity. Use them instead of `Scan`-based extract jobs.

## Common Mistakes

- Choosing MRSC and then needing TTL or transactions.
- Adding a replica without matching the table-level write quota in every Region.
- Relying on version-check optimistic locking across MREC Regions.
- Expecting PITR, deletion protection, or Contributor Insights to follow a new replica.
- Building a consumer that assumes global ordering of stream records, or that stream records group a transaction.
- Recreating a stream to change the view type without repointing consumers to the new ARN.
- Treating TTL as an exact expiry time.
