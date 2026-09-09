# Example 04 — Briefset mode: checkout i18n migration

This example shows the full briefset flow on a checkout i18n migration
that splits cleanly into multiple execution contexts.

It demonstrates: (a) why the request is a briefset rather than a single
brief, (b) the Stage 4 decomposition walk (Korean), (c) the parent
brief, (d) the child briefs, and (e) the validator output.

**What this example produces:** a parent brief that *coordinates* and
three child briefs that *execute*. A coding agent never picks up the
parent to write code — the parent tells the orchestrator (or a human
lead) which child can start now and which has to wait. Each child is a
standalone work instruction that a coding agent picks up cold, exactly
the way it would pick up a single-mode brief.

---

## Input (Korean, pasted by a tech lead)

> 다음 스프린트에서 체크아웃 i18n을 정리해야 함.
> - 메시지 키 정리 (지금 일부는 영어 하드코딩)
> - 카트 카피 새로 받음 (마케팅에서 보내준 거)
> - 결제 시 입력 검증 에러 메시지가 영어로 떠서 한국어 카피로 교체
>
> 다 끝나면 결제 화면에서 영어 텍스트가 한 글자도 안 남아야 함.
> 메시지 파일은 `src/i18n/messages.ko.json` 한 곳에 모임.

---

## Stage 1 — Ambiguity Gate + briefset signal check

Anchor coverage:

- **PROBLEM** ✓ — checkout has English hardcoded text leaking through.
- **GOAL** ✓ — no English remaining in the checkout flow.
- **SCOPE** ✓ — checkout (cart, message keys, validation copy).
- **TARGET** ✓ — `src/i18n/messages.ko.json` and the checkout components
  that consume it.

Four anchors → CONTINUE.

Briefset signals (per `references/briefset.md`):

- ✅ Each subtask has its own completion criterion (keys cleaned / cart
  copy applied / validation copy translated).
- ✅ Each subtask touches a distinct primary entry point — message-key
  refactor (`src/i18n/`), cart UI components, validation pipeline.
- ✅ Work types mix: cleaning hardcoded strings is `refactor`, applying
  marketing copy is `feat`-ish content change, validation copy fix is
  `fix`.
- ✅ Shared conflict surface: `src/i18n/messages.ko.json` — every child
  edits this file.

Multiple signals strong → the author selects **briefset mode** and reports
the evidence before Stage 2; no output-format confirmation is needed.

---

## Stage 2 — Per-child work types (provisional)

| # | Slug | Provisional type | Reason |
|---|---|---|---|
| 01 | `message-keys` | `refactor` | structural cleanup, no behavior change |
| 02 | `cart-copy` | `feat` | new marketing copy, user-visible content change |
| 03 | `validation-copy` | `fix` | wrong-language error breaks UX expectation |

Mixed types are expected in briefset mode; do not flatten.

---

## Stage 3 — Codebase review (combined, tagged per child)

```
rg "i18n" -t ts src/checkout
rg "messages\.ko" -t ts
rg "validation" -g "src/checkout/**" -l
glob src/i18n/*.json
read src/i18n/messages.ko.json (head, structure)
read src/checkout/Cart.tsx
read src/checkout/PaymentForm.tsx (validation block)
```

Findings tagged per child:

- **01 message-keys** — `src/checkout/PaymentForm.tsx:42-78` has hardcoded
  English error labels; message-key namespacing inconsistent
  (`payment.err.*` vs `payment_err_*`).
- **02 cart-copy** — `src/checkout/Cart.tsx`, `src/checkout/CartItem.tsx`
  consume marketing-owned strings; new copy file pending from PM.
- **03 validation-copy** — `src/checkout/validation.ts` returns raw
  English strings from Zod schema; needs to return message keys instead.

All three children touch `src/i18n/messages.ko.json` → **conflict
hotspot**.

---

## Stage 4 — Briefset User Decision Table (Korean)

코드베이스와 입력으로 명백한 분해, 자식별 작업 유형, 실행 순서,
병렬화, 충돌 소유권은 작성 담당이 확정한다. 표에는 마케팅 원문의
수용 기준과 영어 fallback 일정처럼 사용자만 소유하는 결정만 남긴다.

