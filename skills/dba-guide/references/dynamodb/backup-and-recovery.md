# DynamoDB Backup and Recovery

Checked: 2026-11-27. Configurable PITR retention dates from 2025-01-07 ([versions/2025.md](versions/2025.md)); filtered export and bulk put items from 2026 ([versions/2026.md](versions/2026.md)).

Contents: choosing a mechanism; PITR; on-demand backups and AWS Backup; restore procedure and verification; undoing bad writes in place; deleted tables and deletion protection; export, import, and bulk load; quotas; common mistakes.

## Choosing a Mechanism

| Need | Use | Notes |
|---|---|---|
| Undo accidental writes or deletes in the last days | PITR | Per-second granularity, 1 to 35 days; restore creates a new table |
| Long-term retention, compliance, WORM | AWS Backup (on-demand backups through backup plans, Vault Lock, cold storage, cross-account and cross-Region copies) | Backups encrypted with a vault key independent of the table key |
| Ad hoc snapshot before a risky change | `create-backup` or AWS Backup on-demand job | Full backup, retained until deleted |
| Region loss | Global tables (availability), plus cross-Region restore or AWS Backup copies (data protection) | Replication copies mistakes to every Region; it is not a backup |
| Analytics copy or partial extraction | Export to S3 (full, incremental, filtered) | Needs PITR; does not consume read capacity |
| Load data | Import from S3 (new table) or bulk put items (existing table) | Neither consumes table write capacity |

DynamoDB local supports none of the backup APIs; `describe-continuous-backups` and `update-continuous-backups` fail there with `UnknownOperationException` (container output). Test backup and restore runbooks in an AWS account.

## Point-in-Time Recovery

```bash
aws dynamodb update-continuous-backups --table-name Orders \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true,RecoveryPeriodInDays=35
aws dynamodb describe-continuous-backups --table-name Orders
```

Read the output: `PointInTimeRecoveryStatus` must be `ENABLED`; `ContinuousBackupsStatus` is always `ENABLED` and means nothing on its own. `EarliestRestorableDateTime` and `LatestRestorableDateTime` bound the window; the latest point is typically about five minutes before now.

Decision rules:

- Enable PITR on every production table, on each global table replica separately (PITR is not synchronized), and before creating exports or zero-ETL integrations, which require it.
- Keep `RecoveryPeriodInDays` at 35 unless policy demands less. Price depends on table plus LSI size, not on the period. Lowering the period discards recovery points outside the new window immediately; raising it does not bring back old points.
- Disabling and re-enabling PITR resets the window; immediately after re-enabling you can restore only to `LatestRestorableDateTime`. Treat disabling as a destructive change.
- PITR has no effect on table performance or latency.

## On-Demand Backups and AWS Backup

```bash
aws dynamodb create-backup --table-name Orders --backup-name orders-before-migration
aws dynamodb describe-backup --backup-arn <arn>     # wait for BackupStatus AVAILABLE
aws dynamodb list-backups --table-name Orders
aws dynamodb restore-table-from-backup --target-table-name Orders-restored --backup-arn <arn>
```

AWS Backup adds scheduled plans, incremental backups after the first full one, cross-Region and cross-account copies, lifecycle to cold storage, tags, audit reports, and Vault Lock. AWS Backup must be opted in per account and Region for DynamoDB. Tags and ABAC are not supported on DynamoDB-native backups; use AWS Backup if backups need tag-based control.

## Restore Procedure

Every restore (PITR or backup) creates a new table. The source table stays online and is unaffected.

```bash
# Latest restorable time, same Region
aws dynamodb restore-table-to-point-in-time --source-table-name Orders \
  --target-table-name Orders-20261127-0910 --use-latest-restorable-time

# Specific time, without GSIs (faster), on-demand billing
aws dynamodb restore-table-to-point-in-time --source-table-name Orders \
  --target-table-name Orders-20261127-0905 --restore-date-time 2026-11-27T09:05:00Z \
  --global-secondary-index-override '[]' --billing-mode-override PAY_PER_REQUEST

# Cross-Region: run in the destination Region, pass the source ARN and an SSE override
aws dynamodb restore-table-to-point-in-time --region eu-west-1 \
  --source-table-arn arn:aws:dynamodb:us-east-1:123456789012:table/Orders \
  --target-table-name Orders-dr --use-latest-restorable-time \
  --sse-specification-override Enabled=true,SSEType=KMS
```

Restored from the source: data, GSIs and LSIs (unless overridden), provisioned capacity as it was at the restore point, and encryption settings. Not restored; configure them on the new table: auto scaling policies, IAM policies, CloudWatch alarms, Contributor Insights, tags, stream settings, TTL, deletion protection, and PITR itself. Overrides exist for GSIs, LSIs, billing mode, provisioned throughput, and encryption. Cross-Region restore is not available to or from Asia Pacific (Hong Kong) or Middle East (Bahrain).

Restore time depends on data size and number of indexes and has no fixed bound. Do not change or remove the IAM permissions of the identity running the restore while it is in progress; the restore can fail to write data.

### Getting the Application Back

A restore does not replace the original table. Choose one of:

