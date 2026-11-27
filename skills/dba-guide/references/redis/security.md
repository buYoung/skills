# Redis Security

Checked: 2026-11-27 (sources at the end). Applies to Redis Open Source 6.2 to 8.12.

## Baseline

Redis is designed for trusted networks. With no password and all interfaces bound, any client that reaches the port can read, delete, or reconfigure everything.

1. Bind to private interfaces (`bind 10.0.0.5 127.0.0.1 -::1`) and firewall the client port and, for Cluster, the bus port.
2. Keep `protected-mode yes` (shipped `redis.conf` default). In protected mode, a server with default bind and no password answers only loopback clients. Since 7.0, setting `bind` explicitly no longer turns protected mode off. The official Docker image ran with `protected-mode no` and the default user `nopass` (observed). The entrypoint does not set it; the docker-library build patches the compiled-in default to `no` (`Dockerfile.template`), so `redis-server` defaults to `no` even when started with a config file that omits the setting (8.12.0). Set `protected-mode yes` explicitly in the config; never expose such a container port.
3. Disable or restrict the `default` user and create named users with least privilege.
4. Turn on TLS for anything crossing an untrusted network.
5. Keep `enable-debug-command no`, `enable-module-command no`, `enable-protected-configs no` (defaults since 7.0).

Check the current state:

```
CONFIG GET protected-mode
CONFIG GET bind
ACL LIST
ACL WHOAMI
CONFIG GET tls-port
```

Fresh official image (7.2.17 to 8.12.0): `ACL LIST` returns `user default on nopass sanitize-payload ~* &* +@all`, meaning every connection is authenticated as a user with all permissions on all keys and channels.

## ACLs

Rules apply left to right. A new user starts `off`, with no passwords, no keys, no channels, `-@all`. Each `ACL SETUSER` call modifies the user incrementally; it does not reset it unless you include `reset`.

| Rule | Meaning |
|---|---|
| `on` / `off` | Allow or block new authentications (existing connections stay) |
| `>pw` / `<pw` / `#<sha256>` / `nopass` / `resetpass` | Passwords |
| `~pattern`, `%R~pattern`, `%W~pattern` (7.0+) | Key access: read-write, read-only, write-only |
| `&pattern`, `allchannels`, `resetchannels` | Pub/Sub channels (6.2+) |
| `+cmd`, `-cmd`, `+cmd|sub`, `-cmd|sub` (7.0+) | Commands and subcommands |
| `+@category`, `-@category` | Categories (`ACL CAT` lists them) |
| `( ... )` (7.0+) | Selector: an alternative rule set; command allowed if root rules or any selector match |
| `reset` | Back to the new-user state |

Examples:

```
# application user: data commands on its prefix, no admin or dangerous commands
ACL SETUSER app on >S3cret-app ~app:* &app:* +@all -@admin -@dangerous

# read-only reporting user
ACL SETUSER report on >S3cret-ro %R~* +@read -@dangerous

# lock down the default user after creating an admin
ACL SETUSER admin on >S3cret-admin ~* &* +@all
ACL SETUSER default off
```

Replication user: replicas authenticate with `masteruser` and `masterauth`. A minimal rule on the primary is `ACL SETUSER repl on >S3cret-repl +psync +replconf +ping`. With `default` turned off, a replica using it reached `master_link_status:up` and received writes on 7.2.17 and 8.12.0, with an empty `ACL LOG`; the same held without `+ping`. Test it on a rehearsal pair before relying on it.

Decisions and pitfalls:

- `+@all -@write` is not "read-only plus future reads": since [8.0](versions/8.0.md), bundled JSON, search, time series, and probabilistic commands belong to the standard categories, so such rules changed meaning on upgrade. Re-test ACLs after every upgrade.
- `+@all` includes commands that modules load later; category rules other than `+@all` exclude module commands. Prefer explicit allow lists for untrusted tenants.
- `@dangerous` covers `FLUSHALL`, `KEYS`, `CONFIG`, `DEBUG`, `SAVE`, `REPLICAOF`, `MIGRATE`, `RESTORE`, `SORT`, `CLIENT`, `INFO`, and more. Monitoring users need `INFO` and `SLOWLOG`; grant them explicitly (`+info +slowlog|get +latency|latest`).
- Since 7.0, new users get no channel access (`acl-pubsub-default resetchannels`). On 6.2 they get all channels.
- Sentinel-monitored nodes: Sentinel's `auth-user` needs only `&__sentinel__:hello`; no other user should be able to publish or subscribe to it, because forged hello messages can redirect Sentinels and leak credentials. Avoid `&*` for any user on those nodes, including the legacy `default` user.
- Search indexes: a user can create or read an index only over key prefixes inside its own key patterns.
- `rename-command` is deprecated; use ACLs instead.

Persist users: define them in `aclfile` and use `ACL SAVE`/`ACL LOAD`, or put `user` lines in `redis.conf` and `CONFIG REWRITE`. `ACL LOAD` keeps existing connections since [7.4](versions/7.4.md). Duplicate user declarations at startup are an error (7.0+).

Audit:

```
ACL LOG 10          # recent denials: reason, username, client info
ACL LOG RESET
INFO stats          # acl_access_denied_auth, _cmd, _key, _channel, _tls_cert (8.6+)
ACL DRYRUN app SET app:1 x     # 7.0+: would this user be allowed?
ACL GETUSER app
```

