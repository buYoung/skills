# Caveman Style Reference (full mode, file-only)

This file specifies how the brief body is rewritten in caveman **full** mode and exactly which substrings stay in normal prose.
It applies to the saved Markdown only — chat / questions / status messages stay in full natural prose at all times.

The rules here are derived from the standalone `caveman` skill (full intensity level) and adapted for an executable work-instruction artifact rather than conversational replies.
Where caveman's defaults would risk technical ambiguity in a brief, this document tightens the rule.

**Caveman is a register transform, not a content reduction.** Every rule below applies to *how* prose is written (articles, fillers, phrasing, sentence shape).
None of them apply to *what* the brief contains.
Bullet count, enumerate depth, the number of distinct concerns surfaced per section, and the coverage of input items are identical to a normal-mode brief written from the same input.
If a caveman rule below would force you to drop a fact, a bullet, or a distinct concern to satisfy a register goal, the rule yields — correctness and completeness always beat compression.

---

## Two Hard Rules

1. **Brief file body uses caveman full mode.** Always.
   No mode switch inside the file.
2. **Chat / interaction surfaces are normal prose.** Always.
   No caveman in halt messages, interview questions, recommended answers, save reports, validator dialogs, edit confirmations.

Both rules are absolute.
There is no situation in which they invert.

---

## Full-Mode Conversion Rules (apply to brief body)

The rules below operate on **register only**.
They never reduce bullet count, never merge two distinct concerns into one bullet, and never drop facts.
If applying a rule would change *what is said*, skip the rule for that bullet.

Drop:

- Articles: `a`, `an`, `the`.
- Filler: `just`, `really`, `basically`, `actually`, `simply`, `literally`, `obviously`.
- Pleasantries / hedging: `please`, `kindly`, `I think`, `it seems that`, `arguably`, `probably`.
- Throat-clearing intros: `In order to …`, `It is worth noting that …`, `One thing to consider is …`.

Compress (register-only — never collapse meaning):

- **Truly-redundant phrasal verbs → single verb.** Allowed only when the long form adds no information beyond the short form.
  Whitelist examples: `make use of` → `use`, `take into account` → `consider`, `give consideration to` → `consider`, `carry out` → `do`.
- **Adjectival pile-ups → one adjective**, but only when the extras are synonymous.
  `large extensive comprehensive refactor` → `big refactor`.
  **Not** `large urgent customer-facing refactor` → `big refactor` (urgency and surface area are distinct facts).
- **Long synonyms → short synonyms.** `extensive` → `big`, `utilize` → `use`, `subsequently` → `then`, `prior to` → `before`.

**Forbidden (these are content compression, not register compression):**

- Replacing a verb that names a specific action with a generic one that drops the action's nature.
  `implement a solution for the cache invalidation race` → `fix race` is a content drop ("implement a solution for" is doing real work — saying *what* the work is).
  Keep the specific verb; only drop the truly redundant phrasal scaffolding around it.
- Merging two bullets that describe two distinct concerns.
  Caveman shortens each bullet, never combines them.
- Dropping qualifiers that pin scope, threshold, or condition (`only on cold start`, `≤ 5KB gzipped`, `iOS Safari 17+`).

Allow:

- Sentence fragments.
  `New ref each render. useMemo wrap.`
- Pattern: `[thing] [action] [reason]. [next step].`
- Arrows for chained causality if the chain is short and the referents are obvious: `inline obj prop → new ref → re-render`.

---

## Auto-Clarity Carve-Outs (stay in normal prose)

Inside the brief, these substrings are **never** caveman-rewritten:

| Region | Why preserved |
|---|---|
| Code blocks (fenced / inline) | Code is code. |
| File paths, directory paths, glob patterns | Routing artifacts. |
| Function names, identifiers, type names, env var names | Verbatim referents. |
| PR numbers (`PR #128`), issue numbers, commit hashes, URLs | Verbatim referents. |
| Error strings (quoted) | Must match logs / search verbatim. |
| Quantitative expressions (numbers, units, thresholds, versions, environment conditions) | They define acceptance and compatibility; `30Hz`, `≤ 5KB gzipped`, `iOS 17+`, and `only on cold start` must survive intact. |
| `# [<type>] <title>` line | Title format is contract. |
| `## ` and `### ` section headers | Validator parses these. |
| `## Work Type` value (`feat`, `refactor`, …) | Validator parses this. |
| `- N/A — <reason>` escape hatch token | The literal `N/A —` is a contract token; the reason after the em dash is caveman. |
| The `(proposed)` marker on entry-point bullets | Validator parses this. |
| Checklist marker `- [ ]` / `- [x]` | Validator parses this. |
| Entire `## Open Questions` section body | Questions are read by humans deciding what to clarify; full prose preserves nuance and avoids ambiguous fragments. |

Step-order-sensitive content stays in normal prose when fragment-style compression would obscure the order:

- `## Reproduction` numbered step list — write each step as a clear fragment but never collapse two steps' conjunctions into one bullet.
  If a sequence requires `then` / `next` / `before` / `after` to remain unambiguous, keep those words.
- `## Behavior Contract` invariants and verification methods — the contract is what the downstream agent diffs against.
  Ambiguity here costs more than tokens saved.
- `## Acceptance Criteria` checklist items — each item must be individually checkable.
  Fragments OK, ambiguous fragments not.
- `## Side Effect Checkpoints` checklist items — same as Acceptance Criteria.
- `## Constraints` API-shape / contract / version-pin constraints — these are legal-style statements; preserve precision.
- Any bullet carrying a numeric threshold, unit, version, frequency, platform version, or environment condition — keep the exact expression and the qualifier that scopes it.
- Any bullet describing an **irreversible** or **destructive** action (data deletion, schema migration, force-push, rate-limit raise) drops back to normal prose, mirroring caveman's standard Auto-Clarity rule for destructive ops.

