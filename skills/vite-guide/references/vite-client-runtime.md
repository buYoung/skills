# Vite 7/8 Client Runtime

## Read When

Read for preflight-validated Vite 7 or 8 entry/dev/proxy/alias, env/mode/exposure, asset URL/public/query, or Vite 8 path-resolution and diagnostic work. Exclude build chunks/plugins, deployment recovery, migration, and shared runtime gating.

## Collect Inputs

First set `responsibility` to `entry-dev`, `env`, `asset`, or `diagnostics`; receive the validated Vite/Node preflight record and exact Vite major/minor. Then collect only:

- `entry-dev`: workspace/root, config, HTML/input, scripts, requested alias/proxy, TypeScript config owner, and import consumers.
- `env`: owner, mode/source, prefix, sensitivity, expected type, build-time versus deploy-time need.
- `asset`: consumer API, source ownership, filename stability, representation, base path, and custom HTML element/attribute when relevant.
- `diagnostics`: reproduced browser symptom, missing terminal evidence, current console/devtools setup, desired signal, dependency authority, and rollback point.

## Decision Sequence and Table

1. Select responsibility. 2. Apply the exact version gate. 3. Identify the owner. 4. Make the minimum edit/finding. 5. Run only its verification.

| Observation | Selection | Action | Handoff |
|---|---|---|---|
| Valid root/configured MPA entry | retain | No boilerplate change | none |
| Alias mismatch with explicit config owner | aligned resolution | Change Vite and language paths together | none |
| Vite 8 `tsconfig` paths are authoritative and matching cost is accepted | built-in path resolution | Enable `resolve.tsconfigPaths`; avoid a competing alias copy | none |
| Dev-only API routing | dev proxy | Keep production behavior separate | none |
| Public build-time env value | direct `import.meta.env` | Static access/explicit conversion | none |
| Secret or deploy-time mutable value | non-client owner | Remove exposure; return scope stop | none |
| Source-owned asset | source import/CSS URL | Use graph transform/hash | none |
| Fixed/unreferenced filename | `public` | Use base-aware direct URL | none |
| Consumer-specific representation | query suffix | Select URL/raw/inline/no-inline | none |
| Vite 8.1+ custom HTML attribute owns an asset URL | additional asset source | Configure only the evidenced element/attribute | none |
| Vite 8 browser error is absent from agent-visible output | scoped console forwarding | Forward only required unhandled/log levels in development | none |
| Devtools requested without package/experimental authority | blocked | Do not install or enable | none |

## Actions and Prohibitions

Do not re-evaluate the common runtime gate or use a Vite 8-only option under Vite 7. For `entry-dev`, avoid hidden root changes, duplicated alias owners, and production security in a proxy. For `env`, avoid secrets, dynamic keys, and prefix-as-security claims. For `asset`, avoid hardcoded subpath roots, ordinary source assets in `public`, and broad custom-attribute matching. For `diagnostics`, preserve browser reproduction and do not forward sensitive application data or treat forwarded logs as a production observability system.

## Stop or Roll Back

For `entry-dev`, stop only on ambiguous root, conflicting alias owners, or unsupported hook. For `env`, stop only on secret/deploy-time owner or unresolved prefix/source. For `asset`, stop only on missing asset, representation, or base conflict. For `diagnostics`, stop on missing reproduction, unsupported Vite minor, sensitive output, or dependency authority. Roll back only the selected responsibility on its dev/build regression.

## Verify

Verify only the selected responsibility: entry/navigation/alias/proxy/build; mode/source/exposure/conversion; emitted asset name/hash/query/base/loading; or the exact browser event/log level reaching the terminal without unrelated data. For `resolve.tsconfigPaths`, verify the matching `tsconfig` include/files scope and affected imports.

## Return and Handoff

Return the selected responsibility's decision and evidence with `next_reference: none`. SSR/server-owned runtime configuration returns a scope stop; do not route through another Vite leaf.

Fact sources: [Vite guide](https://vite.dev/guide/), [env](https://vite.dev/guide/env-and-mode), [assets](https://vite.dev/guide/assets), [shared options](https://vite.dev/config/shared-options), and [server options](https://vite.dev/config/server-options).
