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

## Purpose / Background

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
save_issue
  title: "[corral] Implement global hotkey system"
  team: "private"
  project: "corral"
  description: (filled from main template)
  priority: 3
  → Result: PRI-42
```

**2) Create sub-issues:**
```
save_issue
  title: "[corral] Configure Tauri global hotkey plugin"
  team: "private"
  project: "corral"
  parentId: "PRI-42"
  labels: ["Front-end", "Feature"]
  description: (filled from sub template)
  → Result: PRI-43

save_issue
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

**2) Create main issue:**
```
save_issue
  title: "[corral] Implement real-time notification system"
  team: "private"
  project: "corral"
  description: |
    ## PRD Context

    - **Topic**: 실시간 알림 시스템
    - **Target audience**: Fullstack developers
    - **Language**: Korean
    - **Tone**: Professional
    - **Pipeline pattern**: A. Blank→Complete

    ## Purpose / Background

    사용자는 댓글, 멘션, 상태 변경 같은 주요 인앱 이벤트를 실시간으로
    확인해야 합니다. 지금은 페이지를 새로고침해야 새 알림이 보입니다.

    ## Goal

    이벤트가 발생하면 바로 사용자에게 알림을 보내는 WebSocket 기반
    실시간 알림 시스템을 만듭니다.

    ## Acceptance Criteria

    - [ ] WebSocket 연결로 알림을 실시간으로 받는다
    - [ ] 알림 목록 API가 페이지네이션을 지원한다 (GET /api/notifications?cursor=)
    - [ ] 헤더에 읽지 않은 알림 수가 표시된다
    - [ ] 알림을 클릭하면 해당 리소스로 이동한다

    ## Scope

    **In Scope:** WebSocket 서버, 알림 CRUD API, 알림 UI 컴포넌트
    **Out of Scope:** 이메일/푸시 알림, 알림 설정 페이지 (후속 이슈에서 다룸)

    ## Impact Area

    백엔드: notifications 모듈, WebSocket 게이트웨이
    프론트엔드: 헤더 컴포넌트, 알림 드롭다운
  priority: 2
  → Result: PRI-50
```

**3) Create sub-issues:**
```
save_issue
  title: "[corral] Create notification data model and migration"
  team: "private"
  project: "corral"
  parentId: "PRI-50"
  labels: ["Back-end", "Feature"]
  description: |
    ## Task Description

    notifications 테이블을 만드는 마이그레이션(롤백 포함)과 TypeORM 엔티티를 추가합니다.

    ## Target Location

    - src/database/migrations/
    - src/modules/notifications/entities/notification.entity.ts

    ## Technical Details

    - **Data model**:
      - notifications 테이블: id(UUID), userId(FK), type(enum), title(varchar 200),
        body(text), resourceType(varchar 50), resourceId(varchar 50),
        isRead(boolean, default false), createdAt(timestamp)
      - 인덱스: (userId, createdAt DESC), (userId, isRead)

    ## Done Criteria

    - [ ] 마이그레이션을 실행하면 notifications 테이블이 생성된다
    - [ ] Notification 엔티티가 TypeORM 데코레이터로 정의되어 있다
    - [ ] 롤백 마이그레이션을 실행하면 테이블이 삭제된다

    ## Dependencies

    None
  → Result: PRI-51

save_issue
  title: "[corral] Implement notification CRUD REST API"
  team: "private"
  project: "corral"
  parentId: "PRI-50"
  labels: ["Back-end", "Feature"]
  description: |
    ## Task Description

    알림 목록 조회(커서 기반 페이지네이션), 읽음 처리, 읽지 않은 알림 수 조회 API를
    구현합니다. 읽음 처리는 본인 알림에만 허용합니다.

    ## Target Location

    - src/modules/notifications/notifications.controller.ts
    - src/modules/notifications/notifications.service.ts

    ## Technical Details

    - **API spec**:
      - GET /api/notifications?cursor=&limit=20
        - Success: 200 + `{ items: Notification[], nextCursor: string | null }`
      - PATCH /api/notifications/:id/read
        - Success: 200 + `{ id, isRead: true }`
        - Error: 404 (알림 없음), 403 (본인 알림이 아님)
      - GET /api/notifications/unread-count
        - Success: 200 + `{ count: number }`

    ## Done Criteria

    - [ ] GET /api/notifications가 커서 기반 페이지네이션으로 동작한다
    - [ ] PATCH /api/notifications/:id/read는 본인 알림만 읽음으로 바꾼다
    - [ ] GET /api/notifications/unread-count가 읽지 않은 알림 수를 반환한다

    ## Dependencies

    PRI-51(데이터 모델)이 먼저 완료되어야 합니다
  blockedBy: ["PRI-51"]
  → Result: PRI-52
```

**4) Report results:**
> Issues created
>
> **Main issue**: PRI-50 — [corral] Implement real-time notification system
>
> **Sub-issues:**
> | # | Title | Labels | Depends on |
> |---|---|---|---|
> | PRI-51 | [corral] Create notification data model and migration | Back-end, Feature | None |
> | PRI-52 | [corral] Implement notification CRUD REST API | Back-end, Feature | PRI-51 |
