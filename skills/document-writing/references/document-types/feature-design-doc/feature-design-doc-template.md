---
doc-type: Feature Design Doc
profile: full # full | compact — see feature-design-doc-create.md
feature-name: [kebab-case-feature-name]
status: active # active | superseded
created: [YYYY-MM-DD]
last-verified: [YYYY-MM-DD]
verified-against: [commit hash the doc was last checked against]
tags: [] # search keywords / aliases for discovery
related: [] # relative paths to related FDDs
purpose: Source of design decisions, not implementation actions
agent-readable: true
not:
  - task list
  - PR checklist
  - file-level change guide
---

# [Feature Name] Feature Design Doc

## 1. Document Intent

This document is the source of design decisions, not implementation actions.

It defines product behavior, domain concepts, policy decisions, platform constraints,
cross-cutting concerns, and alternatives considered.

Implementation plans, task ordering, file paths, function names, and PR breakdowns
are produced separately.

---

## 2. Background / Problem

Explain the current problem, user pain, and product context.

Questions to answer:

- What problem exists today?
- Why is the current behavior insufficient?
- Why should this feature exist now?
- What user workflow does this improve?

---

## 3. Feature Definition

Define the feature in one sentence.

```text
[Feature Name] is ...
```

### This feature is

> Use this section for category and identity.
> These statements explain what kind of feature this is.

- ...
- ...
- ...

### This feature is not

> Use this section only for category-level misunderstandings.
> Do not put version-specific exclusions here. Put those in Scope.
> Do not put deliberately rejected goals here. Put those in Non-Goals.

- ...
- ...
- ...

---

## 4. Goals & Non-Goals

> Goals describe what this design is trying to achieve.
>
> Non-Goals are things that could reasonably have been goals,
> but were intentionally not selected.
>
> Category-level negatives belong in `Feature Definition`.
> Version-level exclusions belong in `Scope`.

### Goals

- ...
- ...
- ...

### Non-Goals

- ...
- ...
- ...

---

## 5. User Model & Core Concepts

### User Model

Describe how users understand this feature.

Users think of this feature as:

- ...
- ...
- ...

Users should not need to understand:

- ...
- ...
- ...

### Core Concepts

| Concept | Meaning |
| ------- | ------- |
| ...     | ...     |
| ...     | ...     |

---

## 6. Relationship to Existing Features

Explain how this feature relates to existing product concepts.

| Existing Feature | Relationship                              |
| ---------------- | ----------------------------------------- |
| ...              | Reused / extended / replaced / unaffected |
| ...              | ...                                       |

Guidance:

- Use this section for conceptual relationships.
- Do not list files, modules, or implementation tasks here.
- File-level details belong in the Implementation Plan.

---

## 7. Primary User Flows

Describe user-visible flows, not implementation steps.

### 7.1 Main Flow

```text
User does ...
  -> System does ...
  -> User sees ...
```

### 7.2 Secondary Flow

```text
...
```

### 7.3 Failure / Partial Success Flow

```text
...
```

---

## 8. Design

Describe the actual feature design at the system level.

Do not turn this section into a task list.
Avoid file paths, function names, and PR ordering unless they are essential to the design itself.

### 8.1 Behavior

Describe how the system behaves.

Examples:

- What is captured?
- What is restored?
- What is matched?
- What is persisted?
- What is shown to the user?

### 8.2 Conceptual Data Model

Describe entities and important fields conceptually.

| Entity | Meaning |
| ------ | ------- |
| ...    | ...     |

| Field | Meaning |
| ----- | ------- |
| ...   | ...     |

### 8.3 Failure Handling

Describe expected failure categories and how the system should respond.

Examples:

- Missing resource
- Permission denied
- Ambiguous match
- Unsupported platform behavior
- Partial success

Detailed user-visible result states may be placed in `Result Semantics`.

---

## 9. Policy Decisions

Use this section for decisions that resolve ambiguity.

Each policy should include the decision and rationale.

### 9.1 [Policy Area]

Decision:

- ...

Rationale:

- ...

Example policy areas:

- Matching policy
- Missing resource policy
- Permission policy
- Launch policy
- Persistence policy
- Conflict resolution policy
- Degradation policy

---

## 10. Alternatives Considered

Use this section to record meaningful options that were considered and rejected.

This prevents future readers or code agents from reintroducing discarded approaches
without understanding why they were rejected.

### Alternative: [Name]

Description:

- ...

Why not chosen:

- ...

### Alternative: [Name]

Description:

- ...

Why not chosen:

- ...

---

## 11. Cross-cutting Concerns

> The sections below are checklist prompts.
>
> Do not silently delete an item because it seems irrelevant.
> If an item does not apply, write:
>
> `Not applicable: [short reason]`
>
> Silence is not distinguishable from accidental omission.
>
> Compact profile only: the six subsections below may be replaced by a
> single list with one line per concern, e.g.
> `- Security: Not applicable: no new attack surface`.

### 11.1 Security

- ...
- Not applicable: ...

### 11.2 Privacy

- ...
- Not applicable: ...

### 11.3 Permissions

- ...
- Not applicable: ...

### 11.4 Observability

- ...
- Not applicable: ...

### 11.5 Accessibility

- ...
- Not applicable: ...

### 11.6 Internationalization

- ...
- Not applicable: ...

---

## 12. Scope

> Scope is version- or release-specific.
> For solo or continuous-delivery work with no release train,
> label the boundary "as implemented (YYYY-MM-DD)".
>
> Use this section to say what is included or excluded from the current delivery.
> Do not use this section for category-level identity statements.
> Do not use this section for rejected design alternatives.

### In Scope for [Version]

- ...
- ...
- ...

### Out of Scope for [Version]

- ...
- ...
- ...

---

## 13. Risks & Open Questions

### Risks

Known risks that are accepted or need mitigation.

- ...
- ...

### Open Questions

Questions that are intentionally left unresolved in this design.

- ...
- ...

---

## 14. Platform Design

> Optional.
>
> Required for cross-platform, OS-sensitive, hardware-sensitive,
> browser-sensitive, runtime-sensitive, or platform API-heavy features.

### 14.1 Common Design

Describe platform-independent behavior.

### 14.2 [Platform A]

Describe platform-specific capabilities, constraints, and differences.

### 14.3 [Platform B]

Describe platform-specific capabilities, constraints, and differences.

---

## 15. Result Semantics

> Optional.
>
> Required for features with meaningful operation states, partial success,
> restore results, sync states, migration outcomes, or user-visible failures.
>
> Use this section for externally visible result states.
> Internal implementation state machines belong in the Implementation Plan
> unless they are part of the product design.

| State | Meaning | User-visible? |
| ----- | ------- | ------------- |
| ...   | ...     | Yes / No      |

---

## 16. Future Extensions

> Optional.
>
> Use this section only for follow-up ideas that are intentionally outside
> the current scope but worth preserving as future candidates.
>
> Do not duplicate every Out of Scope item here.
> Only list items that are plausible future product directions.

- ...
- ...
- ...

---

## Revision History

> Optional at first save; required from the first update onward.
> Append-only — never rewrite or delete earlier entries.
>
> Record design changes, superseded decisions (mark the original entry
> in place with `[superseded YYYY-MM-DD — see Revision History]` and keep it),
> and known deviations between this document and the implemented behavior
> that are not yet resolved.

| Date | Type | Summary |
| ---- | ---- | ------- |
| YYYY-MM-DD | updated / superseded / deviation | ... |

---

## Appendix

> Optional.
>
> Use for references, API notes, code maps, diagrams, prior art, research notes,
> screenshots, or links that support the design but are not part of the core narrative.

### Code Map (non-normative)

> Recommended for features documented after implementation.
> Code anchors are navigation metadata, not design content — they are exempt
> from the implementation-leakage rule, and they MAY go stale. Pair them with
> the `verified-against` commit so future readers can diff forward.

| Concept / Flow | Where it lived (as of `verified-against`) |
| -------------- | ----------------------------------------- |
| ...            | ...                                       |
