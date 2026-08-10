---
name: vite-guide
description: Use for implementing, reviewing, refactoring, migrating, or diagnosing Vite 7/8 browser clients when runtime, build, plugin, deployment, performance, or compatibility judgment is needed, including CSR SPA/MPA and backend-embedded clients. Excludes framework-owned SSR/server functions, unsupported Vite majors, non-client bundling, and UI-framework decisions.
license: MIT
---

# Vite Guide

Confirm the exact Vite and Node versions. Require Node 20.19+, 22.12+, or a later major; stop on unresolved or unsupported versions and unapproved prerelease features.

## Route

Open only the closest reference; follow an explicit `next_reference` when needed.

- Entry, dev server, proxy, env, assets, diagnostics: [client runtime](references/vite-client-runtime.md)
- Imports, chunks, Rollup/Rolldown, plugins, performance: [build and plugins](references/vite-build-plugins.md)
- Base path, caching, stale chunks, reload: [deployment](references/vite-deployment.md)
- Vite 6 departure: [Vite 6 to 7 migration](references/vite-6-to-7-migration.md)
- Vite 7 departure and Vite 8 arrival: [Vite 7 to 8 migration](references/vite-7-to-8-migration.md)

## Boundary

Keep UI-framework decisions outside this skill. For framework-owned lazy boundaries, Compiler semantics, or recovery UI, require the caller's framework decision and return only Vite build or deployment evidence.

Return the selected reference, decision, changes or findings, verification status and evidence, next owner, and unverified risks. Never report blocked, failed, or unrun verification as passed.
