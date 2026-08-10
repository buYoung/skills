---
name: react-guide
description: >
  Use for implementation, review, refactoring, migration, or diagnosis in a
  browser-rendered React 18 or React 19 CSR application when the task requires
  React design judgment or version compatibility. Covers component/public API
  structure, Hooks and Effects, state/data ownership, render performance,
  async UI, accessibility, React 18→19 migration, React 19 APIs, and React
  Compiler behavior independently of the build tool. Do not use by default
  for React 17 or earlier, React 20 or later, SSR/hydration/RSC/server
  functions, build-tool configuration, or isolated copy and styling work.
license: MIT
---

# React Execution Router

## Scope and Classification

Apply only to browser-rendered React 18/19 CSR or a client island whose server boundary is already owned elsewhere. Stop on SSR/hydration architecture, RSC, server functions, or an unresolved React major.

Record once: `request_mode` (`implement|review|migrate|diagnose`), mutation authority, requested outcome, resolved `react/react-dom` versions, React 19.2 gate, app/library/mixed consumers, CSR boundary, optional build-tool identity, and the first observed work signal. Do not infer unresolved or mixed versions.

## Conditional Table of Contents

Choose exactly one initial leaf closest to the requested outcome. Read another leaf only when the first leaf returns it.

| Initial signal or task | Initial leaf |
|---|---|
| Component size/separation/composition, feature folders, export/import, public API | [React structure and public API](references/react-structure-public-api.md) |
| Custom Hook extraction, duplicate lifecycle, unnecessary Effect, subscription/timer/browser API | [React Hooks and Effects](references/react-hooks-effects.md) |
| State lift/down, reducer/Context/store, URL state, server-data owner, request lifetime | [React state and data](references/react-state-data.md) |
| Rerender, memoization, Profiler, Performance Tracks, Compiler-related optimization | [React render performance](references/react-render-performance.md) |
| Lazy/Suspense, loading/background/empty/error, Error Boundary, retry/reset | [React async UI](references/react-async-ui.md) |
| Already-owned control/navigation semantics, keyboard/focus/name, announcement, reduced motion | [React accessibility](references/react-accessibility.md) |
| React 18 root/unmount warning, ref/Context syntax, React 18 Compiler compatibility | [React 18 runtime compatibility](references/react-18-runtime-compatibility.md) |
| Explicit React 18→19 departure audit | [React 18 to 19 migration](references/react-18-to-19-migration.md) |
| React 19 arrival validation with normalized departure evidence | [React 19 migration](references/react-19-migration.md) |
| React 19 ref/provider, `Activity`, `useEffectEvent` | [React 19 component APIs](references/react-19-component-apis.md) |
| React 19 form mutation, Action API, or `use(Context|Promise)` | [React 19 Actions and async APIs](references/react-19-actions-async.md) |
| Explicit React 19 Compiler config/diagnostics with caller evidence | [React 19 Compiler](references/react-19-compiler.md) |

## Cross-Skill Boundary

Keep React ownership here. When a resolved Vite 7/8 client requires bundler output, `@vitejs/plugin-react`, or deployed-chunk recovery evidence, return `next_skill: react-vite-guide` with the React decision and caller identity. For another or unresolved build tool, return the external build-owner need without guessing its integration. Do not link directly into another skill package.

## Minimal Execution Loop

1. Run the selected leaf with the common inputs.
2. Pass `handoff_evidence` unchanged to an exact internal `next_reference`.
3. Use `next_skill` only after the React owner decision is complete enough for an integration handoff.
4. Do not revisit an owner unless new evidence returns from the exact caller.
5. Stop on a handoff cycle, version/scope mismatch, missing required evidence, failed verification, breaking public decision without approval, or mutation beyond authority.

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
next_skill: <none | react-vite-guide | return_to_caller>
handoff_evidence: [<evidence the next owner can reuse>]
```

## Complete or Stop

- `review`: finish with evidence-backed findings and risks; no mutation is required.
- `diagnose`: finish with root cause, affected React owner, and verification evidence.
- `implement|migrate`: finish with authorized React changes and proportionate verification.

Return the classification, visited leaves, decision records, stopped/non-applied branches, cross-skill handoffs, and remaining unverified risks. A blocked or failed leaf cannot be reported as passed.
