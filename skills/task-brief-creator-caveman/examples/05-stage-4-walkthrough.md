# Example 05 — Stage 4 decision table (`useAuth` hook refactor)

A multi-decision `refactor` input where Stage 4 first resolves
codebase-answerable facts, then asks the user to decide the remaining
scope and contract questions in one Markdown decision table.

**What this example shows:** how Stage 4 separates technical facts from
user-owned decisions. Narrow codebase probes remove questions that do
not need user judgment. The remaining questions are shown as rows with
`순번`, `내용`, `수정 추천안`, and `근거`. Because the work type is
`refactor`, the walkthrough also shows the Stage 5.5 downstream
interpretation check and the Stage 5.7 cold-pickup gate firing and
terminating on a clean first pass — including the
caveman-only `over_terse_bullets` check.

The chat exchange below is in Korean because the user wrote in Korean.
The saved brief is in English (skill output policy).

---

## Input (typed by user)

```
useAuth 훅 깔끔하게 정리하고 싶은데 컴포넌트 너무 많이 의존하고
있어서 어디까지 손대야 할지 애매해.
```

---

## Anchor Check (Stage 1)

| Anchor | Derivable? | Reasoning |
|---|---|---|
| **PROBLEM** | ✓ | "깔끔하게 정리" + "어디까지 손대야 할지 애매" → structural cleanup with unclear boundary. |
| **GOAL** | ✓ (implicit) | A tidier `useAuth` whose blast radius on consumers is bounded. |
| **SCOPE** | ✓ | "useAuth 훅" — narrow named subsystem. |
| **TARGET** | ✓ | `useAuth` is a concrete hook. Stage 3 will resolve the file path. |

**Anchors present: 4 / 4** → CONTINUE. No halt.

Briefset signals not strong enough to recommend a split (one named
hook, one cohesive cleanup goal) — stay in single-brief output mode.

---

## Provisional Work Type (Stage 2)

Input language ("정리", "어디까지 손대야 할지") plus the consumer-count
anxiety strongly suggest `refactor`. Type stays provisional and will
be confirmed inside the Stage 4 decision table.

---

## Codebase Review Notes (Stage 3)

Inline `rg` / `Read` / allowed symbol probes, ~6 reads / 4 queries
(carry-over budget for Stage 4 probes: ~9 reads / ~6 queries unused +
~5 reads / ~3 queries Stage 4 cap):

- `src/hooks/useAuth.ts` — 7 exports: `useAuth` hook, `AuthState`
  type, `AuthAction` enum, `loginWithCredentials`, `logout`,
  `refreshSession`, `useAuthSelector` (memoized derived state).
  3 internal helpers not exported.
- `src/contexts/AuthContext.tsx` — paired provider. Stores reducer
  state and dispatches into `useAuth`. Tightly coupled.
- `rg "from '@/hooks/useAuth'" -t ts` → 14 component files import
  one or more named exports. `useAuth` itself: 12 sites.
  `useAuthSelector`: 4 sites. Other named exports: ≤ 2 sites each.
- `src/hooks/__tests__/useAuth.test.ts` — 23 tests covering the
  hook surface (`login`, `logout`, refresh, selector memoization).
- 6 component tests jest-mock `@/hooks/useAuth` with a stub object;
  none of them assert on internals.

Tagged candidate `Open Questions` from review:

- Is `useAuthSelector` part of the public surface or an internal
  helper that leaked? (4 import sites is a small spread.)
- The 3 internal helpers — are any of them used elsewhere via dynamic
  reach (e.g., through `AuthContext`)?

---

## Stage 4 — User Decision Table

The skill probes codebase-answerable nodes first. It does not ask about
the 3 internal helpers after `rg "_validateToken\|_normalizeRole\|_decodeJwt"`
shows they are only referenced inside `useAuth.ts`.

