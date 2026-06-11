---
name: feature-design-doc
description: Create, update, or fact-check a Feature Design Doc that captures product/system design decisions for downstream code agents. Use whenever the user mentions "기능 문서", "기능 설계 문서", "Feature Design Doc", "FDD", "design doc", or asks to write, draft, generate, update, revise, review, validate, fact-check, audit, or normalize a feature document — even when the user does not explicitly use the word "design", and especially right after a feature was ideated and implemented in-session (vibe-coding) and now needs documenting. Trigger on near-misses like "기능 정리 문서 좀 써줘", "이 문서 좀 검토해줘 우리 기능 design 관련이야", or "design doc 좀 만들어볼래". NOT for system/architecture design docs, RFCs, implementation plans, task lists, or READMEs — the subject must be a single product feature. This skill enforces that the artifact remains a decision source, not an implementation plan or task list, so use it whenever the working artifact is meant to drive what a feature *is* rather than *how it gets built*.
---

# Feature Design Doc

A Feature Design Doc (FDD) is the **source of design decisions** for a feature — the artifact a code agent should read first to understand *what the feature is and why*. It earns its keep whether written before implementation or right after a feature was built: in iterative work, the doc saved at the end of one session is the decision source for the next.

This skill creates, updates, or fact-checks an FDD against a fixed template, and protects the boundary between **design decisions** and **implementation actions**. That boundary is the single most common failure mode for this artifact, so most of the guidance below is about defending it.

## Core principle

> Feature Design Doc is the **decision source**. Implementation Plan derives task ordering from it. Task Breakdown comes out of the Implementation Plan.

Concretely, an FDD captures:

- Product behavior, user flows, domain concepts
- Policy decisions that resolve ambiguity
- Cross-cutting concerns (security, privacy, permissions, observability, accessibility, i18n)
- Alternatives considered and why they were rejected
- Version-specific scope, risks, and open questions
- Platform constraints when they materially shape the design

It does **not** capture:

- File paths, function names, module names
- Task ordering, PR breakdowns, ticket IDs
- "Step 1: create X. Step 2: modify Y." sequences
- Code-agent commands ("run `pnpm test`", "edit `auth.ts`")

When in doubt: would a code agent reading this doc need to *make a product decision*, or *take a coding action*? FDD is about the first; everything else is downstream.

## Decide the mode first

**Scope gate before anything else**: this skill documents a single product feature. If the request is actually a system/architecture design doc, a DB or API schema design, an RFC, an implementation plan, or a README, say that the FDD format does not fit and stop — do not force the template onto a non-feature subject.

When invoked, identify which mode applies. Each mode has a different shape of output:

| Mode | Trigger signal | What to produce |
| --- | --- | --- |
| **Create** *(default)* | User describes a new or just-built feature, gives a problem statement, or asks to "write/draft/generate" a doc — or the signal is ambiguous | A complete Markdown FDD saved to `docs/FDD/<kebab-case-feature-name>.md` |
| **Update** | An FDD already exists for the feature and the user asks to reflect new decisions, changed behavior, or a just-modified implementation | The same file revised in place (append-oriented — see "Update workflow") plus a new `Revision History` entry |
| **Fact-check** | User points at an existing doc and asks to "review/validate/audit/check"; or attaches a doc path explicitly | A findings report grouped by severity, citing affected section names *and external sources* |
| **Normalize** | User has a doc that mixes design + implementation, or sections are mislabeled — usually surfaced from a Fact-check first | A revised doc plus a short prose summary of what moved where |

**Default to Create when uncertain** — but if a file already exists at the target path, default to Update instead. Only ask which mode to use if there is literally no feature signal *and* no document attached (e.g., the user just typed "기능 문서" with no context). For everything else, infer and proceed — wrong-mode cost is recoverable, but interrogation is not.

## The reference template

Load [`references/feature_design_doc_template.md`](references/feature_design_doc_template.md) before creating or fact-checking. That file is the canonical structure; this SKILL.md only adds *how to use it well*.

