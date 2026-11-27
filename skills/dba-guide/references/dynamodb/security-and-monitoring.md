# DynamoDB Security and Monitoring

Checked: 2026-11-27. Resource-based policies, ABAC (2024), `AmazonDynamoDBFullAccess_v2` (2025), and the 2026 condition keys are dated in [versions/index.md](versions/index.md).

Contents: authentication and IAM; fine-grained access control; resource-based policies; encryption; network access; auditing with CloudTrail; CloudWatch metrics and alarms; Contributor Insights; common mistakes.

## Authentication and IAM

DynamoDB has no database users. Every request is signed with AWS credentials (SigV4) and authorized by IAM identity policies and resource-based policies (together with organization-level controls). There is no superuser inside the service to fall back on.

- Grant actions per table and index ARN (`arn:aws:dynamodb:<region>:<acct>:table/Orders` and `.../table/Orders/index/*`); streams have their own ARNs (`.../table/Orders/stream/<label>`).
- `AmazonDynamoDBFullAccess` was deprecated on 2025-04-25 in favor of `AmazonDynamoDBFullAccess_v2`. `AmazonDynamoDBReadOnlyAccess` includes `dynamodb:GetResourcePolicy` and ABAC status actions.
- ABAC: tag tables and indexes and match principal tags in conditions. Tags are not restored with a table and not supported on DynamoDB-native backups.
- PartiQL `SELECT` without partition key equality runs a full scan; the Developer Guide has an IAM example that allows PartiQL selects but denies full-table-scan statements (PartiQL IAM page): a `Deny` on `dynamodb:PartiQLSelect` with `"Condition": {"Bool": {"dynamodb:FullTableScan": ["true"]}}`, next to an `Allow` on `dynamodb:PartiQLSelect`.

## Fine-Grained Access Control

Condition keys:

| Key | Represents | Pitfall |
|---|---|---|
| `dynamodb:LeadingKeys` (interchangeable with `dynamodb:FirstPartitionKeyValues`) | Partition key values in the request | Requires `ForAllValues`; `ForAllValues` is true when the key is absent (for example `Scan`), so add `"Null": {"dynamodb:LeadingKeys": "false"}`. Use `StringEquals`/`StringLike` for String, `NumericEquals` for Number, `BinaryEquals` with base64 for Binary keys |
| `dynamodb:SecondPartitionKeyValues` to `FourthPartitionKeyValues` | Further partition key attributes (multi-attribute keys) | Plural even for single-item actions |
| `dynamodb:Attributes` | Top-level attributes named in the request | Evaluated on the request, not the response: a read without a projection returns every attribute |
| `dynamodb:Select` | `ALL_ATTRIBUTES`, `ALL_PROJECTED_ATTRIBUTES`, `SPECIFIC_ATTRIBUTES`, `COUNT` | Require `SPECIFIC_ATTRIBUTES` together with `Attributes` |
| `dynamodb:ReturnValues` | `ALL_OLD`, `UPDATED_OLD`, `ALL_NEW`, `UPDATED_NEW`, `NONE` | Restrict it, or writes can return restricted attributes |
| `dynamodb:ReturnConsumedCapacity` | `TOTAL`, `NONE` | |

For transactions, each item is authorized separately with its own action (`dynamodb:PutItem`, `UpdateItem`, `DeleteItem`, `GetItem`, `ConditionCheckItem`) and partition key. For batch operations, `LeadingKeys` contains every item's partition key.

Item-level policy fragment for per-user data:

```json
"Condition": {
  "ForAllValues:StringEquals": {"dynamodb:LeadingKeys": ["${www.amazon.com:user_id}"]},
  "Null": {"dynamodb:LeadingKeys": "false"}
}
```

FGAC is not supported for `SearchVectors`. Contributor Insights shows primary key values to anyone with CloudWatch access, regardless of FGAC; do not enable it on tables whose keys are sensitive.

## Resource-Based Policies

Attach policies to tables (covering their indexes) and streams; maximum 20 KB including whitespace.

```bash
aws dynamodb put-resource-policy --resource-arn arn:aws:dynamodb:us-east-1:123456789012:table/Orders \
  --policy file://orders-policy.json
aws dynamodb get-resource-policy --resource-arn arn:aws:dynamodb:us-east-1:123456789012:table/Orders
aws dynamodb delete-resource-policy --resource-arn arn:aws:dynamodb:us-east-1:123456789012:table/Orders
```

