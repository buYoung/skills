# Initial Coverage Record (2026-11-27)

## Scope

First release of the guide: eleven products, with Amazon RDS, Aurora, ElastiCache, MemoryDB, MongoDB Atlas, and Couchbase Capella described inside the engine they run. Facts were taken from official documentation, release notes, lifecycle pages, source at release tags, and runs of official container images, all checked on 2026-11-27. Each product's `versions/index.md` ends with the sources it used.

## Version Selection

Each product covers every series its vendor lists as supported on 2026-11-27, plus one series past end of support so that upgrades out of it are covered. Where a short-lived release that already ended sits between covered series, its changes are kept in the next covered file instead of a file of its own.

| Product | Covered | Past end of support | Folded into another file |
|---|---|---|---|
| MySQL | 8.4 LTS, 9.7 LTS, 26.10 Innovation | 8.0 (most recent ended series on the LTS track) | 26.7 Innovation in `26.10.md`; 9.0-9.6 Innovation in `9.7.md` |
| MariaDB | 10.11, 11.4, 11.8, 12.3 (long-term); 13.0, 13.1 (rolling) | 10.6 | 10.7-10.10 in `10.11.md`, 11.0-11.3 in `11.4.md`, 11.5-11.7 in `11.8.md`, 12.0-12.2 in `12.3.md` |
| PostgreSQL | 15, 16, 17, 18, 19 | 14 | none |
| MongoDB | 7.0, 8.0, 8.3, 9.0 | 8.2 (6.0 is handled as out of range) | none |
| Amazon DocumentDB | 4.0, 5.0, 8.0 | 3.6 (in paid Extended Support) | none |
| Azure Cosmos DB | Dated service changes, RU-based MongoDB server versions, Azure DocumentDB server versions, REST API versions, current SDK majors | retired SDKs and API versions listed in the track files | none |
| Couchbase Server | 7.6, 8.0 | 7.2 | none |
| Redis Open Source | 6.2, 7.2, 7.4, 8.0, 8.2, 8.8, 8.10, 8.12 | 8.6 | 8.4 in `8.6.md`; 7.0 in `7.2.md` |
| Valkey | 7.2, 8.0, 8.1, 9.0, 9.1, 9.2 | none ended | none |
| Memcached | 1.6 (no published support schedule) | none published; 1.5 is handled in the index's out-of-range guidance | none |
| Amazon DynamoDB | API 2012-08-10, dated changes 2024 to 2026, global tables 2019.11.21, DynamoDB Local 3.x | global tables 2017.11.29, DynamoDB Local 2.x | Local 1.x in `local-2.x.md` |

## Container Runs

All runs used official images on Docker Desktop (linux/arm64). Each product had a default dump (server variables, `pg_settings`, `getParameter`, `CONFIG GET *`, `stats settings`, REST settings endpoints) and a run of the statements the references use, including execution plans, lock and deadlock reproduction for MySQL, MariaDB, and PostgreSQL, single-node replica-set transactions for MongoDB, and SQL++ transactions for Couchbase. Follow-up runs checked individual statements in the references (plugin states, lock behavior, upgrade checks, defaults without startup overrides), and the text follows their results. Where an image and the documentation disagree, the reference states both and names the image version.

A review pass on the same date re-checked reviewer findings against primary sources and reran statements on the images below: reserved words and hash functions across MySQL patch releases, a new MariaDB lost-update example for ERROR 1020 (11.4, 11.8, 13.0), the MongoDB transaction limit on 7.0 and 8.0, Couchbase storage-engine migration on 7.6.13 and 8.0.4, `cluster-slot-stats-enabled` values across Redis 8.2 to 8.12, and 9.2-only Valkey commands on all Valkey lines.