| 순번 | 내용 | 수정 추천안 | 근거 |
|---|---|---|---|
| 1 | 자식 02의 마케팅 카피 수용 기준 | `docs/marketing/cart-copy-2026-04.md`와 cart copy diff가 0이어야 한다. | 마케팅 승인 원문은 사용자가 소유하며, 원문 일치가 해석보다 안전한 완료 기준이다. |
| 2 | 영어 fallback 처리 일정 | 비차단 질문으로 저장하고 EN locale rebuild 전까지 defer한다. | 현재 `ko` 범위는 안전하게 실행할 수 있지만, 별도 fallback 일정은 제품/릴리스 소유 결정이다. |

User: approve row 1, supply the approved file at `docs/marketing/cart-copy-2026-04.md`, and keep row 2 as a structured non-blocking question with the recommended default.

### Termination

차단 사용자 결정은 모두 확정됐다. 코드베이스 프로브는 분해,
작업 유형, 순서, 병렬화, 충돌 규칙을 해결했고, 영어 fallback만
안전한 기본값과 재확인 시점을 가진 parent `Open Questions`로 남긴다.
Stage 5로 이동.

---

## Stage 5 — Save

Files written, in order (children first so the parent can reference them):

```
docs/briefs/2026-04-30-refactor-checkout-i18n-01-message-keys.md
docs/briefs/2026-04-30-feat-checkout-i18n-02-cart-copy.md
docs/briefs/2026-04-30-fix-checkout-i18n-03-validation-copy.md
docs/briefs/2026-04-30-briefset-checkout-i18n.md
```

---

## Parent brief (saved file)

