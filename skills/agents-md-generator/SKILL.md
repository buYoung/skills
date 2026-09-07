---
name: agents-md-generator
description: Analyze repository structure and generate or update standardized AGENTS.md files that serve as contributor guides for AI agents. Supports both single-repo and monorepo structures. Measures LOC to determine character limits and produces structured documents covering overview, optional ownership maps, patterns, conventions, and working agreements. Update mode refreshes only standard sections while preserving user-defined custom sections. Existing unmarked files require a concrete change preview and one-time user confirmation before adoption; heading matches alone never authorize rewriting. Use when the user wants an AGENTS.md generated or refreshed — setting one up for a new repository, onboarding AI agents to an existing codebase, updating an existing AGENTS.md after meaningful project changes, or when the user mentions AGENTS.md. Not for CLAUDE.md, README, or other documentation files.
license: MIT
---

# AGENTS.md Generation Capability

This skill enables the agent to generate `AGENTS.md` files that serve as contributor guides for AI agents working on a codebase.

## Core Capability

- **Function**: Analyze repository boundaries and generate or update a standardized `AGENTS.md` document
- **Output Format**: Markdown file with structured sections
- **Character Limit**: Dynamic, based on repository LOC (Lines of Code)
- **Monorepo Support**: Automatically detects monorepo structures and generates hierarchical documentation (Root + Packages)
- **Update Support**: Refreshes only standard sections in a marked, managed `AGENTS.md`, preserving user-defined custom sections. Unmarked files require a concrete change preview and one-time adoption confirmation; files without matching standard headings require an explicit full-regeneration request

## Output Sections

### Single Repo / Package Document (4-5 Sections)
For single repositories or individual packages in a monorepo:

- **Overview**: 1-2 sentence project description (abstract, no tool/framework lists)
- **Ownership Map**: Optional, evidence-backed map split into stable ownership boundaries and active change routes — entry points, state owners, behavior decision points, external surfaces, contracts/side effects, verification anchors, and recent history-informed routes. Omit this section when the repository does not expose stable boundaries or active routes worth documenting; never invent ownership just to fill the template.
- **Core Behaviors & Patterns**: Cross-cutting patterns traced through full flows — error propagation chains, state lifecycle transitions, cross-boundary wiring mechanisms, resilience/recovery strategies, shared resource management. Discovered via multi-phase analysis: surface idiom detection, then deep tracing across layers.
- **Conventions**: Naming, code style, API/interface design conventions (callback naming, return value shapes, method responsibility splitting), configuration/registration structure, boundary conventions (error flattening, schema drift absorption, containment rules), component composition patterns.
- **Working Agreements**: Rules for agent behavior and communication

### Monorepo Root Document (2-3 Sections)
For the root of a monorepo structure:

- **Overview**: 1-2 sentences describing the monorepo's purpose
- **Ownership Map**: Optional map split into stable package-level responsibility boundaries and active cross-package change routes. At monorepo roots, package names plus manifests, public exports, README text, dependency direction, and recent confirmed change clusters can establish enough evidence; omit the section when the root exposes only an uninformative package list.
- **Working Agreements**: Common working agreements applicable to all packages

## Operation Modes

### Generate vs Update

- **Generate**: Creates a new `AGENTS.md` from scratch (default when no `AGENTS.md` exists)
- **Update**: Refreshes standard sections in an existing managed `AGENTS.md` while preserving custom sections. A valid management marker establishes enrollment in this workflow; matching headings identify replacement candidates, not authorship. Unmarked files need one-time adoption confirmation after a concrete preview; zero matching headings require an explicit full-regeneration request. See [./references/update_strategy.md](./references/update_strategy.md) for the marker contract and adoption workflow.

The agent automatically selects the appropriate mode based on whether an `AGENTS.md` file already exists at the target location.

### Generation Modes (Monorepo)

Supports three modes: **All** (root + all packages, default), **Root Only**, and **Single Package**. See [./references/monorepo_strategy.md](./references/monorepo_strategy.md) for detailed strategy and mode selection criteria.

## Execution Workflow

Run these steps in order. Each step has a fixed output that the next step depends on; skipping ahead produces wrong character budgets, unmatched update sections, or missed monorepo packages. The bundled scripts under `./scripts/` make the deterministic steps reproducible — invoke them rather than re-deriving the logic each run.

### Step 1 — Decide Mode

