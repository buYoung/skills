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

Multiple signals strong → **briefset mode**. Surface the intent before
Stage 2: "이 작업은 단일 브리프보다 briefset이 맞을 것 같아 — 셋으로
쪼갰을 때 명확하게 갈리거든."

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

User: approve row 1 and keep row 2 as a structured non-blocking question with the recommended default.

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
- Eliminate hardcoded English from checkout flow so Korean users see Korean copy end-to-end.
- Replace cart copy with PM-supplied marketing-approved Korean copy in same pass.

## Child Briefs
- [ ] `docs/briefs/2026-04-30-refactor-checkout-i18n-01-message-keys.md` — Normalize checkout message-key namespacing; exists because hardcoded strings and inconsistent key naming block downstream copy work.
- [ ] `docs/briefs/2026-04-30-feat-checkout-i18n-02-cart-copy.md` — Apply PM-supplied cart copy; exists because marketing-owned content change is independent of code refactor.
- [ ] `docs/briefs/2026-04-30-fix-checkout-i18n-03-validation-copy.md` — Translate Zod-driven validation error strings; exists because wrong-language error break the no-English goal and depend on stable message keys from 01.

## Execution Order
- Wave 1 — `docs/briefs/2026-04-30-refactor-checkout-i18n-01-message-keys.md`: Start: current keys and rendered-copy contract confirmed; Deliverable: normalized namespace manifest with placeholders and proof; Location: `docs/briefs/handoffs/checkout-i18n/message-keys.md` (proposed); Done: child 01 stage checks and Acceptance Criteria pass; Handoff: children 02 and 03 read same manifest before edits.
- Wave 2 — `docs/briefs/2026-04-30-feat-checkout-i18n-02-cart-copy.md`: Start: namespace manifest `cart.*` fields verified; Deliverable: approved cart-copy evidence; Location: `docs/briefs/handoffs/checkout-i18n/cart-copy.md` (proposed); Done: child 02 stage checks and Acceptance Criteria pass; Handoff: global verification receives cart-copy diff evidence.
- Wave 2 — `docs/briefs/2026-04-30-fix-checkout-i18n-03-validation-copy.md`: Start: namespace manifest `payment.err.*` fields verified; Deliverable: validation-copy evidence; Location: `docs/briefs/handoffs/checkout-i18n/validation-copy.md` (proposed); Done: child 03 stage checks and Acceptance Criteria pass; Handoff: global verification receives validation-copy evidence.

## Dependencies
- Predecessor: `docs/briefs/2026-04-30-refactor-checkout-i18n-01-message-keys.md`; Deliverable path: `docs/briefs/handoffs/checkout-i18n/message-keys.md` (proposed); Format: Markdown headings `Namespaces`, `Placeholders`, and `Evidence` with separate `cart.*` and `payment.err.*` entries; Successor: `docs/briefs/2026-04-30-feat-checkout-i18n-02-cart-copy.md`; Starts when: manifest lists resolvable `cart.*` placeholders; Verify: `inspect Namespaces, Placeholders, Evidence, and cart.* entries in the handoff`; Inputs: complete `docs/briefs/handoffs/checkout-i18n/message-keys.md` file; Expected: all three headings exist and at least one resolvable `cart.*` entry names its consumer.
- Predecessor: `docs/briefs/2026-04-30-refactor-checkout-i18n-01-message-keys.md`; Deliverable path: `docs/briefs/handoffs/checkout-i18n/message-keys.md` (proposed); Format: Markdown headings `Namespaces`, `Placeholders`, and `Evidence` with separate `cart.*` and `payment.err.*` entries; Successor: `docs/briefs/2026-04-30-fix-checkout-i18n-03-validation-copy.md`; Starts when: manifest lists resolvable `payment.err.*` placeholders; Verify: `inspect Namespaces, Placeholders, Evidence, and payment.err.* entries in the handoff`; Inputs: complete `docs/briefs/handoffs/checkout-i18n/message-keys.md` file; Expected: all three headings exist and at least one resolvable `payment.err.*` entry names its consumer.

## Parallelization
- Can run together: `docs/briefs/2026-04-30-feat-checkout-i18n-02-cart-copy.md` and `docs/briefs/2026-04-30-fix-checkout-i18n-03-validation-copy.md` — key namespaces do not overlap. Join when: both deliverables rebased onto child 01 and checks pass together.
- Must not overlap: `docs/briefs/2026-04-30-refactor-checkout-i18n-01-message-keys.md` and `docs/briefs/2026-04-30-feat-checkout-i18n-02-cart-copy.md` — child 02 waits for child 01 manifest. Join when: child 01 handoff verified before child 02 edits `cart.*` values.
- Must not overlap: `docs/briefs/2026-04-30-refactor-checkout-i18n-01-message-keys.md` and `docs/briefs/2026-04-30-fix-checkout-i18n-03-validation-copy.md` — child 03 waits for child 01 manifest. Join when: child 01 handoff verified before child 03 edits `payment.err.*` values.