```markdown
# Brief Set: Checkout i18n cleanup

## Purpose
- Eliminate hardcoded English from the checkout flow so Korean users see
  Korean copy end-to-end.
- Replace cart copy with PM-supplied marketing-approved Korean copy in
  the same pass.

## Child Briefs
- [ ] `docs/briefs/2026-04-30-refactor-checkout-i18n-01-message-keys.md` — Normalize checkout message-key namespacing; exists because hardcoded strings and inconsistent key naming block downstream copy work.
- [ ] `docs/briefs/2026-04-30-feat-checkout-i18n-02-cart-copy.md` — Apply PM-supplied cart copy; exists because marketing-owned content change is independent of code refactor.
- [ ] `docs/briefs/2026-04-30-fix-checkout-i18n-03-validation-copy.md` — Translate Zod-driven validation error strings; exists because wrong-language error breaks the no-English goal and depends on stable message keys from 01.

## Execution Order
- Wave 1 — `docs/briefs/2026-04-30-refactor-checkout-i18n-01-message-keys.md`: Start: current keys and rendered-copy contract are confirmed; Deliverable: normalized namespace manifest with preserved values and proof; Location: `docs/briefs/handoffs/checkout-i18n/message-keys.md` (proposed); Done: child 01 stage checks and Acceptance Criteria pass; Handoff: children 02 and 03 read the same manifest before editing.
- Wave 2 — `docs/briefs/2026-04-30-feat-checkout-i18n-02-cart-copy.md`: Start: the namespace manifest's `cart.*` fields are verified; Deliverable: approved cart-copy evidence; Location: `docs/briefs/handoffs/checkout-i18n/cart-copy.md` (proposed); Done: child 02 stage checks and Acceptance Criteria pass; Handoff: global verification receives the cart-copy diff evidence.
- Wave 2 — `docs/briefs/2026-04-30-fix-checkout-i18n-03-validation-copy.md`: Start: the namespace manifest's `payment.err.*` fields are verified; Deliverable: validation-copy evidence; Location: `docs/briefs/handoffs/checkout-i18n/validation-copy.md` (proposed); Done: child 03 stage checks and Acceptance Criteria pass; Handoff: global verification receives the validation-copy evidence.

## Dependencies
- Predecessor: `docs/briefs/2026-04-30-refactor-checkout-i18n-01-message-keys.md`; Deliverable path: `docs/briefs/handoffs/checkout-i18n/message-keys.md` (proposed); Format: Markdown headings `Namespaces`, `Placeholders`, and `Evidence` with separate `cart.*` and `payment.err.*` entries preserving current rendered values; Successor: `docs/briefs/2026-04-30-feat-checkout-i18n-02-cart-copy.md`; Starts when: the manifest lists resolvable `cart.*` placeholders; Verify: `inspect Namespaces, Placeholders, Evidence, and cart.* entries in the handoff`; Inputs: the complete `docs/briefs/handoffs/checkout-i18n/message-keys.md` file; Expected: all three headings exist and at least one resolvable `cart.*` entry names its consumer.
- Predecessor: `docs/briefs/2026-04-30-refactor-checkout-i18n-01-message-keys.md`; Deliverable path: `docs/briefs/handoffs/checkout-i18n/message-keys.md` (proposed); Format: Markdown headings `Namespaces`, `Placeholders`, and `Evidence` with separate `cart.*` and `payment.err.*` entries preserving current rendered values; Successor: `docs/briefs/2026-04-30-fix-checkout-i18n-03-validation-copy.md`; Starts when: the manifest lists resolvable `payment.err.*` placeholders; Verify: `inspect Namespaces, Placeholders, Evidence, and payment.err.* entries in the handoff`; Inputs: the complete `docs/briefs/handoffs/checkout-i18n/message-keys.md` file; Expected: all three headings exist and at least one resolvable `payment.err.*` entry names its consumer.

## Parallelization
- Can run together: `docs/briefs/2026-04-30-feat-checkout-i18n-02-cart-copy.md` and `docs/briefs/2026-04-30-fix-checkout-i18n-03-validation-copy.md` — their key namespaces (`cart.*` vs `payment.err.*`) do not overlap. Join when: both child deliverables are rebased onto child 01 and their checks pass together.
- Must not overlap: `docs/briefs/2026-04-30-refactor-checkout-i18n-01-message-keys.md` and `docs/briefs/2026-04-30-feat-checkout-i18n-02-cart-copy.md` — child 02 waits for child 01's namespace manifest. Join when: child 01's handoff is verified before child 02 edits `cart.*` values.
- Must not overlap: `docs/briefs/2026-04-30-refactor-checkout-i18n-01-message-keys.md` and `docs/briefs/2026-04-30-fix-checkout-i18n-03-validation-copy.md` — child 03 waits for child 01's namespace manifest. Join when: child 01's handoff is verified before child 03 edits `payment.err.*` values.

## Conflict Hotspots
- `src/i18n/messages.ko.json` — Children: `docs/briefs/2026-04-30-refactor-checkout-i18n-01-message-keys.md`, `docs/briefs/2026-04-30-feat-checkout-i18n-02-cart-copy.md`; Access: serialized; Owner: `docs/briefs/2026-04-30-refactor-checkout-i18n-01-message-keys.md`; Rule: child 01 lands namespace structure before child 02 changes only `cart.*` values.
- `src/i18n/messages.ko.json` — Children: `docs/briefs/2026-04-30-refactor-checkout-i18n-01-message-keys.md`, `docs/briefs/2026-04-30-fix-checkout-i18n-03-validation-copy.md`; Access: serialized; Owner: `docs/briefs/2026-04-30-refactor-checkout-i18n-01-message-keys.md`; Rule: child 01 lands namespace structure before child 03 changes only `payment.err.*` values.
- `src/i18n/messages.ko.json` — Children: `docs/briefs/2026-04-30-feat-checkout-i18n-02-cart-copy.md`, `docs/briefs/2026-04-30-fix-checkout-i18n-03-validation-copy.md`; Access: parallel-safe; Rule: child 02 owns `cart.*`, child 03 owns `payment.err.*`, neither reorders unrelated keys, and both rebase before the join.

## Shared Constraints
- Korean (`ko`) is the only locale touched in this set.
- [deferred] English fallback strings and the `en` locale rebuild are excluded from all children until separately approved.
- No new i18n tooling — stay on the existing `react-i18next` setup.

## Global Acceptance Criteria
- [ ] Inspect rendered Cart, CartItem, and PaymentForm on the Korean locale, including populated/empty cart, required-field errors, and every validation error category returned by the reviewed schema; no user-visible English remains in these states, including attributes and resolved translation values.
- [ ] Record a non-empty checkout source-file inventory for the scans below. Treat their results as checks of the stated source patterns only; no-match results alone do not prove rendered-language coverage.
- [ ] `rg -n '>[[:space:]]*[A-Za-z][^<{]*<' src/checkout` returns exit 1 after scanning all checkout JSX files — no matches of this literal JSX-text pattern remain.
- [ ] `rg -n 'message:[[:space:]]*"[A-Za-z]' src/checkout` returns exit 1 after scanning validation sources — no matches of this literal validation-message pattern remain.
- [ ] `rg "[가-힣]" src/checkout` returns exit 1 after scanning all checkout sources — Korean copy resolves from `src/i18n/messages.ko.json` rather than hardcoded component text.
- [ ] All three child briefs' Acceptance Criteria are checked.
- [ ] Cart copy diff against `docs/marketing/cart-copy-2026-04.md` is 0 (verbatim match).

## Open Questions
- [non-blocking] Should English fallback strings be added in a follow-up briefset or wait for the EN locale rebuild? — Default: defer them to the EN locale rebuild; Reconfirm before: checkout i18n release scope is finalized.
```

