---
name: task-brief-creator
description: >
  Generate an executable implementation work-plan Markdown at `docs/briefs/` from planning notes or a rough task description. Work brief, task brief, handoff brief, implementation ticket, and task spec remain trigger aliases. Nine required sections are keyed to Conventional Commits types so coding agents switch behavior (refactor → preserve, fix → reproduce first, perf → measure first). Briefset mode emits a parent execution-management document plus N child briefs when the input describes multiple execution contexts. Explicit task intent only — use when the user invokes this skill or asks for a work plan, implementation plan, work brief, task brief, handoff brief, implementation ticket, or task spec for a coding agent. Not for prose summaries, status reports, design docs, or meeting notes. For the caveman-register variant (compressed saved-plan prose), use task-brief-creator-caveman instead.
---

# Task Brief Creator

Produce an executable implementation work plan under `docs/briefs/` that one coding agent authors and another coding agent can execute without reconstructing the route or re-interviewing the requester. The historical work-brief and handoff names remain activation aliases; the saved artifact's primary identity is a code-execution PLAN.

The plan is the *execution artifact*. Its job is to let a coding agent recover the first stage, intended order, stage deliverables and handoffs, replan boundaries, and whole-work completion criteria — while routing it to the right files and fixing the behavior envelope.

**The plan is an executable work instruction — nothing else.** It is not a scope-control memo, discussion summary, background briefing, or rationale document. Every section must answer *"what does the coding agent do next?"* — if a section reads like meeting minutes, negotiation history, or context prose, rewrite it until it routes to files, decisions, or verifiable outcomes. A plan that makes the coding agent reconstruct its execution sequence or re-interview the requester is a **failed plan**, regardless of how polished it reads.

**"Executable, not discursive" is a *prose style* rule, not a *content reduction* rule.** It tells you how each bullet should read — direct actions and necessary facts; a brief reason stays when it prevents misuse or changes execution. It does not tell you to *drop* distinct concerns, *merge* unrelated bullets, or *summarize* the input down to its highlights. A brief that omits a concern from the input is also a failed brief, because the downstream agent will silently miss it. Tight prose, full enumeration: short bullets are fine and encouraged, but every distinct concern from the input and the codebase review must land somewhere in the brief.

---

## Modes

This skill operates in one of two **output modes**:

- **Single-plan mode** (default; historical single-brief name remains) — emits one executable work plan per invocation. The workflow below covers this case end to end.
- **Briefset mode** — emits a parent execution-management document plus N independently executable child briefs. Used when the input describes **multiple execution contexts** that need coordination (independent completion criteria, mixed work types, ordered dependencies, parallelizable waves, or shared conflict hotspots). Selected by the criteria in `references/briefset.md`; long input, many files, or many related edit points alone never trigger briefset mode.

Output-mode selection happens at Stage 1 alongside the ambiguity gate and is author-owned when the input and codebase make it evident. In briefset mode, follow the workflow below with the per-stage adaptations in `references/briefset.md` (parent template, naming, decomposition decision table, dual-validator save).

**Stage 4 always runs an ownership pass.** When user-owned decisions remain after codebase review, present only those decisions in a Markdown table with `순번`, `내용`, `수정 추천안`, and `근거`. Codebase-resolvable facts, output mode, evident work type, and reversible implementation choices are decided by the author or worker; product intent, scope, compatibility breaks, external ownership, and acceptance thresholds remain user-owned. The decision table is the output of the ownership pass when it has rows, not a separate mode. See `references/stage-4-interview.md` for the full decision classification, codebase-precedence, and termination rules.

---

## Code Agent Operating Path

Load references only when their decision point arrives:

