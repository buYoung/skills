# Amazon DynamoDB Versions

Checked: 2026-11-27 against the Developer Guide document history (https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DocumentHistory.html), the global tables versions page (https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_versions.html), and the DynamoDB local release history (https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocalHistory.html). DynamoDB has no published lifecycle page with end-of-support dates for the service; the pages above are the closest official equivalent.

DynamoDB is a managed service without server versions. Behavior changes arrive as dated feature launches on a single low-level API version (`20120810`, written `2012-08-10` in SDK service IDs). Three things do carry versions and change what a DBA does: the global tables version of a replicated table, the DynamoDB local release used for tests, and the AWS CLI or SDK release that must know a new parameter before you can use it.

## Support Status

| Series | Release type | First available | End of support | File |
|---|---|---|---|---|
| Low-level API `20120810` | Only API version; all features are added to it | 2012, per the version string | None published | This file |
| Service changes 2026 | Dated feature launches | 2026-01-13 onward (first entry kept) | Not applicable | [2026](2026.md) |
| Service changes 2025 | Dated feature launches | 2025-01-07 onward (first entry kept) | Not applicable | [2025](2025.md) |
| Service changes 2024 | Dated feature launches | 2024-03-19 onward (first entry kept; earlier 2024 history entries are documentation-only) | Not applicable | [2024](2024.md) |
| Global tables 2019.11.21 | Current | Upgrade path documented 2020-03-16 | None published | [global-tables-2019.11.21](global-tables-2019.11.21.md) |
| Global tables 2017.11.29 | Legacy, "should be avoided for new global tables" | 2017, per the version string | No date published; upgrade recommended | [global-tables-2017.11.29](global-tables-2017.11.29.md) |
| DynamoDB local 3.x | Current (recommended) | 3.0.0 on 2025-07-17; latest 3.3.2 on 2026-10-15 | None published | [local-3.x](local-3.x.md) |
| DynamoDB local 2.x | Legacy | 2.0.0 on 2023-07-05; last 2.6.0 on 2025-03-13 | None published | [local-2.x](local-2.x.md) |
| DynamoDB local 1.x | Deprecated | Last release 1.25.1 on 2024-11-06 | Deprecated; no date published | Covered in [local-2.x](local-2.x.md) as the upgrade source |

