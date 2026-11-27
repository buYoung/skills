# Request Units, Throughput, and Indexing

Checked: 2026-11-27. Read when sizing or reducing RU/s, choosing manual, autoscale, or serverless, diagnosing high RU charges, or changing an indexing policy on Azure Cosmos DB (API for NoSQL unless noted). For 429 diagnosis see [operations.md](operations.md#diagnose-429-rate-limiting).

## Contents

- [How RUs are charged](#how-rus-are-charged)
- [Capacity modes](#capacity-modes)
- [Minimums and scaling speed](#minimums-and-scaling-speed)
- [Workload isolation features](#workload-isolation-features)
- [Indexing policy](#indexing-policy)
- [Composite indexes](#composite-indexes)
- [Changing an indexing policy safely](#changing-an-indexing-policy-safely)
- [Evidence: measuring RU cost and index use](#evidence-measuring-ru-cost-and-index-use)
- [Common mistakes](#common-mistakes)

## How RUs are charged

- A point read of a 1 KB item by `id` and partition key costs 1 RU. Point reads are always cheaper than a query returning the same item.
- Write cost rises with item size and with the number of indexed properties. By default every property is indexed.
- Strong and bounded staleness reads read two replicas and cost about twice the RUs of session, consistent prefix, or eventual reads. Write cost is the same at all levels.
- Query cost depends on result count, number and kind of predicates, UDFs, source data size, result size, and projections. The same query on the same data costs the same each time, so one measurement is representative.
- Cross-partition queries add about 2-3 RU per extra physical partition checked.
- RU/s provisioned on a container is provisioned in every region of the account: R RU/s with N regions is R x N billed.
- Failed requests (400, 412, 449, and others) are charged.
- Each response carries the charge in `x-ms-request-charge`; the SDKs expose it as the response's request charge.

## Capacity modes

| Mode | Behavior | Choose when | Limits and costs |
| --- | --- | --- | --- |
| Manual provisioned | Fixed RU/s in 100 RU/s steps, billed hourly | Steady, predictable load | 429 when a second's consumption exceeds the RU/s available on a partition |
| Autoscale | You set `Tmax`; the system scales `T` between `0.1*Tmax` and `Tmax` instantly; billed per hour for the highest `T` reached (at least `0.1*Tmax`) | Variable or unknown load; the autoscale page says it saves cost if you use full `Tmax` in 66% of hours or fewer | `Tmax` in 1,000 RU/s steps, minimum 1,000. Storage allowance `0.1*Tmax` GB; above that `Tmax` rises automatically |
| Serverless | No provisioned RU/s; billed for RUs consumed and storage | Intermittent traffic, average-to-peak under 10%, dev/test | One region only, can't add regions; no shared-throughput databases; each physical partition serves up to 5,000 RU/s |

Dynamic scaling (per-region and per-partition autoscale) is on by default for accounts created after 2024-09-25. Older accounts enable it under Features or programmatically (`enablePerRegionPerPartitionAutoscale` in the ARM schema). With it, each partition and region scales and bills separately instead of following the hottest partition. It doesn't apply to manual or serverless resources.

Serverless to provisioned (API for NoSQL): an in-place, irreversible change. Each container becomes manual throughput of `partitions x 5000` RU/s. No management operations run during the change, there is no SLA on its duration, and a restored deleted account comes back as provisioned.

```bash
# Read the mode and the current throughput
az cosmosdb show -g <rg> -n <account> --query "{capacityMode:capacityMode, limit:capacity.totalThroughputLimit}"
az cosmosdb sql container throughput show -g <rg> -a <account> -d <db> -n <container>
```

`capacity.totalThroughputLimit` caps the total RU/s that can be provisioned on the account (`-1` means no limit); use it as a cost guard.

Shared database throughput: the autoscale page says it is not recommended for most workloads, because one container's burst can throttle the others. Put throughput on containers. Throughput buckets don't work and priority-based execution is non-deterministic on shared-throughput containers.

## Minimums and scaling speed

Minimum RU/s (service-quotas page):

| Resource | Manual minimum | Autoscale minimum `Tmax` |
| --- | --- | --- |
| Container | max(400, storage GB x 1, highest RU/s ever / 100) | max(1000, storage GB x 10, highest `Tmax` ever / 10), rounded up to 1,000 |
| Shared database | max(400, storage GB x 1, highest ever / 100, 400 + max(containers - 25, 0) x 100) | max(1000, storage GB x 10, highest ever / 10, 1000 + max(containers - 25, 0) x 1000) |

Example: a container scaled once to 50,000 RU/s for a load can't go back below 500 RU/s manual (or 5,000 autoscale `Tmax`), even when nearly empty. Scale up for bulk loads knowing the floor it leaves.

Scaling speed:

- Changes inside the current physical-partition capacity apply immediately. The ceiling for an instant change is `number of PartitionKeyRangeIds x 10,000` RU/s.
- Above that, the scale-up is asynchronous (new physical partitions); the quotas page says minutes to hours, the 429 guide says up to 5-6 hours. Plan large increases ahead of events.
- Throughput updates are limited to 25 per 5 minutes per account (control-plane limit).
- Scaling up then down leaves many partitions with little RU/s each (throughput fragmentation). Partition merge (preview) reduces the physical partition count; see below.

## Workload isolation features

| Feature | What it does | Requirements and limits |
| --- | --- | --- |
| Burst capacity | Each physical partition accrues up to 5 minutes of idle RU/s and spends it at up to 3,000 RU/s | Provisioned accounts only; only partitions with under 3,000 RU/s benefit; not guaranteed; 15-20 minutes to take effect after enabling; NoSQL, Cassandra, Gremlin, MongoDB, Table |
| Priority-based execution | Under overload, throttles `Low` priority requests first | Best effort, no SLA. Not for serverless. Non-deterministic on shared-throughput containers. Weak for reads under strong and bounded staleness. Requests default to `High`; change the account default with `--default-priority-level`. Data Explorer runs at Low when enabled. SDKs: .NET 3.38.0, Java 4.45.0, JavaScript 4.0.0, Python 4.14.2 |
| Throughput buckets | Cap a workload at a percentage of container throughput without reserving it; up to 5 buckets per container; optional default bucket | Not for shared-throughput databases or serverless. SDKs: .NET 3.63.0, Java 4.83.0, JavaScript 4.8.0, Python 4.16.4. Data Explorer uses bucket 1 if configured. Monitor Total Requests and Total Request Units split by `ThroughputBucket` |
| Partition merge (preview) | Reduces physical partitions in place | While enabled, only .NET 3.27.0+, Java 4.42.0+, Spark connector 4.18.0+, JavaScript 4.3+ can connect; Go SDKs and some connectors are blocked. For Python the merge page conflicts (the caution blocks "any Python SDK", the SDK table lists 4.14.2+): assume Python clients are blocked, and test on a non-production account before enabling. Accounts that ever merged can't use the all versions and deletes change feed |
| Throughput redistribution across partitions (preview) | Gives a hot physical partition more of the RU/s | Only when the hot partition is predictable (429 guide) |

Priority example (Azure CLI 2.81.0 or later per the page):

```bash
az cosmosdb update -g <rg> -n <account> --enable-priority-based-execution true
az cosmosdb update -g <rg> -n <account> --default-priority-level low
```

```python
# Python SDK: mark a background read low priority
item = container.read_item("item2", "pk2", priority="Low")
```

Merge candidates (merge page): RU/s per physical partition at or below 5,000 and average storage per physical partition under 20 GB. Preview the result first:

```powershell
Invoke-AzCosmosDBSqlContainerMerge -ResourceGroupName <rg> -AccountName <acct> `
  -DatabaseName <db> -Name <container> -WhatIf
```

Before a merge, set RU/s close to the steady-state target so the service computes an efficient layout. Upgrade every client SDK before enabling the feature, because unsupported SDKs fail as soon as it is on.

## Indexing policy

Default policy for new NoSQL containers: consistent mode, every path included (`/*`), range indexes for strings and numbers, `_etag` excluded. The vNext emulator returned exactly this policy for a new container (`includedPaths: [{"path":"/*"}]`, `excludedPaths: [{"path":"/\"_etag\"/?"}]`).

| Setting | Values and rules |
| --- | --- |
| `indexingMode` | `consistent` (index updated synchronously) or `none` (no secondary index; key-value use or bulk load). `lazy` can't be chosen for new containers and can return incomplete results |
| Paths | Scalar ends in `/?`; arrays as `/[]`; subtree as `/*`. Root `/*` must be either included or excluded |
| Precedence | The more precise path wins: deeper beats shallower, `/?` beats `/*` |
| System properties | `id` and `_ts` are always indexed in consistent mode and don't appear in the policy |
| Partition key | With an exclude-root policy, include the partition key paths (each hierarchical level) explicitly |
| Spatial | Not created by default; add `Point`, `Polygon`, `MultiPolygon`, or `LineString` indexes for spatial functions |
| Tuple | `<prefix>/[]/{a, b}/?` indexes combinations inside array elements |
| Vector | `flat` (up to 505 dimensions, exact), `quantizedFlat` (up to 4,096), `diskANN` (up to 4,096, approximate). Vector policies and indexes are immutable after creation |
| Full text | `fullTextIndexes` paths; requires the Full Text and Hybrid Search feature and a matching container full-text policy |

Decision rules:

- Write-heavy container with known queries: exclude the root and include only filtered and sorted paths. Every unindexed property lowers write RUs.
- Evolving schema with ad hoc queries: keep the root included and exclude large or never-queried subtrees (blobs, nested payloads).
- Pure key-value access by `id` and partition key: `indexingMode: none`, unless TTL is needed (then consistent with `/*` excluded and no included paths).

Policy example, exclude-root with explicit includes:

```json
{
  "indexingMode": "consistent",
  "automatic": true,
  "includedPaths": [
    { "path": "/customerId/?" },
    { "path": "/status/?" },
    { "path": "/createdAt/?" }
  ],
  "excludedPaths": [ { "path": "/*" } ],
  "compositeIndexes": [
    [ { "path": "/status", "order": "ascending" }, { "path": "/createdAt", "order": "descending" } ]
  ]
}
```

Limits: 1,500 included and 1,500 excluded paths per container; composite indexes up to 8 properties and 100 composite paths per container (service-quotas page).

## Composite indexes

- Required for `ORDER BY` on two or more properties. The path order must match the `ORDER BY` order, and the directions must match exactly or be fully reversed.
- For filters on several properties: equality properties first, then at most one range property (`>`, `<`, `>=`, `<=`, `!=`) last. A query with two range filters needs two composite indexes.
- For a filter plus `ORDER BY` on another property: add the filter properties to the front of the `ORDER BY` so the composite index can serve it.
- For `SUM` and `AVG` with filters: equality properties first, the aggregated property last.

| Composite index | Query | Served |
| --- | --- | --- |
| `(name ASC, age ASC)` | `WHERE c.name = "John" AND c.age > 18` | Yes |
| `(name ASC, age ASC)` | `ORDER BY c.age ASC, c.name ASC` | No |
| `(name ASC, age ASC)` | `ORDER BY c.name DESC, c.age DESC` | Yes |
| `(name ASC, timestamp ASC)` | `WHERE c.name = "John" ORDER BY c.timestamp ASC` | No; rewrite as `ORDER BY c.name, c.timestamp` |

## Changing an indexing policy safely

- An update triggers an online, in-place index transformation. Reads and writes stay available. The transformation consumes the container's RUs at lower priority than user requests, so it runs slower on a busy container.
- New indexes are used only after the transformation completes. Removed indexes stop being used immediately and queries fall back to scans.
- Replacing an index: add the new one, wait for completion, then remove the old one in a separate change.
- Group several removals into one policy change; across several changes, query results can be inconsistent until all finish.
- Track progress in the portal or through the SDK's `IndexTransformationProgress` (how-to-manage-indexing-policy page). After a restore, check it too, because indexes can still be rebuilding.

Rollback: re-apply the previous policy JSON. Keep it in source control; `az cosmosdb sql container show ... --query resource.indexingPolicy` prints the current one.

## Evidence: measuring RU cost and index use

```bash
# REST query, read the charge header (emulator form; on Azure add auth headers)
curl -si -X POST "$EP/dbs/app/colls/orders/docs" \
  -H 'Content-Type: application/query+json' -H 'x-ms-documentdb-isquery: true' \
  -H 'x-ms-documentdb-partitionkey: ["c1"]' \
  -d '{"query":"SELECT * FROM c WHERE c.status = @s","parameters":[{"name":"@s","value":"paid"}]}' \
  | grep -i -E 'x-ms-request-charge|x-ms-continuation|x-ms-item-count'
```

Index metrics (off by default; enable only while troubleshooting):

| SDK | Option |
| --- | --- |
| .NET v3 (3.21.0+) | `QueryRequestOptions { PopulateIndexMetrics = true }`, read `response.IndexMetrics` |
| Java v4 (4.19.0+) | `CosmosQueryRequestOptions.setIndexMetricsEnabled(true)`, output in diagnostics |
| JavaScript | `{ populateIndexMetrics: true }`, read `indexMetrics` |
| Python (4.6.0+) | `populate_index_metrics=True`; response header `x-ms-cosmos-index-utilization` (only if items return) |
| Go | `PopulateIndexMetrics: true`; `page.IndexMetrics` is base64 |

Reading the output: Utilized Single and Composite Indexes are in use; Potential Single and Composite Indexes are suggestions with an Index Impact Score of high or low. Add high-impact suggestions, then re-measure `x-ms-request-charge`.

For costly queries across the workload, use the `QueryRuntimeStatistics` diagnostic log category; see [operations.md](operations.md#diagnostic-logs).

The vNext emulator does not implement request units: every response observed carried `x-ms-request-charge: 1`. Measure RU cost only against an Azure account.

## Common mistakes

- Comparing RU costs measured on the emulator.
- Fixing write RU cost by adding RU/s instead of excluding unused paths.
- Removing an index before its replacement finishes building.
- Running a two-property `ORDER BY` without a composite index; the service requires one (the API for MongoDB returns error 2 `BadValue` in the same case). The vNext emulator doesn't require it, so a local test won't catch it ([emulator.md](emulator.md)).
- Using shared database throughput for unrelated containers.
- Leaving autoscale `Tmax` high after a migration; it raises the minimum and the billed floor (`0.1*Tmax`).
- Scaling far above the instant ceiling minutes before a launch.