---

## Child brief 01 — message-keys (saved file)

```markdown
# [refactor] Normalize checkout message-key namespacing

## Work Type
refactor

## Current State (As-Is)
- [confirmed] `src/checkout/PaymentForm.tsx:42-78` hardcodes English error labels — Evidence: `PaymentForm` validation-rendering branch.
- [confirmed] Checkout uses both `payment.err.*` and `payment_err_*` key forms — Evidence: repository search across checkout consumers.
- [inferred] The duplicate forms can cause lookup drift during parallel copy work — Confirm by: map both forms to consumers before normalization.

## Behavior Contract
- Locked: every user-visible string already shown in the checkout flow continues to render the same text, including existing English text until its copy-owning child changes it. No text content change is permitted in this child — only the resolution path moves from inline literal to `t('namespace.key')`.
- Locked: error-throwing call sites in `src/checkout/PaymentForm.tsx` keep emitting the same logical error categories (no error-code change downstream).
- Contract artifacts: `src/checkout/__tests__/PaymentForm.test.tsx` (rendered-text assertions) and the existing Cypress `cypress/e2e/checkout.cy.ts` happy-path scenarios.
- Verification: full unit suite + the checkout Cypress scenarios stay green; manual diff of rendered text on the cart and payment screens shows zero copy change.

## Desired Outcome (To-Be)
- Migrated checkout JSX literals and existing key consumers resolve through `t('namespace.key')` while preserving current rendered values; schema-returned validation messages remain child 03 work.
- Single namespacing convention adopted (`payment.err.*`, `cart.*`) across checkout consumers.

## Scope
### In Scope
- `src/checkout/**/*.tsx` — migrate direct JSX literals and existing key lookups to `t(...)` with preserved values; leave schema-returned message translation to child 03.
- `src/i18n/messages.ko.json` — collapse duplicate keys to the dot-separated form; add missing keys carrying the current rendered values for 02 and 03 to update.
- `src/i18n/index.ts` — re-export the cleaned namespace.
### Out of Scope
- [hard] Cart user-visible copy text (handled by `02-cart-copy`).
- [hard] Validation error copy text (handled by `03-validation-copy`).
- [deferred] English (`en`) locale file and fallback rebuild — separate future briefset.
- [deferred] A hardcoded-string ESLint rule — separate tooling plan; not required for namespace migration.

## Constraints
- Touch only the Korean (`ko`) locale and keep the existing `react-i18next` setup.
- Preserve current rendered values when replacing inline literals with keys; `Placeholders` means named downstream-owned keys with those current values, never empty substitutions.
- Child 02 owns `cart.*` copy and child 03 owns `payment.err.*` copy after this child lands; do not change their text here.

## Related Files / Entry Points
- `src/checkout/PaymentForm.tsx` — inline English error labels lines 42-78.
- `src/i18n/messages.ko.json` — duplicate-key collapse target.
- `src/i18n/index.ts` — barrel re-export.
- `src/checkout/Cart.tsx`, `src/checkout/CartItem.tsx` — consumers needing key swap.

## Execution Plan
### Stage 1 — Lock the rendered-copy contract
- Starts when: Existing checkout copy, key consumers, and child ownership boundaries are confirmed.
- Work: Pin the current rendered-copy contract and map legacy key forms to consumers before edits.
- No-op when: `cart.*` and `payment.err.*` are already canonical, all checkout consumers resolve them, and the current rendered-copy checks pass without edits.
- No-op handoff: Children 02 and 03 receive unchanged-state evidence at `docs/briefs/handoffs/checkout-i18n/message-keys.md` and continue from the verified placeholders.
- Deliverable: A verified behavior baseline and namespace migration map at `docs/briefs/handoffs/checkout-i18n/message-keys.md`; Format: `Namespaces`, `Placeholders`, and `Evidence` headings.
- Verify: `rg 'payment_err_|payment\.err\.|cart\.' src/checkout src/i18n/messages.ko.json`; Inputs: all checkout consumers plus the complete Korean message file; Expected: every legacy key is classified and every canonical namespace has a recorded consumer or placeholder.
- Ends when:
  - [ ] Every legacy checkout key form maps to a consumer or an explicit removal target.
- Handoff: Stage 2 receives the behavior baseline and namespace migration map from `docs/briefs/handoffs/checkout-i18n/message-keys.md`.
- Replan when: A legacy key is consumed outside checkout or preserving a value requires changing copy owned by child 02 or 03.

### Stage 2 — Normalize the shared key surface
- Starts when: Stage 1 provides the migration map and behavior baseline.
- Work: Produce stable `cart.*` and `payment.err.*` namespaces without changing user-visible copy.
- Deliverable: Normalized namespaces and placeholders recorded at `docs/briefs/handoffs/checkout-i18n/message-keys.md` for Wave 2 children.
- Verify: `rg 'payment_err_' src/checkout src/i18n/messages.ko.json`; Inputs: all migrated checkout consumers and the complete Korean message file; Expected: exit 1 with a non-empty target file set, while canonical `cart.*` and `payment.err.*` keys remain resolvable.
- Ends when:
  - [ ] Checkout consumers resolve the normalized keys and rendered copy remains unchanged.
- Handoff: Parent Wave 2 receives the stable namespaces, placeholders, and verification evidence from `docs/briefs/handoffs/checkout-i18n/message-keys.md`.
- Replan when: Normalization requires a copy change or a cross-locale contract change.

## Side Effect Checkpoints
- [ ] All existing checkout E2E tests still pass without copy assertions failing.
- [ ] `t('payment.err.*')` keys still resolve after underscore variants are removed.
- [ ] No untranslated key warnings in the dev console after the swap.

## Acceptance Criteria
- [ ] Compare every literal and lookup in the migration map with its resulting key and rendered value; every mapped item is externalized without copy changes. Source-pattern scans are supporting evidence only.
- [ ] No underscore-form message keys (`*_err_*`) remain in `src/i18n/messages.ko.json`.
- [ ] Placeholder keys for `cart.*` and `payment.err.*` exist (each key preserves its current rendered text; empty replacement values are not allowed) so children 02 and 03 can fill them without edits to 01's surface.

## Open Questions
- None — no user-owned decision remains; lint enforcement is explicitly deferred as separate tooling work.
```

