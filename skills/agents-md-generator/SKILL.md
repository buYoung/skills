---
name: agents-md-generator
description: Analyze repository structure and generate or update standardized AGENTS.md files that serve as contributor guides for AI agents. Supports both single-repo and monorepo structures. Measures LOC to determine character limits and produces structured documents covering overview, folder structure, patterns, conventions, and working agreements. Update mode refreshes only the standard sections while preserving user-defined custom sections. Use when setting up a new repository, onboarding AI agents to an existing codebase, updating an existing AGENTS.md, or when the user mentions AGENTS.md.
license: MIT
---

# AGENTS.md Generation Capability

This skill enables the agent to generate `AGENTS.md` files that serve as contributor guides for AI agents working on a codebase.

## Core Capability

- **Function**: Analyze repository structure and generate or update a standardized `AGENTS.md` document
- **Output Format**: Markdown file with structured sections
- **Character Limit**: Dynamic, based on repository LOC (Lines of Code)
- **Monorepo Support**: Automatically detects monorepo structures and generates hierarchical documentation (Root + Packages)
- **Update Support**: Refreshes only standard sections in an existing `AGENTS.md`, preserving user-defined custom sections

## Output Sections

### Single Repo / Package Document (5 Sections)
For single repositories or individual packages in a monorepo:

- **Overview**: 1-2 sentence project description (abstract, no tool/framework lists)
- **Folder Structure**: Key directories and their contents
- **Core Behaviors & Patterns**: Cross-cutting patterns traced through full flows — error propagation chains, state lifecycle transitions, cross-boundary wiring mechanisms, resilience/recovery strategies, shared resource management. Discovered via multi-phase analysis: surface idiom detection, then deep tracing across layers.
- **Conventions**: Naming, code style, API/interface design conventions (callback naming, return value shapes, method responsibility splitting), configuration/registration structure, boundary conventions (error flattening, schema drift absorption, containment rules), component composition patterns.
- **Working Agreements**: Rules for agent behavior and communication

### Monorepo Root Document (3 Sections)
For the root of a monorepo structure:

- **Overview**: 1-2 sentences describing the monorepo's purpose
- **Folder Structure**: High-level map of apps, packages, and shared configs
- **Working Agreements**: Common working agreements applicable to all packages

## Operation Modes

### Generate vs Update

- **Generate**: Creates a new `AGENTS.md` from scratch (default when no `AGENTS.md` exists)
- **Update**: Refreshes standard sections in an existing `AGENTS.md` while preserving custom sections. See [./references/update_strategy.md](./references/update_strategy.md) for detailed workflow and section matching rules.

The agent automatically selects the appropriate mode based on whether an `AGENTS.md` file already exists at the target location.

### Generation Modes (Monorepo)

Supports three modes: **All** (root + all packages, default), **Root Only**, and **Single Package**. See [./references/monorepo_strategy.md](./references/monorepo_strategy.md) for detailed strategy and mode selection criteria.

## Execution Workflow

Run these steps in order. Each step has a fixed output that the next step depends on; skipping ahead produces wrong character budgets, unmatched update sections, or missed monorepo packages. The bundled scripts under `./scripts/` make the deterministic steps reproducible — invoke them rather than re-deriving the logic each run.

### Step 1 — Decide Mode

1. Check whether `AGENTS.md` exists at the target location. Present → **Update**. Absent → **Generate**.
2. Run monorepo detection at the repo root:

   ```bash
   python ./scripts/detect_monorepo.py <repo_root>
   ```

   Output: `{is_monorepo, markers}`. If `is_monorepo` is true, choose **All / Root Only / Single Package** per [./references/monorepo_strategy.md](./references/monorepo_strategy.md). Otherwise treat the repo as a single document.

### Step 2 — Measure LOC and Allocate Budget

For each target document (single repo, or root + each package), run:

```bash
python ./scripts/loc_to_limit.py <target_directory>
```

Output: `{loc, scale, character_limit}`. If the script reports `tokei` is missing, surface its install message and stop — do not estimate LOC by hand. Allocate `character_limit` across sections using the proportions in [./references/loc_measurement.md](./references/loc_measurement.md) (Section Budget Allocation).

### Step 3 — Build Stack Context

Before pattern/convention analysis, read the package manifests at the document's scope (root or per package) per [./references/read_only_commands.md](./references/read_only_commands.md) > Dependency Discovery. Skip lock files. Use this stack context to focus Step 4 on relevant frameworks rather than searching blindly.

### Step 4 — Analyze the Repository

Run the multi-phase analysis defined in [./references/agents_md_template.md](./references/agents_md_template.md):

1. **Phase 1** — Stack & Surface Discovery (recurring idioms in 3+ files, project-specific abstractions).
2. **Phase 2** — Deep Tracing across layers (error propagation, wiring, state lifecycle, failure paths, centralized delegation).
3. **Phase 3** — Validation (each pattern present in 3+ locations, accounting for cross-layer flows).

