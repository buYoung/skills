---
name: linear-issue-worker
description: >
  Skill for executing code tasks from Linear issues created by the linear-issue-creator skill.
  Reads a main issue's sub-issues, resolves the dependency graph (blockedBy), then sequentially
  works through each actionable sub-issue: transitions status to In Progress, performs the actual
  code work (file creation/modification), validates against Done Criteria, posts completion comments,
  and transitions to Done.
  Use this skill whenever the user asks to "work on a Linear issue", "execute Linear tasks",
  "implement the sub-issues", "start working on PRI-XX", "process my Linear issues",
  "do the coding work from Linear", or any request to pick up and implement tasks that already
  exist as Linear issues. Also triggers when the user says "work on this issue", "implement this",
  or references a specific issue identifier (e.g., PRI-42) and wants the actual code done.
  This skill is the counterpart to linear-issue-creator — the creator makes issues, this skill does them.
---

# Linear Issue Worker

Execute code tasks from Linear issues produced by the `linear-issue-creator` skill.
Read structured sub-issues, resolve dependency order, perform the actual file changes,
and keep Linear in sync throughout.

---

## Contract with linear-issue-creator

The creator produces a **1 main issue + N sub-issues** structure.
Each sub-issue contains everything needed for one unit of code work:
Task Description, Target Location, Technical Details, Done Criteria, and Dependencies.
This skill consumes that structure and turns it into real code changes.

---

## Workflow

### Step 1 — Receive the Main Issue

The user provides a main issue identifier (e.g., `PRI-42`).

1. Call `Linear:get_issue` with `includeRelations: true`
2. Parse the main issue description to extract:
   - **Purpose / Background** — why this work exists
   - **Goal** — desired end state
   - **Acceptance Criteria** — final validation checklist (used at the very end)
   - **Scope** — boundaries of the work
   - **Impact Area** — affected parts of the codebase
3. Keep this context in mind — it guides all sub-issue work, but you do NOT code against the main issue directly

### Step 2 — List and Sort Sub-Issues

1. Call `Linear:list_issues` with `parentId` set to the main issue identifier
2. For each sub-issue, call `Linear:get_issue` with `includeRelations: true` to retrieve `blockedBy` data
   - If `get_issue` fails for a sub-issue, retry once. If it still fails, use the data already available from `list_issues` and check the `blocks` field of other sub-issues to infer the dependency graph
3. Filter out sub-issues with status `Done` or `Canceled`
4. Build a dependency-respecting execution order:
   - A sub-issue is **ready** when it has no `blockedBy` entries, or all its blockers are `Done`
   - Sort ready issues by priority (Urgent first), then creation order
   - If circular dependencies are detected, report to the user and stop

Present the execution plan and wait for user confirmation:
```
📋 Execution Plan for PRI-42:
1. PRI-43 — [project] Configure hotkey plugin (no dependencies)
2. PRI-44 — [project] Build settings UI (blocked by PRI-43)

Proceed?
```

### Step 3 — Process Each Sub-Issue

For each sub-issue in order, run the full execution cycle below.
After completing one sub-issue, re-evaluate the remaining list — previously blocked issues may now be ready.

---

## Sub-Issue Execution Cycle

### 3a. Read and Parse

Parse each section of the sub-issue description:

| Section | How to use it |
|---|---|
| **Task Description** | Understand what to build / change / fix |
| **Target Location** | Open these files to understand current code structure |
| **Technical Details** | Plan the implementation — patterns, libraries, API specs |
| **Done Criteria** | Exit conditions — every item must be satisfiable |
| **Dependencies** | Verify prerequisite sub-issues are already Done |

Check the sub-issue's **labels** to determine approach:

| Label | Approach |
|---|---|
| `Front-end` | Work in frontend codebase, verify from browser/UI perspective |
| `Back-end` | Work in server codebase, verify from API/DB perspective |
| `Feature` | Design-first, build the new thing |
| `Bug` | Root-cause analysis first, then fix |
| `Refactor` | Preserve behavior, improve structure |
| `Chore` | Config / build / dependency changes |
| `Perf` | Measure before and after |
| `Docs` | Documentation changes only |

### 3b. Transition to In Progress + Start Comment

Update the issue status:
```
Linear:save_issue
  id: "<sub-issue-id>"
  state: "started"
```

Post a start comment:
```
Linear:save_comment
  issueId: "<sub-issue-id>"
  body: |
    ## 🚀 Work Started

    ### Approach
    - [Brief description of implementation approach]
    - [Key files to modify or create]
    - [Notable decisions or trade-offs]
```

### 3c. Perform Code Work

1. **Explore** — Read files listed in Target Location to understand current state
2. **Plan** — Based on Technical Details, decide exactly what to change
3. **Implement** — Create or modify files
4. **Verify** — Check each Done Criteria item against the changes

