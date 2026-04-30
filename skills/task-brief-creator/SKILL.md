---
name: task-brief-creator
description: >
  Generate a structured work-brief Markdown at `docs/briefs/` from planning
  notes or a rough task description. Eight required sections plus optional
  task-specific constraints, keyed to Conventional Commits types so downstream
  coding agents switch behavior (refactor → preserve, fix → reproduce first,
  perf → measure first). Briefset mode produces a parent execution-management
  document plus N child briefs when the input describes multiple execution
  contexts (mixed types, ordered dependencies, shared conflict surfaces).
  Halts on vague input. Manual trigger only.
---

# Task Brief Creator

Produce a structured work-brief Markdown document under `docs/briefs/` that a
downstream coding agent (or a human engineer) can pick up and execute without
re-interviewing the requester.

The brief is the *handoff artifact*. Its job is to shrink the cost of the first
hour a coding agent spends on the task — routing it to the right files, fixing
the behavior envelope, and pre-answering the questions that would otherwise
bounce back to the requester.

**The brief is an executable work instruction — nothing else.** It is not a
scope-control memo, not a discussion summary, not a planning note, not a
background briefing, not a rationale document. Every section must answer
*"what does the coding agent do next?"* — if a section reads like meeting
minutes, negotiation history, or context prose, rewrite it until it routes
to files, decisions, or verifiable outcomes. A brief that makes the
downstream agent re-interview the requester is a **failed brief**, regardless
of how polished it reads.

---

## Modes

This skill operates in one of two modes:

- **Single-brief mode** (default) — emits one brief per invocation. The
  workflow below covers this case end to end.
- **Briefset mode** — emits a parent execution-management document plus
  N independently executable child briefs. Used when the input describes
  **multiple execution contexts** (independent completion criteria,
  distinct entry-point files, mixed work types, ordered dependencies,
  parallelizable waves, or shared conflict hotspots that need
  coordination). Triggered by the criteria in
  `references/briefset.md`; long input alone never triggers briefset
  mode.

Mode selection happens at Stage 1 alongside the ambiguity gate. In
briefset mode, follow the workflow below with the per-stage adaptations
in `references/briefset.md` (parent template, naming, batched
decomposition question, dual-validator save).

---

## When This Skill Runs

- **Manual trigger only.** The user invokes this skill explicitly (via slash
  command, `/task-brief-creator`, or similar).
- Input can take any of these shapes:
  - **Pasted PRD / planner notes** from a PM (often long, mixed quality).
  - **Rough task notes** typed into chat (one or two lines).
  - **Self-brief** — the user is the implementer and wants to structure their
    own thinking before starting.
  - **Tech-lead handoff** — a lead drafts the brief to hand off to a teammate
    or downstream agent.
  - **Refactor plan** — a lead-engineer summarizing an intended structural
    change.
- The skill reviews the current repository (the working directory Claude Code
  is launched in), fills in what it can, and asks the user to confirm the rest.

---

## Interaction Language

- **Chat / live interaction language follows the user's input.** If the user
  writes in Korean, reply in Korean. If they write in English, reply in
  English. Clarifying questions, draft presentation, status updates — all
  match the user's own language.
- **The brief document itself is written in English.** Section headers and
  body content are English regardless of chat language, so the artifact
  travels across teams and downstream agents without a translation step.
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

If `docs/briefs/` does not exist, create it. If a file with the same name
already exists, append `-v2`, `-v3`, … until the path is unique — do not
overwrite.

For briefset mode, the parent uses
`YYYY-MM-DD-briefset-<set-slug>.md` and children use
`YYYY-MM-DD-<type>-<set-slug>-NN-<child-slug>.md`. See
`references/briefset.md` for the parent template and naming rules.

The eight required H2 sections are: `Work Type`, `Current State (As-Is)`,
`Desired Outcome (To-Be)`, `Scope` (with `In Scope` / `Out of Scope` H3s),
`Related Files / Entry Points`, `Side Effect Checkpoints`, `Acceptance
Criteria`, `Open Questions`. Optional `Constraints` may appear between `Scope`
and `Related Files / Entry Points` when task-specific constraints exist.

Bullet count is not capped. Large work may need many bullets. The rule is
cohesion, not brevity:

- Each bullet should describe one coherent unit of context, scope, risk, or
  verification.
- Do not merge unrelated concerns into one bullet just to keep the document
  short.
- Write as many bullets as the task needs; do not compress larger work into
  vague combined bullets.

---

## Workflow

### Stage 1 — Ambiguity Gate (HALT or CONTINUE)

Before full codebase review, check whether the input contains enough signal to
ground the brief. Use the **four-anchor heuristic**:

| Anchor | What it answers | Maps to |
|---|---|---|
| **PROBLEM** | What is wrong or what is changing? | § Current State (As-Is) |
| **GOAL** | What should be true when it's done? | § Desired Outcome (To-Be) |
| **SCOPE** | Where does this apply (module, feature area, user surface)? | § In/Out of Scope |
| **TARGET** | Which part of the system is touched (file, subsystem, layer)? | § Related Files / Entry Points |

Count how many anchors are derivable from the input. Derivable = a reasonable
engineer could answer the anchor from the user's input without inventing intent.

- **3 or 4 anchors present** → **CONTINUE** to Stage 2. Missing detail gets
  filled in Stage 3 via codebase review or Stage 4 via user questions.
- **PROBLEM + GOAL + SCOPE present, TARGET missing** → run a narrow target
  probe before deciding. Use at most a few `rg` / glob queries to find likely
  files, directories, routes, commands, or modules. If a concrete entry point
  emerges, **CONTINUE**. If not, **HALT** and ask the user for the target area.
- **2 or fewer anchors present** → **HALT**. Respond in the user's chat
  language naming exactly which anchors are missing, and ask for more input.
  Do NOT proceed through Stages 2–6 on an underspecified input. The
  briefset-mode check below also waits — never split an underspecified
  input into multiple equally underspecified child briefs. Example halt
  messages:

  **English:**
  > I can't ground the brief from this input alone. Missing — **PROBLEM**
  > (what is being fixed or changed) and **TARGET** (which area / file /
  > subsystem is touched). Can you paste the spec or add one or two lines?

  **Korean:**
  > 입력만으로는 브리핑 만들기 어려워. 다음이 아직 확인 안 돼 —
  > **PROBLEM**(뭘 고치거나 바꾸는지)과 **TARGET**(어느 영역/파일/시스템을
  > 건드리는지). 더 얹어줄래? 기획서 붙여넣거나 한두 줄 더 써주면 돼.

**Why halt instead of guess:** an underspecified brief is worse than no brief —
the downstream agent commits to the wrong problem framing and the rework cost
eats the whole savings. Pushing back early is cheaper than producing a
confident-looking but wrong document.

**Edge case — pasted spec that looks long but is content-light:** word count
is not a proxy for the four anchors. A 2,000-word product narrative without a
concrete PROBLEM or TARGET still halts. Judge by anchor coverage, not length.

See `examples/03-halt-ambiguous.md` for a worked halt case.

**Briefset signal check (after CONTINUE):** once anchors clear, also
evaluate whether the input describes multiple execution contexts (mixed
work types, ordered dependencies, shared conflict surfaces, distinct
entry points). If briefset signals are clearly present, plan for
briefset mode and surface that intent before Stage 2. See
`references/briefset.md` § "When To Enter Briefset Mode" for the full
criteria. If unclear, default to single-brief mode and let Stage 4
surface the question.

### Stage 2 — Work Type Selection

Determine the Conventional Commits type. Consult
`references/work-types.md` for the full list and per-type behavior hints.

- If the input explicitly names a type (e.g., "this is a refactor"), use it
  when the input evidence agrees.
- If the user names a type that conflicts with the described work (e.g.,
  "refactor" but the work changes behavior), pause and confirm with one
  question before codebase review.
- If the type is implicit but high-confidence, assign a provisional type and
  confirm it in the Stage 4 question batch. Do not add a separate early
  round-trip just for type confirmation.
- If the implicit type is low-confidence and changes the likely execution
  approach, ask one short question before proceeding.

### Stage 3 — Codebase Review (inline)

Use **inline Grep / Read / Glob** — do *not* spawn subagents for this step.
The goal is enough context to fill `Current State (As-Is)` and `Related Files
/ Entry Points`, not exhaustive exploration.

Review budget (soft limits):

- At most ~15 file reads
- At most ~10 Grep queries
- Stop as soon as you can confidently name the entry points

Strategy:

1. Start wide with `rg` on keywords from the input — feature names, function
   names, error strings, routes, type names.
2. Narrow with `rg -l` to list candidate files, then Read the 2–4 most
   promising ones.
