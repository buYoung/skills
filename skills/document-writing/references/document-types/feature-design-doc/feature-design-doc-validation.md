# FDD validation

The structural validator lives at scripts/validate_fdd.py inside the installed document-writing skill package.

## Status and verification metadata

Keep design authority separate from implementation verification. A pre-implementation FDD may be the active design source without claiming that code implements it. Use the existing frontmatter keys:

| Key | Meaning and allowed representation |
| --- | --- |
| `status` | `draft` while blocking design decisions remain unresolved or authority is not established; `active` when the user or an authoritative source establishes it as the current design decision source; `superseded` when another decision source replaces it. Authoring alone does not activate a draft. |
| `created` | The actual creation date; preserve it on updates. |
| `last-verified` | Date of the most recent whole-document check against the declared basis, or `unverified` when no such check has occurred. Writing, formatting, or running the structural validator alone does not advance it. |
| `verified-against` | The exact commit checked for implementation conformance; `not-applicable-pre-implementation` when only a pre-implementation design source was reviewed; `unverified` when implementation conformance is relevant but unchecked. Do not substitute the current HEAD for a commit actually checked. |

In the opening or Document Intent, identify the decision authority, reviewed source and version or date when known, and verification scope. For a compact profile without Document Intent, use the opening. State whether the check covered design-source consistency, implementation conformance, or both. A design with blocking decisions remains a draft even if its structure passes validation; an active FDD may retain explicitly accepted open questions.

For a partial update, preserve the previous whole-document verification metadata. Append the changed sections, actual check date, sources or commit checked, and unchecked remainder in Revision History, and disclose that scope in the completion report. If the change makes the previous verification basis misleading, mark the affected claims as pending verification. Advance whole-document metadata only after a whole-document check; a normalization-only change does not imply renewed factual verification.

Existing `active` and `superseded` values remain valid. Do not require a new approval merely to restate an already authoritative decision. The structural validator does not validate lifecycle authority, these sentinel meanings, or verification coverage; those are part of the model review below.

## Commands

Run the validator against the canonical FDD path. Use JSON output for machine consumption and strict mode when major findings should fail verification.

The validator has three exit classes:

- 0: clean at the selected threshold
- 1: findings at or above the threshold
- 2: invocation or file error

## Structural responsibility

The validator checks:

- Required frontmatter and profile values
- Required numbered sections for full and compact profiles
- Empty required sections
- Heading title drift and section order
- Duplicate or misplaced numbered headings
- Cross-cutting concern coverage
- Code-fence-aware heading parsing

It reports optional numbered sections without deciding whether their semantic trigger applies.

## Model responsibility

After structural validation, review:

- Section responsibility placement
- Implementation leakage
- Factual accuracy against the codebase
- Whether optional sections are semantically required
- Whether alternatives and policy decisions are evidence-backed
- Whether update history is preserved
- Whether lifecycle status, decision authority, verification basis, and reported coverage match the evidence, including pre-implementation and partial-update cases

A structural pass is not a semantic pass. Never report the FDD as fully verified when only the script ran.
