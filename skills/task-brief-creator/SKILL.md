---
name: task-brief-creator
description: >
  Generate a structured work-brief Markdown at `docs/briefs/` from planning
  notes or a rough task description. Eight required sections keyed to
  Conventional Commits types so downstream coding agents switch behavior
  (refactor → preserve, fix → reproduce first, perf → measure first).
  Briefset mode emits a parent execution-management document plus N child
  briefs when the input describes multiple execution contexts.
---

# Task Brief Creator

Produce a structured work-brief Markdown document under `docs/briefs/` that a downstream coding agent (or a human engineer) can pick up and execute without re-interviewing the requester.

The brief is the *handoff artifact*.
Its job is to shrink the cost of the first hour a coding agent spends on the task — routing it to the right files, fixing the behavior envelope, and pre-answering the questions that would otherwise bounce back to the requester.

**The brief is an executable work instruction — nothing else.** It is not a scope-control memo, not a discussion summary, not a planning note, not a background briefing, not a rationale document.
Every section must answer *"what does the coding agent do next?"* — if a section reads like meeting minutes, negotiation history, or context prose, rewrite it until it routes to files, decisions, or verifiable outcomes.
A brief that makes the downstream agent re-interview the requester is a **failed brief**, regardless of how polished it reads.

**"Executable, not discursive" is a *prose style* rule, not a *content reduction* rule.** It tells you how each bullet should read — direct, action-routing, no rationale prose.
It does not tell you to *drop* distinct concerns, *merge* unrelated bullets, or *summarize* the input down to its highlights.
A brief that omits a concern from the input is also a failed brief, because the downstream agent will silently miss it.
Tight prose, full enumeration: short bullets are fine and encouraged, but every distinct concern from the input and the codebase review must land somewhere in the brief.

---

## Modes

This skill operates in one of two **output modes**:

- **Single-brief mode** (default) — emits one brief per invocation.
  The workflow below covers this case end to end.
- **Briefset mode** — emits a parent execution-management document plus N independently executable child briefs.
  Used when the input describes **multiple execution contexts** that need coordination (independent completion criteria, mixed work types, ordered dependencies, parallelizable waves, or shared conflict hotspots).
  Recommended by the criteria in `references/briefset.md`; long input, many files, or many related edit points alone never trigger briefset mode.

Output-mode selection happens at Stage 1 alongside the ambiguity gate.
In briefset mode, follow the workflow below with the per-stage adaptations in `references/briefset.md` (parent template, naming, decomposition decision table, dual-validator save).

**Stage 4 always runs as a user decision table** — after codebase review, gather ambiguous or user-owned decisions and present them in a Markdown table with `순번`, `내용`, `수정 추천안`, and `근거`.
Codebase-resolvable technical facts are probed instead of asked, while product intent, scope, acceptance thresholds, sequencing, and ownership decisions are tabled for the user.
The decision table is the default Stage 4 behavior, not a separate mode.
See `references/stage-4-interview.md` for the full decision classification, codebase-precedence, and termination rules.

---

## Code Agent Operating Path

Load references only when their decision point arrives:

1. Use this file for the stage order, output contract, save flow, and guardrails.
2. Read `references/work-types.md` during Stage 2 when the work type is not obvious or when the type changes downstream behavior.
3. Read `references/briefset.md` during Stage 1 when multiple execution contexts are plausible.
4. Read `references/bloat-decomposition.md` only after a candidate child brief is independently executable but still looks oversized or mixed.
5. Read `references/stage-4-interview.md` before presenting user-owned decisions.
6. Read `references/template.md` while composing the saved Markdown.

Do not re-open every reference by habit.
The goal is to keep the live context focused on the next decision the coding agent must make.

---

## When This Skill Runs

- **Manual trigger only.** The user invokes this skill explicitly (via slash command, `/task-brief-creator`, or similar).
- Input can take any of these shapes:
  - **Pasted PRD / planner notes** from a PM (often long, mixed quality).
  - **Rough task notes** typed into chat (one or two lines).
  - **Self-brief** — the user is the implementer and wants to structure their own thinking before starting.
  - **Tech-lead handoff** — a lead drafts the brief to hand off to a teammate/cop or downstream agent.
  - **Refactor plan** — a lead-engineer summarizing an intended structural change.