3. If the input mentions a subsystem (e.g., "auth middleware", "checkout
   flow"), glob for likely directories first.
4. Capture an As-Is picture by coherent context units: how each relevant
   function, module, behavior, integration, or user surface is shaped today.
5. Capture concrete Related File / entry-point hints with one-line purposes.
   At least one entry point must be solid before saving the brief.

**Do not:**

- Read entire large files when symbolic reads (or targeted ranges) suffice.
- Chase tangential code just to pad the brief. If it does not tighten
  `Current State (As-Is)` or `Related Files / Entry Points`, skip it.
- Make architectural claims the code does not support. If uncertain, flag
  it in `Open Questions` instead.

### Stage 4 — Active Interview

Fill remaining gaps by asking the user. Batch questions — never drip them
one by one.

Required gaps to close before drafting:

- **Desired Outcome (To-Be)** (always ask if not explicit) — what is true at
  the end.
- **Work Type** — confirm the provisional type from Stage 2 when it was
  inferred rather than explicitly provided.
- **Out of Scope** — the most valuable guardrail for the downstream agent.
  Offer a proposed out-of-scope list based on the input and let the user
  edit.
- **Related Files / Entry Points** — confirm at least one concrete entry point
  if the codebase review did not surface one. This section is mandatory because
  the brief must tell the downstream agent where to start.
- **Acceptance Criteria** — what makes the task verifiably done.
- **Side Effect Checkpoints** — what else must be verified if this area is
  touched. Draft a candidate list from the codebase review and ask the user
  to confirm / extend.
- **Open Questions** — explicitly surface anything the codebase review
  raised that the user should answer or delegate to the downstream agent.

Batch 3–6 questions per round. Prefer concrete yes/no or pick-from-list
framings over open-ended prompts. Use the `AskUserQuestion` tool where
available for structured multi-question rounds.

### Stage 5 — Save + Validate

Once Stage 4 closes, compose the final Markdown internally and **write it
straight to disk** — do not paste the full brief into chat first. The user
reviews the file in their editor in Stage 6, where real markdown rendering
and diff tooling are available.

1. Compute the filename per the **Output Contract** above.
2. Ensure `docs/briefs/` exists; create it if not.
3. Resolve filename collisions by appending `-v2`, `-v3`, ….
4. Render the complete template from `references/template.md` and write
   the file (English section headers, English body).
5. **Run the structural validator** — a fast smoke test for the template
   contract:

   ```bash
   python3 skills/task-brief-creator/scripts/validate_brief.py \
     docs/briefs/<filename>.md
   ```

   - Exit **0** → proceed to Stage 6 with a "passed" banner.
   - Exit **1** (structural failure) → **leave the file in place**. Do
     not delete or silently rewrite it. Carry the failed checks into
     Stage 6 so the user can see what tripped and decide how to fix.
   - Exit **2** (file I/O error) → the save did not actually land;
     investigate and retry.

   The validator only checks **structural** conformity (section presence,
   checklist format, filename pattern, type coherence). It does *not*
   judge content quality — that's what the human review in Stage 6 is
   for. Passing validator ≠ good brief; failing validator = malformed
   brief.

### Stage 6 — Review + Iterate

The brief is on disk. Hand off to the user for review.

1. Report the path, a one-line summary (work type + title), and the
   validator result. Use the user's chat language.

   **English (validator passed):**
   > Saved — `docs/briefs/2026-04-23-feat-dark-mode-settings.md`
   > (`feat`: Dark mode toggle in Settings; structural validation passed).
   > Open it and let me know if anything needs editing.

   **Korean (validator passed):**
   > 저장 완료 — `docs/briefs/2026-04-23-feat-dark-mode-settings.md`
   > (`feat`: Dark mode toggle in Settings; 구조 검증 통과).
   > 파일 열어보고 고칠 부분 있으면 알려줘.

   **English (validator failed):**
   > Saved — `docs/briefs/2026-04-23-feat-dark-mode-settings.md`, but the
   > structural validator flagged 2 issue(s):
   >   ✗ <first failure verbatim>
   >   ✗ <second failure verbatim>
   > The file is on disk. Want me to patch these, or will you edit
   > directly?

   **Korean (validator failed):**
   > 저장 완료 — `docs/briefs/2026-04-23-feat-dark-mode-settings.md`,
   > 다만 구조 검증에서 2건 지적:
   >   ✗ <첫 번째 실패 메시지 그대로>
   >   ✗ <두 번째 실패 메시지 그대로>
   > 파일은 디스크에 있음. 내가 패치할까, 직접 고칠래?

2. If the user requests changes, apply them with `Edit` against the
   on-disk file. Do **not** re-render the full brief into chat — that
   defeats the point of save-then-review. Re-run the validator after
   each edit pass and report the delta.

3. The user owns "done." Do not stage or commit the file. Loop on
   Stage 6 until they explicitly stop.

**Why save-then-review:** an earlier iteration rendered the full brief
in chat for approval *before* writing to disk. In hands-on use that
flooded the conversation with markdown that renders poorly inside a code
fence and was awkward to edit conversationally. Writing to disk first
lets the user review in their editor (real markdown, real diff tools,
real inline edits) and lets the validator surface structural issues
immediately. The tradeoff — a file briefly on disk before approval — is
neutral: `docs/briefs/` is the intended home for these files, and the
commit step stays with the user.

---

## Template

See `references/template.md` for:

- The exact eight-required-section Markdown template.
- Per-section writing guidance (what good looks like, what not to write).
- Worked example of a filled brief.

The emitted brief is in English. Chat interaction language follows the
user's input.

---

## Work Types

See `references/work-types.md` for:

- The ten Conventional Commits types.
- Per-type agent behavior hints (why the type matters — it changes how the
  downstream coding agent approaches the work).
- Classification tips for ambiguous cases.

---

## Examples

See `examples/` for worked end-to-end scenarios (input → codebase review →
interview → output). Start with `examples/README.md` for the index.

---

## Structural Validator

`scripts/validate_brief.py` is a stand-alone Python 3 script (no external
deps) that verifies structural conformity of a saved brief. It is wired into
Stage 6 but can also be run ad-hoc against any existing brief:

```bash
python3 skills/task-brief-creator/scripts/validate_brief.py \
  docs/briefs/2026-04-23-feat-global-hotkey-system.md
```

Exit codes: `0` pass, `1` structural failure, `2` file I/O error.

Scope of the validator (deliberately structural only):

- Filename pattern, title format, type coherence across filename / title /
  section value, and slug length.
- Presence of required H2 sections + `In Scope` / `Out of Scope` H3s.
- Bullet content in narrative sections; `- [ ]` format in checklist
  sections; populated `Open Questions`.
- Optional `Constraints` heading shape.

Out of scope (still on the human): concreteness of bullets, whether
Out-of-Scope entries are real guardrails vs. filler, whether entry points are
legitimate, whether Acceptance Criteria are measurable.

For briefset mode, use `scripts/validate_briefset.py` on the parent file —
it validates the parent structure and re-runs `validate_brief.py`'s checks
transitively on every referenced child brief, so one invocation covers
the whole set:

```bash
python3 skills/task-brief-creator/scripts/validate_briefset.py \
  docs/briefs/2026-04-30-briefset-checkout-i18n.md
```

Same exit codes. See `references/briefset.md` for what the parent
validator checks and what stays on the human reviewer.

---

## Guardrails

- **Executable, not discursive.** The emitted document is a work instruction,
  not a memo about the work. If any section reads like a discussion summary,
  scope-negotiation log, planning note, or rationale essay, rewrite it until
  it directs concrete action. Prose that explains *why we are thinking about
  this* belongs in the PR description, not the brief.
- **Never fabricate file paths or PR numbers.** `Related Files / Entry Points`
  is mandatory because it is the downstream agent's starting route. If the
  codebase review does not surface at least one concrete file, directory,
  route, command, module, related brief, or confirmed proposed path, ask the
  user to provide or confirm the entry point before saving the brief.
- **Never infer Acceptance Criteria from thin air.** Vague criteria poison
  the downstream agent. Ask the user.
- **Never proceed past the Ambiguity Gate on a hunch.** Halting is the
  correct answer when anchors are missing.
- **Keep Out-of-Scope specific.** "Don't refactor unrelated code" is filler.
  "Do not change the `PaymentService` interface" is a real guardrail.
- **One brief per invocation, unless the input has multiple execution
  contexts.** If it does, switch to briefset mode (see
  `references/briefset.md`). Briefset mode is the supported way to
  handle multi-context work — do not stuff multiple unrelated tasks
  into a single brief, and do not nest briefsets (a child cannot become
  a parent).

---

## Pre-Save Checklist

Self-check before invoking `Write` in Stage 5. The structural validator
catches format errors after the fact; this list catches content gaps it
cannot see.

- [ ] Filename matches `YYYY-MM-DD-<type>-<slug>.md`.
- [ ] `<type>` is one of the ten Conventional Commits types.
- [ ] Title on line 1 starts with `[<type>]`.
- [ ] `Current State (As-Is)` and `Desired Outcome (To-Be)` are both
      populated and distinguishable.
- [ ] `Out of Scope` has at least one specific entry (or an explicit
      "None — self-contained." with rationale).
- [ ] `Acceptance Criteria` are measurable (checkable, not aspirational).
- [ ] `Related Files / Entry Points` entries are existing repo paths,
      verified references, or confirmed proposed paths.
- [ ] `Open Questions` uses `- None` only if the brief is genuinely
      unambiguous; otherwise populate it with real questions.
