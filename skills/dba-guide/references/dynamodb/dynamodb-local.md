# DynamoDB Local and the Service

Checked: 2026-11-27 against the DynamoDB local usage notes and a run of `amazon/dynamodb-local:latest` reporting `Version: 3.3.2`. Release details: [versions/local-3.x.md](versions/local-3.x.md), [versions/local-2.x.md](versions/local-2.x.md).

DynamoDB local is a downloadable implementation of the DynamoDB API (JAR, Docker image `amazon/dynamodb-local`, Maven artifact, CloudShell alias) for development and tests. It is not a scaled-down service: it has no partitions, no capacity enforcement, no Regions, and no backup or replication features. Use it to test request syntax, data access code, and expression logic; test capacity, throttling, consistency timing, security, and operations on the service.

## Running It

```bash
# Ephemeral, in memory (the image's default command, per the container log)
docker run --rm -p 8000:8000 amazon/dynamodb-local:3.3.2

# Persistent, one shared database file
docker run --rm -p 8000:8000 -v "$PWD/ddb:/home/dynamodblocal/data" -w /home/dynamodblocal \
  amazon/dynamodb-local:3.3.2 -jar DynamoDBLocal.jar -sharedDb -dbPath ./data

aws dynamodb list-tables --endpoint-url http://localhost:8000
```

On 2026-11-27 the `3.3.2` tag pulled from Docker Hub with the same digest as `latest` (`sha256:6ada631e...`). The startup log prints the configuration (`Port`, `InMemory`, `Version`, `DbPath`, `SharedDb`, `shouldDelayTransientStatuses`, `CorsParams`); check it in CI logs.

Options:

| Option | Effect |
|---|---|
| `-inMemory` | No files; data lost on exit. Cannot combine with `-dbPath` |
| `-dbPath <dir>` | Directory for the database file (default current directory) |
| `-sharedDb` | One file `shared-local-instance.db` for all credentials and Regions; without it, files are named `<accesskeyid>_<region>.db`, so clients with different fake credentials see different tables |
| `-port <n>` | Default 8000 |
| `-delayTransientStatuses` | Adds delays for GSIs in `CREATING` and `DELETING` to mimic the service |
| `-optimizeDbBeforeStartup` | Optimize tables at start; needs `-dbPath` |
| `-cors <list>` | CORS allow list; default `*` |
| `-disableTelemetry` | Turn off telemetry (added in 2.1.0) |
| `-version`, `-help` | Print version or usage |

Credentials must be present but need not be valid; the access key ID may contain only letters and digits. The AWS CLI needs `--endpoint-url` on every command. Running the image with only `-help` as the argument prints the Java launcher's help, not DynamoDB local's (container output); pass `-jar DynamoDBLocal.jar -help`, which lists the options above. `-jar DynamoDBLocal.jar -version` prints `3.3.2`.

## Differences That Change Test Results

