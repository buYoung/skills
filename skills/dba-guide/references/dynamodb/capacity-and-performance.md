# DynamoDB Capacity and Performance

Checked: 2026-11-27. Dated changes (warm throughput 2024, on-demand maximum 2024, four mode switches per day 2025, throttling reasons 2025) are in [versions/index.md](versions/index.md).

Contents: capacity units; choosing a capacity mode; quotas; on-demand scaling and warm throughput; provisioned mode and auto scaling; burst and adaptive capacity; throttling diagnosis; latency; DAX; common mistakes.

## Capacity Units

| Operation | Unit cost |
|---|---|
| Strongly consistent read, up to 4 KB | 1 read unit |
| Eventually consistent read, up to 4 KB | 0.5 read unit |
| Transactional read, up to 4 KB | 2 read units |
| Write, up to 1 KB | 1 write unit |
| Transactional write, up to 1 KB | 2 write units, also when the transaction is canceled |
| Conditional write that fails | Write units for the item size, still charged |
| GSI maintenance | Write units on each affected GSI (see [data-modeling](data-modeling.md)) |

Sizes are binary (1 KB = 1024 bytes). `GetItem` and `BatchGetItem` round each item up to 4 KB; `Query` rounds the total result; `Scan` charges for items evaluated. `PutItem` and `UpdateItem` charge the larger of the old and new item. Measure instead of estimating: add `--return-consumed-capacity INDEXES` to a request and read `ConsumedCapacity.Table` and `ConsumedCapacity.GlobalSecondaryIndexes`.

## Choosing a Capacity Mode

| Factor | On-demand (`PAY_PER_REQUEST`) | Provisioned (`PROVISIONED`) |
|---|---|---|
| Default | Default and recommended per the on-demand page (console, NoSQL Workbench) | CloudFormation default when `BillingMode` is omitted |
| Billing | Per request unit | Per provisioned unit-hour, used or not; reserved capacity possible (max 1,000,000 units per account, adjustable) |
| Scaling | Immediate up to double the previous peak; new tables sustain 4,000 writes and 12,000 reads per second | Auto scaling reacts to utilization; manual changes take effect after `UpdateTable` completes |
| Ceiling | Table-level quota (40,000 read and 40,000 write request units by default, adjustable), plus optional per-table maximum | Provisioned value; account quota 80,000 RCU and 80,000 WCU by default |
| Throttle reason when out of capacity | `AccountLimitExceeded`, `MaxOnDemandThroughputExceeded`, `KeyRangeThroughputExceeded` | `ProvisionedThroughputExceeded`, `KeyRangeThroughputExceeded` |
| Fits | Unknown, spiky, or new workloads; low average utilization | Steady, predictable traffic with high utilization |

Switching: provisioned to on-demand up to four times per rolling 24 hours; on-demand to provisioned at any time. The switch takes several minutes and the table serves the previous provisioned throughput meanwhile. A table switched to on-demand for the first time keeps at least the throughput it was provisioned for (or 4,000 writes and 12,000 reads per second if it was smaller). Console switches to on-demand delete auto scaling settings; CLI and SDK switches preserve them for a later return to provisioned. When switching back to provisioned, size from `ConsumedReadCapacityUnits` and `ConsumedWriteCapacityUnits` history (for a global table, the maximum across replicas).

## Quotas

| Quota | Default | Adjustable |
|---|---|---|
| Per table (on-demand or provisioned), read / write | 40,000 / 40,000 units per second | Yes |
| Per account, provisioned tables and GSIs | 80,000 RCU / 80,000 WCU | Yes |
| Per partition | 3,000 read units / 1,000 write units per second | No |
| Provisioned decreases | 4 at the start of the UTC day, plus 1 per hour, at most 4 available; up to 27 per day per table and per GSI | Yes (default quota) |
| Tables per Region | 2,500 (up to 10,000 through the account team) | Yes |
| Concurrent control-plane operations | 500 tables in `CREATING`, `UPDATING`, `DELETING` | — |
| `DescribeLimits` | About once per minute | — |
| Write capacity with Streams enabled (provisioned) | 40,000 WCU per table | — |