- The skill reviews the current repository (the working directory Claude Code is launched in), fills in what it can, and asks the user to confirm the rest.

---

## Interaction Language

- **Chat / live interaction language follows the user's input.** If the user writes in Korean, reply in Korean.
  If they write in English, reply in English.
  Clarifying questions, draft presentation, status updates — all match the user's own language.
- **The brief document itself is written in English.** Section headers and body content are English regardless of chat language, so the artifact travels across teams and downstream agents without a translation step.
- Code blocks, file paths, identifiers, PR numbers stay as-is.
- This SKILL.md and reference files stay in English (repo authoring policy).

---

## Output Contract

| Field | Value |
|---|---|
| Directory | `docs/briefs/` (relative to repository root) |
| Filename | `YYYY-MM-DD-<type>-<slug>.md` |
| `YYYY-MM-DD` | Today's date in repository's local timezone |
| `<type>` | Conventional Commits type (see `references/work-types.md`) |
| `<slug>` | kebab-case short slug, ≤40 chars, derived from the brief title |
| Body format | Markdown, following `references/template.md` exactly |

**Example filename:** `2026-04-23-feat-global-hotkey-system.md`

If `docs/briefs/` does not exist, create it.
If a file with the same name already exists, append `-v2`, `-v3`, … until the path is unique — do not overwrite.

For briefset mode, the parent uses `YYYY-MM-DD-briefset-<set-slug>.md` and children use `YYYY-MM-DD-<type>-<set-slug>-NN-<child-slug>.md`.
See `references/briefset.md` for the parent template and naming rules.

The eight required H2 sections are: `Work Type`, `Current State (As-Is)`, `Desired Outcome (To-Be)`, `Scope` (with `In Scope` / `Out of Scope` H3s), `Related Files / Entry Points`, `Side Effect Checkpoints`, `Acceptance Criteria`, `Open Questions`.
Optional `Constraints` may appear between `Scope` and `Related Files / Entry Points` when task-specific constraints exist.

Three work types require an **additional H2 section** between `Current State (As-Is)` and `Desired Outcome (To-Be)`:

- `fix` → `## Reproduction`
- `perf` → `## Baseline Measurement`
- `refactor` → `## Behavior Contract`

These exist because the work type changes the downstream agent's behavior (reproduction-first, measurement-first, behavior-preservation), and the brief must carry the type-specific input that behavior depends on.
The escape hatch when the section legitimately has nothing concrete to capture is a single bullet `- N/A — <reason>`.
See `references/template.md` and `references/work-types.md` for the per-section guidance.

Bullet count is not capped.
The rule is cohesion plus completeness, not brevity:

- Each bullet should describe one coherent unit of context, scope, risk, or verification.
- **Enumerate every distinct concern.** If the input or the Stage 3 codebase review surfaces N distinct concerns that map to a section, the section gets ≥ N bullets.
  Sections expand to fit the work; they are not capped.
  A section reduced to one bullet when the input contained multiple concerns for it is the failure mode this rule exists to prevent.
- Do not merge unrelated concerns into one bullet just to keep the document short.
- Write as many bullets as the task needs; do not compress larger work into vague combined bullets.
  Short prose per bullet is fine and encouraged — short *count* is the failure.

---

## Workflow

### Stage 1 — Ambiguity Gate (HALT or CONTINUE)

Before full codebase review, check whether the input contains enough signal to ground the brief.
Use the **four-anchor heuristic**:

| Anchor | What it answers | Maps to |
|---|---|---|
| **PROBLEM** | What is wrong or what is changing? | § Current State (As-Is) |
| **GOAL** | What should be true when it's done? | § Desired Outcome (To-Be) |
| **SCOPE** | Where does this apply (module, feature area, user surface)? | § In/Out of Scope |
| **TARGET** | Which part of the system is touched (file, subsystem, layer)? | § Related Files / Entry Points |

Count how many anchors are derivable from the input.
Derivable = a reasonable engineer could answer the anchor from the user's input without inventing intent.

- **3 or 4 anchors present** → **CONTINUE** to Stage 2.
  Missing detail gets filled in Stage 3 via codebase review or Stage 4 via user questions.
- **PROBLEM + GOAL + SCOPE present, TARGET missing** → run a narrow target probe before deciding.
  Use at most a few `rg` / glob queries to find likely files, directories, routes, commands, or modules.
  If a concrete entry point emerges, **CONTINUE**.
  If not, **HALT** and ask the user for the target area.
