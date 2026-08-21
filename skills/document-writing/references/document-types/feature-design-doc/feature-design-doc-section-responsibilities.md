# FDD section responsibilities

Use this reference whenever creating, updating, fact-checking, or normalizing an FDD.

## Responsibility map

| Statement | Section |
| --- | --- |
| What kind of feature this is or is not | Feature Definition |
| What the design aims to achieve | Goals |
| A plausible goal deliberately rejected | Non-Goals |
| What is included or excluded for a version | Scope |
| How users understand the feature | User Model & Core Concepts |
| How this feature relates to existing product concepts | Relationship to Existing Features |
| User-visible sequences and outcomes | Primary User Flows |
| System-level product behavior and conceptual model | Design |
| A rule that resolves product ambiguity, with rationale | Policy Decisions |
| A considered design path and why it was rejected | Alternatives Considered |
| Security, privacy, permissions, observability, accessibility, and internationalization | Cross-cutting Concerns |
| Accepted risks and deliberately unresolved decisions | Risks & Open Questions |
| Platform-specific capability or constraint | Platform Design |
| Externally meaningful success, partial, and failure states | Result Semantics |
| Plausible later product direction | Future Extensions |

## Common confusions

### Feature Definition versus Non-Goals

Identity says what category the feature belongs to. A non-goal is something the feature could reasonably have pursued but deliberately does not.

### Non-Goals versus Scope

A non-goal rejects an aspiration. Out of Scope excludes work from the current release boundary and may still allow it later.

### Scope versus Future Extensions

Scope defines the current delivery boundary. Future Extensions preserves selected plausible directions, not every excluded item.

### Design failure handling versus Result Semantics

Design describes how the product should handle a failure category. Result Semantics defines meaningful externally visible outcome states.

### Policy Decisions versus Alternatives

A policy resolves recurring ambiguity. An alternative records a design path that was considered and rejected.

When a statement appears to fit two sections, rewrite it until its responsibility is singular rather than duplicating it.

## Decision ownership and semantic deduplication

Assign one canonical owning section to each policy, invariant, numeric limit, decision rule, and exception list. Other sections may project only the consequence needed for their own responsibility; they should not redefine the exact rule or repeat its rationale.

- Primary User Flows own user actions and visible outcomes, not complete policy formulas.
- Design owns system boundaries, conceptual models, and failure mechanisms, not policy rationale or result-state tables.
- Policy Decisions own the exact rule and rationale.
- Cross-cutting Concerns own only the security, privacy, permission, observability, accessibility, or internationalization consequence.
- Scope owns the versioned feature surface, not detailed decision algorithms.
- Result Semantics owns state names, effects, and user visibility, not the policy that selects a state.

Use a concise cross-reference when another section needs the canonical rule. Treat an exact limit, decision formula, or exception list that is fully restated in three or more responsibility sections as a consolidation candidate.

During final review, remove or replace a repeated statement with a cross-reference when deleting it would not erase that section's unique responsibility. Consistency through repetition is not a substitute for clear decision ownership.
