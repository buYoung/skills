---
name: linear-issue-creator
description: >
  Skill for creating structured issues in Linear. Produces a main issue + multiple sub-issues,
  automatically applying project linking, title prefix, and labeling rules.
  Use this skill whenever the user asks to "create a Linear issue", "register a task in Linear",
  "break down tasks into Linear issues", "create a feature issue", "file a bug in Linear",
  "make a Linear ticket", or any other request related to creating new issues in Linear.
  Triggers for all new issue creation — not for querying or updating existing issues.
---

# Linear Issue Creator

Create issues in Linear using the Linear MCP with a **1 main issue + N sub-issues** structure.

---

## Core Principles

| Aspect | Main Issue | Sub-Issue |
|---|---|---|
| Perspective | Business / user perspective | Developer / engineer perspective |
| Unit | One feature or problem | One PR-completable task |
| Key question | "What changes for the user?" | "What code do we change?" |
| Labels | None | Exactly 2 (1 area + 1 type) |
| Status mgmt | Auto-completes when all sub-issues are done | Transitions individually |

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

Call `Linear:save_issue` to create the main issue.

**Parameters:**
```
title: "[ProjectName] Main title"
team: "private"
project: "project-name"
description: (use template below)
priority: appropriate priority (1=Urgent, 2=High, 3=Normal, 4=Low)
```

**Main issue description template:**

```markdown
## Purpose / Background

Describe why this work is needed.
Include business context, user problems, or technical debt.

## Goal

Define the end state when this issue is complete, in one or two sentences.

## Acceptance Criteria

- [ ] Condition 1 that must be met for the work to be considered "done"
- [ ] Condition 2
- [ ] Condition 3

## Scope

**In Scope:**
- What this issue covers

**Out of Scope:**
- What this issue does NOT cover

## Impact Area

Describe which services, modules, or screens are affected.
```

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

**Sub-issue description template:**

```markdown
## Task Description

Describe specifically what to change, add, or remove.

## Target Location

- List relevant file paths, modules, endpoints, or component names.

## Technical Details

- **Logic / data flow changes**: What logic changes and how
- **Libraries / patterns**: Tech stack or design patterns to use
- **API spec** (if applicable):
  - Request: `METHOD /path` + body shape
  - Response: success / error response shape

## Done Criteria

- [ ] Specific condition that marks this sub-issue as complete
  - e.g., "POST /api/users endpoint returns 422 validation error"
  - e.g., "Login form shows error message when email field is empty"

## Dependencies

- State if another sub-issue must be completed first.
  - e.g., "Requires SUB-002 (DB schema change) to be done first"
- If none, write "None".
```

### Step 4: Link Dependencies

If sub-issues depend on each other, connect them with `blockedBy`.

```
Linear:save_issue (update)
  id: "dependent issue identifier"
  blockedBy: ["prerequisite issue identifier"]
```

### Step 5: Report Results

Summarize all created issues for the user:

- Main issue identifier + title + URL
- Sub-issue list (identifier, title, 2 labels, dependencies)

---

## Example: Full Flow

User: "Create a global hotkey feature for the corral project. It's a front-end feature."

**1) Create main issue:**
```
Linear:save_issue
  title: "[corral] Implement global hotkey system"
  team: "private"
  project: "corral"
  description: (filled from main template)
  priority: 3
  → Result: PRI-42
```

**2) Create sub-issues:**
```
Linear:save_issue
  title: "[corral] Configure Tauri global hotkey plugin"
  team: "private"
  project: "corral"
  parentId: "PRI-42"
  labels: ["Front-end", "Feature"]
  description: (filled from sub template)
  → Result: PRI-43

Linear:save_issue
  title: "[corral] Build hotkey settings UI component"
  team: "private"
  project: "corral"
  parentId: "PRI-42"
  labels: ["Front-end", "Feature"]
  description: (filled from sub template)
  blockedBy: ["PRI-43"]
  → Result: PRI-44
```

**3) Report results:**
> ✅ Issues created
>
> **Main issue**: PRI-42 — [corral] Implement global hotkey system
>
> **Sub-issues:**
> | # | Title | Labels | Depends on |
> |---|---|---|---|
> | PRI-43 | [corral] Configure Tauri global hotkey plugin | Front-end, Feature | None |
> | PRI-44 | [corral] Build hotkey settings UI component | Front-end, Feature | PRI-43 |

---

## Pre-Creation Checklist

Verify before creating any issue:

- [ ] Is the project specified?
- [ ] Do all issue titles start with `[ProjectName]`?
- [ ] Does the main issue have **no labels**?
- [ ] Does every sub-issue have **exactly 2 labels** (1 area + 1 type)?
- [ ] Does each sub-issue's `parentId` point to the main issue?
- [ ] Are all issues linked to the project via `project`?
- [ ] Are inter-sub-issue dependencies defined?
