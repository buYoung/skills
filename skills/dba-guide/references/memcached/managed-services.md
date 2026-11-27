# Memcached Managed Services

Amazon ElastiCache for Memcached, node-based clusters and ElastiCache Serverless. No pricing. Checked 2026-11-27 against the ElastiCache engine versions, parameters, upgrade considerations and supported-commands pages (sources in [versions/index.md](versions/index.md)).

## Version availability

| ElastiCache version | Notes from AWS |
| --- | --- |
| 1.6.22 | latest offered; bug fixes and cumulative updates |
| 1.6.17 | `lru_crawler`, `lru` and `slabs` admin commands no longer supported; `lru_crawler` is controlled through the parameter group |
| 1.6.12 | adds in-transit encryption |
| 1.6.6 | parameter family `memcached1.6`; extstore not supported |
| 1.5.16, 1.5.10, 1.4.34, 1.4.33, 1.4.24, 1.4.14, 1.4.5 | older versions still listed |

Upstream is at 1.6.45. Every ElastiCache version predates the 2026 upstream security releases (1.6.42–1.6.45); the engine versions page says nothing about back-porting those fixes. Ask AWS Support, or check the AWS security bulletins for the CVE, before relying on an ElastiCache node being patched. State the gap when answering version-sensitive questions and do not assume upstream features newer than 1.6.22 exist on ElastiCache (for example the 1.6.23 built-in proxy, the post-1.6.27 `E` CAS override, or the 1.6.40 `mg ... C<cas>` behavior).

## What the service takes over and what it removes

| Area | Node-based | Serverless |
| --- | --- | --- |
| Process start options | replaced by parameter groups (a custom group is needed to change anything) | not exposed |
| Memory | `max_cache_memory` per node type, not modifiable; item memory = `max_cache_memory` − `memcached_connections_overhead` (default 100 MB) | managed |
| Threads | `num_threads` per node type, not modifiable | managed |
| Connections | `max_simultaneous_connections` 65000, not modifiable | managed |
| Extstore | not supported | not supported |
| TLS | in-transit encryption from 1.6.12 | required for all connections |
| UDP, binary protocol | not covered on the pages checked | not supported (TLS required; binary protocol deprecated upstream) |
| `stats` variants | available; admin commands limited from 1.6.17 | only `stats` and `stats reset`; others return `ERROR` |
| `lru`, `lru_crawler`, `slabs`, `watch`, `verbosity`, `me` | `lru`, `lru_crawler`, `slabs` unavailable from 1.6.17 | not supported |
| `get`/`gets` | normal | limited to 16 KB (AWS: to prevent DoS through fetches of very many keys) |
| delayed `flush_all` | normal | rejected with `CLIENT_ERROR` |

AWS example for item memory: a `cache.m5.large` node has 6537 MB `max_cache_memory`; with the default 100 MB connection overhead, 6437 MB are available for items. `memcached_connections_overhead`, `max_item_size` and `chunk_size` take effect after a restart, which empties the node.

Parameters modifiable in custom groups include `max_item_size` (default 1048576), `chunk_size` (48), `chunk_size_growth_factor`, `error_on_memory_exhausted`, `cas_disabled`, `binding_protocol`, `memcached_connections_overhead`, `maxconns_fast`, `slab_automove`, `slab_reassign`, `lru_crawler`, `lru_maintainer`, `hash_algorithm`, `disable_flush_all`, `idle_timeout`, `track_sizes`, `slab_chunk_max`, `watcher_logbuf_size`, `worker_logbuf_size`. Not modifiable: `max_simultaneous_connections`, `backlog_queue_limit`, `hashpower_init`, `large_memory_pages`, `lock_down_paged_memory`, `requests_per_event`, among others.

## Failover, backups and maintenance

- AWS states that the Memcached engine does not support persistence. A node replacement or reboot loses that node's data. Backup and restore exist only for Serverless Memcached; node-based Memcached clusters have none (snapshot and restore page). Design exactly as for self-hosted memcached: tolerate misses and spread keys over enough nodes.
- Engine version upgrades of node-based clusters are always disruptive and clear all cache data in the cluster. Treat them as a cold start of the whole pool: low-traffic window and database headroom, or a parallel new cluster that clients move to gradually.
- AWS reserves the right to patch clusters for critical security issues; maintenance windows apply to node-based clusters.
- ElastiCache Auto Discovery (offered since ElastiCache 1.4.14) lets supporting client libraries determine all nodes of a cluster automatically. Adding or removing nodes still changes the client hash ring as described in [guide.md](guide.md#client-side-distribution-and-failure).

## Diagnostics that replace self-hosted ones

| Self-hosted | ElastiCache |
| --- | --- |
| start options, `stats settings` | `aws elasticache describe-cache-parameters --cache-parameter-group-name <group>`; `stats settings` on node-based nodes (not on the restricted list, which covers Serverless only; Serverless answers `ERROR` to any `stats` form except `stats` and `stats reset`) |
| `stats`, `stats items`, `stats slabs` | node-based: available; Serverless: `stats` and `stats reset` only |
| host CPU, memory, swap, connections | `AWS/ElastiCache` host metrics per node: `CPUUtilization`, `FreeableMemory`, `SwapUsage`, `NetworkBytesIn`/`Out` (host-level metrics page); `CurrConnections` (includes 2–3 ElastiCache monitoring connections) on the Memcached metrics page |
| version | `aws elasticache describe-cache-clusters --show-cache-node-info` (`EngineVersion`) and `version` on the node |

## Choosing Memcached or Valkey on ElastiCache

Inference from the documented feature sets: choose Memcached only for a pure look-aside cache that tolerates node loss and benefits from multithreading per node. Choose Valkey when you need replication and failover, snapshots, data structures, or newer features, or when the upstream security gap of the offered Memcached versions matters. See [../valkey/managed-services.md](../valkey/managed-services.md).
