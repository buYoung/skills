# Couchbase Monitoring and Latency Diagnosis

Checked: 2026-11-27 (sources at the end). Applies to Couchbase Server 7.2–8.0.

## Contents

- Metric sources
- What to watch
- Query monitoring keyspaces
- Per-node Data Service tools
- Logs and diagnostics collection
- Diagnosis paths

## Metric Sources

| Source | Scope | Use |
|---|---|---|
| `GET :8091/metrics` (or `:18091`) | The node you call, in Prometheus text format | Scraping. Both containers return `cm_*`, `audit_*`, and `sys_*` series first. |
| `GET :8091/prometheus_sd_config` (7.2.1+) | Cluster node list for Prometheus HTTP service discovery | Replaces the deprecated `/prometheus_sd_config.yaml` |
| `GET :8091/pools/default/stats/range/<metric>[/<function>]`, `POST /pools/default/stats/range` | Cluster-wide time series kept by the built-in Prometheus | Ad-hoc questions without an external TSDB. In 8.0 these replace the deprecated `/pools/default/buckets/<b>/stats`. |
| `GET /pools/default/buckets/<b>` `basicStats` | Instant bucket summary | `quotaPercentUsed`, `opsPerSec`, `diskFetches`, `itemCount`, `memUsed`, `dataUsed`, `diskUsed`, `vbActiveNumNonResident` |
| `cbstats`, `mcstat` (port 11210) | One node's Data Service | Deep KV internals: timings, checkpoints, DCP, vBuckets |
| `system:*` keyspaces | Query Service | Active, completed, and prepared requests, vitals, indexes |
| Couchbase Web Console | Cluster | Dashboards built on the same statistics |

Prometheus scrape configuration (create a user with the External Stats Reader role, `external_stats_reader`):

```yaml
- job_name: "couchbase-server"
  basic_auth: {username: "prometheus", password: "***"}
  tls_config: {ca_file: "/etc/prometheus/cb-cert.pem"}
  scheme: "https"
  http_sd_configs:
    - url: https://node1:18091/prometheus_sd_config
      basic_auth: {username: "prometheus", password: "***"}
      tls_config: {ca_file: "/etc/prometheus/cb-cert.pem"}
```

Statistics REST examples. On both containers, `kv_ops` with `/irate`, with `/rate`, and with no function segment each returned `{"data":[{"metric":{...},"values":[[<unix time>,"<value>"],...]}]}`, with `bucket`, `start` (negative = seconds ago), and `step` (seconds) as query parameters:

```sh
curl -s -u Administrator:password \
  'http://127.0.0.1:8091/pools/default/stats/range/kv_ops/irate?bucket=app&start=-300&step=10'
curl -s -u Administrator:password \
  'http://127.0.0.1:8091/pools/default/stats/range/kv_curr_items?bucket=app'
```

Caveats:

- Do not let monitoring agents read `/proc/<pid>/smaps` for the large memcached and indexer processes. It has caused 10–20 s stalls.
- 7.6.0–7.6.10 and 8.0.0–8.0.1 report `cm_rest_request_enters_total` and `cm_rest_request_leaves_total` twice on `/metrics` (MB-70951, fixed in 7.6.11 and 8.0.2, listed again in 8.0.3). Deduplicate in the scraper or upgrade. Both containers, already on the fixed releases, showed each once.
- 7.6.6 and 8.0.0 could emit many DCP connection series for nonconforming connection names. Later releases aggregate them under `connection_type="_unknown"` (MB-63827).
- 8.0: `kv_vb_ht_memory_bytes` is deprecated in favor of `kv_vb_ht_memory_overhead`. `kv_ep_mem_low_wat_percent_ratio` and `kv_ep_mem_high_wat_percent_ratio` now report 0–1 instead of 0–0.01 (MB-62647). Fix any alert thresholds built on the old scale.
  - The containers differ from that note: 7.6.13 exposes `kv_ep_mem_high_wat_percent_ratio` (0.0085 for the 85% default), while 8.0.4 has no `_ratio` series and exposes `kv_ep_mem_high_wat_percent` and `kv_ep_mem_low_wat_percent` (0.85 and 0.75). Check the series name as well as the scale after upgrading.

## What to Watch

Metric names were confirmed against the Data Service metrics reference where noted, and against `/metrics` on the 7.6.13 and 8.0.4 containers where marked "container".