Section optionality:

- Sections **1–13** are required in the default `full` profile (see "Profiles" below).
- **`14. Platform Design`** is required when the feature is cross-platform, OS-sensitive, hardware-sensitive, browser-sensitive, runtime-sensitive, or platform API-heavy. Otherwise omit — but keep the remaining section numbers unchanged; never renumber.
- **`15. Result Semantics`** is required when the feature has meaningful operation states (partial success, restore results, sync states, migration outcomes, user-visible failures). Otherwise omit.
- **`16. Future Extensions`** is for plausible future product directions only. Do not duplicate every `Out of Scope` bullet here.
- **`Revision History`** is optional at first save, required from the first update onward (see "Update workflow").
- **`Appendix`** is for supporting material that does not belong in the main narrative, including the non-normative `Code Map` (see the leakage exception below).

### Profiles

The frontmatter `profile` key selects the required-section contract; the validator enforces whichever is declared.

- **`profile: full`** *(default)* — sections 1–13 required as listed above.
- **`profile: compact`** — for small features. Sections 2, 3, 4, 7, 8, 9, 10, 12, 13 stay required; **1, 5, 6 become optional**; section 11 stays required but may be condensed to one line per concern (`- Security: Not applicable: <reason>`). Section numbers never change — omit, don't renumber.

Use compact only when ALL of these hold:

- single platform, no platform-conditional behavior
- no new or changed persisted data model
- no auth/permission surface change
- no external standard or compliance involvement (OAuth, WCAG, GDPR, ...)
- one primary user flow

If any fails, use full. When unsure, use full — compact exists to keep small docs honest, not to make big docs cheap.

## Section responsibility map

The hardest mistake to catch is putting the right content in the wrong section. The three sections most often confused are `Feature Definition`, `Non-Goals`, and `Scope`. Use this map to keep them separate:

| Statement type | Belongs in |
| --- | --- |
| "This is a *kind of* X" / "This is *not a kind of* Y" (identity) | `Feature Definition` → "This feature is" / "This feature is not" |
| "We could have done X but chose not to" (rejected aspiration) | `Goals & Non-Goals` → "Non-Goals" |
| "Not in v1.0, planned later" (release boundary) | `Scope` → "Out of Scope for [Version]" |
| "We considered approach X but chose Y" (rejected design path) | `Alternatives Considered` |
| "When situation is ambiguous, decide this way, because..." (rule with rationale) | `Policy Decisions` |
| "The system needs to handle this failure category" (design-level) | `Design` → "Failure Handling" |
| "User-visible outcome state" (success/partial/failed) | `Result Semantics` |

If the same statement seems to fit multiple sections, re-read this map. It almost always belongs in only one.

## Creation workflow

### Phase 0 — Identify the input source

Create has two entry paths. Pick one before doing anything else:

- **Post-implementation** *(the common case)* — the feature was just ideated and built in this session (vibe-coding), or already exists in the codebase. The primary sources are the session conversation, the implementation diff, and git history. **Harvest first, ask second**: extract the Phase 1 answers, policy decisions, and rejected alternatives from those sources, present everything you inferred as one confirmation batch, and ask only for what genuinely cannot be recovered.
- **Pre-implementation** — the feature is still an idea; there is no code or session record to harvest. Run Phase 1 as an interview.

### Phase 1 — Required inputs (single batched round)

Before drafting, settle the 5 minimum decisions:

1. **Feature name** (short label that becomes the filename in kebab-case)
2. **One-sentence definition** ("[Feature] is ...")
3. **Problem statement** — what's broken without it
4. **Primary users / actors** — who experiences this feature
5. **Target version or release** — the scope boundary for "v1 vs later"

In the post-implementation path, fill all five from the session and the code first; the "batch" becomes a single confirmation message ("here is what I inferred — correct anything wrong") rather than five questions.

