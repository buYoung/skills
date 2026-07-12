---
name: react-vite-guide
description: >
  Use for implementation, review, refactoring, migration, or diagnosis in a
  React 18 or React 19 project built with Vite 7 when the task requires React
  design judgment, version compatibility, or a Vite client build decision.
  The primary scope is browser-rendered CSR SPA/MPA and Vite client builds
  embedded in an existing backend. Do not use by default for non-Vite React,
  React 17 or earlier, React 20 or later, Vite 6 or earlier, Vite 8 or later,
  framework-owned SSR/RSC/server functions, or isolated copy and styling work.
license: MIT
---

# React + Vite Execution Router

## Scope and Classification

Apply only to CSR SPA/MPA or an existing backend's Vite client. Stop on SSR, hydration architecture, RSC, or server-function ownership.

Record once: `request_mode` (`implement|review|migrate|diagnose`), mutation authority, requested outcome, resolved React/Vite versions, React 19.2 gate, app/library/mixed consumers, CSR boundary, and the first observed work signal. Do not infer unresolved or mixed versions.

Only when the signal is Vite work, also collect the actual Node version plus CI/runtime evidence. Continue to the selected Vite leaf only when Vite is in that leaf's supported source/target boundary and Node satisfies `(major == 20 and minor >= 19)`, `(major == 22 and minor >= 12)`, or `major > 22`; otherwise return a blocked record before reading a leaf. Pass this preflight evidence unchanged.

## Conditional Table of Contents

Choose exactly one initial leaf closest to the requested outcome. Read another leaf only when the first leaf returns it.

| Initial signal or task | Initial leaf |
|---|---|
| Component size/separation/composition, feature folders, export/import, public API | [React structure and public API](references/react-structure-public-api.md) |
| Custom Hook extraction, duplicate lifecycle, unnecessary Effect, subscription/timer/browser API | [React Hooks and Effects](references/react-hooks-effects.md) |
| State lift/down, reducer/Context/store, URL state, server-data owner, request lifetime | [React state and data](references/react-state-data.md) |
| Rerender, memoization, Profiler, performance claim, Compiler-related optimization | [React render performance](references/react-render-performance.md) |
| Lazy/Suspense, loading/background/empty/error, Error Boundary, retry/reset | [React async UI](references/react-async-ui.md) |
| Already-owned control/navigation semantics, keyboard/focus/name, announcement, reduced motion | [React accessibility](references/react-accessibility.md) |
| React 18 root/unmount warning, ref/Context syntax, React 18 Compiler compatibility | [React 18 runtime compatibility](references/react-18-runtime-compatibility.md) |
| Explicit React 18→19 departure audit | [React 18 to 19 migration](references/react-18-to-19-migration.md) |
| React 19 migration arrival validation with normalized departure evidence already present | [React 19 migration](references/react-19-migration.md) |
| React 19 ref/provider, `Activity`, `useEffectEvent` | [React 19 component APIs](references/react-19-component-apis.md) |
| React 19 form submission/mutation owner, Action API, or `use(Context|Promise)` | [React 19 Actions and async APIs](references/react-19-actions-async.md) |
| Compiler performance/optimization without normalized baseline | [React render performance](references/react-render-performance.md) |
| Vite 7 entry/dev/proxy, env/mode, asset URL/public/query | [Vite 7 client runtime](references/vite-7-client-runtime.md) |
| Vite 7 dynamic import/chunk/import graph, `manualChunks`, plugin | [Vite 7 build and plugins](references/vite-7-build-plugins.md) |
| Vite 7 subpath, cache headers, stale chunk, reload recovery | [Vite 7 deployment](references/vite-7-deployment.md) |
| Explicit Vite 6→7 migration | [Vite 6 to 7 migration](references/vite-6-to-7-migration.md) |

## Minimal Execution Loop

1. Run the selected leaf with the common inputs.
2. Collect its decision record. Pass `handoff_evidence` unchanged to its exact `next_reference`.
3. A leaf handoff must be `none`, an exact relative `.md` path, or `return_to_caller`. Resolve `return_to_caller` only from the exact caller path in received evidence; local compare/reverify stays inside the current leaf.
4. Do not revisit an owner already decided unless new evidence is returned.
5. Stop on a handoff cycle, version/scope mismatch, missing required evidence, failed verification, breaking public decision without approval, or mutation beyond authority.
6. Finish when `next_reference` is `none` and the request-mode completion rule is met.

## Common Decision Record

```yaml
reference: <leaf filename>
task_branch: <executed responsibility>
inputs_observed: [<paths, owners, symptoms, measurements>]
decision: <selection or not-applied>
actions_or_findings: [<authorized changes or read-only findings>]
verification:
  status: passed | failed | not-run | blocked
  evidence: <result or reason>
stop_reason: <none or reason>
next_reference: <none or relative leaf path>
handoff_evidence: [<evidence the next leaf can reuse>]
```

## Complete or Stop

- `review`: finish with evidence-backed findings and risks; no mutation is required.
- `diagnose`: finish with root cause, affected owner, and verification evidence.
- `implement|migrate`: finish with authorized changes and proportionate verification.

Return the classification, visited leaves, decision records, stopped/non-applied branches, and remaining unverified risks. A blocked or failed leaf cannot be reported as passed.