- **2 or fewer anchors present** → **HALT**.
  Respond in the user's chat language naming exactly which anchors are missing, and ask for more input.
  Do NOT proceed through Stages 2–6 on an underspecified input.
  The briefset-mode check below also waits — never split an underspecified input into multiple equally underspecified child briefs.
  Example halt messages:

  **English:**
  > I can't ground the brief from this input alone.
  > Missing — **PROBLEM** (what is being fixed or changed) and **TARGET** (which area / file / subsystem is touched).
  > Can you paste the spec or add one or two lines?

  **Korean:**
  > 입력만으로는 브리핑 만들기 어려워.
  > 다음이 아직 확인 안 돼 — **PROBLEM**(뭘 고치거나 바꾸는지)과 **TARGET**(어느 영역/파일/시스템을 건드리는지).
  > 더 얹어줄래?
  > 기획서 붙여넣거나 한두 줄 더 써주면 돼.

**Why halt instead of guess:** an underspecified brief is worse than no brief — the downstream agent commits to the wrong problem framing and the rework cost eats the whole savings.
Pushing back early is cheaper than producing a confident-looking but wrong document.

**Edge case — pasted spec that looks long but is content-light:** word count is not a proxy for the four anchors.
A 2,000-word product narrative without a concrete PROBLEM or TARGET still halts.
Judge by anchor coverage, not length.

See `examples/03-halt-ambiguous.md` for a worked halt case.

**Briefset signal check (after CONTINUE):** once anchors clear, also evaluate whether the input describes multiple execution contexts.
Do not use file count, line count, input length, or several related edit points as triggers by themselves.
Those are supporting evidence only.

If briefset signals are strong, recommend briefset mode and ask the user to choose before Stage 2 instead of switching silently.
Use the user's chat language and keep the question short.
Korean example:

> 다중 브리프로 나누는 것이 권장됩니다.
> 실행 단위가 독립적이고 순서/병렬 조정이 필요해 보입니다.
> 어떻게 진행할까요?
> 1. 다중 브리프로 생성
> 2. 단일 브리프로 유지

If the user chooses briefset, continue with `references/briefset.md`.
If the user chooses single-brief, keep one cohesive brief and document the requested execution ordering in `Constraints` / `Acceptance Criteria` as needed.
If the evidence is unclear, default to single-brief mode and let Stage 4 surface the question.

### Stage 2 — Work Type Selection

Determine the Conventional Commits type.
Consult `references/work-types.md` for the full list and per-type behavior hints.

- If the input explicitly names a type (e.g., "this is a refactor"), use it when the input evidence agrees.
- If the user names a type that conflicts with the described work (e.g., "refactor" but the work changes behavior), pause and confirm with one question before codebase review.
- If the type is implicit but high-confidence, assign a provisional type and include it in the Stage 4 decision table only when user confirmation is still useful.
  Do not add a separate early round-trip just for type confirmation.
- If the implicit type is low-confidence and changes the likely execution approach, ask one short question before proceeding.

See `references/work-types.md` for the full type-confirmation routing table (explicit-agree / explicit-conflict / high-confidence implicit / low-confidence implicit).

### Stage 3 — Codebase Review

The goal is enough context to fill `Current State (As-Is)` and `Related Files / Entry Points`, not exhaustive exploration.
Use whatever code search / read / symbol tooling fits the host environment — default `Grep` / `Read` / `Glob`, semantic tools where available (Serena MCP, ast-grep, language servers), or a short-lived subagent (e.g. `Explore`) when parallel lookups or main-context isolation is worth it.
Tool choice is the runtime's call; this stage only fixes the *purpose* and *budget* of the review.

Review budget (soft limits):

- At most ~15 file reads
- At most ~10 search queries
- Stop when you can confidently enumerate the **primary** entry points and major affected areas implied by the input — not just the first file or symbol that grounds the brief.
  If likely input-implied surfaces remain unverified within the review budget, surface them in `Open Questions` so the downstream agent inherits them rather than having them silently dropped.

Strategy:

1. Start wide with keyword search on terms from the input — feature names, function names, error strings, routes, type names.
2. Narrow to a list of candidate files, then read the 2–4 most promising ones.
3. If the input mentions a subsystem (e.g., "auth middleware", "checkout flow"), look at likely directories first.
4. Capture an As-Is picture by coherent context units: how each relevant function, module, behavior, integration, or user surface is shaped today.
5. Capture concrete Related File / entry-point hints with one-line purposes.
   At least one entry point must be solid before saving the brief.

**Do not:**

- Read entire large files when symbolic / targeted-range reads suffice.
- Chase tangential code just to pad the brief.
  If it does not tighten `Current State (As-Is)` or `Related Files / Entry Points`, skip it.
- Make architectural claims the code does not support.
  If uncertain, flag it in `Open Questions` instead.

### Stage 4 — User Decision Table

After Stage 3 has gathered enough codebase context, collect the remaining ambiguous or user-owned decisions into a Markdown decision table.
Stage 4 is not a pre-review guessing interview: ask only after the codebase has been checked enough to state the uncertainty, the recommended change, and the evidence behind it.

Use this exact table shape for user-decision questions:

```markdown
| 순번 | 내용 | 수정 추천안 | 근거 |
|---|---|---|---|
| 1 | <decision the user must make> | <recommended change to apply to the brief> | <codebase/input evidence and risk> |
```

Keep these four headers exactly as written, even when the surrounding conversation is not Korean.
They are the stable decision-table contract: number, decision content, recommended change, and rationale.

Required gaps to close before drafting:

- **Desired Outcome (To-Be)** — confirm when absent, ambiguous, or when the codebase review suggests more than one plausible interpretation.
- **Work Type** — confirm the provisional type from Stage 2 when it was inferred rather than explicitly provided.
- **Out of Scope** — the most valuable guardrail for the downstream agent.
  Put unclear or high-risk scope boundaries in the decision table with a recommended exclusion/inclusion.
- **Related Files / Entry Points** — confirm at least one concrete entry point if the codebase review did not surface one.
  This section is mandatory because the brief must tell the downstream agent where to start.
- **Acceptance Criteria** — what makes the task verifiably done.
- **Side Effect Checkpoints** — what else must be verified if this area is touched.
  If the list has user-owned tradeoffs, present those tradeoffs in the decision table instead of hiding them in a generic "add/change?" prompt.
- **Open Questions** — explicitly surface anything the codebase review raised that the user should answer, keep in the brief, or delegate to the downstream agent.

**Decision-table rule.** Each row must be a real decision, not a vague status note.
`내용` states what the user must decide.
`수정 추천안` states the concrete brief change you recommend.
`근거` cites the input, codebase finding, existing pattern, or risk.
After the user answers, patch the draft plan in memory before composing the brief.
Full decision classification, table rules, and termination rules live in `references/stage-4-interview.md`.

### Stage 5 — Save + Validate

Once Stage 4 closes, compose the final Markdown internally and **write it straight to disk** — do not paste the full brief into chat first.
The user reviews the file in their editor in Stage 6, where real markdown rendering and diff tooling are available.

1. Compute the filename per the **Output Contract** above.
2. Ensure `docs/briefs/` exists; create it if not.
3. Resolve filename collisions by appending `-v2`, `-v3`, ….
4. Render the complete template from `references/template.md` and write the file (English section headers, English body).
5. **Run the structural validator** — a fast smoke test for the template contract:

   ```bash
   python3 skills/task-brief-creator/scripts/validate_brief.py \
     docs/briefs/<filename>.md
   ```

   - Exit **0** → proceed to Stage 6 with a "passed" banner.
   - Exit **1** (structural failure) → **leave the file in place**.
     Do not delete or silently rewrite it.
     Carry the failed checks into Stage 6 so the user can see what tripped and decide how to fix.
   - Exit **2** (file I/O error) → the save did not actually land; investigate and retry.

   The validator only checks **structural** conformity (section presence, checklist format, filename pattern, type coherence).
   It does *not* judge content quality — that's what the Stage 5.5 self-check and the human review in Stage 6 are for.
   Passing validator ≠ good brief; failing validator = malformed brief.

### Stage 5.5 — Content-Level Self-Check

The structural validator confirms the file has the required sections.
It does not confirm the file is a *complete* work instruction.
Before handing off in Stage 6, re-read the saved brief from disk and run a content-coverage self-check against the original input plus Stage 3 / Stage 4 findings.

