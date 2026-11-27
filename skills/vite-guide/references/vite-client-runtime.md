# Vite 7/8 Client Runtime

## Read When

Read for Vite 7 or 8 entry/dev/proxy/alias, dev-server file access, env/mode/exposure, asset URL/public/query, or Vite 8 path-resolution and diagnostic work. Use related build, deployment, migration, or SSR guidance when those concerns are involved.

## Collect Inputs

Identify the relevant `entry-dev`, `env`, `asset`, or `diagnostics` paths and inspect exact Vite/Node versions. Collect their inputs as needed:

- `entry-dev`: workspace/root, config, HTML/input, scripts, requested alias/proxy, TypeScript config owner, import consumers, and dev-server reachability with its `server.fs` settings.
- `env`: owner, mode/source, prefix, sensitivity, expected type, build-time versus deploy-time need.
- `asset`: consumer API, source ownership, filename stability, representation, base path, and custom HTML element/attribute when relevant.
- `diagnostics`: reproduced browser symptom, missing terminal evidence, current console/devtools setup, desired signal, dependency authority, and rollback point.

## Decision Sequence and Table

1. Select responsibility. 2. Apply the exact version gate. 3. Identify the owner. 4. Make the minimum edit/finding. 5. Run only its verification.

| Observation | Selection | Action | Related guidance |
|---|---|---|---|
| Valid root/configured MPA entry | retain | No boilerplate change | none |
| Alias mismatch with explicit config owner | aligned resolution | Change Vite and language paths together | none |
| Vite 8 `tsconfig` paths are authoritative and matching cost is accepted | built-in path resolution | Enable `resolve.tsconfigPaths`; avoid a competing alias copy | none |
| Vite 8.4+ new path mapping can use package.json `imports` (`#` specifiers) | subpath imports | Prefer them over a new `resolve.alias` or tsconfig paths, as the Vite 8.4 announcement recommends; CSS `url()` resolves them from 8.4 | none |
| Vite 8.4+ dev server may be reachable by others, or an allow-list policy is requested | extended file-serve check | Set `server.fs.strict: 'extended'`; adding `server.fs.allow: []` serves only files referenced from the entries | none |
| Dev-only API routing | dev proxy | Keep production behavior separate | none |
| Public build-time env value | direct `import.meta.env` | Static access/explicit conversion | none |
| Secret or deploy-time mutable value | non-client owner | Remove client exposure; use server runtime or explicit public runtime configuration | none |
| Source-owned asset | source import/CSS URL | Use graph transform/hash | none |
| Fixed/unreferenced filename | `public` | Use base-aware direct URL | none |
| Consumer-specific representation | query suffix | Select URL/raw/inline/no-inline | none |
| Vite 8.1+ custom HTML element or attribute owns an asset URL | `html.additionalAssetSources` | Map only the evidenced element to `srcAttributes`/`srcsetAttributes`; narrow with `filter` when needed | none |
| Supported Vite minor, browser error is absent from agent-visible output | scoped console forwarding | Forward only required unhandled/log levels in development | none |
| DevTools requested | version/command check | Confirm experimental support, the minor's supported commands, and package compatibility | none |

## Actions and Prohibitions

Do not use a Vite 8-only option under Vite 7 or a minor-gated option below its minor; inspect installed metadata when version evidence is incomplete. For `entry-dev`, avoid hidden root changes, duplicated alias owners, and production security in a proxy. For `env`, avoid secrets, dynamic keys, and prefix-as-security claims. For `asset`, avoid hardcoded subpath roots, ordinary source assets in `public`, and broad custom-attribute matching. For `diagnostics`, preserve browser reproduction and do not forward sensitive application data or treat forwarded logs as a production observability system.

## Uncertainty and Regressions

Investigate ambiguous roots, missing assets, exposure defects, and broken imports. Defer only the choice that depends on an unresolved runtime, asset representation, or public configuration contract. For diagnostics, check exact minor support and avoid sensitive logs; repair or revert a selected change that regresses dev/build behavior.

## Diagnostic Mode and Version Boundaries

`server.forwardConsole` forwards selected browser events/log levels to the development server's terminal in supporting Vite 8 versions. It is a development diagnostic path, not production logging or build analysis. Inspect the installed minor's option/defaults; do not infer availability in Vite 7 from current Vite 8 documentation.

The separate `devtools` option is experimental, defaults to `false`, and requires a compatible `@vitejs/devtools` dependency. Through Vite 8.2 it runs only in build mode. From 8.3 it runs for both `serve` and `build` by default: use `apply` to limit it to one command, install `@vitejs/devtools-vite` for dev-server inspection and `@vitejs/devtools-rolldown` for build analysis, and set it in user config because plugin `config` hooks cannot change it. Check those conditions before enabling it; it does not replace a browser reproduction or console forwarding. See [server options](https://vite.dev/config/server-options#server-forwardconsole), [DevTools options](https://vite.dev/config/shared-options#devtools), and the [8.3.0 changelog](https://github.com/vitejs/vite/blob/v8.4.0/packages/vite/CHANGELOG.md#830-2026-09-10).

## Verify

Verify only the selected responsibility: entry/navigation/alias/proxy/build; mode/source/exposure/conversion; emitted asset name/hash/query/base/loading; or the exact browser event/log level reaching the terminal without unrelated data. For `resolve.tsconfigPaths`, verify the matching `tsconfig` include/files scope and affected imports. For extended `server.fs.strict`, verify that entries, CSS `url()` assets, and plugin-generated modules still load, and with `server.fs.allow: []` that an unreferenced file is refused.

## Result and Related Guidance

Explain the runtime decision and relevant checks. Use [SSR integration](vite-ssr.md) for server module execution and env boundaries, [build/plugins](vite-build-plugins.md) for output, and [deployment](vite-deployment.md) for production paths. An absent preflight report is not a blocker.

Fact sources: [Vite guide](https://vite.dev/guide/), [env](https://vite.dev/guide/env-and-mode), [assets](https://vite.dev/guide/assets), [shared options](https://vite.dev/config/shared-options) including [`html.additionalAssetSources`](https://vite.dev/config/shared-options#html-additionalassetsources), [server options](https://vite.dev/config/server-options) including [`server.fs.strict`](https://vite.dev/config/server-options#server-fs-strict), and the [Vite 8.4 announcement](https://vite.dev/blog/announcing-vite8-4).
