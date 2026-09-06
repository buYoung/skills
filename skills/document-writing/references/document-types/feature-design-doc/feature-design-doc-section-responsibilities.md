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

When a statement appears to fit two sections, assign its definition to one owner and tailor any summary elsewhere to that section's responsibility.

## Internal decision note before drafting

Before writing or changing FDD prose, make a short internal working note from the supplied inputs and relevant evidence. For an existing FDD, include its retained decisions and distinguish them from authorized changes. The note is working context, not an additional user deliverable or a required file.

For each material decision, record its meaning, supporting source or passage, authority or unresolved status, and one canonical owning section from the map above. For a policy, record the source-authorized applicability conditions together with the response they govern, so reuse preserves both. Distinguish:

- Supplied or verified decisions: supported by an authoritative input or checked evidence, including faithful restatements.
- Necessary consequences: behavior that follows from the inputs without selecting an additional product choice.
- Explanatory inferences: plausible effects that help explain the design; qualify them as inferences rather than approved policy or the historical reason for a decision.
- Unresolved choices or proposals: behavior the inputs leave open, including conflicts; absence of a rule does not establish its opposite.

For a proposed behavioral claim, ask whether materially different behaviors could satisfy the same inputs. If they could and the claim mandates one, it introduces an unresolved product choice unless supplied or verified authority selects it. Restatement and necessary implications are allowed; plausibility alone is not authority. Record decision rationale only when supported, and mark missing rationale rather than inventing it. Consider only the alternatives needed to make this distinction, not an exhaustive design search; this classification requires no separate file, user deliverable, or additional model call.

Use this note while drafting each section. A template prompt is a question to check against the note, not authority to choose a default, boundary case, failure response, persistence effect, or policy. Keep supported portions and mark material unresolved choices within the actual requested scope with [NEEDS INPUT: ...], linking to Risks & Open Questions when useful. Omit hypothetical cases outside that scope rather than turning them into new required questions. Follow the create workflow's live-user or incomplete-draft handling; missing answers do not invalidate the supported portions.

For review or fact-check, reconstruct the same note within the review scope without changing the document. Distinguish decisions stated only in the target from those corroborated by its sources; an unavailable source is a verification gap, not proof that a decision was invented.

## Decision ownership and semantic deduplication

Assign one canonical owning section to each policy, invariant, numeric limit, decision rule, and exception list. Keep the authoritative definition and supported decision rationale there. Other sections may give concise summaries, context-specific effects, and user outcomes, clearly linked to the owning definition and without adding behavior or exceptions.

A policy owner owns its source-authorized applicability conditions and response together. In behavior, failure handling, flows, results, or other consuming sections, preserve those conditions explicitly or through a clear reference; broadening, narrowing, or omitting them must not redefine where the policy applies. A section may describe only its stated local context or sub-flow while linking to the owner, without restating the policy's full scope. A concept definition may cover more cases than a policy: reusing that definition does not authorize applying the policy to every case it includes. Changing policy scope requires a separate request or an evidence-backed decision, not an explanatory paraphrase.

- Primary User Flows own user actions and visible outcomes, not complete policy formulas.
- Design owns system boundaries, conceptual models, and failure mechanisms, not policy rationale or result-state tables.
- Policy Decisions own the exact rule and rationale.
- Cross-cutting Concerns own only the security, privacy, permission, observability, accessibility, or internationalization consequence.
- Scope owns the versioned feature surface, not detailed decision algorithms.
- Result Semantics owns state names, effects, and user visibility, not the policy that selects a state.

Single ownership does not mean a word or numeric value may appear only once. Flag a passage when it restates the full values, conditions, exceptions, or decision formula as an independent rule definition, or diverges from the owner. Judge its meaning and role, not occurrence counts. A flow may summarize a limit with its value and describe the user's outcome while clearly referring to the owning policy; it should not reproduce the complete policy as another authority.

Use the [semantic review procedure](feature-design-doc-validation.md#semantic-review-procedure) to check the actual document after drafting. Preserve each section's unique responsibility and distinguish current definitions from explicitly superseded decisions, exact quotations, and append-only history; deduplication does not authorize erasing those records.
