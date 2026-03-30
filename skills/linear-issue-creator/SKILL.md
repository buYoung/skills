---
name: linear-issue-creator
description: >
  Create structured Linear issues (main + sub-issues) with project linking, title prefix, and labeling.
  Use when asked to create, register, or break down tasks into Linear issues. Not for querying or updating.
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

For a full flow example, see `references/templates.md`.

## Pre-Creation Checklist

Verify before creating any issue:

- [ ] Is the project specified?
- [ ] Do all issue titles start with `[ProjectName]`?
- [ ] Does the main issue have **no labels**?
- [ ] Does every sub-issue have **exactly 2 labels** (1 area + 1 type)?
- [ ] Does each sub-issue's `parentId` point to the main issue?
- [ ] Are all issues linked to the project via `project`?
- [ ] Are inter-sub-issue dependencies defined?
