---
name: react-vite-guide
description: >
  Use only when a browser-rendered React 18 or React 19 client and Vite 7 or
  Vite 8 must be decided together: React.lazy/Suspense with Vite dynamic
  imports and chunks, @vitejs/plugin-react or React Compiler integration, or
  Vite stale-chunk recovery with React async UI and accessibility. Also use
  for an explicit handoff from react-guide or vite-guide at one of these
  boundaries. Do not use for React-only component, Hook, state, or API work;
  Vite-only env, asset, build, plugin, deployment, or migration work;
  non-Vite React; non-React Vite; SSR/hydration/RSC/server functions; or
  isolated copy and styling work.
license: MIT
---

# React + Vite Integration Router

## Scope and Classification

Apply only when React 18/19 CSR ownership and Vite 7/8 client ownership are both resolved and one decision requires evidence from both. React-only work belongs to `react-guide`; Vite-only work belongs to `vite-guide`.

Record once: `request_mode` (`implement|review|migrate|diagnose`), mutation authority, requested outcome, resolved React and Vite versions, React 19.2 gate, actual Node/CI evidence for Vite work, app/library/mixed consumers, CSR boundary, `caller_skill` (`none|react-guide|vite-guide`), and the received handoff evidence. Do not infer unresolved or mixed versions.

For Vite work, require Node `(major == 20 and minor >= 19)`, `(major == 22 and minor >= 12)`, or `major > 22`. Stop before reading a leaf when the React/Vite/Node boundary is unsupported.

## Conditional Table of Contents

Choose exactly one integration leaf. Read another only when the first leaf returns it.

| Cross-boundary signal | Initial leaf |
|---|---|
| `React.lazy`/Suspense, dynamic import, chunk graph, CSS/modulepreload, same-interaction bundle claim | [React lazy and Vite build](references/react-lazy-vite-build.md) |
| `@vitejs/plugin-react`, inline Babel, React Compiler target/runtime/config, Vite 7→8 plugin arrival | [React Compiler and Vite plugin](references/react-compiler-vite-plugin.md) |
| `vite:preloadError`, removed chunks, reload recovery, React fallback/work preservation/focus/announcement | [Vite deployment and React recovery](references/vite-deployment-react-recovery.md) |

## Ownership and Handoff

- This skill decides only the seam between React and Vite; it does not re-own their internal decisions.
- Missing React owner evidence returns `next_skill: react-guide`.
- Missing Vite owner evidence returns `next_skill: vite-guide`.
- When invoked by another skill, finish with `return_to_caller` and preserve its fixed metric, boundary, and verification target.
- Do not link directly into another skill package or assume a missing skill is installed; return the named requirement when unavailable.

## Common Decision Record

```yaml
reference: <integration leaf filename>
caller_skill: <none | react-guide | vite-guide>
integration_branch: <lazy-build | compiler-plugin | deployment-recovery>
inputs_observed: [<React and Vite evidence>]
decision: <selection or not-applied>
actions_or_findings: [<authorized integration changes or findings>]
verification:
  status: passed | failed | not-run | blocked
  evidence: <same-condition result or reason>
stop_reason: <none or reason>
next_reference: <none or relative integration leaf path>
next_skill: <none | react-guide | vite-guide | return_to_caller>
handoff_evidence: [<evidence the next owner can reuse>]
```

## Complete or Stop

Finish only when both owners agree on the same boundary and the cross-boundary verification passes. Return the classification, visited integration leaf, decision record, stopped/non-applied branches, caller return, and remaining unverified risks. A blocked or failed owner cannot be reported as an integration pass.
