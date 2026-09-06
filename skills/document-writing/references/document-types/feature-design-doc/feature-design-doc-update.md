# Updating a Feature Design Doc

Read the canonical FDD, current implementation or supplied decision changes, section responsibilities, implementation-leakage rules, and validation instructions.

FDD updates are append-oriented: current facts change in place, but decision history is not erased.

## Update sequence

1. Confirm the existing file is the canonical FDD for the feature.
2. Identify changed behavior, policies, scope, result states, platform constraints, risks, or decisions. Build the [internal decision note](feature-design-doc-section-responsibilities.md#internal-decision-note-before-drafting), separating retained decisions, supported changes, and unresolved choices with evidence and owners.
3. Compare the document with current implementation when implementation is in scope.
4. Update factual sections in place, defining each changed exact rule once at its owner and updating dependent effects and references without inventing missing behavior.
5. Preserve decision history.
6. Append Revision History.
7. Record verification scope and update metadata according to the validation reference.
8. Validate and update the index.

## Factual sections

Update current truth in sections such as Design, Primary User Flows, Scope, Result Semantics, and Platform Design.

## Decision sections

Do not delete or silently rewrite prior Policy Decisions or Alternatives Considered. Mark a replaced decision as superseded with the date and a pointer to Revision History, then add the new decision.

Record known document-versus-implementation deviations that remain unresolved.

## Metadata and index

Apply [feature-design-doc-validation.md](feature-design-doc-validation.md) for status and verification metadata. A partial update records its checks and unchecked remainder in Revision History without advancing the previous whole-document `last-verified` or `verified-against`. Refresh those fields only after a whole-document check. Update tags, related paths, status, and the index entry only when their meaning changed.

## Final verification

Run the structural validator, then the [semantic review procedure](feature-design-doc-validation.md#semantic-review-procedure) against the actual revision, original FDD, supplied changes, and decision note. Keep corrections within the requested change and its dependencies; report unrelated gaps. Check that the update did not convert the FDD into a changelog, task plan, or code walkthrough.
