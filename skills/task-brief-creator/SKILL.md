---
name: task-brief-creator
description: >
  Generate an executable implementation work-plan Markdown at `docs/briefs/`
  from planning notes or a rough task description. Work brief, task brief,
  handoff brief, implementation ticket, and task spec remain trigger aliases.
  Nine required sections are keyed to Conventional Commits types so coding agents switch behavior
  (refactor → preserve, fix → reproduce first, perf → measure first).
  Briefset mode emits a parent execution-management document plus N child
  briefs when the input describes multiple execution contexts.
  Manual trigger only — use when the user explicitly invokes this skill or
  asks for a work plan, implementation plan, work brief, task brief, handoff brief,
  implementation ticket, or task spec for a coding agent. Not for prose summaries, status
  reports, design docs, or meeting notes. For the plain-language caveman
  variant, use task-brief-creator-caveman instead.
---

# Task Brief Creator

Produce an executable implementation work plan under `docs/briefs/` that one coding agent authors and another coding agent can execute without reconstructing the route or re-interviewing the requester.
The historical work-brief and handoff names remain activation aliases; the saved artifact's primary identity is a code-execution PLAN.

The plan is the *execution artifact*.
Its job is to let a coding agent recover the first stage, intended order, stage deliverables and handoffs, replan boundaries, and whole-work completion criteria — while routing it to the right files and fixing the behavior envelope.

**The plan is an executable work instruction — nothing else.** It is not a scope-control memo, discussion summary, background briefing, or rationale document.
Every section must answer *"what does the coding agent do next?"* — if a section reads like meeting minutes, negotiation history, or context prose, rewrite it until it routes to files, decisions, or verifiable outcomes.
A plan that makes the coding agent reconstruct its execution sequence or re-interview the requester is a **failed plan**, regardless of how polished it reads.

**"Executable, not discursive" is a *prose style* rule, not a *content reduction* rule.** It tells you how each bullet should read — direct, action-routing, no rationale prose.
It does not tell you to *drop* distinct concerns, *merge* unrelated bullets, or *summarize* the input down to its highlights.
A brief that omits a concern from the input is also a failed brief, because the downstream agent will silently miss it.
Tight prose, full enumeration: short bullets are fine and encouraged, but every distinct concern from the input and the codebase review must land somewhere in the brief.

---

## Modes

This skill operates in one of two **output modes**:

- **Single-plan mode** (default; historical single-brief name remains) — emits one executable work plan per invocation.
  The workflow below covers this case end to end.
- **Briefset mode** — emits a parent execution-management document plus N independently executable child briefs.
  Used when the input describes **multiple execution contexts** that need coordination (independent completion criteria, mixed work types, ordered dependencies, parallelizable waves, or shared conflict hotspots).
  Selected by the criteria in `references/briefset.md`; long input, many files, or many related edit points alone never trigger briefset mode.

Output-mode selection happens at Stage 1 alongside the ambiguity gate and is author-owned when the input and codebase make it evident.
In briefset mode, follow the workflow below with the per-stage adaptations in `references/briefset.md` (parent template, naming, decomposition decision table, dual-validator save).

**Stage 4 always runs an ownership pass.** When user-owned decisions remain after codebase review, present only those decisions in a Markdown table with `순번`, `내용`, `수정 추천안`, and `근거`.
Codebase-resolvable facts, output mode, evident work type, and reversible implementation choices are decided by the author or worker; product intent, scope, compatibility breaks, external ownership, and acceptance thresholds remain user-owned.
The decision table is the output of the ownership pass when it has rows, not a separate mode.
See `references/stage-4-interview.md` for the full decision classification, codebase-precedence, and termination rules.

---

## Code Agent Operating Path

Load references only when their decision point arrives:

1. Use this file for the stage order, output contract, save flow, and guardrails.
2. Read [references/work-types.md](references/work-types.md) during Stage 2 when the work type is not obvious or when the type changes downstream behavior.
3. Read [references/briefset.md](references/briefset.md) during Stage 1 when multiple execution contexts are plausible.
4. Read [references/bloat-decomposition.md](references/bloat-decomposition.md) only after a candidate child brief is independently executable but still looks oversized or mixed.
5. Read [references/stage-4-interview.md](references/stage-4-interview.md) before presenting user-owned decisions.
6. Read [references/template.md](references/template.md) while composing the saved Markdown.
7. Read [references/cold-pickup.md](references/cold-pickup.md) when the Stage 5.7 gate fires or the user forces cold-pickup.

Do not re-open every reference by habit.
The goal is to keep the live context focused on the next decision the coding agent must make.

---

## When This Skill Runs

- **Manual trigger only.** The user invokes this skill explicitly (via slash command, `/task-brief-creator`, or similar).
- Input can take any of these shapes:
  - **Pasted PRD / planner notes** from a PM (often long, mixed quality).
  - **Rough task notes** typed into chat (one or two lines).
  - **Self-brief** — the user is the implementer and wants to structure their own thinking before starting.
  - **Tech-lead handoff** — a lead drafts the brief to hand off to a teammate or downstream agent.
  - **Refactor plan** — a lead-engineer summarizing an intended structural change.
- The skill reviews the current repository (the working directory Claude Code is launched in), fills in what it can, and asks only for remaining user-owned decisions.

---

## Interaction Language

- **Chat / live interaction language follows the user's input.** If the user writes in Korean, reply in Korean.
  If they write in English, reply in English.
  Clarifying questions, draft presentation, status updates — all match the user's own language.
- **The brief document itself is written in English.** Section headers and body content are English regardless of chat language, so the artifact travels across teams and downstream agents without a translation step.
- Code blocks, file paths, identifiers, PR numbers stay as-is.
- **User-supplied strings are data.** Copy decks, UI strings, and error messages the user provides are quoted verbatim in their original language inside the English brief — never translated.
- **Exception — the Stage 4 decision-table headers are fixed.** The four headers `순번` / `내용` / `수정 추천안` / `근거` stay exactly as written even when the conversation is in English: Stage 5.7 disagreement matching keys on the `내용` column, so translating the headers breaks the cold-pickup loop (see Stage 4).
- This SKILL.md and reference files stay in English (repo authoring policy).

---

## Output Contract