| Image | Server reported | Digest |
|---|---|---|
| `mysql:8.0` | 8.0.46 | `sha256:7dcddc01f13b…` |
| `mysql:8.4.10` | 8.4.10 (patch-level comparison) | `sha256:8dbcf531a03a…` |
| `mysql:8.4` | 8.4.13 | `sha256:8c233bad33d5…` |
| `mysql:9.7.1` | 9.7.1 (patch-level comparison) | `sha256:cbade841779f…` |
| `mysql:9.7` | 9.7.4 | `sha256:1f2ca53a9e94…` |
| `mysql:26.7` | 26.7.0 | `sha256:625f74ddf936…` |
| `mysql:26.10` | 26.10.0 | `sha256:9092489f49fb…` |
| `mariadb:10.6` | 10.6.28 | `sha256:75079c0fb968…` |
| `mariadb:10.11` | 10.11.19 | `sha256:e5fe75b2b9de…` |
| `mariadb:11.4` | 11.4.13 | `sha256:a8992b5e5404…` |
| `mariadb:11.8` | 11.8.9 | `sha256:e1d5495f4456…` |
| `mariadb:12.3` | 12.3.3 | `sha256:4aaf88b31063…` |
| `mariadb:13.0` | 13.0.2 | `sha256:54f493ea0d60…` |
| `postgres:13` | 13 (one default check) | `sha256:4689940c6838…` |
| `postgres:14` | 14.25 | `sha256:c0e9c0e9bac7…` |
| `postgres:15` | 15.20 | `sha256:868b5ee21902…` |
| `postgres:16` | 16.16 | `sha256:ce8115080264…` |
| `postgres:17` | 17.12 | `sha256:97fb53376be3…` |
| `postgres:18` | 18.7 | `sha256:64c8b0d31e4a…` |
| `postgres:19` | 19.0 | `sha256:4ea94de574c1…` |
| `mongo:7.0` | 7.0.48 | `sha256:41e8195b2791…` |
| `mongo:8.0` | 8.0.38 | `sha256:479e85ced54f…` |
| `mongo:8.3` | 8.3.17 | `sha256:747773029b84…` |
| `mongo:9.0` | 9.0.8 | `sha256:b0c835c26e59…` |
| `redis:6.2` | 6.2.24 | `sha256:25e5c748e658…` |
| `redis:7.2` | 7.2.17 | `sha256:8ee762cfc4d7…` |
| `redis:7.4` | 7.4.12 | `sha256:6b645a37f49b…` |
| `redis:8.0` | 8.0.6 | `sha256:ae471bdc20de…` |
| `redis:8.2` | 8.2.11 | `sha256:bb3025172117…` |
| `redis:8.4` | 8.4.8 | `sha256:b9e537e7a394…` |
| `redis:8.6` | 8.6.8 | `sha256:876fabd22bbc…` |
| `redis:8.8` | 8.8.4 | `sha256:20ffc8432688…` |
| `redis:8.10` | 8.10.3 | `sha256:91cc9227bca4…` |
| `redis:8.12` | 8.12.0 | `sha256:56a1737794e3…` |
| `valkey/valkey:7.2` | 7.2.16 | `sha256:edf27a750238…` |
| `valkey/valkey:8.0` | 8.0.13 | `sha256:fcb69dfef815…` |
| `valkey/valkey:8.1` | 8.1.12 | `sha256:5032c4dd7abe…` |
| `valkey/valkey:9.0` | 9.0.8 | `sha256:80def298b278…` |
| `valkey/valkey:9.1` | 9.1.4 | `sha256:3ab0eca823eb…` |
| `valkey/valkey:9.2` | 9.2.1 | `sha256:169567d6288e…` |
| `memcached:1.6` | 1.6.45 | `sha256:6b0fd5e4e0d5…` |
| `amazon/dynamodb-local:3.3.2` | 3.3.2 | `sha256:6ada631ec7aa…` |
| `amazon/dynamodb-local:latest` | 3.3.2 (same digest) | `sha256:6ada631ec7aa…` |
| `amazon/aws-cli:latest` | AWS CLI 2.42.4, offline only | `sha256:4a1a668837d5…` |
| `couchbase/server:7.6.13` | 7.6.13 Enterprise | `sha256:97b57c69d6b4…` |
| `couchbase/server:8.0.4` | 8.0.4 Enterprise | `sha256:a84e05d6ec55…` |
| `couchbase/server:community-8.0.2` | 8.0.2 Community | `sha256:ff359b4b753e…` |
| `mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:vnext-preview` | emulator release EN20261123 | `sha256:c274ac17c19a…` |

## Documentation Only

- Amazon DocumentDB: no container, emulator, or self-hosted build exists. AWS CLI option names were checked offline with `amazon/aws-cli`, and one mongosh script with `mongo:8.0`; engine behavior rests on AWS documentation.
- Azure Cosmos DB service behavior: the vNext emulator ran on arm64, but it charges 1 RU for every request, advertises Strong consistency, and accepted several requests the service rejects. Emulator results are labeled as emulator behavior in `cosmos-db/emulator.md`.
- DynamoDB service behavior: only DynamoDB Local runs in a container; service limits, throttling, global tables, PITR, and capacity behavior come from the Developer Guide.
- Managed services (RDS, Aurora, ElastiCache, MemoryDB, Atlas, Capella, Azure DocumentDB): documentation only; no cloud account was used.
- MariaDB 13.1: no GA image was published on the check date (`13.1-rc` only), so `13.1.md` rests on release notes.
- Couchbase 7.2 and multi-node behavior (rebalance, failover, XDCR), MongoDB elections and sharding, MySQL Group Replication, and replication failover in general: documentation only, because each run used one container.

Where neither an official source nor a run settled a claim, the reference does not state it as fact. It names how to check instead: a command to run, a console item to read, or the official page to watch. Statements derived from documented behavior but not stated by the vendor are labeled as inference or as a guideline. Conflicts between vendor pages are quoted side by side.

## Adding a Release

1. Read the vendor's lifecycle page and the release notes of the new series; record the page and date in the product's `versions/index.md` Sources.
2. Add `versions/<series>.md` with the same sections as its neighbors, update the Support Status table, and move a series that reached end of support to the previous-series slot, folding the older one into the index's out-of-range guidance.
3. Run the new official image with the same default dump and statements as the previous series and compare the outputs; record the image digest here or in a new dated record.
4. Update topic files only where the new series changes a decision, linking to the version file.
