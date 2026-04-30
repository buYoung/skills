# Example 04 — Briefset mode: checkout i18n migration

This example shows the full briefset flow on a checkout i18n migration
that splits cleanly into multiple execution contexts.

It demonstrates: (a) why the request is a briefset rather than a single
brief, (b) the Stage 4 batched decomposition question, (c) the parent
brief, (d) the child briefs, and (e) the validator output.

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

## Stage 4 — Batched decomposition question (Korean)

> i18n briefset 분해안 검토 부탁:
>
> 1. 자식 셋으로 나누는 게 맞아? (`message-keys`, `cart-copy`,
>    `validation-copy`)
> 2. 빠진 자식 있어? 합쳐야 할 거는?
> 3. 실행 순서: `message-keys`(01) 먼저 → `cart-copy`(02)·`validation-copy`(03) 뒤로. 맞아?
> 4. 02·03이 동시에 가도 돼? — `messages.ko.json`을 둘 다 만져서 충돌
>    가능성 있는데, 키 영역이 겹치지 않으면 병렬 가능.
> 5. 추가 충돌 영역 있어? (현재는 `src/i18n/messages.ko.json` 하나만 잡음)
> 6. 공통 제약: 한국어만 1차 대상, 영어 fallback은 이번 set에서 건드리지
>    않음 — 맞아?
> 7. Open Questions 후보 확인:
>    - parent: 영어 fallback 문자열은 후속 briefset으로 처리할지, EN locale
>      일정까지 미룰지?
>    - 01: hardcoded JSX string 금지 ESLint rule은 이번 brief에 포함할지,
>      후속으로 미룰지?
>    - 02/03: 별도 Open Question 없이 `- None`으로 둬도 될지?
> 8. 02 자식의 완료 기준에 "마케팅이 보내준 카피와 1:1 일치" 정도가
>    들어가도 되나, 아니면 더 구체적으로?

**User answers (summarized):**

1. ✅ Three children correct.
2. None missing.
3. Order correct: 01 first, 02 and 03 after.
4. Parallel OK because cart keys (`cart.*`) and validation keys
   (`payment.err.*`) don't overlap. Document the conflict-hotspot rule
   anyway.
5. Add `src/i18n/index.ts` barrel — also touched by all three.
6. Yes — Korean only this round.
7. Keep the English fallback question on the parent. Keep the ESLint
   rule question in child 01 because it should not block the current
   i18n rewrite. Child 02 and 03 have no open questions.
8. Add criterion: "PM-supplied copy diff 0 — verbatim match against
   `docs/marketing/cart-copy-2026-04.md`".

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
- Wave 1: `01-message-keys` runs first.
- Wave 2: `02-cart-copy` and `03-validation-copy` can run in parallel after 01 lands.

## Dependencies
- `2026-04-30-feat-checkout-i18n-02-cart-copy.md` depends on `2026-04-30-refactor-checkout-i18n-01-message-keys.md` because it consumes the normalized `cart.*` key namespace introduced by 01.
- `2026-04-30-fix-checkout-i18n-03-validation-copy.md` depends on `2026-04-30-refactor-checkout-i18n-01-message-keys.md` because validation must emit the new `payment.err.*` keys defined by 01.

## Parallelization
- `2026-04-30-feat-checkout-i18n-02-cart-copy.md` and `2026-04-30-fix-checkout-i18n-03-validation-copy.md` can run in parallel — their key namespaces (`cart.*` vs `payment.err.*`) do not overlap.
- Both still touch `src/i18n/messages.ko.json` and `src/i18n/index.ts`; coordinate via small, key-scoped commits and rebase rather than long-lived branches.

## Conflict Hotspots
- `src/i18n/messages.ko.json` — every child edits this file. Append-only edits per child; no key reordering.
- `src/i18n/index.ts` — barrel re-exports get touched by all three. Keep additions alphabetized to minimize merge friction.

## Shared Constraints
- Korean (`ko`) is the only locale touched in this set. English fallback strings are out of scope.
- No new i18n tooling — stay on the existing `react-i18next` setup.

## Global Acceptance Criteria
- [ ] `rg "[A-Za-z]{4,}" src/checkout` finds no English-letter sequences in user-visible JSX strings.
- [ ] All three child briefs' Acceptance Criteria are checked.
- [ ] Cart copy diff against `docs/marketing/cart-copy-2026-04.md` is 0 (verbatim match).

## Open Questions
- Should English fallback strings be added in a follow-up briefset, or deferred until the EN locale rebuild is scheduled?
```

---

## Child brief 01 — message-keys (saved file, abridged)

```markdown
# [refactor] Normalize checkout message-key namespacing

## Work Type
refactor

## Current State (As-Is)
- `src/checkout/PaymentForm.tsx:42-78` hardcodes English error labels instead of resolving message keys.
- Message-key naming is inconsistent across checkout: `payment.err.*` (dot-separated) coexists with `payment_err_*` (underscore-separated).
- `src/i18n/messages.ko.json` has both styles, doubling lookup paths and breaking grep-by-key.

## Desired Outcome (To-Be)
- All checkout strings resolve through `t('namespace.key')`; no inline English literals remain in the JSX or in error throwers.
- Single namespacing convention adopted (`payment.err.*`, `cart.*`) and enforced by an ESLint rule (or a TODO if rule cannot land in this brief).

## Scope
### In Scope
- `src/checkout/**/*.tsx` — replace inline English with `t(...)` calls.
- `src/i18n/messages.ko.json` — collapse duplicate keys to the dot-separated form; add missing keys as empty placeholders for 02 and 03 to fill.
- `src/i18n/index.ts` — re-export the cleaned namespace.
### Out of Scope
- Cart user-visible copy text (handled by `02-cart-copy`).
- Validation error copy text (handled by `03-validation-copy`).
- English (`en`) locale file — separate future briefset.

## Related Files / Entry Points
- `src/checkout/PaymentForm.tsx` — inline English error labels lines 42-78.
- `src/i18n/messages.ko.json` — duplicate-key collapse target.
- `src/i18n/index.ts` — barrel re-export.
- `src/checkout/Cart.tsx`, `src/checkout/CartItem.tsx` — consumers needing key swap.

## Side Effect Checkpoints
- [ ] All existing checkout E2E tests still pass without copy assertions failing.
- [ ] `t('payment.err.*')` keys still resolve after underscore variants are removed.
- [ ] No untranslated key warnings in the dev console after the swap.

## Acceptance Criteria
- [ ] `rg "[A-Za-z]{4,}" src/checkout/**/*.tsx` finds no English-letter sequences in JSX text or error throws.
- [ ] No underscore-form message keys (`*_err_*`) remain in `src/i18n/messages.ko.json`.
- [ ] Placeholder keys for `cart.*` and `payment.err.*` exist (empty strings allowed) so children 02 and 03 can fill them without edits to 01's surface.

## Open Questions
- ESLint rule to forbid hardcoded JSX strings — block this brief or defer to a follow-up?
```

(Children 02 and 03 follow the same template; omitted here for brevity.)

---

## Stage 6 — Validator output

```bash
$ python3 skills/task-brief-creator/scripts/validate_briefset.py \
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
  ✓ child `2026-04-30-refactor-checkout-i18n-01-message-keys.md`: structural checks OK.
  ✓ child `2026-04-30-feat-checkout-i18n-02-cart-copy.md`: structural checks OK.
  ✓ child `2026-04-30-fix-checkout-i18n-03-validation-copy.md`: structural checks OK.

PASS - structural checks OK (0 warning(s)).
```

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