When you do need to ask, group everything into **one round**. `AskUserQuestion` accepts at most 4 questions per call, so either reduce the open items below five first (infer what you can) or split 4+1; free-text items (name, definition, problem statement) work better as a single grouped plain message than as option lists. Do not interrogate one-by-one — that frays the conversation and the user already knows roughly what they want to tell you. If the user's initial message already answers some of these, only ask for the gaps.

If no live user is reachable (subagent, CI, automation), do not stall in Phase 1: fill the five from available sources, mark inferences explicitly, and use `[NEEDS INPUT: ...]` for true unknowns — Phase 4 defines how marked drafts hand off.

For item 5, solo or continuous-delivery work with no release train defaults the boundary to `as implemented (YYYY-MM-DD)`.

### Phase 2 — Research before drafting

After Phase 1, do targeted research **in parallel** so the draft isn't built on speculation. Scope the research by what the feature actually touches.

**Post-implementation features — read the implementation first.** The just-written code is the primary source of truth: extract `Behavior`, `Policy Decisions`, and `Failure Handling` from what the code actually does, not from memory of the discussion. Where the session decided one thing and the code does another, surface the mismatch — ask the user when interactive, otherwise record it in `Risks & Open Questions` as a known deviation. Mine the session conversation for approaches that were tried or discussed and dropped; they feed `Alternatives Considered` (evidence gate in Phase 3). The research below still applies, but it grounds a record of what was built rather than speculation about what might be.

**Always do — codebase research:**

- Identify existing features named in `Relationship to Existing Features` and verify they exist in the repo. Use Serena/Grep to find their primary modules.
- For data-model design: look for existing schemas, models, types that this feature will interact with.
- For policy decisions involving config/flags: search for current configuration sites.
- For platform-sensitive features: check what platforms the repo already supports.

The point of codebase research is to ground the FDD in **what is actually true now**, so design decisions reference reality rather than guesses.

**Conditional — web research:**

Do web research **only when the feature touches a well-known external standard or protocol**. Examples that warrant it:

- Auth: OAuth 2.0, OIDC, PKCE, FIDO2/WebAuthn, JWT, SAML
- A11y: WCAG, ARIA
- API/protocol: OpenAPI, JSON-RPC, gRPC, MQTT
- Privacy/compliance: GDPR, CCPA, HIPAA
- File formats / cryptography / browser APIs that have a public spec

If the feature is purely internal (e.g., "Q4 internal reporting dashboard", "admin-only user search panel"), **skip web research**. It introduces hallucinated "best practices" that don't match the actual product, and the cost is real.

### Phase 3 — Draft

1. **Draft top-down** following template order: Document Intent → Background → Feature Definition → Goals/Non-Goals → User Model → Relationship → Flows → Design → Policies → Alternatives → Cross-cutting → Scope → Risks → (optional sections as required by their trigger conditions).
2. **Numbered template headings stay in English** — sections `## 1.` through `## 16.`, the Cross-cutting subsections `### 11.1` through `### 11.6`, and the literal `## Appendix` / `## Revision History` headings. The validator keys on the H2 section numbers/titles and the `11.x` subsection numbers; keeping the numbered skeleton in English keeps it stable for the validator and for downstream agents.
3. **Author-named fill-in headings may use the user's language.** Headings the author invents to populate template slots — for example, the policy names under section 9 (the template shows `### 9.1 [Policy Area]` as a placeholder), the platform names under section 14, the alternative names under section 10 — should match the team's natural vocabulary. The validator only inspects the numbered skeleton, so this does not break anything.
4. **Body content is written in the user's primary language** — the language the user has been conversing in. Tables, bullets, prose narrative all in user-language; numbered headings, section numbers, frontmatter keys stay English.
5. **Apply the responsibility map** as you write. If you catch yourself putting "we will not support iOS yet" under `Feature Definition`, that's a Scope statement; move it.
6. **Cross-cutting concerns must be answered, not skipped.** For each of Security, Privacy, Permissions, Observability, Accessibility, Internationalization: write either concrete content or `Not applicable: <short reason>` — with the colon and a real reason. The validator flags both colonless `- Not applicable` and reasonless `- Not applicable:` forms. The `Not applicable` marker itself stays in English even in non-English documents — the validator only recognizes the English form; the reason text may be in the user's language.
7. **Mark unresolved gaps inline** with `[NEEDS INPUT: <what's missing>]` rather than hallucinating. Phase 4 resolves these.
8. **Alternatives need evidence.** Record only alternatives traceable to a source: discussed in this session, visible in git history (reverted or abandoned commits), or supplied by the user. If none exist, write "No alternatives were recorded during development." An invented strawman alternative is worse than an honest blank — future agents treat this section as real decision history.
9. **Fill the frontmatter metadata.** `feature-name`, `profile`, `created` and `last-verified` (today), `verified-against` (`git rev-parse --short HEAD`), `tags`, and `related` (paths of FDDs this feature touches). Future agents use these to judge freshness and to find the doc.