## Child brief 02 — cart-copy (saved file)

```markdown
# [feat] Apply approved Korean cart copy

## Work Type
feat

## Current State (As-Is)
- [confirmed] `Cart.tsx` and `CartItem.tsx` render marketing-owned text — Evidence: the Stage 3 checkout consumer review.
- [confirmed] The user selected `docs/marketing/cart-copy-2026-04.md` as the copy authority — Evidence: Stage 4 row 1; availability and contents are checked before editing.

## Desired Outcome (To-Be)
- Cart and cart-item copy matches the approved Korean source verbatim.
- Existing cart behavior, message keys, and interpolation values remain compatible.

## Scope
### In Scope
- Update the `cart.*` values in `src/i18n/messages.ko.json` and their cart display bindings.
- Record the source-to-rendered-copy comparison for global verification.
### Out of Scope
- [hard] Changing `payment.err.*` copy or validation behavior — child 03 owns that work.
- [hard] Renaming the namespaces established by child 01.
- [deferred] English fallback strings and the `en` locale rebuild.

## Constraints
- Touch only Korean (`ko`) copy and use the existing `react-i18next` setup.
- Child 02 owns `cart.*`; do not reorder unrelated message keys or edit `src/i18n/index.ts` after child 01 lands.
- Preserve the approved wording, punctuation, interpolation names, and cart actions. Ask before choosing among conflicting source versions.

## Related Files / Entry Points
- `src/checkout/Cart.tsx`, `src/checkout/CartItem.tsx` — inspect the cart copy bindings and rendered states.
- `src/i18n/messages.ko.json` — edit only the approved `cart.*` values.
- `docs/marketing/cart-copy-2026-04.md` — approved source for verbatim comparison.
- `docs/briefs/handoffs/checkout-i18n/message-keys.md` (proposed) — child 01 supplies the namespace contract before this child starts.

## Execution Plan
### Stage 1 — Confirm source and current cart copy
- Starts when: Child 01 has completed its checks and `docs/briefs/handoffs/checkout-i18n/message-keys.md` provides the `cart.*` keys, preserved values, and consumer map; the approved marketing source is available.
- Work: Map the approved copy to cart states and confirm whether any edit is still needed.
- No-op when: The complete rendered cart and cart-item copy already matches the approved source and existing cart behavior checks pass.
- No-op handoff: Global verification receives the unchanged-state comparison at `docs/briefs/handoffs/checkout-i18n/cart-copy.md`; skip Stage 2 and continue the parent join.
- Deliverable: A source-to-key comparison at `docs/briefs/handoffs/checkout-i18n/cart-copy.md`; Format: `Source`, `Mappings`, and `Evidence` headings with each source item, key, rendered value, and observation.
- Verify: `inspect approved source, namespace handoff, and populated/empty cart states`; Inputs: complete marketing source, message-keys handoff, Cart, and CartItem; Expected: every approved source item has a key and rendered state, with mismatches recorded explicitly.
- Ends when:
  - [ ] The complete copy mapping distinguishes unchanged entries from entries requiring edits.
- Handoff: Stage 2 receives the mapping and required changes, or global verification receives the no-change evidence at `docs/briefs/handoffs/checkout-i18n/cart-copy.md`.
- Replan when: Source is missing or conflicting, or a copy change requires new behavior; stop dependent edits and ask the plan author to resolve source/scope before continuing.

### Stage 2 — Apply and verify cart wording
- Starts when: Stage 1 supplies a confirmed source mapping and identifies remaining copy edits.
- Work: Apply the approved wording while preserving interpolation and cart behavior.
- Deliverable: Integrated cart copy with final comparison evidence at `docs/briefs/handoffs/checkout-i18n/cart-copy.md`.
- Verify: `compare approved source items with rendered populated/empty Cart and CartItem states`; Inputs: complete source mapping and changed cart screens; Expected: every mapped wording matches verbatim and existing cart actions still work.
- Ends when:
  - [ ] All mapped values match and interpolation renders without missing-key warnings.
- Handoff: Global verification receives `docs/briefs/handoffs/checkout-i18n/cart-copy.md` after child 01 integration and the child 03 join.
- Replan when: A mismatch cannot be fixed inside cart-owned values/bindings; stop and return to the parent for bounded correction, re-verification, and relationship review.

## Side Effect Checkpoints
- [ ] Existing cart actions and empty/populated state checks still pass.
- [ ] Interpolation names remain compatible with the reviewed consumers.
- [ ] No child 03-owned validation copy or unrelated message key changed.

## Acceptance Criteria
- [ ] Every approved source item matches rendered cart copy verbatim; the comparison evidence records the complete population.
- [ ] Cart and CartItem show Korean copy in the mapped states without missing-key warnings or changed cart behavior.
- [ ] The parent join can read the completed `docs/briefs/handoffs/checkout-i18n/cart-copy.md` evidence.

## Open Questions
- None — the user selected the copy authority; source availability and any conflicting revisions are explicit start/replan boundaries.
```