## Conflict Hotspots
- `src/i18n/messages.ko.json` — Children: `docs/briefs/2026-04-30-refactor-checkout-i18n-01-message-keys.md`, `docs/briefs/2026-04-30-feat-checkout-i18n-02-cart-copy.md`; Access: serialized; Owner: `docs/briefs/2026-04-30-refactor-checkout-i18n-01-message-keys.md`; Rule: child 01 lands namespace structure before child 02 changes only `cart.*` values.
- `src/i18n/messages.ko.json` — Children: `docs/briefs/2026-04-30-refactor-checkout-i18n-01-message-keys.md`, `docs/briefs/2026-04-30-fix-checkout-i18n-03-validation-copy.md`; Access: serialized; Owner: `docs/briefs/2026-04-30-refactor-checkout-i18n-01-message-keys.md`; Rule: child 01 lands namespace structure before child 03 changes only `payment.err.*` values.
- `src/i18n/messages.ko.json` — Children: `docs/briefs/2026-04-30-feat-checkout-i18n-02-cart-copy.md`, `docs/briefs/2026-04-30-fix-checkout-i18n-03-validation-copy.md`; Access: parallel-safe; Rule: child 02 owns `cart.*`, child 03 owns `payment.err.*`, neither reorders unrelated keys, both rebase before join.

## Shared Constraints
- Korean (`ko`) only locale touched in this set. English fallback strings out of scope.
- No new i18n tooling — stay on existing `react-i18next` setup.

## Global Acceptance Criteria
- [ ] `rg -n '>[[:space:]]*[A-Za-z][^<{]*<' src/checkout` returns exit 1 after scanning all checkout JSX files — no user-visible English JSX text remains.
- [ ] `rg -n 'message:[[:space:]]*"[A-Za-z]' src/checkout` returns exit 1 after scanning validation sources — no raw English validation message remains.
- [ ] `rg "[가-힣]" src/checkout` returns exit 1 after scanning all checkout sources — Korean copy resolves from `src/i18n/messages.ko.json`, not hardcoded component text.
- [ ] All three child briefs' Acceptance Criteria checked.
- [ ] Cart copy diff against `docs/marketing/cart-copy-2026-04.md` is 0 (verbatim match).

## Open Questions
- [non-blocking] Should English fallback strings be added in a follow-up briefset or wait for the EN locale rebuild? — Default: defer them to the EN locale rebuild; Reconfirm before: checkout i18n release scope is finalized.
```

---

## Child brief 01 — message-keys (saved file, abridged)

```markdown
# [refactor] Normalize checkout message-key namespacing

## Work Type
refactor

## Current State (As-Is)
- [confirmed] `src/checkout/PaymentForm.tsx:42-78` hardcode English labels — Evidence: `PaymentForm` validation-rendering branch.
- [confirmed] Checkout uses `payment.err.*` and `payment_err_*` forms — Evidence: repo search across checkout consumers.
- [inferred] Duplicate forms risk lookup drift during parallel copy work — Confirm by: map both forms to consumers before normalization.

## Behavior Contract
- Locked: every user-visible string already shown in checkout flow continue to render same Korean text. No text content change permitted in this child — only resolution path moves from inline literal to `t('namespace.key')`.
- Locked: error-throwing call sites in `src/checkout/PaymentForm.tsx` keep emitting same logical error categories (no error-code change downstream).
- Contract artifacts: `src/checkout/__tests__/PaymentForm.test.tsx` (rendered-text assertions) and existing Cypress `cypress/e2e/checkout.cy.ts` happy-path scenarios.
- Verification: full unit suite + checkout Cypress scenarios stay green; manual diff of rendered Korean text on cart and payment screens shows zero copy change.

## Desired Outcome (To-Be)
- All checkout strings resolve through `t('namespace.key')`; no inline English literals remain in JSX or in error throwers.
- Single namespacing convention adopted (`payment.err.*`, `cart.*`) across checkout consumers.

## Scope
### In Scope
- `src/checkout/**/*.tsx` — replace inline English with `t(...)` calls.
- `src/i18n/messages.ko.json` — collapse duplicate keys to dot-separated form; add missing keys as empty placeholders for 02 and 03 to fill.
- `src/i18n/index.ts` — re-export cleaned namespace.
### Out of Scope
- [hard] Cart user-visible copy text (handled by `02-cart-copy`).
- [hard] Validation error copy text (handled by `03-validation-copy`).
- [deferred] English (`en`) locale file — separate future briefset.
- [deferred] Hardcoded-string ESLint rule — separate tooling plan.

## Related Files / Entry Points
- `src/checkout/PaymentForm.tsx` — inline English error labels lines 42-78.
- `src/i18n/messages.ko.json` — duplicate-key collapse target.
- `src/i18n/index.ts` — barrel re-export.
- `src/checkout/Cart.tsx`, `src/checkout/CartItem.tsx` — consumers needing key swap.