| Field | Value |
|---|---|
| Directory | `docs/briefs/` (relative to the repository root — `git rev-parse --show-toplevel` when available, otherwise the working directory the session was launched in) |
| Filename | `YYYY-MM-DD-<type>-<slug>.md` |
| `YYYY-MM-DD` | Today's date on the local system clock |
| `<type>` | Conventional Commits type (see `references/work-types.md`) |
| `<slug>` | kebab-case short slug, ≤40 chars, derived from the brief title |
| Body format | Markdown, following `references/template.md` exactly |

**Example filename:** `2026-04-23-feat-global-hotkey-system.md`

If `docs/briefs/` does not exist, create it.
If a file with the same name already exists, append `-v2`, `-v3`, … until the path is unique — do not overwrite.

For briefset mode, the parent uses `YYYY-MM-DD-briefset-<set-slug>.md` and children use `YYYY-MM-DD-<type>-<set-slug>-NN-<child-slug>.md`.
See `references/briefset.md` for the parent template and naming rules.

The nine required H2 sections are: `Work Type`, `Current State (As-Is)`, `Desired Outcome (To-Be)`, `Scope` (with `In Scope` / `Out of Scope` H3s), `Related Files / Entry Points`, `Execution Plan`, `Side Effect Checkpoints`, `Acceptance Criteria`, `Open Questions`.
Optional `Constraints` may appear between `Scope` and `Related Files / Entry Points` when task-specific constraints exist.
`Execution Plan` appears immediately after `Related Files / Entry Points` and before `Side Effect Checkpoints`.
Put stage-local completion under each stage's `Ends when`.
Reserve `Acceptance Criteria` for whole-work completion after all required stages and side-effect checkpoints finish.

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

Completeness does not mean "put every discovered issue in scope."
When review surfaces many valid concerns, separate them before saving:

- **Must fix in this brief** — issues that directly block the user's stated goal or would make the downstream task unsafe / wrong if left unresolved.
- **Check while here** — nearby contract or documentation consistency checks that are cheap and directly connected to the must-fix work.
- **Defer / record** — valid follow-up issues that do not have to change for this brief to succeed.

`In Scope` should usually hold the must-fix set plus tightly coupled checks, not the whole discovery list.
Record deferred items in `Out of Scope` as `[deferred]`; use `Open Questions` only for non-blocking user-owned decisions with a safe default and reconfirm milestone.
If more than five independent must-fix concerns remain after this triage, reconsider briefset mode or ask the user to choose the first slice only when slicing is a user-owned scope decision.

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

- **All 4 anchors present** → **CONTINUE** to Stage 2.
- **3 anchors present, TARGET missing** → run a narrow target probe before deciding.
  Use at most a few `rg` / glob queries to find likely files, directories, routes, commands, or modules.
  If a concrete entry point emerges, **CONTINUE**.
  If not, **HALT** and ask the user for the target area.
- **3 anchors present, PROBLEM or GOAL or SCOPE missing** → **CONTINUE** only when the missing anchor can be stated in one concrete sentence derived from the input (write that sentence into the brief; vague fillers like "make it better / cleaner" do not count).
  Otherwise **HALT** and ask for that anchor.
  Detail that survives this check gets filled in Stage 3 via codebase review or Stage 4 via user questions.
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

If briefset signals are strong, select briefset mode and state the evidence before Stage 2.
If the candidate contexts are fully independent — no ordering, dependencies, or shared conflict hotspots — select separate single-plan invocations instead: a parent whose coordination sections are all `- None — <reason>` adds overhead without value.
If the evidence is unclear, default to single-plan mode.
Ask only when output topology depends on a user-owned delivery boundary, release unit, or scope choice; do not ask the user to choose a document shape when code and input already settle it.
Several stages inside one cohesive execution context do not justify briefset mode; consult `references/bloat-decomposition.md` before splitting an oversized candidate.

### Stage 2 — Work Type Selection

Determine the Conventional Commits type.
Consult `references/work-types.md` for the full list and per-type behavior hints.

- If the input explicitly names a type (e.g., "this is a refactor"), use it when the input evidence agrees.
- If the named type conflicts with the described outcome, classify by the outcome and record the mismatch; ask only if resolving it requires a user-owned behavior or scope decision.
- If the type is implicit but high-confidence, assign it without a confirmation round-trip.
- If the implicit type is low-confidence but technically resolvable, probe the codebase or put the distinction into the first `Execution Plan` stage as an investigation with a `Replan when` boundary.
- Ask in Stage 4 only when the work type depends on an underlying product or scope choice the user owns; derive the type from that answer.

See `references/work-types.md` for the full author-selection routing table.

### Stage 3 — Codebase Review

The goal is enough context to fill `Current State (As-Is)` and `Related Files / Entry Points`, not exhaustive exploration.
Use whatever code search / read / symbol tooling fits the host environment and repository guidance — default `Grep` / `Read` / `Glob`, allowed semantic tools, language servers, or a short-lived subagent (e.g. `Explore`) when parallel lookups or main-context isolation is worth it.
Tool choice is the runtime's call; this stage only fixes the *purpose* and *budget* of the review.

Review budget (soft limits):

- At most ~15 file reads
- At most ~10 search queries
- Stop when you can confidently enumerate the **primary** entry points and major affected areas implied by the input — not just the first file or symbol that grounds the brief.
  If likely input-implied surfaces remain unverified within the review budget, add a bounded investigation stage with a named deliverable and `Replan when` condition.

Strategy:

1. Start wide with keyword search on terms from the input — feature names, function names, error strings, routes, type names.
2. Narrow to a list of candidate files, then read the 2–4 most promising ones.
3. If the input mentions a subsystem (e.g., "auth middleware", "checkout flow"), look at likely directories first.
4. Capture an As-Is picture by coherent context units: how each relevant function, module, behavior, integration, or user surface is shaped today.
5. Capture concrete Related File / entry-point hints with one-line purposes.
   At least one entry point must be solid before saving the brief.

Active judgement:

- Let the user's goal drive any extra probing.
  If the first code reads surface a nearby signal that could change the work direction — a dependency, style hook, comment, product doc, older brief, or unused surface that clearly belongs to the same feature — check just enough to decide how it affects the brief.
  Do not turn this into a mandatory repo-wide audit.