## Child brief 03 — validation-copy (saved file)

```markdown
# [fix] Render Korean checkout validation messages

## Work Type
fix

## Current State (As-Is)
- [confirmed] Checkout validation returns raw English messages from its Zod schema — Evidence: Stage 3 inspection of `src/checkout/validation.ts`.
- [inferred] Returning the established message keys and resolving their Korean values can close the language gap without changing validation decisions — Confirm by: pin each existing validation category and its display binding in Stage 1.

## Reproduction
- Steps: open the Korean checkout PaymentForm; submit missing required values, then exercise each invalid-input category in the existing validation schema.
- Observed: English validation messages are reported by the input and visible in the reviewed schema; record the actual rendered messages in Stage 1.
- Expected: each category displays Korean wording while the same input remains valid or invalid as before.
- Environment: the project's existing checkout development/test environment with locale set to `ko`; record the tested build and cases before edits.
- Frequency: not measured yet — record the outcome of each existing validation case during reproduction rather than inventing a rate.

## Desired Outcome (To-Be)
- Checkout validation messages resolve the established `payment.err.*` Korean values.
- Error categories, validation decisions, field associations, and submission behavior remain unchanged.

## Scope
### In Scope
- Resolve validation messages through the existing Korean message catalog and PaymentForm bindings.
- Record category-by-category reproduction and correction evidence.
### Out of Scope
- [hard] Cart copy and `cart.*` values — child 02 owns them.
- [hard] Changing validation rules or externally consumed error categories without a new user decision.
- [deferred] English fallback strings and the `en` locale rebuild.

## Constraints
- Touch only Korean (`ko`) copy and use the existing `react-i18next` setup.
- Child 03 owns `payment.err.*`; do not reorder unrelated keys or edit `src/i18n/index.ts` after child 01 lands.
- Preserve the validation return shape consumed outside checkout. If the required message-key mapping breaks it, stop and return to the parent before changing the contract.

## Related Files / Entry Points
- `src/checkout/validation.ts` — pin the current categories and message-producing branches.
- `src/checkout/PaymentForm.tsx` — inspect how each category reaches the rendered field error.
- `src/i18n/messages.ko.json` — edit the `payment.err.*` values only.
- `src/checkout/__tests__/PaymentForm.test.tsx`, `cypress/e2e/checkout.cy.ts` — inspect existing validation and submission checks.
- `docs/briefs/handoffs/checkout-i18n/message-keys.md` (proposed) — child 01 supplies the namespace contract before this child starts.

## Execution Plan
### Stage 1 — Pin validation categories and language failures
- Starts when: Child 01 has completed its checks and `docs/briefs/handoffs/checkout-i18n/message-keys.md` provides the `payment.err.*` keys, preserved values, and consumer map.
- Work: Reproduce each current validation category and map it to its rendered message and expected Korean value.
- No-op when: Every reviewed category already renders Korean copy and existing validation/submission checks pass without edits.
- No-op handoff: Global verification receives unchanged-state evidence at `docs/briefs/handoffs/checkout-i18n/validation-copy.md`; skip Stage 2 and continue the parent join.
- Deliverable: A category/message baseline at `docs/briefs/handoffs/checkout-i18n/validation-copy.md`; Format: `Cases`, `Messages`, and `Evidence` headings with input category, key, expected Korean text, and observed result.
- Verify: `inspect schema categories and exercise their existing PaymentForm validation states in ko`; Inputs: all schema error categories and the namespace handoff; Expected: every category has a recorded rendered result and unchanged validation decision.
- Ends when:
  - [ ] Each category has a pinned result and a known display binding before correction.
- Handoff: Stage 2 receives the baseline and remaining language failures, or global verification receives no-change evidence at `docs/briefs/handoffs/checkout-i18n/validation-copy.md`.
- Replan when: The evidence is incomplete or a category needs a user-owned wording/contract decision; stop dependent edits and return to the parent for clarification and bounded correction/re-verification before recalculating the route.

### Stage 2 — Correct message resolution and verify behavior
- Starts when: Stage 1 supplies the category baseline, agreed wording, and remaining language failures.
- Work: Resolve the Korean messages without changing validation decisions or external error contracts.
- Deliverable: Corrected message bindings with before/after evidence at `docs/briefs/handoffs/checkout-i18n/validation-copy.md`.
- Verify: `replay every recorded validation case and existing successful checkout scenario in ko`; Inputs: complete category baseline and updated PaymentForm/messages; Expected: every field error is Korean, each validation decision/category is preserved, and successful submission still works.
- Ends when:
  - [ ] Every pinned category renders the expected Korean message without changing its validity decision.
- Handoff: Global verification receives `docs/briefs/handoffs/checkout-i18n/validation-copy.md` after child 01 integration and the child 02 join.
- Replan when: Correct rendering requires an external return-shape or validation-rule change; stop and return to the parent for a user decision, bounded correction, re-verification, and handoff recalculation.

## Side Effect Checkpoints
- [ ] Valid checkout still submits successfully using the existing scenario.
- [ ] Error categories, field associations, and externally consumed return shapes stay compatible.
- [ ] No cart-owned values or unrelated message keys changed.

## Acceptance Criteria
- [ ] Every recorded validation category displays its expected Korean wording with no untranslated key.
- [ ] Existing validation decisions and successful checkout behavior remain unchanged.
- [ ] The complete before/after record at `docs/briefs/handoffs/checkout-i18n/validation-copy.md` is available for the parent join.

## Open Questions
- None — source and contract uncertainties are explicit investigation/replan boundaries; any new user-owned choice is asked before its dependent edit.
```