| Concern | Metrics or fields | Read as |
|---|---|---|
| Working set fits | Resident ratio per bucket (`kv_vb_perc_mem_resident_ratio{state="active"}`, 0–1; container. There is no `kv_vb_resident_items_ratio`), `kv_ep_bg_fetched` (confirmed: items fetched from disk), `basicStats.diskFetches` | Rising background fetches with falling residency on Couchstore means the bucket quota is too small. Magma buckets run at low residency by design, so watch fetch latency instead. |
| Memory pressure | `basicStats.quotaPercentUsed`, temporary OOM errors (`kv_ep_tmp_oom_errors`, and `kv_ep_oom_errors` for hard OOMs; container), ejection counters (`kv_ep_num_value_ejects`; container) | Sustained use above the high watermark (85%) with temp OOMs means writes are being rejected. |
| Persistence backlog | `kv_ep_diskqueue_items` (confirmed: items in the disk queue), `kv_ep_data_write_failed` (confirmed) | A growing disk queue means the disk cannot keep up. Any write failure needs investigation; it can trigger disk-based auto-failover if enabled. |
| Replication backlog | `kv_dcp_items_remaining` (confirmed: items still to send on outgoing DCP streams) | Intra-cluster replicas, indexes, and XDCR all consume DCP. A backlog delays durable writes and index freshness. |
| KV latency | `kv_cmd_duration_seconds` (confirmed: per-opcode histogram), `cbstats ... timings` | Compare p99 per opcode. |
| Clock drift | `kv_ep_ahead_exceptions` (confirmed: HLC CAS too far in the future), and the related clock-drift threshold metric | Fix NTP before relying on LWW or transactions. |
| Cluster health | `cm_rebalance_in_progress`, `cm_is_balanced`, `cm_failover_total`, `cm_graceful_failover_total`, `cm_auto_failover_count`, `cm_auto_failover_enabled` (7.2/7.2.6+) | Alert on any unplanned failover and on long rebalances. |
| XDCR | `xdcr_changes_left_total` per replication, `xdcr_docs_failed_cr_source_total`, `xdcr_docs_failed_cr_target_total`, `kv_conflicts_resolved{result=...}` | `changes_left` should drain to near 0. Persistent growth means the target or the link is too slow. |
| Audit | `audit_queue_length`, `audit_unsuccessful_retries` (container) | A growing queue means auditing is falling behind. |
| Host | `sys_cpu_utilization_rate`, `sys_mem_actual_free`, `sys_cpu_cgroup_*`, `sys_allocstall` (container) | `allocstall` growth signals memory reclaim pressure on the host. |

Built-in alerts worth enabling (email or UI): auto-failover events, disk-full thresholds, memcached connections above 90% of the limit (7.2.4+), Index low residency (7.2+), change-history size (7.2+), and certificate expiry (7.6+).

## Query Monitoring Keyspaces

All are per Query node but queried cluster-wide. They are transient, not persisted, and reset when the Query service restarts. Restricted keyspaces need the `query_system_catalog` role.

| Keyspace | Content | Typical query |
|---|---|---|
| `system:active_requests` | Running statements | `SELECT requestId, elapsedTime, statement, users FROM system:active_requests ORDER BY elapsedTime DESC;` |
| `system:completed_requests` | Statements above `completed-threshold` (1000 ms default), at most `completed-limit` (4000) per node, or matching other qualifiers | ``SELECT statement, elapsedTime, resultCount, phaseCounts, `~analysis` FROM system:completed_requests WHERE state = "completed" ORDER BY serviceTime DESC LIMIT 20;`` (backtick the `~` fields; unquoted `~analysis` fails with syntax error 3000 on both containers) |
| `system:completed_requests_history` | Streamed archive files (7.6.4+, when `completed-stream-size` > 0) | Slow on large histories. Reading the GZIP files directly can be faster. |
| `system:prepareds` | Prepared statement cache | `SELECT name, statement, uses, lastUse FROM system:prepareds;` |
| `system:vitals` | Per-node CPU, memory, GC, request rates, latency percentiles, spills | `SELECT * FROM system:vitals;` |
| `system:indexes` | Index definitions and state | Backtick reserved-word fields; see [indexes-and-queries.md](indexes-and-queries.md) |
| `system:group_info`, `system:bucket_info` | Groups and buckets (8.0) | — |

Admin REST equivalents on port 8093: `/admin/vitals`, `/admin/active_requests`, `/admin/completed_requests`, `/admin/prepareds`, and `/admin/settings`.

Actions:

```sql
-- Kill a runaway statement
DELETE FROM system:active_requests WHERE requestId = "<uuid>";
-- Purge completed-request history before a test run
DELETE FROM system:completed_requests;
```

```sh
# Log every request from one user, or every statement matching a pattern (8.0 adds "statement" and "plan")
curl -s -u Administrator:password http://127.0.0.1:8093/admin/settings \
  -H 'Content-Type: application/json' -d '{"completed": {"user": "app_rw"}}'
curl -s -u Administrator:password http://127.0.0.1:8093/admin/settings \
  -H 'Content-Type: application/json' -d '{"completed": {"statement": "%orders%"}}'
# Remove the qualifier afterwards
curl -s -u Administrator:password http://127.0.0.1:8093/admin/settings \
  -H 'Content-Type: application/json' -d '{"completed": {"-user": "app_rw"}}'
```

Reading `system:completed_requests` entries:

- `elapsedTime` is total time. `serviceTime` is execution. `phaseTimes` shows where it went. `phaseCounts` shows rows per phase.
- `~analysis` (8.0.4 example: `["High IO time"]`) is the server's own hint. The 7.6.13 container's entries had no `~analysis` field.
- `~qualifier` shows which logging rule captured the entry (`threshold` in the containers).
- `cpuTime`, `ioTime`, and `waitTime` separate compute from waiting on KV or the indexer.
- `scanConsistency` `unbounded` (the `not_bounded` setting) is normal for most reads. `request_plus` entries with large `waitTime` point to index lag.
- `usedMemory` versus `memoryQuota` shows how close a request came to its quota.
- Order by `serviceTime` and group by `statement` to find the costliest statement shapes. Then run `EXPLAIN` and `ADVISE` on them.

