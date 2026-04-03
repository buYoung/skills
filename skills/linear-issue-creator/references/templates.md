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

---

## PRD Main Issue Description Template

```markdown
## PRD Context

- **Topic**: [PRD topic]
- **Target audience**: Fullstack developers
- **Language**: Korean
- **Tone**: Professional
- **Pipeline pattern**: [A. Blank→Complete / B. Draft→Complete / C. Polish only]

## Background & Purpose

[Describe why this feature/system is needed.
Include specific context: user problems, business requirements, or technical debt.]

## Goal

[Define the end state when this issue is complete, in 1-2 sentences.]

## Acceptance Criteria

- [ ] [Measurable condition 1 — e.g., "POST /api/orders returns 201"]
- [ ] [Measurable condition 2 — e.g., "Order list page displays shipping status column"]
- [ ] [Measurable condition 3]

## Technical Requirements Overview

[Summarize key technical requirements from frontend/backend/infra perspectives.
Each sub-issue covers details — present only the big picture here.]

## Scope

**In Scope:**
- [Features/modules this issue covers]

**Out of Scope:**
- [What this issue does NOT cover — explicitly set boundaries]

## Impact Area

[List which services, modules, screens, and APIs are affected.]
```

---

## PRD Sub-Issue Description Template

```markdown
## Task Description

[Describe specifically what to change/add/remove.
Ensure enough specificity that the implementer can start work without additional questions.]

## Target Location

- [List file paths, module names, endpoints, or component names]

## Technical Details

- **Logic / data flow**: [What logic changes and how]
- **Tech stack / patterns**: [Technologies, design patterns to use]
- **API spec** (if applicable):
  - Request: `METHOD /path` + body format
  - Success response: HTTP code + body format
  - Error response: HTTP code + error code + body format
- **Data model** (if applicable):
  - Table/collection name, fields, types, constraints

## Done Criteria

- [ ] [Code-level verifiable condition]
  - e.g., "POST /api/orders with out-of-stock item returns 409 + `{ code: 'OUT_OF_STOCK' }`"
  - e.g., "Order detail page shows shipping tracking link when status is 'Shipping'"

## Dependencies

- [State prerequisite sub-issues if any]
- If none, write "None".
```

---

## Example: Full Flow (Generic)

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

---

## Example: Full Flow (PRD Pipeline, Pattern A)

User: "Create a PRD for a real-time notification system. Project is corral. Starting from scratch."

**1) Pattern selection:** Blank state → Pattern A (content-strategy → content-production → content-humanizer → copy-editing)

**2) Description writing process:**
- content-strategy: Plan notification system PRD structure (WebSocket connection, notification CRUD API, UI components, notification settings)
- content-production: Draft with concrete specs (endpoints, data model, component structure)
- content-humanizer: Remove AI patterns, convert to natural Korean technical writing
- copy-editing: Clarity + Specificity + So What review

**3) Create main issue:**
```
Linear:save_issue
  title: "[corral] Implement real-time notification system"
  team: "private"
  project: "corral"
  description: |
    ## PRD Context

    - **Topic**: Real-time notification system
    - **Target audience**: Fullstack developers
    - **Language**: Korean
    - **Tone**: Professional
    - **Pipeline pattern**: A. Blank→Complete

    ## Background & Purpose

    Users need to see key in-app events (comments, mentions, status changes)
    in real time. Currently they must refresh to see new notifications,
    degrading user experience.

    ## Goal

    Build a WebSocket-based real-time notification system that delivers
    notifications to users immediately when events occur.

    ## Acceptance Criteria

    - [ ] Notifications are received in real time via WebSocket connection
    - [ ] Notification list API supports pagination (GET /api/notifications?cursor=)
    - [ ] Unread notification count is displayed in the header
    - [ ] Clicking a notification navigates to the relevant resource

    ## Scope

    **In Scope:** WebSocket server, notification CRUD API, notification UI components
    **Out of Scope:** Email/push notifications, notification settings page (handled in follow-up issues)

    ## Impact Area

    Backend: notifications module, WebSocket gateway
    Frontend: header component, notification dropdown
  priority: 2
  → Result: PRI-50
```

**4) Create sub-issues:**
```
Linear:save_issue
  title: "[corral] Create notification data model and migration"
  team: "private"
  project: "corral"
  parentId: "PRI-50"
  labels: ["Back-end", "Feature"]
  description: |
    ## Task Description

    Create the notifications table that serves as the foundation for the notification system.

    ## Target Location

    - src/database/migrations/
    - src/modules/notifications/entities/notification.entity.ts

    ## Technical Details

    - **Data model**:
      - notifications table: id(UUID), userId(FK), type(enum), title(varchar 200),
        body(text), resourceType(varchar 50), resourceId(varchar 50),
        isRead(boolean, default false), createdAt(timestamp)
      - Indexes: (userId, createdAt DESC), (userId, isRead)

    ## Done Criteria

    - [ ] Running migration creates the notifications table
    - [ ] Notification entity is defined with TypeORM decorators
    - [ ] Rollback migration drops the table

    ## Dependencies

    None
  → Result: PRI-51

Linear:save_issue
  title: "[corral] Implement notification CRUD REST API"
  team: "private"
  project: "corral"
  parentId: "PRI-50"
  labels: ["Back-end", "Feature"]
  description: |
    ## Task Description

    Implement the notification CRUD API.

    ## Target Location

    - src/modules/notifications/notifications.controller.ts
    - src/modules/notifications/notifications.service.ts

    ## Technical Details

    - **API spec**:
      - GET /api/notifications?cursor=&limit=20
        - Success: 200 + `{ items: Notification[], nextCursor: string | null }`
      - PATCH /api/notifications/:id/read
        - Success: 200 + `{ id, isRead: true }`
        - Error: 404 (notification not found), 403 (not own notification)
      - GET /api/notifications/unread-count
        - Success: 200 + `{ count: number }`

    ## Done Criteria

    - [ ] GET /api/notifications works with cursor-based pagination
    - [ ] PATCH /api/notifications/:id/read marks only own notifications as read
    - [ ] GET /api/notifications/unread-count returns unread notification count

    ## Dependencies

    Requires PRI-51 (data model) to be completed first
  blockedBy: ["PRI-51"]
  → Result: PRI-52
```

**5) Report results:**
> Issues created
>
> **Main issue**: PRI-50 — [corral] Implement real-time notification system
>
> **Sub-issues:**
> | # | Title | Labels | Depends on |
> |---|---|---|---|
> | PRI-51 | [corral] Create notification data model and migration | Back-end, Feature | None |
> | PRI-52 | [corral] Implement notification CRUD REST API | Back-end, Feature | PRI-51 |