---

## Picked Up Cold — How Coding Agents Map onto Waves

The parent's `Execution Order` translates directly to coding-agent
scheduling:

- **Wave 1 (sequential).** A single coding agent picks up child 01
  (`refactor-...01-message-keys`). Its `Behavior Contract` lets the agent
  verify "no rendered text changed" mechanically (existing tests + manual
  diff on the cart and payment screens). Wave 1 lands behind a green test
  suite before Wave 2 starts.
- **Wave 2 (parallel).** Two coding agents start at the same time:
  - Agent A picks up child 02 (`feat-...02-cart-copy`) and works only
    inside the `cart.*` key namespace.
  - Agent B picks up child 03 (`fix-...03-validation-copy`) and works
    only inside the `payment.err.*` key namespace.
  - Both touch `src/i18n/messages.ko.json`, but child 02 owns `cart.*`
    and child 03 owns `payment.err.*`; neither edits `src/i18n/index.ts`
    after child 01 establishes exports. The parent's pairwise hotspot
    rule makes that parallel boundary and rebase join explicit.

A coding agent picking up child 01 cold should:

1. Open `src/checkout/PaymentForm.tsx` lines 42–78 and confirm the
   inline English error labels listed in `Current State (As-Is)`.
2. Open `src/i18n/messages.ko.json`, identify the duplicate
   `payment_err_*` keys, and plan the collapse to `payment.err.*`.
