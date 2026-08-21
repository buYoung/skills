# Normalizing a Feature Design Doc

Normalize when the artifact is intended to be an FDD but mixes design decisions with implementation actions or places content under the wrong section.

Read the canonical template, section responsibilities, implementation-leakage rules, validation instructions, and shared existing-document reference.

## Workflow

1. Confirm the artifact is genuinely an FDD.
2. Map each statement to its design responsibility.
3. Move design content into the correct FDD section.
4. Remove implementation actions from the FDD while reporting where they belong.
5. Preserve decisions and history.
6. Report material movements.
7. Validate the normalized document.

Do not silently delete useful implementation content. Identify it as belonging in an implementation plan or other downstream artifact.

Normalization edits a decision record. Do not overwrite the original in place without authorization when the request is review-only or the canonical ownership is unclear.