1. Point the application at the restored table name (fastest; reapply every setting listed above first, and re-create stream consumers, zero-ETL integrations, and global table replicas).
2. Copy the needed items from the restored table back into the original (keeps the name, ARN, streams, and replicas; costs writes on the original and is slower). This is a suggestion, not a documented method; the documented in-place method is below.

### Verify a Restore

1. `describe-table` on the new table: `TableStatus` `ACTIVE`, `RestoreSummary.RestoreInProgress` false (RestoreSummary API reference), expected `ItemCount` and indexes (counts refresh about every six hours, so use a `Scan --select COUNT` on a test-sized table or compare known keys instead).
2. Read a list of known items written just before and just after the restore point with strongly consistent `GetItem`.
3. Run the application's critical queries against it with `--return-consumed-capacity TOTAL`.
4. Re-enable PITR, deletion protection, TTL, streams, Contributor Insights, alarms, and tags; confirm with `describe-continuous-backups`, `describe-time-to-live`, and `describe-table`.
5. Record restore duration; it is your measured RTO for that table size.

## Undoing Bad Writes In Place

When a small set of writes must be reversed and the original table should stay in service:

1. Run an incremental export with view type new and old images for the window of the bad writes (15 minutes to 24 hours per export, inside the PITR window; several exports for longer periods).
2. Write the old images back from S3 with a bulk job, optionally transforming them. The Developer Guide points to the open-source Bulk Executor (AWS Glue based, no official support).
3. Use condition expressions on the write-back so that items changed again after the incident are not overwritten (guideline, not from the documentation).

```bash
aws dynamodb export-table-to-point-in-time \
  --table-arn arn:aws:dynamodb:us-east-1:123456789012:table/Orders \
  --s3-bucket orders-exports --export-type INCREMENTAL_EXPORT \
  --incremental-export-specification ExportFromTime=2026-11-27T09:00:00Z,ExportToTime=2026-11-27T09:30:00Z,ExportViewType=NEW_AND_OLD_IMAGES
```

Parameter names and values match the CLI reference: `--export-type FULL_EXPORT|INCREMENTAL_EXPORT` (default full; incremental requires the specification) and `ExportViewType` `NEW_AND_OLD_IMAGES` (default) or `NEW_IMAGE`. The reference's prose spells the second value `NEW_IMAGES`, but its possible-values list and JSON syntax use `NEW_IMAGE`.

## Deleted Tables and Deletion Protection

- Deleting a table with PITR enabled creates a system backup named `<table>$DeletedTableBackup`, kept 35 days at no charge. Restore it like any backup; it restores the state just before deletion.
- Without PITR or an on-demand backup, `DeleteTable` is unrecoverable. Production safety: enable deletion protection on every production table and replica. It is off by default, including on restored tables and new global replicas.

```bash
aws dynamodb update-table --table-name Orders --deletion-protection-enabled
aws dynamodb delete-table --table-name Orders
# ValidationException: Resource cannot be deleted as it is currently protected against deletion. Disable deletion protection first.
```

(Error text from DynamoDB local 3.3.2.) Disable with `--no-deletion-protection-enabled` only in a reviewed change.

- If DynamoDB loses access to a customer managed KMS key, the table is archived: backed up and the original deleted. Protect key policies and deletion schedules as carefully as the table ([security-and-monitoring](security-and-monitoring.md)).

## Export, Import, and Bulk Load

| Feature | Target | Capacity impact | Key limits |
|---|---|---|---|
| Full export to S3 | S3, DynamoDB JSON or Ion | None | Up to 300 concurrent tasks or 100 TB in flight |
| Incremental export | S3, changed items with chosen view | None | Window 15 minutes to 24 hours; 10 MB minimum charge |
| Filtered export (2026-10-01) | S3, key condition, filter, projection | None | Same as full or incremental |
| Import from S3 | New table only (GSIs allowed, no LSIs) | None | CSV, DynamoDB JSON, Ion; GZIP or ZSTD; 50 concurrent jobs, 15 TB in us-east-1, us-west-2, eu-west-1 and 1 TB elsewhere; 50,000 objects per job |
| Bulk put items (2026-11-05) | Existing table | None on the table | Standard 100 GB or Accelerated 1 TB per operation; 5 concurrent per tier per account; 1 active per table; 50,000 objects of up to 5 GB |

Cautions:

- Exports have no completion-time SLA.
- Import overwrites duplicate keys silently; the processed count will not match the item count. Items that fail validation are still billed. Do not modify source S3 objects during an import (`ObjectModifiedInS3DuringImport`).
- Bulk put items overwrites items with the same key unless each record carries a condition expression such as `attribute_not_exists(PK)`; review the output report in S3 for failed and skipped items.

## Quotas

Up to 50 concurrent restores totaling 50 TB through DynamoDB backups or PITR; AWS Backup supports 50 concurrent restores totaling 25 TB.

## Common Mistakes

- Treating global tables as backups.
- Restoring and forgetting to re-enable PITR, TTL, streams, alarms, and deletion protection on the new table.
- Disabling PITR "temporarily" and losing the recovery window.
- Planning an RTO without having timed a restore of a production-sized table.
- Testing backup scripts against DynamoDB local, which has no backup APIs.
