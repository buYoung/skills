# Linux vNext Emulator: What It Can and Can't Prove

Checked: 2026-11-27. Read before using the Azure Cosmos DB emulator to test application behavior, CI pipelines, or examples from this reference. Sources: the emulator-linux page and a run of `mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:vnext-latest` on arm64 (release `EN20261123`; REST requests, startup log, and `--help` output). On 2026-11-27 the `vnext-latest` and `vnext-preview` tags resolved to the same index digest, `sha256:c274ac17c19a5f74dbadbc99f259bc49a8640a03f6789f54d7f76cbfc33ff6b6`; the runs used `vnext-preview`.

## Scope

- API for NoSQL only, gateway mode only. No MongoDB, Cassandra, Gremlin, or Table endpoints. The Table FAQ also says the Table SDK can't be used with the emulator.
- Runs on x64 and arm64 as a Docker container. Internally it runs PostgreSQL with a `pgcosmos` extension behind a Rust gateway (container log); behavior can differ from the service in ways the feature table doesn't list.
- No authentication enforcement, even with `--key-file`. HTTPS changes transport only. Don't expose it beyond a trusted network.

## Start and readiness

```bash
docker run --detach -p 8081:8081 -p 8080:8080 -p 1234:1234 \
  mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:vnext-latest
curl -s http://localhost:8080/ready    # readiness; /alive and /status also exist
```

- `/alive`, `/ready`, `/status`, and the deprecated `/health` (health port 8080) returned 200 once ready, each with the same JSON body: per-component checks (`postgres`, `gateway`, `explorer`), `ready`, `protocol`, and the release string as `version` (`EN20261123`). Before readiness the port refused connections.
- Default protocol is HTTP. The .NET and Java SDKs need `--protocol https` (and the Java trust store needs the emulator certificate).
- Data lives in `/data`; mount it to persist between runs. Without a mount, `--rm` discards everything.
- Seed scripts: `ENABLE_INIT_DATA=true` runs `.csh` Azure Cosmos DB Shell scripts from `/init` in alphabetical order; the shell is in the image as `cosmoshell.sh`.
- Large query results can fail with HTTP 500; raise `--query-buffer-size` (KB, default 4096, max 65536).
- Telemetry to Microsoft is on by default (`--enable-telemetry`); set it to `false` in CI if policy requires.
- The `--help` output of release EN20261123 lists options not in the docs table: `--default-consistency-level` (default `Strong`), thin-client (Gateway 2.0) endpoint on port 10250, `--gateway-engine`, `--change-stream-retention-size-mb`, `--enable-package-update`, `--health-port`. The docs table lists `https-insecure` as a protocol value; the help output lists only `http` and `https`.

## Feature support that changes test results

| Feature | Emulator | Consequence |
| --- | --- | --- |
| Request units | Not implemented; every response observed had `x-ms-request-charge: 1` | Don't measure or compare RU costs locally |
| Throughput (offers) | No-op; `GET /offers` returned `offerType: "Invalid"` with the requested 400 RU/s | No 429s from throughput limits; can't test autoscale, buckets, priority |
| Custom indexing policy | Accepted; only DiskANN vector indexes take effect. Range, composite, and spatial indexes planned, not available | Queries that need a composite index on Azure pass locally: a cross-partition `ORDER BY c.status ASC, c.total DESC` with no composite index returned 200, correctly sorted |
| Vector indexes | `diskANN` supported; `flat`, `quantizedFlat`, full-text not supported | |
| Stored procedures, triggers, UDFs | Not planned. A create request returned 201; executing it returned 400 "Server-side script execution is not supported in this emulator" | Code that depends on them passes create and fails later |
| Update collection, users, permissions, client encryption keys | No-op | Settings don't apply |
| Parallel partitioned queries, read collection/database feeds | Not yet implemented | |
| Change feed, batch, bulk, patch, TTL, partitioned containers | Supported | Bulk is not supported by the .NET SDK against the emulator |
| TTL | Documented as supported. With `defaultTtl: 5`, a point read returned 404 after expiry, but queries (single- and cross-partition) and the read feed still returned the item 190 seconds later | Don't rely on the emulator to show expired items disappearing from queries |
| Consistency | Account advertises `Strong` by default | Azure accounts default to Session; `--default-consistency-level Session` makes `GET /` return `Session`. The help text says this controls SDK compatibility only, not replication guarantees. The `x-ms-consistency-level` request header isn't validated: `Strong` on a Session account, and an invalid value, both returned 200 |
| Topology | One partition key range; one region (`South Central US`) | No splits, no hot partitions, no failover |

## Observed behavior (release EN20261123)

| Test | Result | Service behavior to expect |
| --- | --- | --- |
| `GET /` | 200 with `writableLocations`, `readableLocations`, `userConsistencyPolicy` | Same shape |
| New container definition | Default policy `/*` included, `/"_etag"/?` excluded; LWW on `/_ts`; `partitionKey.version: 2` | Same defaults documented |
| Hierarchical key container | Created with `kind: MultiHash` | Same |
| Insert without `x-ms-documentdb-partitionkey` | 201 | The REST reference says the header is required for document operations on partitioned collections; expect an error on Azure |
| Point read with the wrong partition key | 404 `NotFound` | Same |
| Replace with stale `If-Match` | 412 `PreconditionFailed` | Same status |
| 2 MiB + 1 KB item | 413 `RequestEntityTooLarge` | 413 for items over 2 MB |
| Cross-partition `ORDER BY` with `x-ms-max-item-count: 5` | All results in one page, no `x-ms-continuation`: `x-ms-item-count` was the full result count (14 with `WHERE c.total > 5`, 22 without a filter). A single-partition query and the read feed honored the page size and returned a continuation | Page size honored; continuation returned |
| Partition key in header differs from the body, on create or on a replace that changes the key value | 400 `BadRequest`, substatus 1001, "PartitionKey extracted from document doesn't match the one specified in the header."; the stored item is unchanged | Partition key values are immutable |
| `id` containing `/` or `\` | 201; a point read with `a%2Fb` in the path returned the item | `/` and `\` are not allowed in `id` |
| `defaultTtl: 60` with `indexingMode: none` | 201; container created with both settings | TTL can't be enabled when indexing mode is `none` |
| Hierarchical key `["t1","u1"]` in `x-ms-documentdb-partitionkey` | Create 201, point read 200, cross-partition prefix query on `tenantId` 200 with one item; a one-level value `["t1"]` on the point read returned 400 ("Length does not match the number of partition key paths") | Header format not yet checked on an Azure account |
| Transactional batch of 101 operations | 400 "The maximum number of operations allowed in a single transaction is 100", no items written; 100 operations returned 200 | 100-operation limit |
| Delete, then latest-version change feed from the beginning | 204; the deleted item was absent from the feed | Deletes don't appear in latest version mode |
| Session token | Format `0:0#<n>` | Format differs by partition and region |

## Use it for

- Schema and container-definition tests, partition key extraction, CRUD, patch, batch, change feed consumers, TTL as seen by point reads, and SDK wiring in CI.
- Seeding repeatable datasets with Azure Cosmos DB Shell scripts.

## Don't use it for

- RU budgeting, indexing-policy tuning, 429 handling, consistency or failover behavior, authentication and RBAC tests, stored procedure logic, or performance numbers.
- Request validation the service applies but the emulator skipped: `id` characters, TTL with indexing mode `none`, composite-index requirements for `ORDER BY`, and the per-request consistency level.

Use a low-throughput or serverless Azure account for those.
