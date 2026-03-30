# Issue Description Templates

## Main Issue Description Template

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

---

## Sub-Issue Description Template

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
> Issues created
>
> **Main issue**: PRI-42 — [corral] Implement global hotkey system
>
> **Sub-issues:**
> | # | Title | Labels | Depends on |
> |---|---|---|---|
> | PRI-43 | [corral] Configure Tauri global hotkey plugin | Front-end, Feature | None |
> | PRI-44 | [corral] Build hotkey settings UI component | Front-end, Feature | PRI-43 |