### Phase 4 — Resolve gaps, validate, save

1. **Resolve gap markers.** If a live user is present (interactive Claude Code session), surface every `[NEEDS INPUT: ...]` marker as a single follow-up batch — ask all gap-fills together in one round. If no live user is reachable (subagent, CI, automation), the draft with `[NEEDS INPUT]` markers is itself the deliverable: do not loop trying to ask, just hand off the marked draft so the downstream caller (or a future interactive pass) can fill them.
2. After filling gaps, **run the structural validator**. It ships with this skill at `scripts/validate_fdd.py`, next to this SKILL.md — resolve the path from wherever the skill is installed (for marketplace installs that is NOT the project repo):
   ```bash
   python3 <skill-directory>/scripts/validate_fdd.py docs/FDD/<kebab-case-feature-name>.md
   ```
   The authoritative list of what it checks is the script's docstring (frontmatter and freshness metadata, required sections per profile, empty sections, duplicate/misplaced headings, Cross-cutting answers). It is structural only — content judgement is yours. If `python3` or the script is unavailable in the environment, skip it and check the structure against the template manually; do not block on the tool.
3. **Resolve what the validator reports**: critical findings always; major findings either fix or explicitly accept, each with a one-line reason in your summary to the user. `PASS (N major unresolved)` is not a clean pass.
4. **Run the leakage sweep manually** (see "Implementation leakage" section below) — the validator does not catch this.
5. **Save the final document** to `docs/FDD/<kebab-case-feature-name>.md`. Create `docs/FDD/` if it does not exist. If a file with that name already exists, that is almost always an Update, not a Create — switch to the Update workflow instead of forking copies. Never create `-v2` or date-suffixed duplicates: parallel versions of the same FDD destroy discoverability and leave future agents guessing which one is current.
6. **Update the index.** Maintain `docs/FDD/index.md` (create it if missing) with one line per document: feature name (linked), one-sentence definition, profile, status, `last-verified`. This is how future agents find the right FDD without grepping every file.

## Update workflow

Use when an existing FDD must reflect new decisions or a changed implementation — the most common lifecycle event when a feature evolves across sessions.

Update is **append-oriented**: factual sections are corrected in place; decision history is never erased.

1. Load the existing FDD and identify what changed — new session decisions, the implementation diff, or both. Harvest from the session and code exactly as in Create's post-implementation path.
2. **Factual sections** (`Design`, `Primary User Flows`, `Scope`, `Result Semantics`, `Platform Design`): update in place to match current reality.
3. **Decision sections** (`Policy Decisions`, `Alternatives Considered`): never delete or rewrite an existing entry. Mark a replaced decision `[superseded YYYY-MM-DD — see Revision History]` where it stands, and add the new decision alongside it.
4. **Append a `Revision History` entry**: date, type (updated / superseded / deviation), one-line summary. Record any known doc-vs-code deviations you are not resolving now — an honest deviation note beats a doc that silently lies.
5. **Refresh the frontmatter**: `last-verified` (today) and `verified-against` (current commit). Update the doc's line in `docs/FDD/index.md` if the definition or status changed.
6. Run the validator and the leakage sweep as in Create Phase 4.

## Implementation leakage — what to watch for

