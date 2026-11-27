# MariaDB Security

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)). Applies to MariaDB 10.6-13.1. MariaDB's authentication model differs from MySQL 8: the default plugin for password accounts is still `mysql_native_password`, `unix_socket` is installed by default, and the modern options are `ed25519` and PARSEC (11.6+).

## Authentication Plugins

| Plugin | Loaded by default | Strength | Use for | Notes |
| --- | --- | --- | --- | --- |
| `mysql_native_password` | Yes | SHA-1 based challenge-response | Legacy clients | Default for `CREATE USER ... IDENTIFIED BY` in all covered images (the account shows `plugin=mysql_native_password`) |
| `unix_socket` | Yes | As strong as OS user security | Local admin and maintenance scripts | Used by `root@localhost` on package installs (the official images configure root with a password instead) |
| `ed25519` | No (`INSTALL SONAME 'auth_ed25519'`) | Elliptic-curve signatures | Password accounts where the connectors support it | Images: `ERROR 1524 (HY000): Plugin 'ed25519' is not loaded` until installed |
| `parsec` | No (`INSTALL SONAME 'auth_parsec'`), 11.6+ | Salted PBKDF2 + ed25519 signature, client and server scrambles | New password accounts on 11.8+ where clients support it | Intended to become the default in a future release; `parsec_iterations` (13.1) sets PBKDF2 rounds for passwords set afterwards |
| `caching_sha2_password` | No (`INSTALL SONAME 'auth_mysql_sha2'`), 12.3+ | SHA-256 based | Clients built for MySQL 8 | Added for MySQL compatibility. 12.3.3 and 13.0.2 images: `ERROR 1524 (HY000): Plugin 'caching_sha2_password' is not loaded` until installed; after `INSTALL SONAME 'auth_mysql_sha2'` the account is created and a TCP login with the `mariadb` client works. The error log then reports `caching_sha2_password: failed to read private_key.pem` although `caching_sha2_password_auto_generate_rsa_keys=ON` |
| `gssapi`, `pam` | No | External | Kerberos/AD, PAM | |

Examples:

```sql
INSTALL SONAME 'auth_ed25519';                     -- once; remembered across restarts and upgrades
CREATE USER 'app'@'10.0.%' IDENTIFIED VIA ed25519 USING PASSWORD('...');

INSTALL SONAME 'auth_parsec';                      -- 11.6+
CREATE USER 'svc'@'%' IDENTIFIED VIA parsec USING PASSWORD('...');

-- Local OS admin without password; fallback to a password if needed
CREATE USER 'ops'@'localhost' IDENTIFIED VIA unix_socket;
ALTER USER 'root'@'localhost' IDENTIFIED VIA unix_socket OR mysql_native_password USING PASSWORD('...');

SELECT user, host, plugin FROM mysql.user ORDER BY user, host;     -- audit plugins in use
```

Decision rules:

- Prefer PARSEC (11.8+) or `ed25519` for new password accounts after confirming every client connector supports them (`ed25519`: Connector/C, ODBC, J, Node.js; MySqlConnector for .NET needs an extra package). Keep `mysql_native_password` only for clients that cannot change, and require TLS for them.
- `unix_socket` is only as strong as the Unix accounts: broad `sudo`, writable scripts, or command injection on the host become database access. From 11.6 it can map an OS user to a different DB user (`IDENTIFIED VIA unix_socket AS 'bob'`).
- Switching `root@localhost` from `unix_socket` to a password breaks scripts that rely on passwordless access (for example `sudo mariadb-upgrade`).
- Accounts migrated from MySQL 8 with `caching_sha2_password` cannot log in to MariaDB before 12.3; recreate them with a supported plugin during migration.

## Accounts, Roles and Privileges

```sql
CREATE ROLE app_read;
GRANT SELECT ON app.* TO app_read;
GRANT app_read TO 'report'@'%';
SET DEFAULT ROLE app_read FOR 'report'@'%';     -- roles are not active at login otherwise
SHOW GRANTS FOR 'report'@'%';
```

The images confirm this sequence; `SHOW GRANTS` lists `GRANT app_read TO ...`, the `USAGE` line with the password hash, and `SET DEFAULT ROLE`.

MariaDB-specific privilege points:

- `SUPER` was split over several releases into narrower privileges (`READ_ONLY ADMIN` separated in 10.11, plus `BINLOG MONITOR`, `REPLICA MONITOR`, `CONNECTION ADMIN` and others). Grant the narrow one: a backup user needs `RELOAD, PROCESS, LOCK TABLES, BINLOG MONITOR`.
- `read_only=ON` does not stop users with `READ_ONLY ADMIN` (10.11+); keep that privilege away from application accounts on replicas.
- `GRANT ... TO PUBLIC` (10.11+) applies to all accounts, present and future; review `SHOW GRANTS FOR PUBLIC`.
- `SHOW CREATE ROUTINE` privilege (11.3+, so 11.4+) lets non-owners read routine bodies.
- `DELETE HISTORY` privilege controls purging of system-versioned history.
- `SET SESSION AUTHORIZATION` (12.3+) runs statements as another user; grant the ability narrowly.
- `DENY` (13.1) adds negative grants that override any grant at the same or lower level; only `REVOKE DENY` removes one; `SHOW GRANTS` shows denies only to users with `SELECT` on `mysql`.
- `DROP USER` warns when the user has active sessions (12.3+). Existing sessions of a dropped user keep running until they disconnect; kill them explicitly (find them in `information_schema.PROCESSLIST` by `USER`).
- `default_password_lifetime=0` (no expiry by default); `max_password_errors` locks an account after repeated failed logins when set; `information_schema.USERS` (11.5+, so 11.8+) shows expiry and error counts.
- Password validation plugins: `simple_password_check`, `cracklib_password_check`, `password_reuse_check` (10.7+); `strict_password_validation=ON` (default in the images) rejects pre-hashed passwords that would bypass validation.

