---
name: task-brief-creator-caveman
description: >
  Generate a structured work-brief Markdown at `docs/briefs/` from planning
  notes or a rough task description, with the brief body written in
  caveman **full** mode as a register-only transform that preserves every
  fact, bullet, and section depth from the normal-mode equivalent. Eight
  required sections keyed to Conventional Commits types so downstream
  coding agents switch behavior (refactor → preserve, fix → reproduce
  first, perf → measure first). Briefset mode emits a parent
  execution-management document plus N child briefs when the input
  describes multiple execution contexts. Chat / questions / status
  reporting stay in normal prose — caveman applies to the saved file only.
  Use only when the user explicitly asks for the caveman register or
  invokes this skill by name; for normal-prose briefs use
  task-brief-creator instead.
---

# Task Brief Creator (Caveman)

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
Caveman tightens *prose* further; it never tightens *enumeration*.

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

1. Use this file for the stage order, output contract, save flow, caveman constraints, and guardrails.
2. Read [references/caveman-style.md](references/caveman-style.md) before composing or patching saved brief prose.
3. Read [references/work-types.md](references/work-types.md) during Stage 2 when the work type is not obvious or when the type changes downstream behavior.
4. Read [references/briefset.md](references/briefset.md) during Stage 1 when multiple execution contexts are plausible.
5. Read [references/bloat-decomposition.md](references/bloat-decomposition.md) only after a candidate child brief is independently executable but still looks oversized or mixed.
6. Read [references/stage-4-interview.md](references/stage-4-interview.md) before presenting user-owned decisions.
7. Read [references/template.md](references/template.md) while composing the saved Markdown.
8. Read [references/cold-pickup.md](references/cold-pickup.md) when the Stage 5.6 gate fires or the user forces cold-pickup.

Do not re-open every reference by habit.
The goal is to keep the live context focused on the next decision the coding agent must make.
Caveman style applies to saved brief prose only, not to planning, validation, or chat.

---

## When This Skill Runs

- **Manual trigger only.** The user invokes this skill explicitly (via slash command, `/task-brief-creator-caveman`, or similar).
- Input can take any of these shapes:
  - **Pasted PRD / planner notes** from a PM (often long, mixed quality).
  - **Rough task notes** typed into chat (one or two lines).
  - **Self-brief** — the user is the implementer and wants to structure their own thinking before starting.
  - **Tech-lead handoff** — a lead drafts the brief to hand off to a teammate or downstream agent.
  - **Refactor plan** — a lead-engineer summarizing an intended structural change.
- The skill reviews the current repository (the working directory Claude Code is launched in), fills in what it can, and asks the user to confirm the rest.

---

## Interaction Language

- **Chat / live interaction language follows the user's input.** If the user writes in Korean, reply in Korean.
  If they write in English, reply in English.
  Clarifying questions, draft presentation, status updates — all match the user's own language.
