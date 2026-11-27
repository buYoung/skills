# Couchbase Server Versions

Checked: 2026-11-27 against the Couchbase Software Lifecycle Schedules (https://www.couchbase.com/support-policy/EOL/, page dated November 17, 2026) and the Enterprise Software Support Policy (https://www.couchbase.com/support-policy/enterprise-software/, page dated October 19, 2026).

## Support Status

Couchbase Server is versioned `major.minor.maintenance`. Lifecycle is tracked per minor series (7.2, 7.6, 8.0). From 7.2 on, each major or minor release gets Full Maintenance for 36 months from its GA date, and End of Life is also 36 months from GA, so there is no separate Limited Support period for these series. Full Maintenance runs to the last day of the month shown; the release is End of Life the day after the date shown.

| Series | Release type | GA | End of Full Maintenance | End of Life | Latest maintenance release seen | File |
|---|---|---|---|---|---|---|
| 8.0 | Major | Oct 2025 | Oct 2028 | Oct 2028 | 8.0.4 (November 2026) | [8.0](8.0.md) |
| 7.6 | Minor | Mar 2024 | Mar 2027 | Mar 2027 (the 7.6 release notes banner gives March 31, 2027) | 7.6.13 (November 2026) | [7.6](7.6.md) |
| 7.2 | Minor | Jun 2023 | Jul 2026 | Jul 2026 (ended before 2026-11-27) | 7.2.8 (August 2025) per the 7.2 release notes | [7.2](7.2.md) |

Notes:

- 7.2 is covered only as the most recent series that reached End of Life, to support upgrade paths. Treat any 7.2 cluster as unsupported.
- 7.6 reaches End of Life on March 31, 2027, four months after the check date. Plan 7.6 clusters onto 8.0.
- The lifecycle page lists no 8.1 or 9.0 series on 2026-11-27. One 8.0 release note (MB-67849) mentions builds "through 8.1.0", so an 8.1 series may follow; check the lifecycle page before stating that 8.0 is the latest.
- The support policy applies to Enterprise Edition under subscription. Community Edition gets no vendor support or hot fixes, and the editions page says it does not include the latest bug fixes.
- Couchbase Capella supports Server 8.0 and 7.6 for new clusters on the check date and patches each version for 36 months from GA. See [managed-services.md](../managed-services.md).

## Identify the Running Version

Use the REST API on the cluster manager port (8091, or 18091 with TLS). All commands need a user that can read cluster settings.

```sh
# Build string and edition of the node you hit
curl -s -u Administrator:password http://127.0.0.1:8091/pools \
  | jq '{implementationVersion, isEnterprise, isDeveloperPreview}'
# 8.0.4 container output: "implementationVersion":"8.0.4-6414-enterprise","isEnterprise":true,"isDeveloperPreview":false

# Version of every node, plus the numeric compatibility of each
curl -s -u Administrator:password http://127.0.0.1:8091/pools/default \
  | jq '.nodes[] | {hostname, version, clusterCompatibility, services}'

# Effective cluster compatibility (the lowest node version) and the orchestrator
curl -s -u Administrator:password http://127.0.0.1:8091/pools/default/terseClusterInfo
# returns e.g. {"clusterUUID":"...","orchestrator":"ns_1@node3.","isBalanced":true,"clusterCompatVersion":"8.0"}
```

From SQL++ (cbq, Query Workbench, or `:8093/query/service`):

```sql
SELECT RAW DS_VERSION();
-- 8.0.4 container: "8.0.4-6414-enterprise"; 7.6.13 container: "7.6.13-9436-enterprise"
```

On a node's filesystem, `cat /opt/couchbase/VERSION.txt` prints the build: `8.0.4-6414` and `7.6.13-9436` in the containers. `/opt/couchbase/bin/couchbase-server --version` adds the edition: `Couchbase Server 8.0.4-6414 (EE)`, and `Couchbase Server 8.0.2-5503 (CE)` on the Community image.

How to read the output:

- `isEnterprise` gives the edition. Enterprise builds end in `-enterprise` (container). Community builds end in `-community`. The `community-8.0.2` container reported `"implementationVersion":"8.0.2-5503-community","isEnterprise":false`.
- `clusterCompatVersion` stays at the lowest node version until every node runs the new version. That is the finalization point described under Upgrade Paths. A cluster whose nodes report different `version` values is in mixed mode.
- `nodes[].clusterCompatibility` is numeric. The containers reported 458758 on 7.6.13 and 524288 on 8.0.4, which matches major × 65536 + minor (inference; no documentation states the encoding). Use `clusterCompatVersion` when you need a readable value.
- `isDeveloperPreview: true` means Developer Preview was enabled. The upgrade documentation says such a cluster cannot be downgraded. Do not run production on it.

Capella: the cluster's Couchbase Server version appears in the Capella UI and the Management API. `SELECT RAW DS_VERSION();` also works through a cluster access credential. Capella cluster access credentials are data-access credentials (basic bucket/scope/collection access, or advanced roles), so before relying on the `/pools` calls above, run them with the credential you have and check which roles its Access Control entry lists.

## Upgrade Paths

Supported direct paths into the current series (Enterprise and Community Edition use the same table):

| From | Path |
|---|---|
| 7.6.x | 7.6.x → any 8.0.x |
| 7.2.x | 7.2.x → any 8.0.x, or 7.2.x → 7.6.x |
| 7.1.x | → 7.2.3 → 8.0.x (8.0 table). The 7.6 table allows 7.1 → 7.6.x directly. |
| 7.0.x | → 7.2.3 → 8.0.x (8.0 table); → 7.1 → 7.6.x (7.6 table). The current upgrade page's text says "first upgrade to a version between 7.1 and 7.2.3. Then upgrade to version 7.6 or later", which is looser than its table; follow the table. |
| 6.5, 6.6, 7.0 | Cannot go directly to 7.2.4 or later (Erlang compatibility). Upgrade to a version between 7.1 and 7.2.3 first. |
| 6.0.x, 6.5.x | → 6.6 → 7.2.3 → 8.0.x |
| 5.x | → 6.6 → 7.2.3 → 8.0.x |

Rules that apply to every path:

- Upgrades go node by node. A cluster in mixed mode is supported only while the upgrade is in progress.
- Upgrading between non-adjacent versions is not supported. Upgrade every node to the intermediate version before starting the next hop.
- Community Edition to Enterprise Edition is a separate rolling swap to fresh EE nodes at the same version. It is not supported when Index Service nodes exist, and it cannot be combined with a version change.
- From 7.2 on, every node certificate must name the node in a Subject Alternative Name, or the upgrade can fail.

Downgrade and rollback limits:

- Maintenance upgrades (for example 8.0.3 → 8.0.4) can be rolled back online at any time, even after the last node is upgraded.
- Major or minor upgrades (7.6 → 8.0) can be rolled back only before finalization. Finalization happens when the last node runs the new version. After that, the only way back is a new cluster on the old version plus a data migration, for example from an XDCR disaster-recovery cluster still on the old version.
- To keep the option open while testing on 7.6.0 or later, add an arbiter node (no services) that stays on the old version. It blocks finalization and also blocks the new features. Remove it to finalize.
- A downgrade must be online (swap rebalance with the old version). Offline downgrade, or graceful failover followed by full recovery, cannot be used to downgrade.
- A cluster that ever had Developer Preview enabled cannot be downgraded.

Generic procedure:

1. Pre-checks: read the target series file ([8.0](8.0.md) or [7.6](7.6.md)) for blockers. Confirm the source version is on a supported path. Check node certificates for SANs. On x86-64, confirm AVX2 before 8.0. List buckets with `curl -s -u ... :8091/pools/default/buckets | jq '.[] | {name, bucketType, storageBackend, numVBuckets}'` and remove `memcached` buckets before 8.0. Review scripts that create buckets without `storageBackend`. Check SDK versions against the target.
2. Rehearse: restore a recent `cbbackupmgr` backup into a scratch cluster on the source version, or build one with XDCR. Upgrade it with the same method you plan to use in production. Run the application test suite, and compare `EXPLAIN` output for the top statements from `system:completed_requests`.
3. Choose the method: swap rebalance (needs spare nodes, keeps full capacity), graceful failover plus delta recovery (Data-only nodes, reduced capacity, no spare node), or offline (downtime; disable auto-failover first and re-enable it at the end). Take a fresh backup.
4. Switch: upgrade one node, rebalance, and check health (`couchbase-cli server-list`, `/pools/default` node `status`, rebalance report). Repeat. Do not change XDCR filter or mapping settings while the cluster is mixed (8.0 note MB-66140).
5. Post-checks: `clusterCompatVersion` equals the target. Every index is `online` in `system:indexes`. XDCR replications are running with `changes_left` draining. Backups succeed. Re-enable any setting you disabled for the upgrade, such as client-certificate authentication or auto-failover.

## Outside the Covered Range

- Older than 7.2 (7.1, 7.0, 6.x): these series have been End of Life since July 2025 or earlier. Read the archived release notes and upgrade pages for that version (docs-archive.couchbase.com), then follow the path table above. Claims in this reference that may not hold before 7.2 include: the `_system` scope (7.6+), Magma change history (7.2+), Prometheus service discovery at `/prometheus_sd_config` (7.2.1+), audit `pruneAge` (7.2.4+), bucket `rank`, arbiter nodes, and user backup (7.6+), Argon2id password hashing (7.6+), and scopes and collections (7.0+).
- Newer than 8.0 (8.1 or later, if released): read that series' "What's New" and "Release Notes" pages at docs.couchbase.com/server/<series>/ and the upgrade page's "Before You Upgrade" section. Defaults that changed in 8.0, such as the storage engine, vBucket count, warmup, and role splits, may change again. Re-check the lifecycle page for support dates.
- Any answer about a server outside 7.2–8.0 must state the version gap, name the release notes it relied on, and mark behavior taken from this reference as unverified for that version.

## Sources

- Couchbase Software Lifecycle Schedules — https://www.couchbase.com/support-policy/EOL/ — checked 2026-11-27
- Couchbase Enterprise Software Support Policy — https://www.couchbase.com/support-policy/enterprise-software/ — checked 2026-11-27
- Release Notes for Couchbase Server 8.0 — https://docs.couchbase.com/server/current/release-notes/relnotes.html — checked 2026-11-27
- What's New in Version 8.0 — https://docs.couchbase.com/server/current/introduction/whats-new.html — checked 2026-11-27
- Release Notes for Couchbase Server 7.6 — https://docs.couchbase.com/server/7.6/release-notes/relnotes.html — checked 2026-11-27
- What's New in Version 7.6 — https://docs.couchbase.com/server/7.6/introduction/whats-new.html — checked 2026-11-27
- Release Notes for Couchbase Server 7.2 — https://docs.couchbase.com/server/7.2/release-notes/relnotes.html — checked 2026-11-27
- What's New in Version 7.2 — https://docs.couchbase.com/server/7.2/introduction/whats-new.html — checked 2026-11-27
- Upgrade (8.0) — https://docs.couchbase.com/server/current/install/upgrade.html — checked 2026-11-27
- Upgrade (7.6) — https://docs.couchbase.com/server/7.6/install/upgrade.html — checked 2026-11-27
- Upgrade Procedure Selection — https://docs.couchbase.com/server/current/install/upgrade-procedure-selection.html — checked 2026-11-27
- Retrieving Cluster Information (`GET /pools`) — https://docs.couchbase.com/server/current/rest-api/rest-cluster-get.html — checked 2026-11-27
- Identifying the Orchestrator Node (`terseClusterInfo`) — https://docs.couchbase.com/server/current/rest-api/rest-identify-orchestrator.html — checked 2026-11-27
- Couchbase Server Editions — https://docs.couchbase.com/server/current/introduction/editions.html — checked 2026-11-27
- Capella: Upgrading a Cluster — https://docs.couchbase.com/cloud/clusters/upgrade-database.html — checked 2026-11-27
- XDCR Overview (scopes and collections require 7.0+) — https://docs.couchbase.com/server/current/learn/clusters-and-availability/xdcr-overview.html — checked 2026-11-27
- Runs of the vendor images `couchbase/server:8.0.4`, `couchbase/server:7.6.13`, and `couchbase/server:community-8.0.2` (digests in the coverage record, `updates/2026-11-27-initial-coverage.md`): REST settings, SQL++ statements and transactions, EXPLAIN and ADVISE output, and `cbbackupmgr` — run 2026-11-27
