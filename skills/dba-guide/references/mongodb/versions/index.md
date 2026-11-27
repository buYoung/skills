# MongoDB Versions

Checked: 2026-11-27 against the MongoDB lifecycle schedule (https://www.mongodb.com/legal/support-policy/lifecycles), the Software Support Policy (https://www.mongodb.com/legal/support-policy/software), and "MongoDB Versions and Upgrade Paths" (https://www.mongodb.com/docs/mongodb-versions/).

## Support Status

MongoDB numbers releases `X.Y.Z`. The support policy defines three server release types that matter here:

- Major release (`X.0`): supported 5 years from GA. Enterprise Advanced customers can buy a 2-year Extended Lifecycle Support (ELS) period.
- Minor release (`X.Y`, 8.2 and later): self-managed and Atlas Auto Upgrade deployments could run 8.2 and 8.3. Each minor has its own end date on the lifecycle page. Before 8.2, the same numbering was called a "rapid release" and was Atlas-only.
- Feature Update release (`X.5`, starting with the 9.x cycle): the annual minor release that self-managed and Atlas Manual Upgrade clusters can run. It has the same end-of-life and ELS eligibility as its major. On 2026-11-27 no Feature Update release exists yet. From 9.0 on, other minors go only to Atlas clusters on Auto Upgrades.

Self-managed server (Enterprise Advanced table on the lifecycle page). "MongoDB Versions and Upgrade Paths" states that each major version is supported for five years and that self-managed deployments must upgrade before end of life; applying the same dates to Community is an inference, since the lifecycle and support-policy pages do not mention Community:

| Series | Type | GA (lifecycle page / first patch in release notes) | End of life | Extended support | File |
| --- | --- | --- | --- | --- | --- |
| 9.0 | Major | September 2026 / 9.0.0 on 2026-09-28 | 2031-10-31 | ELS (2 years, EA) available for majors | [9.0](9.0.md) |
| 8.3 | Minor | May 2026 / 8.3.0 on 2026-05-04 | 2029-10-31 | not stated | [8.3](8.3.md) |
| 8.0 | Major | October 2024 / 8.0.0 on 2024-10-02 | 2029-10-31 | ELS (2 years, EA) available for majors | [8.0](8.0.md) |
| 7.0 | Major | August 2023 / 7.0.0 on 2023-08-15 | 2027-08-31 | ELS (2 years, EA) available for majors | [7.0](7.0.md) |
| 8.2 | Minor (ended) | September 2025 | 2026-07-31 | none | [8.2](8.2.md) |

8.2 is the most recent series that reached end of life before 2026-11-27. It is covered only because a deployment on 8.2 must leave it through 8.3. The last major to reach end of life was 6.0 (2025-07-31); it is not covered.

Atlas has separate tables on the same lifecycle page:

| Atlas track | Series | End of life |
| --- | --- | --- |
| Dedicated (major only) | 9.0 | 2031-10-31 |
| Dedicated (major only) | 8.0 | 2029-10-31 |
| Dedicated (major only) | 7.0 | 2027-08-31 |
| Auto Upgrade | 9.0 | TBD |
| Auto Upgrade | 8.3 | TBD, no sooner than October 2026 |
| Auto Upgrade | 8.2 | 2026-07-31 |

Latest public patches on 2026-11-27, from the release notes: 9.0.8 (2026-11-10), 8.3.17 (2026-11-10), 8.0.38 (2026-11-10), 7.0.48 (2026-11-10). The release notes also list Atlas-only patches, 8.0.39 and 7.0.49 (2026-11-18). The official `mongo` images for tags 9.0, 8.3, 8.0, and 7.0 reported 9.0.8, 8.3.17, 8.0.38, and 7.0.48.

Run the latest patch of a series. The release notes carry "Critical Advisories" tables of affected patch ranges, for example SERVER-131805 in 7.0.0-7.0.44, 8.0.0-8.0.33, and 8.3.0-8.3.12.

## Identify the Running Version

Run all of these in `mongosh`. The outputs shown were checked against the official images.

```javascript
db.version()                                   // "9.0.8"
db.adminCommand({ buildInfo: 1 }).version      // same string
db.adminCommand({ buildInfo: 1 }).modules      // [] on the Community image
db.adminCommand({ getParameter: 1, featureCompatibilityVersion: 1 })
// { featureCompatibilityVersion: { version: '9.0' }, ok: 1, ... }
db.serverStatus().storageEngine.name           // 'wiredTiger'
db.adminCommand({ getCmdLineOpts: 1 }).parsed  // effective startup options
db.hello()                                     // setName, isWritablePrimary, msg: 'isdbgrid' on mongos
```

How to read the results:

- Edition: `buildInfo.modules` is `[]` on the Community images. The buildInfo reference lists `enterprise` as a possible value, so an Enterprise build shows it there. Features documented as Enterprise-only (auditing, Kerberos, LDAP, encryption at rest, file copy based initial sync) fail or are missing on Community. The 8.3 and 9.0 images report `buildInfoAuthMode: 'requiresAuth'` (7.0 and 8.0 have no such parameter), and on a 9.0.8 container with a root user created, an unauthenticated `buildInfo` failed with code 13 `Command buildInfo requires authentication`. Check the edition as an authenticated user on 8.3 and 9.0. The server parameters page does not document `buildInfoAuthMode`.
- FCV: a binary can run with the previous series' FCV during an upgrade. The FCV, not the binary, decides which persisted features exist and whether a downgrade is still possible. Check it on every member. On 8.2+ `$currentOp` also reports a `versionContext` field holding the operation's FCV.
- Topology: in `hello()`, `msg: "isdbgrid"` means a `mongos`. `setName` means a replica set member. Neither means a standalone (the hello reference documents `isdbgrid` for `mongos`).
- Sharded clusters: run the checks on `mongos`, on each shard primary, and on the config server replica set. FCV is set through `mongos`.
- Atlas: the cluster's version and release cadence (a pinned major, or "Latest Version With Auto Upgrades") are shown in the Atlas UI. `atlas clusters describe <cluster>` prints an `MDB VER` column; `-o json` returns the full cluster document, which also shows the release cadence. `db.version()` works on Atlas too. Atlas Infinite clusters always run the latest 9.x; the project activity feed reports the exact version.
- MongoDB-compatible services (Amazon DocumentDB, Azure Cosmos DB for MongoDB) report a wire-protocol compatibility version, not a MongoDB server build. See [DocumentDB compatibility](../../documentdb/compatibility.md) and [Cosmos DB MongoDB compatibility](../../cosmos-db/mongodb-compatibility.md). Do not apply this reference to them.

## Upgrade Paths

Supported direct paths for self-managed deployments, from the per-version upgrade pages:

| From | To | Notes |
| --- | --- | --- |
| 7.0 (FCV 7.0) | 8.0 | Only path out of 7.0. Earlier majors must step through each major first. |
| 8.0 (FCV 8.0) | 8.3 | Direct; "Upgrade 8.0 to 8.3". |
| 8.2 (FCV 8.2) | 8.3 | Required way out of 8.2 if going forward. |
| 8.0 (FCV 8.0) | 9.0 | Direct; the 9.0 pages state "you must be running a 8.0 or 8.3 release". |
| 8.3 (FCV 8.3) | 9.0 | Direct. |
| 7.0 | 9.0 | Not supported. Go 7.0 → 8.0 → 9.0, with FCV raised to 8.0 in between. |

Rules from "MongoDB Versions and Upgrade Paths":

- Before 9.0 you cannot skip minor releases. To get from a minor to the next major, either upgrade through each remaining minor or downgrade to the previous major and then upgrade.
- Each step is a binary change followed by an FCV change. The FCV must equal the source series before you start the next step.
- Downgrades go only to the immediately preceding release (the previous major or minor) and cannot be chained. They require that the FCV was never raised, or was lowered first after removing backward-incompatible features. The 7.0 and 8.0 release notes add that binary downgrades are not supported for Community Edition and need MongoDB support for Enterprise after an FCV change. The 8.3 and 9.0 notes say "starting in MongoDB 8.3, you can downgrade ... to the immediately previous minor or major version". Read the downgrade page of the exact pair before relying on a downgrade.
- Atlas: a downgrade after a major upgrade is possible only if the FCV was pinned before the upgrade (pin lasts up to 4 weeks). Auto Upgrade and Infinite clusters cannot choose versions.

Generic procedure for a replica set (adapt per topology; sharded clusters have their own pages that also stop the balancer):

1. Pre-checks.
   - Read the target's release notes and compatibility-changes page. Then read the target version file here.
   - Confirm that every driver, ODM, and tool supports the target version.
   - Confirm FCV equals the source series on every member: `db.adminCommand({ getParameter: 1, featureCompatibilityVersion: 1 })`.
   - Confirm no member is in `ROLLBACK` or `RECOVERING` (`rs.status()`), and that no initial sync is running.
   - Check disk headroom and the oplog window (`rs.printReplicationInfo()`).
   - Patch the source to its latest patch release first.
2. Rehearsal. Restore a recent backup to a staging deployment with the same topology. Run the binary upgrade there and replay representative traffic. Compare explain plans for the top query shapes (from `$queryStats` or the slow log). Time the procedure.
3. The switch. This is a rolling restart: plan for one election and for the restart of each member.
   1. Upgrade the secondaries one at a time: `db.adminCommand({ shutdown: 1 })`, replace the binary, restart, and wait for `SECONDARY` in `rs.status()`.
   2. Run `rs.stepDown()` on the primary. Wait until another member is `PRIMARY`, then upgrade the old primary the same way.
   3. Leave FCV at the old value for a burn-in period. That keeps the downgrade path open.
   4. When downgrade is no longer expected, run `db.adminCommand({ setFeatureCompatibilityVersion: "<target>", confirm: true })` on the primary (on `mongos` for sharded clusters). It is idempotent, so retry it if it fails. Running it during an initial sync restarts that sync.
4. Post-checks.
   - Confirm FCV on each member.
   - Look for new startup warnings in the log.
   - Compare slow-query volume, `queues.execution` queueing, replication lag, and plan changes against the baseline.
   - Run `checkMetadataConsistency` on sharded clusters (from `mongos`).

## Outside the Covered Range

- Older than 7.0 (6.0, 5.0, 4.x): these are past end of life; 6.0 ended on 2025-07-31. Their documentation is under https://www.mongodb.com/docs/legacy/ and is no longer maintained. Read the release notes and compatibility-changes page of each major from the running version up to 7.0, and plan one major per step. Claims here that may not hold on them:
  - the dynamic ticket algorithm (7.0+);
  - `queues.execution` (8.0+, previously `wiredTiger.concurrentTransactions`);
  - query settings and `queryShapeHash` (8.0+);
  - `$queryStats`;
  - `analyzeShardKey` (7.0+);
  - majority write acknowledgment on oplog write (8.0+);
  - the `confirm: true` requirement on `setFeatureCompatibilityVersion` (7.0+).
- Newer than 9.0 (a 9.x minor on Atlas Auto Upgrade or Infinite, the 9.5 Feature Update release, or 10.0): read the release notes and compatibility page for that series, starting from https://www.mongodb.com/docs/manual/release-notes/. Treat changed defaults, new error codes, and `$queryStats` and serverStatus field names as unverified until checked.
- Any answer about a server outside 7.0-9.0 must state the version gap and which statements were not checked for that version.

## Sources

Lifecycle and versions:
- MongoDB lifecycle schedules — https://www.mongodb.com/legal/support-policy/lifecycles — checked 2026-11-27
- MongoDB Software Support Policy — https://www.mongodb.com/legal/support-policy/software — checked 2026-11-27
- MongoDB Versions and Upgrade Paths — https://www.mongodb.com/docs/mongodb-versions/ — checked 2026-11-27
- Release Notes index — https://www.mongodb.com/docs/manual/release-notes/ — checked 2026-11-27
- Legacy documentation — https://www.mongodb.com/docs/legacy/ — checked 2026-11-27

Release notes, compatibility, upgrade and downgrade:
- 9.0 release notes — https://www.mongodb.com/docs/manual/release-notes/9.0/ — checked 2026-11-27
- 9.0 compatibility changes — https://www.mongodb.com/docs/manual/release-notes/9.0-compatibility/ — checked 2026-11-27
- Upgrade 8.3 replica set to 9.0 — https://www.mongodb.com/docs/manual/release-notes/9.0-upgrade-replica-set/ — checked 2026-11-27
- Upgrade 8.0 replica set to 9.0 — https://www.mongodb.com/docs/manual/release-notes/9.0-upgrade-from-8.0-replica-set/ — checked 2026-11-27
- Downgrade 9.0 to 8.3 — https://www.mongodb.com/docs/manual/release-notes/9.0-downgrade/ — checked 2026-11-27
- Downgrade 9.0 replica set to 8.3 — https://www.mongodb.com/docs/manual/release-notes/9.0-downgrade-replica-set/ — checked 2026-11-27
- 8.3 release notes — https://www.mongodb.com/docs/manual/release-notes/8.3/ — checked 2026-11-27
- 8.3 release notes, versioned copy with 8.2 changes — https://www.mongodb.com/docs/v8.3/release-notes/8.3/ — checked 2026-11-27
- 8.3 compatibility changes (manual) — https://www.mongodb.com/docs/manual/release-notes/8.3-compatibility/ — checked 2026-11-27
- 8.3 compatibility changes incl. 8.2 — https://www.mongodb.com/docs/v8.3/release-notes/8.3-compatibility/ — checked 2026-11-27
- Upgrade 8.0 to 8.3 — https://www.mongodb.com/docs/manual/release-notes/8.3-upgrade-from-8.0/ — checked 2026-11-27
- 8.0 release notes — https://www.mongodb.com/docs/manual/release-notes/8.0/ — checked 2026-11-27
- 8.0 compatibility changes — https://www.mongodb.com/docs/manual/release-notes/8.0-compatibility/ — checked 2026-11-27
- Upgrade 7.0 replica set to 8.0 — https://www.mongodb.com/docs/manual/release-notes/8.0-upgrade-replica-set/ — checked 2026-11-27
- 7.0 release notes — https://www.mongodb.com/docs/manual/release-notes/7.0/ — checked 2026-11-27
- 7.0 compatibility changes — https://www.mongodb.com/docs/manual/release-notes/7.0-compatibility/ — checked 2026-11-27

Manual topic pages:
- Data modeling — https://www.mongodb.com/docs/manual/data-modeling/ — checked 2026-11-27
- Data modeling best practices — https://www.mongodb.com/docs/manual/data-modeling/best-practices/ — checked 2026-11-27
- Specify validation level — https://www.mongodb.com/docs/manual/core/schema-validation/specify-validation-level/ — checked 2026-11-27
- Handle invalid documents — https://www.mongodb.com/docs/manual/core/schema-validation/handle-invalid-documents/ — checked 2026-11-27
- Limits and thresholds — https://www.mongodb.com/docs/manual/reference/limits/ — checked 2026-11-27
- ESR guideline — https://www.mongodb.com/docs/manual/tutorial/equality-sort-range-guideline/ — checked 2026-11-27
- Explain results — https://www.mongodb.com/docs/manual/reference/explain-results/ — checked 2026-11-27
- Index builds on populated collections — https://www.mongodb.com/docs/manual/core/index-creation/ — checked 2026-11-27
- Transactions — https://www.mongodb.com/docs/manual/core/transactions/ — checked 2026-11-27
- Transactions production considerations — https://www.mongodb.com/docs/manual/core/transactions-production-consideration/ — checked 2026-11-27
- Default MongoDB read/write concerns — https://www.mongodb.com/docs/manual/reference/mongodb-defaults/ — checked 2026-11-27
- Replica set oplog — https://www.mongodb.com/docs/manual/core/replica-set-oplog/ — checked 2026-11-27
- Replica set elections — https://www.mongodb.com/docs/manual/core/replica-set-elections/ — checked 2026-11-27
- Replica set arbiter — https://www.mongodb.com/docs/manual/core/replica-set-arbiter/ — checked 2026-11-27
- Choose a shard key — https://www.mongodb.com/docs/manual/core/sharding-choose-a-shard-key/ — checked 2026-11-27
- Reshard a collection — https://www.mongodb.com/docs/manual/core/sharding-reshard-a-collection/ — checked 2026-11-27
- analyzeShardKey — https://www.mongodb.com/docs/manual/reference/command/analyzeShardKey/ — checked 2026-11-27
- Backup methods — https://www.mongodb.com/docs/manual/core/backups/ — checked 2026-11-27
- Back up with filesystem snapshots — https://www.mongodb.com/docs/manual/tutorial/backup-with-filesystem-snapshots/ — checked 2026-11-27
- Back up a sharded cluster with database dumps — https://www.mongodb.com/docs/manual/tutorial/backup-sharded-cluster-with-database-dumps/ — checked 2026-11-27
- mongodump — https://www.mongodb.com/docs/database-tools/mongodump/ — checked 2026-11-27
- WiredTiger storage engine — https://www.mongodb.com/docs/manual/core/wiredtiger/ — checked 2026-11-27
- Production notes — https://www.mongodb.com/docs/manual/administration/production-notes/ — checked 2026-11-27
- Configuration file options — https://www.mongodb.com/docs/manual/reference/configuration-options/ — checked 2026-11-27
- Security checklist — https://www.mongodb.com/docs/manual/administration/security-checklist/ — checked 2026-11-27
- Auditing — https://www.mongodb.com/docs/manual/core/auditing/ — checked 2026-11-27
- $queryStats — https://www.mongodb.com/docs/manual/reference/operator/aggregation/queryStats/ — checked 2026-11-27
- db.setProfilingLevel() — https://www.mongodb.com/docs/manual/reference/method/db.setProfilingLevel/ — checked 2026-11-27

Atlas:
- MongoDB versions in Atlas — https://www.mongodb.com/docs/atlas/atlas-versions/ — checked 2026-11-27
- Upgrade major MongoDB version for a cluster — https://www.mongodb.com/docs/atlas/tutorial/major-version-change/ — checked 2026-11-27
- Unsupported commands — https://www.mongodb.com/docs/atlas/reference/unsupported-commands/ — checked 2026-11-27
- Atlas Infinite overview — https://www.mongodb.com/docs/atlas/infinite/atlas-infinite-landing/ — checked 2026-11-27
- Cluster maintenance — https://www.mongodb.com/docs/atlas/tutorial/cluster-maintenance-window/ — checked 2026-11-27
- Cloud backup overview — https://www.mongodb.com/docs/atlas/backup/cloud-backup/overview/ — checked 2026-11-27
- Backup policies — https://www.mongodb.com/docs/atlas/backup/cloud-backup/configure-backup-policy/ — checked 2026-11-27
- Point-in-time restore — https://www.mongodb.com/docs/atlas/recover-pit-continuous-cloud-backup/ — checked 2026-11-27
- Database users — https://www.mongodb.com/docs/atlas/security-add-mongodb-users/ — checked 2026-11-27
- Atlas user roles — https://www.mongodb.com/docs/atlas/reference/user-roles/ — checked 2026-11-27
- Performance Advisor — https://www.mongodb.com/docs/atlas/performance-advisor/ — checked 2026-11-27

Container evidence:
- Official `mongo` images 7.0, 8.0, 8.3, 9.0 (image digests in the coverage record, `updates/2026-11-27-initial-coverage.md`): version and FCV output, `getParameter` dumps, explain output, transaction and validation errors on a single-node replica set, and the 9.0 server log — run 2026-11-27