From 8.6, personal data is hidden from ACL logs and server logs; `hide-user-data-from-log` ([7.4](versions/7.4.md)+, default `no`) hides user data in the server log. There is no built-in audit log of successful commands; `MONITOR` shows everything but costs throughput and exposes data. Do not leave it running.

## TLS

TLS must be compiled in (`BUILD_TLS=yes`). Configure:

```
port 0                          # disable plaintext, or keep both during migration
tls-port 6379
tls-cert-file /etc/redis/tls/redis.crt
tls-key-file /etc/redis/tls/redis.key
tls-ca-cert-file /etc/redis/tls/ca.crt
tls-auth-clients yes            # default: clients must present a trusted certificate (mTLS)
tls-replication yes             # replica side: TLS to the primary
tls-cluster yes                 # cluster bus
tls-protocols "TLSv1.2 TLSv1.3"
```

- `tls-auth-clients yes` is the default (8.12 image): a server certificate alone is not enough; clients must present one too. Set `tls-auth-clients no` when clients authenticate by password only. `tls-auth-clients` also accepts `optional` (8.12.0: `CONFIG SET` accepts `no`, `yes`, `optional`; checked on a server without TLS ports, so the handshake behavior was not tested).
- Certificate-to-user mapping (`tls-auth-clients-user`, [8.6](versions/8.6.md)+) authenticates clients by certificate; failures increment `acl_access_denied_tls_cert`.
- `tls-groups` ([8.12](versions/8.12.md)) sets key exchange groups, for example `X25519:prime256v1`; both sides must share one. Changeable at runtime; an invalid name leaves the old value in effect.
- Sentinel uses `tls-replication` to decide whether to talk TLS to data nodes and on its own port.
- Since 8.0, TLS and I/O threads work together.
- TLS lowers per-instance throughput; benchmark with `redis-benchmark --tls` before sizing.
- Certificate-check fixes: 8.10.1 fixed a client-certificate bypass where a Common Name with an embedded NUL byte let a client authenticate as another ACL user, and a use-after-free in the TLS pending-data list (also fixed in 6.2.24); 8.12.0 fixed TLS session resumption across listeners and after changes to `tls-auth-clients` or `tls-expected-peer-name`. If you rely on certificate authentication, run a patch that includes these fixes; check the release notes of your series.

Rotate certificates: replace the files and `CONFIG SET tls-cert-file <path>` to reload. The reload builds a new TLS context for new connections (`tlsConfigure` in `src/tls.c`); connections already established keep the session they negotiated. Confirm what new clients get with `openssl s_client -connect <host>:6379 </dev/null 2>/dev/null | openssl x509 -noout -enddate`. Check expiry with `openssl x509 -enddate -noout -in redis.crt`.

Verify:

```
redis-cli --tls --cacert ca.crt --cert client.crt --key client.key -p 6379 PING
openssl s_client -connect host:6379 -CAfile ca.crt </dev/null | head
```

## Dangerous Operations

| Command | Risk | Safer path |
|---|---|---|
| `FLUSHALL`, `FLUSHDB` | Drops data; `FLUSHALL` also clears the RDB and saves an empty one when `save` is set | Block via ACL (`-flushall -flushdb`); use `ASYNC` when intended |
| `KEYS`, `SMEMBERS`/`HGETALL` on big keys | Blocks the server | `SCAN`, `SSCAN`, `HSCAN` |
| `CONFIG SET` of file-location parameters | Historical file-write attack vector | Kept out of reach by `enable-protected-configs no` (the protected configs are `dir` and `dbfilename`, `PROTECTED_CONFIG` in `src/config.c` of 7.0.0 and 8.12.0) and by `-@admin` |
| `DEBUG`, `MODULE LOAD` | Crash or arbitrary code | Disabled by default since 7.0 |
| `SHUTDOWN`, `REPLICAOF`, `FAILOVER`, `CLUSTER RESET` | Outage or data loss | Admin users only |
| `EVAL` with untrusted script text | Script runs with the caller's rights and blocks the server | Never build scripts from user input; apply Lua CVE patches (many 6.2 to 8.x patch releases fix Lua issues) |

## Common Mistakes

- Container or cloud instance with `protected-mode no` and `nopass` on a reachable port.
- Using the `default` user for applications, so a leaked password is full admin.
- Relying on `requirepass` alone: it sets the default user's password; all clients share one secret.
- Forgetting `masteruser`/`masterauth` on replicas after enabling ACLs; replication breaks with authentication errors.
- ACL rules defined only with `ACL SETUSER` and never saved; they vanish on restart.

Sources: https://redis.io/docs/latest/operate/oss_and_stack/management/security/, https://redis.io/docs/latest/operate/oss_and_stack/management/security/acl/, https://redis.io/docs/latest/operate/oss_and_stack/management/security/encryption/, https://redis.io/docs/latest/operate/oss_and_stack/management/sentinel/, https://redis.io/docs/latest/commands/flushall/, https://raw.githubusercontent.com/redis/redis/7.0.0/00-RELEASENOTES, https://raw.githubusercontent.com/redis/redis/7.4.0/00-RELEASENOTES, https://raw.githubusercontent.com/redis/redis/6.2/00-RELEASENOTES, https://redis.io/docs/latest/develop/whats-new/8-6/, https://redis.io/docs/latest/operate/oss_and_stack/stack-with-enterprise/release-notes/redisce/redisos-8.10-release-notes/, https://redis.io/docs/latest/develop/whats-new/8-12/ (checked 2026-11-27); images `redis:7.2` to `redis:8.12`, statement runs and `CONFIG GET` output (2026-11-27).