Check quotas with `aws dynamodb describe-limits` (DynamoDB local returns the defaults 80,000 and 40,000) and the Service Quotas console. Raise the table-level quota in every Region before adding a global table replica; mismatched limits make replica creation fail.

## On-Demand Scaling and Warm Throughput

On-demand serves up to double the previous peak instantly. Exceeding double the previous peak within 30 minutes can throttle. For a planned event, either grow traffic over at least 30 minutes or pre-warm.

Warm throughput is the read and write rate a table or GSI can serve immediately. Read it:

```bash
aws dynamodb describe-table --table-name Orders \
  --query 'Table.{Table:WarmThroughput,Indexes:GlobalSecondaryIndexes[*].{Name:IndexName,Warm:WarmThroughput}}'
```

Pre-warm (charged; cannot be decreased afterwards; asynchronous until `Status` is `ACTIVE`):

```bash
aws dynamodb update-table --table-name Orders \
  --warm-throughput ReadUnitsPerSecond=60000,WriteUnitsPerSecond=20000
```

Values above the table-level quota require a quota increase first. For 2019.11.21 global tables the setting applies to all replicas.

Maximum on-demand throughput caps spend or protects downstream systems:

```bash
aws dynamodb update-table --table-name Orders \
  --on-demand-throughput MaxReadRequestUnits=5000,MaxWriteRequestUnits=2000
```

Requests above the cap fail with `ThrottlingException` and reason `TableReadMaxOnDemandThroughputExceeded` or `TableWriteMaxOnDemandThroughputExceeded`. The cap is best effort; burst capacity can briefly exceed it. Set `-1` to remove it. The minimum is 1, and the value must be below the table-level quota. CloudWatch shows the configured caps as `OnDemandMaxReadRequestUnits` and `OnDemandMaxWriteRequestUnits`. On a global table the AWS pages disagree: "How global tables work" lists on-demand maximum read throughput as overridable per replica (write is synchronized), while the maximum-throughput page says settings on one replica are applied to all replicas. After setting a cap, run `describe-table` in each replica Region and read `OnDemandThroughput`.

## Provisioned Mode and Auto Scaling

- Provision GSI write capacity at least equal to the table's; a starved GSI throttles table writes.
- Auto scaling targets a utilization (console default 70%, minimum 5 units when switching from on-demand in the console). It responds to sustained load, not to second-level spikes; burst capacity covers short spikes.
- Decreases are rate-limited (see quotas). Increases can be made as often as needed but not "very rapidly"; large jumps can take time.
- During a legacy global table upgrade, auto scaling does not adjust capacity; switch to on-demand first ([global-tables-2019.11.21](versions/global-tables-2019.11.21.md)).

## Burst and Adaptive Capacity

- Burst capacity: up to 300 seconds of unused read and write capacity is retained and can absorb short spikes. DynamoDB may also consume it for background work without notice. Do not size for it.
- Adaptive capacity: on by default, no cost. It raises capacity for partitions receiving more traffic, as long as the table's total and the per-partition maximum (3,000 read units, 1,000 write units per second) are not exceeded. It isolates frequently accessed items onto their own partitions, and can split an item collection by sort key, except when the sort key increases or decreases monotonically with the traffic or when the table has an LSI.
- A single item can never exceed the per-partition maximum. For a single hot key, cache it (DAX or application cache), shard writes, or change the model.

## Throttling Diagnosis

Throttled requests return `ProvisionedThroughputExceededException`, `ThrottlingException`, or `RequestLimitExceeded` (HTTP 400). Exceptions carry `ThrottlingReasons`, each with a `reason` and a `resource` ARN (table or `.../index/<name>`).