8.0 AWR keeps historical query statistics. `cbqueryreportgen` builds reports from it, and AWR must be enabled first.

## Per-Node Data Service Tools

```sh
# Operation latency histograms for one bucket on this node
/opt/couchbase/bin/cbstats -u Administrator -p password -b app localhost:11210 timings
# Everything, as JSON
/opt/couchbase/bin/cbstats -u Administrator -p password -b app -j localhost:11210 all
# Checkpoint and DCP state (replication and indexing backlog)
/opt/couchbase/bin/cbstats -u Administrator -p password -b app localhost:11210 checkpoint
/opt/couchbase/bin/cbstats -u Administrator -p password -b app localhost:11210 dcp
```

- `cbstats` reports one node only. Run it on each Data node, or use `-a` for all buckets.
- The stat groups `all`, `checkpoint`, `dcp`, and `timings` all returned output on both containers, and `-j` printed `all` as JSON. Only `timings` is shown on the fetched page.
- `mcstat` (8.0): one stat group per call, and `--json` output piped to `jq`; `--json=pretty` is ignored.
- Slow KV operations are also logged by memcached (`kv_slow_ops_2_gtrace` ships in both images to turn them into traces).

## Logs and Diagnostics Collection

- Logs live under `/opt/couchbase/var/lib/couchbase/logs` (`memcached.log*`, `query.log`, `indexer.log`, `goxdcr.log`, `debug.log`, `audit.log`, rebalance reports under `rebalance/`). These names match the 8.0.4 container running Data, Index and Query (`indexer.log` and `query.log` appear only on nodes with those services); the 7.6.13 Data-only container had the same Data-side files.
- Support bundle: `cbcollect_info` (in both images), or "Collect Information" in the UI (`/controller/startLogsCollection`). `cblogredaction` redacts user data before sharing.
- Rebalance report JSON: per-vBucket move timings. Use it to see whether backfill (data copy) or takeover dominates a slow rebalance.

## Diagnosis Paths

Slow KV reads:

1. Is it one node? Compare `kv_cmd_duration_seconds` per node, and `cbstats timings` on the slow node.
2. Disk fetches? Rising `kv_ep_bg_fetched` and low residency on a Couchstore bucket mean the quota is short; add memory or move to Magma. On Magma, check disk latency and the reader-thread setting.
3. Hot key or hot vBucket? One active vBucket serializes its writes. Look for skew in per-vBucket stats and in the application's key distribution.
4. Network or client: SDK timeouts with low server-side latency point at client connection pools, TLS handshakes (see the 8.0.4 MB-74905 fix for port 18091), or the network.

Slow writes or temporary failures:

1. `quotaPercentUsed` above 85% with temp-OOM errors: ejection cannot keep up. Raise the quota or use `fullEviction`.
2. A growing `kv_ep_diskqueue_items`: the disk is too slow, or compaction is competing. Check compaction activity and the writer threads.
3. Durable writes: check replica health and `kv_dcp_items_remaining`. One slow replica node slows every `majority` write that involves it.

Slow queries:

1. Find the statements in `system:completed_requests`, ordered by `serviceTime`.
2. `EXPLAIN`: look for `PrimaryScan3` or `#sequentialscan`, wide spans, a `Fetch` you could avoid, or a missing ORDER/LIMIT pushdown.
3. `profile=timings`: `servTime` on `IndexScan3` points to the indexer (residency, CPU, or index lag under `request_plus`). `servTime` on `Fetch` points to KV.
4. `ADVISE`, create the index with `defer_build`, build it, then re-run `EXPLAIN`.
5. Check `system:vitals` for GC pause percentage, queued requests (`request.queued.count`), and spills (`spills.order`, `spills.merge`, `spills.seq_scan`).

Rebalance too slow:

1. The rebalance report shows the phase that dominates.
2. Raise concurrent vBucket moves (default 4, max 64) only if disk and network have headroom.
3. Check whether Index or Search stages dominate. File-based index rebalance (7.6+) avoids rebuilds.

Sources: Configure Prometheus to Collect Couchbase Metrics (https://docs.couchbase.com/server/current/manage/monitor/set-up-prometheus-for-monitoring.html), Data Service Metrics (https://docs.couchbase.com/server/current/metrics-reference/data-service-metrics.html), Statistics REST (https://docs.couchbase.com/server/current/rest-api/rest-statistics.html), cbstats (https://docs.couchbase.com/server/current/cli/cbstats-intro.html), Manage and Monitor Queries (https://docs.couchbase.com/server/current/n1ql/n1ql-manage/monitoring-n1ql-query.html), XDCR Conflict Resolution, Rebalance, What's New 7.2, 7.6, and 8.0, Release Notes 7.2, 7.6, and 8.0, container outputs for 7.6.13 and 8.0.4, all checked 2026-11-27.