## Execution Plan
### Stage 1 — Lock rendered-copy contract
- Starts when: Existing checkout copy, key consumers, and child ownership confirmed.
- Work: Pin Korean rendered-copy contract and map legacy forms before edits.
- No-op when: `cart.*` and `payment.err.*` already canonical, all checkout consumers resolve them, and current rendered-copy checks pass without edits.
- No-op handoff: Children 02 and 03 receive unchanged-state evidence at `docs/briefs/handoffs/checkout-i18n/message-keys.md` and continue from verified placeholders.
- Deliverable: Verified behavior baseline and namespace migration map at `docs/briefs/handoffs/checkout-i18n/message-keys.md`; Format: `Namespaces`, `Placeholders`, and `Evidence` headings.
- Verify: `rg 'payment_err_|payment\.err\.|cart\.' src/checkout src/i18n/messages.ko.json`; Inputs: all checkout consumers plus complete Korean message file; Expected: every legacy key classified and every canonical namespace has recorded consumer or placeholder.
- Ends when:
  - [ ] Every legacy key maps to consumer or explicit removal target.
- Handoff: Stage 2 receives behavior baseline and migration map from `docs/briefs/handoffs/checkout-i18n/message-keys.md`.
- Replan when: Legacy key is used outside checkout or carries copy owned by child 02/03.

### Stage 2 — Normalize shared key surface
- Starts when: Stage 1 provides migration map and behavior baseline.
- Work: Produce stable `cart.*` and `payment.err.*` namespaces without copy change.
- Deliverable: Normalized namespaces and placeholders recorded at `docs/briefs/handoffs/checkout-i18n/message-keys.md` for Wave 2.
- Verify: `rg 'payment_err_' src/checkout src/i18n/messages.ko.json`; Inputs: all migrated checkout consumers and complete Korean message file; Expected: exit 1 with non-empty target file set, while canonical `cart.*` and `payment.err.*` keys remain resolvable.
- Ends when:
  - [ ] Checkout consumers resolve normalized keys and Korean copy stays unchanged.
- Handoff: Parent Wave 2 receives stable namespaces, placeholders, and verification evidence from `docs/briefs/handoffs/checkout-i18n/message-keys.md`.
- Replan when: Normalization requires copy change or cross-locale contract change.

## Side Effect Checkpoints
- [ ] All existing checkout E2E tests still pass without copy assertions failing.
- [ ] `t('payment.err.*')` keys still resolve after underscore variants removed.
- [ ] No untranslated key warnings in dev console after swap.

## Acceptance Criteria
- [ ] `rg "[가-힣]" src/checkout` return no matches — every inline copy literal externalized to `src/i18n/messages.ko.json` and resolve through `t('namespace.key')`.
- [ ] No underscore-form message keys (`*_err_*`) remain in `src/i18n/messages.ko.json`.
- [ ] Placeholder keys for `cart.*` and `payment.err.*` exist (empty strings allowed) so children 02 and 03 can fill them without edits to 01's surface.

## Open Questions
- None — no user-owned decision remains; lint enforcement is deferred as separate tooling work.
```

(Children 02 and 03 follow the same template; omitted here for brevity.
Both contain a populated `Side Effect Checkpoints` and child-scoped
`Acceptance Criteria`, and — per decision row 8 — both close their
`Open Questions` with the reasoned `- None — <reason>` form, e.g.
`- None — Stage 4 resolved scope and key ownership for this child; no
user-owned decision remains.` Their first-stage `Starts when` repeats
`docs/briefs/handoffs/checkout-i18n/message-keys.md`; every stage has
`Verify` / `Inputs` / `Expected`; every Stage 1 has paired no-change
fields. Child 03, being a `fix`, also carries a populated
`## Reproduction` section per the type-conditional rule. Both bodies
are in caveman full mode like the two files shown above.)

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
    after child 01 establishes exports. Parent pairwise hotspot rule
    makes parallel boundary and rebase join explicit.

A coding agent picking up child 01 cold should:

1. Open `src/checkout/PaymentForm.tsx` lines 42–78 and confirm the
   inline English error labels listed in `Current State (As-Is)`.
2. Open `src/i18n/messages.ko.json`, identify the duplicate
   `payment_err_*` keys, and plan the collapse to `payment.err.*`.
3. Add empty placeholder keys for `cart.*` and `payment.err.*` so
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
the per-child validation. The validator checks structure only — the
caveman register of the brief bodies is invisible to it.

**Stage 5.7 note** — briefset mode is itself an auto-ON trigger for
cold-pickup verification: the parent and every child each run their own
sub-agent pass (per-child signal gating is intentionally disabled in
briefset mode). `references/cold-pickup.md` requires one
`over_terse_bullets` list in each caveman report. With all four files
terminating on a clean first pass, the Stage 6 banner reports the
collapsed form
`cold-pickup: 1/1 parent + 3/3 children verdict:clean (no ask-backs, no missing concerns, no over-terse bullets)`.
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
