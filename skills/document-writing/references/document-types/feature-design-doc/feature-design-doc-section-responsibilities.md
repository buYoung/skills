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

## Internal decision note before drafting

Before writing or changing FDD prose, make a short internal working note from the supplied inputs and relevant evidence. For an existing FDD, include its retained decisions and distinguish them from authorized changes. The note is working context, not an additional user deliverable or a required file.

For each material decision, record its meaning, supporting source or passage, authority or unresolved status, and one canonical owning section from the map above. Separate supplied or verified decisions from missing choices, conflicts, and proposals; absence of a rule does not establish its opposite. Record rationale only when supported, and mark missing rationale rather than inventing it.

Use this note while drafting each section. A template prompt is a question to check against the note, not authority to choose a default, boundary case, failure response, persistence effect, or policy. Keep supported portions and mark unresolved choices with [NEEDS INPUT: ...], linking to Risks & Open Questions when useful. Follow the create workflow's live-user or incomplete-draft handling; missing answers do not invalidate the supported portions.

For review or fact-check, reconstruct the same note within the review scope without changing the document. Distinguish decisions stated only in the target from those corroborated by its sources; an unavailable source is a verification gap, not proof that a decision was invented.

## Decision ownership and semantic deduplication

Assign one canonical owning section to each policy, invariant, numeric limit, decision rule, and exception list. Other sections may project only the consequence needed for their own responsibility; they should not redefine the exact rule or repeat its rationale.

- Primary User Flows own user actions and visible outcomes, not complete policy formulas.
- Design owns system boundaries, conceptual models, and failure mechanisms, not policy rationale or result-state tables.
- Policy Decisions own the exact rule and rationale.
- Cross-cutting Concerns own only the security, privacy, permission, observability, accessibility, or internationalization consequence.
- Scope owns the versioned feature surface, not detailed decision algorithms.
- Result Semantics owns state names, effects, and user visibility, not the policy that selects a state.

Define each exact numeric value, policy, exception, and branch condition once in its owning section. In other sections, state only the context-specific effect and a concise cross-reference; even an identical second definition creates another place that can drift. A flow may describe the user reaching a limit without repeating its value, and a result state may describe its effect without redefining the condition that selects it.

Use the [semantic review procedure](feature-design-doc-validation.md#semantic-review-procedure) to check the actual document after drafting. Preserve each section's unique responsibility and distinguish current definitions from explicitly superseded decisions, exact quotations, and append-only history; deduplication does not authorize erasing those records.
