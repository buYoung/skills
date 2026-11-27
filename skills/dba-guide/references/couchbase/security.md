# Couchbase Security

Checked: 2026-11-27 (sources at the end). Applies to Couchbase Server 7.2–8.0. Capella's model is in [managed-services.md](managed-services.md).

## Authentication

- Local users (domain `local`), external users (LDAP, domain `external`), SAML single sign-on for the Web Console (7.6+), and client X.509 certificates. Internal service users such as `@cbq-engine` and `@goxdcr` exist and appear in audit records.
- Client-certificate authentication can be disabled, enabled, or mandatory. 8.0 adds `Hybrid` (certificate or password; requires `clusterEncryptionLevel` `all` or `strict`). From 8.0, certificate authentication can be combined with node-to-node encryption. The upgrade page disables it with `couchbase-cli ssl-manage ... --set-client-auth-state disabled`, but `ssl-manage -h` in the 7.6.13 and 8.0.4 images lists no such flag. They offer `--set-client-auth <path>` ("A path to a file containing the client auth configuration") and `--client-auth` (show the current setting).
- SCRAM-SHA1, SHA256, and SHA512 are all enabled in both containers (`scramSha1Enabled`, `scramSha256Enabled`, `scramSha512Enabled` true in `/settings/security`).
- Password hashing: Argon2id for new passwords from 7.6. Container values: `"passwordHashAlg":"argon2id"`, `argon2idTime` 3, `argon2idMem` 524288. Users created before the upgrade keep their SHA1-based hashes until migration is enabled with `allowHashMigrationDuringAuth` (false by default). Migration requires every node on 7.6+.
- 8.0 (EE): lock and unlock local users (active sessions and long-lived connections are cut immediately), force a password change at next login, and track last activity of local users toward the cluster manager. Activity tracking does not cover application traffic.
- 7.6: internal credentials can be rotated on demand. The container shows `intCredsRotationInterval` 1800000 ms.

```sh
# Create an application user limited to one collection
couchbase-cli user-manage -c 127.0.0.1:8091 -u Administrator -p password --set \
  --rbac-username app_rw --rbac-password '***' --auth-domain local \
  --roles 'data_reader[app:inv:orders],data_writer[app:inv:orders],query_select[app:inv:orders]'
# Inspect
curl -s -u Administrator:password http://127.0.0.1:8091/settings/rbac/users | jq '.[] | {id, domain, roles}'
```

Both containers accepted this `user-manage` command (`SUCCESS: User app_rw set`), and `/settings/rbac/users` listed each role with `bucket_name`, `scope_name`, and `collection_name`. 8.0 also accepts SQL++ `CREATE USER`, `ALTER USER`, `DROP USER`, and the matching `GROUP` statements.

## RBAC Roles

Most roles are Enterprise-only. Community Edition has `admin` (Full Admin) and `ro_admin` (Read-Only Admin). The `community-8.0.2` container lists those two plus `bucket_full_access`.

| Level | Roles (identifiers) |
|---|---|
| Cluster | `admin`, `ro_admin`, `security_admin`, `ro_security_admin` (8.0), `user_admin_local` (8.0), `user_admin_external` (8.0), `cluster_admin`, `eventing_admin`, `backup_admin`, `replication_admin`, `query_system_catalog`, `query_manage_system_catalog`, `query_external_access`, `query_manage_global_functions`, `query_execute_global_functions`, `query_manage_global_external_functions`, `query_execute_global_external_functions`, `analytics_reader`, `analytics_admin`, `query_use_sequential_scans` (7.6), `external_stats_reader` (External Stats Reader; identifier from `/settings/rbac/roles` on both containers) |
| Bucket | `bucket_admin`, `scope_admin`, `views_admin`, `views_reader`, `replication_target`, `data_backup`, `analytics_manager`, `mobile_sync_gateway`, Search Admin and Search Reader (the backup docs name `fts_admin`), `bucket_full_access` (deprecated; do not grant) |
| Scope | `query_manage_functions`, `query_execute_functions`, `query_manage_external_functions`, `query_execute_external_functions`, `query_manage_sequences`, `query_use_sequences`, `eventing_manage_functions` |
| Collection | `data_reader`, `data_writer`, `query_select`, `query_insert`, `query_update`, `query_delete`, `query_manage_index` |
| Bucket, scope, or collection | `data_dcp_reader`, `data_monitoring`, `query_list_index`, `analytics_select`, Sync Gateway roles |

Decision rules:

- Give applications collection-level `data_reader`/`data_writer` for KV and the matching `query_*` roles for SQL++. KV and Query privileges are separate. A user with `data_reader` but no `query_select` cannot run `SELECT`.
- Give monitoring agents External Stats Reader (enough for `/metrics` and `/prometheus_sd_config`) and `query_system_catalog` for the restricted system keyspaces. Do not grant `ro_admin` just to read stats.
- Backup jobs: `data_backup` on the buckets, plus `eventing_admin`, `fts_admin`, and `analytics_admin` if Eventing, Search alias, and Analytics metadata must be included. Otherwise use `admin`.
- XDCR: `replication_admin` for the user who manages replications on the source, and `replication_target` (XDCR Inbound) on the target bucket for the user named in the remote reference.
- `query_use_sequential_scans` lets queries run with no index. Grant it only for small keyspaces.