When in doubt: write normal prose.
Caveman never wins over correctness.

---

## Per-Section Guidance

### `## Work Type`

The bare type token (`feat`, `refactor`, …).
Single line, no prose.
Caveman doesn't apply because there's nothing to compress.

### `## Current State (As-Is)`

Caveman OK.
Each bullet is one fragment describing today's behavior.

- Normal: `LoginForm validates email only on blur — users do not see the error until they try to submit.`
- Caveman: `` `LoginForm` email validate on blur only. User no see error till submit. ``

### `## Desired Outcome (To-Be)`

Caveman OK.
Mirror As-Is structure.

- Normal: `LoginForm shows the email error live while the user is typing.`
- Caveman: `` `LoginForm` show email error live as user type. ``

### `## Reproduction` (`fix` only)

Per-line caveman OK; **step order stays clear**.
Keep `then` / `next` / `before` / `after` when they carry the order.

- OK: `Steps: load /login on iOS Safari 17, type "foo@bar", submit. Result: "invalid credentials" toast. Expected: success.`
- Avoid: `Load login type submit fail toast.` (collapses 3 steps into one fragment, order lost.)

### `## Baseline Measurement` (`perf` only)

Numbers, units, methods stay verbatim.
Surrounding prose caveman.

- OK: `Current: TTFB p95 = 420ms over 1000 req, k6 local on M1 Pro, dev build. Target: p95 ≤ 250ms same setup.`

### `## Behavior Contract` (`refactor` only)

Locked behaviors and verification methods stay precise.
Caveman the prose around them, but never compress the invariant itself into ambiguity.

- OK: `` Locked: public methods of `UserService` (signature, return shape, thrown errors). Contract: `src/user/__tests__/UserService.test.ts` pass unchanged. Verification: full suite + 3 manual scenarios in `docs/qa/user-service.md`. ``
- Avoid: `Lock UserService.` (lost the contract.)

### `## Scope` → `### In Scope` / `### Out of Scope`

Caveman OK.
Out of Scope bullets must still name the *specific* thing — caveman compresses prose, not specificity.

- OK: `` Do not change `PaymentService` interface — other team depend on it. ``
- Bad (already bad pre-caveman): `Don't touch unrelated code.` Caveman doesn't fix lazy guardrails.

### `## Constraints`

Legal-style statements stay precise.
Caveman the connective tissue only.

- OK: `Bundle size delta ≤ 5KB gzipped.`
- OK: `Tauri v2 plugin only — v1 not on table.`
- Avoid: `Bundle small.` (lost the threshold.)

### `## Related Files / Entry Points`

Path / identifier / PR number stays verbatim.
The one-line purpose after the em dash is caveman.

- OK: `` `src/auth/LoginForm.tsx` — email validate logic live here. ``
- OK: `PR #128 — last year Tauri v1 attempt; ref prior constraints.`

### `## Side Effect Checkpoints`

Checklist items.
Each item individually checkable.
Fragments OK, ambiguous fragments not.

- OK: `- [ ] Login E2E pass (cypress/e2e/login.cy.ts).`
- OK: `- [ ] Existing session cookie format compatible — existing user no need re-login.`
- Avoid: `- [ ] Login still work.` (caveman of `Login still works.` is fine, but the original was already too vague.)

### `## Acceptance Criteria`

Same rule as Side Effect Checkpoints.
Measurability survives caveman; vagueness does not become OK.

- OK: `- [ ] Email error appear after 500ms debounce while user type.`
- OK: `- [ ] Lighthouse Performance ≥ 90 (mobile).`

### `## Open Questions`

**Normal prose only — caveman does not apply to this section.** Open Questions surface ambiguity that the downstream agent (or a human reviewer) must resolve.
Compressing the question text risks losing the nuance that makes the question answerable.
Write each bullet as a complete, naturally phrased question.
Identifiers, paths, and quoted strings still stay verbatim per the standard carve-outs.

- OK: `- Are the 5 default key combos finalized by product, or should the implementer propose a draft?`
- OK: `- Linux is unsupported — should the Settings section be hidden, or rendered disabled with an explanation?`
- Avoid: `- 5 default key combos finalized, or propose draft?` (caveman fragment; ambiguous antecedent.)
- Avoid: `- Linux unsupported: hide section, or show disabled?` (telegraphic; loses the "with an explanation" branch.)

---

## Worked Conversion (single bullet)

Normal prose:

> The `LoginForm` component currently validates the email field only on the `onBlur` event, which means the user does not actually see the validation error until they try to submit the form.

Caveman full:

> `LoginForm` validate email on blur only.
> User no see error till submit attempt.

Both carry the same technical claim.
The caveman version drops 17 words.

---

## Negative Examples (do not do)

- **Caveman in chat.** "Halt.
  Anchor missing.
  Send more." → wrong; chat uses normal prose.
  Correct: "I can't ground the brief from this input alone.
  Missing PROBLEM and TARGET — can you add a couple of lines?"
- **Caveman in section headers.** `## State Now` instead of `## Current State (As-Is)` → wrong; the validator parses headers.
- **Caveman of error strings.** `"invalid cred"` instead of `"invalid credentials"` → wrong; error strings must match the source verbatim.
- **Caveman of paths.** `` `LoginForm` `` instead of `` `src/auth/LoginForm.tsx` `` → wrong; the entry point loses its routing power.
- **Caveman of order-sensitive multi-step repro.** `migrate drop column backup` → wrong; collapses three steps into ambiguity.
  Keep the conjunctions.
- **Switching to `ultra` or `wenyan`.** Out of scope for this skill.
  Stay in `full`.