1. Check whether `AGENTS.md` exists at the target location. Present → **Update candidate** (subject to the management check below). Absent → **Generate**.
2. Run monorepo detection at the repo root:

   ```bash
   python ./scripts/detect_monorepo.py <repo_root>
   ```

   Output: `{is_monorepo, markers}`. A `true` result is provisional: discover the actual packages per [./references/monorepo_detection.md](./references/monorepo_detection.md). If fewer than 2 packages are found, treat the repo as a single document despite the marker. Otherwise choose **All / Root Only / Single Package** per [./references/monorepo_strategy.md](./references/monorepo_strategy.md). If `is_monorepo` is false, treat the repo as a single document.

3. Before LOC measurement or deep analysis, run `python ./scripts/parse_sections.py <path/to/AGENTS.md> --doc-type <single_repo|monorepo_root>` for each existing target. `management_status` is `managed`, `unmarked`, or `invalid`; `generated_doc_type` records the valid marker's original document type or is null. Invalid markers stop automatic updating. Resolve the original type in the next item before applying the heading-count gate: unmarked files with matching standard headings may proceed to preparation of an adoption preview, but not writing; zero matched headings under the original type require an explicit full-regeneration request. A matching heading alone never authorizes a write.
4. Compare a valid `generated_doc_type` with the current target type. When they differ, rerun the parser with the original type to identify the original managed and custom sections before preparing full regeneration. For an unmarked file, infer its original type from distinctive standard headings (`## 3. Working Agreements` versus `## 3. Core Behaviors & Patterns` / `## 5. Working Agreements`); ask which original type to use if these conflict or are insufficient. Preserve original custom sections and obtain confirmation of the concrete type-transition preview before overwriting.
5. For package documents, check whether the repository-root `AGENTS.md` exists. If it does, reference its actual relative path. If it does not, include the common working agreements directly in the package document plus any discovered package-local verification command. Do not create a root file for a Single Package request. In All mode, recheck after the root has been handled.

### Step 2 — Measure LOC and Allocate Budget

For each target document (single repo, or root + each package), run:

```bash
python ./scripts/loc_to_limit.py <target_directory>
```

Output: `{loc, scale, character_limit}`. If the script reports `tokei` is missing, surface its install message and stop — do not estimate LOC by hand. Use the proportions in [./references/loc_measurement.md](./references/loc_measurement.md) as initial section allocations, then redistribute capacity according to verified content. Only the combined preamble and managed sections have a hard character limit; the section proportions are not independent ceilings.

### Step 3 — Build Stack Context

Before pattern/convention analysis, read the package manifests at the document's scope (root or per package) per [./references/read_only_commands.md](./references/read_only_commands.md) > Dependency Discovery. Skip lock files. Use this stack context to focus Step 4 on relevant frameworks rather than searching blindly.

### Step 4 — Analyze the Repository

Read [./references/content_quality.md](./references/content_quality.md) before analysis. Keep a compact internal record of decision-relevant facts, their current source evidence, and their intended destination. In Generate mode, discover these facts from source. In Update mode, also extract important facts from the old analysis-derived managed sections as inspection leads, reconfirm them against current source, and discover what the old document missed. The old document is not evidence of current behavior, and the working record is not a new output section.

For selected important behaviors, inspect direct implementing helpers until applicable choices, guard/bypass paths, recovery outcomes, state lifetime, ownership/cleanup conditions, and actual recipients are established. Save that compact relationship record in a temporary scratch file outside the target repository before drafting. A feature or helper name by itself does not close source tracing. Recent history affects active-route classification, not whether a currently verified safety contract is retained.

Before history-driven prioritization, build the coverage table from documented capabilities and authoritative registrations/public surfaces. In Update mode, also account for every old managed Stable boundary, Active route, and core flow. Confirm each row's current owner/consumer and selection or evidence-based exclusion. Trace selected rows from `open` to `closed` using actual implementing files and symbols, including each behavior-changing stage of a pipeline. A history window with no changes cannot exclude a live hook, migration, or safety condition.

For **Update mode**, use git history as an ownership-discovery signal before deep source tracing:

1. Prefer changes since the last skill-generated `AGENTS.md` update for the target document. If no reliable update anchor exists, default to roughly the last 3 months and adjust by repository activity.
2. Run the bundled high-churn signal helper before manually expanding git history:

   ```bash
   python ./scripts/git_ownership_signals.py <target_directory>
   ```

   If a reliable update anchor exists, pass it with `--anchor <commit-ish>`. The script emits compact Markdown-KV to minimize context use.
3. Start with commit metadata and changed paths only. Do not read broad diffs by default.
4. Look for changed-path clusters, repeated co-change patterns, renames/moves, deleted paths, and high-churn boundary files.
5. Use history to decide where to inspect next, not what to document. Add an `Ownership Map` boundary only when current code or documented contracts confirm it.
6. Do not persist timeline summaries such as "earlier focus" or "current focus" in `AGENTS.md`. Report them only in the user-facing summary unless the transition is currently represented in code as a live migration or compatibility boundary.

