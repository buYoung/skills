# MySQL Security: Authentication, Privileges, TLS, Auditing

Checked: 2026-11-27. Applies to MySQL 8.0 through 26.10.

## Authentication Plugins

| Plugin | 8.0 | 8.4 | 9.0+ (9.7, 26.x) |
|---|---|---|---|
| `caching_sha2_password` | default | default | default |
| `mysql_native_password` | available, deprecated | present but disabled; enable with `mysql_native_password=ON` | removed from the server |
| `sha256_password` | available, deprecated | available, deprecated | deprecated, expect removal (9.7 manual); still ACTIVE in the 9.7/26.x containers |
| `authentication_ldap_*`, `authentication_kerberos`, `authentication_oci` | Enterprise | Enterprise | Enterprise |
| `authentication_webauthn` | Enterprise | Enterprise | Enterprise; Community from 26.10.0 |

Container evidence: `mysql_native_password` is ACTIVE on 8.0.46, DISABLED on 8.4.13, and absent on 9.7.4 and 26.x; `CREATE USER ... IDENTIFIED WITH mysql_native_password` fails with ERROR 1524 on 8.4.13 (default), 9.7.4 and 26.x. On 8.4.13 started with `--mysql-native-password=ON` the plugin is ACTIVE and such an account can log in; 9.7.4 refuses to start with that option ("unknown variable"). `@@default_authentication_plugin` returns ERROR 1193 on 8.4+; use `@@authentication_policy` (`*,,` by default on all versions).

`caching_sha2_password` on a connection without TLS needs RSA key exchange: clients must use TLS, or request the server's public key (`--get-server-public-key`, or `GET_SOURCE_PUBLIC_KEY=1` for replication). After a server restart the authentication cache is empty, so the first login of each account takes the full exchange; non-TLS clients without the public-key option fail at that point.

Migrate accounts off `mysql_native_password` before 8.4/9.x:

```sql
SELECT user, host, plugin, password_last_changed FROM mysql.user
 WHERE plugin <> 'caching_sha2_password' AND user NOT LIKE 'mysql.%';
ALTER USER 'app'@'%' IDENTIFIED WITH caching_sha2_password BY 'new-secret';
```

A stored native hash cannot be converted; each account needs its password set again. Use dual passwords to rotate without downtime:

```sql
ALTER USER 'app'@'%' IDENTIFIED BY 'new-secret' RETAIN CURRENT PASSWORD;
-- deploy the new secret to all clients, then
ALTER USER 'app'@'%' DISCARD OLD PASSWORD;
```

Password policy:

```sql
INSTALL COMPONENT 'file://component_validate_password';
SET PERSIST validate_password.policy = 'MEDIUM', validate_password.length = 14;
ALTER USER 'app'@'%' FAILED_LOGIN_ATTEMPTS 5 PASSWORD_LOCK_TIME 1;   -- lock for 1 day
CREATE USER 'ops'@'%' IDENTIFIED BY RANDOM PASSWORD;   -- length = generated_random_password_length (20)
```

Brute-force throttling: the Connection Control plugins are deprecated since 9.2.0; use `component_connection_control`.

## Accounts and Privileges

- An account is `'user'@'host'`. MySQL matches the most specific host first, so an anonymous account (`''@'localhost'`) can shadow a named one. Remove anonymous accounts.
- Use roles for permission sets:
  ```sql
  CREATE ROLE 'app_read';
  GRANT SELECT ON app.* TO 'app_read';
  GRANT 'app_read' TO 'reporting'@'10.0.%';
  SET DEFAULT ROLE 'app_read' TO 'reporting'@'10.0.%';
  SHOW GRANTS FOR 'reporting'@'10.0.%' USING 'app_read';
  ```
  Container check: the same sequence works on all five versions. A role is inactive in a session unless it is a default role, activated with `SET ROLE`, or `activate_all_roles_on_login=ON`. From 9.5.0, `activate_mandatory_roles=ON` activates `mandatory_roles` at login.
- `SUPER` is deprecated. Grant the dynamic privilege for the task: `SYSTEM_VARIABLES_ADMIN`, `CONNECTION_ADMIN`, `REPLICATION_SLAVE_ADMIN`, `BINLOG_ADMIN`, `BACKUP_ADMIN`, `CLONE_ADMIN`, `SERVICE_CONNECTION_ADMIN`, `SYSTEM_USER`. 8.4 adds `FLUSH_PRIVILEGES`, `OPTIMIZE_LOCAL_TABLE`, `TRANSACTION_GTID_TAG`, `SET_ANY_DEFINER`, `ALLOW_NONEXISTENT_DEFINER`, and removes `SET_USER_ID`.
- `SYSTEM_USER` protects administrative accounts: only holders of `SYSTEM_USER` can modify them or kill their sessions.
- `partial_revokes=ON` allows `GRANT SELECT ON *.* ...` followed by `REVOKE SELECT ON mysql.* ...`. It changes how grants are stored; set it the same way on all servers of a topology.
- Database-level grants that use `%` or `_` as wildcards are deprecated since 8.2.0. Escape `_` in database names (`app\_db`) or grant per database.
- Definers: views and routines run with the definer's privileges by default (`SQL SECURITY DEFINER`). Dropping the definer account breaks the objects; 8.4 adds `ALLOW_NONEXISTENT_DEFINER` for deliberate orphan definers.
- `FLUSH PRIVILEGES` is unnecessary after `GRANT` or `CREATE USER` and is deprecated since 9.2.0. It is needed only after editing grant tables directly, which you should not do.

