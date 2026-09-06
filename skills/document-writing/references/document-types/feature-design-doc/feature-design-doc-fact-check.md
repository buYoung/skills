# Fact-checking a Feature Design Doc

Fact-check both structural conformance and external truth. A well-structured FDD that contradicts the product or implementation is more dangerous than a visibly incomplete draft.

Read the validation instructions, canonical template, section responsibilities, implementation-leakage rules, shared source-grounding reference, and shared existing-document reference.

## 1. Establish the structural baseline

Run the FDD validator. Treat its findings as the structural baseline rather than duplicating them manually.

## 2. Review semantic placement

Execute the [semantic review procedure](feature-design-doc-validation.md#semantic-review-procedure) in read-only mode, using the source checks in step 3 as evidence. Reconstruct the internal decision note for the reviewed scope, compare actual claims with available authority, and identify unsupported certainty and repeated exact definitions. Report missing evidence as a verification gap rather than assuming invention.

Check that:

- Feature identity, non-goals, version scope, policies, alternatives, and result states occupy their assigned sections.
- Cross-cutting concerns contain supported answers, explicit unresolved questions, or reasoned non-applicability; unknown applicability has not been presented as non-applicability.
- Alternatives are traceable rather than invented.
- Implementation actions have not leaked into design sections.

## 3. Verify external truth selectively

Use repository evidence for current concepts, related features, behavior, conceptual models, configuration, policies, result states, and platform support.

First apply the status and verification metadata rules in the validation reference. For a pre-implementation FDD, check consistency with the authoritative design inputs and distinguish planned behavior from implemented behavior; do not treat the absence of an implementation as a defect or imply a commit was verified. For a scoped review, report exactly which sections and sources were checked and what remains unchecked. Review remains read-only, including verification metadata.

Use primary external sources only for relevant standards, protocols, regulations, formats, security requirements, or platform APIs.

Do not waste verification effort on narrative problem framing that only reflects product intent.

## 4. Cite findings

For repository findings, cite the path and line. For external findings, link the authoritative source and identify the supporting claim. When the document and implementation disagree, cite both.

## 5. Report

Group findings from highest to lowest severity:

- Critical: likely to cause incorrect implementation or regression
- Major: a material design decision, policy, required section, or external requirement is missing or wrong
- Minor: wording, placement, or template consistency reduces reliability without changing core behavior

For each finding, state the section, problem, evidence, and correction. Do not modify the FDD unless the user also asks for a change.
