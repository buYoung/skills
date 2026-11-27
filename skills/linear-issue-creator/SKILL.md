---
name: linear-issue-creator
description: >
  Create structured Linear issues (main + sub-issues) with project linking, title prefix, and labeling.
  Supports two workflows: Generic (code tasks) and PRD Pipeline (제품 요구사항 정의서).
  PRD Pipeline applies content-strategy, content-production, content-humanizer, copy-editing principles
  to produce high-quality issue descriptions targeting fullstack developers in Korean.
  Use when asked to create, register, or break down tasks into Linear issues. Not for querying or updating.
---

# Linear Issue Creator

Create issues in Linear using the Linear MCP with a **1 main issue + N sub-issues** structure.

Tool names in this skill (`save_issue`) are the Linear MCP server's names. Clients add their own prefix (Claude Code shows `mcp__<server>__save_issue`), so check the connected server's tool list for the exact name (`/mcp` in Claude Code shows each tool's full name) and the input schema in its tool definition for parameters before the first call.

---

## Core Principles

| Aspect | Main Issue | Sub-Issue |
|---|---|---|
| Perspective | Business / user perspective | Developer / engineer perspective |
| Unit | One feature or problem | One PR-completable task |
| Key question | "What changes for the user?" | "What code do we change?" |
| Labels | None | Exactly 2 (1 area + 1 type) |
| Status mgmt | Finished after the reviewer's final review | Transitions individually |

Linear marks the main issue Done when all sub-issues are done only if the team has Parent auto-close enabled (Settings > Team > Workflow). It then happens as soon as the last sub-issue is done, before `linear-issue-reviewer` runs its final review. Either way, the main issue counts as finished only after the reviewer's final review comment (`## 📋 최종 리뷰 완료`); without auto-close, the user closes it after that comment.

---

## Workflow Selection

Before gathering requirements, determine the workflow type:

| Workflow | When to use | Description |
|---|---|---|
| **Generic** | Code tasks: feature, bug, refactor, etc. | Use existing flow as-is |
| **PRD Pipeline** | Issues requiring a PRD (product requirements doc) or feature spec | Apply content skill principles for high-quality descriptions |

- Generic → proceed to **Issue Creation Workflow** section below
- PRD Pipeline → proceed to **PRD Pipeline Workflow** section below

If the user doesn't specify, infer from the work description. Ask if unclear.

---

## Mandatory Rules (Never Skip)

### 1. Project Linking
Every issue (main + sub) must be linked to a project via the `project` parameter.

### 2. Title Prefix
Every issue title must start with `[ProjectName]`.

**Examples:**
- `[corral] Implement global hotkey system`
- `[corral] Configure Tauri global hotkey plugin`

### 3. Labeling (Sub-Issues Only)
Each sub-issue must have **exactly 2 labels**. The main issue has **no labels**.

**Area label** (pick exactly 1):
- `Back-end`
- `Front-end`

**Type label** (pick exactly 1):
- `Bug` — Bug fix
- `Chore` — Build, config, dependency maintenance
- `Docs` — Documentation
- `Perf` — Performance improvement
- `Refactor` — Code refactoring (no behavior change)
- `Feature` — New feature or feature update

### 4. Team
Always use `"private"` as the team when creating issues.

---

## Issue Creation Workflow

### Step 1: Gather Requirements

Confirm the following with the user:

1. **Project**: Which project (coin-agent, home-page, corral, intellij-jsoninja, etc.)
2. **Work description**: What to build, fix, or change
3. **Area**: Back-end / Front-end
4. **Type**: Bug / Chore / Docs / Perf / Refactor / Feature

If the user has already provided sufficient information, proceed directly. Otherwise, ask.

### Step 2: Create the Main Issue

Call `save_issue` to create the main issue.

**Parameters:**
```
title: "[ProjectName] Main title"
team: "private"
project: "project-name"
description: (use template below)
priority: appropriate priority (0=No priority, 1=Urgent, 2=High, 3=Medium, 4=Low)
```

Use the **main issue description template** from `references/templates.md`.

Do NOT assign any labels to the main issue.

### Step 3: Create Sub-Issues

Use the main issue's ID as `parentId` for each sub-issue.

**Parameters:**
```
title: "[ProjectName] Sub-task title"
team: "private"
project: "project-name"
parentId: "main issue ID or identifier"
labels: ["area-label", "type-label"]   ← always exactly 2
description: (use template below)
priority: appropriate priority
```

Use the **sub-issue description template** from `references/templates.md`.

### Step 4: Link Dependencies

If sub-issues depend on each other, connect them with `blockedBy`. Pass it in the dependent sub-issue's create call when the prerequisite already exists (as in the examples in `references/templates.md`), or update the dependent issue afterwards:

```
save_issue (update)
  id: "dependent issue identifier"
  blockedBy: ["prerequisite issue identifier"]
```

### Step 5: Report Results

Summarize all created issues for the user:

- Main issue identifier + title + URL
- Sub-issue list (identifier, title, 2 labels, dependencies)

In draft output mode, report the file path instead (see **Draft Output (No Linear Writes)**).

---

For a full flow example, see `references/templates.md`.

---

## PRD Pipeline Workflow

Workflow for producing PRD-quality (product requirements document) issue descriptions.
Applies principles from four content skills (content-strategy, content-production, content-humanizer, copy-editing) during the description writing process.

**Fixed context:**
- Target audience: Fullstack developers
- Language: Korean
- Tone: Professional (explaining to a peer developer — professional without being overly formal)

### PRD Step 1: Gather Requirements + Select Pattern

Collect the same information as Generic Step 1 (Project, Work description, Area, Type).
Additionally confirm:

1. **PRD topic**: What the PRD is about
2. **Current state**: Topic only, draft exists, or nearly complete
3. **Auto-select pattern**:

| Pattern | Starting state | Content skill stages to apply |
|---|---|---|
| **A. Blank → Complete** | Topic only | content-strategy → content-production → content-humanizer → copy-editing |
| **B. Draft → Complete** | Draft exists | content-humanizer → copy-editing |
| **C. Polish only** | Nearly complete | copy-editing |

### PRD Step 2: Write Descriptions (Per-Pattern Process)

Apply the applicable stages in order to write issue descriptions.
See `references/prd-pipeline.md` for the detailed guide.

**Pattern A (Blank → Complete) — All 4 stages:**

1. **content-strategy principles**: Plan the PRD structure
   - Derive required sections from the target audience's perspective (feature overview, technical requirements, API specs, data models, non-functional requirements, etc.)
   - Determine technical depth and scope for each section
   - Establish sub-issue decomposition strategy

2. **content-production principles**: Draft the descriptions
   - Write technical requirements at an implementation-ready level of specificity
   - Make Acceptance Criteria measurable
   - Define per-sub-issue Done Criteria at code level
   - Use concrete numbers/specs instead of vague terms ("improve," "optimize")

3. **content-humanizer principles**: Remove AI patterns
   - Eliminate repetitive phrasing (e.g., same sentence structure repeated)
   - Remove unnecessary qualifiers ("very important," "essential," "critical")
   - Replace with expressions developers actually use
   - Deliberately vary sentence length

4. **copy-editing principles**: Run PRD-relevant Seven Sweeps checks. The four below are the minimum; section 4 of `references/prd-pipeline.md` has the checklist for all seven.
   - **Clarity**: No ambiguous requirements
   - **Specificity**: Concrete numbers, endpoints, data types specified
   - **So What**: Each requirement explains "why it's needed"
   - **Prove It**: Technical claims have backing (benchmarks, references, etc.)

**Pattern B (Draft → Complete)**: Apply stages 3-4 only
**Pattern C (Polish only)**: Apply stage 4 only

### PRD Step 3: Create Main Issue

Same as Generic Step 2 — call `save_issue`.
Use the **PRD Main Issue Description Template** from `references/templates.md`.

### PRD Step 4: Create Sub-Issues

Same as Generic Step 3 — create sub-issues.
Use the **PRD Sub-Issue Description Template** from `references/templates.md`.

### PRD Step 5: Link Dependencies + Report Results

Same as Generic Steps 4-5.

---

## Draft Output (No Linear Writes)

When the user asks not to create the issues in Linear and to save the descriptions to a file instead (e.g., "Linear에 실제로 생성하지 말고 이슈 설명문만 파일로 저장해줘"), run the selected workflow as usual but skip every `save_issue` call and write one Markdown file.

- **Path**: the path the user gives; otherwise `linear-issue-drafts/[project]_[YYYY-MM-DD].md` under the current directory.
- **Identifiers**: use `MAIN` and `SUB-01`, `SUB-02`, … wherever a Linear identifier would go (parent, dependencies, the Dependencies section).
- **Blocks**: one block per issue, main issue first. Each block lists the fields the create call would send, then the description from the template.

```markdown
# MAIN — [corral] Implement global hotkey system

- Project: corral
- Team: private
- Priority: 3 (Medium)
- Labels: None

(main issue description)

---

# SUB-01 — [corral] Configure Tauri global hotkey plugin

- Project: corral
- Team: private
- Parent: MAIN
- Labels: Front-end, Feature
- Blocked by: None

(sub-issue description)
```

The Mandatory Rules and the Pre-Creation Checklist still apply to the drafted fields.

---

## Pre-Creation Checklist

Verify before creating any issue:

**Common:**
- [ ] Is the project specified?
- [ ] Do all issue titles start with `[ProjectName]`?
- [ ] Does the main issue have **no labels**?
- [ ] Does every sub-issue have **exactly 2 labels** (1 area + 1 type)?
- [ ] Does each sub-issue's `parentId` point to the main issue?
- [ ] Are all issues linked to the project via `project`?
- [ ] Are inter-sub-issue dependencies defined?

**PRD Pipeline additional checks (when PRD workflow is selected):**
- [ ] Is the pattern (A/B/C) determined?
- [ ] Has the description passed through all content skill stages for the selected pattern?
- [ ] Is it written in Korean?
- [ ] Is the Professional tone maintained?
- [ ] Are concrete specs included with no vague expressions?
- [ ] Are AI patterns (repetitive phrasing, excessive qualifiers) removed?