Audit privileged accounts:

```sql
SELECT GRANTEE, PRIVILEGE_TYPE FROM information_schema.USER_PRIVILEGES
 WHERE PRIVILEGE_TYPE IN ('SUPER','SYSTEM_USER','CONNECTION_ADMIN','SYSTEM_VARIABLES_ADMIN','FILE','SHUTDOWN','CREATE USER');
SELECT user, host, account_locked, password_expired FROM mysql.user;
```

## TLS

Defaults (all containers): `auto_generate_certs=ON` creates a self-signed CA and server certificate at initialization (the 26.10 log warns "CA certificate ca.pem is self signed"), `tls_version=TLSv1.2,TLSv1.3`, `require_secure_transport=OFF`. `have_ssl` exists only in 8.0 (ERROR 1193 on 8.4+).

Decisions:

1. Replace the auto-generated certificates with ones from your CA so clients can verify the server (`--ssl-mode=VERIFY_IDENTITY`). Self-signed certificates encrypt but do not authenticate the server.
2. Require TLS server-wide with `SET PERSIST require_secure_transport = ON` (Unix socket connections still work), or per account with `REQUIRE SSL`, `REQUIRE X509`, or `REQUIRE SUBJECT '...'`.
3. Rotate certificates without a restart: replace the files, then `ALTER INSTANCE RELOAD TLS;`. In 8.4+, `tls_certificates_enforced_validation=ON` makes startup and reload refuse invalid certificates.
4. Replication: from 9.5.0, `SOURCE_SSL=1` and Group Replication `REQUIRED` TLS are defaults. On older versions set them explicitly.
5. 26.7+ built with OpenSSL 3.5+: post-quantum key exchange is preferred, with classical fallback; `force_pqc=ON` (and the per-channel variants) requires it. Check with `SHOW SESSION STATUS LIKE 'Tls_key_exchange_algorithm'`.

Check a session: `\s` in the mysql client, or `SELECT * FROM performance_schema.status_by_thread WHERE VARIABLE_NAME = 'Ssl_version'`.

## Server Hardening

| Item | Default | Recommendation |
|---|---|---|
| `local_infile` | OFF (containers) | Keep OFF; enable only for a planned load. |
| `secure_file_priv` | `/var/lib/mysql-files/` in the image | Limits `LOAD DATA INFILE` and `SELECT ... INTO OUTFILE` to one directory; `NULL` disables them. An empty value removes the limit; do not use it. |
| `FILE` privilege | | Grant only to tooling that needs server-side file access. |
| `skip_name_resolve` | ON in the image | Avoids DNS dependence; host parts of accounts must then be IP addresses or netmask/CIDR ranges. |
| X Protocol (`mysqlx_port` 33060) | listening in all containers, including 26.10 | If nothing uses it, disable the X Plugin (`mysqlx=OFF` in `[mysqld]`) or firewall the port. Container: 26.10.0 started with `--mysqlx=OFF` shows `mysqlx` DISABLED, has no `mysqlx_port` variable (error 1193), and listens only on 3306. |
| Admin interface (port 33062) | configured, `create_admin_listener_thread=OFF` | Bind `admin_address` to a management network if used. |
| `mysql` client `--system-command` | OFF from 9.1.0 (container: TRUE on 8.0.46 and 8.4.13, FALSE on 9.7.4 and 26.x; `--commands` likewise) | Keeps scripts from running shell commands. |
| Encryption at rest | off | `default_table_encryption=ON` with a keyring component (`component_keyring_file` at minimum; KMS-backed keyrings in Enterprise). Back up the keyring separately. The `keyring_file` plugin is removed in 8.4. |

## Auditing

- Enterprise: MySQL Enterprise Audit (`audit_log`) with JSON filter rules. 26.7.0 adds `Audit_log_file_count` / `audit_log.file_count` status variables.
- Community: Oracle ships no audit plugin. The general query log (`general_log=ON`) records every statement with high overhead and no filtering; passwords in account statements are rewritten unless `log_raw=ON`. Use it only for short investigations. For connection-level evidence use Performance Schema (`performance_schema.accounts`, `host_cache`) and the error log (`log_error_verbosity=3` includes aborted-connection notes).
- Managed services have their own audit options; see [managed-services.md](managed-services.md#diagnostics-that-replace-self-hosted-ones).

## Sources

Checked 2026-11-27: statement runs on the official mysql:8.0 to 26.10 images (plugin status, role commands, errors 1524 and 1193, TLS variables, X Plugin listener in the 26.10 log); MySQL 8.4 What Is New (native password disabled, removed privileges and plugins, `tls_certificates_enforced_validation`); MySQL 8.4 manual, Native Pluggable Authentication (https://dev.mysql.com/doc/refman/8.4/en/native-pluggable-authentication.html); Changes in MySQL 9.0.0, 9.2.0, 9.5.0, 26.7.0 and 26.10.0 (native password removal, deprecations, role and TLS defaults, PQC, WebAuthn in Community). Dual passwords, failed-login tracking, `REQUIRE` clauses, `partial_revokes` and `log_raw` follow the MySQL 8.4 manual Security chapter (https://dev.mysql.com/doc/refman/8.4/en/security.html) and server system variables page.