| 순번 | 내용 | 수정 추천안 | 근거 |
|---|---|---|---|
| 1 | `AuthContext.tsx` scope boundary | Freeze `AuthContext.tsx`; refactor only `useAuth.ts` while preserving the import surface. | The file is tightly coupled through reducer/dispatch, and crossing that boundary changes the requested scope. |

User: approve row 1 and freeze `AuthContext.tsx`.

### Termination

남은 사용자 소유 결정 없음, 사용자 응답 일관, 예산 안에서 완료.
`Open Questions` 후보 중 codebase로 해결된 2개는 제거. 잔여 질문이
없으므로 `- None — <reason>` 형태로 사유를 명시해 닫는다. Stage 5로
이동.

---

## Output (`docs/briefs/2026-05-04-refactor-useauth-hook.md`)

```markdown
# [refactor] Tidy `useAuth` hook internals while freezing public surface

## Work Type
refactor

## Current State (As-Is)
- [confirmed] `src/hooks/useAuth.ts` export 7 named values; 14 component files depend on surface — Evidence: exports plus repo import search.
- [confirmed] Three internal helpers have no reach outside `useAuth.ts` — Evidence: repo-wide symbol search.
- [confirmed] `useAuthSelector` imported in 4 dashboard components — Evidence: named-import search.
- [confirmed] `src/hooks/__tests__/useAuth.test.ts` carry 23 behavior cases — Evidence: existing test declarations.
- [confirmed] `src/contexts/AuthContext.tsx` coupled through reducer/dispatch and frozen by Stage 4 scope decision — Evidence: provider imports and approved row.

## Behavior Contract
- Locked: every case in `src/hooks/__tests__/useAuth.test.ts` (all 23 tests).
- Locked: the named-export shape of `useAuth.ts` — same names, same call signatures, same return types.
- Locked: `src/contexts/AuthContext.tsx` — file diff must be zero lines.
- Verification: `pnpm vitest src/hooks/__tests__/useAuth.test.ts` green before and after; `git diff --stat src/contexts/AuthContext.tsx` returns 0; the 14 importing component files compile and test without modification.

## Desired Outcome (To-Be)
- `useAuth.ts` internally reorganized — helpers grouped, dead branches removed, naming consistent — with no observable change to consumers.
- 3 internal helpers can be renamed, merged, or restructured freely; not part of contract.
- `AuthContext.tsx` and all 14 import sites untouched.

## Scope
### In Scope
- Internal restructure of `src/hooks/useAuth.ts` (helper grouping, internal naming, dead-code removal, internal type cleanup).
- Free editing of 3 file-internal helpers as long as public surface stay identical.
### Out of Scope
- [hard] Any change to `src/contexts/AuthContext.tsx` (hard freeze).
- [hard] Any change to named-export surface of `useAuth.ts`.
- [hard] Modifying any of 14 importing component files.
- [hard] Promoting `useAuthSelector` to separate file or demoting it to internal.
- [deferred] Adjusting `AuthContext` ↔ `useAuth` coupling (separate effort if needed).

## Related Files / Entry Points
- `src/hooks/useAuth.ts` — sole edit target; restructure internals only.
- `src/hooks/__tests__/useAuth.test.ts` — locked test suite; do not modify, must stay green.
- `src/contexts/AuthContext.tsx` — frozen; reference only.
- `src/components/dashboard/` — imports `useAuthSelector`; do not edit.

## Execution Plan
### Stage 1 — Lock behavior and export baseline
- Starts when: Existing hook suite, export surface, and frozen consumer files available.
- Work: Verify behavior contract and record public/internal boundary before edits.
- Deliverable: Green baseline and export/consumer map constraining refactor.
- Ends when:
  - [ ] All 23 behavior cases pass and 7-export surface is recorded.
- Handoff: Stage 2 receives verified baseline and public/internal boundary.
- Replan when: Baseline fails or internal helper has unrecorded external consumer.

### Stage 2 — Reorganize hook internals
- Starts when: Stage 1 provides verified baseline and boundary map.
- Work: Improve internal organization while preserving locked exports, behaviors, and frozen files.
- Deliverable: Focused `useAuth.ts` refactor ready for contract verification.
- Ends when:
  - [ ] Internal organization goal met without edits outside `useAuth.ts`.
- Handoff: Overall verification receives focused refactor and original baseline evidence.
- Replan when: Cleanup requires `AuthContext.tsx`, consumer, or export-surface change.
- Worker decision: Rename, merge, or regroup three internal helpers inside locked behavior contract.

## Side Effect Checkpoints
- [ ] No diff in `src/contexts/AuthContext.tsx` (`git diff --stat` empty).
- [ ] No diff in any of 14 importing component files (`git diff src/components`).
- [ ] No new exports added, no existing exports removed or renamed in `useAuth.ts`.
- [ ] Type-check pass against unmodified consumer files.

## Acceptance Criteria
- [ ] All 23 cases in `src/hooks/__tests__/useAuth.test.ts` pass after refactor.
- [ ] Named-export surface of `src/hooks/useAuth.ts` byte-identical for names and shape.
- [ ] `src/contexts/AuthContext.tsx` unchanged.
- [ ] None of 14 importing component files require edits to compile or test.
- [ ] `src/hooks/useAuth.ts` diff show clearer internal organization (helpers grouped, dead branches removed, naming consistent) without relying on line-count reduction as success signal.

## Open Questions
- None — every Stage 3 uncertainty was resolved by a codebase probe (internal-helper reach, `useAuthSelector` consumer spread) or by a Stage 4 user answer (`AuthContext.tsx` freeze).
```

