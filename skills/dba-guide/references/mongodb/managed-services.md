# MongoDB Managed Services (Atlas)

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)). Only Atlas behavior stated in the Atlas documentation is described here.

MongoDB-compatible services from other vendors are not MongoDB server builds. See [Amazon DocumentDB compatibility](../documentdb/compatibility.md) and [Azure Cosmos DB for MongoDB compatibility](../cosmos-db/mongodb-compatibility.md).

## Editions and tiers

| | Atlas Core | Atlas Infinite (public preview) |
| --- | --- | --- |
| Architecture | compute and storage on the same node (WiredTiger behavior as in this reference) | compute separated from a MongoDB-managed storage layer; failover coordinated by the storage layer; read-only nodes need no initial sync |
| Tiers | Free, Flex, Dedicated M10+ | M10-M60 General, M40-M60 Low-CPU (preview) |
| Versions | choose a major (Manual Upgrades) or Auto Upgrades | always latest 9.x via Auto Upgrades; cannot choose |
| Sharding | yes | not in preview |
| Profiler | yes on M10+ (but `setProfilingLevel` is limited; see below) | cannot be enabled |
| `mongodump --oplog` / `mongorestore --oplogReplay` | yes | not supported |
| Switch edition | — | not possible after creation; no live migration or backup restore between editions |

The edition cannot be changed later; decide before creating the cluster. The storage engine sections of [configuration](configuration.md) apply to Atlas Core and self-managed deployments only.

## What Atlas takes over and what it restricts

Atlas runs provisioning, replication, failover, patching, backups, and monitoring. In exchange, administrative commands are limited. These commands appear in the Atlas "unsupported commands" tables; the per-tier marks did not extract cleanly, so check the page for a given tier:

- `setParameter` (and helpers that use it, such as `db.setLogLevel()`), `shutdown`, `fsync`/`fsyncLock`/`fsyncUnlock`, `logRotate`, `setFeatureCompatibilityVersion`, `compact`, `autoCompact`;
- `replSetReconfig` / `rs.reconfig()`;
- `setProfilingLevel` (shell helper);
- `createUser` / `db.createUser()`.

Explicit per-tier limits:

| Tier | Limits |
| --- | --- |
| Free / Flex | `killOp` only for your own operations; `getParameter` only `authSchemaVersion` and `authenticationMechanisms`; `aggregate` `maxTimeMS` capped at 300 s, `allowDiskUse` ignored, no `$accumulator`, `$function`, `$$USER_ROLES`; no `$where`; restricted `serverStatus`; 500 connections |
| M10+ Core | `killOp` only for your own operations; `killAllSessions` needs `killAnySession` or the `killOpSession` role; `reshardCollection`, `unshardCollection`, `rewriteCollection` only on M30+ sharded clusters |
| M10+ Infinite | as Core for `killOp`/`killAllSessions`; `profile` only at level 0 |

Consequences for common self-managed procedures:

- Parameters such as `maxTransactionLockRequestTimeoutMillis` cannot be changed with `setParameter`. The transaction guide says to contact Atlas Support. Transaction lifetime has its own Atlas setting ("Set Transaction Lifetime").
- `maxIndexBuildMemoryUsageMegabytes` cannot be modified. Atlas sets index build defaults per tier.
- The `fsyncLock`-based backups in [backup-and-recovery](backup-and-recovery.md) do not apply. Use Cloud Backup.
- FCV is managed by Atlas (pinning only; see below).
- Per-node connection limits by tier, from the limits page: M10 1500; M20/M30 3000; M40 6000; M50 16000; M60 32000; M140 96000; M200/M300 128000. The page has conflicting values for M80 (64000 and 96000).

## Versions, upgrades, FCV

- Two cadences:
  - Manual Upgrades: pick a major (7.0, 8.0, 9.0). Patches still roll out automatically.
  - Latest Version With Auto Upgrades: Atlas delivers majors, minors (8.3, 9.x), and patches, and advances FCV after its own rollout checks.
- Switching:
  - Manual → Auto is allowed at any time.
  - Auto → Manual is allowed only between a new major's release and its first minor.
- Major upgrade paths offered: 7.0 → 8.0, 8.0 → 9.0, and 8.0 or 9.0 → Auto Upgrades. You can upgrade only one major at a time. Atlas performs it as a rolling change with at least one election.
- Downgrade is possible only if the FCV was pinned before the upgrade. The pin holds the old FCV for up to 4 weeks. You cannot upgrade two versions past a pinned FCV. Without a pin, the only way back is to terminate and re-create the cluster, for example a staging cluster.
- End of life:
  - Atlas emails at least six months before a version's EOL, and later stops new deployments on it.
  - Clusters still on the version after the stated date are upgraded to the current default target version, which is not always the next major, during the maintenance window.
  - Atlas Dedicated EOL dates: 7.0 on 2027-08-31, 8.0 on 2029-10-31, 9.0 on 2031-10-31.