See [./references/read_only_commands.md#git-history-signals-update-mode](./references/read_only_commands.md#git-history-signals-update-mode) for token-safe git commands and expansion rules.

Run the multi-phase analysis defined in [./references/agents_md_template.md](./references/agents_md_template.md):

1. **Phase 1** — Stack & Surface Discovery (recurring idioms in 3+ files, project-specific abstractions).
2. **Phase 2** — Deep Tracing across layers (error propagation, wiring, state lifecycle, failure paths, centralized delegation).
3. **Phase 3** — Validation (prefer patterns present in 3+ locations, accounting for cross-layer flows; also retain a single verified critical boundary that governs safe work).

If Serena MCP is available, prefer its read-only symbol tools (`find_symbol`, `find_referencing_symbols`, `get_symbols_overview`, etc.) over `rg` / `grep` / `find` — symbolic queries are more accurate for caller tracing and cross-layer flows. See [./references/read_only_commands.md#symbol-level-analysis-optional-requires-serena-mcp](./references/read_only_commands.md#symbol-level-analysis-optional-requires-serena-mcp).

Run this analysis in the current context only. **Do not delegate to subagents** — Phase 3 cross-pattern validation and section-level budget tracking require a unified view (see [Scope Boundaries](#scope-boundaries) > Single-Context Execution).

Document only patterns/conventions actually observed. Preserve necessary entry points, behavior-changing alternatives, exception/fallback conditions, lifecycle obligations, and compatibility effects. If a section needs more than its initial allocation, redistribute unused capacity within the total limit rather than deleting these facts. Apply the compression order in the content-quality reference.

If optional `## 2. Ownership Map` has no evidence-backed content, omit the section and keep later section numbers unchanged. Section numbers are update-mode identifiers; never renumber `Core Behaviors & Patterns`, `Conventions`, or `Working Agreements` to close the gap. When evidence exists, split Ownership Map content into `Stable Ownership Boundaries` for the durable safety boundaries the previous single-list Ownership Map would have documented, and `Active Change Routes` for recent history-informed routes confirmed against current code. Treat `Active Change Routes` as additive update-mode context, not as a replacement or filter for stable boundaries. Stable bullets are full change-routing rules; Active bullets are parent-linked or cross-boundary delta routes. Do not restate the parent Stable boundary's broad owner, contract, or verification in Active. If no meaningful delta remains after removing inherited Stable details, omit the Active route. Do not impose a bullet-count limit beyond the section character budget.

### Step 5 — Assemble (Generate) or Splice (Update)

Draft the closed, decision-relevant contracts into Ownership Map/Core Behaviors first, without duplicating them across sections. Use remaining capacity for repository-specific conventions; do not fill generic naming, role, logging, or resource lists at the expense of a covered contract. Keep every coverage row accounted for when removing an Active label or consolidating sections.

- **Generate**: Emit the document using the structure in [./references/agents_md_template.md](./references/agents_md_template.md) (4-5 sections for single repo / package, 2-3 for monorepo root, depending on whether `Ownership Map` has evidence-backed content). Add exactly one standalone `<!-- agents-md-generator: v1; doc-type: single_repo -->` line to the preamble, before the first `##` heading; use `monorepo_root` for a monorepo root. Use [./references/working_agreements.md](./references/working_agreements.md) for the Working Agreements section and its root-absence fallback.
- **Update**: Run the section parser on the existing file:

  ```bash
  python ./scripts/parse_sections.py <path/to/AGENTS.md> --doc-type single_repo
  ```

  (Use `--doc-type monorepo_root` for a monorepo root, or the original type from Step 1 when preparing a transition.) The output marks each `## ` heading as `is_standard` (a replacement candidate subject to the management gate) or not (preserved), flags evidence-gated headings in `optional_standard`, and marks matched optional sections with `is_optional_standard`. Legacy `## 2. Folder Structure` sections report `canonical_title: "## 2. Ownership Map"` so approved updates can migrate them. Replace **only** the standard sections' bodies; keep custom sections, the file title, and the preamble unchanged except for approved marker insertion or type-transition replacement. Insert missing required headings at their numbered position, and missing optional headings only when fresh analysis produced evidence-backed content. Full reassembly rules: [./references/update_strategy.md](./references/update_strategy.md).

  **Management gate**: use the Step 1 management result, not `is_standard` alone. For an unmarked file, finish a concrete preview of replacements, insertions, deletions, and marker insertion, then obtain one-time adoption confirmation. On approval, write the adoption and marker together; on refusal, leave the original file unchanged. A general update request is not adoption confirmation. Preserve all non-standard content and the existing preamble except the expressly approved marker insertion. Invalid markers must be reported rather than silently repaired. See the update strategy for details.

  If the existing document type no longer matches the repo (e.g., a single repo became a monorepo), force full regeneration instead of update: carry every custom section over verbatim into the regenerated document (original order preserved) and get the user's confirmation before overwriting.

### Step 6 — Verify and Write

Before writing, confirm:

- The combined length of the preamble and the standard (managed) sections is within `character_limit`. Section allocations may be exceeded after rebalancing; preserve section responsibilities and do not add filler. Custom sections are excluded from the budget and must never be trimmed to satisfy it.
- The document has exactly one valid management marker in its preamble and its document type matches the output. The marker counts toward the preamble budget. Preserve the preamble apart from approved marker insertion or type-transition replacement. An unmarked file is written only after approval of its concrete adoption preview.
- None of the [Anti-Patterns](./references/agents_md_template.md#anti-patterns-excluded-content) appear (no Common Commands, run/test/build/deploy instructions, IDE/tooling settings, etc.). Exception: the discovered type-check command in Working Agreements is required content, not a build/run instruction.
- For Update mode: every standard section body was rebuilt from its managed source, not reused because the old wording appeared acceptable.
- For both modes: after final compression, compare the assembled document with the working fact record per [./references/content_quality.md](./references/content_quality.md). Every important verified fact must be conveyed, corrected to current behavior, or excluded with an evidence-based reason. Unexplained loss or distortion fails verification even if structure and length pass. Reconfirmed identifiers and meaning may recur in freshly written sections; freshness does not require erasing useful facts. If important facts cannot fit after reallocation and compression, finish a reviewable candidate and ask about scope or total limit before writing.
- Read the temporary record and final output together: point each important fact to its actual final sentence and check its applicable relationship fields. Reverse-check broad claims about recovery, migration, restoration, reuse, guards, and resource ownership against their implementing helpers. If both record and prose omit a condition, reopen the helper; their agreement is not a pass. Keep this audit outside `AGENTS.md` and report only material corrections or limitations to the user.
- Check coverage as well as depth: all old managed boundaries/routes/flows and documented or registered capability candidates have a current disposition, and no selected row remains `open`. Empty history, generic "lower value", or space pressure is not an exclusion reason for a current safety contract. Generic pipeline stage names do not establish the stages' actual choices or recovery conditions.
- For Update mode: scan only managed standard sections for stale standing work-agreement wording. Fail verification if managed content still contains `Keep edits minimal`, `Minimal changes`, `preserve public APIs`, `existing plugin behavior`, or `avoid unnecessary abstraction`; custom sections may keep any user-owned wording.
- For Update mode: every preserved custom section is byte-for-byte identical to the original.
- For Update mode: report to the user any wording being removed from managed standard sections — user additions inside managed sections are not preserved, so list what is dropped before overwriting and suggest moving anything user-owned into a custom section.
- For Update mode: if an existing managed `Ownership Map` or legacy `Folder Structure` section will be omitted because no current evidence supports it, report that whole-section removal and get confirmation before overwriting.
- For single-repo documents: the managed `Working Agreements` section does not contain monorepo-only wording such as package-level `AGENTS.md` guidance.
- For package documents: a root reference resolves to an existing file; otherwise the package contains common working agreements directly and no missing-root reference. If a root document now exists where a previous update used the fallback, switch to inheritance through the usual managed-section replacement and dropped-wording report.

Then write with the Edit/Write tool. For Monorepo with mode = **All**, repeat Steps 2–6 per target package after handling the root, re-running the Step 1 Generate/Update decision, management check, and root-existence check for each package — a package without `AGENTS.md` is Generate even when the root was Update.

## Tools

This skill uses the following read-only tools for repository analysis. See [./references/read_only_commands.md](./references/read_only_commands.md) for detailed usage patterns.

- **Serena MCP symbol tools** (preferred when available): `find_symbol`, `find_referencing_symbols`, `find_referencing_code_snippets`, `get_symbols_overview`, `search_for_pattern`, `list_dir`, `find_file`, `read_file`. Prefer these over `rg` / `grep` / `find` for symbol lookups, caller tracing, and structural analysis. Use only the read-only tools listed; do NOT invoke write/edit symbol tools or `execute_shell_command`. See [./references/read_only_commands.md#symbol-level-analysis-optional-requires-serena-mcp](./references/read_only_commands.md#symbol-level-analysis-optional-requires-serena-mcp).
- **`tokei`**: LOC measurement (required)
- **`rg` (ripgrep)**: Content search (fallback when Serena MCP is unavailable)
- **`grep` / `Select-String`**: Content search (fallback per OS, when neither Serena nor `rg` is available)
- **`sed -n` / `Get-Content \| Select-Object`**: Paginated file reading per OS
- **`tree`**: Directory structure visualization
- **`find`**: File and directory discovery (Linux / macOS, fallback when Serena `find_file` is unavailable)
- **`ls`, `pwd`**: Basic directory navigation
- **`git log`, `git show --stat`, `git show --name-only`**: Update-mode ownership discovery signals; use the bundled script first, then metadata and changed paths, never broad diffs by default

### Bundled Scripts

Deterministic steps are bundled as scripts under `./scripts/` so they run identically across invocations and platforms. Prefer these over re-deriving the logic in natural language.

- **`scripts/loc_to_limit.py`**: Runs `tokei` with the prescribed exclusions, parses the `Total` row, and returns `{loc, scale, character_limit}`. Surfaces the install message and exits non-zero if `tokei` is missing.
- **`scripts/detect_monorepo.py`**: Checks marker files (`pnpm-workspace.yaml`, `lerna.json`, `nx.json`, `turbo.json`, `rush.json`, `.moon/workspace.yml`, `go.work`, `Cargo.toml [workspace] members`, `package.json` workspaces, Gradle `settings.gradle*`, Maven `pom.xml <modules>`, Bazel, Buck2, Pants, Hatch/uv/rye). Gradle matching reads complete literal include declarations, including multiline forms, ignores comments/string examples, and deduplicates project paths; it does not evaluate dynamic Gradle expressions. Returns `{is_monorepo, markers}`; a `true` result is provisional until package discovery finds 2+ packages (Step 1).
- **`scripts/parse_sections.py`**: For Update mode. Returns a section map with standard-heading candidates, custom sections, and missing headings, plus `management_status` and `generated_doc_type`. Existing JSON fields and `--doc-type` matching remain unchanged; consumers must use the management gate before writing. Headings and markers inside fenced code blocks are ignored. The parser reports line ranges rather than rewriting content; splice preserved ranges from the original bytes, retaining line endings and trailing whitespace.
- **`scripts/git_ownership_signals.py`**: For Update mode. Runs token-safe git history aggregation over the target directory and prints compact Markdown-KV high-churn path signals. The output is a discovery signal only and must be confirmed against current code before documenting `Ownership Map` boundaries.

## Domain Knowledge

- **LOC Measurement**: Capability to measure repository size and determine character limits. See [./references/loc_measurement.md](./references/loc_measurement.md)
- **Repository Analysis**: Capability to inspect and understand codebase structure. See [./references/read_only_commands.md](./references/read_only_commands.md)
- **Output Template**: Standardized AGENTS.md structure specification. See [./references/agents_md_template.md](./references/agents_md_template.md)
- **Content Quality**: Decision-relevant fact discovery, evidence-based retention/correction, compression order, and final semantic comparison. See [./references/content_quality.md](./references/content_quality.md)
- **Working Agreements**: Agent behavior rules for generated documents. See [./references/working_agreements.md](./references/working_agreements.md)
- **Monorepo Detection**: Capability to identify monorepo structures. See [./references/monorepo_detection.md](./references/monorepo_detection.md)
- **Monorepo Strategy**: Strategy for generating documentation in monorepos. See [./references/monorepo_strategy.md](./references/monorepo_strategy.md)
- **Update Strategy**: Strategy for updating existing AGENTS.md files with selective section refresh. See [./references/update_strategy.md](./references/update_strategy.md)

## Scope Boundaries

- **Read-Only Analysis**: Supports non-destructive commands for repository inspection
- **Output Scope**: Produces documentation content only; excludes run/test/build/deploy instructions. Optional sections are omitted when repository analysis finds no concrete, stable content for them.
- **Excluded Inputs**: Lock files (`pnpm-lock.yaml`, `package-lock.json`, `yarn.lock`, etc.) are outside analysis scope
- **Single-Context Execution (No Subagents)**: This skill **must NOT spawn subagents** (e.g., the `Agent` / `Task` tool, `Explore`, `general-purpose`, or any delegated agent) at any step. AGENTS.md generation requires a unified view of the repository: accumulated stack context (Step 3), per-section character budgets (Step 2), Phase 3 validation across 3+ locations, and Update-mode byte-for-byte preservation of custom sections all depend on a single context. Splitting work across subagents loses this state and produces inconsistent or budget-violating output. A parent agent invoking this skill is fine — the skill's *internal* execution must stay in one context.
