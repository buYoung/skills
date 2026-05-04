# Example 05 — Stage 4 branch walk (`useAuth` hook refactor)

A multi-decision `refactor` input where Stage 4 runs the full
branch-walking interview. Codebase-precedence checks prune two nodes
before they reach the user. The walk is the default Stage 4 flow —
no toggle is involved.

**What this example shows:** how Stage 4 walks the residual decision
tree top-down, asks one question per round with a recommended answer,
and prefers a narrow codebase probe over a user question when the
node is codebase-resolvable. Even when the tree shrinks late in the
walk, the remaining nodes are still asked one at a time — the policy
is uniformly sequential and never batches residual rounds.

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
be confirmed inside the Stage 4 walk (recommended answer).

---

## Codebase Review Notes (Stage 3)

Inline `rg` / `Read` / Serena symbol probes, ~6 reads / 4 queries
(carry-over budget for Stage 4 walk: ~9 reads / ~6 queries unused +
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

## Stage 4 Walk (one question per round)

The skill walks the decision tree. For each node it first runs the
codebase-precedence check; if a probe resolves the node, the user
question is skipped or downgraded to a one-line confirmation.

Tree (constructed from review + residual gaps):

```
Work Type (provisional: refactor)
└─ Behavior Contract (what gets locked)
   ├─ Public surface scope (which exports are public?)
   │  └─ Out of Scope (consumer call sites)
   ├─ Test suite as contract (existing tests sufficient?)
   └─ AuthContext coupling (touch or freeze?)
Acceptance Criteria
Side Effect Checkpoints
Open Questions (only those a probe cannot answer)
```

### Round 1 — Work Type confirmation

> 입력 보면 `refactor`로 잡는 게 맞아 보여 — "정리"라는 단어, 동작
> 변경 의도 없음, 컴포넌트 의존성 걱정. 맞아?
>
> 1. **`refactor` (Recommended)** — 동작 보존, 구조만 변경
> 2. `feat` — 정리 중에 새 인증 흐름도 추가
> 3. `chore` — 코드만 살짝, 거의 dead-code 제거 수준
>
> *내가 보기엔 1번이지만 다르면 알려줘.*

User: **1**.

Tree: type fixed → Behavior Contract branch becomes mandatory.

### Round 2 — Behavior Contract: locked test suite

Codebase-precedence probe first: `rg "describe.*useAuth" src/` and
`Read` on `useAuth.test.ts` → 23 cases cover `login`, `logout`,
session refresh, selector memoization, error states. Probe finding
stated as a confirmation, not an open question.

> Behavior Contract 잠그는 대상으로 `src/hooks/__tests__/useAuth.test.ts`
> 23개 케이스를 그대로 락으로 쓰는 게 자연스러워 보여 — login /
> logout / refresh / selector 4개 영역 다 커버하고 있어. 추가로
> 잠가야 할 외부 계약(예: 컴포넌트 통합 테스트)도 있어?
>
> 1. **테스트 23개만 락 (Recommended)** — 그게 그 훅의 명시 계약
> 2. + 컴포넌트 통합 테스트 일부도 락
> 3. 새 테스트를 먼저 추가하고 그걸 락
>
> *2번이면 어느 컴포넌트인지 알려줘.*

User: **1**.

### Round 3 — Public surface: `useAuthSelector` status

Codebase-precedence probe: `rg "useAuthSelector"` → 4 import sites,
all in `src/components/dashboard/*`. Reading two of them shows they
use it for memoized role-based rendering. Probe outcome: looks
**public** in practice, but the 4-site spread is small enough that
the user might want to fold it back into `useAuth`.

> `useAuthSelector` 4곳에서 import 중 — 전부 `src/components/dashboard/*`
> 안. 메모된 role 기반 렌더에 쓰여. **공식 public surface로 잠그는 게**
> 안전해 보여 (downstream에서 누가 또 쓸지 모르니).
>
> 1. **public 유지, 락 (Recommended)** — Behavior Contract에 포함
> 2. 내부로 강등 — 4곳을 `useAuth` 직접 호출로 inline
> 3. 분리 — 별도 훅 파일로 추출
>
> *2번 고르면 4곳 마이그레이션도 In Scope 들어와야 해.*

User: **1**.

### Round 4 — Internal helpers reach (codebase-resolved)

Tree node: "are the 3 internal helpers reachable from outside?"
Codebase-precedence probe: `rg "_validateToken\|_normalizeRole\|_decodeJwt"`
across `src/` → matches only inside `useAuth.ts`. Probe fully
resolves the node.

> 내부 헬퍼 3개 (`_validateToken`, `_normalizeRole`, `_decodeJwt`) —
> `src/` 전체에서 `useAuth.ts` 안에서만 참조됨. 외부 reach 없음
> 확인. 그래서 자유롭게 정리/이름변경/병합 가능.
>
> *별도 질문 없음, 그냥 알리는 거야.*

User: 👍 (no question fired).

### Round 5 — `AuthContext` coupling

> `AuthContext.tsx`는 `useAuth`와 reducer/dispatch로 단단히 묶여 있어.
> refactor 범위에 포함할까, 다음 brief로 미룰까?
>
> 1. **별도 brief로 미루기 (Recommended)** — 이번엔 `useAuth.ts` 안만
>    정리. Context 변경은 다른 사람도 영향받음
> 2. 같이 정리 — 같은 PR에서 둘 다
> 3. Context는 동결, hook만 손대되 import 면은 유지
>
> *내가 보기엔 1번 — 이번 brief의 blast radius를 hook 파일로 가두자.*

User: **3**. ("Context는 동결인 게 더 깔끔해. 다음 brief 만들 일이
없을 수도 있고.")

Tree update: option 3 prunes the "AuthContext as separate brief"
branch and adds a hard-freeze line to Out of Scope.

### Round 6 — Acceptance Criteria

> Acceptance Criteria 뼈대 — 이렇게 가는 게 맞아 보여:
>
> - [ ] 23개 useAuth 테스트 전부 그린 (Behavior Contract)
> - [ ] `useAuth.ts` 외부 export 시그니처 변경 없음
> - [ ] `AuthContext.tsx` 변경 없음 (file diff = 0줄)
> - [ ] 14개 import 사이트 어느 곳도 수정 불필요
> - [ ] `useAuth.ts` 줄 수 감소 (정리니까 측정 가능한 단순화 신호)
>
> 추가/수정?

User: "다 좋아. 마지막 줄 수 감소는 30% 이상으로 못 박지 말고 그냥
'감소'로 두자."

Skill: 그대로 반영.

### Termination

남은 mandatory 노드 없음, 사용자 응답 일관, 예산 안에서 완료.
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

- **Why the walk produced a tighter brief than a batched round
  would have** — the `AuthContext` coupling decision (Round 5) gated
  the rest of the Out of Scope section. In a single batched round,
  the user would have answered all questions in parallel and the
  skill would have had to draft Out of Scope before knowing whether
  `AuthContext` was in or out. Walking the tree top-down let Round 5
  prune later branches cleanly. This is exactly the failure mode the
  uniform sequential walk is designed to prevent: any cross-edge
  between nodes defeats batching, and "is there an edge?" is itself
  the kind of question agents misjudge under pressure to save rounds.
- **Why two rounds did not become user questions** — the
  codebase-precedence check resolved them. Round 4 ran a single `rg`
  to confirm the 3 internal helpers had no external reach; Round 3
  ran a 1-query probe to confirm `useAuthSelector`'s consumer
  spread. Both nodes downgraded to one-line confirmations or pure
  notifications. That is the core gain: ask the user only when the
  codebase cannot answer.
- **Why Open Questions ended at `None`** — every Stage 3 candidate
  open question was either resolved by a probe (helpers reach,
  selector publicness) or by a user answer (AuthContext freeze).
  Recording `None` here is honest, not lazy.
- **Why this passed the structural validator** — Stage 4 is a
  behavior variant of the brief-authoring pipeline, not an output
  variant. The saved brief has the same eight required H2 sections
  plus the type-conditional `Behavior Contract` for `refactor`.
  `validate_brief.py` does not care how the bullets were authored.
- **Why the user's "Context 동결" answer reshaped Out of Scope mid-walk** —
  every answer in the walk is allowed to prune the rest of the tree.
  The agent revised the Out of Scope draft right after Round 5
  rather than waiting until the end.
- **Budget accounting** — Stage 3 used ~6 reads / 4 queries; the
  Stage 4 walk added ~3 reads / 2 queries (Rounds 2, 3, 4). Total
  well under the soft caps (~15 + ~5 reads, ~10 + ~3 queries).
- **Why the walk stayed sequential through the late shrinkage** — by
  Round 5 the residual count had dropped (Rounds 2 and 4 were resolved
  by codebase probes, Round 1 fixed the type), but Rounds 5 and 6
  still fired one at a time. The walk policy is uniform: no mid-walk
  collapse into a batched prompt, even when only two rounds remain.
  This guarantees the dependency-resolution property end-to-end —
  Round 5's "Context 동결" answer reshapes Round 6's Acceptance
  Criteria draft, which would not have worked if 5 and 6 had been
  asked together.
