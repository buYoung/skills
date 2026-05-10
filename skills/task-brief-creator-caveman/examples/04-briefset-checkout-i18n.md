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

코드베이스가 답할 수 있는 노드는 먼저 확인한다. 그 다음 분해,
자식별 작업 유형, 실행 순서, 충돌 영역, 자식별 잔여 결정처럼
사용자 소유 판단만 표로 묻는다.

| 순번 | 내용 | 수정 추천안 | 근거 |
|---|---|---|---|
| 1 | briefset 분해안 | `01-message-keys`, `02-cart-copy`, `03-validation-copy` 셋으로 분해한다. | 입력의 세 줄이 서로 다른 entry point와 완료 기준을 가진다. 하나로 합치면 작업 유형 규율이 섞인다. |
| 2 | 자식별 work type | `01=refactor`, `02=feat`, `03=fix`로 둔다. | 01은 구조 정리와 behavior 보존, 02는 새 마케팅 카피라는 사용자 가시 변경, 03은 잘못된 언어 노출 결함 수정이다. |
| 3 | 실행 순서 | Wave 1: 01, Wave 2: 02 + 03. | 01의 키 네임스페이스가 먼저 자리잡아야 02와 03이 안정적으로 키를 채울 수 있다. |
| 4 | 병렬화 여부 | 02와 03은 같은 wave에서 병렬 가능하되 충돌 영역을 parent에 표기한다. | 코드베이스 프로브에서 `cart.*`와 `payment.err.*` 키 영역은 겹치지 않았다. 다만 둘 다 `messages.ko.json`을 편집한다. |
| 5 | 충돌 영역 | `src/i18n/messages.ko.json`과 `src/i18n/index.ts`를 parent의 conflict hotspot으로 둔다. | checkout import가 barrel을 통해 들어오며, 자식 셋 모두 새 키 추가로 두 파일을 만질 가능성이 있다. |
| 6 | 공통 제약 | 한국어(`ko`) 로케일만 대상, 영어 fallback은 Out of Scope, 새 i18n 도구 도입 없음. | 입력이 "결제 화면에서 영어 텍스트가 한 글자도 안 남아야 함"과 기존 메시지 파일 유지 방향을 명시했다. |
| 7 | 자식 02 완료 기준 | `docs/marketing/cart-copy-2026-04.md`와 cart copy diff가 0이어야 한다는 기준을 추가한다. | 마케팅 카피 적용은 해석보다 원문 일치가 검증 가능한 완료 기준이다. |
| 8 | 사용자 결정이 필요한 Open Questions | Parent에는 영어 fallback 처리 일정을 남기고, 01에는 hardcoded JSX string 금지 ESLint rule을 후속 권장으로 남긴다. 02와 03은 `- None`으로 둔다. | fallback 일정과 lint rule 도입은 코드베이스만으로 결정할 수 없는 범위/일정 판단이다. |

User: approve rows 1-8.

### Termination

모든 사용자 소유 결정이 확정됐다. 코드베이스 프로브는 병렬화와
충돌 영역의 기술적 사실을 먼저 해결했고, 남은 사용자 결정은
parent와 child `Open Questions`에 명시적으로 배치된다. Stage 5로
이동.

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
- Wave 1: `01-message-keys` run first.
- Wave 2: `02-cart-copy` and `03-validation-copy` can run in parallel after 01 lands.

## Dependencies
- `2026-04-30-feat-checkout-i18n-02-cart-copy.md` depends on `2026-04-30-refactor-checkout-i18n-01-message-keys.md` — consume normalized `cart.*` key namespace introduced by 01.
- `2026-04-30-fix-checkout-i18n-03-validation-copy.md` depends on `2026-04-30-refactor-checkout-i18n-01-message-keys.md` — validation must emit new `payment.err.*` keys defined by 01.

