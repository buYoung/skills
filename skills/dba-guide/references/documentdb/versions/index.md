# Amazon DocumentDB Versions

Checked: 2026-11-27 against the official lifecycle page [Amazon DocumentDB engine version support dates](https://docs.aws.amazon.com/documentdb/latest/devguide/docdb-version-support-dates.html) and [Amazon DocumentDB Extended Support](https://docs.aws.amazon.com/documentdb/latest/devguide/extended-support.html).

Amazon DocumentDB is an AWS-only managed service. It implements the MongoDB wire protocol and a subset of the MongoDB API on an AWS storage engine; it is not MongoDB. There is no self-hosted build and no official container image, so nothing in this reference was checked against a running server. Its engine numbers name the MongoDB API level it emulates, not a MongoDB server release, and its lifecycle is separate from MongoDB's.

## Support Status

| Series | MongoDB API level | Release type | GA | End of standard support | Extended Support | File |
| --- | --- | --- | --- | --- | --- | --- |
| 8.0 | MongoDB 8.0 drivers; also supports applications built on API 6.0 and 7.0 | Current major. Minor versions 8.0.0 to 8.0.3. No LTS designated yet | 14 Nov 2025 | Not announced (page shows N/A) | Not announced | [8.0](8.0.md) |
| 5.0 | MongoDB 5.0 | Major. 5.0.0 is the LTS minor version. Minors 5.0.1 and 5.0.2 exist | 1 Mar 2023 | Not announced (N/A) | Not announced | [5.0](5.0.md) |
| 4.0 | MongoDB 4.0 | Major, engine patches only (no minor versions) | 9 Nov 2020 | Not announced (N/A) | Not announced | [4.0](4.0.md) |
| 3.6 | MongoDB 3.6 | Major, engine patches only. Out of standard support | 9 Jan 2019 | 30 Mar 2026 | Enrolled automatically from 31 Mar 2026; year-3 pricing from 31 Mar 2028; ends 30 Mar 2029. Year-1 pricing start conflicts between pages, see below | [3.6](3.6.md) |

- N/A on the lifecycle page means AWS has not published a date. It does not mean the version will be supported indefinitely. Check the page again before you plan a long-lived cluster on 4.0.
- Year-1 Extended Support pricing for 3.6 starts on 31 Mar 2026 according to the support-dates page and on 1 Jul 2026 according to the Extended Support page. Both pages say that enrollment starts on 31 Mar 2026. Quote both dates if the bill is the question.
- After Extended Support ends, AWS upgrades the cluster to a supported engine version itself. Extended Support covers critical and high CVE fixes, critical bug fixes, and support cases. It does not add features.
- Elastic clusters are a separate cluster type and have no numbered engine series of their own. They speak a MongoDB 5.0-compatible wire protocol, they are not available on engine 8.0, and they are not offered in China or AWS GovCloud Regions. See [compatibility.md](../compatibility.md#elastic-clusters).
- Serverless is an instance class (`db.serverless`) inside an instance-based cluster. It is available on 5.0 and 8.0 only, and it is not a separate version.

### Version numbering

| Identifier | Form | Example | Where it appears |
| --- | --- | --- | --- |
| Engine version | `major.major.minor` | `5.0.1`, `8.0.3` | `EngineVersion` in `describe-db-clusters`; the value you pass to `--engine-version` |
| Engine patch version | `<prefix>.0.<patch>` | `3.0.17983` | `getEngineVersion` command; release notes |

| Patch prefix | Engine series |
| --- | --- |
| `1.0.x` | 3.6 |
| `2.0.x` | 4.0 |
| `3.0.x` | 5.0 |
| `4.0.x` | 8.0 |

Minor versions exist only from 5.0 on. On 3.6 and 4.0 the engine version is always `3.6.0` or `4.0.0`, and changes arrive as patches. A minor version never applies itself. You upgrade to it by modifying the cluster, and you cannot downgrade afterward. Engine patches come in three categories: optional (never auto-applied), required (auto-applied in the cluster maintenance window after `AutoAppliedAfterDate`, about 30 days after release), and forced (applied outside the window after `ForcedApplyDate`). Source: [Maintaining Amazon DocumentDB](https://docs.aws.amazon.com/documentdb/latest/devguide/db-instance-maintain.html).

The minor-version calendar on the lifecycle page lists only 5.0.0 (LTS, dated 16 Feb 2026) and 5.0.1 (8 Jun 2026). The release notes also document 5.0.2 (28 Sep 2026), 8.0.1 (first entry 13 Jul 2026), 8.0.2 (28 Sep 2026), and 8.0.3 (11 Nov 2026). The MVU page lists 8.0.0 through 8.0.3 as upgrade targets. Use `describe-db-engine-versions` in the target Region to find out which minor versions you can actually choose there.

## Identify the Running Version

Run these checks before you answer any version-dependent question. Record the cluster type, the engine version, the engine patch version, and the planner version.

1. Engine version and cluster type (instance-based cluster):

   ```
   aws docdb describe-db-clusters \
     --db-cluster-identifier mycluster \
     --query 'DBClusters[0].[Engine,EngineVersion,DBClusterParameterGroup,StorageType]'
   ```

   `Engine` is `docdb`. `EngineVersion` is, for example, `5.0.0` or `8.0.2`. A parameter group named `default.docdb5.0` or `default.docdb8.0` means that the defaults apply and none of the parameters can be changed in that group. Look for `PendingModifiedValues.EngineVersion` in the full output. It shows an upgrade that is scheduled for the next maintenance window, and the console does not display it.

2. Engine patch version, from a shell connection:

   ```
   db.runCommand({getEngineVersion: 1})
   ```

   Before 5.0.2 and 8.0.2, the result holds the patch version only, for example `{ "engineVersion" : "3.0.17983", "ok" : 1 }`. From 5.0.2 and 8.0.2 on, it returns `engine-version+patch-version`, for example `5.0.2+3.0.12345` or `8.0.2+4.0.12345`. Update any script that parses this output when you move to those versions. Read the series from the patch prefix (see the table above).

   Inference, not stated in the documentation: `getEngineVersion` is a DocumentDB-specific command, so if it succeeds you are on DocumentDB and not on MongoDB. A MongoDB server would be expected to reject it as an unknown command.

3. Query planner in effect (5.0 and 8.0):

   ```
   aws docdb describe-db-cluster-parameters \
     --db-cluster-parameter-group-name my-params \
     --query "Parameters[?ParameterName=='planner_version'].[ParameterValue,Source]"
   ```

   In a shell, `explain()` output shows `queryPlanner.plannerVersion`. The parameter reference names the parameter `planner_version`, but the planner v2 and v3 pages call it `plannerVersion`. Use the name that `describe-db-cluster-parameters` returns.

4. LTS status (5.0 only): the cluster is on LTS when `EngineVersion` is `5.0.0` and the patch version is `3.0.17983` or later ([LTS page](https://docs.aws.amazon.com/documentdb/latest/devguide/docdb-lts-release.html)).

5. Serverless platform version, if the cluster uses `db.serverless` instances: read `ServerlessV2PlatformVersion` in `describe-db-clusters` output. Platform version 4 is newer, and existing clusters move to it through the `serverless-platform-version-update` maintenance action.

6. Elastic clusters have no engine-version field. Identify them with:

   ```
   aws docdb-elastic get-cluster --cluster-arn <elastic-cluster-arn> \
     --query 'cluster.[clusterName,status,shardCount,shardCapacity,shardInstanceCount]'
   ```

   Treat an elastic cluster as MongoDB 5.0 wire-protocol compatible, with the elastic column of the [supported API tables](https://docs.aws.amazon.com/documentdb/latest/developerguide/mongo-apis.html).

7. Versions available in a Region, and valid upgrade targets:

   ```
   aws docdb describe-db-engine-versions --engine docdb \
     --query 'DBEngineVersions[].[EngineVersion,DBParameterGroupFamily]'

   aws docdb describe-db-engine-versions --engine docdb --engine-version 5.0.0 \
     --query 'DBEngineVersions[].ValidUpgradeTarget[].[EngineVersion,IsMajorVersionUpgrade]'
   ```

8. Pending patches and OS updates:

   ```
   aws docdb describe-pending-maintenance-actions \
     --filters Name=db-cluster-id,Values=mycluster
   ```

There is no documented `featureCompatibilityVersion` in DocumentDB. The major engine version is the compatibility level, and it changes only through a major version upgrade or a migration. The supported-APIs page doesn't list `setFeatureCompatibilityVersion`, and no page documents an FCV. To see it on a cluster, run `db.adminCommand({getParameter: 1, featureCompatibilityVersion: 1})` and expect an error or no FCV value.

Do not judge compatibility from the driver's server-version handshake or from `buildInfo`. The developer guide does not document what version string those return on each engine. To see the difference on your cluster, compare `db.version()` with `aws docdb describe-db-clusters --query 'DBClusters[].EngineVersion'`. Use the engine version, and use the [supported APIs page](https://docs.aws.amazon.com/documentdb/latest/developerguide/mongo-apis.html) for feature checks.

## Upgrade Paths

### Supported paths

| From | To | Method | Notes |
| --- | --- | --- | --- |
| 3.6 | Any published 5.0 or 8.0 minor | In-place MVU | Direct 3.6/4.0 to 8.0 MVU available since 31 Aug 2026. You do not need to stop at a `.0` minor first |
| 4.0 | Any published 5.0 or 8.0 minor | In-place MVU | Same as above |
| 5.0.0, 5.0.1 | 8.0.0, 8.0.1, 8.0.2, 8.0.3 | In-place MVU | Available since 20 Apr 2026 |
| 5.0.2 | 8.0.2, 8.0.3 | In-place MVU | A 5.0.2 cluster cannot go to 8.0.0 or 8.0.1 |
| 5.0.x | later 5.0.y | Minor version upgrade (`modify-db-cluster --engine-version`) | One-way, brief downtime |
| 8.0.x | later 8.0.y | Minor version upgrade | One-way, brief downtime |
| Any instance-based version | Any newer version, or an elastic cluster | AWS DMS full load + CDC, or `mongodump`/`mongorestore` | Use this for global clusters, for near-zero-downtime cutover, or for cross-type moves |
| 3.6 | 4.0 | DMS or dump/restore | The MVU table does not list 4.0 as an MVU target |

Sources: [In-place MVU](https://docs.aws.amazon.com/documentdb/latest/devguide/docdb-mvu.html), [minor version upgrade](https://docs.aws.amazon.com/documentdb/latest/devguide/docdb-minor-version-upgrade.html), [upgrading with DMS](https://docs.aws.amazon.com/documentdb/latest/devguide/docdb-migration.versions.html).

### Limits

- There is no downgrade path, neither for major nor for minor versions. To roll back, restore the pre-upgrade snapshot to a new cluster, then repoint the application. You lose writes made after the snapshot.
- In-place MVU is not supported for global clusters or elastic clusters. For a global cluster, remove the secondaries, run the MVU on the now-regional primary, and add secondaries back with the same names to keep their endpoints. Re-seeding the secondaries costs I/O.
- Point-in-time restore cannot cross engine versions. For example, you cannot restore a 3.6 cluster to a 4.0 point in time.
- Minor upgrades in a global cluster: upgrade the secondary clusters before the primary.

### Generic procedure

1. Pre-checks.
   - Read the target version file ([4.0](4.0.md), [5.0](5.0.md), [8.0](8.0.md)) and [compatibility.md](../compatibility.md) for behavior changes that affect your queries.
   - Move any `db.r4.*` instance to `db.r5` or newer. 4.0 and later do not support r4.
   - Scale a burstable primary (`db.t3.medium`, `db.t4g.medium`) to at least `db.r5.large` or `db.r6g.large`. The MVU limits indexes on burstable instances: 3,000 on `db.t4g.medium` and 10,000 on `db.t3.medium`.
   - For a serverless writer, set the maximum DCU in `ServerlessV2ScalingConfiguration` to at least 3.
   - Apply pending OS maintenance first. Apply pending engine patches before that, because they can hide OS patches.
   - For 5.0 to 8.0 only: find every partial index whose `partialFilterExpression` uses `$type` with `binData`, `bool`, `date`, `double`, `decimal`, `array`, or a numeric type code. Drop it before the upgrade and recreate it afterward, or the upgrade fails.
   - Create a custom cluster parameter group in the target family (`docdb5.0` or `docdb8.0`) and copy over your non-default settings: `tls`, `audit_logs`, `profiler*`, `change_stream_log_retention_duration`, `ttl_monitor`. If you do not name one, the default group of the target family is used.
   - Check that the drivers work with the target: 5.0 and 8.0 need a driver compatible with MongoDB 5.0 or later. 8.0 and 5.0.1 or later need TLS 1.2 or later. On 8.0.2 and later you can drop `retryWrites=false`; before that you must keep it.
   - Take a manual snapshot. The MVU also creates `preupgrade-<cluster>-<from>-to-<to>-<timestamp>`, and that snapshot is not deleted automatically.
2. Rehearsal. Clone the cluster ([cloning](https://docs.aws.amazon.com/documentdb/latest/devguide/db-cluster-cloning.html)). A clone costs no extra storage until you write to it. Give the clone the same instance count as production so the downtime estimate is realistic. Run the MVU on the clone, measure the downtime, and run the application test suite and the critical queries with `explain("executionStats")` against it.
3. Switch. This step causes downtime: the cluster is unavailable and reboots several times. Schedule it in a low-traffic window.

   ```
   aws docdb modify-db-cluster \
     --db-cluster-identifier mycluster \
     --allow-major-version-upgrade \
     --engine-version 8.0.3 \
     --db-cluster-parameter-group-name my-docdb80-params \
     --apply-immediately
   ```

   The MVU page writes this flag as `--cluster-parameter-group`. AWS CLI 2.42.4 rejects that spelling with `Unknown options: --cluster-parameter-group` and suggests `--db-cluster-parameter-group-name`, the option used above and elsewhere in the guide.

   Follow progress with `aws docdb describe-events --source-identifier mycluster --source-type db-cluster`. The final event is "Database cluster engine major version has been upgraded". If the upgrade fails, AWS rolls it back automatically and reports "Database cluster is in a state that cannot be upgraded".
4. Post-checks.
   - Wait for the event "Index metadata refresh process completed". This can take up to two hours. Until then, do not reboot, fail over, or scale the writer. Query plans may be slow during the refresh. Contact AWS Support if the refresh has not finished after three hours.
   - Confirm `EngineVersion` and `getEngineVersion`.
   - If the source was 3.6 or 4.0, rebuild indexes with `reIndex`. This is optional and costs I/O.
   - Tag clusters that came from 3.6. They keep the 3.6 behavior for numeric comparisons inside subdocuments.
   - Take a fresh manual snapshot.
   - Update drivers if you want to use new features.

## Outside the Covered Range

- Older than 3.6: no such engine exists. 3.6 was the first DocumentDB engine.
- 3.6 after 30 Mar 2029: AWS upgrades the cluster itself. Find out which version it landed on with the identification steps above before you rely on any 3.6 statement.
- Newer than covered (for example 8.0.4 or later, or a new major such as a 9.x line): read the [release notes](https://docs.aws.amazon.com/documentdb/latest/devguide/release-notes.html), the [compatibility page](https://docs.aws.amazon.com/documentdb/latest/devguide/compatibility.html), the [supported APIs page](https://docs.aws.amazon.com/documentdb/latest/developerguide/mongo-apis.html), and the [features by version table](https://docs.aws.amazon.com/documentdb/latest/devguide/docdb-engine-version-supportability.html).
- Claims in this reference most likely to go stale: unsupported operators and stages (AWS adds them in minor versions and patches); the default planner and planner limitations; retryable-write support; elastic cluster limitations; which features are missing on 8.0 compared with 5.0 (elastic clusters, LTS); Performance Insights availability; the lifecycle dates themselves.
- Your answer must state the version gap. For example: "This reference covers through 8.0.3 as of 2026-11-27; your cluster reports 8.0.5, so verify X against the 8.0.5 release notes."

## Sources

- Amazon DocumentDB engine version support dates, https://docs.aws.amazon.com/documentdb/latest/devguide/docdb-version-support-dates.html, checked 2026-11-27
- Amazon DocumentDB Extended Support, https://docs.aws.amazon.com/documentdb/latest/devguide/extended-support.html, checked 2026-11-27
- Using a long-term support (LTS) release, https://docs.aws.amazon.com/documentdb/latest/devguide/docdb-lts-release.html, checked 2026-11-27
- Amazon DocumentDB features and configurations (features by version), https://docs.aws.amazon.com/documentdb/latest/devguide/docdb-engine-version-supportability.html, checked 2026-11-27
- Release notes, https://docs.aws.amazon.com/documentdb/latest/devguide/release-notes.html, checked 2026-11-27
- Amazon DocumentDB compatibility with MongoDB, https://docs.aws.amazon.com/documentdb/latest/devguide/compatibility.html, checked 2026-11-27
- Supported MongoDB APIs, operations, and data types, https://docs.aws.amazon.com/documentdb/latest/developerguide/mongo-apis.html, checked 2026-11-27
- Amazon DocumentDB in-place major version upgrade, https://docs.aws.amazon.com/documentdb/latest/devguide/docdb-mvu.html, checked 2026-11-27
- Amazon DocumentDB minor version upgrade, https://docs.aws.amazon.com/documentdb/latest/devguide/docdb-minor-version-upgrade.html, checked 2026-11-27
- Maintaining Amazon DocumentDB (engine version numbering, patches), https://docs.aws.amazon.com/documentdb/latest/devguide/db-instance-maintain.html, checked 2026-11-27
- Upgrading your Amazon DocumentDB cluster using AWS DMS, https://docs.aws.amazon.com/documentdb/latest/devguide/docdb-migration.versions.html, checked 2026-11-27
- Amazon DocumentDB: how it works (versions, storage, endpoints), https://docs.aws.amazon.com/documentdb/latest/devguide/how-it-works.html, checked 2026-11-27
- Restoring to a point in time, https://docs.aws.amazon.com/documentdb/latest/devguide/backup_restore-point_in_time_recovery.html, checked 2026-11-27
- Using Amazon DocumentDB elastic clusters, https://docs.aws.amazon.com/documentdb/latest/devguide/docdb-using-elastic-clusters.html, checked 2026-11-27
- Requirements and limitations for DocumentDB serverless, https://docs.aws.amazon.com/documentdb/latest/developerguide/docdb-serverless-limitations.html, checked 2026-11-27
- AWS CLI reference: docdb describe-db-engine-versions, https://docs.aws.amazon.com/cli/latest/reference/docdb/describe-db-engine-versions.html, checked 2026-11-27
- AWS CLI reference: docdb-elastic get-cluster, https://docs.aws.amazon.com/cli/latest/reference/docdb-elastic/get-cluster.html, checked 2026-11-27
- Troubleshooting performance and resource utilization (getEngineVersion output), https://docs.aws.amazon.com/documentdb/latest/devguide/user_diagnostics.html, checked 2026-11-27