8.0 role changes (check after upgrade, and after restoring pre-8.0 users):

- `ro_admin` lost security reads. They moved to `ro_security_admin`, which upgrade grants to every `ro_admin` holder. From 8.0.1, `ro_security_admin` can also list users and groups (MB-70597).
- The 7.x roles Local User Security Admin and External User Security Admin (`security_admin_local` and `security_admin_external` on 7.6.13) became `user_admin_local` and `user_admin_external`. Their extra security privileges moved to `security_admin`. Upgrade grants affected users the new role plus `security_admin`.
- 8.0.1 MB-70629 reports that groups holding `security_admin_local`, `security_admin_external`, or `ro_admin` were not converted correctly on upgrade, or on restore of a pre-8.0 backup. Fix them by hand. The release note's replacement names (`local_user_admin`, `external_user_admin`) differ from the roles page (`user_admin_local`, `user_admin_external`). Use the roles page identifiers: 8.0.4's `/settings/rbac/roles` lists `user_admin_local`, `user_admin_external`, and `ro_security_admin`, and no `security_admin_local` or `security_admin_external`.
- The user-admin roles cannot grant, or edit users holding, Full Admin, Read-Only Admin, the user-admin roles, or Security Admin.
- `security_admin` manages LDAP, SAML, certificates, encryption at rest, audit, and logging, but not users or groups.

```sh
# Who has which roles; review after upgrades
curl -s -u Administrator:password http://127.0.0.1:8091/settings/rbac/users | jq '.[] | {id, roles: [.roles[].role]}'
curl -s -u Administrator:password http://127.0.0.1:8091/settings/rbac/groups | jq .
```

## TLS: Clients

- Ports in the containers' `nodes[].ports`: KV `direct` 11210, `httpsMgmt` 18091, `httpsCAPI` 18092. Plain management is 8091, and Query is 8093. `nodes[].ports` does not list the KV TLS port (11207) or the Query TLS port (18093), but `netstat -ltn` shows both listening in both containers.
- Minimum TLS version: `tlsv1.2` (default; container) or `tlsv1.3`. TLS 1.0 and 1.1 were removed in 7.6, and upgrades raise lower settings to 1.2. It can be set globally or per service (`/settings/security/<service>`).
- Cipher suites: the server's order is used by default (`honorCipherOrder` true). Custom lists must be subsets of each service's supported list, which `/settings/security` shows per service. For HTTP/2 over TLS 1.2, a custom list must include `TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256`. Only the Cluster Manager, Data, and Analytics services accept custom TLS 1.3 suite lists.

```sh
couchbase-cli setting-security -c 127.0.0.1:8091 -u Administrator -p password --set --tls-min-version tlsv1.3
curl -s -u Administrator:password http://127.0.0.1:8091/settings/security | jq '{tlsMinVersion, honorCipherOrder, cipherSuites}'
```

Before raising the minimum to 1.3, inventory client TLS stacks: SDK runtimes, JDBC and ODBC drivers, backup hosts, and XDCR peers. A failed handshake looks like a network outage to the application.

## TLS: Between Nodes

Node-to-node encryption (EE) has three levels, set with `clusterEncryptionLevel`. Both containers report `"clusterEncryptionLevel":"none"` until it is enabled.

| Level | Encrypts | Notes |
|---|---|---|
| `control` | Cluster-management traffic only | Default when first enabled |
| `all` | Management and service data between nodes | 8.0 uses mTLS between nodes when encryption is on (MB-50939) |
| `strict` | Same as `all`, and only encrypted connections from clients are accepted | Loopback traffic on the same node stays plain. The Eventing debugger port (9140) becomes unavailable. |

Procedure (each step is a cluster-wide change; rehearse first):

```sh
# 1. Disable auto-failover for the change window
couchbase-cli setting-autofailover -c n1:8091 -u Administrator -p password --enable-auto-failover 0
# 2. Pause deployed Eventing functions (eventing-function-setup ... --pause --name <fn>)
# 3. Enable encryption (level control)
couchbase-cli node-to-node-encryption -c n1:8091 -u Administrator -p password --enable
# 4. Raise the level
couchbase-cli setting-security -c n1:8091 -u Administrator -p password --set --cluster-encryption-level all
# 5. Resume Eventing; re-enable auto-failover
couchbase-cli setting-autofailover -c n1:8091 -u Administrator -p password \
  --enable-auto-failover 1 --auto-failover-timeout 120
# Verify
couchbase-cli node-to-node-encryption -c n1:8091 -u Administrator -p password --get
curl -s -u Administrator:password http://n1:8091/pools/default | jq .clusterEncryptionLevel
```

Before choosing `strict`: confirm every client, script, and tool connects over TLS (`couchbases://`, `https://`), and that every XDCR replication is configured as fully secure. Clients on plain ports fail immediately after the switch.

## Certificates