- Free and Flex clusters stay on a major version (8.0 on 2026-11-27), are upgraded automatically, and cannot be downgraded.
- Live Migration and `mongosync` do not work on minor versions, so they are not available with Auto Upgrades.
- Before a major upgrade:
  - Atlas requires `Project Owner` and a healthy cluster.
  - Finish any on-demand snapshot first.
  - For 8.0, check storage capacity and enable storage auto-scaling (scales at 90% disk use) because of write-blocking behavior.
  - Rehearse on a staging cluster restored from a production snapshot, and test primary failover there.

## Maintenance

- Maintenance windows, protected hours, and maintenance waves are project-level settings for Dedicated (M10+) clusters. Free and Flex are maintained automatically.
- Maintenance is rolling and needs at least one election per replica set. With low disk IOPS, expect brief degradation while the cache warms.
- Deferral: "Defer 1 Week" postpones the scheduled maintenance. Automatic deferral moves each maintenance by one week, so maintenance effectively runs every two weeks; you get one extra manual deferral. Automatic deferral is unavailable when maintenance waves are used in the organization.
- Protected hours: a daily span of up to 18 hours with no standard updates.
- Urgent maintenance (for example zero-day security patches) ignores windows, protected hours, and waves.
- Waves: Wave 1 through Last Wave, at least 48 hours apart, and every project in a wave finishes before the next starts. Assigning Dev → Wave 1, QA → Wave 2, and Prod → Last Wave guarantees at least seven days between environments. On Auto Upgrades, waves are the only ordering control.
- Applications must handle elections. Use retryable writes, transaction retry logic, and Atlas "Test Primary Failover" before relying on them.

## Backups and restore

- Cloud Backup on M10+ uses the cloud provider's native snapshots (AWS, Azure, Google Cloud). Optional multi-region snapshot distribution copies snapshots and oplogs to other regions.
- Default policy (snapshots at 18:00 UTC):

  | Policy | Frequency | Retention |
  | --- | --- | --- |
  | Hourly | every 6 h (non-NVMe), every 12 h (NVMe) | 7 days |
  | Daily | daily | 7 days |
  | Weekly | Saturday | 4 weeks |
  | Monthly | last day of month | 12 months |
  | Yearly | 1 December | 1 year |

- Continuous Cloud Backup adds point-in-time restore:
  - The restore window is set in the backup policy and cannot exceed the hourly snapshot retention.
  - Restore points: date/time at one-minute precision, or an oplog timestamp at one-second precision.
  - Enabling it raises cost. Disabling it deletes the continuous backup history.
  - The target cluster must run the same MongoDB version as the snapshot.
  - Atlas Infinite always has a 24-hour continuous window and uses its own restore procedure.
- Sharded clusters are backed up per shard. After adding or removing a shard, older snapshots cannot be restored to that cluster, only to a cluster with matching topology.
- A Backup Compliance Policy protects backups from deletion. With it enabled, only MongoDB Support can shorten the restore window.
- Restores need `Project Backup Manager`, `Project Backup Recovery Operator` (PIT restore), or `Project Owner`.
- Infinite preview gaps: no collection-level restore, no snapshot download, no cross-organization restore, no snapshot distribution.
- Verify restores the same way as self-managed (see [backup-and-recovery](backup-and-recovery.md#verify-restores)): restore to a separate cluster and compare.

## Security differences

- Database users are managed only through the Atlas UI, CLI (`atlas dbusers create|list|describe|update|delete`), Admin API, or supported integrations. Atlas rolls back user changes made any other way. In the UI each user gets one built-in role, plus any number of custom roles and specific privileges. Built-in roles apply to all clusters in the project unless access is restricted per cluster.
- Authentication:
  - SCRAM (default; SCRAM-SHA-256).
  - Atlas-managed or self-managed X.509. Atlas-managed certificates cannot be revoked, only the user deleted; an alert comes 30 days before expiry.
  - OIDC Workforce/Workload identity (MongoDB 7.0+).
  - AWS IAM.
  - LDAP (deprecated since MongoDB 8.0).
- Temporary users expire after 6 hours, 1 day, or 1 week.
- Each project allows at most 100 database users.
- Auditing is available on M10+ (configured in Atlas).
- Atlas Infinite encrypts all data, with CMK through AWS KMS in preview.

## Diagnostics that replace self-managed tools

| Self-managed | Atlas replacement |
| --- | --- |
| Slow query log, profiler | Query Profiler; Performance Advisor (M10+) uses slow-operation data with a dynamically managed threshold by default (opt out for a fixed 100 ms); Namespace Insights for per-collection latency |
| Index advice by hand | Performance Advisor suggestions ranked by wasted bytes read, with execution count, docs scanned/returned, in-memory sorts; can create the index (optionally rolling, not for unique indexes) |
| `setParameter` / `setProfilingLevel` | project settings, or Atlas Support |
| Log files on disk | log downloads (not on Infinite in preview) |
| `mongostat`, `mongotop` | work on Core; incomplete on Infinite |

The Atlas CLI exposes `atlas performanceAdvisor slowQueryLogs list`, `suggestedIndexes list`, and `namespaces list`. `$queryStats` is enabled on M10+ (see [monitoring](monitoring.md#querystats)). The Performance Advisor gives no suggestions for time series collections, or when the log timestamp format is `ctime`.
