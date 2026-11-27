# Consistency, Replication, and Failover

Checked: 2026-11-27. Read when choosing a consistency level, adding regions, enabling multi-region writes, planning failover and RPO/RTO, or handling write conflicts on Azure Cosmos DB. API mappings for MongoDB and Cassandra are noted where they differ.

## Contents

- [Replication model](#replication-model)
- [Consistency levels](#consistency-levels)
- [Choosing a level](#choosing-a-level)
- [Durability and RPO by configuration](#durability-and-rpo-by-configuration)
- [Single-write multi-region accounts and failover](#single-write-multi-region-accounts-and-failover)
- [Multi-region writes and conflicts](#multi-region-writes-and-conflicts)
- [Change feed](#change-feed)
- [Evidence and drills](#evidence-and-drills)
- [Common mistakes](#common-mistakes)

## Replication model

- Inside a region each physical partition is a replica set of four replicas. Writes commit to a local majority (three of four) at every consistency level.
- Across regions, replication is asynchronous except under strong consistency, which commits in every region (global majority) before acknowledging.
- Zone redundancy spreads a region's replicas across availability zones; Microsoft picks the zones.
- Serverless accounts run in one region only (availability zones in supported regions).
- Read regions can be added or removed at any time; RU/s are provisioned in every region.

## Consistency levels

From strongest to weakest. Read consistency is scoped to one logical partition.

| Level | Read guarantee | Read quorum | Write quorum | Read RU cost |
| --- | --- | --- | --- | --- |
| Strong | Linearizable; latest committed write | Local minority (2 replicas) | Global majority (every region) | about 2x |
| Bounded staleness | Lag between regions below K versions or T seconds | Local minority | Local majority | about 2x |
| Session | Read-your-writes and write-follows-reads within a session token | Single replica, session token | Local majority | 1x |
| Consistent prefix | No out-of-order view of transactional batches | Single replica | Local majority | 1x |
| Eventual | No ordering | Single replica | Local majority | 1x |

Details that change decisions:

- The default level is Session (MongoDB consistency-mapping page).
- Session tokens are per partition. A client that has never written to a physical partition, or that was re-created, reads that partition with eventual semantics until its own writes rebuild the token cache. To let another process read its own writes, pass `x-ms-session-token` to it unchanged.
- A per-request override can only weaken the account level (`x-ms-consistency-level` header or SDK option). On a strong account, reads overridden to session use one replica, but writes still replicate synchronously to every region. The vNext emulator doesn't validate the header ([emulator.md](emulator.md#observed-behavior-release-en20261123)).
- After changing the account default, restart applications so SDK clients pick it up.
- Bounded staleness minimums: single region K=10 writes or T=5 seconds; multi-region K=100,000 or T=300 seconds. If a region's lag on a partition exceeds the bound, writes to that partition are throttled.
- Bounded staleness on a multi-write account is an anti-pattern; strong is not available with multiple write regions.
- Strong consistency for accounts spanning more than 5,000 miles (8,000 km) is blocked by default; enabling it needs a support request.
- Dynamic quorum: with three or more regions under strong consistency, unresponsive regions can be dropped from the quorum (one region for 3-4 regions, two for 5). Dropped regions don't serve reads until re-added.
- Gremlin and Table use the account default level. MongoDB maps write concern to the account default and maps read concern per request; client write concern values are ignored (all writes are quorum). Cassandra has its own mapping page (cassandra/consistency-mapping; page not checked).

Latency on the consistency page: reads and writes under 10 ms at p99 for all levels, except writes on multi-region strong accounts, which take about 2 x RTT between the two farthest regions plus 10 ms at p99.

## Choosing a level

1. Default to Session for user-facing apps that read their own writes through the same client.
2. Use Strong only when a stale read anywhere is unacceptable and the regions are close; it doubles read RUs and adds cross-region RTT to every write. It gives RPO 0 in single-write accounts.
3. Use Bounded staleness for single-write, multi-region accounts that want near-strong reads in other regions with a defined lag bound; it also doubles read RUs.
4. Use Consistent prefix or Eventual for counters, feeds, and analytics reads where ordering doesn't matter; they give the most read throughput per RU.
5. With multi-region writes, choose Session or weaker and keep each client's reads and writes in its local region.

## Durability and RPO by configuration

From the consistency page:

| Regions | Write regions | Consistency | RPO in a region outage |
| --- | --- | --- | --- |
| 1 | single or multiple | any | under 240 minutes |
| more than 1 | single | Session, Consistent prefix, Eventual | under 15 minutes |
| more than 1 | single | Bounded staleness | K and T |
| more than 1 | single | Strong | 0 |
| more than 1 | multiple | Session, Consistent prefix, Eventual | under 15 minutes |
| more than 1 | multiple | Bounded staleness | K and T |

A single-region account depends on that region's recovery. Backups are a separate risk control; see [operations.md](operations.md#backup-and-restore).

## Single-write multi-region accounts and failover

Failover types (reliability guide for Cosmos DB for NoSQL):

| Type | Who triggers | Data loss | Typical recovery | Use |
| --- | --- | --- | --- | --- |
| Per-partition automatic failover (PPAF) | Service, per partition | Unreplicated writes on affected partitions can be lost unless strong | About 3 minutes for affected partitions | Partial-region failures; NoSQL only |
| Forced failover (offline region) | You | Unreplicated writes in the old write region can be lost | Seconds once triggered; you must detect the outage | Recommended fast path during a real outage; DR drills |
| Change write region | You, regions healthy | None; replication catches up first | Brief interruption | Planned moves; fails during an outage |
| Service-managed failover | Microsoft, account level | Unreplicated writes can be lost | Declaring the outage can take an hour or more | Last resort; don't wait on it |

PPAF requirements: single write region with at least one read region; strong, session, consistent prefix, or eventual consistency (bounded staleness not yet supported); API for NoSQL; global Azure region; SDKs .NET 3.62.0+, Java 4.79.0+, Python 4.16.0+, Node.js 4.7.0+, Rust 1.0.0+. Upgrade every client before enabling it, or writes can fail during a partition failover. PPAF is billed as part of the Business Critical service tier. Metric `PartitionWriteGlobalStatus` counts write partitions per region.

For read-region outages, client configuration matters more than the failover type: set the SDK preferred-regions list so reads move to the next region without any service-side failover.

During an outage, don't run control-plane changes on the affected account (change write region, failover priorities, switching to multi-write, consistency changes, network or private endpoint changes, throughput changes). The reliability guide says they cause account inconsistency and delay recovery. After a forced or service-managed failover, Microsoft brings the region back online; for healthy regions this is automated but can take several days. With private endpoints, check private DNS routing after an offline-region operation.

Regional failovers are limited to 10 per hour per account (single-write accounts only).

## Multi-region writes and conflicts

- The first region is the hub. Writes in satellite regions commit locally, then go to the hub for conflict resolution; until then they are tentative. Writes in the hub are confirmed immediately.
- Two timestamps: `_ts` (local write time) and `crts` (conflict-resolution time, set by the hub). Change feed orders by `crts` on multi-write accounts.
- Strong consistency is not allowed. Lightweight transactions in API for Cassandra are not supported on multi-write accounts.
- Raw REST clients on multi-write accounts: the request-headers page says `x-ms-cosmos-allow-tentative-writes: true` allows writes to all locations, and that write requests without it (or with `false`) fail with 403 "Writes are not allowed in the region".

Conflict types: insert (same `id` in two regions), replace (same item updated in two regions), delete (delete in one region, update in another).

| Policy | Behavior | Availability |
| --- | --- | --- |
| Last writer wins (default) | Highest value of the conflict-resolution path wins; default path `/_ts`; delete always wins over insert or replace | All APIs; custom numeric path only for NoSQL |
| Custom | Registered merge stored procedure runs exactly once per conflict; if missing or failing, conflicts go to the conflicts feed for the application to resolve | NoSQL only; set at container creation only |

Container definitions show the policy; the vNext emulator returned `"conflictResolutionPolicy": {"mode": "LastWriterWins", "conflictResolutionPath": "/_ts"}` for a new container.

Practices from the multi-region-writes page:

- Send each client's reads and writes to its local region only. Don't send the same write to all regions, pick regions randomly, or round-robin.
- Don't make reads in region B depend on writes in region A; that depends on replication lag.
- Pass session tokens between client instances for reads only, not writes. A write carrying a token from another region waits for the receiving region to catch up.
- Avoid rapid repeated updates to one document; they overlap with conflict resolution and raise latency.

Restore of multi-write accounts restores only hub-confirmed writes; containers with a custom conflict policy come back with last writer wins on `_ts`.

## Change feed

- Enabled on every container. Reads consume RUs; the change feed processor also needs a lease container.
- Latest version mode: inserts and updates, the latest version of each item only, readable from the container's beginning, a point in time, or now. Deletes and TTL expirations are not included.
- All versions and deletes mode (NoSQL only): every create, update, delete, and TTL expiration within the continuous backup retention window. Requires continuous backup. Enable it with the account feature or `"enableAllVersionsAndDeletesChangeFeed": true` (preview API version `2024-12-01-preview` or later); enabling takes up to 30 minutes and can't be done at account creation. It can start only from now or from a saved lease or continuation token, doesn't return previous images, and isn't available on accounts that ever used partition merge.
- Ordering is guaranteed per partition key value only. Items written in one batch, stored procedure, or bulk request share a modification time and can arrive in any order.
- Delivery: each change appears once; the change feed processor gives at-least-once processing with automatic checkpoints, so make consumers idempotent.
- Multi-region: changes in one region are visible in all. On multi-write accounts, latest version mode can drop an update that lost to a newer change in another region; all versions and deletes mode captures all.
- API for MongoDB exposes it as change streams; API for Cassandra as a query with predicate.

Over REST, a change feed read is a GET on the documents feed with `A-IM: Incremental feed` and `x-ms-documentdb-partitionkeyrangeid`; each item carries `_lsn` (observed on the vNext emulator). On the emulator an item deleted with 204 was absent from a later latest-version read from the beginning.

## Evidence and drills

```bash
# Account replication and consistency configuration
az cosmosdb show -g <rg> -n <account> --query "{consistency:consistencyPolicy, multiWrite:enableMultipleWriteLocations, autoFailover:enableAutomaticFailover, locations:locations[].{name:locationName, priority:failoverPriority, zoneRedundant:isZoneRedundant}}"
```

Data-plane view: `GET /` on the account endpoint returns `writableLocations`, `readableLocations`, `userConsistencyPolicy`, and `enableMultipleWriteLocations`. The vNext emulator returns one location and `Strong` unless started with `--default-consistency-level` ([emulator.md](emulator.md#feature-support-that-changes-test-results)).

Metrics to watch: Probabilistically Bounded Staleness (how often reads are stronger than configured), replication latency (portal Metrics > Consistency), Total Requests split by region and status code, `PartitionWriteGlobalStatus` for PPAF.

Drills:

- Forced failover drill on a non-production account: take the write region offline, measure the time until writes succeed in the new region, and count lost or duplicated writes. Microsoft then brings the offline region back, which can take days; schedule the next drill accordingly.
- PPAF drill: the PPAF page provides a fault-injection script (`EnableDisableChaosFault.ps1`, fault type `PerPartitionAutomaticFailover`); it affects 10% of the container's partitions (minimum 1, maximum 10) and takes up to 15 minutes to start and to stop.

## Common mistakes

- Choosing Strong for a multi-continent account without measuring write latency (2 x RTT plus 10 ms at p99).
- Expecting read-your-writes after re-creating the SDK client, or across processes without passing the session token.
- Enabling multi-region writes and then reading in a different region than the write.
- Waiting for service-managed failover during an outage instead of a forced failover.
- Running scaling or configuration changes on an account during a regional incident.
- Using latest version change feed to propagate deletes; deletes don't appear. Use soft-delete markers with TTL, or all versions and deletes mode.