- From 7.2, node certificates must carry the node name as a Subject Alternative Name. Couchbase checks this on upload and when a node joins (`validateNodeCertSan` true in the containers). Upgrades fail if it is missing.
- 7.6: PKCS#12 node certificates and elliptic-curve keys. Certificate-expiry alerts warn 30 days ahead by default (`certExpirationDays`).
- 8.0: regenerate pre-7.6 out-of-the-box CA certificates before combining client-certificate authentication with N2N encryption (MB-47905). Before 8.0.4, parallel `loadTrustedCAs` calls during automated rotation could fail with HTTP 500 and leave mixed node certificates (MB-74940). On 8.0.0–8.0.3, rotate one node at a time.
- 8.0.4 fixed a hang on port 18091 caused by TLS health checks that open and close connections without sending a request (MB-74905). On earlier 8.0.x, make load-balancer health checks send a real HTTP request.

## Auditing

- Disabled by default and enabled per node. Each node logs only its own events to `audit.log` in `logPath` (`/opt/couchbase/var/lib/couchbase/logs` in both containers). Collect from every node for a cluster-wide view. The current auditing pages do not say whether auditing requires Enterprise Edition. On the `community-8.0.2` container, `GET` and `POST /settings/audit` return "This http API endpoint requires enterprise edition" (HTTP 400).
- Rotation every `rotateInterval` seconds (900–604800, a multiple of 60) or at `rotateSize` (1 MiB–500 MiB, default 20 MiB). Rotated files are kept forever unless `pruneAge` (seconds, default 0 = never; 7.2.4+) is set. Fresh 7.6.13 and 8.0.4 nodes report `"auditdEnabled":false`, `rotateInterval` 86400, `rotateSize` 20971520, and `pruneAge` 0. From 8.0, `audit.log` is a symlink to the current file.
- Non-filterable events are always recorded once auditing is on. Filterable events can be disabled by ID (list them with `/settings/audit/descriptors`), and ignored for listed users (`disabledUsers` entries such as `app_rw/local`, `ldapuser/external`, `@eventing/local`).
- Data-access events produce far more volume than admin events. Enable only the events and users you need, and size `rotateSize` and `pruneAge` for that volume (inference; the fetched pages give no throughput figures).
- Writing audit settings requires Full Admin or Security Admin. Read-Only Security Admin can read them.

```sh
curl -s -X POST -u Administrator:password http://127.0.0.1:8091/settings/audit \
  -d auditdEnabled=true -d rotateInterval=86400 -d rotateSize=104857600 -d pruneAge=2592000
curl -s -u Administrator:password http://127.0.0.1:8091/settings/audit | jq .
curl -s -u Administrator:password http://127.0.0.1:8091/settings/audit/descriptors | jq '.[] | {id, name, module}'
curl -s -u Administrator:password http://127.0.0.1:8091/settings/audit/nonFilterableDescriptors | jq length
```

Monitor the audit queue: the 7.6.13 and 8.0.4 `/metrics` output includes `audit_queue_length` and `audit_unsuccessful_retries`. A growing queue means audit writes are falling behind.

## Encryption at Rest

- 8.0 (EE): native encryption for bucket data, logs, audit, and configuration, with keys from third-party key management services such as AWS KMS and KMIP-compliant servers. The per-bucket key is `encryptionAtRestKeyId` (`-1` = off). Changing the key re-encrypts the data. The 8.0.4 container reported configuration data `"encrypted"` with no setup, and logs and audit unencrypted. `cbbackupmgr` does not back up encryption-at-rest settings, so re-apply them after restoring into a new cluster.
- 7.x: no native encryption at rest. Use filesystem or volume encryption.
- Backups: encrypted `cbbackupmgr` repositories are GA in 7.6 (developer preview in 7.2).

## Hardening Checklist

1. Do not use `Administrator` for applications. Create per-application users with collection-level roles.
2. Require TLS for clients (`couchbases://`). Use at least `all` for node-to-node encryption when traffic crosses untrusted networks, and fully secure XDCR.
3. Turn on auditing with `pruneAge` set, and ship `audit.log` from every node.
4. After any upgrade to 8.0, review users and groups for the role split.
5. Rotate node certificates before `certExpirationDays` alerts fire; on 8.0 before 8.0.4, one node at a time.
6. Enable password hash migration once every node runs 7.6+, so old SHA1-based hashes are replaced as users log in.

Sources: Roles (https://docs.couchbase.com/server/current/learn/security/roles.html), On-the-Wire Security (https://docs.couchbase.com/server/current/learn/security/on-the-wire-security.html), Manage On-the-Wire Security (https://docs.couchbase.com/server/current/manage/manage-security/manage-tls.html), Manage Node-to-Node Encryption (https://docs.couchbase.com/server/current/manage/manage-nodes/apply-node-to-node-encryption.html), Auditing (https://docs.couchbase.com/server/current/learn/security/auditing.html), Configure Auditing REST (https://docs.couchbase.com/server/current/rest-api/rest-auditing.html), cbbackupmgr backup (role names for metadata), Upgrade (client-cert command), What's New 7.6 and 8.0, Release Notes 7.2, 7.6, and 8.0, Couchbase Server Editions, container outputs for 7.6.13 and 8.0.4, all checked 2026-11-27.