1. Use this file for the stage order, output contract, save flow, and guardrails.
2. Read [references/work-types.md](references/work-types.md) during Stage 2 when the work type is not obvious or when the type changes downstream behavior.
3. Read [references/briefset.md](references/briefset.md) during Stage 1 when multiple execution contexts are plausible.
4. Read [references/bloat-decomposition.md](references/bloat-decomposition.md) only after a candidate child brief is independently executable but still looks oversized or mixed.
5. Read [references/codebase-review.md](references/codebase-review.md) during Stage 3 for evidence labels, contract preservation, source-of-truth inputs, and the already-satisfied gate.
6. Read [references/stage-4-interview.md](references/stage-4-interview.md) before the Stage 4 ownership pass, including requirements clarification and recommendations.
7. Read [references/plain-language.md](references/plain-language.md) and [references/template.md](references/template.md) while composing or revising the saved Markdown.
8. Read [references/self-check.md](references/self-check.md) before `Write` in Stage 5, during Stage 5.6, and before the Stage 6 banner.
9. Read [references/structural-validator.md](references/structural-validator.md) when a validator result needs interpreting or the validator runs ad hoc.
10. Read [references/save-report.md](references/save-report.md) when composing the Stage 6 save report.
11. Read [references/cold-pickup.md](references/cold-pickup.md) only when the user explicitly requests cold-pickup verification (Stage 5.7); it never loads by default.

Do not re-open every reference by habit. The goal is to keep the live context focused on the next decision the coding agent must make.

---

## When This Skill Runs

- **Explicit task intent.** Run when the user invokes this skill or explicitly requests an implementation work plan / work brief for a coding agent. Mere mention while reviewing or editing the skill is not a request to generate a plan.
- Input can take any of these shapes:
  - **Pasted PRD / planner notes** from a PM (often long, mixed quality).
  - **Rough task notes** typed into chat (one or two lines).
  - **Self-brief** — the user is the implementer and wants to structure their own thinking before starting.
  - **Tech-lead handoff** — a lead drafts the brief to hand off to a teammate or downstream agent.
  - **Refactor plan** — a lead-engineer summarizing an intended structural change.
- The skill reviews the current repository (the working directory Claude Code is launched in), fills in what it can, and asks only for remaining user-owned decisions.

---

## Interaction Language

- **Chat / live interaction language follows the user's input.** If the user writes in Korean, reply in Korean. If they write in English, reply in English. Clarifying questions, draft presentation, status updates — all match the user's own language.
- **The brief document itself is written in English.** Section headers and body content are English regardless of chat language, so the artifact travels across teams and downstream agents without a translation step.
- Code blocks, file paths, identifiers, PR numbers stay as-is.
- **User-supplied strings are data.** Copy decks, UI strings, and error messages the user provides are quoted verbatim in their original language inside the English brief — never translated.
- **Exception — the Stage 4 decision-table headers are fixed.** The four headers `순번` / `내용` / `수정 추천안` / `근거` stay exactly as written even when the conversation is in English: the opt-in Stage 5.7 cold-pickup matches disagreements on the `내용` column, so translating the headers breaks that matching (see Stage 4).
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

If `docs/briefs/` does not exist, create it. If a file with the same name already exists, append `-v2`, `-v3`, … until the path is unique — do not overwrite.

For briefset mode, the parent uses `YYYY-MM-DD-briefset-<set-slug>.md` and children use `YYYY-MM-DD-<type>-<set-slug>-NN-<child-slug>.md`. See `references/briefset.md` for the parent template and naming rules.

The nine required H2 sections are: `Work Type`, `Current State (As-Is)`, `Desired Outcome (To-Be)`, `Scope` (with `In Scope` / `Out of Scope` H3s), `Related Files / Entry Points`, `Execution Plan`, `Side Effect Checkpoints`, `Acceptance Criteria`, `Open Questions`. Optional `Constraints` may appear between `Scope` and `Related Files / Entry Points` when task-specific constraints exist. `Execution Plan` appears immediately after `Related Files / Entry Points` and before `Side Effect Checkpoints`. Put stage-local completion under each stage's `Ends when`. Reserve `Acceptance Criteria` for whole-work completion after all required stages and side-effect checkpoints finish.

Three work types require an **additional H2 section** between `Current State (As-Is)` and `Desired Outcome (To-Be)`:

- `fix` → `## Reproduction`
- `perf` → `## Baseline Measurement`
- `refactor` → `## Behavior Contract`