If Serena MCP is available, prefer its read-only symbol tools (`find_symbol`, `find_referencing_symbols`, `get_symbols_overview`, etc.) over `rg` / `grep` / `find` — symbolic queries are more accurate for caller tracing and cross-layer flows. See [./references/read_only_commands.md#symbol-level-analysis-optional-requires-serena-mcp](./references/read_only_commands.md#symbol-level-analysis-optional-requires-serena-mcp).

Run this analysis in the current context only. **Do not delegate to subagents** — Phase 3 cross-pattern validation and section-level budget tracking require a unified view (see [Scope Boundaries](#scope-boundaries) > Single-Context Execution).

Stay within each section's character budget from Step 2. Document only patterns/conventions actually observed.

### Step 5 — Assemble (Generate) or Splice (Update)

- **Generate**: Emit the document using the structure in [./references/agents_md_template.md](./references/agents_md_template.md) (5 sections for single repo / package, 3 for monorepo root). Use [./references/working_agreements.md](./references/working_agreements.md) for the Working Agreements section.
- **Update**: Run the section parser on the existing file:

  ```bash
  python ./scripts/parse_sections.py <path/to/AGENTS.md> --doc-type single_repo
  ```

  (Use `--doc-type monorepo_root` for the monorepo root document.) The output marks each `## ` heading as `is_standard` (managed) or not (preserved). Replace **only** the standard sections' bodies; keep custom sections, the file title, and any preamble before the first `##` unchanged. Insert any `missing_standard` heading at its numbered position relative to other standard sections. Full reassembly rules: [./references/update_strategy.md](./references/update_strategy.md).

  If the existing document type no longer matches the repo (e.g., a single repo became a monorepo), force full regeneration instead of update.

### Step 6 — Verify and Write

Before writing, confirm:

- Total length is within `character_limit`; no section exceeds its budget.
- None of the [Anti-Patterns](./references/agents_md_template.md#anti-patterns-excluded-content) appear (no Common Commands, run/test/build/deploy instructions, IDE/tooling settings, etc.).
- For Update mode: every preserved custom section is byte-for-byte identical to the original.

Then write with the Edit/Write tool. For Monorepo with mode = **All**, repeat Steps 2–6 per target package after handling the root.

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

### Bundled Scripts

Deterministic steps are bundled as scripts under `./scripts/` so they run identically across invocations and platforms. Prefer these over re-deriving the logic in natural language.

- **`scripts/loc_to_limit.py`**: Runs `tokei` with the prescribed exclusions, parses the `Total` row, and returns `{loc, scale, character_limit}`. Surfaces the install message and exits non-zero if `tokei` is missing.
- **`scripts/detect_monorepo.py`**: Checks marker files (`pnpm-workspace.yaml`, `lerna.json`, `nx.json`, `turbo.json`, `rush.json`, `.moon/workspace.yml`, `go.work`, `Cargo.toml [workspace]`, `package.json` workspaces, Gradle `settings.gradle*`, Maven `pom.xml <modules>`, Bazel, Buck2, Pants, Hatch/uv/rye). Returns `{is_monorepo, markers}`.
- **`scripts/parse_sections.py`**: For Update mode. Parses an existing `AGENTS.md` and returns a section map flagging which `##` headings are standard (managed) vs custom (preserved), plus any missing standard headings.

## Domain Knowledge

- **LOC Measurement**: Capability to measure repository size and determine character limits. See [./references/loc_measurement.md](./references/loc_measurement.md)
- **Repository Analysis**: Capability to inspect and understand codebase structure. See [./references/read_only_commands.md](./references/read_only_commands.md)
- **Output Template**: Standardized AGENTS.md structure specification. See [./references/agents_md_template.md](./references/agents_md_template.md)
- **Working Agreements**: Agent behavior rules for generated documents. See [./references/working_agreements.md](./references/working_agreements.md)
- **Monorepo Detection**: Capability to identify monorepo structures. See [./references/monorepo_detection.md](./references/monorepo_detection.md)
- **Monorepo Strategy**: Strategy for generating documentation in monorepos. See [./references/monorepo_strategy.md](./references/monorepo_strategy.md)
- **Update Strategy**: Strategy for updating existing AGENTS.md files with selective section refresh. See [./references/update_strategy.md](./references/update_strategy.md)

## Scope Boundaries

- **Read-Only Analysis**: Supports non-destructive commands for repository inspection
- **Output Scope**: Produces documentation content only; excludes run/test/build/deploy instructions
- **Excluded Inputs**: Lock files (`pnpm-lock.yaml`, `package-lock.json`, `yarn.lock`, etc.) are outside analysis scope
- **Single-Context Execution (No Subagents)**: This skill **must NOT spawn subagents** (e.g., the `Agent` / `Task` tool, `Explore`, `general-purpose`, or any delegated agent) at any step. AGENTS.md generation requires a unified view of the repository: accumulated stack context (Step 3), per-section character budgets (Step 2), Phase 3 validation across 3+ locations, and Update-mode byte-for-byte preservation of custom sections all depend on a single context. Splitting work across subagents loses this state and produces inconsistent or budget-violating output. A parent agent invoking this skill is fine — the skill's *internal* execution must stay in one context.