3. Add keys initialized with the current rendered values for `cart.*` and `payment.err.*` so
   children 02 and 03 have a stable surface to fill (per child 01's
   `Acceptance Criteria` #3).
4. Run the unit + Cypress suites continuously to keep the `Behavior
   Contract` verifiable.

The agent does **not** edit cart copy text (per `Out of Scope` — that's
child 02), does not translate Zod validation strings (per `Out of
Scope` — that's child 03), and does not touch the English locale (per
`Shared Constraints`).

---

## Stage 6 — Validator output

`<skill-dir>` is the installed skill package directory (the directory
containing `SKILL.md`) — the validator ships with the skill, not with
the user's repository.

```bash
$ python3 <skill-dir>/scripts/validate_briefset.py \
    docs/briefs/2026-04-30-briefset-checkout-i18n.md
Validating briefset: docs/briefs/2026-04-30-briefset-checkout-i18n.md

Validating 3 child brief(s)...

  ✓ Parent filename format OK (set-slug='checkout-i18n').
  ✓ Title line OK (title='Checkout i18n cleanup').
  ✓ Section `## Purpose` present.
  ✓ Section `## Child Briefs` present.
  ✓ Section `## Execution Order` present.
  ✓ Section `## Dependencies` present.
  ✓ Section `## Parallelization` present.
  ✓ Section `## Conflict Hotspots` present.
  ✓ Section `## Shared Constraints` present.
  ✓ Section `## Global Acceptance Criteria` present.
  ✓ Section `## Open Questions` present.
  ✓ `## Child Briefs` uses `- [ ]` checklist format.
  ✓ `## Global Acceptance Criteria` uses `- [ ]` checklist format.
  ✓ `## Execution Order` references every child exactly once with a concrete deliverable location.
  ✓ `## Dependencies` defines 2 addressable handoff edge(s) with format and verification signals.
  ✓ child `2026-04-30-refactor-checkout-i18n-01-message-keys.md`: structural checks OK.
  ✓ child `2026-04-30-feat-checkout-i18n-02-cart-copy.md`: structural checks OK.
  ✓ child `2026-04-30-fix-checkout-i18n-03-validation-copy.md`: structural checks OK.
  ✓ Every dependency deliverable path is repeated in its producer and successor child execution plan.

PASS - structural checks OK (0 warning(s)).
```

One `validate_briefset.py` invocation covers the whole set — it re-runs
`validate_brief.py`'s structural checks transitively on every referenced
child, so the three `child ...: structural checks OK.` lines above *are*
the per-child validation.

**Stage 5.7 note** — briefset mode is itself an auto-ON trigger for
cold-pickup verification: the parent and every child each run their own
sub-agent pass (per-child signal gating is intentionally disabled in
briefset mode). With all four files terminating on a clean first pass,
the Stage 6 banner reports the collapsed form
`cold-pickup: 1/1 parent + 3/3 children verdict:clean (no ask-backs, no missing concerns)`.
See `references/cold-pickup.md` for the report schema and termination
triggers, and example 05 for a full single-file pass.

---

## What this example shows

- **Briefset trigger is the *signal mix*, not the input length.** The
  Korean input is short, but mixed types + shared hotspot + ordered
  dependency are enough.
- **Per-child work types stay distinct.** Flattening this to a single
  `feat` would lose the `refactor`'s behavior-preservation discipline
  and the `fix`'s reproduction-first framing.
- **Conflict hotspots are separate from dependencies.** 02 and 03 have
  no functional dependency on each other but both edit a shared file —
  the parent calls that out so a downstream agent does not run them
  in unmanaged parallel.
- **Status lives only on the parent.** Child briefs do not carry their
  own checkbox.
- **Children are independently executable.** A downstream agent picking
  up 02 alone has every piece of context it needs from the child brief
  itself.
