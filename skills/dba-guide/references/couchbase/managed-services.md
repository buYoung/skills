# Couchbase Capella (Managed Service) Differences

Checked: 2026-11-27 against the Capella documentation (sources at the end). Applies to Capella operational clusters, the fully managed Couchbase Server offering. Capella's separate Analytics and App Services products are out of scope.

## What Capella Takes Over

- Provisioning, node layout, OS and security patching, and Couchbase Server upgrades. Upgrades run as maintenance jobs: optional self-service jobs, or mandatory jobs scheduled by Couchbase.
- Failover and rebalance during maintenance. The cluster moves to a "redeploying" state while nodes are rebalanced, and is designed to stay available. Single-node clusters may have downtime.
- Encryption at rest by default, with a per-cluster key from the cloud provider's KMS (AWS KMS, Google Cloud KMS, Azure Key Vault). Customer-managed keys are supported.
- TLS 1.2 or higher on every connection. It cannot be turned off.
- Backups run on separate compute that Capella provisions, which limits the impact on the cluster.

## What Is Removed or Restricted

| Area | Self-managed Server | Capella |
|---|---|---|
| Administrative access | Full Admin user, REST on 8091/18091, `couchbase-cli`, node shell | Capella UI, the Management API, and cluster access credentials for data. There is no node shell. Cluster access credentials carry bucket/scope/collection access or advanced roles (cluster access credentials page); check which roles a credential has on the cluster's Access Control page before planning admin REST calls. |
| Database users | Any RBAC role | Cluster access credentials, created by a Project Owner or Cluster Manager. Basic access grants Read, Write, or Read/Write on chosen buckets, scopes, and collections. Advanced access (paid plans) assigns predefined or custom roles. Credentials cannot create buckets. |
| Network access | Your firewall | Allowed IP list (optionally time-limited), VPC peering, or private endpoints (AWS PrivateLink, Azure Private Link, GCP Private Service Connect). Restricted public access is available on request for new clusters. |
| Server version | Any supported release | 8.0 (latest) or 7.6 (previous) for new clusters on the check date. Capella chooses the patch level. |
| Views | Supported on Couchstore | Not supported. Use `--disable-views` when restoring into Capella. |
| Query, Analytics, and user metadata in `cbbackupmgr` | Fully available | Credentials cannot read or write some of it. Use `--capella` (7.6+ tools) or the `--disable-*` set. |
| Tuning (cbepctl, memcached settings, OS) | Yours | Not exposed. Some features, such as auto-reprepare on 7.6.10+, need a Support request. |
| Bucket type names | Couchbase, Ephemeral | "Memory and Disk", "Memory Only" |

## Versions and Support Window

- Each Couchbase Server version on Capella gets patches for 36 months from its GA date, the same window as self-managed Enterprise. Capella notifies you 6 months before your version leaves support. After that, Couchbase Support works with you to upgrade. End-of-support versions cannot be used for new deployments, get no OS or security patches, and have no SLA.
- Mandatory critical upgrades (security, OS, fixes, version compliance): Couchbase aims for 1–2 weeks of notice, then a 2–4 week upgrade window, and can adjust both. You can move the job within the window. Notification emails go to Organization Owners, Project Owners, and Cluster Managers when the job is scheduled and 1 week, 24 hours, and 1 hour before the target start.
- Self-service jobs (most patch releases) can be scheduled by you or started with "Upgrade Now". The cluster must be on and healthy. An off or unhealthy cluster has its job rescheduled an hour later, repeatedly. A job due within an hour also blocks turning the cluster off.
- No cluster reconfiguration is possible while an upgrade runs. Data tools stay available.
- Free-tier clusters are upgraded at Couchbase's convenience, outside the paid-cluster timeframes.
- Version-specific notes in this reference still apply. For example, 7.6.6+ is required for cross-region backup copies and for restoring a cluster backup into another cluster. Capella's own upgrade process decides when 8.0 behavior changes, such as the storage default and the role split, reach your cluster.

Identify the version: the Capella UI cluster page or the Management API, or `SELECT RAW DS_VERSION();` with a cluster access credential.

## Backups and Restore

Capella has two mechanisms.

Cluster backups (snapshots of the whole cluster):

- Default schedule every 4 hours with 7-day retention; on-demand backups also default to 7 days. The schedule is in UTC.
- AWS and Azure clusters on 7.6.6+ can copy backups to up to 2 other regions. GCP clusters cannot.
- Restore replaces all data on the target cluster. It deletes all cluster access credentials and allowed IPs, makes the cluster unavailable until it completes, and reverts the node count and Server version to the backup's (a 7.6.5 backup temporarily puts the cluster back on 7.6.5). Record credentials, IP lists, and node changes before restoring.
- Restoring to a different cluster in the project works only when both clusters run 7.6.6 or later. The cluster's own Backup tab restores only to itself.
- Azure: after 500 incremental snapshots, backups become full and cost much more.

Bucket backups (per bucket, on demand or scheduled):

