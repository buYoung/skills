# Example 05 — Stage 4 decision table (`useAuth` hook refactor)

A multi-decision `refactor` input where Stage 4 first resolves
codebase-answerable facts, then asks the user to decide the remaining
scope and contract questions in one Markdown decision table.

**What this example shows:** how Stage 4 separates technical facts from
user-owned decisions. Narrow codebase probes remove questions that do
not need user judgment. The remaining questions are shown as rows with
`순번`, `내용`, `수정 추천안`, and `근거`.

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

Inline `rg` / `Read` / Serena symbol probes, ~6 reads / 4 queries
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
| 1 | Work type to write into the brief | Keep `refactor`. | The input asks to tidy the hook and bound dependency risk, with no requested behavior change. |
| 2 | Behavior Contract source | Use the 23 existing `src/hooks/__tests__/useAuth.test.ts` cases as the locked behavior contract. | Codebase review shows these cases cover login, logout, refresh, selector memoization, and error states. |
| 3 | `useAuthSelector` public-surface status | Treat `useAuthSelector` as public and keep it in the Behavior Contract. | It is imported by 4 dashboard components for memoized role-based rendering. Internalizing it would expand scope into consumer migration. |
| 4 | `AuthContext.tsx` coupling | Freeze `AuthContext.tsx`; refactor only `useAuth.ts` while preserving the import surface. | The file is tightly coupled through reducer/dispatch. User prefers a narrow hook-only brief and no separate context follow-up. |
| 5 | Acceptance Criteria wording | Require all 23 tests green, unchanged export signatures, zero `AuthContext.tsx` diff, no consumer-site edits, and a reduced `useAuth.ts` line count without a fixed percentage target. | These criteria preserve behavior while allowing internal cleanup. A fixed 30% reduction would be arbitrary for a refactor. |

User: approve rows 1-3 and 5; for row 4 choose "freeze `AuthContext.tsx`."

### Termination

남은 사용자 소유 결정 없음, 사용자 응답 일관, 예산 안에서 완료.
`Open Questions` 후보 중 codebase로 해결된 2개는 제거. 잔여
질문은 `None`. Stage 5로 이동.

---

## Output (`docs/briefs/2026-05-04-refactor-useauth-hook.md`)

```markdown
# [refactor] Tidy `useAuth` hook internals while freezing public surface

## Work Type
refactor

## Current State (As-Is)
- `src/hooks/useAuth.ts` exports 7 named values (`useAuth`, `AuthState`, `AuthAction`, `loginWithCredentials`, `logout`, `refreshSession`, `useAuthSelector`); 14 component files depend on the surface.
- 3 file-internal helpers (`_validateToken`, `_normalizeRole`, `_decodeJwt`) have no reach outside `useAuth.ts` (verified by repo-wide search) but currently sit alongside the public exports without grouping.
- `useAuthSelector` is imported in 4 dashboard components and is treated as part of the public contract.
- `src/hooks/__tests__/useAuth.test.ts` carries 23 cases covering login / logout / refresh / selector memoization; this is the de facto behavior specification.
- `src/contexts/AuthContext.tsx` is tightly coupled to `useAuth` via reducer/dispatch but is explicitly out of scope for this brief.

## Behavior Contract
- Locked: every case in `src/hooks/__tests__/useAuth.test.ts` (all 23 tests).
- Locked: the named-export shape of `useAuth.ts` — same names, same call signatures, same return types.
- Locked: `src/contexts/AuthContext.tsx` — file diff must be zero lines.
- Verification: `pnpm vitest src/hooks/__tests__/useAuth.test.ts` is green before and after; `git diff --stat src/contexts/AuthContext.tsx` returns 0; the 14 importing component files compile and test without modification.

## Desired Outcome (To-Be)
- `useAuth.ts` is internally reorganized — helpers grouped, dead branches removed, naming consistent — with no observable change to consumers.
- The 3 internal helpers can be renamed, merged, or restructured freely; they are not part of the contract.
- `AuthContext.tsx` and all 14 import sites are untouched.

## Scope
### In Scope
- Internal restructure of `src/hooks/useAuth.ts` (helper grouping, internal naming, dead-code removal, internal type cleanup).
- Free editing of the 3 file-internal helpers as long as the public surface stays identical.
### Out of Scope
- Any change to `src/contexts/AuthContext.tsx` (hard freeze).
- Any change to the named-export surface of `useAuth.ts`.
- Modifying any of the 14 importing component files.
- Promoting `useAuthSelector` to a separate file or demoting it to internal.
- Adjusting the `AuthContext` ↔ `useAuth` coupling (separate effort if needed).

## Related Files / Entry Points
- `src/hooks/useAuth.ts` — sole edit target; restructure internals only.
- `src/hooks/__tests__/useAuth.test.ts` — locked test suite; do not modify, must stay green.
- `src/contexts/AuthContext.tsx` — frozen; reference only.
- `src/components/dashboard/` — imports `useAuthSelector`; do not edit.

## Side Effect Checkpoints
- [ ] No diff in `src/contexts/AuthContext.tsx` (`git diff --stat` is empty).
- [ ] No diff in any of the 14 importing component files (`git diff src/components`).
- [ ] No new exports added, no existing exports removed or renamed in `useAuth.ts`.
- [ ] Type-check passes against the unmodified consumer files.

## Acceptance Criteria
- [ ] All 23 cases in `src/hooks/__tests__/useAuth.test.ts` pass after the refactor.
- [ ] The named-export surface of `src/hooks/useAuth.ts` is byte-identical for names and shape.
- [ ] `src/contexts/AuthContext.tsx` is unchanged.
- [ ] None of the 14 importing component files require edits to compile or test.
- [ ] `src/hooks/useAuth.ts` line count decreases (measurable simplification signal).

## Open Questions
- None
```

---

## Picked Up Cold — Coding Agent's First Actions

A coding agent receiving only the saved brief should reach a green
locked-test run inside an hour. From the brief alone:

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
6. Confirm line-count reduction (Acceptance Criteria #5).

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
- **Why Open Questions ended at `None`** — every Stage 3 candidate
  open question was either resolved by a probe (helpers reach,
  selector publicness) or by a user answer (AuthContext freeze).
  Recording `None` here is honest, not lazy.
- **Why this passed the structural validator** — Stage 4 is a
  behavior variant of the brief-authoring pipeline, not an output
  variant. The saved brief has the same eight required H2 sections
  plus the type-conditional `Behavior Contract` for `refactor`.
  `validate_brief.py` does not care how the bullets were authored.
- **Why the user's "Context 동결" answer reshaped Out of Scope** —
  row 4 is a user-owned scope decision, so the saved brief reflects
  that answer by freezing `AuthContext.tsx` and keeping the work inside
  `useAuth.ts`.
- **Budget accounting** — Stage 3 used ~6 reads / 4 queries; the
  Stage 4 probes added ~3 reads / 2 queries. Total
  well under the soft caps (~15 + ~5 reads, ~10 + ~3 queries).
- **Why the table still avoids lazy batching** — each row maps to a
  concrete brief edit, and dependent facts are called out in `근거`.
  It is not a generic "add or change?" prompt; it is a compact decision
  register the user can approve or override by row.