- **The brief document itself is written in English.** Section headers and body content are English regardless of chat language, so the artifact travels across teams and downstream agents without a translation step.
- Code blocks, file paths, identifiers, PR numbers stay as-is.
- **User-supplied strings are data.** Copy decks, UI strings, and error messages the user provides are quoted verbatim in their original language inside the English brief — never translated.
- **Exception — the Stage 4 decision-table headers are fixed.** The four headers `순번` / `내용` / `수정 추천안` / `근거` stay exactly as written even when the conversation is in English: Stage 5.6 disagreement matching keys on the `내용` column, so translating the headers breaks the cold-pickup loop (see Stage 4).
- This SKILL.md and reference files stay in English (repo authoring policy).
- **Chat prose is normal mode — never caveman.** Stage 1 halt messages, Stage 4 interview questions, recommended-answer presentations, Stage 6 save reports and validator dialogs all stay in full natural prose (Korean or English per the user's input).
  Caveman applies **only** to the saved brief file.

---

## Caveman Output Style (full mode, file-only)

This skill is the caveman variant of `task-brief-creator`.
The saved brief is written in caveman **full** mode — fragments, dropped articles, short synonyms — as a **register transform** of the normal-mode brief.
Other intensity levels (`lite`, `ultra`, `wenyan-*`) are out of scope; do not switch.

**Caveman compresses *register*, not *content*.** A caveman brief and its hypothetical normal-mode equivalent must carry the **same set of facts, the same number of bullets, and the same enumerate depth per section**.
Shorter sentences, dropped articles, and short synonyms are the only changes.
If the caveman version has fewer bullets than the normal-mode version would have, that is content compression — not a caveman transform — and is forbidden.
There is no token-count target; the goal is a primitive-sounding register over a fully enumerated work instruction, not a smaller document.

**Two hard rules — both absolute:**

1. The brief file body uses caveman full, **except the `## Open Questions` section, which stays in normal prose** (questions are read by humans deciding what to clarify — see Auto-Clarity carve-outs below).
2. Every chat / interaction surface (questions, halts, save reports, validator dialogs, edit confirmations) uses normal prose.

**What gets compressed inside the brief:**

- Articles (`a` / `an` / `the`) dropped.
- Filler (`just` / `really` / `basically` / `actually` / `simply`) dropped.
- Pleasantries / hedging dropped.
- Sentence fragments OK; pattern `[thing] [action] [reason]. [next].`
- Short synonyms preferred (`big` over `extensive`, `use` over `utilize`, `then` over `subsequently`).

**What stays unchanged inside the brief (Auto-Clarity carve-outs):**

- Code blocks, inline code, file paths, function names, identifiers.
- PR numbers, URLs, commit hashes.
- Error strings (quoted exact).
- `Acceptance Criteria` / `Side Effect Checkpoints` checklist items — caveman compression OK on the prose, but order-sensitive multi-step verification stays disambiguated.
  If conjunction loss changes meaning, drop back to normal for that bullet.
- `Reproduction` steps where step order matters.
- `Behavior Contract` invariants and verification methods.
- `Constraints` legal / API-shape constraints.
- Section headers, the title `# [<type>] <title>`, and the `## Work Type` value (`feat`, `refactor`, …).
- The escape-hatch token `- N/A — <reason>` for type-conditional sections.
- The entire `## Open Questions` section body.
  Questions are read by humans deciding what to clarify; caveman fragments lose the nuance that makes a question answerable.
  Write each bullet as a complete, naturally phrased question.

When in doubt — if compression creates technical ambiguity — write that bullet in normal prose.
Caveman never wins over correctness.

See `references/caveman-style.md` for the full conversion rules, section-by-section guidance, and good/bad examples.

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
  Caveman never merges bullets — it shortens each bullet's prose.
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

If briefset signals are strong, recommend briefset mode and ask the user to choose before Stage 2 instead of switching silently.
If the candidate contexts are fully independent — no ordering, no dependencies, no shared conflict hotspots — recommend separate single-brief invocations (one per task) instead of a briefset: a parent whose coordination sections are all `- None — <reason>` adds overhead without value.
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
  Low-confidence means two or more candidate types remain plausible **and** they would force different type-conditional sections or downstream behavior profiles; otherwise treat the inference as high-confidence.

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
4. Render the complete template from `references/template.md` and write the file (English section headers, English body **in caveman full mode** — see `references/caveman-style.md` for conversion rules and the Auto-Clarity carve-outs that stay in normal prose).
5. **Run the structural validator** — a fast smoke test for the template contract:

   ```bash
   python3 <skill-dir>/scripts/validate_brief.py docs/briefs/<filename>.md
   ```

   `<skill-dir>` is the installed skill package directory — the directory containing this SKILL.md (resolve it from wherever this skill was loaded, e.g. `~/.claude/skills/task-brief-creator` or a plugin cache).
   Never assume the user's repository contains the script: the brief lives in the user's repo, the validator lives with the skill.

   - Exit **0** → continue to Stage 5.5; the validator result is reported in the Stage 6 banner.
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
Caveman compresses *how* the brief reads, never *what* it contains — so this self-check is identical to the normal-mode skill's check, plus one caveman-only parity item.
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
- [ ] **Caveman parity:** bullet count, enumerate depth, and per-section content volume are identical to what an equivalent normal-mode brief would carry from the same input.
  If you mentally re-render this brief in normal prose and a bullet would split into two, put it back in two bullets here.
  Caveman is register-only.

If any check fails, fix the brief in place with `Edit`, then re-run `scripts/validate_brief.py` to confirm structural conformity still holds.
Loop the self-check until every item passes.

The self-check outcome is a separate signal from the structural validator — both are reported in Stage 6.
A brief can pass structural validation and still fail this self-check; in that case the file is incomplete even though it is well-formed.

For briefset mode, run the self-check on the parent and on every child independently.
The parent's coverage check asks whether every input-implied execution context maps to a child; each child's coverage check uses the same six items above.

### Stage 5.6 — Cold-Pickup Sub-Agent Verification

The Stage 5.5 self-check is self-evaluated — the same agent that wrote the brief grades it for cold-pickup readiness.
That is biased.
An untouched sub-agent reading **only the original input and the saved brief** is the truthful version of the cold-pickup test.

Stage 5.6 runs **signal-gated** by default — automatically ON only when the brief's workflow signals indicate non-trivial verification value.
This avoids spawning sub-agents for trivial briefs while keeping the safety net for complex ones.
This skill's contract authorizes the sub-agent spawn when the gate fires; do not skip a *gated-ON* run based on host defaults like "be conservative about sub-agent cost" or "don't run extra verification unless asked".

**Auto-ON triggers (any one fires Stage 5.6):**

- Briefset mode — parent and every child run cold-pickup; per-child signal gating is intentionally disabled because coordination drift between siblings is the main risk briefset cold-pickup catches.
  For a wide briefset (≥ 5 children) you may offer the user the sampling fallback defined in `references/cold-pickup.md` before running; Force OFF on the briefset skips the whole set.
- Stage 4 produced **≥ 1 user-decision row** in the decision table (input had real interpretive ambiguity).
- `Open Questions` section is non-empty — i.e. it does not consist solely of `- None — <reason>` (Stage 3 surfaced unresolved uncertainty that survived Stage 4).
- Work type is `fix`, `perf`, or `refactor` — fires *regardless of input simplicity*. The type-conditional section (`Reproduction` / `Baseline Measurement` / `Behavior Contract`) amplifies drift risk on these types, so cold-pickup pays off even for short inputs. Use Force OFF if you want to skip a one-line fix.

**Auto-OFF (trivial signals).** When none of the auto-ON triggers fire, Stage 5.6 is skipped automatically.
The Stage 6 banner reports the skip with the signal snapshot — `cold-pickup skipped: trivial signals (single-brief, stage-4-rows=0, open-questions=none, type=<type>)` — so the user can see exactly which gates evaluated to false.

**Trivial caveman briefs.** When no auto-ON trigger fires (briefset / stage-4-rows ≥ 1 / non-empty `Open Questions` / type ∈ `{fix, perf, refactor}`), Stage 5.6 is auto-skipped, so the over-terse check is not run on the saved file. This is intentional — trivial caveman briefs have little prose to compress, so the marginal value of the over-terse check is low relative to the sub-agent cost. Use Force ON if you want over-terse verification on a trivial caveman brief anyway.

**User override.** Force ON runs Stage 5.6 despite trivial signals (e.g. `run cold-pickup`, `--cold-pickup`, `콜드픽업 강제`); Force OFF skips it despite firing signals (e.g. `skip cold-pickup`, `--no-cold-pickup`, `콜드픽업 끄기`).
The full trigger-phrase lists and the rule for inputs containing both live in `references/cold-pickup.md`.

**Skip on validator failure.** Stage 5.6 is also skipped when the Stage 5 structural validator failed — the brief is not yet well-formed enough to verify.

Reasons that are **not** valid skips when a gate has fired: token budget, latency, inferred host policy, "the brief looks fine".
If a gate fires and Stage 5.6 is skipped anyway, the Stage 6 banner is wrong and the loop is broken.

**Mechanism — when the gate fires, read `references/cold-pickup.md` (report schema, pass bookkeeping, routing table, termination triggers, banner formats), then:**

1. Snapshot the saved brief for this pass (rollback anchor — see *Pass Bookkeeping and Rollback* in the reference).
2. Spawn an `Explore` or `general-purpose` sub-agent.
   If the host cannot spawn sub-agents, use the *Sub-Agent Unavailable Fallback* in the reference — never silently skip a gated-ON run.
3. Hand it **only the original user input or planning notes plus the brief path** — no Stage 3 uncertainty register, no Stage 4 decisions, no suspected gaps, no decomposition rationale, and no Stage 5.5 result.
   Do not include hints such as what to inspect, what might be missing, or which split you expect the sub-agent to prefer.
   For briefset mode, hand the parent and every child path one at a time; each file runs its own cold-pickup pass.
4. Collect the YAML report (schema and sub-agent rules in the reference; the caveman variant adds `over_terse_bullets` on top of the standard schema — see below) and diff it against the original input + Stage 3 uncertainty register + Stage 4 decisions.

**Caveman extension.** The sub-agent prompt adds one item to the standard four — *are any bullets so terse they hide intent?*.
Caveman is a register transform; if compression made a bullet ambiguous, the sub-agent flags it and the bullet is rewritten in normal prose under the Auto-Clarity carve-out before the brief passes Stage 5.6.
The report gains one caveman-specific list on top of the standard schema in the reference:

```yaml
over_terse_bullets:
  - id: t1
    bullet: "<direct quote of the bullet from the brief>"
    reason: <why caveman compression made intent ambiguous>
```

Every `ask_backs[*]`, `missing_concerns[*]`, and `over_terse_bullets[*]` **must include a direct-quote `evidence` / `bullet`** — paraphrases are not accepted; if no quote applies, drop the item.
`verdict: clean` is only valid when `ask_backs`, `missing_concerns`, and `over_terse_bullets` are all empty, and the termination triggers in the reference count unrejected `over_terse_bullets` alongside `ask_backs` + `missing_concerns` (Regression, Stable findings, Clean pass).

**Drift handling.** When the report's `verdict` is `needs_changes` or `blocked`, or when any unrejected `ask_backs` / `missing_concerns` / `over_terse_bullets` survive routing — `Edit` the saved brief in place to close the gap, re-run `validate_brief.py`, and re-run cold-pickup.
Route every `ask_backs[*]` / `missing_concerns[*]` through the routing table in the reference before patching, including the disagreement-vs-drift check against answered Stage 4 rows.
`over_terse_bullets[*]` are caveman-register findings; they never match a Stage 4 row `내용`, so they are always treated as drift — patch in place under the Auto-Clarity carve-out, never as disagreement.
Loop until one of the six termination triggers in the reference fires (Regression, Oscillation, Stable findings, Clean pass, No-op pass — evaluated in that priority order) or the hard cap of **5 passes** is reached.

Cold-pickup never overrides a Stage 4 decision the user already locked, never invents Acceptance Criteria, Side Effect Checkpoints, or Out-of-Scope guardrails the input did not imply, and never silently rewrites `Open Questions` — drift fixes either resolve a question into another section or leave the question intact for the user.

**Reporting.** The cold-pickup outcome integrates into the Stage 6 save banner alongside the structural validator and the Stage 5.5 self-check, using the banner phrasings in `references/cold-pickup.md`.
For briefset mode, the banner uses the collapsed `parent + K/N children` format from the reference — one summary line plus details only on flagged children, not one line per child.
The caveman pass-everything line additionally reports over-terse status: `cold-pickup: 1/1 parent + N/N children verdict:clean (no ask-backs, no missing concerns, no over-terse bullets)`.

### Stage 6 — Review + Iterate

The brief is on disk.
Hand off to the user for review.

1. Report the path, a one-line summary (work type + title), the structural validator result, the Stage 5.5 self-check result, **and the Stage 5.6 cold-pickup result**.
   Use the user's chat language.
   All three signals are reported together so the user can see whether the file is well-formed, complete, *and* cold-pickup-ready.

   **English (validator + self-check + cold-pickup passed):**
   > Saved — `docs/briefs/2026-04-23-feat-dark-mode-settings.md` (`feat`: Dark mode toggle in Settings; structural validation passed; content self-check passed — N input concerns covered, caveman parity OK; cold-pickup terminated with `clean_pass` after 1 pass (no ask-backs, no missing concerns, no over-terse bullets)).
   > Open it and let me know if anything needs editing.

   Banner termination trigger reflects the actual loop outcome — `clean_pass` (normal), `regression`, `oscillation`, `stable_findings`, `no_op`, or `hard_cap`. Any non-`clean_pass` trigger means residual concerns must follow in the banner as bullet items.

   **Korean (validator + self-check + cold-pickup passed):**
   > 저장 완료 — `docs/briefs/2026-04-23-feat-dark-mode-settings.md` (`feat`: Dark mode toggle in Settings; 구조 검증 통과; 내용 자체 검증 통과 — 입력 항목 N개 모두 매핑, 문체 변환 동등성 확인; cold-pickup `clean_pass`로 1회 만에 종료 (ask-back 없음, missing 없음, 과압축 지적 없음)).
   > 파일 열어보고 고칠 부분 있으면 알려줘.

   **English (validator + self-check passed, cold-pickup auto-skipped on trivial signals):**
   > Saved — `docs/briefs/2026-04-23-feat-dark-mode-settings.md` (`feat`: Dark mode toggle in Settings; structural validation passed; content self-check passed — N input concerns covered, caveman parity OK; cold-pickup skipped: trivial signals (single-brief, stage-4-rows=0, open-questions=none, type=feat)).
   > Tell me `run cold-pickup` or `--cold-pickup` if you want the sub-agent verification anyway.

   **English (validator failed):**
   > Saved — `docs/briefs/2026-04-23-feat-dark-mode-settings.md`, but the structural validator flagged 2 issue(s): ✗ <first failure verbatim> ✗ <second failure verbatim> The file is on disk.
   > Want me to patch these, or will you edit directly?

   Mirror any banner into the user's chat language as the Korean example above shows — translate the prose, keep paths, filenames, and technical fields (`trivial signals (...)`, termination triggers, validator messages) verbatim.

   When the structural validator fails, Stage 5.5 and Stage 5.6 are **skipped** — the brief is not yet well-formed enough to run content or cold-pickup checks against.
   The banner stays as shown; do not append `self-check skipped` / `cold-pickup skipped` lines in this case.

   If the structural validator passed but the Stage 5.5 self-check surfaced gaps that you fixed in place, mention what you patched so the user knows the brief was tightened before handoff (e.g., "self-check found 2 input concerns missing from In Scope and one bullet that had been merged for caveman compression; restored them, re-validated").
   If Stage 5.6 patched the brief after cold-pickup drift, report it the same way (e.g., `cold-pickup flagged 2 gap(s) and 1 over-terse bullet; patched in place`).
   If the user used Force OFF triggers, report `cold-pickup skipped per user request`.
   If Stage 5.6 was auto-skipped because no auto-ON trigger fired, report `cold-pickup skipped: trivial signals (...)` with the signal snapshot shown in the banner case above.

2. If the user requests changes, apply them with `Edit` against the on-disk file.
   Do **not** re-render the full brief into chat — that defeats the point of save-then-review.
   Re-run the validator after each edit pass and report the delta.

3. If the saved single brief contains `Open Questions` that require a user decision (after any Stage 5.6 patches have landed), present them immediately after the save report using the same four-column decision table from Stage 4:

   ```markdown
   | 순번 | 내용 | 수정 추천안 | 근거 |
   |---|---|---|---|
   | 1 | <Open Question requiring user decision> | <recommended patch to apply to the brief> | <why this cannot be delegated safely> |
   ```

   After the user answers, patch the saved brief in place, move resolved questions into the appropriate sections, leave only genuinely unresolved or delegated questions in `Open Questions`, and re-run the validator plus Stage 5.5 self-check.
   Chat stays normal prose; only saved brief body prose uses caveman full mode.

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
It runs as step 5 of Stage 5 (save + validate) but can also be run ad-hoc against any existing brief.
Always resolve the script path against `<skill-dir>` — the installed skill package directory containing this SKILL.md — never against the user's repository:

```bash
python3 <skill-dir>/scripts/validate_brief.py \
  docs/briefs/2026-04-23-feat-global-hotkey-system.md
```

Exit codes: `0` pass, `1` structural failure, `2` file I/O error.

Scope of the validator (deliberately structural only):

- Filename pattern, title format, type coherence across filename / title / section value, and slug length.
- Presence and template order of required H2 sections + `In Scope` / `Out of Scope` H3s; duplicate H2 sections are rejected.
- Type-conditional section (`Reproduction` / `Baseline Measurement` / `Behavior Contract`) present and populated for the matching type.
- Bullet content in narrative sections; `- [ ]` format in checklist sections; populated `Open Questions` with `- None — <reason>` when no questions remain.
- Inline-code paths under `Related Files / Entry Points` resolve on disk (skipped when the bullet carries the exact literal token `(proposed)`).
- Optional `Constraints` heading shape.
- Warning only: `Out of Scope` bullets without `[hard]` or `[deferred]` classification.
  The validator does not judge whether the classification is semantically correct.

Out of scope (still on the human): concreteness of bullets, whether Out-of-Scope entries are real guardrails vs. filler, whether entry points are *good* (the path-existence check only catches fabricated paths, not poorly-chosen ones), whether Acceptance Criteria are measurable, whether the type-conditional section's content is sufficient.

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
- **Never infer Acceptance Criteria from thin air.** Vague criteria poison the downstream agent.
  Ask the user.
- **Never proceed past the Ambiguity Gate on a hunch.** Halting is the correct answer when anchors are missing.
- **Keep Out-of-Scope specific.** "Don't refactor unrelated code" is filler.
  "Do not change the `PaymentService` interface" is a real guardrail.
- **Keep implementation judgment out of Out-of-Scope.** `Out of Scope` tells the downstream coding agent what not to do.
  Put bounded implementation choices in `Constraints`, and user-owned unresolved choices in `Open Questions`.
- **One brief per invocation, unless the input has multiple execution contexts.** If it does, recommend briefset mode and ask the user to choose (see `references/briefset.md`).
  Briefset mode is the supported way to handle multi-context work — do not stuff multiple unrelated tasks into a single brief unless the user explicitly chooses single-brief after the recommendation, and do not nest briefsets (a child cannot become a parent).
  When the contexts share no dependency, no ordering, and no conflict hotspot, recommend separate single-brief invocations instead of a briefset (see Stage 1).
- **Decision table does not bypass the ambiguity gate.** Halt-eligible inputs still halt at Stage 1.
  Do not try to reconstruct missing PROBLEM / GOAL / SCOPE / TARGET through a large decision table — the gate exists precisely to prevent that failure mode.
  See `references/stage-4-interview.md` for the table rules and termination conditions.
- **Caveman never leaks into chat.** Stage 1 halt messages, Stage 4 questions, recommended answers, Stage 6 save reports, validator dialogs and edit confirmations are full natural prose.
  If the user later asks for clarification of the brief, paraphrase a normal-prose summary in chat — do not just paste the caveman bullet back.
  Caveman is the *file's* register, not the conversation's.
- **Caveman never overrides correctness.** If full-mode compression creates technical ambiguity in a bullet (order-of-operations risk, ambiguous referent, irreversible-op warning), write that bullet in normal prose.
  Auto-Clarity rule: compression yields when meaning is at risk.

---

## Pre-Save Checklist

Self-check before invoking `Write` in Stage 5.
The structural validator catches format errors after the fact; this list catches content gaps it cannot see.

- [ ] Filename matches `YYYY-MM-DD-<type>-<slug>.md`.
- [ ] `<type>` is one of the ten Conventional Commits types.
- [ ] Title on line 1 matches `# [<type>] <title>`.
- [ ] `Current State (As-Is)` and `Desired Outcome (To-Be)` are both populated and distinguishable.
- [ ] If type is `fix` / `perf` / `refactor`, the type-conditional section (`Reproduction` / `Baseline Measurement` / `Behavior Contract`) is present and populated — `- N/A — <reason>` if genuinely none.
- [ ] `Out of Scope` has at least one specific entry (or an explicit "None — self-contained." with rationale).
  Use `[hard]` for must-not-touch guardrails and `[deferred]` for follow-up work when the distinction matters.
- [ ] `Acceptance Criteria` are measurable (checkable, not aspirational).
- [ ] `Related Files / Entry Points` entries are existing repo paths, verified references, or confirmed proposed paths.
  Paths under inline-code that are not yet created carry the exact literal token `(proposed)` so the structural validator does not flag them as fabricated — variants like `(proposed edit)` are not recognized.
  Each entry routes the agent's first read or first edit, not just "related file" context.
- [ ] `Open Questions` uses `- None — <reason>` only if the brief is genuinely unambiguous; otherwise populate it with real questions.
- [ ] Body prose **outside `## Open Questions`** is in caveman full mode (articles/filler/pleasantries dropped, fragments OK, short synonyms).
- [ ] `## Open Questions` bullets stayed in normal prose — each question is complete, naturally phrased, and unambiguous.
- [ ] Auto-Clarity carve-outs stayed in normal prose (code, paths, identifiers, error strings, quantitative expressions, ordered repro steps, behavior contracts, constraints with semantic risk).
- [ ] Section headers, title, and `## Work Type` value were not caveman-rewritten.
- [ ] `- N/A — <reason>` escape hatch (where used) keeps the literal `N/A —` token; only the reason after the em dash is caveman.
- [ ] **Enumerate parity:** bullet count and per-section enumerate depth match what an equivalent normal-mode brief would carry.
  No bullet was merged, no concern was dropped, and no qualifier was removed for register reasons.
  Caveman compressed *how* each bullet reads, not *how many* bullets there are.

## Post-Run Checklist (before the Stage 6 banner)

Evaluated after Stage 5.5 / 5.6 have run or been skipped, immediately before reporting the Stage 6 banner — these items cannot be checked before `Write`.

- [ ] Cold-pickup ran when any auto-ON trigger fired (briefset / stage-4-rows ≥ 1 / non-empty `Open Questions` / type ∈ `{fix, perf, refactor}`) OR the user used Force ON triggers.
- [ ] Cold-pickup auto-skipped with `trivial signals (...)` snapshot when no auto-ON trigger fired and no Force ON was used.
- [ ] Cold-pickup skipped per user request (`cold-pickup skipped per user request`) when Force OFF was used, even if auto-ON triggers would have fired.
- [ ] Stage 6 banner reflects what actually ran — a silent skip on a fired gate is **not** acceptable.