The brief is a work instruction, not a summary.
Any concern that existed in the input must survive into the brief — possibly reshaped into the right section, never silently dropped.
Run this checklist:

- [ ] **Input coverage:** every distinct concern named in the input, including referenced spec section headings that change the coding route, maps to at least one bullet somewhere in the brief (In Scope, Out of Scope, Related Files, Constraints, Side Effect Checkpoints, Acceptance Criteria, or Open Questions, depending on the concern's shape).
  If a spec section is intentionally not implemented now, it appears in `Out of Scope` as `[hard]` or `[deferred]`, or in `Open Questions` when the user must decide.
  Two unrelated implementation or verification obligations are never merged into one bullet.
- [ ] **Stage 3 coverage:** every primary entry point or major affected area surfaced during the codebase review appears in `Related Files / Entry Points`, and every uncertainty raised by the review either appears in `Open Questions` or was explicitly resolved during Stage 4.
- [ ] **Section depth:** no section was reduced to a single bullet when the input or Stage 3 findings contain multiple distinct concerns for it.
  Sections expand to fit the work; they are not capped.
- [ ] **No content compression:** no bullet was shortened by dropping qualifiers, quantities, units, thresholds, versions, environment conditions, or ordering words (`only on cold start`, `≤ 5KB gzipped`, `iOS Safari 17+`, `after move end`).
  "Executable, not discursive" is a *prose* rule, not a *content* rule.
- [ ] **Cold-pickup test:** a downstream coding agent reading only the brief can act on the first 30 minutes of the task without re-interviewing the requester.
  If a re-interview would be needed, identify the thin section and patch it.

If any check fails, fix the brief in place with `Edit`, then re-run `scripts/validate_brief.py` to confirm structural conformity still holds.
Loop the self-check until every item passes.

The self-check outcome is a separate signal from the structural validator — both are reported in Stage 6.
A brief can pass structural validation and still fail this self-check; in that case the file is incomplete even though it is well-formed.

For briefset mode, run the self-check on the parent and on every child independently.
The parent's coverage check asks whether every input-implied execution context maps to a child; each child's coverage check uses the same five items above.

### Stage 5.6 — Cold-Pickup Sub-Agent Verification

The Stage 5.5 self-check is self-evaluated — the same agent that wrote the brief grades it for cold-pickup readiness.
That is biased.
An untouched sub-agent reading **only the original input and the saved brief** is the truthful version of the cold-pickup test.

Stage 5.6 is **default ON**.
The user can skip it with an explicit opt-out — see the `## Cold-Pickup Verification (Stage 5.6)` section below for the trigger words.

Mechanism:

1. Spawn an `Explore` or `general-purpose` sub-agent.
2. Hand it **only the original user input or planning notes plus the brief path** — no Stage 3 uncertainty register, no Stage 4 decisions, no suspected gaps, no decomposition rationale, and no Stage 5.5 result.
   Do not include hints such as what to inspect, what might be missing, or which split you expect the sub-agent to prefer.
   For briefset mode, hand the parent and every child path one at a time; each file runs its own cold-pickup pass.
3. Ask the sub-agent to report exactly four things:
   1. **First 3 concrete actions** — the file it would open, the search it would run, the hypothesis it would test before writing any code.
   2. **Ask-back items** — anything it would ask the requester back before starting.
   3. **Missing or under-specified concerns** — concerns it suspects are missing or specified too thinly to act on.
   4. **Confidence (1–5)** that it can complete the task without re-interviewing.
4. Diff the sub-agent's report against the original input + Stage 3 uncertainty register + Stage 4 decisions.

**Drift handling.** When the sub-agent surfaces drift — an ask-back the brief should have answered, a concern the brief omitted, or a confidence < 4 — `Edit` the saved brief in place to close the gap, re-run `validate_brief.py`, and re-run cold-pickup **at most once more**.
Two cold-pickup passes is the hard cap; do not loop further.

**Pass conditions:**

- Confidence ≥ 4, **and**
- No ask-back maps to a concern that was already present in the input or resolved during Stage 4.

**Disagreement vs drift.** The sub-agent sees the original input and the brief but not the Stage 3 register or Stage 4 decisions, so it cannot know which items the user locked.
The main agent classifies each ask-back before deciding to patch:

- If the ask-back's subject matches the `내용` of a row in the Stage 4 decision table that the user answered, treat it as **disagreement** — chat-only comment, no patch.
- Otherwise treat it as **drift** — patch in place per the drift-handling rule above.

Cold-pickup never overrides user decisions, never invents Acceptance Criteria, never silently rewrites Open Questions.

**Reporting.** The cold-pickup outcome integrates into the Stage 6 save banner alongside the structural validator and the Stage 5.5 self-check.
For briefset mode, the banner uses the collapsed `parent + K/N children` format defined under `## Cold-Pickup Verification (Stage 5.6)` below — one summary line plus details only on flagged children, not one line per child.

### Stage 6 — Review + Iterate

The brief is on disk.
Hand off to the user for review.

1. Report the path, a one-line summary (work type + title), the structural validator result, the Stage 5.5 self-check result, **and the Stage 5.6 cold-pickup result**.
   Use the user's chat language.
   All three signals are reported together so the user can see whether the file is well-formed, complete, *and* cold-pickup-ready.

   **English (validator + self-check + cold-pickup passed):**
   > Saved — `docs/briefs/2026-04-23-feat-dark-mode-settings.md` (`feat`: Dark mode toggle in Settings; structural validation passed; content self-check passed — N input concerns covered; cold-pickup passed (confidence 5/5; no ask-backs)).
   > Open it and let me know if anything needs editing.

   **Korean (validator + self-check + cold-pickup passed):**
   > 저장 완료 — `docs/briefs/2026-04-23-feat-dark-mode-settings.md` (`feat`: Dark mode toggle in Settings; 구조 검증 통과; 내용 자체 검증 통과 — 입력 항목 N개 모두 매핑됨; cold-pickup 통과 (confidence 5/5; ask-back 없음)).
   > 파일 열어보고 고칠 부분 있으면 알려줘.

   **English (validator failed):**
   > Saved — `docs/briefs/2026-04-23-feat-dark-mode-settings.md`, but the structural validator flagged 2 issue(s): ✗ <first failure verbatim> ✗ <second failure verbatim> The file is on disk.
   > Want me to patch these, or will you edit directly?

   **Korean (validator failed):**
   > 저장 완료 — `docs/briefs/2026-04-23-feat-dark-mode-settings.md`, 다만 구조 검증에서 2건 지적: ✗ <첫 번째 실패 메시지 그대로> ✗ <두 번째 실패 메시지 그대로> 파일은 디스크에 있음.
   > 내가 패치할까, 직접 고칠래?

   When the structural validator fails, Stage 5.5 and Stage 5.6 are **skipped** — the brief is not yet well-formed enough to run content or cold-pickup checks against.
   The banner stays as shown; do not append `self-check skipped` / `cold-pickup skipped` lines in this case.

   If the structural validator passed but the Stage 5.5 self-check surfaced gaps that you fixed in place, mention what you patched so the user knows the brief was tightened before handoff (e.g., "self-check found 2 input concerns missing from In Scope; added them, re-validated").
   If Stage 5.6 patched the brief after cold-pickup drift, report it the same way (e.g., `cold-pickup flagged 2 gap(s); patched in place`).
   If the user opted out, report `cold-pickup skipped per user request`.

2. If the user requests changes, apply them with `Edit` against the on-disk file.
   Do **not** re-render the full brief into chat — that defeats the point of save-then-review.
   Re-run the validator after each edit pass and report the delta.

3. If the saved single brief contains `Open Questions` that require a user decision, present them immediately after the save report using the same four-column decision table from Stage 4:

   ```markdown
   | 순번 | 내용 | 수정 추천안 | 근거 |
   |---|---|---|---|
   | 1 | <Open Question requiring user decision> | <recommended patch to apply to the brief> | <why this cannot be delegated safely> |
   ```

   After the user answers, patch the saved brief in place, move resolved questions into the appropriate sections, leave only genuinely unresolved or delegated questions in `Open Questions`, and re-run the validator plus Stage 5.5 self-check.

4. The user owns "done." Do not stage or commit the file.
   Loop on Stage 6 until they explicitly stop.

**Why save-then-review:** an earlier iteration rendered the full brief in chat for approval *before* writing to disk.
In hands-on use that flooded the conversation with markdown that renders poorly inside a code fence and was awkward to edit conversationally.
Writing to disk first lets the user review in their editor (real markdown, real diff tools, real inline edits) and lets the validator surface structural issues immediately.
The tradeoff — a file briefly on disk before approval — is neutral: `docs/briefs/` is the intended home for these files, and the commit step stays with the user.

---

## Template

See `references/template.md` for:

- The exact eight-required-section Markdown template.
- Per-section writing guidance (what good looks like, what not to write).
- Worked example of a filled brief.

The emitted brief is in English.
Chat interaction language follows the user's input.

---

## Work Types

See `references/work-types.md` for:

- The ten Conventional Commits types.
- Per-type agent behavior hints (why the type matters — it changes how the downstream coding agent approaches the work).
- Classification tips for ambiguous cases.

---

## Examples

See `examples/` for worked end-to-end scenarios (input → codebase review → interview → output).
Start with `examples/README.md` for the index.

---

## Structural Validator

`scripts/validate_brief.py` is a stand-alone Python 3 script (no external deps) that verifies structural conformity of a saved brief.
It is wired into Stage 6 but can also be run ad-hoc against any existing brief:

```bash
python3 skills/task-brief-creator/scripts/validate_brief.py \
  docs/briefs/2026-04-23-feat-global-hotkey-system.md
```

Exit codes: `0` pass, `1` structural failure, `2` file I/O error.

Scope of the validator (deliberately structural only):

- Filename pattern, title format, type coherence across filename / title / section value, and slug length.
- Presence of required H2 sections + `In Scope` / `Out of Scope` H3s.
- Type-conditional section (`Reproduction` / `Baseline Measurement` / `Behavior Contract`) present and populated for the matching type.
- Bullet content in narrative sections; `- [ ]` format in checklist sections; populated `Open Questions` with `- None — <reason>` when no questions remain.
- Inline-code paths under `Related Files / Entry Points` resolve on disk (skipped when the bullet carries a `(proposed)` marker).
- Optional `Constraints` heading shape.
- Warning only: `Out of Scope` bullets without `[hard]` or `[deferred]` classification.
  The validator does not judge whether the classification is semantically correct.

Out of scope (still on the human): concreteness of bullets, whether Out-of-Scope entries are real guardrails vs. filler, whether entry points are *good* (the path-existence check only catches fabricated paths, not poorly-chosen ones), whether Acceptance Criteria are measurable, whether the type-conditional section's content is sufficient.

For briefset mode, use `scripts/validate_briefset.py` on the parent file — it validates the parent structure and re-runs `validate_brief.py`'s checks transitively on every referenced child brief, so one invocation covers the whole set:

```bash
python3 skills/task-brief-creator/scripts/validate_briefset.py \
  docs/briefs/2026-04-30-briefset-checkout-i18n.md
```

Same exit codes.
See `references/briefset.md` for what the parent validator checks and what stays on the human reviewer.

---

## Cold-Pickup Verification (Stage 5.6)

Stage 5.6 spawns an `Explore` or `general-purpose` sub-agent that reads only the original user input or planning notes plus the saved brief, then reports its first 3 actions, ask-back items, missing concerns, and confidence (1–5).
The main agent diffs that report against the original input + Stage 3 register + Stage 4 decisions, patches the brief in place if drift is found, and re-runs the structural validator.

**Default behavior: ON.** Cold-pickup runs automatically after Stage 5.5 passes.

**Opt-out.** The user can skip Stage 5.6 with any of:

- An explicit phrase in the input — `skip cold-pickup`, `cold-pickup off`, `no cold-pickup`, `콜드픽업 건너뛰기`, `콜드픽업 끄기`, `cold-pickup 생략`.
- A flag-style hint — `--no-cold-pickup` or equivalent.
- Any other phrase that unambiguously opts out of cold-pickup verification — when in doubt, confirm with one short question before skipping.

When the user opts out, Stage 5.6 is bypassed cleanly and the Stage 6 save banner reports `cold-pickup skipped per user request`.

**Loop cap.** A maximum of two cold-pickup passes per brief.
If drift remains after the second pass, surface the residual gaps in Stage 6 as comments for the user rather than continuing to patch.

**Briefset cost note.** In briefset mode the total spawn count is `parent + N children`, multiplied by up to `2×` when drift triggers a retry.
For a wide briefset (≥ 5 children) this becomes the most expensive Stage 5.6 case — recommend the user opt out for that briefset, or run Stage 5.6 only on the parent and a sample of children, when cost matters.

**Briefset reporting (Stage 6 banner).** Per-child cold-pickup status is collapsed to one summary line plus details only on flagged children, not one line per child:

- Pass-everything case: `cold-pickup: 1/1 parent + N/N children passed (avg confidence X/5; no ask-backs)`.
- Mixed case: `cold-pickup: 1/1 parent passed, K/N children passed, M flagged — see chat for details`, then list the flagged child paths and the specific drift items below.

**What cold-pickup never does:**

- Override a Stage 4 decision the user already locked.
- Invent Acceptance Criteria, Side Effect Checkpoints, or Out-of-Scope guardrails the input did not imply.
- Silently rewrite `Open Questions` — drift fixes either resolve a question into another section or leave the question intact for the user.

## Guardrails

- **Executable, not discursive.** The emitted document is a work instruction, not a memo about the work.
  If any section reads like a discussion summary, scope-negotiation log, planning note, or rationale essay, rewrite it until it directs concrete action.
  Prose that explains *why we are thinking about this* belongs in the PR description, not the brief.
- **Never fabricate file paths or PR numbers.** `Related Files / Entry Points` is mandatory because it is the downstream agent's starting route.
  If the codebase review does not surface at least one concrete file, directory, route, command, module, related brief, or confirmed proposed path, ask the user to provide or confirm the entry point before saving the brief.
- **Never infer Acceptance Criteria from thin air.** Vague criteria poison the downstream agent.
  Ask the user.
- **Never proceed past the Ambiguity Gate on a hunch.** Halting is the correct answer when anchors are missing.
- **Keep Out-of-Scope specific.** "Don't refactor unrelated code" is filler.
  "Do not change the `PaymentService` interface" is a real guardrail.
- **Keep implementation judgment out of Out-of-Scope.** `Out of Scope` tells the downstream coding agent what not to do.
  Put bounded implementation choices in `Constraints`, and user-owned unresolved choices in `Open Questions`.
- **One brief per invocation, unless the input has multiple execution contexts.** If it does, recommend briefset mode and ask the user to choose (see `references/briefset.md`).
  Briefset mode is the supported way to handle multi-context work — do not stuff multiple unrelated tasks into a single brief unless the user explicitly chooses single-brief after the recommendation, and do not nest briefsets (a child cannot become a parent).
- **Decision table does not bypass the ambiguity gate.** Halt-eligible inputs still halt at Stage 1.
  Do not try to reconstruct missing PROBLEM / GOAL / SCOPE / TARGET through a large decision table — the gate exists precisely to prevent that failure mode.
  See `references/stage-4-interview.md` for the table rules and termination conditions.

---

## Pre-Save Checklist

Self-check before invoking `Write` in Stage 5.
The structural validator catches format errors after the fact; this list catches content gaps it cannot see.

- [ ] Filename matches `YYYY-MM-DD-<type>-<slug>.md`.
- [ ] `<type>` is one of the ten Conventional Commits types.
- [ ] Title on line 1 starts with `[<type>]`.
- [ ] `Current State (As-Is)` and `Desired Outcome (To-Be)` are both populated and distinguishable.
- [ ] If type is `fix` / `perf` / `refactor`, the type-conditional section (`Reproduction` / `Baseline Measurement` / `Behavior Contract`) is present and populated — `- N/A — <reason>` if genuinely none.
- [ ] `Out of Scope` has at least one specific entry (or an explicit "None — self-contained." with rationale).
  Use `[hard]` for must-not-touch guardrails and `[deferred]` for follow-up work when the distinction matters.
- [ ] `Acceptance Criteria` are measurable (checkable, not aspirational).
- [ ] `Related Files / Entry Points` entries are existing repo paths, verified references, or confirmed proposed paths.
  Paths under inline-code that are not yet created carry a `(proposed)` marker so the structural validator does not flag them as fabricated.
  Each entry routes the agent's first read or first edit, not just "related file" context.
- [ ] `Open Questions` uses `- None — <reason>` only if the brief is genuinely unambiguous; otherwise populate it with real questions.
- [ ] Cold-pickup verification ran (or user opted out).
