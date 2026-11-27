# Memcached Guide

Checked: 2026-11-27 against memcached 1.6.45 (official `memcached:1.6` image), `doc/protocol.txt` at tag 1.6.45 and https://docs.memcached.org/. Version-specific changes are in [versions/1.6.md](versions/1.6.md).

Contents:

1. [When to use Memcached](#when-to-use-memcached)
2. [Memory model and slab classes](#memory-model-and-slab-classes)
3. [LRU, expiration and eviction](#lru-expiration-and-eviction)
4. [Slab rebalancing](#slab-rebalancing)
5. [Item and key size limits](#item-and-key-size-limits)
6. [Connections and threads](#connections-and-threads)
7. [Client-side distribution and failure](#client-side-distribution-and-failure)
8. [Protocols: text, meta, binary](#protocols-text-meta-binary)
9. [Extstore (flash)](#extstore-flash)
10. [Built-in proxy](#built-in-proxy)
11. [Warm restart](#warm-restart)
12. [Security](#security)
13. [Stats and diagnosis](#stats-and-diagnosis)
14. [Common mistakes](#common-mistakes)

## When to use Memcached

Memcached is a multithreaded, in-memory key/value cache. Servers do not know about each other: no replication, no crosstalk, no persistence (warm restart and extstore do not survive a crash), and no data structures beyond byte strings with client flags, a TTL and a CAS value. Distribution, failover and invalidation live in the client or in the built-in proxy.

| Need | Memcached | Valkey/Redis |
| --- | --- | --- |
| Look-aside cache of serialized objects, simple get/set/delete | good fit; worker threads scale across cores | also fits; commands execute on one main thread |
| Data that must survive a node loss | no (a lost node = misses) | replication, persistence |
| Data structures, atomic multi-field updates, pub/sub, scripts | no | yes |
| Large values on flash | extstore | not in core |
| Stampede protection | meta protocol (`N`, `R`, `W`/`Z` flags) | locks with `SET NX` |

If losing one node's contents would overload the database, size the pool (more, smaller nodes) and the database for that miss storm, or choose a replicated store. For the Valkey side see [../valkey/data-modeling.md](../valkey/data-modeling.md).

## Memory model and slab classes

- `-m` (default 64 MB) limits item memory only. The hash table, connection buffers and thread structures come on top, so the process uses more than `-m`. Values below 64 MB may still use 64 MB.
- Memory is assigned to slab classes in pages (`total_pages` in `stats slabs`; page size 1 MB by default: one used class shows `total_pages 1` and `total_malloced 1048576`). Each class holds chunks of one size; sizes start at `-n` (48 bytes minimum for key+value+flags) and grow by `-f` (1.25) up to `slab_chunk_max` (512 KB). Items larger than `slab_chunk_max` are stored across several chunks: with `-I 4m`, a 2,000,000-byte value used four 512 KB chunks of the largest class (two pages) plus one 120-byte chunk in class 2, and `stats items` counts it under the largest class.
- An item lands in the smallest class whose chunk fits key, value and item header; the rest of the chunk is wasted. Compare `stats items` `items:N:mem_requested` with `stats slabs` `N:chunk_size` × `N:used_chunks` to measure waste per class.
- `-o track_sizes` plus `stats sizes` shows the item size histogram. On a running server started without it, process `lru_crawler metadump all` output offline; that command does not block the server.
- Lower `-f` (for example 1.08) only when the size histogram shows items clustered just above class boundaries and memory waste matters; more classes spread memory thinner and make rebalancing more important.
- The hash table grows at runtime (`hash_power_level`, `hash_is_expanding` in `stats`). For servers that reach a known size, set `-o hashpower=N` from a production `hash_power_level` to avoid expansion work at startup.
- `-L` tries to use large memory pages; `-k` locks paged memory. Swapping destroys memcached latency; monitor host swap.
- Runtime memory change: `cache_memlimit <megabytes>`. Raising lets the server request more memory; lowering releases memory asynchronously only when slab reassignment and automove are enabled.

## LRU, expiration and eviction

1.6 defaults to the segmented LRU (`lru_segmented yes`) with a background maintainer thread:

- New items enter HOT. Items hit at least twice are active. At the bottom of HOT, active items move to WARM and others to COLD; active items in COLD move to WARM. HOT and WARM are capped by a percentage of the class's memory (`hot_lru_pct 20`, `warm_lru_pct 40`) and by age relative to COLD (`hot_max_factor 0.20`, `warm_max_factor 2.00`). COLD is uncapped and evictions come from its tail. This protects frequently read items from one-off scans.
- `temp_lru` (off by default) with `temporary_ttl` (61 s): items with a TTL at or below this go to a TEMP LRU, are never bumped and cannot be evicted. Do not raise `temporary_ttl` far, or memory can be exhausted.
- The LRU crawler (`lru_crawler yes`) scans classes in the background and reclaims expired items early (`crawler_reclaimed`, `crawler_items_checked`).
- Expiration time: 0 = never expires (still evictable); up to 30 days (2,592,000 s) is relative; larger values are a Unix timestamp; negative = expired at once. A TTL of 1 can expire immediately because time advances on second boundaries.
- `-M` returns an error on memory exhaustion instead of evicting (`store_no_memory` counts rejects). Use it only when the data must not silently disappear.
- Eviction evidence: `stats` `evictions`, `evicted_unfetched` (evicted, never read after being set), `evicted_active` (evicted although recently hit), `expired_unfetched`; `stats items` per class `evicted`, `evicted_nonzero` (items with a TTL evicted early), `evicted_time` (seconds since the last evicted item was last fetched; small values mean live data is being evicted), and `age`.

## Slab rebalancing

Without rebalancing, early traffic patterns freeze memory into classes. 1.6 defaults: `slab_reassign yes`, `slab_automove 1`.

| `slabs automove` | Behavior |
| --- | --- |
| 0 | thread on standby |
| 1 (default) | return pages to a global pool when a class has more than 2 pages worth of free chunks; reassign them as needed |
| 2 | move pages on every eviction; not recommended (and the `slabs_mover=2` start option is discouraged since 1.6.41) |

Manual move: `slabs reassign <src> <dst>` (replies `OK`, `BUSY`, `BADCLASS`, `NOSPARE`, `NOTFULL`, `UNSAFE`, `SAME`). Evidence: `slabs_moved`, `slab_reassign_running`, `slab_reassign_busy_items`, `slab_global_page_pool`.

Diagnosis rule from the maintenance guide: if the classes with the most evictions are also those with the most `total_pages`, the pool is out of memory; if not, memory is misallocated and rebalancing fixes it (very old versions needed a restart).

## Item and key size limits

- Keys: at most 250 characters; no whitespace or control characters in the text protocol. Meta commands accept base64-encoded binary keys with the `b` flag.
- Values: `-I` sets the maximum item size (default 1 MB, range 1k to 1024m). Rejected writes count in `store_too_large`.
- Prefer compressing or splitting values over raising `-I` far: large items take whole pages and push out many small items.
- Client flags: 32-bit (`client_flags_size 4` in `stats settings`); the protocol text recommends 16 bits for compatibility with very old servers.

## Connections and threads

- `-c` (default 1024) caps simultaneous connections. At the limit memcached disables its listener and new connections wait in the backlog (`-b`, 1024); with `maxconns_fast` (default on) new connections over the limit are closed immediately. Evidence: `listen_disabled_num` and `rejected_connections` should stay at or near 0; compare `curr_connections` with `max_connections`; `accepting_conns 0` means saturated now.
- Per-connection memory is small (400–500 bytes idle since 1.6.0), so set `-c` above the real peak (processes per host × hosts, plus admin and cron headroom). Raise the process file-descriptor limit to match; `stats` shows `reserved_fds`.
- `-o read_buf_mem_limit=<MB>` caps connection read/response buffers; only for very high connection limits (20k+).
- `-o idle_timeout=<s>` closes idle clients; use it against leaked connections, not as a pool setting.
- `-t` worker threads (default 4). Each thread handles many connections through libevent. Raise only when worker CPU saturates; very large values (80+) make memcached slower. `-R` (20) limits requests processed per event per connection so one pipelining client cannot starve others; `conn_yields` counts how often it applied.
- `stats conns` lists each socket with `addr`, `listen_addr`, `state`, `secs_since_last_cmd`.

## Client-side distribution and failure

- Clients choose the server for a key with a hashing algorithm, normally a consistent hash. All clients must use the same server list, order and hash settings, or they read and write different nodes and see stale data.
- Adding a node remaps about 1/N of keys with consistent hashing and almost all keys with modulo hashing. Add capacity during low database load and expect a miss spike.
- A failed node means misses for its keys. Configure the client either to remove it from the ring (its keys move to other nodes) or to keep it and treat errors as misses. Inference, not stated in the documentation: if a node that was only partitioned rejoins the ring, it can serve values that were updated elsewhere meanwhile; invalidate on write from the application and keep TTLs bounded.
- Invalidation: delete or overwrite on the owning server after a database write. With several pools (for example per region), the meta `E` flag sets the CAS to an external version (row version, clock) so out-of-order updates fail with `EX` instead of overwriting newer data. The project describes this as not strict.
- Memcached has no cross-node commands; `flush_all` affects one server, and `flush_all <delay>` lets you stagger flushes across servers.

## Protocols: text, meta, binary

Text protocol (verified in the official image):

```
set k 0 60 3        # flags 0, TTL 60 s, 3 bytes
abc
STORED
gets k
VALUE k 0 3 2       # last number = CAS
abc
END
incr n 10           # value must be a decimal unsigned 64-bit; incr wraps at 2^64, decr stops at 0
```

Meta protocol (complete since 1.6.0): two-letter commands with flags, usable on the same connection as text commands.

```
mg k v t c          # value, TTL remaining, CAS
VA 3 t60 c2
abc
ms k2 3 T60         # set with TTL 60
xyz
HD
md k2               # delete
HD
mn                  # no-op marker at the end of a pipeline
MN
```

| Goal | Meta form |
| --- | --- |
| get with client flags and value | `mg key f v` |
| get-and-touch | `mg key v T90` |
| revalidate without transferring the value (1.6.40+) | `mg key v C<cas>` → `HD` if unchanged, `VA` if changed |
| stampede protection on miss | `mg key v c N30` → the first client gets `W` and recaches; others see `Z` |
| early recache before expiry | `mg key v t R30` → `W` when the remaining TTL is below 30 s |
| serve stale while one client refreshes | `md key I T30` marks the item stale; `mg` then returns `X` and gives `W` to one client |
| add / replace / append / prepend | `ms key <len> ME` / `MR` / `MA` / `MP` |
| compare-and-set | `ms key <len> C<cas>` → `HD`, `EX`, `NF` |
| quiet pipelining | `q` hides `HD`/`EN`; `O<opaque>` or `k` match replies; end with `mn` |
| read without LRU bump | `mg key v u` |
| item debug | `me key` → `exp`, `la`, `cas`, `fetch`, `cls`, `size` |

Return codes: `VA` value follows, `HD` success without value, `EN` miss, `NS` not stored, `EX` CAS mismatch, `NF` not found, `MN` no-op. Errors: `ERROR`, `CLIENT_ERROR <msg>`, `SERVER_ERROR <msg>`.

Binary protocol: deprecated since 1.6.0, still accepted with `-B auto` (default). Needed only for SASL. New clients should use the meta protocol.

## Extstore (flash)

Keys, item headers and the hash table stay in RAM; values of eligible items move to a file on flash. Use it when values are much larger than keys, longer retention would raise the hit ratio, and RAM is the constraint. It needs flash storage, not rotational disks, and saves little for tiny values.

```
memcached -m 8192 -o ext_path=/mnt/nvme/extstore:200G
```

| Option | Default (1.6.45 `memcached -h`/`stats settings`) | Meaning |
| --- | --- | --- |
| `ext_item_size` | 512 bytes | only larger items are flushed; raise it (for example to 65536) to flush only big values and cut flash writes |
| `ext_item_age` | no age limit | only items idle at least this long |
| `ext_page_size` | 64 MB | storage page |
| `ext_wbuf_size` | 4 MB | write buffer |
| `ext_threads` | 1 | I/O threads; raise only if read latency is high while the drive is idle; stay at 8 or fewer |
| `ext_compact_under` / `ext_drop_under` | 1% / 1/4 of storage | when compaction / dropping of COLD items starts |
| `ext_max_frag` | 0.80 | compact pages less full than this |
| `ext_recache_rate` | 2000 | 1-in-N chance to pull a frequently read flash item back into RAM |
| `ext_low_ttl` | 0 (off) | colocate short-TTL items to reduce compaction |

The extstore documentation page gives different defaults for `ext_wbuf_size` (8 MB) and `ext_compact_under` (1/4 of pages) than the 1.6.45 binary; trust `memcached -h` and `stats settings` on the running version.

Rules: the flash contents are indexed only in RAM, so a restart empties flash. `incr`/`decr`/`append`/`prepend` do not work on flushed items and UDP cannot read them. If writes outpace flushing, memcached evicts from the RAM tail instead of waiting. Watch `evictions`, per-class `age`, the `extstore_*` counters in `stats`, `stats extstore`, and device write volume (flash endurance). Runtime tuning: `extstore item_size 4096` and the other `extstore` subcommands. 1.6.41 fixed a compaction bug, present since extstore was written, that could lose frequently accessed items; run 1.6.41 or later with extstore.

## Built-in proxy

Since 1.6.23 a proxy-enabled build can route requests to pools of backend memcached servers: clients connect to the proxy with the basic or meta protocol; the proxy picks a pool by key prefix, listener port or route handler, then a backend in the pool by consistent hash. Pools can be grouped into sets and zones for failover priorities; handlers such as `route_allsync` send a request to several pools in parallel.

- The proxy is not enabled in default source builds; compile with proxy support. The official `memcached:1.6` image (1.6.45) has it compiled in. Start with `-o proxy_config=routelib,proxy_arg=/etc/memcached/routes.lua` (`routelib` selects the bundled route library; `proxy_arg` passes the route config file).
- Use it to remove hashing logic from heterogeneous clients, to migrate pools, and for zone-local reads.
- 1.6.39 through 1.6.45 contain many proxy fixes (memory corruption, overflows); run 1.6.45.
- In the official image, `-o proxy_config=routelib` loads the bundled route library and, without `proxy_arg`, exits with a Lua error from `load_userconfig`; started without `proxy_config`, `stats settings` shows `proxy_enabled no`.

## Warm restart

`-e /dev/shm/memcached.mem` (file on tmpfs or a DAX mount, large enough for `-m`) keeps item memory in an mmap file. Stop with `SIGUSR1` (or `shutdown graceful` when `-A` is set); the next start with compatible settings rebuilds the hash table in seconds (minutes near a billion items). Changing `-m`, `-I`, slab chunk sizes, CAS or slab reassignment starts empty. The clock must not jump while the server is down, and sets and deletes sent during the restart are missed: use it only when the application can pause writes or tolerate that window. Incompatible with extstore. Main use: binary upgrades without a cold cache.

## Security

Memcached is built for trusted networks. Defaults that matter (1.6.45):

| Item | Default | Action |
| --- | --- | --- |
| listen address | all interfaces (`INADDR_ANY`; the image listens on `0.0.0.0:11211` and `[::]:11211`) | set `-l 10.0.0.5`, or a Unix socket with `-s` (disables TCP/UDP) |
| UDP | off since 1.5.6 | keep `-U 0` |
| authentication | none | SASL (`-S`, binary protocol only, no encryption) or ASCII auth file (`-Y`, experimental) |
| TLS | off; build with `--enable-tls` | `-Z -o ssl_chain_cert=...,ssl_key=...` |
| `shutdown` command | disabled | enable with `-A` only where needed |
| `flush_all` | enabled | `-F` disables it |
| `stats cachedump`, `stats detail`, `lru_crawler metadump` | enabled | `-X` disables them |
| `watch` (live logging) | enabled | `-W` disables it |

- Never expose memcached to the internet or untrusted users; the project says SASL helps but should not be fully trusted.
- TLS: needs OpenSSL 1.1.1 or later. `ssl_verify_mode` 0 none (default), 1 request, 2 require, 3 once; `ssl_ca_cert` for accepted client CAs; `ssl_min_version` default TLS 1.2. Per-listener control with prefixes `notls:`, `btls:`, `mtls:` in `-l`. Rotate certificates with `refresh_certs` (same file paths) or `SIGHUP` (1.6.40+); `stats` shows `time_since_server_cert_refresh`. `ssl_wbuf_size` (16 KB) per worker thread is extra memory.
- SASL: build with `--enable-sasl`, start with `-S`; the server then accepts only the binary protocol and requires authentication before any command. Text and meta clients cannot use SASL.
- ASCII auth (`-Y <file>` with `user:pass` lines): clients authenticate with a `set` whose payload is `username password`. 1.6.43 enforced ASCII auth more strictly and 1.6.44 fixed a crash with auth enabled and empty lines; use 1.6.45.

## Stats and diagnosis

| Command | Use |
| --- | --- |
| `stats` | global counters: connections, memory, evictions, hits and misses |
| `stats settings` | effective configuration; compare with the intended start options |
| `stats slabs` | per class: `chunk_size`, `total_pages`, `used_chunks`, `free_chunks`, hits per class |
| `stats items` | per class: `number_hot/warm/cold`, `age`, evictions, `evicted_time`, crawler counters |
| `stats sizes` | size histogram (needs `-o track_sizes`) |
| `stats conns` | per-connection state |
| `stats extstore` | extstore detail |
| `stats detail on` / `stats detail dump` | per-prefix stats (prefix delimiter `-D`, default `:`); adds overhead |
| `lru_crawler metadump all` | one line per item without locking the cache; output starts with `OK` since 1.6.43 |
| `watch fetchers mutations evictions` | live log stream; use briefly |
| `me <key>` | metadata of one item |

Readings:

- Hit ratio = `get_hits / (get_hits + get_misses)`. Misses on keys that are never set (for example flags of absent users) depress it; cache an explicit "not set" marker instead.
- High `get_expired` relative to hits suggests TTLs shorter than the reuse interval (interpretation). High `evictions` with small `evicted_time` means too little memory or misallocated slabs.
- Memory pressure: `bytes` against `limit_maxbytes`; per-class `total_pages` against evictions (see slab rebalancing).
- Connection pressure: `listen_disabled_num`, `rejected_connections`, `curr_connections`, `max_connections`.
- Unexpected flushes: alert when `cmd_flush` increases.
- Wasted writes: `evicted_unfetched` and `expired_unfetched` count items stored but never read.
- Restart detection: `uptime` resets; a cold-cache period follows.

Triage for "the cache got slow" or "database load spiked":

1. `uptime` and `cmd_flush` on every node (restart or flush = cold cache).
2. Hit ratio per node; one node with low hits points to a client hashing mismatch or a recent restart.
3. `listen_disabled_num` and `curr_connections` against `max_connections`.
4. Worker CPU (`rusage_user`, `rusage_system` deltas) against `threads`; `conn_yields` for heavy pipeliners.
5. Evictions and `evicted_time`, then slab distribution.
6. Host: swap, NIC errors, dropped packets.

## Common mistakes

- Treating `-m` as the process memory limit.
- Raising `-I` to store multi-megabyte values instead of compressing or splitting them.
- Different server lists or hash settings across clients.
- Exposing port 11211 to untrusted networks or enabling UDP.
- Assuming SASL encrypts traffic.
- Using `flush_all` for invalidation in production; it clears the whole node.
- Long `watch` sessions or `stats cachedump` on busy nodes; prefer `lru_crawler metadump` for item listings.
- Restarting every node at once during an upgrade; roll one node at a time.