- Use for cross-account access, cross-account Lambda stream triggers, zero-ETL to Redshift, and multi-account global tables.
- Block Public Access is applied in the create and modify workflows; IAM Access Analyzer reports external access.
- Production safety: a policy containing only `Deny` statements can lock everyone out of future policy updates. Exempt an administering principal in the `Deny` before applying it.
- After a successful `PutResourcePolicy` on a table, further `PutResourcePolicy` and `DeleteResourcePolicy` calls on it are rejected for 15 seconds. Across tables: 25 `PutResourcePolicy` and 50 `DeleteResourcePolicy` requests per second; `GetResourcePolicy` 100 per second. A policy included in `CreateTable` or `PutResourcePolicy` counts as two extra control-plane requests per KB.
- Cross-account `Scan` of a secondary index is not supported through resource-based policies.
- DynamoDB local does not implement resource policies: 3.3.2 rejects `PutResourcePolicy` and `GetResourcePolicy` with `UnknownOperationException`.

## Encryption

At rest: all data is encrypted, including keys, indexes, streams, global tables, backups, and DAX. Choose the KMS key type per table; you can switch later:

| Key | Cost | Control |
|---|---|---|
| AWS owned key (default) | No additional charge | Owned and managed by DynamoDB |
| AWS managed key | KMS charges | Stored in your account, managed by AWS KMS |
| Customer managed key | KMS charges | You create, own, and manage it (key policy, rotation, deletion) |

```bash
aws dynamodb update-table --table-name Orders \
  --sse-specification Enabled=true,SSEType=KMS,KMSMasterKeyId=arn:aws:kms:us-east-1:123456789012:key/<key-id>
aws dynamodb describe-table --table-name Orders --query Table.SSEDescription
```

- Key switches per table: up to four in a 24-hour window counted from table creation, plus one more for each six-hour period without a change, so at most about eight per day. Switching to the AWS owned key is always allowed.
- A KMS alias is resolved to the key ID when you set it; repointing the alias later does not change the table's key.
- Production safety: if DynamoDB loses access to a customer managed key, the table is archived (backed up and the original deleted). Alarm on KMS key state and policy changes and keep key deletion behind a waiting period.
- Some sort key values that mark partition range boundaries are stored in plaintext in table metadata; use client-side encryption (AWS Database Encryption SDK) for sensitive sort keys.
- Contributor Insights publishes key values to CloudWatch encrypted with an AWS owned key, independent of the table's key.

In transit: service endpoints use HTTPS; DynamoDB local and the ExtendDB dev image serve plain HTTP.

## Network Access

- Gateway VPC endpoints and, since 2024-03-19, interface endpoints (PrivateLink) for DynamoDB; PrivateLink for Streams since 2025-03-26; DAX control plane PrivateLink since 2025-10-30.
- IPv6 and dual-stack endpoints (2025-10-03; China Regions 2026-05-30). Update IP-based IAM conditions to include IPv6 ranges when moving to dual-stack.
- Current SDKs use account-based endpoints for DynamoDB and, since 2026-11-17, for Streams (`<account-id>.streams-ddb.<region>.amazonaws.com`). The DynamoDB pattern is `https://<account-id>.ddb.<region>.amazonaws.com` (SDK overview page). Allow both in hostname-based egress filters, or set `ACCOUNT_ID_ENDPOINT_MODE` to keep Regional endpoints.

## Auditing with CloudTrail

- Control-plane operations (table, index, backup, PITR, resource policy, and DAX management calls) are logged by default as CloudTrail events; the CloudTrail page lists the control-plane actions. Data-plane calls need data events on `AWS::DynamoDB::Table` (which also captures stream calls) or `AWS::DynamoDB::Stream`.
- Item-level calls are data events and must be enabled explicitly: `GetItem`, `PutItem`, `UpdateItem`, `DeleteItem`, `BatchGetItem`, `BatchWriteItem`, `Query`, `Scan`, `TransactGetItems`, `TransactWriteItems`, `ExecuteStatement`, `BatchExecuteStatement`, `ExecuteTransaction`, `SearchVectors`, and for Streams `GetRecords` and `GetShardIterator`. Filter by resource type (for example `AWS::DynamoDB::Stream`) to control cost.
- `GetRecords` data events include DynamoDB internal calls such as global table replication; use the "Exclude AWS service-initiated events" template or an advanced selector with `userIdentity.arn` `NotStartsWith` `AWSServiceRoleFor` to avoid charges.
- TTL deletions are not logged in CloudTrail; capture them from the stream instead.
- Bulk put items logs `StartBulkPutItems` (management) and `BulkPutItems` (data) events.