- A schedule starts with a full backup, followed by incrementals at a chosen hourly interval. A restore applies the full backup first, then the incrementals. A full backup is roughly 40% of the dataset size.
- Retention for scheduled bucket backups: 30 days to 5 years. On-demand: 30 days. The cost-optimized policy keeps only the monthly restore point for the chosen period, and the others for about 4 weeks (the page says both "four weeks" and "30 days").
- Use bucket backups to move data to a different cluster.
- No point-in-time snapshot: items are individually consistent, and the consistency window across items is usually a few seconds.
- Scheduled backups do not run while the cluster is off, and backups still expire while it is off.
- Downloads: up to 5 TB on AWS, GCP, and Azure. Retrieve the URL within 12 hours and start the download within 1 hour of copying it. The file is kept about 24 hours, with a SHA-256 checksum. The archive is a `cbbackupmgr` repository: `cbbackupmgr info --archive <path>/<repo> --repo <repo>`.

`cbbackupmgr` against Capella:

```sh
cbbackupmgr config --archive /backups --repo capella_db1 --capella
cbbackupmgr backup --archive /backups --repo capella_db1 \
  --cluster couchbases://cb.<id>.cloud.couchbase.com --username dbuser --password '***' \
  --cacert /root/capella.pem --full-backup --threads 4
# Self-managed -> Capella (target buckets must already exist; no --auto-create-buckets)
cbbackupmgr restore --archive /backups --repo repo_mydb \
  --cluster couchbases://cb.<id>.cloud.couchbase.com --cacert /root/capella.pem \
  -u dbuser -p '***' --capella
```

With tools older than 7.6, replace `--capella` with `--disable-analytics --disable-cluster-analytics --disable-bucket-query --disable-cluster-query --disable-views`. Use `--cacert` in production; `--no-ssl-verify` is for development only. Add your client IP to the allowed list first.

## Failover, Replication, and XDCR

- Replica counts, durability, and transactions behave as in [transactions-and-durability.md](transactions-and-durability.md). Capella handles node failure. You see the effects (rebalances, the redeploying state) but do not run failover commands.
- XDCR between Capella and self-managed Enterprise 7.2+ can be fully secure, and Capella's CAs are trusted automatically on 7.2+ servers. The vBucket-count and ECCV rules in [replication-and-xdcr.md](replication-and-xdcr.md) still apply, including the 8.0 Magma/128 default.

## Security

- Organization and project roles control the Capella UI. Cluster access credentials control data. Keep them separate: an Organization Owner is not a database user.
- SSO (Okta, Azure AD, Ping Identity, CyberArk), TOTP MFA for non-SSO users, and a 5-minute account lock after 5 failed logins.
- Event auditing is available, logged per node, and downloaded as one compressed file.
- A HashiCorp Vault plugin can issue short-lived cluster credentials.

## Monitoring

- Each cluster has a native Prometheus target. Scrape it through HTTP service discovery at `https://<public-connection-string>:18091/prometheus_sd_config`, with a cluster credential and the cluster certificate (`ca_file`). Add the scraper's IP to the cluster's Allowed IP list; Capella denies connections from addresses not on it (allowed IP page). The Prometheus page's sample uses a cluster username and password but names no access level; start with a read-only credential and widen it only if discovery or scraping fails.
- Metrics over private endpoints are available only on request to Capella Support, at `...:18091/prometheus_sd_config?network=external`. On AWS this limits the cluster to 20 nodes, or 13 if Query nodes were mapped 1:1 on private endpoints.
- Query monitoring keyspaces (`system:completed_requests` and the others), `EXPLAIN`, `ADVISE`, and `profile` work as on Server, subject to the credential's roles. See [monitoring.md](monitoring.md).
- Node-level tools (`cbstats`, `mcstat`, log files, `cbcollect_info`) are not available, because there is no node access. Use Capella metrics, alerts, and Support log collection (inference, not documented).

## Choosing Capella Versus Self-Managed

Prefer Capella when the team does not want to own upgrades, patching, backup infrastructure, and failover operations, and when TLS-only access, managed encryption, and the upgrade windows are acceptable. Prefer self-managed Server when you need full-admin settings, Views, OS tuning, node-level diagnostics, control over exact maintenance releases and upgrade timing, Community Edition, or network topologies that Capella's private networking does not support.

Sources: Capella Upgrading a Cluster (https://docs.couchbase.com/cloud/clusters/upgrade-database.html), Backup and Restore (https://docs.couchbase.com/cloud/clusters/backup-restore.html), Take or Schedule a Cluster Backup (https://docs.couchbase.com/cloud/clusters/take-cloud-snapshot.html), Restore a Cluster Backup (https://docs.couchbase.com/cloud/clusters/restore-cloud-snapshot.html), Back Up and Restore with Command Line Tools (https://docs.couchbase.com/cloud/clusters/cli-backup-restore.html), Security (https://docs.couchbase.com/cloud/security/security.html), Add a Capella Cluster to a Prometheus Server (https://docs.couchbase.com/cloud/clusters/monitoring/prometheus.html), Manage Cluster Access Credentials (https://docs.couchbase.com/cloud/clusters/manage-database-users.html), Capella Release Notes (https://docs.couchbase.com/cloud/release-notes/release-notes.html), Memory (bucket type names), What's New 7.2, Release Notes 7.6, all checked 2026-11-27.