- Prefer a reasoned recommendation over asking the user.
  If a nearby signal is relevant but not required for the requested slice, encode the judgment in `Constraints`, `Out of Scope` as `[deferred]`, `Side Effect Checkpoints`, or `Acceptance Criteria`.
  Ask only when the choice changes product behavior, scope, ownership, or acceptance in a way the requester must own.
- Separate implementation completion from user / operator success when both exist.
  Code may already expose a pass condition, event, return value, validator status, or stored state that says "done"; the user-facing or operator-facing success may be different.
  Capture both when they matter: put the existing pass condition in `Current State (As-Is)` / `Side Effect Checkpoints`, and put the intended observable outcome in `Desired Outcome (To-Be)` / `Acceptance Criteria`.
- If a nearby signal is weak, mention it in the Stage 6 save report instead of bloating the brief.
  The brief stays executable; the report can carry useful "noticed while reviewing" context.

Evidence discipline:

- Mark load-bearing findings as **confirmed** when the codebase review directly verified them.
  A confirmed finding cites the file and a stable locator: section heading, function / class name, validator message, command output, or nearby quoted token.
  Line numbers are useful as secondary hints, but do not rely on line numbers alone because they drift after edits.
- Mark risk statements as **inferred** when they describe likely downstream behavior rather than a fact already present in a file.
  Name what would confirm the inference, such as a validator fixture, an execution-reconstruction check, or a specific command.
- Do not write an inferred risk as if it were a confirmed defect.
  The saved brief may stay concise, but the wording must let the downstream agent tell evidence from judgment.
- Prefix every load-bearing `Current State (As-Is)` bullet with `[confirmed]` or `[inferred]`.
  The validator checks the label shape only; Stage 5.6 and human review own the truthfulness of the classification.

Contract discipline:

- Name the existing contracts that must keep speaking the old shape while the change lands.
  Contracts can be public APIs, persisted ids, database rows, event names, config keys, file formats, CLI flags, i18n keys, analytics events, generated schemas, or cross-process payloads.
- Put contract-preservation facts in `Constraints` or `Side Effect Checkpoints`, not as vague `Out of Scope` filler.
  Good: `- [ ] Existing saved sessions with status "pending" still deserialize.`
  Bad: `- [ ] Do not break compatibility.`
- If the requested outcome requires changing a contract, surface the compatibility choice in Stage 4 unless the user already explicitly approved the break.

**Source-of-truth inputs.** When the user provides a checklist, TODO file, review rubric, audit notes, or any document as the source of truth, do not turn it into a representative summary.

- Treat each listed item as a required concern until it is mapped, explicitly deferred / out of scope, or represented as a non-blocking user-owned Open Question with a safe default.
- Preserve the source's own dimensions, such as named variants, files, examples, sections, or checklist groups.
  Do not collapse them unless the user asks for a summary rather than an executable brief.
- Use searches only for literal terms that come from the user's source document or the target files being reviewed.
  Do not invent generic banned-pattern searches unless the user, repository rules, or source document defines those patterns.
- The saved brief does not need to expose an internal ledger, but Stage 5.6 must be able to trace each source item to a concrete bullet or checklist item.

If the source document is long, keep a private coverage ledger during review.
The ledger does not need to be saved, but every source item must end as one of: in scope, out of scope / deferred, execution stage, acceptance criterion, side-effect checkpoint, related file, constraint, or structured non-blocking open question.

**Do not:**

- Read entire large files when symbolic / targeted-range reads suffice.
- Chase tangential code just to pad the brief.
  If it does not tighten `Current State (As-Is)` or `Related Files / Entry Points`, skip it.
- Make architectural claims the code does not support.
  If uncertain, label it `[inferred]` and route confirmation into an investigation stage or `Replan when` boundary.

**Already-satisfied gate.** Before Stage 4, compare the full requested outcome and acceptance boundary against current code plus current verification signals.

- If all requested outcomes are confirmed, all acceptance checks already hold, and no edit, integration, migration, or evidence-producing work remains, create no plan.
  Report `no-work-needed` in the user's language with the inspected paths, verification action, and observed signal, then stop.
- If the user explicitly asked for a saved verification record despite the already-satisfied state, create a verification-only plan that expects no edits and records the no-change evidence route.
  Its first stage must also say what happens if the proof fails: stop dependent work, return to the owning plan, activate bounded correction plus re-verification work, then re-run the briefset topology and handoffs before continuing.
- If only part of the outcome is already satisfied, keep the remaining work and make the no-change branch explicit instead of directing an unconditional edit.
- In briefset mode, re-run topology after this gate: zero active children means `no-work-needed`, one means single-plan mode, and two or more retain briefset mode. Follow `references/briefset.md` for the child and handoff rules.

This outcome is called `no-work-needed`; do not confuse it with Stage 5.7's `No-op pass`, which describes a review-loop termination.

### Stage 4 — User Decision Table

After Stage 3 has gathered enough codebase context, run an ownership pass and collect only remaining user-owned decisions into a Markdown decision table.
Stage 4 is not a pre-review guessing interview: ask only after the codebase has been checked enough to state the uncertainty, the recommended change, and the evidence behind it.

Use this exact table shape for user-decision questions:

```markdown
| 순번 | 내용 | 수정 추천안 | 근거 |
|---|---|---|---|
| 1 | <decision the user must make> | <recommended change to apply to the brief> | <codebase/input evidence and risk> |
```

Keep these four headers exactly as written, even when the surrounding conversation is not Korean.
They are the stable decision-table contract: number, decision content, recommended change, and rationale.

User-owned gaps to close before drafting:

- **Desired Outcome (To-Be)** — confirm when absent, ambiguous, or when the codebase review suggests more than one plausible interpretation.
- **Out of Scope** — the most valuable guardrail for the downstream agent.
  Put unclear or high-risk scope boundaries in the decision table with a recommended exclusion/inclusion.
- **Acceptance Criteria** — what makes the task verifiably done.
  If the code has a separate internal completion condition and the user has a separate success condition, carry both instead of collapsing them into one vague criterion.
- **Compatibility and ownership** — ask before breaking a contract or crossing an externally owned boundary.
- **Open Questions** — keep only non-blocking user-owned decisions with a safe fallback and reconfirm milestone.

The author determines output mode, work type, entry points, side-effect checks, and technical sequencing when the input and codebase make them evident.
Technical unknowns become investigation stages, bounded `Worker decision` fields, `Replan when` conditions, constraints, or author-selected defaults.

