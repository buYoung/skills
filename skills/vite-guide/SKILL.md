---
name: vite-guide
description: >
  Use for implementation, review, refactoring, migration, or diagnosis in a
  Vite 7 or Vite 8 browser client when the task requires Vite runtime, build,
  plugin, deployment, performance, or version-compatibility judgment. Covers
  CSR SPA/MPA clients and Vite clients embedded in an existing backend,
  independently of the UI framework. Do not use by default for Vite 6 or
  earlier, Vite 9 or later, framework-owned SSR/server functions, non-client
  bundling, or UI-framework component and state decisions.
license: MIT
---

# Vite Execution Router

## Scope and Classification

Apply only to a Vite 7/8 browser client for CSR SPA/MPA or an existing backend's client build. Stop on framework-owned SSR, server functions, or an unresolved Vite major.

Record once: `request_mode` (`implement|review|migrate|diagnose`), mutation authority, requested outcome, resolved Vite major/minor, actual Node version plus CI/runtime evidence, app/library/mixed output consumers, optional UI-framework identity, and the first observed work signal. Do not infer unresolved or mixed versions.

Continue only when the selected leaf supports the source/target version and Node satisfies `(major == 20 and minor >= 19)`, `(major == 22 and minor >= 12)`, or `major > 22`; otherwise return a blocked record before reading a leaf. Treat prerelease or experimental features as unsupported unless the exact Vite version, opt-in authority, verification target, and rollback point are present.

## Conditional Table of Contents

Choose exactly one initial leaf closest to the requested outcome. Read another leaf only when the first leaf returns it.

| Initial signal or task | Initial leaf |
|---|---|
| Entry/dev/proxy, env/mode, asset URL/public/query, path resolution, forwarded diagnostics | [Vite client runtime](references/vite-client-runtime.md) |
| Dynamic import/chunk/import graph, Rollup/Rolldown config, plugin, measured dev/build performance | [Vite build and plugins](references/vite-build-plugins.md) |
| Subpath, cache headers, stale chunk, reload recovery | [Vite deployment](references/vite-deployment.md) |
| Explicit Vite 6→7 migration | [Vite 6 to 7 migration](references/vite-6-to-7-migration.md) |
| Explicit Vite 7→8 migration | [Vite 7 to 8 migration](references/vite-7-to-8-migration.md) |

## Cross-Skill Boundary

Keep Vite runtime/build/deployment ownership here. When the resolved UI framework is React 18/19 and the decision depends on a Suspense/lazy boundary, `@vitejs/plugin-react`/React Compiler, or user-visible stale-chunk recovery, return `next_skill: react-vite-guide` with the Vite evidence and caller identity. For another or unresolved framework, return the framework-owner need without inventing its semantics. Do not link directly into another skill package.

## Minimal Execution Loop

1. Run the selected leaf with the common preflight evidence.
2. Pass `handoff_evidence` unchanged to an exact internal `next_reference`.
3. Use `next_skill` only after the Vite owner decision is complete enough for integration.
4. Do not revisit an owner unless new evidence returns from the exact caller.
5. Stop on a handoff cycle, version/scope mismatch, missing evidence, failed verification, incompatible plugin/output, or mutation beyond authority.

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
- `diagnose`: finish with root cause, affected Vite owner, and verification evidence.
- `implement|migrate`: finish with authorized Vite changes and proportionate verification.

Return the classification, visited leaves, decision records, stopped/non-applied branches, cross-skill handoffs, and remaining unverified risks. A blocked or failed leaf cannot be reported as passed.
