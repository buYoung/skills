# Security: Authentication, Privileges, TLS, Auditing

Checked: 2026-11-27 (sources in [versions/index.md](versions/index.md#sources)).

## Client authentication (`pg_hba.conf`)

Rules are checked top to bottom; the first line whose type, database, user, and address match decides. A later, stricter line never applies if an earlier line matched.

```
# TYPE   DATABASE     USER        ADDRESS          METHOD
local    all          postgres                     peer
hostssl  app          app_rw      10.0.0.0/16      scram-sha-256
hostssl  replication  replicator  10.0.1.0/24      scram-sha-256
host     all          all         0.0.0.0/0        reject
```

- `hostssl` requires TLS; `host` accepts TLS or plain; `hostnossl` only plain.
- Inspect the effective rules (with errors) without reading the file: `SELECT line_number, type, database, user_name, address, auth_method, error FROM pg_hba_file_rules;` Reload after editing: `SELECT pg_reload_conf();`. A file with errors keeps the old rules loaded and logs the error.
- 16+: regular expressions (prefix `/`), `include`, `include_dir`, `include_if_exists`.
- The official container image ships `trust` for local and loopback connections and appends `host all all all scram-sha-256` (container, images 14 to 19). Never copy that into production.

Methods:

| Method | Use | Notes |
| --- | --- | --- |
| `scram-sha-256` | default for passwords | `password_encryption = scram-sha-256` default since 14 |
| `md5` | legacy only | MD5-hashed passwords deprecated in 18 (warning on `CREATE/ALTER ROLE`), 19 also warns after each MD5 login; an `md5` hba line still accepts SCRAM-stored passwords |
| `peer` | local Unix-socket admin access | OS user must match DB user (or an ident map) |
| `cert` | client certificates | `clientname=DN` (14+) matches the full DN |
| `gss`, `sspi`, `ldap` | enterprise directories | |
| `oauth` | 18+ | needs `oauth_validator_libraries` |
| `radius` | removed in 19 | migrate before upgrading |
| `trust` | never on networks | |

Move from MD5 to SCRAM:

```sql
SELECT rolname FROM pg_authid WHERE rolpassword LIKE 'md5%';   -- superuser required
SET password_encryption = 'scram-sha-256';
ALTER ROLE app_rw PASSWORD '...';     -- or \password app_rw in psql (avoids logging the cleartext)
```

Then change `md5` lines to `scram-sha-256` and reload. Clients must support SCRAM (libpq 10+). Container: on 18 and 19, setting an MD5 password prints `WARNING:  setting an MD5-encrypted password`; on 17 no warning.

Do not put cleartext passwords in SQL that is logged (`log_statement = 'ddl'` or `'all'` logs `ALTER ROLE ... PASSWORD`). Use psql `\password` or pre-hashed values.

## Roles and privileges

- Roles are cluster-wide; privileges are per object. `LOGIN` makes a role a user.
- Grant through group roles: create `app_read`, `app_write`; grant those to login roles. 16+: each membership grant has `INHERIT`, `SET`, `ADMIN` options (`GRANT app_read TO alice WITH INHERIT TRUE, SET FALSE;`); inspect `pg_auth_members` (`inherit_option` and `set_option` present on the 16.16 container and later, absent on 14 and 15).
- Owners have all privileges and can `DROP`; let a dedicated non-login role own application objects, and let migrations `SET ROLE` to it.
- Default privileges for future objects: `ALTER DEFAULT PRIVILEGES FOR ROLE app_owner IN SCHEMA app GRANT SELECT ON TABLES TO app_read;` They apply only to objects created later by that role.
- `public` schema: since 15, new databases do not grant `CREATE` to `PUBLIC` and the schema is owned by `pg_database_owner`. Upgraded or restored databases keep old permissions; run `REVOKE CREATE ON SCHEMA public FROM PUBLIC;`.
- `CREATEROLE` lets a role create and manage other roles; since 16 it only manages roles it has `ADMIN OPTION` on.
- Superuser bypasses all checks, including RLS. Limit it to break-glass accounts.

Predefined roles worth using:

| Role | Since | Grants |
| --- | --- | --- |
| `pg_read_all_data`, `pg_write_all_data` | 14 | read/write all tables, views, sequences (19: large objects too); good for dump and ETL accounts |
| `pg_monitor` (`pg_read_all_stats`, `pg_read_all_settings`, `pg_stat_scan_tables`) | before 14 | monitoring without superuser |
| `pg_signal_backend` | before 14 | cancel/terminate non-superuser sessions |
| `pg_checkpoint` | 15 | run `CHECKPOINT` |
| `pg_use_reserved_connections` | 16 | use `reserved_connections` slots |
| `pg_create_subscription` | 16 | create subscriptions |
| `pg_maintain` | 17 | `VACUUM`, `ANALYZE`, `REINDEX`, `REFRESH MATERIALIZED VIEW`, `CLUSTER`, `LOCK TABLE` on all relations; `MAINTAIN` privilege per table |
| `pg_signal_autovacuum_worker` | 18 | signal autovacuum workers |

Audit who can do what:

```sql
SELECT r.rolname, r.rolsuper, r.rolcreaterole, r.rolcreatedb, r.rolreplication, r.rolbypassrls,
       array(SELECT b.rolname FROM pg_auth_members m JOIN pg_roles b ON b.oid = m.roleid WHERE m.member = r.oid) AS member_of
FROM pg_roles r WHERE r.rolname !~ '^pg_' ORDER BY 1;

SELECT grantee, table_schema, table_name, privilege_type
FROM information_schema.role_table_grants WHERE grantee NOT IN ('postgres') ORDER BY 1,2,3;
```

18+: `pg_get_acl()` returns the ACL of any object by catalog and OID.

## Function and search_path safety

- `SECURITY DEFINER` functions run as their owner. Always attach `SET search_path = pg_catalog, app` (or schema-qualify everything) so a caller cannot shadow objects, and revoke `EXECUTE` from `PUBLIC` before granting it narrowly.
- 17+: maintenance commands run with a safe `search_path`; functions used in indexes and materialized views must set their own.
- Do not put writable schemas before `pg_catalog`-dependent lookups in a role's `search_path`.

## Row-level security

```sql
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON invoices
  USING (tenant_id = current_setting('app.tenant_id')::int);
```

- Table owners bypass RLS unless `ALTER TABLE ... FORCE ROW LEVEL SECURITY`; superusers and `BYPASSRLS` roles always bypass.
- A policy predicate that cannot use an index slows every query; index `tenant_id`.
- `pg_dump` runs with `row_security = off` and fails if RLS would hide rows, unless the dumping role bypasses RLS; 18+ `--no-policies` omits policies from the dump.

## TLS

Server settings: `ssl = on`, `ssl_cert_file`, `ssl_key_file` (key readable only by the server user), `ssl_ca_file` for client-certificate verification, `ssl_min_protocol_version` (default `TLSv1.2`, container 18 and 19). 18 adds `ssl_tls13_ciphers` and `ssl_groups` (default `X25519:prime256v1`); 19 adds server-side SNI with `pg_hosts.conf` (`ssl_sni`).

Clients must verify the server: libpq `sslmode=verify-full` with `sslrootcert`. `sslmode=require` encrypts but does not authenticate the server. 17+ `sslnegotiation=direct` skips the plaintext negotiation round trip.

Check who is on TLS:

```sql
SELECT a.pid, a.usename, a.client_addr, s.ssl, s.version, s.cipher
FROM pg_stat_ssl s JOIN pg_stat_activity a USING (pid) WHERE a.backend_type = 'client backend';
```

Certificate rotation: replace files, then `SELECT pg_reload_conf();` (existing sessions keep their old session; new connections use the new certificate).

## Auditing and logging

Core logging, not a full audit trail:

| Setting | Records |
| --- | --- |
| `log_connections`, `log_disconnections` | logins, auth method, duration; 18+ `log_connections` takes a list of connection stages instead of a boolean (stage names `receipt`, `authentication`, `authorization`, `setup_durations`, or `all`; boolean values still accepted; container 18.7 and 19.0). It cannot be changed with `SET` in a session; set it in the configuration and reload |
| `log_statement = 'ddl'` | all DDL (also `'mod'` for DML, `'all'`) |
| `log_line_prefix` | include `%m [%p] %q%u@%d %r` for time, pid, user, database, client; 18+ `%L` local address |
| `log_destination = jsonlog` (15+) | structured logs for shipping |

For object-level audit (who read which table), use an audit extension such as pgaudit (third-party, outside core; supported on all available RDS for PostgreSQL and Aurora PostgreSQL versions per the AWS pgAudit pages) or capture at the application. `log_statement = 'all'` on a busy server produces very large logs and still misses statements inside functions.

## Hardening checklist

- No `trust` lines except possibly local `peer`; `reject` at the end of `pg_hba.conf`.
- `listen_addresses` limited to required interfaces.
- `password_encryption = scram-sha-256`; no remaining MD5 hashes.
- TLS on, clients use `verify-full`.
- No application role is superuser, owner of its tables, or `BYPASSRLS`.
- `REVOKE CREATE ON SCHEMA public FROM PUBLIC;` in every pre-15-origin database.
- Extensions: install only needed ones; untrusted languages (`plpython3u`) only for superusers.
- Keep the minor version current; minor releases contain the security fixes.
