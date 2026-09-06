# Normalizing a Feature Design Doc

Normalize when the artifact is intended to be an FDD but mixes design decisions with implementation actions or places content under the wrong section.

Read the canonical template, section responsibilities, implementation-leakage rules, validation instructions, and shared existing-document reference.

## Workflow

1. Confirm the artifact is genuinely an FDD.
2. Build the [internal decision note](feature-design-doc-section-responsibilities.md#internal-decision-note-before-drafting) from the original and supplied sources, mapping each statement to its design responsibility and preserving unresolved status.
3. Move design content into the correct FDD section. Consolidate current authoritative definitions at their owner and retain concise linked summaries and contextual effects elsewhere under the section-responsibility rules; do not resolve missing behavior to fill the template.
4. Remove implementation actions from the FDD while reporting where they belong.
5. Preserve decisions and history.
6. Report material movements.
7. Run structural validation, then the [semantic review procedure](feature-design-doc-validation.md#semantic-review-procedure) against the actual result, original, inputs, and note. Check preservation of decisions as well as unsupported additions and repeated definitions within the authorized scope.

Preserve lifecycle status and factual verification metadata unless the work also establishes a new design authority or performs a factual check. Record normalization and its actual scope in Revision History according to [feature-design-doc-validation.md](feature-design-doc-validation.md); structural conformance alone does not renew factual verification.

Do not silently delete useful implementation content. Identify it as belonging in an implementation plan or other downstream artifact.

Normalization edits a decision record. Do not overwrite the original in place without authorization when the request is review-only or the canonical ownership is unclear.