Document history dates are the dates the Developer Guide changed. A feature can launch earlier or later than its documentation entry (for example, DynamoDB local 3.3.0 added multi-attribute GSI keys on 2026-01-19, while the guide's entry for multi-attribute keys is dated 2026-04-16). Quote the date as a documentation date unless an announcement confirms the launch date.

Changes before 2024 that are now baseline and are described in the topic files without a version note: transactions (2018-11-27), on-demand capacity (2018-11-28), encryption at rest for all data (2018-11-15), customer managed keys (2019-11-25), adaptive capacity isolation of hot items (2019-11-26), Contributor Insights GA (2020-04-02), empty non-key string and binary values (2020-05-18), export to S3 (2020-11-09), PartiQL and Kinesis Data Streams (2020-11-23), AWS Backup integration (2021-11-24), 2,500 tables per Region default (2022-03-09), import from S3 (2022-08-18), deletion protection (2023-03-08), incremental export (2023-09-26), zero-ETL to OpenSearch Service (2023-11-28).

## Identify the Running Version

There is no server version to query. Establish these facts instead.

| Question | Command | Read |
|---|---|---|
| Which endpoint am I talking to? | `aws dynamodb describe-table --table-name T --query Table.TableArn` | Service ARNs carry the Region and account (`arn:aws:dynamodb:us-east-1:123456789012:table/T`). DynamoDB local 3.3.2 returns `arn:aws:dynamodb:ddblocal:000000000000:table/T` (container output). |
| Global tables version | `aws dynamodb describe-table --table-name T --query Table.GlobalTableVersion` | `"2019.11.21"` means a current-version replica. For legacy, run `aws dynamodb describe-global-table --global-table-name T`; success means 2017.11.29, `GlobalTableNotFoundException` means not legacy. |
| Global table consistency mode | `aws dynamodb describe-table --table-name T --query 'Table.{Mode:MultiRegionConsistency,Replicas:Replicas[*].RegionName,Witness:GlobalTableWitnesses}'` | `STRONG` means MRSC; `EVENTUAL` or an absent field means MREC (TableDescription reference: the field is optional, values `EVENTUAL`/`STRONG`, default `EVENTUAL`). |
| Capacity mode and limits | `aws dynamodb describe-table --table-name T --query 'Table.{Billing:BillingModeSummary,Prov:ProvisionedThroughput,OnDemand:OnDemandThroughput,Warm:WarmThroughput,Class:TableClassSummary}'` | `PAY_PER_REQUEST` is on-demand. `WarmThroughput` shows `ReadUnitsPerSecond`, `WriteUnitsPerSecond`, `Status`. DynamoDB local returns `null` for `WarmThroughput` (container output). |
| Account quotas | `aws dynamodb describe-limits` | Call at most about once a minute; it throttles otherwise. |
| PITR state | `aws dynamodb describe-continuous-backups --table-name T` | `PointInTimeRecoveryStatus` decides restorability; `ContinuousBackupsStatus` is always `ENABLED`. DynamoDB local rejects this call with `UnknownOperationException`. |
| DynamoDB local release | Startup log line `Version: 3.3.2`; or `java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -version` (flag exists since 2.2.0 and 1.25.0) | Compare with [local-3.x](local-3.x.md). |
| Client release | `aws --version`; SDK version from the dependency manifest | New request parameters (for example `--warm-throughput`, `--multi-region-consistency`, `--contributor-insights-mode`) are unknown to older CLI releases, which reject them. Upgrade the CLI or SDK first. |

There is no feature compatibility level. Every table in a Region gets new service behavior at the same time; you opt in through request parameters and table settings.

## Upgrade Paths

| From | To | Path | Rollback |
|---|---|---|---|
| Global tables 2017.11.29 | 2019.11.21 | Console, table, Global Tables tab, Update version. Needs `dynamodb:UpdateGlobalTableversion` in every replica Region. Details in [global-tables-2019.11.21](global-tables-2019.11.21.md). | No downgrade path is documented. Treat it as one-way. |
| DynamoDB local 2.x | 3.x | Replace the JAR or image tag; embedded and Maven users change imports from `com.amazonaws.services.dynamodbv2` to `software.amazon.dynamodb` and the Maven coordinates to `software.amazon.dynamodb:DynamoDBLocal`. | Pin the old image tag or artifact version. |
| DynamoDB local 1.x | 2.x | Move to the `jakarta` namespace; Java 11 for 2.0.0, Java 17 from 2.3.0, JRE 17 required from 2.6.0. | Pin the old version. |
| Older CLI or SDK | Current | Upgrade the client before using a new parameter; check for changed defaults such as account-based endpoints (SDKs since 2024 for DynamoDB, documented for DynamoDB Streams on 2026-11-17). | Pin the client version; set `account_id_endpoint_mode = disabled` to return to Regional endpoints. |
| `AmazonDynamoDBFullAccess` managed policy | `AmazonDynamoDBFullAccess_v2` | Attach the v2 policy and remove the deprecated one after testing (deprecated 2025-04-25). | Reattach the old policy while it still exists. |

Generic procedure for adopting a service change:

1. Pre-check. Read the feature's limitations page and the [2026](2026.md), [2025](2025.md), or [2024](2024.md) entry. Check quotas with Service Quotas and `describe-limits`. Confirm the CLI or SDK knows the parameter.
2. Rehearse. Restore a copy with `restore-table-to-point-in-time` (see [backup-and-recovery](../backup-and-recovery.md)) or create a test table with the same key schema and indexes. DynamoDB local does not reproduce capacity, throttling, PITR, global tables, or vector indexes; rehearse those on the service.
3. Switch. Apply the change with `update-table` or infrastructure as code. Many changes are asynchronous: poll `describe-table` until `TableStatus`, `IndexStatus`, or `WarmThroughput.Status` is `ACTIVE`.
4. Post-check. Watch `ThrottledRequests`, `SuccessfulRequestLatency`, `SystemErrors` (with the `Operation` dimension), and `ReplicationLatency` for global tables. Confirm the setting with `describe-table`.

Changes that cannot be undone or have rate limits: warm throughput increases cannot be decreased; provisioned-to-on-demand switches are limited to four per 24 hours; LSIs cannot be added or removed after creation; global table consistency mode cannot be changed after creation; a stream's `StreamViewType` cannot be edited (disable and re-enable, which creates a new stream ARN).

## Outside the Covered Range

- Information older than 2024: the service applies current behavior to every table, so older material may describe limits that changed (for example, one provisioned-to-on-demand switch per day before 2025-08-12, or a fixed 35-day PITR window before 2025-01-07; DynamoDB local itself allowed only 25 actions per transaction before 1.21.0). Check the current Developer Guide page and the document history before relying on them.
- Changes after 2026-11-27: read the document history RSS feed (https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/dynamodbupdates.rss) and the "What's New" announcements. Claims in this reference most likely to drift: quotas, MRSC Region list, Contributor Insights modes, throttling reason codes, vector index limits, and bulk put items limits.
- Legacy global tables (2017.11.29): many statements in [global-tables-and-streams](../global-tables-and-streams.md) do not hold; use [global-tables-2017.11.29](global-tables-2017.11.29.md).
- DynamoDB local older than 3.x, or ExtendDB: feature support differs by release; check [dynamodb-local](../dynamodb-local.md) and the release history.
- In every answer, state the date of the documentation you relied on and, for local testing, the DynamoDB local release.

## Sources

Versions and lifecycle:

- Document history for the Amazon DynamoDB Developer Guide — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DocumentHistory.html — checked 2026-11-27
- DynamoDB global tables versions — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_versions.html — checked 2026-11-27
- Global tables version 2017.11.29 (Legacy) — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/globaltables.V1.html — checked 2026-11-27
- Release history for DynamoDB local — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocalHistory.html — checked 2026-11-27
- Deploying DynamoDB locally on your computer — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.DownloadingAndRunning.html — checked 2026-11-27
- DynamoDB local usage notes — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.UsageNotes.html — checked 2026-11-27
- Setting up ExtendDB — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ExtendDB.html — checked 2026-11-27
- ExtendDB behavior differences from DynamoDB — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ExtendDB.Differences.html — checked 2026-11-27
- DynamoDB low-level API (X-Amz-Target `DynamoDB_20120810`) — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Programming.LowLevelAPI.html — checked 2026-11-27
- DynamoDB API Reference — https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/Welcome.html — checked 2026-11-27

Limits, capacity, errors, and performance:

- Constraints in Amazon DynamoDB — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Constraints.html — checked 2026-11-27
- Quotas in Amazon DynamoDB — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ServiceQuotas.html — checked 2026-11-27
- DynamoDB on-demand capacity mode — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/on-demand-capacity-mode.html — checked 2026-11-27
- DynamoDB maximum throughput for on-demand tables — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/on-demand-capacity-mode-max-throughput.html — checked 2026-11-27
- Considerations when switching capacity modes — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-switching-capacity-modes.html — checked 2026-11-27
- Understanding DynamoDB warm throughput — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/warm-throughput.html — checked 2026-11-27
- Increase your existing table's warm throughput — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/update-warm-throughput.html — checked 2026-11-27
- DynamoDB burst and adaptive capacity — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/burst-adaptive-capacity.html — checked 2026-11-27
- Using write sharding — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-sharding.html — checked 2026-11-27
- Troubleshooting throttling — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TroubleshootingThrottling.html — checked 2026-11-27
- Diagnosing throttling — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/throttling-diagnosing-workflow.html — checked 2026-11-27
- DynamoDB read and write operations — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/read-write-operations.html — checked 2026-11-27
- Error handling with DynamoDB — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Programming.Errors.html — checked 2026-11-27
- BatchWriteItem API — https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_BatchWriteItem.html — checked 2026-11-27
- BatchGetItem API — https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_BatchGetItem.html — checked 2026-11-27
- TransactWriteItems API (cancellation reason codes) — https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_TransactWriteItems.html — checked 2026-11-27
- Basic operations on DynamoDB tables — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/WorkingWithTables.Basics.html — checked 2026-11-27

Modeling and indexes:

- Data modeling foundations — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/data-modeling-foundations.html — checked 2026-11-27
- Improving data access with secondary indexes — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/SecondaryIndexes.html — checked 2026-11-27
- Using Global Secondary Indexes — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html — checked 2026-11-27
- Managing Global Secondary Indexes — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.OnlineOps.html — checked 2026-11-27
- Multi-attribute keys pattern — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.DesignPattern.MultiAttributeKeys.html — checked 2026-11-27
- Local secondary indexes — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/LSI.html — checked 2026-11-27
- Filter expressions for Query — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Query.FilterExpression.html — checked 2026-11-27
- PartiQL select statements — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ql-reference.select.html — checked 2026-11-27
- DynamoDB table classes — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.TableClasses.html — checked 2026-11-27
- Vector index requirements and limitations — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/VectorSearch.Requirements.html — checked 2026-11-27

Transactions and consistency:

- DynamoDB read consistency — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadConsistency.html — checked 2026-11-27
- Amazon DynamoDB Transactions: How it works — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/transaction-apis.html — checked 2026-11-27
- Best practices for handling concurrent updates — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/BestPractices_ImplementingVersionControl.html — checked 2026-11-27

Global tables, streams, TTL, integrations:

- How DynamoDB global tables work — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_HowItWorks.html — checked 2026-11-27
- Tutorials: Creating global tables (MREC and MRSC CLI) — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables.tutorial.html — checked 2026-11-27
- Change data capture for DynamoDB Streams — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html — checked 2026-11-27
- DynamoDB Streams and Time to Live — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/time-to-live-ttl-streams.html — checked 2026-11-27
- Using Kinesis Data Streams to capture changes — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/kds.html — checked 2026-11-27
- Getting started with Kinesis Data Streams for DynamoDB — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/kds_gettingstarted.html — checked 2026-11-27
- Using time to live (TTL) — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/howitworks-ttl.html — checked 2026-11-27
- Zero-ETL integration with Amazon Redshift — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/RedshiftforDynamoDB-zero-etl.html — checked 2026-11-27

Backup and recovery:

- Backup and restore for DynamoDB — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Backup-and-Restore.html — checked 2026-11-27
- Point-in-time backups — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Point-in-time-recovery.html — checked 2026-11-27
- Enable point-in-time recovery — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/PointInTimeRecovery_Howitworks.html — checked 2026-11-27
- Restoring a table to a point in time — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/PointInTimeRecovery.Tutorial.html — checked 2026-11-27
- Restore a table — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/pointintimerecovery_restores.html — checked 2026-11-27
- Backing up a table — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Backup.Tutorial.html — checked 2026-11-27
- Using AWS Backup with DynamoDB — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/backuprestore_HowItWorksAWS.html — checked 2026-11-27
- Best practices for PITR recovery — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-pitr-recovery.html — checked 2026-11-27
- Rolling back unwanted writes in place — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-pitr-recovery-inplace-rollback.html — checked 2026-11-27
- Export to S3: how it works — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/S3DataExport.HowItWorks.html — checked 2026-11-27
- Import from S3: how it works — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/S3DataImport.HowItWorks.html — checked 2026-11-27
- Working with bulk put items — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/BulkPutItems.HowItWorks.html — checked 2026-11-27

Security and monitoring:

- DynamoDB encryption at rest — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/EncryptionAtRest.html — checked 2026-11-27
- Using IAM policy conditions for fine-grained access control — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/specifying-conditions.html — checked 2026-11-27
- Using resource-based policies — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/access-control-resource-based.html — checked 2026-11-27
- Logging DynamoDB operations by using AWS CloudTrail — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/logging-using-cloudtrail.html — checked 2026-11-27
- DynamoDB metrics and dimensions — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/metrics-dimensions.html — checked 2026-11-27
- CloudWatch Contributor Insights for DynamoDB: how it works — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/contributorinsights_HowItWorks.html — checked 2026-11-27
- Getting started with Contributor Insights (CLI) — https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/contributorinsights_tutorial.html — checked 2026-11-27

Container evidence:

- Run of `amazon/dynamodb-local:latest` (digest `sha256:6ada631ec7aa5fc83446855eb17233e3dad184fec47477e8140c6c569cfe0c86`, arm64): startup banner, `-help` output, and the CLI commands that the DynamoDB local files mark as container results — run 2026-11-27
