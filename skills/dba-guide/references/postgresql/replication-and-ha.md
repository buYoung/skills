# Replication and High Availability

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)). The core server provides replication and promotion; automatic failover needs an external cluster manager, which is outside the official documentation and this reference.

## Choosing a mechanism

| Need | Use | Notes |
| --- | --- | --- |
| Hot standby for failover and read scaling | physical streaming replication | whole cluster, same major version and platform, byte-identical |
| Zero data loss on primary failure | physical replication with `synchronous_standby_names` | commit waits for standby acknowledgment |
| Replicate a subset of tables, to a different major version, or to another system | logical replication (publications/subscriptions) | row-level changes; DDL and (before 19) sequences are not replicated |
| Major upgrade with minimal downtime | logical replication old → new | see [backup-and-recovery.md](backup-and-recovery.md) and [versions/index.md](versions/index.md#upgrade-paths) |
| Delayed copy to recover from human error | physical standby with `recovery_min_apply_delay` | combine with PITR, not instead of it |

## Physical streaming replication

Primary settings (defaults on 14 to 19 per container): `wal_level = replica`, `max_wal_senders = 10`, `max_replication_slots = 10`, `hot_standby = on`. Add a `pg_hba.conf` line for the `replication` pseudo-database and a role with `REPLICATION`.

Create a standby:

```bash
pg_basebackup -h primary -U replicator -D /var/lib/postgresql/data \
  --wal-method=stream --checkpoint=fast --progress \
  --create-slot --slot=standby1 --write-recovery-conf
```

`--write-recovery-conf` (`-R`) writes `primary_conninfo` and `primary_slot_name` to `postgresql.auto.conf` and creates `standby.signal`. Start the server; it streams from the primary.

Use a physical replication slot (above) so the primary keeps WAL the standby still needs. Then cap the risk: a down standby with a slot makes the primary keep WAL until the disk fills.

- `max_slot_wal_keep_size` (default -1 = unlimited) limits WAL held by slots; exceeding it invalidates the slot (`wal_status = lost`) and the standby must be rebuilt. Set it below the free space of `pg_wal`.
- 18+: `idle_replication_slot_timeout` invalidates slots idle for longer than the timeout.
- Without slots, `wal_keep_size` keeps a fixed amount of WAL; a standby that falls further behind needs WAL from the archive (`restore_command`) or a rebuild.

### Monitoring lag

On the primary:

```sql
SELECT application_name, client_addr, state, sync_state,
       pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) AS replay_lag_bytes,
       write_lag, flush_lag, replay_lag
FROM pg_stat_replication;

SELECT slot_name, slot_type, active, wal_status, safe_wal_size,
       pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) AS retained_bytes
FROM pg_replication_slots;
```

On the standby:

```sql
SELECT pg_is_in_recovery(), pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn(),
       now() - pg_last_xact_replay_timestamp() AS replay_delay;
SELECT status, sender_host, last_msg_receipt_time FROM pg_stat_wal_receiver;
```

`replay_delay` grows when the primary is idle even without lag; compare LSNs as well. 19 adds `pg_stat_recovery` and a `connecting` status in `pg_stat_wal_receiver`.

### Standby query conflicts

Replay can conflict with long queries on the standby (the primary vacuumed rows a standby query still needs). The standby cancels the query after `max_standby_streaming_delay` (default 30s).

| Option | Effect | Cost |
| --- | --- | --- |
| `hot_standby_feedback = on` (default off) | primary keeps rows the standby needs | standby queries can bloat the primary |
| Raise `max_standby_streaming_delay` | queries run longer | replay falls behind, failover target is stale |
| Separate reporting standby with high delay, failover standby with low delay | isolates the trade-off | one more server |

Check `pg_stat_database_conflicts` on the standby to see which kind of conflict cancels queries.

## Synchronous replication

```
synchronous_standby_names = 'FIRST 1 (standby1, standby2)'   # priority
synchronous_standby_names = 'ANY 1 (standby1, standby2, standby3)'  # quorum
```

`synchronous_commit` controls what a commit waits for:

| Value | Commit waits until | Data loss on primary crash |
| --- | --- | --- |
| `remote_apply` | standby has replayed | none, and reads on the standby see it |
| `on` (default) | standby has flushed WAL to disk | none |
| `remote_write` | standby OS has received it | possible if the standby OS also crashes |
| `local` | local flush only | standby may miss recent commits |
| `off` | not even local flush (up to 3 x `wal_writer_delay`) | recent commits lost, no corruption |

Decision rules:

- With one synchronous standby and `FIRST 1`, losing that standby stops all commits. Use at least two candidates (`FIRST 1 (a, b)` or `ANY 1 (a, b)`).
- Set `synchronous_commit = local` or `off` per transaction for low-value writes (`SET LOCAL synchronous_commit = off;`) rather than globally.
- Synchronous replication protects committed data, not availability; it adds a network round trip to every commit.

## Failover and switchover

Planned switchover (no data loss):

1. Confirm the target standby is caught up: `pg_stat_replication.replay_lsn` equals `pg_current_wal_lsn()` after stopping writes.
2. Shut down the primary cleanly (`pg_ctl stop -m fast`); it sends remaining WAL to connected standbys. On 19, `wal_sender_shutdown_timeout` can bound this wait (default -1 waits forever).
3. Promote the standby: `SELECT pg_promote();` or `pg_ctl promote`.
4. Point clients to the new primary (DNS, proxy, or connection string with multiple hosts and `target_session_attrs=read-write`).
5. Turn the old primary into a standby with `pg_rewind` (requires `wal_log_hints = on` or data checksums on the old primary) or rebuild it with `pg_basebackup`.

Unplanned failover: same promotion step, but first make sure the old primary cannot accept writes (fence it: stop it, revoke its network access) to avoid split brain. With asynchronous replication, commits not yet replicated are lost; quantify with the last known `replay_lsn`.

Verify after failover: `SELECT pg_is_in_recovery();` returns `false` on the new primary; remaining standbys follow the new timeline (`recovery_target_timeline = 'latest'` is the default; container confirms); slots exist where needed on the new primary (physical slots are not copied by promotion).

## Logical replication

```sql
-- publisher (wal_level = logical; on 19 'replica' also works once a logical slot exists)
CREATE PUBLICATION app_pub FOR TABLE orders, customers;
-- subscriber (tables must already exist with compatible definitions)
CREATE SUBSCRIPTION app_sub
  CONNECTION 'host=pub dbname=app user=repl'
  PUBLICATION app_pub;
```

Requirements and limits:

- Each published table needs a primary key or `REPLICA IDENTITY` (`USING INDEX` or `FULL`) for `UPDATE`/`DELETE` to replicate. `FULL` makes the subscriber search by all columns (16+ can use a B-tree index for it).
- Not replicated: DDL, `TRUNCATE` of tables not in the publication, large objects; sequences before 19. On 19, `FOR ALL SEQUENCES` and `ALTER SUBSCRIPTION ... REFRESH SEQUENCES` synchronize sequence values.
- Each subscription holds a logical slot on the publisher. A stopped or failing subscriber makes the publisher retain WAL and `catalog_xmin` (bloat in catalogs). Monitor `pg_replication_slots` and `pg_stat_subscription_stats` (error counts, 18+ conflict counts).
- Conflicts (duplicate key on insert, missing row) stop the apply worker; the subscriber log shows the error and the LSN. Fix the data, or skip the transaction with `ALTER SUBSCRIPTION app_sub SKIP (lsn = '0/14C0378');` (15+). Use `disable_on_error = true` to stop retry loops.
- Apply runs as the table owner on 16+ (subscription owner needs `SET ROLE` on owners, or `run_as_owner = true`).
- 18 default `streaming = parallel` applies large in-progress transactions with parallel workers.
- 19 `wal_level = replica` with logical slots: the effective level becomes logical when the first logical slot is created and drops back when the last one is dropped, which invalidates logical slots on standbys. Check `SHOW effective_wal_level;`.

`pg_createsubscriber` (17+) turns a physical standby into a logical subscriber without an initial copy.

## Failover slots (17+)

Without them, a physical failover loses the publisher's logical slots and subscribers must resynchronize.

Setup (19 docs; 17+):

1. Create slots with failover enabled: `CREATE SUBSCRIPTION ... WITH (failover = true)` or `pg_create_logical_replication_slot('s', 'pgoutput', false, false, true)`.
2. On the standby: `sync_replication_slots = on`, `hot_standby_feedback = on`, `primary_slot_name` set (physical slot to the primary), and `primary_conninfo` must include a valid `dbname`.
3. On the primary: list the standby's physical slot in `synchronized_standby_slots` so subscribers never get ahead of the standby. Shutdown of the primary then waits for those standbys.
4. Check on the standby: `SELECT slot_name, synced, failover, invalidation_reason FROM pg_replication_slots;` Only slots with `synced = true` before failover can be used afterwards. 19 adds `slotsync_skip_reason`.
5. At failover: disable subscriptions, promote, then `ALTER SUBSCRIPTION ... CONNECTION '<new primary>'` and enable. If the old primary comes back while subscriptions are enabled, subscribers can receive changes from both.

## Read-your-writes on replicas (19)

After a write on the primary, capture an LSN and wait for it on the replica before reading:

```sql
-- primary, after COMMIT
SELECT pg_current_wal_insert_lsn();          -- e.g. 0/0306EE20
-- standby, as the first statement (outside a transaction or before any snapshot)
WAIT FOR LSN '0/0306EE20' WITH (TIMEOUT '200ms', NO_THROW);   -- returns success | timeout | not in recovery
```

`WAIT` cannot run inside a function or after the transaction has taken a snapshot or a lock. Before 19, poll `pg_last_wal_replay_lsn() >= $lsn` instead, or send such reads to the primary.

## Common mistakes

- Physical slots for decommissioned standbys left in place: WAL fills the disk.
- Assuming `hot_standby_feedback` is free.
- Running a single synchronous standby.
- Promoting without fencing the old primary.
- Forgetting that logical replication does not copy DDL: apply schema changes to the subscriber first (additive changes) or in lockstep.
