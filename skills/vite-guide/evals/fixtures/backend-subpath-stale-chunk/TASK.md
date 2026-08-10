# DEP-209: old console tabs loop after deploy

The backend mounts this SPA at `/console/`. Each release removes assets from the previous release. Operators commonly keep a tab open while drafting incident notes.

Captured failure chain:

1. An already-open tab requests a removed dynamic chunk and receives 404.
2. The browser emits Vite's preload failure event.
3. The current bootstrap reloads the page unconditionally.
4. The cached HTML still names the removed chunk, producing a reload loop and sometimes losing an operator draft.
5. Direct navigation and refresh must continue falling back to the SPA entry under `/console/`.

Coordinate the authorized layers in `OWNERSHIP.md` so newly served HTML is always current, content-addressed assets remain long-lived, and one stale client can recover without repeated automatic reloads or silent work loss. A successful boot must not permanently prevent recovery from a later release. Preserve existing hashed asset naming. Do not install dependencies. `REPORT.md` must explain the full topology, cache/recovery contract, verification limits, rollback, and any handoff required for user-visible behavior.
