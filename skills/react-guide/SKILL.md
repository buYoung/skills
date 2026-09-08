---
name: react-guide
description: Use for explaining, designing, implementing, reviewing, refactoring, migrating, or diagnosing React 18/19 applications when React-specific judgment is needed for CSR, SSR, streaming, hydration, structure, APIs, Hooks, state/data, async UI, accessibility, performance, compatibility, or Compiler behavior. Covers React's own server-rendering APIs; excludes framework-specific APIs, RSC/Server Functions implementation, custom server-runtime construction, unsupported React majors, build-tool-only work, and styling/copy-only work.
license: MIT
---

# React Guide

Establish the installed `react`/`react-dom` versions, supported consumers, and rendering path: client rendering, server rendering, or hydration. Inspect package/lockfile and entry-point evidence when available. If versions or inputs are missing, continue investigation and version-independent explanation; defer only choices that depend on the missing facts. Do not assume every React 19 minor exposes the same APIs.

Treat existing defects, incomplete cleanup, and failed checks as diagnosis and repair work. Ask for a decision only when an unresolved product or compatibility choice changes the solution. Migration evidence can come from current source and diagnostics; a prior-stage report is not required.

## Route

Start with the closest reference, then read related references directly as the task crosses topics. Use their inputs and checks selectively for the requested explanation, implementation, or review.

- Structure, composition, exports: [structure and public API](references/react-structure-public-api.md)
- Hooks, Effects, subscriptions: [Hooks and Effects](references/react-hooks-effects.md)
- Local/shared/URL/server state: [state and data](references/react-state-data.md)
- Rerenders, profiling, memoization: [render performance](references/react-render-performance.md)
- Suspense, loading, errors, retry: [async UI](references/react-async-ui.md)
- Server APIs, streaming, initial data, hydration mismatches: [SSR and hydration](references/react-ssr-hydration.md)
- Semantics, keyboard, focus, announcements: [accessibility](references/react-accessibility.md)
- React 18 runtime or Compiler compatibility: [React 18 compatibility](references/react-18-runtime-compatibility.md)
- React 18 departure audit: [React 18 to 19 migration](references/react-18-to-19-migration.md)
- React 19 arrival validation: [React 19 migration](references/react-19-migration.md)
- React 19 ref/provider or 19.2 APIs: [React 19 component APIs](references/react-19-component-apis.md)
- React 19 Actions, forms, `use`: [React 19 async APIs](references/react-19-actions-async.md)
- React Compiler config or diagnostics: [React 19 Compiler](references/react-19-compiler.md)

## Boundary

This skill explains React rendering and state semantics. A build-tool guide owns module loading, client/server artifacts, plugin adapters, and deployment configuration. For a task spanning both, use both guides and connect their evidence; for Vite, pair this guide with `vite-guide`. An artificial handoff or caller identity is unnecessary. Respect actual ownership restrictions supplied by the task.

Keep framework-specific routing/data APIs, RSC/Server Functions implementation, and construction of a custom server runtime outside this guide. Ordinary React SSR within an existing host is supported.

Adapt the response to the request: explain the decision and evidence, report changes or findings, and distinguish performed checks from remaining runtime risks. Claim a performance improvement only with comparable before/after measurements. Do not report blocked, failed, or unrun verification as passed.