These exist because the work type changes the downstream agent's behavior (reproduction-first, measurement-first, behavior-preservation), and the brief must carry the type-specific input that behavior depends on. The escape hatch when the section legitimately has nothing concrete to capture is a single bullet `- N/A — <reason>`. See `references/template.md` and `references/work-types.md` for the per-section guidance.

Bullet count is not capped. The rule is cohesion plus completeness, not brevity:

- Each bullet should describe one coherent unit of context, scope, risk, or verification.
- **Enumerate every distinct concern.** If the input or the Stage 3 codebase review surfaces N distinct concerns that map to a section, the section gets ≥ N bullets. Sections expand to fit the work; they are not capped. A section reduced to one bullet when the input contained multiple concerns for it is the failure mode this rule exists to prevent.
- Do not merge unrelated concerns into one bullet just to keep the document short.
- Write as many bullets as the task needs; do not compress larger work into vague combined bullets. Short prose per bullet is fine and encouraged — short *count* is the failure.

Completeness does not mean "put every discovered issue in scope." When review surfaces many valid concerns, separate them before saving:

- **Must fix in this brief** — issues that directly block the user's stated goal or would make the downstream task unsafe / wrong if left unresolved.
- **Check while here** — nearby contract or documentation consistency checks that are cheap and directly connected to the must-fix work.
- **Defer / record** — valid follow-up issues that do not have to change for this brief to succeed.

`In Scope` should usually hold the must-fix set plus tightly coupled checks, not the whole discovery list. Record deferred items in `Out of Scope` as `[deferred]`; use `Open Questions` only for non-blocking user-owned decisions with a safe default and reconfirm milestone. If more than five independent must-fix concerns remain after this triage, reconsider briefset mode or ask the user to choose the first slice only when slicing is a user-owned scope decision.

---

## Workflow

### Stage 1 — Ambiguity Gate (HALT or CONTINUE)

Before full codebase review, check whether the input contains enough signal to ground the brief. Use the **four-anchor heuristic**:

| Anchor | What it answers | Maps to |
|---|---|---|
| **PROBLEM** | What is wrong or what is changing? | § Current State (As-Is) |
| **GOAL** | What should be true when it's done? | § Desired Outcome (To-Be) |
| **SCOPE** | Where does this apply (module, feature area, user surface)? | § In/Out of Scope |
| **TARGET** | Which part of the system is touched (file, subsystem, layer)? | § Related Files / Entry Points |

Count how many anchors are derivable from the input. Derivable = a reasonable engineer could answer the anchor from the user's input without inventing intent.

- **All 4 anchors present** → **CONTINUE** to Stage 2.
- **3 anchors present, TARGET missing** → run a narrow target probe before deciding. Use at most a few `rg` / glob queries to find likely files, directories, routes, commands, or modules. If a concrete entry point emerges, **CONTINUE**. If not, **HALT** and ask the user for the target area.
- **3 anchors present, PROBLEM or GOAL or SCOPE missing** → **CONTINUE** only when the missing anchor can be stated in one concrete sentence derived from the input (write that sentence into the brief; vague fillers like "make it better / cleaner" do not count). Otherwise **HALT** and ask for that anchor. Detail that survives this check gets filled in Stage 3 via codebase review or Stage 4 via user questions.
- **2 or fewer anchors present** → **HALT**. Respond in the user's chat language naming exactly which anchors are missing, and ask for more input. Do NOT proceed through Stages 2–6 on an underspecified input. The briefset-mode check below also waits — never split an underspecified input into multiple equally underspecified child briefs. Example halt messages:

  **English:**
  > I can't ground the brief from this input alone. Missing — **PROBLEM** (what is being fixed or changed) and **TARGET** (which area / file / subsystem is touched). Can you paste the spec or add one or two lines?

  **Korean:**
  > 입력만으로는 브리핑 만들기 어려워. 다음이 아직 확인 안 돼 — **PROBLEM**(뭘 고치거나 바꾸는지)과 **TARGET**(어느 영역/파일/시스템을 건드리는지). 더 얹어줄래? 기획서 붙여넣거나 한두 줄 더 써주면 돼.

