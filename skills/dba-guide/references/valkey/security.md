# Valkey Security

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)).

ACL users, selectors, key and channel patterns, `requirepass`, protected mode, `rename-command`, protected configs and TLS setup work as in Redis OSS 7.2. Read [../redis/security.md](../redis/security.md) for the mechanism.

## Patch floor

Security fixes have shipped on the supported lines on the same day (for example 2026-11-18). On 2026-11-27 the minimum patch per line is the 2026-11-18 release (CVE-2026-130822, use-after-free in client eviction with `maxmemory-clients`):

| Line | Minimum |
| --- | --- |
| 7.2 | 7.2.16 |
| 8.0 | 8.0.13 |
| 8.1 | 8.1.12 |
| 9.0 | 9.0.8 |
| 9.1 | 9.1.4 |
| 9.2 | 9.2.1 (9.2.0 has a TLS loading regression) |

Earlier 2026 security releases fixed, among others, a heap overflow in cluster Pub/Sub messages (GHSA-f4q9-j22m-xqq9, October), use-after-free in TLS connection handling via `CLIENT KILL` (CVE-2026-56684, July), and an unauthenticated use-after-free in the Lua debugger state on 9.1 (GHSA-fq2f-crmw-q97r, fixed in 9.1.2). Answer "is this version safe" by comparing `valkey_version` against the newest patch of its line on https://valkey.io/download/releases/ and reading the SECURITY entries in `00-RELEASENOTES` for the line.

## Defaults to check

| Item | Shipped `valkey.conf` | Official container (no config file) |
| --- | --- | --- |
| `bind` | `127.0.0.1 -::1` | `* -::*` |
| `protected-mode` | `yes` | `no` |
| default user | `on nopass ~* &* +@all` | same |
| `enable-debug-command`, `enable-module-command`, `enable-protected-configs` | `no` | `no` |
| `hide-user-data-from-log` | `yes` (8.0+) | `yes` |
| `tls-port` | 0 | 0 |

An image started without a config file accepts unauthenticated connections from any address that can reach the port. Always provide a config with ACL users or `requirepass`, or run the container on an isolated network.

## Database-level ACLs (9.1+)

With numbered databases (standalone, or cluster with `cluster-databases > 1`), restrict which databases a user may use:

```
ACL SETUSER tenant1 on >s3cret ~* +@all -@dangerous db=1
ACL SETUSER reporting on >r3port ~* +@read db=1,2
ACL GETUSER tenant1
```

- Rules: `db=<list>`, `alldbs`, `resetdbs` (documented in the 9.2 `valkey.conf`).
- `MOVE` and `COPY` check every database they touch (9.1.1, 9.1.2); `CLUSTER FLUSHSLOT` requires access to all databases.
- `ACL LOG` reports the denied database for `COPY`; `INFO stats` has `acl_access_denied_db`.
- 9.0 nodes do not understand `db=`; finish upgrading before writing these rules. 9.1.1 omits the implicit `alldbs` from `ACL LIST`/`ACL SAVE` so files stay readable by older versions.

## ACL roles and digests (9.2)

```
ACL SETROLE readonly-app ~app:* +@read
ACL SETUSER svc1 on >pw role=readonly-app
ACL ROLES
ACL DIGEST
```

Roles are named, reusable selector sets usable in commands, the ACL file and `valkey.conf`. `ACL DIGEST` returns a fingerprint of the active rules including roles; compare it across nodes after `ACL LOAD` to prove all nodes enforce the same rules. `ACL SETROLE <rolename> <rule> [<rule> ...]` takes the same rules as `ACL SETUSER`; a user gets a role with the `role=<name>` rule. The 9.2.0 GA notes write `role:<name>`, but that is a syntax error in the 9.2.1 image; use `role=` and check with `ACL LIST`. `ACL GETROLE <name>` shows the role's rules and users; `ACL LIST` prints roles as `role <name> ...` lines before the users.

## TLS additions

| Feature | Series | Config |
| --- | --- | --- |
| Authenticate client by certificate CN | 9.0 | `tls-auth-clients-user CN` |
| Authenticate by SAN URI | 9.1 | `tls-auth-clients-user URI` |
| Automatic certificate reload | 9.1 | `tls-auto-reload-interval <seconds>` (0 = off) |
| Certificate expiry in `INFO` | 9.1 | `tls_server_cert_expires_in_seconds`, `tls_ca_cert_expires_in_seconds`, ... |
| Second server certificate (e.g. PQC + RSA) | 9.2 | `tls-alt-cert-file`, `tls-alt-key-file`, `tls-alt-key-file-pass` |
| Cluster bus TLS accepts on I/O threads | 9.2 | automatic with `io-threads > 1` |

With certificate-based user mapping, create the mapped users without passwords so the certificate is the only way in, and keep `tls-auth-clients yes`. A client whose certificate maps to no user stays the default user; disable or restrict `default` (`ACL SETUSER default off`) or such clients get its permissions. 9.0.6/9.1.2 fixed CN comparison so an embedded NUL cannot impersonate another user; run at least those patches when using this feature.

Monitor certificate expiry from `INFO tls` (9.1+) instead of external file checks, and set `tls-auto-reload-interval 86400` so renewed files are picked up without restart.

## Logging and data exposure

- `hide-user-data-from-log yes` (8.0+ default) removes keys, values, client names and ACL usernames from crash and error logs; 8.0.12/8.1.11/9.0.7/9.1.3 extended redaction to error reply text.
- Rejected `AUTH`, `HELLO` and `MIGRATE` credentials are redacted from `MONITOR` and the commandlog since the 2026-11-18 patches.
- `valkey-cli` reads `VALKEYCLI_AUTH` (and `REDISCLI_AUTH`); 9.2 adds `VALKEYCLI_USER`. Use them instead of `-a` on the command line.

## Hardening checklist

1. `ACL SETUSER default off` (or a strong password) and named users per application with key patterns.
2. `rename-command` is still available, but prefer ACL `-@dangerous` and keep `enable-debug-command no`, `enable-module-command no`.
3. Bind to private interfaces; keep `protected-mode yes` as a safety net.
4. TLS for clients, `tls-replication yes`, `tls-cluster yes` on untrusted networks.
5. For atomic slot migration, give `primaryuser` exactly the permissions in [replication-and-cluster.md](replication-and-cluster.md).
6. Verify: `ACL LIST`, `ACL DIGEST` (9.2) per node, `CONFIG GET protected-mode bind tls-port`, `INFO stats` `acl_access_denied_*`, `ACL LOG 20`.