## CloudWatch Metrics and Alarms

| Metric | Dimensions | Statistic to use | Alarm idea |
|---|---|---|---|
| `ConsumedReadCapacityUnits`, `ConsumedWriteCapacityUnits` | `TableName`, `GlobalSecondaryIndexName`; writes also `Source` | Sum per minute / 60 for per-second rate | Near provisioned capacity or on-demand maximum |
| `ProvisionedReadCapacityUnits`, `ProvisionedWriteCapacityUnits` | Table, GSI | Average | Compare with consumption |
| `ThrottledRequests` | `TableName`, `Operation` | Sum | Any sustained non-zero |
| `ReadThrottleEvents`, `WriteThrottleEvents` and the specific `*ProvisionedThroughputThrottleEvents`, `*KeyRangeThroughputThrottleEvents`, `*AccountLimitThrottleEvents`, `*MaxOnDemandThroughputThrottleEvents` | Table, GSI | Sum | Per cause; see [capacity-and-performance](capacity-and-performance.md) |
| `SuccessfulRequestLatency` | `TableName`, `Operation` | p99 or Average; SampleCount gives request count | Latency SLO |
| `SystemErrors` | `TableName` and `Operation` together | Sum | Published only on the pair; an alarm on `TableName` alone stays `INSUFFICIENT_DATA` |
| `UserErrors` | Account and Region | Sum | Sudden rise: validation or authorization bugs (excludes throttling and conditional failures) |
| `ConditionalCheckFailedRequests` | `TableName` | Sum | Contention or idempotency bugs |
| `TransactionConflict` | `TableName` | Sum | Hot items in transactions |
| `ReplicationLatency` | `TableName`, `ReceivingRegion` | Average, Maximum | MREC replica lag |
| `AgeOfOldestUnreplicatedRecord` | Table, Kinesis destination | Maximum | Kinesis feed lag |
| `TimeToLiveDeletedItemCount` | `TableName` | Sum | TTL working |
| `OnlineIndexPercentageProgress` | Table, GSI | Maximum | GSI build progress |
| `AccountProvisionedReadCapacityUtilization`, `MaxProvisionedTableReadCapacityUtilization` (and write variants) | Account | Maximum (5-minute data) | Approaching account quotas |

Request metrics are published per minute; account and capacity utilization metrics every five minutes. Read the per-second rate as Sum over one minute divided by 60; short spikes inside the minute are not visible.

```bash
aws cloudwatch get-metric-statistics --namespace AWS/DynamoDB \
  --metric-name ConsumedWriteCapacityUnits --dimensions Name=TableName,Value=Orders \
  --start-time 2026-11-27T00:00:00Z --end-time 2026-11-27T06:00:00Z \
  --period 60 --statistics Sum
```

## Contributor Insights

Two modes, set per table or GSI and per replica:

| Mode | Tracks | Cost basis | Use |
|---|---|---|---|
| `THROTTLED_KEYS` | Most throttled keys | Only throttled requests generate events | Leave on continuously |
| `ACCESSED_AND_THROTTLED_KEYS` (default) | Most accessed and most throttled keys | Every item read or written is an event (two with a sort key); a `Query` is one event | During investigations and load tests |

Both also bill a fixed monthly charge per rule. With a sort key, rules exist for partition keys and for partition plus sort key pairs. DAX cache hits are not shown. Restored tables need it re-enabled; each global table replica is configured separately. Commands are in [capacity-and-performance](capacity-and-performance.md).

## Common Mistakes

- Attribute-level FGAC without restricting `Select` and `ReturnValues`.
- `ForAllValues` on `LeadingKeys` without the `Null` guard, which lets `Scan` through.
- Deleting or disabling a customer managed key that a table uses.
- Expecting CloudTrail to show item reads without enabling data events.
- Alarming on `SystemErrors` without the `Operation` dimension.
- Enabling Contributor Insights on tables whose keys contain personal data.
