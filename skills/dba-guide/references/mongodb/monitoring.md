# MongoDB Monitoring and Diagnosis

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)). To act on the findings, see [indexes-and-query-plans](indexes-and-query-plans.md) and [configuration](configuration.md).

## Contents

- [Continuous metrics](#continuous-metrics)
- [Slow query log](#slow-query-log)
- [Database profiler](#database-profiler)
- [$queryStats](#querystats)
- [$currentOp and killing operations](#currentop-and-killing-operations)
- [Latency triage](#latency-triage)
- [Version differences in diagnostic output](#version-differences-in-diagnostic-output)

## Continuous metrics

`db.serverStatus()` is the source for most dashboards. FTDC writes the same data to `diagnostic.data` under `dbPath`. Its directory size cap (`diagnosticDataCollectionDirectorySizeMB`) went from 200 MB to 500 MB in 8.3.

| Concern | Where | Read it as |
| --- | --- | --- |
| Throughput | `opcounters`, `opWorkingTime` (8.0+) | baseline per hour of week |
| Ticket queueing | `queues.execution.read/write` (8.0+; 7.0: `wiredTiger.concurrentTransactions`) | sustained `queueLength` or rising `totalTimeQueuedMicros` = overload; `available: 0` alone is not |
| Cache | `wiredTiger.cache` | bytes in cache near max, dirty share high, eviction by app threads |
| Connections | `connections` | `current` vs `available`, `rejected` > 0, 8.2+ `queuedForEstablishment` |
| Replication | `rs.status()`, `metrics.repl.*`, 8.3+ `metrics.repl.network.oplogFetcherLagSeconds` | lag vs oplog window |
| Write conflicts | 9.0 `metrics.operation.writeConflictRetryLimitHit` | rising = hot documents |
| Query engine | `metrics.query.*`, 8.3+ `metrics.query.cbr.*`, 9.0 `metrics.query.operationsFailedDueToMemoryLimit` | memory failures, plan selection behavior |
| Plan cache | `planCache.*` (`replanned` counters, 8.0+) | frequent replanning = unstable plans |
| TTL | 8.3+ `metrics.ttl.*` | deletes keeping up |
| Change streams | 9.0 `metrics.changeStreams.cursor.*` | open cursors, lifespan |

You can request only the sections you need. The 8.3 release notes list this as new in 8.3, but the 7.0.48 and 8.0.38 images also honor it:

```javascript
db.adminCommand({ serverStatus: 1, none: 1, queues: 1, connections: 1 })
// all four images: host, version, process, pid, uptime, uptimeMillis, uptimeEstimate, localTime, connections, queues, ok (8.0 also service)
```

`db.collection.stats()` is a shell helper. For sizes and storage, prefer `$collStats`:

```javascript
db.orders.aggregate([{ $collStats: { storageStats: {} } }])
```

On the images this returned a `wiredTiger` section, with `count` 50000 and `size` 6373331 for the test collection.

## Slow query log

- An operation is logged as slow when it exceeds `slowms` (default 100 ms). From 8.0 the threshold is measured against `workingMillis`, which excludes lock waits and flow control; `durationMillis` is also reported.
- `slowOpSampleRate` (default 1.0) samples the slow operations that get logged.
- From 8.3, `slowinprogms` (default 5000) logs a still-running operation once when it crosses the threshold. The entry is shorter than a normal slow-op entry.
- Set at runtime, without enabling the profiler:

  ```javascript
  db.setProfilingLevel(0, { slowms: 50, sampleRate: 1.0 })
  db.getProfilingStatus()   // 9.0 image: { was: 0, slowms: 100, slowinprogms: 5000, sampleRate: 1 }
  ```
- This does not persist across restarts. Set `operationProfiling.slowOpThresholdMs` in the config file for that.
- Slow-op log entries are JSON with `"c":"COMMAND"`, `"id":51803`, and `"msg":"Slow query"` on all four images. Useful attributes:
  - `ns`, `command`, `planSummary`, `keysExamined`, `docsExamined`, `nreturned`;
  - `workingMillis` (8.0+) next to `durationMillis`;
  - `queryShapeHash` (8.0+). For a plain `find` it appeared in the slow-query line on the 8.3 and 9.0 images but not on 8.0.38;
  - `queues.execution.totalTimeQueuedMicros` (8.0+);
  - `queryFramework` (7.0+);
  - `peakTrackedMemBytes` (8.3+);
  - `originalQueryShapeHash` for `mongos`-originated work (8.3+).
- Read recent log lines without shell access to the host: `db.adminCommand({ getLog: "global" }).log`. This holds the recent in-memory log only. A cursor-returning query can log the slow-query line on its final `getMore`, with the original `find` under `originatingCommand`.

## Database profiler

- The profiler writes to `<db>.system.profile` (a capped collection) in each database where it is enabled.
  - Level 1: operations over `slowms`, or matching `filter`.
  - Level 2: everything.
- The manual warns that profiling degrades performance and can expose query data. Prefer the slow log and `$queryStats`. Enable the profiler briefly, on one database, with a filter.

  ```javascript
  db.setProfilingLevel(1, { filter: { workingMillis: { $gt: 200 }, ns: "shop.orders" } })   // workingMillis filter: 8.0+; 7.0 errors: No such field (or fields) available for profile filter: workingMillis
  db.system.profile.find().sort({ ts: -1 }).limit(5)
  db.setProfilingLevel(0, { filter: "unset" })
  ```
- When a filter is set, `slowms` and `sampleRate` are ignored, for both the profiler and the slow log.
- On `mongos` only level 0 is possible; the settings affect only the diagnostic log.
- 8.3 adds the throttles `internalQueryGlobalProfilingLockDeadlineMs` and `internalProfilingMaxAbandonedWritesPerSecondPerDb`, plus `profiler.totalAbandonedWrites` in serverStatus.
- 8.3.8 raised the privilege required to change `slowms` and `sampleRate` through `profile` (SERVER-130198). Monitoring users may need more rights after patching.

## $queryStats

`$queryStats` aggregates execution statistics per query shape. Run it on `admin` as the first stage. It requires the `queryStatsRead` privilege (`clusterMonitor` has it); `transformIdentifiers` additionally needs `queryStatsReadTransformed`.

```javascript
db.getSiblingDB("admin").aggregate([
  { $queryStats: {} },
  { $sort: { "metrics.totalExecMicros.sum": -1 } },
  { $limit: 10 },
  { $project: { queryShapeHash: 1, "key.queryShape": 1, "metrics.execCount": 1,
                "metrics.totalExecMicros": 1, "metrics.lastExecutionMicros": 1 } }
])
```

The pipeline above (without `lastExecutionMicros`) ran on all four images and returned the `dbaverify.orders` find shape with `queryShapeHash` (8.0+), `key.queryShape`, `metrics.execCount: 20`, and `metrics.totalExecMicros` (`sum`, `max`, `min`, `sumOfSquares`). On these images it returned no entries until collection was turned on (before 9.0) or the sample rate was raised (9.0); see below.

Availability and sampling:

- The reference page states the stage is enabled on Atlas clusters M10 and above. It does not describe self-managed availability.
- On the images, `internalQueryStatsRateLimit` was `0` on 7.0, 8.0, 8.3, and 9.0, and the stage returned no entries.
- On the self-managed Community images before 9.0 (7.0.48, 8.0.38, 8.3.17), `db.adminCommand({ setParameter: 1, internalQueryStatsRateLimit: -1 })` turned collection on, and the stage then returned entries. `internalQueryStatsSampleRate` exists from 8.0 (value `0`) and `internalQueryStatsWriteCmdSampleRate` from 8.3 (value `0`); 7.0 has neither.
- From 9.0, stats are collected by default for a 1% sample of reads (`internalQueryStatsSampleRate`) and writes (`internalQueryStatsWriteCmdSampleRate`); the 9.0 image shows both at `0.01`. Counts are therefore a subset of real traffic; scale them, or raise the sample rate temporarily, for example `db.adminCommand({ setParameter: 1, internalQueryStatsSampleRate: 1 })`.
- Memory for the stats store is capped at 1% of system memory.
- The output format is documented as unstable. 9.0 moved `docsExamined` and `keysExamined` under `metrics.queryExec`, and added write commands. 8.2 moved `cpuNanos` into the metrics (Linux only). Do not hard-code field paths across versions.

## $currentOp and killing operations

```javascript
db.getSiblingDB("admin").aggregate([
  { $currentOp: { allUsers: true, idleConnections: false } },
  { $match: { active: true, secs_running: { $gte: 5 } } },
  { $project: { opid: 1, secs_running: 1, op: 1, ns: 1, "command.filter": 1, planSummary: 1,
                waitingForLock: 1, waitingForFlowControl: 1, currentQueue: 1, appName: 1, client: 1 } }
])
db.killOp(<opid>)
```

- Fields seen on the images differ by version:
  - 8.0+ shows `connectionId`, `client`, `appName`, `secs_running`, `numInterruptChecks`, `queues`, `currentQueue`.
  - 9.0 adds `priorityLowered`, `wasMarkedNonDeprioritizable`, `isFromPriorityPortConnection`.
  - 7.0 shows fewer fields (no `queues`).
- 8.2+ adds `versionContext` (the operation's FCV). 8.3+ adds `inUseTrackedMemBytes` and `peakTrackedMemBytes`. 9.0 adds `cursor.changeStreams.optime`.
- Do not `killOp` index builds on replica sets or sharded clusters; run `dropIndexes` on the primary instead. On a sharded cluster, `killOp` on `mongos` kills reads that span shards, but it does not propagate write operations to the shards; kill those on each shard (killOp page).
- `waitingForLock: true` with a long `secs_running` usually points to DDL or an index build. Find the holder by filtering on `locks` or `waitingForLock: false` with the same `ns`.

## Latency triage

Work through this in order, and stop when the cause is found:

1. Scope: one query shape, one collection, one node, or everything? Use `$queryStats` (or the slow log grouped by `queryShapeHash`) and per-node dashboards.
2. Queueing: `queues.execution` queue length and the slow-log `totalTimeQueuedMicros`. High queueing with normal execution time means overload (CPU, cache, or disk). Look at the node's resources, not at single queries.
3. Plans: for the top shapes, check `planSummary`. A `COLLSCAN`, or `keysExamined`/`docsExamined` far above `nreturned`, is an index problem. A sudden plan change after a deploy or upgrade can be pinned with query settings (8.0+) while you fix the cause.
4. Cache and disk:
   - `wiredTiger.cache` pressure;
   - disk latency (OS tools);
   - checkpoint stalls: on 7.0 the counters are in `db.serverStatus().wiredTiger.transaction` (for example `transaction checkpoint currently running`, `transaction checkpoint max time (msecs)`); 9.0 moves most of them to a separate `wiredTiger.checkpoint` section (containers 7.0.48 and 9.0.8). List the keys on your version and watch how long each checkpoint runs.
5. Replication:
   - lag on secondaries used for reads;
   - flow control engaged (`waitingForFlowControl`);
   - `w: "majority"` writes slowed by a lagging or missing secondary, especially in PSA sets.
6. Locks and DDL: `$currentOp` with `waitingForLock`; index builds; `renameCollection`; `collMod` on large collections.
7. Connections: `connections.current` near the limit, connection storms after failover, `rejected` counts.
8. Memory failures (9.0): `ExceededMemoryLimit` errors and `metrics.query.operationsFailedDueToMemoryLimit`.

Record the evidence for each step so the conclusion can be checked.

## Version differences in diagnostic output

| Item | 7.0 | 8.0 | 8.3 | 9.0 |
| --- | --- | --- | --- | --- |
| Ticket metrics path | `wiredTiger.concurrentTransactions` | `queues.execution` | + deprioritization fields | same as 8.3 |
| Slow threshold basis | duration | `workingMillis` | same | same |
| In-progress slow logging | — | — | `slowinprogms` 5000 | same |
| `queryShapeHash` | — | yes | yes | yes |
| `$queryStats` writes | — | — | — | yes, 1% sampling default |
| Memory tracking fields | — | — | `peakTrackedMemBytes` | + `expressionEvaluationPeakMemoryBytes` |
| serverStatus `service` field | absent | present (`[ 'shard' ]`) | removed | removed |
| Renamed metrics | — | `metrics.repl.buffer.write/apply` | `shardingStatistics.databaseVersionUpdateCounters` added | renamed to `databaseShardingMetadataStatistics`; `metrics.changeStreams.option.showExpandedEvents` |