| Reason suffix | Meaning | Metric | Fix |
|---|---|---|---|
| `ProvisionedThroughputExceeded` | Provisioned table or GSI consumption above its setting | `Read/WriteProvisionedThroughputThrottleEvents` | Raise capacity or auto scaling maximum; on-demand |
| `KeyRangeThroughputExceeded` | One partition above 3,000 read or 1,000 write units per second | `Read/WriteKeyRangeThroughputThrottleEvents` | Find the key with Contributor Insights; shard, cache, or rate-limit sequential scans and ordered bulk writes |
| `AccountLimitExceeded` | On-demand table or GSI above the table-level quota | `Read/WriteAccountLimitThrottleEvents` | Request a quota increase |
| `MaxOnDemandThroughputExceeded` | Above the configured on-demand maximum | `Read/WriteMaxOnDemandThroughputThrottleEvents` | Raise or remove (`-1`) the maximum |

The prefix is `TableRead`, `TableWrite`, `IndexRead`, or `IndexWrite`. Example: `IndexWriteProvisionedThroughputExceeded` on `.../index/OrderDateIndex` means the GSI's write capacity is the bottleneck, even though the application wrote to the table.

Procedure:

1. Log the full exception including `ThrottlingReasons`; SDKs retry throttles automatically, so throttling can show up first as latency.
2. Graph the matching metric for the ARN. Aggregate metrics: `ReadThrottleEvents` and `WriteThrottleEvents` count events (a 10-item `BatchGetItem` counts 10; a table write plus GSI writes count separately); `ThrottledRequests` counts requests (a batch counts only if every item was throttled).
3. For key-range reasons, enable Contributor Insights on the throttled table or GSI. Throttled-keys mode only processes throttled events and is cheap enough to leave on:

   ```bash
   aws dynamodb update-contributor-insights --table-name Orders \
     --contributor-insights-action=ENABLE --contributor-insights-mode=THROTTLED_KEYS
   aws dynamodb describe-contributor-insights --table-name Orders
   ```

   Accessed-and-throttled mode (`ACCESSED_AND_THROTTLED_KEYS`, the default) shows the most accessed keys too, at a per-event cost. Contributor Insights does not measure write throttling caused by a GSI's insufficient write capacity; use the GSI's most-accessed graph for that.
4. If no key dominates, look for unbounded sequential access: a single `Scan` or a bulk write in key order. Use parallel scan segments and rate-limit to stay under 3,000 read or 1,000 write units per key range.
5. Apply the fix and confirm the specific metric drops to zero.

`BatchWriteItem` and `BatchGetItem` return throttled items in `UnprocessedItems` or `UnprocessedKeys` instead of failing; resend them with exponential backoff. A batch fails with an exception only when nothing could be processed.

## Latency

- `SuccessfulRequestLatency` (per `TableName` and `Operation`) measures time inside DynamoDB, excluding network and client time. If the client sees high latency and this metric is flat, look at SDK retries, connection pools, timeouts, DNS, or cross-Region calls.
- Strongly consistent reads, transactions, and MRSC writes cost more latency than eventually consistent reads and MREC writes.
- Configure SDK timeouts and retry strategy explicitly (the Developer Guide has per-language guidance for Java 2.x, Python, and JavaScript, updated 2026-09-02).

## DAX

DAX is an in-memory cache cluster in front of DynamoDB (one primary node and up to ten read replicas; at most 500 tables per cluster). It serves eventually consistent reads; strongly consistent reads and `TransactGetItems` pass through uncached. `TransactWriteItems` through DAX triggers background `TransactGetItems` that consume extra read units. Writes to global table replicas in other Regions bypass DAX, so a DAX cache on a replica refreshes only when its TTL expires. Changing a DAX parameter group on a running cluster applies only to items written afterwards.

## Common Mistakes

- Raising table capacity to fix `KeyRangeThroughputExceeded`; the limit is per partition.
- Forgetting GSI write capacity in provisioned mode.
- Load-testing an on-demand table from zero to ten times the previous peak at once.
- Alarming only on `ThrottledRequests`, which misses partially throttled batches.
- Treating the on-demand maximum as a hard ceiling for billing guarantees.
- Increasing warm throughput "to be safe" without accepting that it cannot be decreased.
