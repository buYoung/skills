# Global Tables Version 2017.11.29 (Legacy)

Checked: 2026-11-27 against https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/globaltables.V1.html and https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_versions.html

Read this when `describe-global-table` succeeds for a table, which means it is a legacy global table.

## Lifecycle

Legacy. The documentation says it "should be avoided for new global tables" and recommends upgrading to [2019.11.21](global-tables-2019.11.21.md). Available in 11 Regions only. No end-of-support date is published.

## Removed or Deprecated

Everything that depends on the current version is absent: MREC/MRSC modes, multi-account replication, replica disassociation, warm throughput on global tables (documented for 2019.11.21 only), and adding replicas to a table that holds data (all replicas must be empty when a Region is added).

## Upgrading Into This Series

Not applicable; this is the upgrade source. Behavior that differs and affects operations while you still run it:

- Each write produces two stream records, and items carry `aws:rep:deleting`, `aws:rep:updateregion`, `aws:rep:updatetime`.
- TTL, auto scaling, GSI, and encryption settings are not synchronized; configure each Region and check each Region.
- TTL deletes are not replicated; expired items can disappear in one Region and remain in another.
- Replication consumes more write units than the current version (for a 1 KB item in two Regions: put 4, update 3, delete 3).
- Monitor `PendingReplicationCount` and `ReplicationLatency`.

Manage it with `create-global-table`, `describe-global-table`, `update-global-table`, `describe-global-table-settings`, `update-global-table-settings`, `list-global-tables`.
