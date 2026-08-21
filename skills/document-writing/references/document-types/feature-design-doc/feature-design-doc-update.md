# Updating a Feature Design Doc

Read the canonical FDD, current implementation or supplied decision changes, section responsibilities, implementation-leakage rules, and validation instructions.

FDD updates are append-oriented: current facts change in place, but decision history is not erased.

## Update sequence

1. Confirm the existing file is the canonical FDD for the feature.
2. Identify changed behavior, policies, scope, result states, platform constraints, risks, or decisions.
3. Compare the document with current implementation when implementation is in scope.
4. Update factual sections in place.
5. Preserve decision history.
6. Append Revision History.
7. Refresh verification metadata.
8. Validate and update the index.

## Factual sections

Update current truth in sections such as Design, Primary User Flows, Scope, Result Semantics, and Platform Design.

## Decision sections

Do not delete or silently rewrite prior Policy Decisions or Alternatives Considered. Mark a replaced decision as superseded with the date and a pointer to Revision History, then add the new decision.

Record known document-versus-implementation deviations that remain unresolved.

## Metadata and index

Refresh last-verified and verified-against. Update tags, related paths, status, and the index entry only when their meaning changed.

## Final verification

Run the structural validator and semantic sweeps. Check that the update did not convert the FDD into a changelog, task plan, or code walkthrough.
