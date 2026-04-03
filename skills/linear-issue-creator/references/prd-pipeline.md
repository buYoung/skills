# PRD Pipeline — Content Skill Application Guide

Detailed guide for writing issue descriptions at PRD quality.
Each stage adapts marketing content skill principles to the **technical document (PRD) context**.

---

## 1. content-strategy: Plan PRD Structure

Just as marketing plans "content pillars + topic clusters," a PRD plans the **issue structure**.

### Key Questions

| Question | PRD meaning |
|---|---|
| Whose problem does this feature solve, and what problem? | Backbone of the Purpose / Background section |
| What does the completed state look like? | Goal section — define in 1-2 sentences |
| Which technical domains are involved? | Sub-issue decomposition criteria (frontend/backend/infra) |
| Are there prerequisites? | Determines inter-sub-issue dependencies |

### PRD Section Derivation Checklist

Structure sections based on what fullstack developers need:

- **Feature overview**: What changes from the user's perspective
- **Technical requirements**: Technical conditions needed for implementation
- **API specs**: Endpoints, request/response formats (if applicable)
- **Data model**: Schema changes, migrations (if applicable)
- **Non-functional requirements**: Performance, security, scalability criteria
- **Impact area**: Which services/modules/screens are affected

### Sub-Issue Decomposition Principles

- One sub-issue = completable in one PR
- Separate frontend/backend work into different sub-issues
- Schema changes always go into a prerequisite sub-issue
- Shared utility/library work gets split out first

---

## 2. content-production: Draft Descriptions

Just as marketing writes "content briefs → drafts," a PRD writes **issue description drafts**.

### Writing Principles

**Specificity is everything.** The goal is for the implementer to start work without asking additional questions.

| Bad example | Good example |
|---|---|
| "Improve performance" | "Reduce list API response time from p95 500ms → 200ms" |
| "Add error handling" | "POST /api/orders returns 409 Conflict + `{ code: 'OUT_OF_STOCK', itemId }` when item is out of stock" |
| "Fix the UI" | "Add 'Shipping Status' column to order list table, values: Preparing/Shipping/Delivered" |
| "Strengthen security" | "Apply JWT auth middleware to all API endpoints, return 401 on expiration" |

### How to Write Acceptance Criteria

Write measurable, code-verifiable criteria:

- "X works" → "Calling X returns Y"
- "X is displayed" → "Screen A renders component B with data C"
- "X is fast" → "p95 response time is under N ms"

### How to Write Done Criteria (for sub-issues)

Each sub-issue's Done Criteria is used by the worker for self-validation, so it must be code-level specific:

- Specify endpoint + HTTP method + expected response
- Specify component name + rendering condition
- Specify error cases and expected behavior

---

## 3. content-humanizer: Remove AI Patterns

AI-generated descriptions exhibit repetitive, mechanical patterns. Transform these into natural Korean technical writing.

### Common AI Patterns in Korean Technical Documents

| AI pattern | Fix direction |
|---|---|
| Repeating "~해야 합니다" (must/should) | Distribute across varied forms: "~한다", "~으로 처리한다", "~를 적용한다" |
| Overuse of "매우 중요한" (very important), "필수적으로" (essentially), "반드시" (absolutely) | Use only when truly necessary. Most can be deleted without losing meaning |
| Repeating "이를 통해" (through this), "이를 위해" (for this) | Connect directly, or use "그래서" (so), "따라서" (therefore) |
| Overuse of "효과적으로" (effectively), "효율적으로" (efficiently) | Replace with concrete numbers or delete |
| All sentences similar length | Mix short and long sentences. One-liners are fine. |
| "~하는 것이 좋습니다" (it would be good to) | Write assertively: "~한다". A PRD is a decision document. |

### Style Guidelines

- **Tone of explaining to a peer developer**: "This feature is for X, and the key point is Y."
- **Remove unnecessary formality**: "본 문서에서는" (In this document) → delete or go straight to the point
- **Prefer active voice**: "Data must be stored" → "The server stores the data"
- **Keep technical terms as-is**: API, endpoint, schema, migration, etc. — do not translate

---

## 4. copy-editing: Seven Sweeps for PRDs

Seven Sweeps framework adapted for the PRD context.

### Sweep 1: Clarity

- [ ] Does every requirement have only one possible interpretation?
- [ ] Does the entire project team understand specialized terms the same way?
- [ ] Does any single sentence contain more than one requirement?
- [ ] Are there no subjective expressions like "appropriate," "sufficient," "as needed"?

### Sweep 2: Voice & Tone (Consistency)

- [ ] Does the entire document maintain the same tone? (No partial shifts between formal ↔ informal)
- [ ] Are verb endings consistent throughout? (No mixing "~합니다" and "~한다" style)
- [ ] Is technical terminology spelled consistently? (e.g., no mixing "엔드포인트" vs "end-point")

### Sweep 3: So What (Necessity)

- [ ] Does each requirement explain "why this is needed"?
- [ ] Does it go beyond listing features to connect to user/business value?
- [ ] Are technical decisions backed by stated rationale? (Why this tech stack? Why this architecture?)

### Sweep 4: Prove It (Evidence)

- [ ] Do performance requirements have target numbers? (p95 200ms, etc.)
- [ ] If "faster than X," is the current state (as-is) specified?
- [ ] Do technical constraints cite their source? (Library limitations, browser compatibility, etc.)

### Sweep 5: Specificity

- [ ] Do API specs include HTTP method, path, request/response format?
- [ ] Are data types and required/optional flags specified?
- [ ] Are error cases and response codes defined?
- [ ] Do UI requirements define what's displayed per state?

### Sweep 6: Heightened Emotion → For PRDs: **Motivation**

- [ ] Is "why this project matters" communicated to the team?
- [ ] (Low priority for PRDs — check only when applicable)

### Sweep 7: Zero Risk → For PRDs: **Gap Prevention**

- [ ] Are edge cases defined?
- [ ] Are error/failure scenario handling plans in place?
- [ ] Is there a migration/rollback plan? (if applicable)
- [ ] Are monitoring/alerting requirements included? (if applicable)