**Decision-table rule.** Each row must be a real decision, not a vague status note.
`내용` states what the user must decide.
`수정 추천안` states the concrete brief change you recommend.
`근거` cites the input, codebase finding, existing pattern, or risk.
After the user answers, patch the draft plan in memory before composing the brief.
A timeout, cancellation, or no response is not approval: non-blocking rows use their declared safe fallback, remain in structured `Open Questions` form, and proceed; any blocking row halts without writing.
Full decision classification, table rules, and termination rules live in `references/stage-4-interview.md`.

Before writing `Open Questions`:

- Make one active judgement pass.
  Ask: would a downstream coding agent still need to ask the requester what to do, or can the brief make a reasonable call?
- Do not use `Open Questions` to avoid making an implementation recommendation.
  If the answer is a reasonable bounded choice, put it into `Worker decision`, `Constraints`, or the relevant execution stage.
- Keep `Open Questions` for user-owned decisions only.
  Product direction, scope expansion, compatibility breaks, acceptance thresholds, and external ownership can require a question.
- Save a question only when it is non-blocking and use exactly `- [non-blocking] <question> — Default: <safe fallback>; Reconfirm before: <stage or milestone>`.
- If the user has not answered a blocking decision and no safe fallback exists, **HALT** and create no file.
- `Open Questions: None` is acceptable only after this pass.
  It means "a downstream agent can proceed without re-interviewing the requester," not "nothing interesting was found."

### Stage 5 — Save + Validate

Once Stage 4 closes, compose the final Markdown internally and **write it straight to disk** — do not paste the full brief into chat first.
The user reviews the file in their editor in Stage 6, where real markdown rendering and diff tooling are available.

1. Compute the filename per the **Output Contract** above.
2. Ensure `docs/briefs/` exists; create it if not.
3. Resolve filename collisions by appending `-v2`, `-v3`, ….
4. Render the complete template from `references/template.md` and write the file (English section headers, English body).
5. **Run the structural validator** — a fast smoke test for the template contract:

   ```bash
   python3 <skill-dir>/scripts/validate_brief.py docs/briefs/<filename>.md
   ```

   If the brief is stored in an isolated artifact tree while its entry-point paths belong to another checkout, add `--repo-root <repository-root>` before the brief path.

   `<skill-dir>` is the installed skill package directory — the directory containing this SKILL.md (resolve it from wherever this skill was loaded, e.g. `~/.claude/skills/task-brief-creator` or a plugin cache).
   Never assume the user's repository contains the script: the brief lives in the user's repo, the validator lives with the skill.

   - Exit **0** → continue to Stage 5.5; the validator result is reported in the Stage 6 banner.
   - Exit **1** (structural failure) → fix the file and rerun the validator without asking the user.
     If the same structural cause still fails after two repair attempts, leave the file in place and carry the residual failure into Stage 6.
   - Exit **2** (file I/O error) → the save did not actually land; investigate and retry.

   The validator only checks **structural** conformity (section presence, checklist format, filename pattern, type coherence).
   It does *not* judge content quality — that's what the Stage 5.5 execution-reconstruction check, Stage 5.6 self-check, Stage 5.7 cold-pickup, and the human review in Stage 6 are for.
   Passing validator ≠ good brief; failing validator = malformed brief.

### Stage 5.5 — Downstream Execution-Reconstruction Check

After the structural validator passes, run a blind downstream execution-reconstruction check before any cold-pickup verification.
This is not a review prompt and not a rubric-driven validation prompt.
Its purpose is to observe how a fresh coding agent naturally reconstructs the saved plan as work to start.
The explanation must recover the first stage, intended order, each stage's deliverable and addressable handoff, verification input and expected signal when present, any no-change branch, replan boundaries, and the whole-work completion basis after side-effect checks.
This checks direction and executability, not full input coverage; Stage 5.6 remains the coverage and missing-content check.

Spawn a sub-agent and send only a natural work-start request in the user's ordinary style, containing the saved brief path.
For briefset mode, include only the briefset parent path.
Do not include the original user request, Stage 3 findings, Stage 4 decisions, suspected gaps, validation criteria, expected answer format, or any hint about what might be wrong.
Do not ask the sub-agent to "verify", "review", "audit", "compare", or "find missing items".

Example shape only — do not hard-code this sentence:

```text
<brief path> 작업 진행할꺼야. 우선 이 브리프 파일을 확인하고 어떻게 작업할껀지 의도 설명해줘.
```

Compare the sub-agent's natural reconstruction against the user's original request, the saved `Execution Plan`, and any user-locked Stage 4 decisions.
Treat only material drift as a failure:

- The work purpose is different.
- The understood scope is materially wider or narrower.
- The first work direction points away from the intended entry points or workflow.
- The first stage, intended order, stage deliverable, handoff, or replan boundary cannot be recovered.
- Stage-local `Ends when` checks are confused with whole-work `Acceptance Criteria`.
- A user constraint, exclusion, or acceptance threshold is missing from the reconstruction.
- The sub-agent assumes work that the brief did not intend.

If material drift appears, patch the brief in place, re-run the structural validator (`validate_brief.py` for a single brief, `validate_briefset.py` for a briefset parent), and run this downstream execution-reconstruction check again with the same information boundary.
Do not fix drift by changing the sub-agent prompt.
Fix the brief.

This check is mandatory whenever the host can spawn a sub-agent.
Do not downgrade it to a self-check because the brief looks obvious or because Stage 5.6 is clean.
The failure being tested is not "did I cover the input?" but "does a fresh agent naturally read the brief the way I intended?"

If the host cannot spawn a sub-agent, report the execution-reconstruction check as unavailable in Stage 6.
Do not block the workflow waiting for sub-agent support; continue to Stage 5.6 and mark Stage 5.5 as unavailable in the save report.
Do not replace it with a self-check; the point is the downstream agent's natural read.

### Stage 5.6 — Content-Level Self-Check

The structural validator confirms the file has the required sections.
It does not confirm the file is a *complete* work instruction.
Before handing off in Stage 6, re-read the saved brief from disk and run a content-coverage self-check against the original input plus Stage 3 / Stage 4 findings.
This checks whether input and codebase concerns survived into the brief; do not treat a clean Stage 5.5 reconstruction as proof that nothing is missing.

