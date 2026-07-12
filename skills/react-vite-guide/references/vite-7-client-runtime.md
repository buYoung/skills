# Vite 7 Client Runtime

## Read When

Read for preflight-validated Vite 7 entry/dev/proxy/alias, env/mode/exposure, or asset URL/public/query work. Exclude build chunks/plugins, deployment recovery, migration, and shared runtime gating.

## Collect Inputs

First set `responsibility` to `entry-dev`, `env`, or `asset`. Always receive the validated Vite/Node preflight record. Then collect only:

- `entry-dev`: workspace/root, config, HTML/input, scripts, requested alias/proxy.
- `env`: owner, mode/source, prefix, sensitivity, expected type, build-time versus deploy-time need.
- `asset`: consumer API, source ownership, filename stability, representation, and base path.

## Decision Sequence and Table

1. Select responsibility. 2. Collect only its inputs. 3. Identify its owner. 4. Make the minimum edit/finding. 5. Run only its verification.

| Observation | Selection | Action | Handoff |
|---|---|---|---|
| Valid root/configured MPA entry | retain | No boilerplate change | none |
| Alias mismatch | aligned resolution | Change Vite and language paths together | none |
| Dev-only API routing | dev proxy | Keep production behavior separate | none |
| Public build-time env value | direct `import.meta.env` | Static access/explicit conversion | none |
| Secret or deploy-time mutable value | non-client owner | Remove exposure; return scope stop | none |
| Source-owned asset | source import/CSS URL | Use graph transform/hash | none |
| Fixed/unreferenced filename | `public` | Use base-aware direct URL | none |
| Consumer-specific representation | query suffix | Select URL/raw/inline/no-inline | none |

## Actions and Prohibitions

Do not re-evaluate the common runtime gate. For `entry-dev`, avoid hidden root changes and production security in a proxy. For `env`, avoid secrets, dynamic keys, and prefix-as-security claims. For `asset`, avoid hardcoded subpath roots, ordinary source assets in `public`, and incidental plugins.

## Stop or Roll Back

For `entry-dev`, stop only on ambiguous root or unsupported hook. For `env`, stop only on secret/deploy-time owner or unresolved prefix/source. For `asset`, stop only on missing asset, representation, or base conflict. Roll back only the selected responsibility on its dev/build regression.

## Verify

Verify only the selected responsibility: entry/navigation/alias/proxy/build; mode/source/exposure/conversion; or emitted asset name/hash/query/base/loading.

## Return and Handoff

Return the selected responsibility's decision and evidence with `next_reference: none`. SSR/server-owned runtime configuration returns a scope stop; do not route through another Vite leaf.

Fact sources: [Vite guide](https://vite.dev/guide/), [env](https://vite.dev/guide/env-and-mode), and [assets](https://vite.dev/guide/assets).