Account hygiene check:

```sql
SELECT user, host, plugin, password_expired FROM mysql.user
WHERE host = '%' OR plugin = 'mysql_native_password' OR authentication_string = '';
```

(`mysql.user` is a view over `mysql.global_priv` in MariaDB; check column names on your version.)

## TLS

| Version | Server default | Client default |
| --- | --- | --- |
| 10.6 | TLS disabled unless certificates are configured (`have_ssl=DISABLED` in the image) | `mariadb` client without `--ssl` by default |
| 10.11 | Same as 10.6 (`have_ssl=DISABLED` in the image) | `--ssl` on by default (10.10+) |
| 11.4+ | TLS on: a self-signed certificate is generated when none is configured (`have_ssl=YES`) | Clients require TLS and verify the server certificate; replication too (`MASTER_SSL_VERIFY_SERVER_CERT`) |

`tls_version` is `TLSv1.2,TLSv1.3` in all images.

Enforce and verify:

```ini
[mariadb]
ssl_cert = /etc/mysql/tls/server-cert.pem
ssl_key  = /etc/mysql/tls/server-key.pem
ssl_ca   = /etc/mysql/tls/ca.pem
require_secure_transport = ON
tls_version = TLSv1.2,TLSv1.3
```

```sql
ALTER USER 'app'@'%' REQUIRE SSL;                   -- per account
SHOW SESSION STATUS LIKE 'Ssl_version';             -- run in the client session to confirm TLS
SHOW SESSION STATUS LIKE 'Ssl_cipher';
```

- The auto-generated certificate (11.4+) encrypts traffic, but clients can verify it only for password accounts using `mysql_native_password`, `ed25519`, or `parsec` (11.6+), the plugins that are MitM-proof without TLS (Zero-Configuration SSL page). For `unix_socket`, passwordless accounts, PAM, GSSAPI, and `caching_sha2_password` (12.3+), distribute a CA-signed certificate or use `--ssl-fp`/`--ssl-fplist`.
- Passphrase-protected keys: `ssl_passphrase` (12.3+).
- Reload certificates with `FLUSH SSL` (accepted in all 10.6-13.0 images); otherwise restart.
- RDS: from RDS 11.8.3, `require_secure_transport` defaults to `1`.

## Auditing

The MariaDB Audit Plugin (`server_audit`) ships with Community Server:

```sql
INSTALL SONAME 'server_audit';
SET GLOBAL server_audit_events = 'CONNECT,QUERY_DDL,QUERY_DCL';
SET GLOBAL server_audit_file_path = '/var/log/mysql/audit.log';
SET GLOBAL server_audit_logging = ON;
```

- Log connects and DDL/DCL at minimum; full `QUERY` logging is heavy on busy servers.
- 12.3: buffered writes (`server_audit_file_buffer_size`), HOST:PORT and TLS version in connection records; Galera applier actions are logged as `<wsrep_applier>`. 13.0: configurable timestamp format.
- Ship the audit file off the host if it must be tamper-evident; the database OS user can modify local files.
- On RDS, auditing is configured through a custom option group with the `MARIADB_AUDIT_PLUGIN` option (RDS MariaDB options page; MariaDB 10.3 and higher).

## Encryption at Rest

- InnoDB and Aria table encryption, temporary-file and binlog encryption (`innodb_encrypt_tables`, `innodb_encrypt_log`, `aria_encrypt_tables`, `encrypt_tmp_files`, `encrypt_binlog`; all `OFF` in the images) require a key management plugin: `file_key_management` (SHA2 key support 12.3+), `hashicorp_key_management` (10.9+, cache flush for forced rotation 12.3), or the AWS KMS plugin.
- Key rotation: `innodb_encryption_rotate_key_age` and `innodb_encryption_threads` (0 in the images; background encryption and rotation do not run until you set it).
- Binlog encryption is not supported with the InnoDB-based binlog (12.3+); Galera gcache is not encrypted.
- RDS does not support native MariaDB encryption at rest; use RDS storage encryption instead.

## Network Exposure

- `bind_address` accepts a comma-separated list (10.11+). Bind to private interfaces only.
- `skip_networking` for socket-only servers.
- `local_infile=ON` in the images; turn it off unless needed (`LOAD DATA LOCAL` lets the server request files from the client).
- `secure_file_priv` is empty in the images (no restriction on `SELECT ... INTO OUTFILE` and `LOAD DATA INFILE` paths). Set it to a dedicated directory.
- `proxy_protocol_networks` lets a proxy pass the real client address; restrict it to the proxy subnet.