---

## Stage 5.5 — Downstream Execution-Reconstruction Check

After structural validation passes, a sub-agent receives a natural
work-start request with only the saved brief path. The sub-agent recovers
Stage 1's behavior/export baseline, Stage 2's bounded refactor, the handoff
into overall verification, and the replan boundary around frozen files.
That reconstruction matches the user request and Stage 4 decisions, so no
patch is needed.

---

## Stage 5.7 — Cold-Pickup Verification

Gate evaluation: work type is `refactor` — type ∈ {fix, perf, refactor}
fires the auto-ON gate regardless of input simplicity (the 5
user-decision rows from Stage 4 would fire it independently). The
structural validator passed in Stage 5 and downstream execution reconstruction
aligned in Stage 5.5, so the pass runs.

Pass 1 — the saved brief is snapshotted, then a sub-agent receives
**only** the original Korean input and the brief path: no Stage 3
uncertainty register, no Stage 4 decisions, no Stage 5.5 downstream
interpretation result, no Stage 5.6 self-check result. The
`references/cold-pickup.md` requires the caveman-only
`over_terse_bullets` list on top of the standard schema.
Its report:

```yaml
verdict: clean
first_actions:
  - Run `pnpm vitest src/hooks/__tests__/useAuth.test.ts` on `main` to confirm the 23-case baseline is green.
  - Open `src/hooks/useAuth.ts` and map the 7 named exports against the locked surface before touching internals.
ask_backs: []
missing_concerns: []
over_terse_bullets: []
```

`verdict: clean` with empty `ask_backs`, `missing_concerns`, and
`over_terse_bullets` is termination trigger 4 (Clean pass) — the loop
stops after 1 pass with no patches, and the pass-1 snapshot is deleted.
Had the sub-agent flagged an over-terse bullet, it would have been
treated as register drift and rewritten in normal prose under the
Auto-Clarity carve-out — never matched against a Stage 4 row as
disagreement.

Stage 6 banner (Korean, because the chat is Korean — structural validation
is reported separately from execution reconstruction, self-check, and cold-pickup):

