---
name: task-brief-creator
description: >
  Generate a structured work-brief Markdown at `docs/briefs/` from planning
  notes or a rough task description. Nine sections keyed to Conventional
  Commits types so downstream coding agents switch behavior (refactor →
  preserve, fix → reproduce first, perf → measure first). Halts on vague
  input. Manual trigger only.
---

# Task Brief Creator

Produce a structured work-brief Markdown document under `docs/briefs/` that a
downstream coding agent (or a human engineer) can pick up and execute without
re-interviewing the requester.

The brief is the *handoff artifact*. Its job is to shrink the cost of the first
hour a coding agent spends on the task — routing it to the right files, fixing
the behavior envelope, and pre-answering the questions that would otherwise
bounce back to the requester.

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

The nine required H2 sections are: `Work Type`, `Current State (As-Is)`,
`Desired Outcome (To-Be)`, `Scope` (with `In Scope` / `Out of Scope` H3s),
`Related Files / Entry Points`, `Side Effect Checkpoints`, `Acceptance
Criteria`, `Open Questions`. `Constraints (optional)` may appear between
`Scope` and `Related Files / Entry Points` when task-specific constraints
exist.

---

## Workflow

### Stage 1 — Ambiguity Gate (HALT or CONTINUE)

Before any codebase work, check whether the input contains enough signal to
ground the brief. Use the **four-anchor heuristic**:

| Anchor | What it answers | Maps to |
|---|---|---|
| **PROBLEM** | What is wrong or what is changing? | § Current State (As-Is) |
| **GOAL** | What should be true when it's done? | § Desired Outcome (To-Be) |
| **SCOPE** | Where does this apply (module, feature area, user surface)? | § In/Out of Scope |
| **TARGET** | Which part of the system is touched (file, subsystem, layer)? | § Related Files / Entry Points |

Count how many anchors are derivable from the input. Derivable = a reasonable
engineer could answer the anchor after reading the input + skimming the repo.

- **3 or 4 anchors present** → **CONTINUE** to Stage 2. Missing anchor(s) get
  filled in Stage 3 via codebase review or Stage 4 via user questions.
- **2 or fewer anchors present** → **HALT**. Respond in the user's chat
  language naming exactly which anchors are missing, and ask for more input.
  Do NOT proceed through Stages 2–6 on an underspecified input. Example halt
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

### Stage 2 — Work Type Selection

Determine the Conventional Commits type. Consult
`references/work-types.md` for the full list and per-type behavior hints.

- If the input explicitly names a type (e.g., "this is a refactor"), use it
  but verify the input evidence agrees — if the user says "refactor" but
  describes a behavior change, confirm with one question.
- If the type is implicit, infer from the input and **confirm with the user**
  via a single short question before proceeding. Do not silently classify —
  the type determines downstream agent behavior.

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
4. Capture a short As-Is picture: how the relevant code is shaped today,
   2–5 bullets max.
5. Capture 2–6 Related File / entry-point hints with one-line purposes.

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
- **Out of Scope** — the most valuable guardrail for the downstream agent.
  Offer a proposed out-of-scope list based on the input and let the user
  edit.
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

- The exact nine-section Markdown template.
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
  section value.
- Presence of required H2 sections + `In Scope` / `Out of Scope` H3s.
- Bullet content in narrative sections; `- [ ]` format in checklist
  sections; populated `Open Questions`.

Out of scope (still on the human): concreteness of bullets, whether
Out-of-Scope entries are real guardrails vs. filler, whether file paths
actually exist in the repo, whether Acceptance Criteria are measurable.

---

## Guardrails

- **Never fabricate file paths or PR numbers.** If the codebase review did
  not surface a path, leave the `Related Files / Entry Points` entry blank
  and add an Open Question instead.
- **Never infer Acceptance Criteria from thin air.** Vague criteria poison
  the downstream agent. Ask the user.
- **Never proceed past the Ambiguity Gate on a hunch.** Halting is the
  correct answer when anchors are missing.
- **Keep Out-of-Scope specific.** "Don't refactor unrelated code" is filler.
  "Do not change the `PaymentService` interface" is a real guardrail.
- **One brief per invocation.** If the input describes multiple independent
  tasks, ask the user which one to brief, or offer to split into multiple
  briefs.

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
- [ ] `Related Files / Entry Points` entries all exist in the repo
      (verified by the review step) — or are flagged as Open Questions.
- [ ] `Open Questions` is empty only if the brief is genuinely
      unambiguous; otherwise populate it (use `- None` if truly none).