| Area | Service | DynamoDB local | Source |
|---|---|---|---|
| Capacity | Enforced; throttling | Provisioned values accepted and ignored; no throttling; `UpdateTable` unlimited | Usage notes |
| Consumed capacity reporting | Real | Reported (put with one GSI: 2.0; GSI eventual query: 0.5) | Container output |
| Table and index states | `CREATING`/`UPDATING` take time | Tables are `ACTIVE` immediately; GSIs pass through `CREATING`/`DELETING` | Usage notes |
| Consistency | Eventual reads can be stale | Eventual reads usually look strong; GSI strong read still rejected with `ValidationException` (the service's text was not compared) | Usage notes; container output |
| Parallel scan | `Segment`/`TotalSegments` | Usage notes: ignored, scans are sequential. 3.3.2 split 25 items into disjoint segments (12 and 13 with `TotalSegments=2`; 9, 3, 7, 6 with 4), so segment code is exercised (conflict; the only place this reference records the figures) | Usage notes vs container output |
| 1 MB page size on index queries | Counts projected attributes | Counts the whole item, so pages can be smaller | Usage notes |
| Transactions | Can throw `TransactionConflictException` | Never throws it; mock conflicts | Usage notes |
| Table names | Case-sensitive | Usage notes: case-insensitive. In 3.3.2, `CreateTable orders` while `Orders` exists fails with `InternalFailure` (HTTP 500, retried by the CLI; the log shows SQLite `table "orders" already exists`), but `DescribeTable orders` returns `ResourceNotFoundException` (conflict) | Usage notes vs container output |
| Item collection metrics | Returned | Null (3.3.2 response body `{}` with `ReturnItemCollectionMetrics=SIZE` on an LSI table) | Usage notes; container output |
| Streams | Shards follow partitions | No partitions; shard behavior differs | Usage notes |
| PartiQL `Limit` on `ExecuteStatement` | Honored | Usage notes: ignored. The release history lists "Support for Limit Operation" for PartiQL in 1.22.0 (2023-06-08), and 3.3.2 honored `Limit=1` on a two-item table: one item and a `NextToken` that returned the second. The usage-notes line looks stale (inference) | Usage notes vs release history and container output |
| Tagging | Supported | `UnknownOperationException: Tagging is not currently supported in DynamoDB Local.` | Usage notes; container output |
| PITR and continuous backups | Supported | `UnknownOperationException` | Usage notes; container output |
| Vector indexes | Supported | `VectorIndexes` accepted and ignored; no `SearchVectors` | Usage notes |
| Regions and accounts | Per Region, per account | Not supported at client level; ARNs use `ddblocal` and `000000000000` | Usage notes; container output |
| Warm throughput | Reported per table and GSI | `WarmThroughput` is `null`; `UpdateTable` with only `--warm-throughput` returns `ValidationException: Nothing to update`, and with another change it is ignored | Container output |
| `BillingModeSummary` | Returned | Usage notes say always null, but 3.3.2 returned `BillingMode: PAY_PER_REQUEST` (conflict) | Usage notes vs container output |
| On-demand maximum throughput | Enforced (best effort) | Accepted and echoed in `OnDemandThroughput`; `-1` for both values removes it (`OnDemandThroughput` null); not enforced (inference from "no throttling") | Container output |
| Deletion protection | Enforced | Enforced (error text not compared with the service) | Container output |
| TTL | Deletes within days | `UpdateTimeToLive`/`DescribeTimeToLive` work; expiry deletion behavior not verified | Container output |
| Quotas | Adjustable | `describe-limits` returns 80,000 account / 40,000 table defaults | Container output |
| Item size | 400 KB | 400 KB enforced (error text not compared with the service) | Container output |
| Resource policies, on-demand backups, Contributor Insights | Supported | `PutResourcePolicy`, `GetResourcePolicy`, `CreateBackup`, `ListBackups`, `UpdateContributorInsights` return `UnknownOperationException: An unknown operation was requested.` | Container output |
| Global table replicas | Supported | `UpdateTable --replica-updates` alone returns `ValidationException: Nothing to update`; with another change it is ignored and `Replicas` stays null | Container output |
| MRSC, exports, imports, bulk put items, KMS | Supported | Not available (not tested) | Inference |

## What to Test Where

| Test | DynamoDB local | Service (test account) |
|---|---|---|
| Expression syntax, reserved words, key conditions | Yes | |
| Conditional write logic and `ReturnValuesOnConditionCheckFailure` | Yes | |
| Transaction success and condition cancellation | Yes | |
| Transaction conflicts, throttling, retries, backoff | No | Yes, or mocks |
| Read-after-write staleness on GSIs | No | Yes |
| Capacity and cost estimates | Indicative only (`ConsumedCapacity`) | Yes |
| IAM, FGAC, resource policies, encryption | No | Yes |
| Backup, restore, export, import, global tables | No | Yes |
| Stream consumer logic | Partly (record shape) | Yes (shards, ordering under load) |

## ExtendDB

Since 2026-11-18 the Developer Guide also documents ExtendDB, an open-source adapter that serves the DynamoDB API from SQLite or PostgreSQL. It is managed by AWS but contains no DynamoDB code. The `extenddb/extenddb-dev` image needs no Java, serves plain HTTP, verifies SigV4 signatures, and grants every seeded credential full access; use it for development and CI only. A durable `extenddb-postgres` image adds TLS and access control. Its behavior differences are published in the ExtendDB repository, not in the Developer Guide; check them before switching test suites (not verified in this reference).

## Common Mistakes

- Concluding a design "scales" because tests on DynamoDB local are fast.
- Different fake credentials in two services without `-sharedDb`, so each sees an empty database.
- Tests that pass only because eventual reads look strong locally.
- Using `latest` in CI and getting a new release mid-project; pin the tag or artifact version.
- Treating parallel scan tests as load tests: 3.3.2 splits items by `Segment`, but there are no partitions or throttling to exercise.