> 저장 완료 — `docs/briefs/2026-05-04-refactor-useauth-hook.md`
> (`refactor`: Tidy `useAuth` hook internals while freezing public
> surface; 구조 검증 통과; downstream 해석 일치; 내용 자체 검증 통과 — 입력의 주요 항목
> 반영, 문체 변환 동등성 확인; cold-pickup `clean_pass`로 1회 만에
> 종료 (ask-back 없음, missing 없음, 과압축 지적 없음)).
> 파일 열어보고 고칠 부분 있으면 알려줘.

The English equivalent of the cold-pickup field is
`cold-pickup clean_pass after 1 pass (no ask-backs, no missing
concerns, no over-terse bullets)`.

---

## Picked Up Cold — Coding Agent's First Actions

A coding agent receiving only the saved brief should be able to start,
preserve the locked behavior, and decide completion without asking for
more scope. From the brief alone:

1. Run `pnpm vitest src/hooks/__tests__/useAuth.test.ts` against `main`
   to confirm the 23-case baseline is green (Behavior Contract).
2. Open `src/hooks/useAuth.ts` (only edit target named in `Related
   Files / Entry Points`) and restructure internals — group helpers,
   remove dead branches, normalize naming. Stay inside the file.
3. Re-run the locked suite after each meaningful change. The suite
   stays green or the change is reverted (Behavior Contract +
   Acceptance Criteria #1).
4. Confirm `git diff --stat` shows changes only in
   `src/hooks/useAuth.ts` (Side Effect Checkpoints + Out of Scope).
5. Verify named-export shape with a type-check pass against the
   unmodified consumers (Acceptance Criteria #2 & #4).
6. Review `useAuth.ts` diff for clearer internal organization without
   using line-count reduction as success signal (Acceptance Criteria #5).

The agent does **not** touch `AuthContext.tsx` (frozen), does not edit
any of the 14 importing components, and does not refactor across
files. The brief explicitly hands the cross-file work to a future
brief if it is ever needed.

---

## Notes

- **Why the decision table produced a tighter brief** — the
  `AuthContext` coupling decision gates the rest of the Out of Scope
  section, so it appears as its own row with the recommended brief
  change and evidence. The user can override just that row without
  losing the other resolved decisions.
- **Why two candidates did not become user questions** — the
  codebase-precedence check resolved them. One probe confirmed the 3
  internal helpers had no external reach; another probe confirmed
  `useAuthSelector`'s consumer spread. Technical facts do not become
  user questions once the repository can answer them.
- **Why Open Questions ended at `- None — <reason>`** — every Stage 3
  candidate open question was either resolved by a probe (helpers
  reach, selector publicness) or by a user answer (AuthContext freeze).
  Recording `None` with its reason is honest, not lazy — and the reason
  is mandatory: the validator rejects a bare `- None`. The bullet also
  stays in normal prose: the entire `Open Questions` section is an
  Auto-Clarity carve-out, never caveman-rewritten.
- **Why this passed the structural validator** — Stage 4 is a
  behavior variant of the brief-authoring pipeline, not an output
  variant. The saved plan has the same nine required H2 sections
  plus the type-conditional `Behavior Contract` for `refactor`, its
  `Out of Scope` bullets carry `[hard]` / `[deferred]` classification,
  and `Open Questions` closes with the reasoned `- None — <reason>`
  form the validator requires. `validate_brief.py` does not care how
  the bullets were authored — or that the body register is caveman —
  only that the saved artifact meets the template contract.
- **Why the user's "Context 동결" answer reshaped Out of Scope** —
  row 1 is a user-owned scope decision, so the saved brief reflects
  that answer by freezing `AuthContext.tsx` and keeping the work inside
  `useAuth.ts`.
- **Budget accounting** — Stage 3 used ~6 reads / 4 queries; the
  Stage 4 probes added ~3 reads / 2 queries. Total
  well under the soft caps (~15 + ~5 reads, ~10 + ~3 queries).
- **Why the table still avoids lazy batching** — each row maps to a
  concrete brief edit, and dependent facts are called out in `근거`.
  It is not a generic "add or change?" prompt; it is a compact decision
  register the user can approve or override by row.