**Why halt instead of guess:** an underspecified brief is worse than no brief — the downstream agent commits to the wrong problem framing and the rework cost eats the whole savings. Pushing back early is cheaper than producing a confident-looking but wrong document.

**Edge case — pasted spec that looks long but is content-light:** word count is not a proxy for the four anchors. A 2,000-word product narrative without a concrete PROBLEM or TARGET still halts. Judge by anchor coverage, not length.

See `examples/03-halt-ambiguous.md` for a worked halt case.

**Briefset signal check (after CONTINUE):** once anchors clear, also evaluate whether the input describes multiple execution contexts. Do not use file count, line count, input length, or several related edit points as triggers by themselves. Those are supporting evidence only.

If briefset signals are strong, select briefset mode and state the evidence before Stage 2. If the candidate contexts have unrelated outcomes and no shared acceptance boundary, select separate single-plan invocations. Independent children serving one coordinated outcome may share a briefset and start in the same wave; do not invent dependencies to justify the parent. If the evidence is unclear, default to single-plan mode. Ask only when output topology depends on a user-owned delivery boundary, release unit, or scope choice; do not ask the user to choose a document shape when code and input already settle it. Several stages inside one cohesive execution context do not justify briefset mode; consult `references/bloat-decomposition.md` before splitting an oversized candidate.

### Stage 2 — Work Type Selection

Determine the Conventional Commits type. Consult `references/work-types.md` for the full list and per-type behavior hints.

- If the input explicitly names a type (e.g., "this is a refactor"), use it when the input evidence agrees.
- If the named type conflicts with the described outcome, classify by the outcome and record the mismatch; ask only if resolving it requires a user-owned behavior or scope decision.
- If the type is implicit but high-confidence, assign it without a confirmation round-trip.
- If the implicit type is low-confidence but technically resolvable, probe the codebase or put the distinction into the first `Execution Plan` stage as an investigation with a `Replan when` boundary.
- Ask in Stage 4 only when the work type depends on an underlying product or scope choice the user owns; derive the type from that answer.

See `references/work-types.md` for the full author-selection routing table.

### Stage 3 — Codebase Review

The goal is enough context to fill `Current State (As-Is)` and `Related Files / Entry Points`, not exhaustive exploration. Use whatever code search / read / symbol tooling fits the host environment and repository guidance — default `Grep` / `Read` / `Glob`, allowed semantic tools, language servers, or a short-lived subagent (e.g. `Explore`) when parallel lookups or main-context isolation is worth it. Tool choice is the runtime's call; this stage only fixes the *purpose* and *budget* of the review.

Review budget (soft limits):

- At most ~15 file reads
- At most ~10 search queries
- Stop when you can confidently enumerate the **primary** entry points and major affected areas implied by the input — not just the first file or symbol that grounds the brief. If likely input-implied surfaces remain unverified within the review budget, add a bounded investigation stage with a named deliverable and `Replan when` condition.

Strategy:

1. Start wide with keyword search on terms from the input — feature names, function names, error strings, routes, type names.
2. Narrow to a list of candidate files, then read the 2–4 most promising ones.
3. If the input mentions a subsystem (e.g., "auth middleware", "checkout flow"), look at likely directories first.
4. Capture an As-Is picture by coherent context units: how each relevant function, module, behavior, integration, or user surface is shaped today.
5. Capture concrete Related File / entry-point hints with one-line purposes. At least one entry point must be solid before saving the brief.

Then apply [references/codebase-review.md](references/codebase-review.md) to what the review found: active judgement about nearby signals, evidence labels, contract preservation, source-of-truth inputs, and the already-satisfied gate. The rules from it that shape every saved plan:

- Prefix every load-bearing `Current State (As-Is)` bullet with `[confirmed]` or `[inferred]`. A confirmed finding cites the file and a stable locator, not a line number alone; an inferred finding names what would confirm it.
- Name the existing contracts that must keep their current shape; surface a required contract break in Stage 4 unless the user already approved it.
- Treat each item of a user-supplied checklist, TODO file, review rubric, or audit document as a required concern, never as material for a representative summary.
- Keep implementation completion and user / operator success separate when they differ.

