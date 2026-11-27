# NoSQL Modeling and Partitioning

Checked: 2026-11-27. Read when designing containers, choosing or changing a partition key, sizing items, or deciding where a transaction boundary falls in Azure Cosmos DB for NoSQL. The partition mechanics also apply to the other RU-based APIs; hierarchical partition keys and global secondary indexes are NoSQL only (see [apis.md](apis.md)).

## Contents

- [Mechanism that drives every decision](#mechanism-that-drives-every-decision)
- [Hard limits](#hard-limits)
- [Choosing a partition key](#choosing-a-partition-key)
- [Hierarchical partition keys](#hierarchical-partition-keys)
- [Synthetic keys and global secondary indexes](#synthetic-keys-and-global-secondary-indexes)
- [Transactions and concurrency](#transactions-and-concurrency)
- [TTL and unique keys](#ttl-and-unique-keys)
- [Changing a partition key](#changing-a-partition-key)
- [Evidence commands](#evidence-commands)
- [Common mistakes](#common-mistakes)

## Mechanism that drives every decision

- Every item has a partition key value and an `id` unique within that value. Items with the same partition key value form a logical partition.
- Cosmos DB hashes the partition key value and maps logical partitions onto physical partitions. You don't control physical partitions. One logical partition always lives on one physical partition.
- A physical partition serves up to 10,000 RU/s and stores up to 50 GB. Provisioned throughput is divided evenly across physical partitions, so a hot key value can be throttled while the container's total RU/s looks unused.
- New physical partitions appear by splitting when throughput or storage grows. Splits don't affect availability. Each physical partition is a replica set of at least four replicas.
- A logical partition is the scope of transactions (stored procedures, triggers, transactional batch).
- A query that doesn't filter on the partition key fans out. The partitioning page gives the overhead as about 2-3 RU per extra physical partition checked. With five or fewer physical partitions the key choice matters little for query cost.

A container needs more than a few physical partitions, and so a query-aligned key, when it has more than 30,000 RU/s provisioned or more than 100 GB stored (partitioning page).

## Hard limits

From the service-quotas page unless noted:

| Limit | Value |
| --- | --- |
| Item size | 2 MB (UTF-8 length of JSON). API for MongoDB: 16 MB after enabling the feature |
| Logical partition storage | 20 GB (temporary increase by support ticket; SLA not honored while raised) |
| Logical and physical partition throughput | 10,000 RU/s |
| Physical partition storage | 50 GB (partitioning page) |
| Partition key value length | 2,048 bytes with large partition keys enabled; 101 bytes otherwise |
| `id` length | 1,023 bytes; `/` and `\` not allowed; use alphanumeric ASCII for interoperability |
| Nesting depth | 128 levels |
| Request size / response page size | 2 MB / 4 MB |
| Single operation execution time | 5 seconds (queries return a continuation token and continue) |
| Transactional batch | 100 operations, one logical partition |
| Databases plus containers per account | 500 (can't be raised) |
| Containers per shared-throughput database | 25 |
| Unique keys per container / paths per unique key | 10 / 16 |
| Hierarchical partition key depth | 3 levels |

Number values beyond IEEE 754 binary64 lose precision. Store large integers (for example 64-bit IDs) as strings, especially in the partition key, which you can't change later.

The vNext emulator enforces the 2 MB item and 100-operation batch limits but not the `id` character rule; test `id` validation against an Azure account ([emulator.md](emulator.md#observed-behavior-release-en20261123)).

## Choosing a partition key

Rules for every container:

1. Pick a property whose value never changes for an item. Partition key values are immutable: a replace must carry the same key; moving an item means create-new plus delete-old, and those two writes are not atomic across logical partitions. On the vNext emulator a replace that sends the old key in `x-ms-documentdb-partitionkey` and a new value in the body returns 400 (substatus 1001, "PartitionKey extracted from document doesn't match the one specified in the header."), as does a create with the same mismatch.
2. Pick high cardinality: many more distinct values than physical partitions.
3. Spread both RU consumption and storage evenly. Check that no single value can reach 20 GB or 10,000 RU/s.
4. For read-heavy containers that will grow past a few physical partitions, pick the property that appears as an equality filter in most queries, so queries route to one partition.
5. For write-heavy containers of any size, or small read-mostly containers queried by id, `/id` is a good key.

| Strategy | Use when | Cost |
| --- | --- | --- |
| Single property (`/customerId`) | High cardinality and matches the main filter | Hot keys if a few values dominate; 20 GB ceiling per value |
| `/id` | Point reads and writes dominate; few other filters | Every non-id filter is cross-partition; no multi-item transactions |
| Synthetic (`customerId-yyyymm`) | No single property is both high-cardinality and query-aligned | Application must build the value; queries on one component fan out |
| Hierarchical (`/tenantId`, `/userId`, `/id`) | A first-level value can exceed 20 GB; multitenant isolation | First level must still have high cardinality; NoSQL only; fixed at creation |
| Global secondary index | Several independent query patterns | Extra storage and RUs; eventually consistent copy |

Anti-patterns named by the partitioning and 429 troubleshooting pages:

- Low-cardinality fields (`status`, `type`, `country`) except for small data with low traffic per value.
- Date as the key for write-heavy telemetry: each day's writes land on one logical partition.
- A random GUID the queries never filter on: writes spread well, every read fans out.
- `/tenantId` alone when one tenant is far larger than the rest.

## Hierarchical partition keys

Up to three key paths, set at container creation (`kind: MultiHash`, `version: 2`). Queries that give the first level, or the first and second, are routed to the subset of physical partitions holding that prefix instead of fanning out. A single first-level value can exceed 20 GB and 10,000 RU/s because its data can span physical partitions.

Container definition (ARM/Bicep form from the hierarchical-partition-keys page):

```json
"partitionKey": {
  "paths": ["/TenantId", "/UserId", "/SessionId"],
  "kind": "MultiHash",
  "version": 2
}
```

Python SDK form:

```python
container = database.create_container(
    id="events",
    partition_key=PartitionKey(path=["/tenantId", "/userId", "/sessionId"], kind="MultiHash"),
)
```

Decision rules:

- The first level must have high cardinality. With few first-level values, writes for each value go to one physical partition until it reaches 50 GB and splits; the page says splits can take 4-6 hours.
- Add `id` (or another GUID) as the last level when a first-level or first-plus-second combination might exceed 20 GB.
- If the first level has low cardinality and you are already at 20 GB, the page recommends a synthetic key instead.
- With an exclude-root indexing policy, include each key level; the indexing page warns that unindexed partition key paths force full scans for queries that filter on them.

Requirements and limits:

| Item | Value |
| --- | --- |
| SDKs (minimum listed) | .NET v3 3.33.0, Java v4 4.42.0, JavaScript v4 4.0.0, Python 4.6.0; Go supports `PartitionKeyKindMultiHash` |
| APIs | NoSQL only |
| Existing containers | Can't convert; create a new container and copy |
| Users and permissions | Permissions must target the full key path, not a prefix |
| Connectors | Limitations exist (for example Azure Data Factory) |

The same page lists Python as supported in its version table and as unsupported in its limitations list. Treat Python 4.6.0+ as supported and test it.

## Synthetic keys and global secondary indexes

A synthetic key concatenates properties into one string at write time. It spreads writes but turns queries on one component into fan-outs.

A global secondary index (GSI) is a read-only container kept in sync from a source container through a managed change feed, with its own partition key, indexing policy, and throughput:

- Requires continuous backup on the account, then the global secondary index feature enabled.
- GSI containers must use autoscale throughput.
- Definition query: `SELECT` of properties (flattened to top level) or `SELECT *`; no `WHERE`, `JOIN`, `DISTINCT`, `GROUP BY`, `ORDER BY`, aliasing, or functions. The source container and definition can't be changed after creation.
- The source `id` appears as `_id` in the GSI.
- Always eventually consistent with the source, whatever the account consistency.
- Replace and delete on the source cost 50-100% more RUs; creates aren't affected.
- Lag metric: Global Secondary Index Propagation Latency in Seconds, split by `GlobalSecondaryIndexName` and `GlobalSecondaryIndexStatus` (`Active`, `InitialBuildAfterCreate`).
- Setup commands in the how-to use the preview management API version `2022-11-15-preview`, while the concept page carries no preview label. Check the account's Features pane in the portal for a preview tag before relying on it in production.

Use a GSI when changing the source partition key would be disruptive, or when one workload (search, vector, analytics) should be isolated from transactional traffic.

## Transactions and concurrency

- Multi-item ACID transactions exist only inside one logical partition, through transactional batch (up to 100 operations) or JavaScript stored procedures and triggers, with snapshot isolation inside the partition.
- Only one transactional operation runs at a time per logical partition key. Concurrent ones fail with 429 and the error `TXN_WAIT_FOR_TRANSACTION_END`. Shorten transactions, retry with backoff, or spread writes across more keys.
- Optimistic concurrency: send the item's `_etag` in `If-Match` on replace or delete. A mismatch returns 412 `PreconditionFailed` ("E-tag mismatch detected" on the vNext emulator).
- Failed requests are charged too, including 412 and 449; a rise in those codes can explain throttling.
- Stored procedures are for multi-item writes in one partition, not for bulk reads; the 429 guide says to do reads and queries client-side.

```bash
# REST: conditional replace (Authorization, x-ms-date, x-ms-version omitted)
curl -X PUT "$EP/dbs/app/colls/orders/docs/o1" \
  -H 'x-ms-documentdb-partitionkey: ["c1"]' \
  -H 'If-Match: "<etag from the last read>"' \
  -H 'Content-Type: application/json' \
  -d '{"id":"o1","customerId":"c1","status":"paid","total":2}'
```

## TTL and unique keys

- TTL requires indexing: you can't enable TTL when `indexingMode` is `none`, and can't set `none` while TTL is on. For a key-value container that still needs TTL, keep `consistent` mode with no included paths and `/*` excluded. The vNext emulator doesn't enforce this ([emulator.md](emulator.md#observed-behavior-release-en20261123)).
- Maximum TTL value: 2,147,483,647 seconds.
- Deletes caused by TTL appear only in the all versions and deletes change feed; in latest version mode the item just disappears.
- Unique key constraints: up to 10 per container and 16 paths each. A unique key is scoped to a logical partition, and it can be defined only when the container is created; the policy can't be changed afterwards. Sparse unique keys aren't supported: a missing value counts as null, so only one item can lack the field (unique-keys page).

## Changing a partition key

The partition key can't be changed in place. Options, lowest risk first:

1. Add a global secondary index with the new key and move read traffic to it (NoSQL, continuous backup required).
2. Create a new container and copy with container copy jobs (offline) or a change-feed-based live migration; then switch the application and validate.
3. For hierarchical keys, the same: new container, copy, switch, validate prefix routing.

Rehearsal: copy into a test container first and compare item counts and the RU charge of the top queries. Rollback: keep the old container and the change-feed processor until the new one has served production for an agreed period.

## Evidence commands

Partition key ranges (one per physical partition) and the container definition, over REST. On the vNext emulator authentication isn't enforced; on Azure add `Authorization`, `x-ms-date`, and `x-ms-version`.

```bash
curl -s "$EP/dbs/app/colls/orders"          # partitionKey, indexingPolicy, conflictResolutionPolicy
curl -s "$EP/dbs/app/colls/orders/pkranges"  # PartitionKeyRanges[].id, minInclusive, maxExclusive
```

Azure Monitor and logs:

- Metric Normalized RU Consumption split by `PartitionKeyRangeId`: one range consistently near 100% while others are low indicates a hot partition.
- `CDBPartitionKeyRUConsumption` (diagnostic logs, resource-specific mode) to find the hot logical key; query in [operations.md](operations.md#diagnose-429-rate-limiting).
- Alert on logical partition storage approaching 20 GB (how-to-alert-on-logical-partition-key-storage-size page).

## Common mistakes

- Choosing a key by cardinality alone without checking the top queries' filters.
- Using a property that changes (status, owner) as the key.
- Expecting a transaction across two partition key values.
- Treating more RU/s as the fix for a hot partition. RU/s is split evenly across physical partitions, so the hot one gains only its share; the 429 guide calls this a short-term measure only.
- Asking support for a raised 20 GB limit as a permanent fix. It is temporary and the SLA doesn't apply while raised.
- Designing container-per-tenant or database-per-tenant multitenancy; the serverless page names both as patterns to avoid (500 databases-plus-containers per account, 25 containers per shared database). Use partition-key-per-tenant or account-per-tenant.