## Parallelization
- `2026-04-30-feat-checkout-i18n-02-cart-copy.md` and `2026-04-30-fix-checkout-i18n-03-validation-copy.md` can run in parallel — their key namespaces (`cart.*` vs `payment.err.*`) do not overlap.
- Both still touch `src/i18n/messages.ko.json` and `src/i18n/index.ts`; coordinate via small, key-scoped commits and rebase, not long-lived branches.

## Conflict Hotspots
- `src/i18n/messages.ko.json` — every child edit this file. Append-only edits per child; no key reordering.
- `src/i18n/index.ts` — barrel re-exports touched by all three. Keep additions alphabetized to minimize merge friction.

## Shared Constraints
- Korean (`ko`) only locale touched in this set. English fallback strings out of scope.
- No new i18n tooling — stay on existing `react-i18next` setup.

## Global Acceptance Criteria
- [ ] `rg "[A-Za-z]{4,}" src/checkout` find no English-letter sequences in user-visible JSX strings.
- [ ] All three child briefs' Acceptance Criteria checked.
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
- `src/checkout/PaymentForm.tsx:42-78` hardcode English error labels instead of resolving message keys.
- Message-key naming inconsistent across checkout: `payment.err.*` (dot-separated) coexist with `payment_err_*` (underscore-separated).
- `src/i18n/messages.ko.json` has both styles — double lookup paths and break grep-by-key.

## Behavior Contract
- Locked: every user-visible string already shown in checkout flow continue to render same Korean text. No text content change permitted in this child — only resolution path moves from inline literal to `t('namespace.key')`.
- Locked: error-throwing call sites in `src/checkout/PaymentForm.tsx` keep emitting same logical error categories (no error-code change downstream).
- Contract artifacts: `src/checkout/__tests__/PaymentForm.test.tsx` (rendered-text assertions) and existing Cypress `cypress/e2e/checkout.cy.ts` happy-path scenarios.
- Verification: full unit suite + checkout Cypress scenarios stay green; manual diff of rendered Korean text on cart and payment screens shows zero copy change.

## Desired Outcome (To-Be)
- All checkout strings resolve through `t('namespace.key')`; no inline English literals remain in JSX or in error throwers.
- Single namespacing convention adopted (`payment.err.*`, `cart.*`) and enforced by ESLint rule (or TODO if rule cannot land in this brief).

## Scope
### In Scope
- `src/checkout/**/*.tsx` — replace inline English with `t(...)` calls.
- `src/i18n/messages.ko.json` — collapse duplicate keys to dot-separated form; add missing keys as empty placeholders for 02 and 03 to fill.
- `src/i18n/index.ts` — re-export cleaned namespace.
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
- [ ] `t('payment.err.*')` keys still resolve after underscore variants removed.
- [ ] No untranslated key warnings in dev console after swap.

## Acceptance Criteria
- [ ] `rg "[A-Za-z]{4,}" src/checkout/**/*.tsx` find no English-letter sequences in JSX text or error throws.
- [ ] No underscore-form message keys (`*_err_*`) remain in `src/i18n/messages.ko.json`.
- [ ] Placeholder keys for `cart.*` and `payment.err.*` exist (empty strings allowed) so children 02 and 03 can fill them without edits to 01's surface.

## Open Questions
- Should an ESLint rule that forbids hardcoded JSX strings block this brief, or be deferred to a follow-up?
```

(Children 02 and 03 follow the same template; omitted here for brevity.
Both contain a populated `Side Effect Checkpoints` and child-scoped
`Acceptance Criteria`. Child 03, being a `fix`, also carries a populated
`## Reproduction` section per the type-conditional rule.)

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
  - Both touch `src/i18n/messages.ko.json` and `src/i18n/index.ts` —
    the parent's `Conflict Hotspots` section tells them to commit
    small, key-scoped changes and rebase rather than long-lived
    branches. Neither agent needs to coordinate with the other beyond
    that rule.

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

```bash
$ python3 skills/task-brief-creator-caveman/scripts/validate_briefset.py \
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