These patterns indicate the doc is drifting into being a task list or PR plan. Remove or relocate them:

- **File or module names**: `auth.ts`, `src/components/Login.tsx`, `UserService` (unless the public API itself is part of the design contract)
- **Function/method names**: `validateToken()`, `handleSubmit` (same exception as above)
- **PR or ticket sequencing**: "PR 1: schema. PR 2: API. PR 3: UI."
- **Step-by-step engineering verbs**: "First create the migration. Then modify the resolver. Finally update the client."
- **Code-agent commands**: "Run `npm test`", "Edit `package.json`"
- **Acceptance-criteria-style checklists** that read like a QA test plan rather than design behavior
- **Implementation phasing of the same feature** — if v1 / v2 phasing is design-irrelevant ordering, it belongs in the Implementation Plan; if v1 / v2 are genuinely different product surfaces, use `Scope` and `Future Extensions`

Leakage is not always wrong — sometimes a file boundary *is* a design contract. The test is: would removing this detail still let the reader understand the design? If yes, remove it.

**Exception — the Appendix Code Map.** Code anchors (entry-point paths, key identifiers, module names) are navigation metadata, not design content. They are allowed in exactly one place: the `Appendix`, under a `Code Map` heading, marked non-normative and paired with the commit they were verified against (`verified-against`). A dated, possibly-stale anchor is far cheaper for a future agent than no anchor at all — but the moment anchors creep into sections 1–16, the leakage rule applies in full.

## Fact-check workflow

Fact-check has two layers:

- **Internal consistency** — does the doc obey the template, section responsibilities, and leakage rules?
- **External truth** — does the doc match what the codebase actually does and what relevant external standards actually say?

Both layers matter. A doc that is internally consistent but factually wrong is worse than one that is structurally messy but accurate — the former misleads the next code agent with false confidence.

### Step 1 — Load and run the validator

