---
name: react-guide
description: Use for implementing, reviewing, refactoring, migrating, or diagnosing React 18/19 browser CSR when React-specific judgment is needed for structure, APIs, Hooks, state/data, async UI, accessibility, performance, compatibility, or Compiler behavior. Excludes SSR/hydration/RSC/server functions, unsupported React majors, build-tool-only work, and styling/copy-only work.
license: MIT
---

# React Guide

Confirm the exact `react`/`react-dom` version and CSR boundary. Stop when the version is unresolved or the server owns the behavior.

## Route

Open only the closest reference; follow an explicit `next_reference` when needed.

- Structure, composition, exports: [structure and public API](references/react-structure-public-api.md)
- Hooks, Effects, subscriptions: [Hooks and Effects](references/react-hooks-effects.md)
- Local/shared/URL/server state: [state and data](references/react-state-data.md)
- Rerenders, profiling, memoization: [render performance](references/react-render-performance.md)
- Suspense, loading, errors, retry: [async UI](references/react-async-ui.md)
- Semantics, keyboard, focus, announcements: [accessibility](references/react-accessibility.md)
- React 18 runtime or Compiler compatibility: [React 18 compatibility](references/react-18-runtime-compatibility.md)
- React 18 departure audit: [React 18 to 19 migration](references/react-18-to-19-migration.md)
- React 19 arrival validation: [React 19 migration](references/react-19-migration.md)
- React 19 ref/provider or 19.2 APIs: [React 19 component APIs](references/react-19-component-apis.md)
- React 19 Actions, forms, `use`: [React 19 async APIs](references/react-19-actions-async.md)
- React Compiler config or diagnostics: [React 19 Compiler](references/react-19-compiler.md)

## Boundary

Keep build-tool decisions outside this skill. For lazy chunks, Compiler adapters, or stale-chunk deployment, return the React decision and the exact build evidence still required without selecting build configuration.

Return the selected reference, decision, changes or findings, verification status and evidence, next owner, and unverified risks. Never report blocked, failed, or unrun verification as passed.
