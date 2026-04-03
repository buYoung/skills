---
name: linear-issue-worker
description: >
  Execute code tasks from Linear sub-issues: resolve dependencies, implement changes, validate Done Criteria, and sync status.
  Use when asked to work on, implement, or start coding a Linear issue (e.g. PRI-42).
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

Post a start comment (write in Korean, Professional tone, no AI patterns — natural and direct):
```
Linear:save_comment
  issueId: "<sub-issue-id>"
  body: |
    ## 🚀 Work Started

    ### Approach
    - [Implementation approach summary — include specific technical decisions]
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

**Comment Quality Guide (Content Skill Principles):**

Apply these principles when writing completion comments to improve quality.
Target audience: Fullstack developers | Language: Korean | Tone: Professional

1. **content-strategy**: Structure comments clearly (maintain Changes → Done Criteria → Notes order. Each section delivers the information the reader needs without gaps).
2. **content-production**: Write specific, verifiable content.
   - "Fixed it" → "Added inventory validation logic to POST /api/orders endpoint, returns 409 when out of stock"
   - "Tests done" → "Added 3 unit tests (normal order, out-of-stock, invalid product ID)"
3. **content-humanizer**: Remove AI patterns and write in natural Korean.
   - Avoid repeating the same sentence structure — vary verb endings and phrasing
   - Remove unnecessary qualifiers ("effectively," "successfully")
   - Maintain the tone of explaining to a peer developer
4. **copy-editing**: Focus on Clarity and Specificity.
   - Verify file paths and change descriptions are concrete with no vague expressions
   - Verify Done Criteria evidence is code-level verifiable

### 3f. Transition to Done

```
Linear:save_issue
  id: "<sub-issue-id>"
  state: "Done"
```

### 3g. Move to Next

Re-evaluate the remaining sub-issues. Issues that were blocked by the just-completed one may now be ready. Pick the next ready sub-issue and repeat from 3a.

---

For exception handling (missing files, unavailable dependencies, ambiguous criteria, blockers, deadlocks), see `references/exceptions.md`.

## Completion

When all sub-issues are processed:

1. Review the main issue's **Acceptance Criteria**
2. Post a summary comment on the **main issue** (write in Korean, Professional tone. Apply content skill principles — specific, no AI patterns, clear):

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
    [Concretely summarize all changes and current state]
```

3. If all acceptance criteria are met and all sub-issues are Done, inform the user that the work is complete
4. If some criteria are unmet, explain what remains and suggest next steps

---

For Linear API details (state values, description parsing, tool calls, retry policy), see `references/linear-api.md`.