**Already-satisfied gate.** Before Stage 4, compare the full requested outcome and acceptance boundary against current code plus current verification signals. If no edit, integration, migration, or evidence-producing work remains, create no plan: report `no-work-needed` in the user's language with the inspected paths, verification action, and observed signal, then stop. Explicitly requested verification records, partial satisfaction, and briefset topology after the gate follow the reference.

### Stage 4 — User Decision Table

After Stage 3 has gathered enough codebase context, run an ownership pass and collect only remaining user-owned decisions into a Markdown decision table. Stage 4 is not a pre-review guessing interview: ask only after the codebase has been checked enough to state the uncertainty, the recommended change, and the evidence behind it.

Use this exact table shape for user-decision questions:

```markdown
| 순번 | 내용 | 수정 추천안 | 근거 |
|---|---|---|---|
| 1 | <decision the user must make> | <recommended change to apply to the brief> | <codebase/input evidence and risk> |
```

Keep these four headers exactly as written, even when the surrounding conversation is not Korean. They are the stable decision-table contract: number, decision content, recommended change, and rationale.

**Intent before enumeration.** If input and bounded review leave multiple plausible goals, behaviors, scope boundaries, or completion criteria, use the table to show the ambiguity, alternatives, recommended interpretation, and evidence before treating one interpretation as the task. Label recommendations as proposals, not existing requirements; an unanswered optional enhancement stays excluded.

The author determines output mode, work type, entry points, side-effect checks, and technical sequencing when the input and codebase make them evident. Technical unknowns become investigation stages, bounded `Worker decision` fields, `Replan when` conditions, constraints, or author-selected defaults. Ask the user for relevant observations or access details only when they hold information unavailable from the reviewed artifacts; do not ask them to perform the technical investigation.

**Decision-table rule.** Each row must request a real decision or a specific unavailable user-held observation, not a vague status note. `내용` states what the user must decide, `수정 추천안` the concrete brief change you recommend, and `근거` the input, codebase finding, existing pattern, or risk. After the user answers, patch the draft plan in memory before composing the brief. An unanswered or skipped question is not approval: non-blocking rows use their declared safe fallback, remain in structured `Open Questions` form, and proceed; any blocking row halts without writing. A task cancellation stops authoring; it is not permission to use fallbacks and continue.

Before writing `Open Questions`, make one active judgement pass: move reasonable bounded choices into `Worker decision`, `Constraints`, or an execution stage, and keep only user-owned decisions. Save each question as `- [non-blocking] <question> — Default: <safe fallback>; Reconfirm before: <stage or milestone>`. If the user has not answered a blocking decision and no safe fallback exists, **HALT** and create no file.

Read [references/stage-4-interview.md](references/stage-4-interview.md) for the user-owned gaps to close before drafting, decision classification, codebase precedence and probe budget, table rules, the full `Open Questions` pass, and termination conditions.

### Stage 5 — Save + Validate

Once Stage 4 closes, compose the final Markdown internally and **write it straight to disk** — do not paste the full brief into chat first. The user reviews the file in their editor in Stage 6, where real markdown rendering and diff tooling are available.