1. Load the document as-is.
2. Run the validator for cheap structural checks (it lives at `scripts/validate_fdd.py` inside this skill's installed directory — not the project repo):
   ```bash
   python3 <skill-directory>/scripts/validate_fdd.py <path>
   python3 <skill-directory>/scripts/validate_fdd.py <path> --format json   # for machine consumption
   ```
   If `python3` or the script is unavailable, fall back to a manual check against the template structure.
3. Take the validator's findings as the **structural baseline**. Do not re-derive them in your own analysis.

### Step 2 — Internal consistency review

Beyond what the validator catches:

1. **Run the responsibility map** against each section's content. Flag statements that live in the wrong section.
2. **Run the leakage sweep** (see "Implementation leakage" below).
3. **Verify `Alternatives Considered` exists and is meaningful** if any design decision is non-obvious. A doc with zero alternatives is suspicious — either the space was trivial, or rejected paths were not recorded.

### Step 3 — External truth review (scoped by section)

Different sections need different verification sources. Do not waste cycles verifying narrative sections.

| Section | Verification source | What to check |
| --- | --- | --- |
| Background / Problem | none | Narrative — not verifiable externally |
| Feature Definition, Goals, Non-Goals | none | Reflects user intent |
| User Model & Core Concepts | codebase (vocabulary) | Are the named concepts already used elsewhere with the same meaning? |
| Relationship to Existing Features | **codebase** | Do the named existing features actually exist? Are the relationships ("extends", "replaces") accurate? |
| Design → Behavior / Data Model | **codebase** | Do referenced schemas, models, types match reality? Any contradiction with current code? |
| Policy Decisions | **codebase** | Are referenced config keys / feature flags real? Does current code already implement a conflicting policy? |
| Alternatives Considered | none | Historical decision record |
| Cross-cutting → Security / Privacy / A11y / i18n | **codebase + web (conditional)** | Do security/privacy claims hold against current code? Does the design satisfy the relevant external standard (when one applies — same conditional-web rule as Create mode)? |
| Scope, Risks, Open Questions | none | Reflects user / team decisions |
| Platform Design | codebase + web (conditional) | Are platform capability claims accurate against documented platform APIs? |
| Result Semantics | codebase | Do enumerated states match current error/status taxonomy if one exists? |

For each finding from this step, **cite the source**:

- Codebase findings → `file/path.ext:LINE` (or a range)
- Web findings → URL and the specific quote that supports the finding
- If the doc contradicts the codebase, quote both: the doc claim and the contradicting code

Findings without a citation are weaker than the structural ones the validator produces — do not present them with the same confidence.

### Step 4 — Report

Group findings by severity, in the user's primary language. Localize severity labels (Korean: 심각/중요/사소; English: critical/major/minor):

- **Critical** — the doc could mislead a code agent into implementing wrong behavior, or contradicts the codebase in a way that would cause regressions
- **Major** — important design decisions, policies, alternatives, or required sections are missing; or external-standard requirements are unmet
- **Minor** — wording, structure, or template-consistency issues

Format:

```
[severity] [section name]
  finding: <one-sentence statement>
  evidence: <file:line | URL | "validator output">
  suggestion: <how to fix>
```

Lead with critical findings. Do not bury them under structural minutiae.

## Normalize workflow

When the user's doc mixes design and implementation, or sections are mislabeled:

1. Identify the misplaced content using the responsibility map.
2. Move design-level content to the right section. Move implementation-level content out of the FDD entirely — note it as "Belongs in Implementation Plan" rather than deleting silently, because the user may want to preserve it elsewhere.
3. Deliver the normalized doc plus a short prose summary of what moved (e.g., "Moved 4 bullets from `Feature Definition` → `Scope`; removed 2 file-path references from `Design` → flagged for Implementation Plan").
4. Normalize edits a decision record — never overwrite the original silently. Confirm before saving in place; if no confirmation channel exists, save alongside as `<name>-normalized.md` and say so in the summary.

## Output guidance

- **Conversation language**: respond in the user's primary language (Korean by default per repository working agreements).
- **Document language**: section headings stay in English (matching `references/feature_design_doc_template.md`); body content (prose, bullets, table cells, examples) is written in the user's primary language. This keeps the validator and downstream code agents working off a stable structural skeleton while the substantive content stays natural for the team that owns it.
- **Output path**: Create-mode output goes to `docs/FDD/<kebab-case-feature-name>.md`. Create the directory if missing. An existing file at the target path means Update mode, not a silent overwrite — see "Decide the mode first".
- **Format**: produce complete Markdown for the document body — never diff-style or partial output unless the user asks for a diff. The "what moved" summaries in Normalize and Update are short prose, not diffs.
- **Preserve exact text** when fact-checking: code blocks, file paths, identifiers, logs, and quoted source text stay byte-identical to what the user provided.
- **Do not invent product decisions**. Use `[NEEDS INPUT: ...]` markers in the draft for anything that cannot be inferred, then resolve them in a single follow-up batch. A hallucinated policy in an FDD propagates into implementation, which is far more expensive to undo than asking.

## Helper script

`scripts/validate_fdd.py` — structural validator. Stdlib-only Python (3.9+). Runs in milliseconds. It lives inside this skill package; invoke it via the skill's installed path, not a project-relative one.

```bash
python3 <skill-directory>/scripts/validate_fdd.py docs/FDD/<file>.md
python3 <skill-directory>/scripts/validate_fdd.py docs/FDD/<file>.md --format json
python3 <skill-directory>/scripts/validate_fdd.py docs/FDD/<file>.md --strict   # majors also fail the exit code
```

Exit codes: 0 (clean at the chosen threshold), 1 (critical findings — or major findings with `--strict`), 2 (invocation error). The script's docstring is the authoritative list of checks: frontmatter (`doc-type`, `created`, `last-verified`, `profile`), required sections per profile, empty required sections, duplicate/misplaced numbered headings, section order, heading title drift, Cross-cutting answers (subsections or the compact condensed form), code-fence-aware parsing. Semantic checks (responsibility map, leakage, factual accuracy) remain LLM-side because they need judgement.