Guidelines:
- Respect existing code style and conventions
- If Target Location files don't exist, search nearby directories for the most logical placement and note the deviation in a comment
- If Technical Details reference a library not in the project, check `package.json` / `requirements.txt` or equivalent first. Install if reasonable, or note the gap
- Keep changes scoped to what the sub-issue describes — don't refactor unrelated code

### 3d. Self-Validate Against Done Criteria

Before marking complete, go through each Done Criteria checkbox:
- Confirm the condition is met by the changes
- If a criterion requires runtime verification (e.g., "API returns 422"), explain what was implemented and why it satisfies the criterion

### 3e. Post Completion Comment

```
Linear:save_comment
  issueId: "<sub-issue-id>"
  body: |
    ## ✅ Work Complete

    ### Changes
    - `path/to/file1.ts` — [what changed]
    - `path/to/file2.ts` — [new file, what it does]

    ### Done Criteria
    - [x] Criterion 1 — [brief evidence]
    - [x] Criterion 2 — [brief evidence]

    ### Notes
    - [Any deviations, edge cases discovered, etc.]
```

### 3f. Transition to Done

```
Linear:save_issue
  id: "<sub-issue-id>"
  state: "Done"
```

### 3g. Move to Next

Re-evaluate the remaining sub-issues. Issues that were blocked by the just-completed one may now be ready. Pick the next ready sub-issue and repeat from 3a.

---

## Exception Handling

**Target Location file doesn't exist:**
1. Post a comment noting the expected file was not found
2. Search nearby directories for the most logical placement
3. If confident, proceed and note the deviation. If unsure, ask the user

**Library / dependency not available:**
1. Check if it can be installed (`npm install`, `pip install`, etc.)
2. If reasonable, install and note in the completion comment
3. If it's a major or unexpected dependency, ask the user

**Done Criteria is ambiguous or impossible:**
1. Post a comment stating your interpretation
2. Proceed based on that interpretation
3. Flag it clearly in the completion comment

**Blocker discovered mid-work:**
1. Post a comment explaining the blocker
2. Transition the issue back to Todo using `state: "unstarted"`
3. Move to the next available sub-issue
4. If nothing else is available, report to the user and stop

**All remaining sub-issues are blocked (deadlock):**
1. Report the dependency graph to the user
2. Suggest which blocker to resolve manually or which dependency to remove

---

## Completion

When all sub-issues are processed:

1. Review the main issue's **Acceptance Criteria**
2. Post a summary comment on the **main issue**:

```
Linear:save_comment
  issueId: "<main-issue-id>"
  body: |
    ## 📋 Overall Completion Report

    ### Completed Sub-Issues
    - [x] SUB-01 — Title
    - [x] SUB-02 — Title

    ### Incomplete Sub-Issues (if any)
    - [ ] SUB-03 — Title (reason: ...)

    ### Acceptance Criteria Review
    - [x] Criterion from main issue — satisfied by SUB-01, SUB-02
    - [ ] Criterion from main issue — not yet met (reason: ...)

    ### Summary
    [Brief summary of all changes and current state]
```

3. If all acceptance criteria are met and all sub-issues are Done, inform the user that the work is complete
4. If some criteria are unmet, explain what remains and suggest next steps

---

## Linear API Reference

### State Parameter Values

The `state` field in `Linear:save_issue` accepts either the state type or state name, but behavior can be inconsistent across statuses. Use these tested, working values:

| Desired Status | `state` value to use | Why |
|---|---|---|
| In Progress | `"started"` | Name `"In Progress"` fails; use the type |
| Done | `"Done"` | Type `"completed"` fails; use the name |
| Back to Todo | `"unstarted"` | Use the type |
| Canceled | `"Canceled"` | Use the name |

Always verify the transition succeeded by checking the `status` field in the API response. If the status didn't change, try the alternative form (name vs type).

### Description Parsing

Linear API may return description text with escaped newlines (`\\n` as `\\\\n` in JSON). When parsing section headers like `## Task Description`, account for this escaping — look for both `## ` and `\\n## ` patterns when splitting sections.

### Tool Call Summary

| Action | Tool | Key Parameters |
|---|---|---|
| Read issue | `Linear:get_issue` | `id`, `includeRelations: true` |
| List sub-issues | `Linear:list_issues` | `parentId` |
| Update status | `Linear:save_issue` | `id`, `state` |
| Post comment | `Linear:save_comment` | `issueId`, `body` |

### Retry Policy

If `Linear:get_issue` or `Linear:list_issues` fails, retry once before falling back to alternative data sources (e.g., inferring relations from sibling issues' `blocks` field).