1. Compute the filename per the **Output Contract** above.
2. Ensure `docs/briefs/` exists; create it if not.
3. Resolve filename collisions by appending `-v2`, `-v3`, ….
4. Run the [Pre-Save Checklist](references/self-check.md#pre-save-checklist), then render the complete template from `references/template.md` and write the file (English section headers, English body).
5. **Run the structural validator** — a fast smoke test for the template contract:

   ```bash
   python3 <skill-dir>/scripts/validate_brief.py docs/briefs/<filename>.md
   ```

   If the brief is stored in an isolated artifact tree while its entry-point paths belong to another checkout, add `--repo-root <repository-root>` before the brief path.

   `<skill-dir>` is the installed skill package directory — the directory containing this SKILL.md (resolve it from wherever this skill was loaded, e.g. `~/.claude/skills/task-brief-creator` or a plugin cache). Never assume the user's repository contains the script: the brief lives in the user's repo, the validator lives with the skill.

   - Exit **0** → continue to Stage 5.6; the validator result is reported in the Stage 6 banner.
   - Exit **1** (structural failure) → fix the file and rerun the validator without asking the user. If the same structural cause still fails after two repair attempts, leave the file in place and carry the residual failure into Stage 6.
   - Exit **2** (file I/O error) → inspect the actual error: invalid arguments, invalid `--repo-root`, missing artifact, or unreadable file. Correct the cause; do not infer that a saved file disappeared or recreate it unnecessarily.

   The validator only checks **structural** conformity (section presence, checklist format, filename pattern, type coherence). It does *not* judge content quality — that's what the Stage 5.6 self-check, the opt-in Stage 5.7 cold-pickup, and the human review in Stage 6 are for. Passing validator ≠ good brief; failing validator = malformed brief.

### Validation Budget

A validation run covers the single plan or the entire parent-and-children set. It consists of the structural validator followed by the Stage 5.6 self-check; nothing in the default run spawns a sub-agent. Structural repairs: at most two attempts for the same structural cause, then carry the residual failure into Stage 6. Self-check: at most two passes per run; every content edit re-runs the structural validator before the next pass. When the budget is exhausted, keep the latest well-formed file, stop automatic repairs, and report the remaining gaps as incomplete, never as passed. A new user answer or requested edit starts a new validation run. The opt-in Stage 5.7 cold-pickup runs once per explicit user request after a completed run; the patches it causes re-enter this budget from the structural validator. Before applying cold-pickup patches, copy the affected files to a scratch directory outside the repository so a patch that breaks a previously passing check can be restored; delete the copies after the final state has been reported.

### Stage 5.6 — Content and Intent Self-Check

The structural validator confirms the file has the required sections. It does not confirm the file is a *complete* work instruction, nor that it says what the user meant. Before handing off in Stage 6, re-read the saved brief from disk and run the [Stage 5.6 checklist](references/self-check.md#stage-56-content-and-intent-checklist) against the original input plus Stage 3 / Stage 4 findings. This is the only verification pass in the default run; an independent read by a fresh sub-agent is available on request through Stage 5.7.

The brief is a work instruction, not a summary. Any concern that existed in the input must survive into the brief — possibly reshaped into the right section, never silently dropped.

If any check fails, fix the brief in place with `Edit`, re-run the structural validator (`validate_brief.py` for a single brief, `validate_briefset.py` for a briefset parent), then run this self-check again. At most two self-check passes per validation run; if a gap remains after the second pass or has no justified patch, stop and report the latest file as incomplete, not passed.

The self-check outcome is a separate signal from the structural validator — both are reported in Stage 6. A brief can pass structural validation and still fail this self-check; in that case the file is incomplete even though it is well-formed.

For briefset mode, run the self-check on the parent and on every child independently. The parent's coverage check asks whether every input-implied execution context maps to a child; each child's coverage check uses every item in the checklist.

### Stage 5.7 — Cold-Pickup Verification (opt-in)

The Stage 5.6 self-check is self-evaluated: the author cannot forget its own intent, so it cannot fully simulate a stranger reading the file cold. Stage 5.7 supplies that stranger — a fresh read-only sub-agent that first reconstructs the plan from the saved brief alone, then compares it with the original input and reports intent deviations, ask-backs, and missing concerns.

**Stage 5.7 never runs by default.** It has no signal gates and no automatic triggers; briefset mode, Stage 4 decision rows, non-empty `Open Questions`, and work type do not start it. It runs only when the user explicitly asks — for example `run cold-pickup`, `--cold-pickup`, `콜드픽업 실행` — either together with the initial input or later in Stage 6 against the current on-disk file. Do not spawn a sub-agent for verification without such a request. Report Stage 5.7 only when requested; omit unsolicited optional-check invitations from Stage 6.

**When requested, read `references/cold-pickup.md` and follow it.** In short:

1. Complete the current validation run first (structural validator and Stage 5.6 pass or report residuals); cold-pickup does not replace either. If structural validation still fails after the repair budget, Stage 5.7 does not run (see Stage 6).
2. Spawn one fresh read-only sub-agent per artifact — one for a single brief; in briefset mode one for the parent plus one per child the user did not exclude — with no inherited conversation and no Stage 3 register, Stage 4 decisions, self-check results, or hints about suspected gaps.
3. Give it the brief path (plus the parent path for a child) and the path of a scratch file holding the original input verbatim; it reads those files only and never explores the repository.
4. Collect the YAML report, route each finding through the reference's routing tables (disagreement vs drift against answered Stage 4 rows), patch drift in place, re-run the structural validator, then Stage 5.6.
5. Report the outcome in the Stage 6 banner. One pass per request: do not re-run cold-pickup automatically after patching; the user asks again if they want another independent read.

Cold-pickup never overrides a Stage 4 decision the user already locked, never invents Acceptance Criteria, Side Effect Checkpoints, or Out-of-Scope guardrails the input did not imply, and never silently rewrites `Open Questions` — drift fixes either resolve a question into another section or leave the question intact for the user. If a fresh read-only sub-agent cannot be spawned or returns an unusable report, report `cold-pickup unavailable (<actual reason>)`; the Stage 5.6 result stands on its own and is never relabeled as an independent read.

### Stage 6 — Review + Iterate

The brief is on disk. Hand off to the user for review.

1. Report the path and one-line summary, then distinguish **structural validation** from **content validation**. Structural validation is the Stage 5 validator result. Content validation is the Stage 5.6 content and intent self-check, and the actual Stage 5.7 result only when the user requested it. Do not imply that the self-check is an independent reader evaluation. Report unavailable, incomplete, restored, and exhausted outcomes explicitly; a missing required result is never a pass. Every reported check must belong to the final saved artifact state. Use the user's chat language.

   Run the [Post-Run Checklist](references/self-check.md#post-run-checklist-before-the-stage-6-banner) first, then report with the banner forms in [references/save-report.md](references/save-report.md). A translated banner keeps paths, filenames, and technical fields verbatim. Briefset banners use the collapsed formats in `references/cold-pickup.md` and `references/briefset.md`.

   When structural validation still fails after the repair budget, Stage 5.6 is **skipped** and Stage 5.7 does not run — the plan is not yet well-formed enough to check content against. If the user requested cold-pickup, append `cold-pickup unavailable (structural validation failed)`; otherwise add no line for the skipped checks.

   Say what the Stage 5.6 self-check patched within the budget, list each Stage 5.7 patched and residual finding as bullets under the banner, and report `cold-pickup unavailable (<actual reason>)` instead of a result when a requested cold-pickup could not run.

2. If the user requests changes, apply them with `Edit` against the on-disk file. Do **not** re-render the full brief into chat — that defeats the point of save-then-review. Re-run the structural validator after each edit pass, then Stage 5.6, and report the delta. Re-run Stage 5.7 only if the user asks for it again.

3. If the saved single plan contains structured non-blocking `Open Questions` (after any Stage 5.7 patches have landed), present them immediately after the save report using the same four-column decision table from Stage 4:

   ```markdown
   | 순번 | 내용 | 수정 추천안 | 근거 |
   |---|---|---|---|
   | 1 | <non-blocking user decision> | <recommended patch to apply to the plan> | <safe default and reconfirm milestone> |
   ```

   After the user answers, patch the saved plan in place, move resolved decisions into the appropriate sections, leave only structured non-blocking user questions in `Open Questions`, then re-run the validator and Stage 5.6. If the user leaves a question unanswered, skips that question, or lets structured input expire, leave the declared defaults active and the questions unchanged; they do not block the coding agent before their named reconfirmation milestones.

4. The user owns "done." A task cancellation stops further edits and verification. Do not stage or commit the file. Loop on Stage 6 until they explicitly stop.

---

## Template, Work Types, and Examples

- `references/template.md` — the exact nine-required-section Markdown template, per-section writing guidance (what good looks like, what not to write), and a worked example of a filled brief. The emitted brief is in English; chat interaction language follows the user's input.
- `references/work-types.md` — the ten Conventional Commits types, per-type agent behavior hints (the type changes how the downstream coding agent approaches the work), and classification tips for ambiguous cases.
- `examples/` — worked end-to-end scenarios (input → codebase review → interview → output); start with `examples/README.md` for the index.

---

## Structural Validator

`scripts/validate_brief.py` checks a single plan; `scripts/validate_briefset.py` checks a briefset parent and re-runs `validate_brief.py`'s checks transitively on every referenced child, so one invocation covers the whole set. Both are stand-alone Python 3 scripts with no external dependencies. They run as step 5 of Stage 5 but can also be run ad hoc against any existing brief. Always resolve the script path against `<skill-dir>` — the installed skill package directory containing this SKILL.md — never against the user's repository:

```bash
python3 <skill-dir>/scripts/validate_brief.py \
  docs/briefs/2026-04-23-feat-global-hotkey-system.md
python3 <skill-dir>/scripts/validate_briefset.py \
  docs/briefs/2026-04-30-briefset-checkout-i18n.md
```

Exit codes (both scripts): `0` pass with no warnings, `1` structural failure or any reported warning, `2` argument, repository-root, or file I/O error. See [references/structural-validator.md](references/structural-validator.md) for what `validate_brief.py` checks and what stays on content review, and the Validator Scope section of `references/briefset.md` for the parent validator.

---

## Guardrails

- **Executable, not discursive.** Apply the intro's prose-style rule to every section — rewrite discussion-summary, negotiation-log, or rationale prose until it directs concrete action; retain only the brief rationale the reader needs to execute safely; author deliberations do not belong in the brief.
- **Never fabricate file paths or PR numbers.** `Related Files / Entry Points` is mandatory because it is the downstream agent's starting route. If the codebase review does not surface at least one concrete file, directory, route, command, module, related brief, or confirmed proposed path, ask the user to provide or confirm the entry point before saving the brief. At least one top-level entry must carry that path in inline code; a plain-text path, PR-only bullet, or symbol-only bullet is not structurally checkable.
- **Ground Acceptance Criteria in input or code evidence.** Vague criteria poison the coding agent. Ask only for product or acceptance thresholds the user owns; derive technical proof paths from the repository.
- **Never proceed past the Ambiguity Gate on a hunch.** Halting is the correct answer when anchors are missing.
- **Keep Out-of-Scope specific.** "Don't refactor unrelated code" is filler. "Do not change the `PaymentService` interface" is a real guardrail.
- **Triage scope before saving.** A good review often finds more problems than one plan should fix. Put the user's required outcome first, keep tightly coupled checks second, and move unrelated valid findings to `[deferred]`; technical unknowns go to investigation or replan boundaries.
- **Keep implementation judgment out of Out-of-Scope.** `Out of Scope` tells the downstream coding agent what not to do. Put bounded implementation choices in `Constraints`, and user-owned unresolved choices in `Open Questions`.
- **Preserve named contracts.** When a change touches existing callers, persisted state, user-visible ids, event flows, schemas, file formats, or generated outputs, name the exact contracts that must remain compatible. Do not rely on "avoid regressions" or "keep compatibility" as a substitute.
- **One plan per invocation, unless the input has multiple execution contexts.** When it does, select briefset mode from the documented signals and explain the evidence (see `references/briefset.md`). Ask only when topology depends on a user-owned delivery or scope boundary. Briefset mode is the supported way to handle multi-context work — do not stuff unrelated execution contexts into one plan, and do not nest briefsets (a child cannot become a parent). When contexts have unrelated outcomes and no shared acceptance boundary, recommend separate single-plan invocations (see Stage 1). Within a briefset, use parallel waves by default and add ordering only for actual preconditions, verified conflicts, or user-required delivery order.
- **Decision table does not bypass the ambiguity gate.** Halt-eligible inputs still halt at Stage 1. Do not try to reconstruct missing PROBLEM / GOAL / SCOPE / TARGET through a large decision table — the gate exists precisely to prevent that failure mode. See `references/stage-4-interview.md` for the table rules and termination conditions.
