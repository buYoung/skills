---
name: vite-guide
description: Use for explaining, designing, implementing, reviewing, refactoring, migrating, or diagnosing Vite 7/8 applications when runtime, build, plugin, deployment, performance, or compatibility judgment is needed, including CSR SPA/MPA, backend-embedded clients, and Vite's own SSR development and production integration. Excludes framework-specific SSR APIs, RSC/Server Functions implementation, custom server-runtime construction, unsupported Vite majors, unrelated non-client bundling, and UI-framework-only decisions.
license: MIT
---

# Vite Guide

Establish the exact installed/target Vite, Node, and plugin versions and whether the path is client rendering, backend integration, or SSR. Check the target package's `engines.node` and plugin peer contracts from installed metadata or its tagged official source. Vite 7.0.0 and 8.0.0 declare `^20.19.0 || >=22.12.0`: Node 21 does not satisfy this range. Do not replace that contract with "any later major" or infer it from the guide's major range.

When facts are missing, continue investigation and common guidance; defer only dependent API/configuration choices and unsupported execution. Existing failures are diagnosis and repair targets. Reconstruct migration evidence from current source if no prior report exists. Check [official release support](https://vite.dev/releases) separately when maintenance status matters: this guide's diagnostic coverage of Vite 7/8 does not promise upstream maintenance or feature backports. Verify minor-specific and experimental features before using them.

## Route

Start with the closest reference, then read related references directly as needed. Collect only the evidence relevant to the requested explanation, implementation, or review.

- Entry, dev server, proxy, env, assets, diagnostics: [client runtime](references/vite-client-runtime.md)
- Imports, chunks, Rollup/Rolldown, plugins, performance: [build and plugins](references/vite-build-plugins.md)
- Base path, caching, stale chunks, reload: [deployment](references/vite-deployment.md)
- SSR middleware, module loading, separate builds, manifests, dependencies: [SSR integration](references/vite-ssr.md)
- Vite 6 departure: [Vite 6 to 7 migration](references/vite-6-to-7-migration.md)
- Vite 7 departure and Vite 8 arrival: [Vite 7 to 8 migration](references/vite-7-to-8-migration.md)

## Boundary

Vite owns module loading, build artifacts, plugin integration, and deployment configuration. UI-framework guidance owns rendering, hydration, component state, and recovery semantics. Use both guides for a task spanning these layers; React applications can pair this guide with `react-guide`. Gather missing framework evidence directly without requiring a formal handoff or caller identity. Respect actual task ownership restrictions.

Support Vite SSR inside an existing host. Framework-specific APIs, RSC/Server Functions implementation, and construction of a custom server runtime remain outside this guide. Preserve existing `ssrLoadModule` integrations; Environment API adoption is a separate decision based on the project's integration and the target version's stability contract.

Adapt the response to the request: decisions and evidence, changes or findings, performed verification, and unresolved risks. Claim performance gains only from comparable before/after measurements. Never report blocked, failed, or unrun verification as passed.

Runtime examples: [Vite 7.0.0 package](https://github.com/vitejs/vite/blob/v7.0.0/packages/vite/package.json), [Vite 8.0.0 package](https://github.com/vitejs/vite/blob/v8.0.0/packages/vite/package.json).