The brief is a work instruction, not a summary.
Any concern that existed in the input must survive into the brief — possibly reshaped into the right section, never silently dropped.
Run this checklist:

- [ ] **Input coverage:** every distinct concern named in the input, including referenced spec section headings that change the coding route, maps to at least one bullet or stage somewhere in the brief (In Scope, Out of Scope, Related Files, Execution Plan, Constraints, Side Effect Checkpoints, Acceptance Criteria, or structured non-blocking Open Questions, depending on the concern's shape).
  If a spec section is intentionally not implemented now, it appears in `Out of Scope` as `[hard]` or `[deferred]`, or in `Open Questions` only when a non-blocking user decision has a safe default.
  Two unrelated implementation or verification obligations are never merged into one bullet.
- [ ] **Source-of-truth coverage:** if the user supplied a checklist, TODO file, review rubric, audit notes, or other source-of-truth document, every listed item is represented in the saved brief, explicitly deferred / out of scope, or saved as a structured non-blocking user question.
  Representative theme coverage is not enough.
- [ ] **Scope triage:** every discovered concern is either must-fix in this brief, a tightly coupled check, explicitly deferred / out of scope, or left for a user decision.
  The brief does not turn a broad review into an unbounded implementation task.
- [ ] **Stage 3 coverage:** every primary entry point or major affected area surfaced during the codebase review appears in `Related Files / Entry Points`, and every technical uncertainty is resolved or routed into an investigation stage, `Worker decision`, or `Replan when` boundary.
- [ ] **Contract preservation:** existing contracts discovered in Stage 3 that must not change are named in `Constraints`, `Side Effect Checkpoints`, or `Acceptance Criteria`; compatibility-sensitive changes are not hidden behind generic wording.
- [ ] **Success split:** when internal completion and user / operator success are different, both are represented; the brief does not treat an event firing, validator passing, or state transition as proof that the user's goal was achieved unless that is actually the goal.
- [ ] **Section depth:** no section was reduced to a single bullet when the input or Stage 3 findings contain multiple distinct concerns for it.
  Sections expand to fit the work; they are not capped.
- [ ] **No content compression:** no bullet was shortened by dropping qualifiers, quantities, units, thresholds, versions, environment conditions, or ordering words (`only on cold start`, `≤ 5KB gzipped`, `iOS Safari 17+`, `after move end`).
  "Executable, not discursive" is a *prose* rule, not a *content* rule.
- [ ] **Evidence clarity:** every load-bearing current-state bullet uses `[confirmed]` or `[inferred]`; confirmed facts cite stable evidence, inferred risks name what will confirm them, and line numbers are not the only locator.
- [ ] **Execution continuity:** Stage 1 has a concrete precondition; stage numbers are consecutive; every stage has a bounded outcome, deliverable, local completion checks, explicit handoff, and replan boundary; each handoff gives the next stage what its `Starts when` requires.
- [ ] **Already-satisfied discipline:** the plan does not force an edit when current evidence already satisfies the requested outcome; full satisfaction exited as `no-work-needed` unless the user explicitly requested a verification record, partial satisfaction has a bounded no-change route, and a failed proof stops dependents and names the correction/re-verification owner.
- [ ] **Verification concreteness:** every named verification action comes from repository evidence or is a bounded inspection, identifies its exact input/target, and states an observable expected signal.
  When success means no matches, the plan also identifies the population being checked so an empty or wrong input cannot pass accidentally.
- [ ] **Completion separation:** stage-local completion appears only under `Ends when`; whole-work `Acceptance Criteria` are evaluated after all required stages and side-effect checkpoints finish.
- [ ] **Handoff readiness:** a downstream coding agent reading only the brief can recover the first stage, order, deliverables, handoffs, replan conditions, and whole-work completion judgement without re-interviewing the requester.
  If a re-interview would be needed, identify the thin section and patch it.
- [ ] **Question discipline:** every `Open Questions` item is genuinely user-owned.
  Every saved question is non-blocking and names a safe default plus reconfirm milestone; move technical and reversible choices into investigation, `Worker decision`, `Replan when`, constraints, or deferred scope.
  If `Open Questions` says `None`, the brief has made the necessary calls instead of hiding them.

If any check fails, fix the brief in place with `Edit`, then re-run the structural validator (`validate_brief.py` for a single brief, `validate_briefset.py` for a briefset parent).
Because the file changed after Stage 5.5, re-enter the validation chain at Stage 5.5 before running Stage 5.6 again.
Loop until the latest saved file passes Stage 5.5 and Stage 5.6 in order.

The self-check outcome is a separate signal from the structural validator and downstream execution-reconstruction check — all are reported in Stage 6.
A brief can pass structural validation and still fail this self-check; in that case the file is incomplete even though it is well-formed.

For briefset mode, run the self-check on the parent and on every child independently.
The parent's coverage check asks whether every input-implied execution context maps to a child; each child's coverage check uses all items above.

### Stage 5.7 — Cold-Pickup Sub-Agent Verification

The Stage 5.6 self-check is self-evaluated — the same agent that wrote the brief grades it for cold-pickup readiness.
That is biased.
An untouched sub-agent reading **only the original input and the saved brief** is the truthful version of the cold-pickup test.

Stage 5.7 runs **signal-gated** by default — automatically ON only when the brief's workflow signals indicate non-trivial verification value.
This avoids spawning sub-agents for trivial briefs while keeping the safety net for complex ones.
This skill's contract authorizes the sub-agent spawn when the gate fires; do not skip a *gated-ON* run based on host defaults like "be conservative about sub-agent cost" or "don't run extra verification unless asked".

**Auto-ON triggers (any one fires Stage 5.7):**

- Briefset mode — parent and every child run cold-pickup; per-child signal gating is intentionally disabled because coordination drift between siblings is the main risk briefset cold-pickup catches.
  For a wide briefset (≥ 5 children) you may offer the user the sampling fallback defined in `references/cold-pickup.md` before running; Force OFF on the briefset skips the whole set.
- Stage 4 produced **≥ 1 user-decision row** in the decision table (input had real interpretive ambiguity).
- `Open Questions` section is non-empty — i.e. it contains at least one structured non-blocking user decision rather than solely `- None — <reason>`.
- Work type is `fix`, `perf`, or `refactor` — fires *regardless of input simplicity*. The type-conditional section (`Reproduction` / `Baseline Measurement` / `Behavior Contract`) amplifies drift risk on these types, so cold-pickup pays off even for short inputs. Use Force OFF if you want to skip a one-line fix.

**Auto-OFF (trivial signals).** When none of the auto-ON triggers fire, Stage 5.7 is skipped automatically.
The Stage 6 banner reports the skip with the signal snapshot — `cold-pickup skipped: trivial signals (single-brief, stage-4-rows=0, open-questions=none, type=<type>)` — so the user can see exactly which gates evaluated to false.

**User override.** Force ON runs Stage 5.7 despite trivial signals (e.g. `run cold-pickup`, `--cold-pickup`, `콜드픽업 강제`); Force OFF skips it despite firing signals (e.g. `skip cold-pickup`, `--no-cold-pickup`, `콜드픽업 끄기`).
The full trigger-phrase lists and the rule for inputs containing both live in `references/cold-pickup.md`.

**Skip on residual validator failure.** Stage 5.7 is skipped only when structural validation still fails after the two repair attempts — the plan is not yet well-formed enough to verify.

Reasons that are **not** valid skips when a gate has fired: token budget, latency, inferred host policy, "the brief looks fine".
If a gate fires and Stage 5.7 is skipped anyway, the Stage 6 banner is wrong and the loop is broken.

**Mechanism — when the gate fires, read `references/cold-pickup.md` (report schema, pass bookkeeping, routing table, termination triggers, banner formats), then:**

1. Snapshot the saved brief for this pass (rollback anchor — see *Pass Bookkeeping and Rollback* in the reference).
2. Spawn an `Explore` or `general-purpose` sub-agent.
   If the host cannot spawn sub-agents, use the *Sub-Agent Unavailable Fallback* in the reference — never silently skip a gated-ON run.
3. Hand it **only the original user input or planning notes plus the brief path** — no Stage 3 uncertainty register, no Stage 4 decisions, no suspected gaps, no decomposition rationale, no Stage 5.5 execution-reconstruction result, and no Stage 5.6 self-check result.
   Do not include hints such as what to inspect, what might be missing, or which split you expect the sub-agent to prefer.
   For briefset mode, the parent pass receives the original input plus the parent path. Each child pass receives the original input, the same parent path, and one child path.
   The parent is a scope-allocation map for the child pass: compare only concerns assigned to that child plus relevant shared constraints, and never patch a sibling-owned concern into the target child.
4. Collect the YAML report (schema and sub-agent rules in the reference) and route it against the original input plus the main agent's Stage 3 uncertainty register and Stage 4 decisions.
   The sub-agent is not responsible for Stage 3 coverage it never saw; Stage 3 coverage remains a Stage 5.6 responsibility.

**Drift handling.** When the report's `verdict` is `needs_changes` or `blocked`, or when any unrejected `ask_backs` / `missing_concerns` survive routing — `Edit` the saved brief in place to close the gap, re-run the structural validator, re-enter Stage 5.5, then Stage 5.6, and only then re-evaluate the Stage 5.7 gate.
Route every `ask_backs[*]` / `missing_concerns[*]` through the routing table in the reference before patching, including the disagreement-vs-drift check against answered Stage 4 rows.
Loop until one of the six termination triggers in the reference fires (Regression, Oscillation, Stable findings, Clean pass, No-op pass, Hard cap — evaluated in that priority order).

Cold-pickup never overrides a Stage 4 decision the user already locked, never invents Acceptance Criteria, Side Effect Checkpoints, or Out-of-Scope guardrails the input did not imply, and never silently rewrites `Open Questions` — drift fixes either resolve a question into another section or leave the question intact for the user.

**Reporting.** The cold-pickup outcome integrates into the Stage 6 save banner alongside the structural validator, Stage 5.5 downstream execution-reconstruction check, and the Stage 5.6 self-check, using the banner phrasings in `references/cold-pickup.md`.
For briefset mode, the banner uses the collapsed `parent + K/N children` format from the reference — one summary line plus details only on flagged children, not one line per child.

### Stage 6 — Review + Iterate

The brief is on disk.
Hand off to the user for review.

1. Report the path and one-line summary, then distinguish **structural validation** from **executability validation**.
   Structural validation is the Stage 5 validator result.
   Executability validation combines the Stage 5.5 execution reconstruction, Stage 5.6 content/execution self-check, and Stage 5.7 cold-pickup result.
   Use the user's chat language.
   All four signals are reported together so the user can see whether the file is well-formed, naturally interpreted as intended, complete, *and* cold-pickup-ready.

   **English (validator + self-check + cold-pickup passed):**
   > Saved — `docs/briefs/2026-04-23-feat-dark-mode-settings.md` (`feat`: Dark mode toggle in Settings; structural validation passed; executability validation passed — execution reconstruction aligned, content/execution self-check passed, cold-pickup terminated with `clean_pass` after 1 pass (no ask-backs, no missing concerns)).
   > Open it and let me know if anything needs editing.

   Banner termination trigger reflects the actual loop outcome — `clean_pass` (normal), `regression`, `oscillation`, `stable_findings`, `no_op`, or `hard_cap`. Any non-`clean_pass` trigger means residual concerns must follow in the banner as bullet items.

   **Korean (validator + self-check + cold-pickup passed):**
   > 저장 완료 — `docs/briefs/2026-04-23-feat-dark-mode-settings.md` (`feat`: Dark mode toggle in Settings; 구조 검증 통과; 실행 가능성 검증 통과 — 실행 경로 복원 일치, 내용/실행 자체 검증 통과, cold-pickup `clean_pass`로 1회 만에 종료 (ask-back 없음, missing 없음)).
   > 파일 열어보고 고칠 부분 있으면 알려줘.

   **English (validator + self-check passed, cold-pickup auto-skipped on trivial signals):**
   > Saved — `docs/briefs/2026-04-23-feat-dark-mode-settings.md` (`feat`: Dark mode toggle in Settings; structural validation passed; executability validation passed — execution reconstruction aligned, content/execution self-check passed, cold-pickup skipped: trivial signals (single-brief, stage-4-rows=0, open-questions=none, type=feat)).
   > Tell me `run cold-pickup` or `--cold-pickup` if you want the sub-agent verification anyway.

   **English (validator still fails after two repair attempts):**
   > Saved — `docs/briefs/2026-04-23-feat-dark-mode-settings.md`, but structural validation still flags 2 issue(s) after two repair attempts: ✗ <first failure verbatim> ✗ <second failure verbatim>. The file is on disk; executability validation did not run.

   Mirror any banner into the user's chat language as the Korean example above shows — translate the prose, keep paths, filenames, and technical fields (`trivial signals (...)`, termination triggers, validator messages) verbatim.

   When structural validation still fails after the repair budget, Stage 5.5, Stage 5.6, and Stage 5.7 are **skipped** — the plan is not yet well-formed enough to run execution, content, or cold-pickup checks against.
   The banner stays as shown; do not append `self-check skipped` / `cold-pickup skipped` lines in this case.

   If Stage 5.5 surfaced material execution-reconstruction drift that you fixed in place, mention what you patched (e.g., "execution reconstruction skipped Stage 2's deliverable; clarified the handoff and re-validated").
   If the structural validator passed but the Stage 5.6 self-check surfaced gaps that you fixed in place, report it the same way (e.g., "self-check found 2 input concerns missing from In Scope; added them, re-validated").
   If Stage 5.7 patched the brief after cold-pickup drift, report it the same way (e.g., `cold-pickup flagged 2 gap(s); patched in place`).
   If the user used Force OFF triggers, report `cold-pickup skipped per user request`.
   If Stage 5.7 was auto-skipped because no auto-ON trigger fired, report `cold-pickup skipped: trivial signals (...)` with the signal snapshot shown in the banner case above.

2. If the user requests changes, apply them with `Edit` against the on-disk file.
   Do **not** re-render the full brief into chat — that defeats the point of save-then-review.
   Re-run the structural validator after each edit pass, then re-run Stage 5.5 and Stage 5.6, then re-evaluate the Stage 5.7 gate and report the delta.

3. If the saved single plan contains structured non-blocking `Open Questions` (after any Stage 5.7 patches have landed), present them immediately after the save report using the same four-column decision table from Stage 4:

   ```markdown
   | 순번 | 내용 | 수정 추천안 | 근거 |
   |---|---|---|---|
   | 1 | <non-blocking user decision> | <recommended patch to apply to the plan> | <safe default and reconfirm milestone> |
   ```

   After the user answers, patch the saved plan in place, move resolved decisions into the appropriate sections, leave only structured non-blocking user questions in `Open Questions`, re-run the validator plus Stage 5.5 execution-reconstruction check and Stage 5.6 self-check, then re-evaluate the Stage 5.7 gate.
   If the user does not answer, cancels, or lets structured input expire, leave the declared defaults active and the questions unchanged; they do not block the coding agent before their named reconfirmation milestones.

4. The user owns "done." Do not stage or commit the file.
   Loop on Stage 6 until they explicitly stop.

**Why save-then-review:** an earlier iteration rendered the full brief in chat for approval *before* writing to disk.
In hands-on use that flooded the conversation with markdown that renders poorly inside a code fence and was awkward to edit conversationally.
Writing to disk first lets the user review in their editor (real markdown, real diff tools, real inline edits) and lets the validator surface structural issues immediately.
The tradeoff — a file briefly on disk before approval — is neutral: `docs/briefs/` is the intended home for these files, and the commit step stays with the user.

---

## Template

See `references/template.md` for:

- The exact nine-required-section Markdown template.
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
It runs as step 5 of Stage 5 (save + validate) but can also be run ad-hoc against any existing brief.
Always resolve the script path against `<skill-dir>` — the installed skill package directory containing this SKILL.md — never against the user's repository:

```bash
python3 <skill-dir>/scripts/validate_brief.py \
  docs/briefs/2026-04-23-feat-global-hotkey-system.md
```

Exit codes: `0` pass with no warnings, `1` structural failure or any reported warning, `2` file I/O error.

Scope of the validator (deliberately structural only):

- Filename pattern, title format, type coherence across filename / title / section value, and slug length.
- Presence and template order of all nine required H2 sections + `In Scope` / `Out of Scope` H3s; duplicate H2 sections are rejected.
- `[confirmed]` / `[inferred]` prefixes in `Current State (As-Is)`, unique consecutive execution-stage headings with required fields, and structured non-blocking `Open Questions` shape.
- Type-conditional section (`Reproduction` / `Baseline Measurement` / `Behavior Contract`) present and populated for the matching type; `- N/A — <reason>` cannot be mixed with other bullets.
- Top-level bullet content in narrative sections; top-level `- [ ]` items in checklist sections; populated `Open Questions` with `- None — <reason>` when no questions remain.
- `Related Files / Entry Points` contains at least one path-shaped inline-code top-level entry; non-proposed paths and root filenames resolve on disk, while confirmed future paths use the exact adjacent `(proposed)` marker. A safe extensionless root basename is checked when it is the first inline-code token of a bullet, already exists at the repository root, or uses that exact marker. This accepts real files such as `Pipfile` without mistaking later symbols such as `STANDARD_SECTIONS` for paths; an invented first-token name fails.
- Optional `--repo-root` lets isolated brief artifacts validate their entry points against the actual target checkout.
- Optional `Constraints` heading shape.
- `Out of Scope` bullets without `[hard]` or `[deferred]` classification are reported as warnings.
  Any warning makes validation fail; the validator does not judge whether the classification is semantically correct.

Out of scope (still on content review): whether evidence labels are truthful, stage outcomes and handoffs are executable, Out-of-Scope entries are real guardrails vs. filler, entry points are *good*, Acceptance Criteria are measurable, and the type-conditional section's content is sufficient.

For briefset mode, use `scripts/validate_briefset.py` on the parent file — it validates the parent structure and re-runs `validate_brief.py`'s checks transitively on every referenced child brief, so one invocation covers the whole set:

```bash
python3 <skill-dir>/scripts/validate_briefset.py \
  docs/briefs/2026-04-30-briefset-checkout-i18n.md
```

Same exit codes.
See `references/briefset.md` for what the parent validator checks and what stays on the human reviewer.

---

## Guardrails

- **Executable, not discursive.** Apply the intro's prose-style rule to every section — rewrite discussion-summary, negotiation-log, or rationale prose until it directs concrete action; *why we are thinking about this* prose belongs in the PR description, not the brief.
- **Never fabricate file paths or PR numbers.** `Related Files / Entry Points` is mandatory because it is the downstream agent's starting route.
  If the codebase review does not surface at least one concrete file, directory, route, command, module, related brief, or confirmed proposed path, ask the user to provide or confirm the entry point before saving the brief.
  At least one top-level entry must carry that path in inline code; a plain-text path, PR-only bullet, or symbol-only bullet is not structurally checkable.
- **Ground Acceptance Criteria in input or code evidence.** Vague criteria poison the coding agent.
  Ask only for product or acceptance thresholds the user owns; derive technical proof paths from the repository.
- **Never proceed past the Ambiguity Gate on a hunch.** Halting is the correct answer when anchors are missing.
- **Keep Out-of-Scope specific.** "Don't refactor unrelated code" is filler.
  "Do not change the `PaymentService` interface" is a real guardrail.
- **Triage scope before saving.** A good review often finds more problems than one plan should fix.
  Put the user's required outcome first, keep tightly coupled checks second, and move unrelated valid findings to `[deferred]`; technical unknowns go to investigation or replan boundaries.
- **Keep implementation judgment out of Out-of-Scope.** `Out of Scope` tells the downstream coding agent what not to do.
  Put bounded implementation choices in `Constraints`, and user-owned unresolved choices in `Open Questions`.
- **Preserve named contracts.** When a change touches existing callers, persisted state, user-visible ids, event flows, schemas, file formats, or generated outputs, name the exact contracts that must remain compatible.
  Do not rely on "avoid regressions" or "keep compatibility" as a substitute.
- **One plan per invocation, unless the input has multiple execution contexts.** When it does, select briefset mode from the documented signals and explain the evidence (see `references/briefset.md`).
  Ask only when topology depends on a user-owned delivery or scope boundary.
  Briefset mode is the supported way to handle multi-context work — do not stuff unrelated execution contexts into one plan, and do not nest briefsets (a child cannot become a parent).
  When the contexts share no dependency, no ordering, and no conflict hotspot, recommend separate single-brief invocations instead of a briefset (see Stage 1).
- **Decision table does not bypass the ambiguity gate.** Halt-eligible inputs still halt at Stage 1.
  Do not try to reconstruct missing PROBLEM / GOAL / SCOPE / TARGET through a large decision table — the gate exists precisely to prevent that failure mode.
  See `references/stage-4-interview.md` for the table rules and termination conditions.

---

## Pre-Save Checklist

Self-check before invoking `Write` in Stage 5.
The structural validator catches format errors after the fact; this list catches content gaps it cannot see.

- [ ] Filename matches `YYYY-MM-DD-<type>-<slug>.md`.
- [ ] `<type>` is one of the ten Conventional Commits types.
- [ ] Title on line 1 matches `# [<type>] <title>`.
- [ ] `Current State (As-Is)` and `Desired Outcome (To-Be)` are both populated and distinguishable.
- [ ] Every load-bearing current-state bullet starts with `[confirmed]` or `[inferred]`; confirmed facts cite stable evidence and inferred findings name what will confirm them.
- [ ] Existing contracts that must not change are named concretely: ids, keys, event names, API shapes, schemas, file formats, persisted values, commands, or generated outputs.
- [ ] If internal completion and user / operator success differ, both are represented in the brief and verification does not confuse one for the other.
- [ ] If type is `fix` / `perf` / `refactor`, the type-conditional section (`Reproduction` / `Baseline Measurement` / `Behavior Contract`) is present and populated — `- N/A — <reason>` if genuinely none.
- [ ] `Out of Scope` has at least one specific entry (or an explicit "None — self-contained." with rationale).
  Use `[hard]` for must-not-touch guardrails and `[deferred]` for follow-up work when the distinction matters.
- [ ] Broad review findings have been triaged into must-fix / check-while-here / deferred; the brief does not ask the downstream agent to fix every valid concern discovered during review.
- [ ] If the brief asks the downstream agent to prove a validator or workflow bug, the verification path uses existing scripts or temporary scratch artifacts only when repository / user rules allow them.
- [ ] `Acceptance Criteria` are measurable (checkable, not aspirational).
- [ ] `Related Files / Entry Points` entries are existing repo paths, verified references, or confirmed proposed paths.
  Paths under inline-code that are not yet created carry the exact literal token `(proposed)` immediately after that path so the structural validator does not flag them as fabricated — variants like `(proposed edit)` are not recognized, and a marker elsewhere in the line does not skip path validation.
  At least one top-level entry contains a path-shaped inline-code token; plain-text paths do not count.
  Each entry routes the agent's first read or first edit, not just "related file" context.
- [ ] `Execution Plan` has consecutive `### Stage N — <name>` stages; every stage contains `Starts when`, bounded `Work`, `Deliverable`, indented `Ends when` checks, `Handoff`, and `Replan when` in order.
- [ ] Each stage handoff supplies the next stage's start, and stage-local `Ends when` checks are distinct from whole-work `Acceptance Criteria` evaluated after all stages and side-effect checks.
- [ ] `Open Questions` contains only structured non-blocking user decisions in `- [non-blocking] <question> — Default: <safe fallback>; Reconfirm before: <stage or milestone>` form, or `- None — <reason>` after one active judgement pass.

## Post-Run Checklist (before the Stage 6 banner)

Evaluated after Stage 5.5 / 5.6 / 5.7 have run or been skipped, immediately before reporting the Stage 6 banner — these items cannot be checked before `Write`.

- [ ] Cold-pickup ran when any auto-ON trigger fired (briefset / stage-4-rows ≥ 1 / non-empty `Open Questions` / type ∈ `{fix, perf, refactor}`) OR the user used Force ON triggers.
- [ ] Cold-pickup auto-skipped with `trivial signals (...)` snapshot when no auto-ON trigger fired and no Force ON was used.
- [ ] Cold-pickup skipped per user request (`cold-pickup skipped per user request`) when Force OFF was used, even if auto-ON triggers would have fired.
- [ ] Stage 6 banner reflects what actually ran — a silent skip on a fired gate is **not** acceptable.
- [ ] Any edit after Stage 5.5, Stage 5.6, Stage 5.7, or Stage 6 re-entered the validation chain from structural validation, then Stage 5.5, then Stage 5.6, before Stage 5.7 was evaluated again.
