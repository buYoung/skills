# MongoDB Security

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)). Atlas user management is in [managed-services](managed-services.md#security-differences).

## Edition matrix

| Feature | Community | Enterprise | Atlas |
| --- | --- | --- | --- |
| SCRAM (default mechanism), X.509 | yes | yes | yes |
| LDAP proxy authentication, Kerberos | — | yes | LDAP (deprecated since 8.0) |
| OIDC (Workforce/Workload identity) | — | yes ("MongoDB Enterprise supports OpenID Connect authentication"; Linux only) | yes, MongoDB 7.0+ |
| Auditing | — | yes | M10+ |
| Encryption at rest in WiredTiger (encrypted storage engine) | — | yes | provider encryption; Infinite requires encryption with a customer key option |
| CSFLE / Queryable Encryption | explicit encryption; Queryable Encryption with automatic encryption is not supported on Community (QE compatibility page). Check the CSFLE compatibility page before planning automatic CSFLE on Community | yes | yes |

LDAP authentication and authorization are deprecated since 8.0. They still work in all 8.x releases and will be removed in a future major.

## Turn on access control

On a fresh deployment:

1. Start `mongod` with `security.authorization: enabled`. For a replica set, also configure internal authentication (below); `security.keyFile` implies authorization.
2. Connect over localhost and create the first user administrator, using the localhost exception. It applies only while the instance has no users or roles, and the first `createUser` or `createRole` ends it. In a sharded cluster it applies to each shard separately, so create a user administrator on each shard's primary or start shards with `enableLocalhostAuthBypass=0` (localhost exception page):

   ```javascript
   use admin
   db.createUser({ user: "useradmin", pwd: passwordPrompt(),
                   roles: [ { role: "userAdminAnyDatabase", db: "admin" } ] })
   ```
3. Create per-application and per-person users with least privilege. Use one user per person or application; the checklist says not to share them.

On a running replica set without auth, plan a rolling change:
1. Deploy the keyfile or X.509 on all members.
2. Restart with `security.transitionToAuth: true`. While it is set, the node does not enforce user access control: anyone who can connect can read, write and administer. Keep the window short.
3. Create users.
4. Restart without the transition setting.

Rehearse it; clients without credentials will be cut off at the last step.

`security.authorization` values are case-sensitive from 9.0.0, 8.3.9, 8.2.13, 8.0.30, and 7.0.41 (`enabled` / `disabled`). Other spellings now stop startup. Check configuration files before patching.

Verify:

```javascript
db.adminCommand({ getCmdLineOpts: 1 }).parsed.security
db.runCommand({ connectionStatus: 1 }).authInfo          // authenticated users and roles
db.getSiblingDB("admin").system.users.find({}, { user: 1, db: 1, mechanisms: 1 })  // needs privileges on admin
```

## SCRAM and mechanisms

- `authenticationMechanisms` on all four images: `MONGODB-X509`, `SCRAM-SHA-1`, `SCRAM-SHA-256`. A user created with default options got both `SCRAM-SHA-1` and `SCRAM-SHA-256` credentials on every image.
- Prefer SCRAM-SHA-256. To create SHA-256-only users, pass `mechanisms: ["SCRAM-SHA-256"]` to `createUser`. On all four images `getUser()` then listed only `[ 'SCRAM-SHA-256' ]`.
- In 8.3+ with `--tlsFIPSMode`, listing `SCRAM-SHA-1` in `authenticationMechanisms` stops startup.
- Restrict where a user can log in from with `authenticationRestrictions` in `createUser` (`clientSource`, `serverAddress`).

## Roles

Useful built-in roles:

| Role | Use |
| --- | --- |
| `read`, `readWrite` (per database) | application users |
| `dbAdmin`, `dbOwner` | per-database administration |
| `userAdmin`, `userAdminAnyDatabase` | user management only |
| `clusterMonitor` | monitoring agents; includes `$queryStats` privileges `queryStatsRead` and `queryStatsReadTransformed` |
| `hostManager` | `fsync` lock for backups, among other host actions |
| `clusterManager` | sharding and replication management, `analyzeShardKey` |
| `backup`, `restore` | `backup` covers `mongodump` of an entire `mongod`. `restore` covers `mongorestore` without `--oplogReplay` when the dump has no `system.profile` data; `--oplogReplay` needs a user-defined role with `anyAction` on `anyResource` (built-in roles page) |
| `root` | break-glass only |
| `directShardOperations` (8.0+) | maintenance commands directly on shard members; the release notes warn it can corrupt data if misused |

Create custom roles for narrower needs with `db.createRole({ role, privileges: [{ resource: { db, collection }, actions: [...] }], roles: [] })`. On 9.0, `usersInfo` accepts `authenticatedMechanism` to choose which authorization backend to query.

## Internal authentication

Members of replica sets and sharded clusters must authenticate to each other.

| `security.clusterAuthMode` | Meaning |
| --- | --- |
| `keyFile` (default) | shared secret file (`security.keyFile`, YAML: one key or a list of keys for rotation) |
| `sendKeyFile` / `sendX509` | transition states for a rolling move from keyfile to X.509 |
| `x509` | recommended; members present certificates |

Keyfile rotation without downtime:
1. Put both old and new keys in the file on every member and restart each in turn.
2. Then remove the old key and restart each in turn again.

This follows from the YAML key-list format. Rehearse it.

9.0.7 and 8.3.16 fixed an X.509 cluster-membership check that could fail open on user lookup errors (SERVER-130169). Run at least those patches, or the matching patch of your series.

## TLS

```yaml
net:
  tls:
    mode: requireTLS                      # disabled | allowTLS | preferTLS | requireTLS
    certificateKeyFile: /etc/mongod/tls/server.pem
    CAFile: /etc/mongod/tls/ca.pem
    disabledProtocols: TLS1_0,TLS1_1      # no spaces; overrides the default
```

- By default MongoDB disables TLS 1.0 when TLS 1.1+ is available. Setting `disabledProtocols` replaces the default list. A space or an unknown value in the list stops startup.
- Roll TLS onto a running set by stepping `mode` from `allowTLS` to `preferTLS` to `requireTLS`, with a rolling restart at each step, after every client is configured for TLS.
- With TLS on `openssl-3.2.2-6.el9_5.x86_64`, 7.0 before 7.0.17 and 8.0 before 8.0.5 can show high CPU; upgrade the server.
- Windows gained TLS 1.3 in 8.0.34 and 8.3.7.
- Verify by connecting with `mongosh --tls` and the correct CA, which must succeed, and with a wrong CA, which must fail. Check `getCmdLineOpts` for the effective `net.tls`. The images run with `tlsMode: 'disabled'`.

## Network exposure

- `net.bindIp` defaults to `localhost` in packaged installs. The Docker images bind `*`; do not expose them without auth and TLS.
- Use firewalls or security groups, and `security.clusterIpSourceAllowlist` to limit which addresses may act as cluster members.
- Arbiters can be logged into only through the localhost exception when auth is on. Keep them on trusted networks with TLS.
- 8.3 added pre-auth limits (`preAuthMaximumMessageSizeBytes`, `capMemoryConsumptionForPreAuthBuffers`) that bound unauthenticated clients.

## Auditing (Enterprise, Atlas M10+)

```yaml
auditLog:
  destination: file          # syslog | console | file
  format: JSON               # JSON | BSON (file only; JSON costs more)
  path: /var/log/mongodb/audit.json
  schema: mongo              # mongo (default) | OCSF (8.0+)
  filter: '{ atype: { $in: [ "authenticate", "createUser", "dropUser", "grantRolesToUser" ] } }'
setParameter:
  auditAuthorizationSuccess: false   # true is required to audit CRUD operations
```

- If the server cannot write to the audit destination, it terminates. Monitor disk space on the audit volume.
- Events are buffered. Events not yet flushed can be lost if the server dies, even after the client got an acknowledgment.
- Secondaries do not log DDL events for replicated changes (5.0+). Collect audit logs from every member.
- An aborted transaction's operations are audited, but the abort itself is not.
- 8.0+ has an `auditConfig` cluster parameter for audit configuration. Change it at runtime with `db.adminCommand({ setClusterParameter: { auditConfig: { filter: {...}, auditAuthorizationSuccess: false } } })` and read it with `getClusterParameter: "auditConfig"`; the change takes effect at once on all config servers and shards. A wide filter or `auditAuthorizationSuccess: true` degrades performance (auditConfig page).
- 9.0 records the real TCP peer (`directRemote` / `direct_endpoint`) when clients connect through a PROXY protocol load balancer.

## Encryption

- At rest: use the Enterprise encrypted storage engine, or encrypt at the filesystem or device level (for example dm-crypt). Protect data, keyfiles, config, and audit logs with filesystem permissions.
- Client-side field-level encryption and Queryable Encryption encrypt fields before they reach the server.
  - `mongodump` and `mongoexport` cannot decrypt these collections.
  - Resharding does not support Queryable Encryption collections.
  - 9.0 deprecates `mongocryptd` in favor of the Automatic Encryption Shared Library, and makes prefix/suffix/substring queries GA. This is incompatible with the 8.2/8.3 preview.
  - Compact Queryable Encryption metadata collections as part of routine operations.

## Hardening checklist

- Run `mongod` as a dedicated OS user without extra privileges, with SELinux or AppArmor enforcing (configure the policy for non-default paths and ports).
- Disable server-side JavaScript (`--noscripting`, or `security.javascriptEnabled: false`) if nothing uses `$where`, `$function`, `$accumulator`, or `mapReduce`. The default is enabled.
- Exclude `storage.dbPath` and the log path from antivirus and EDR scanning.
- Track CVEs in the release notes: 9.0.7 and 8.3.16 (2026-11-10) fixed more than twenty CVEs. Patch to the latest release of the series.
