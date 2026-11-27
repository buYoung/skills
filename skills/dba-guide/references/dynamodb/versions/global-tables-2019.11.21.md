# Global Tables Version 2019.11.21 (Current)

Checked: 2026-11-27 against https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_versions.html and https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_HowItWorks.html

Read this when a table is or will become a global table, or when upgrading a 2017.11.29 global table.

## Lifecycle

Current version and the one AWS recommends. Available in all Regions. No end date published. MREC and MRSC consistency modes, multi-account global tables, warm throughput on global tables, and replica disassociation exist only in this version.

## Changed Defaults

Compared with 2017.11.29:

| Behavior | 2017.11.29 | 2019.11.21 |
|---|---|---|
| Create | Empty Regional tables, then `CreateGlobalTable` | `UpdateTable --replica-updates` on an existing table, which may hold data (MREC) |
| Management APIs | `CreateGlobalTable`, `DescribeGlobalTable`, `DescribeGlobalTableSettings`, `ListGlobalTables`, `UpdateGlobalTable`, `UpdateGlobalTableSettings` | `DescribeTable`, `UpdateTable` |
| Replicated write units for a 1 KB item, two Regions | Put 4, Update 3, Delete 3 | Put 2, Update 2, Delete 2 |
| Stream records per write | 2 | 1 |
| `aws:rep:deleting`, `aws:rep:updateregion`, `aws:rep:updatetime` | Written into items | Not written |
| TTL settings and TTL deletes | Not synchronized, not replicated | Synchronized and replicated |
| Auto scaling, GSI, encryption settings | Not synchronized | Synchronized |
| Metrics | `ReplicationLatency`, `PendingReplicationCount` | `ReplicationLatency` (MREC only) |

## Removed or Deprecated

`PendingReplicationCount` is not published. The `aws:rep:*` attributes are no longer maintained; code that reads them breaks after the upgrade.

## Worth Adopting

- MREC (default) for low-latency local writes with last-writer-wins conflicts; MRSC for RPO zero and cross-Region strong reads. Details and limits in [global-tables-and-streams](../global-tables-and-streams.md).
- Replica disassociation (MREC) to leave a Region without deleting data.
- Warm throughput settings that propagate to every replica.

## Upgrading Into This Series

Pre-checks:

1. Confirm the version: `aws dynamodb describe-global-table --global-table-name T --region <r>` succeeds only for 2017.11.29.
2. Grant `dynamodb:UpdateGlobalTableversion` in every Region with a replica.
3. Find code that reads `aws:rep:*` attributes or depends on two stream records per write, and change it.
4. Switch the table to on-demand for the upgrade, or raise the auto scaling minimums: auto scaling does not adjust capacity while the upgrade runs.

Upgrade: console, Tables, select the table, Global Tables tab, Update version, accept the requirements. Replicas keep serving reads and writes; `TableStatus` goes from `ACTIVE` to `UPDATING` and back. Expect minutes to hours depending on size and replica count. `ReplicationLatency` can spike or stop reporting during the upgrade.

Post-checks: `aws dynamodb describe-table --table-name T --query Table.GlobalTableVersion` returns `"2019.11.21"` in each Region; streams show one record per write; TTL is enabled consistently; alarms that used `PendingReplicationCount` are replaced.

Rollback: no downgrade is documented. Rehearse the code changes against a separate 2019.11.21 global table before upgrading production.

## Managed Service Notes

Global tables do not exist in DynamoDB local or ExtendDB (DynamoDB local has no Regions at client level). Test replication behavior in AWS accounts.
