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

After structural validation, execute the procedure below. Its review scope includes:

- Section responsibility placement
- Implementation leakage
- Factual accuracy against the codebase
- Whether optional sections are semantically required
- Whether alternatives and policy decisions are evidence-backed
- Whether update history is preserved
- Whether lifecycle status, decision authority, verification basis, and reported coverage match the evidence, including pre-implementation and partial-update cases

A structural pass is not a semantic pass. Never report the FDD as fully verified when only the script ran.

## Semantic review procedure

Run this as a distinct pass after drafting or editing, and during review or fact-check. Use the actual resulting document, authoritative inputs, and the [internal decision note](feature-design-doc-section-responsibilities.md#internal-decision-note-before-drafting), not memory of the writing plan. If a file was saved, read its current contents before comparing them; for a conversation-only draft, inspect the complete proposed Markdown.

1. Establish the authorized check scope and evidence basis. Reconstruct the note if none exists. For a focused update or review, inspect changed sections and the owners and dependent references needed to assess their effects; do not turn this into an unrelated whole-document rewrite.
2. Compare material claims in that text with the inputs and note. Pay particular attention to exact values, positive and negative policies, preconditions, exception branches, failure outcomes, and state changes. Identify statements that gained certainty or introduced a choice without support. Check in the reverse direction that supplied decisions were not lost or weakened. Do not use the new draft itself as evidence for its additions.
3. Trace every current exact rule in scope to its one owning section and inspect other occurrences, including paraphrases. Retain the definition and supported rationale at the owner; elsewhere retain only the section-specific effect and a reference. Check that consolidation preserves meaning and references resolve. Preserve historical and protected exact text under the section-responsibility rules.
4. Apply the remaining model-responsibility checks above, including implementation leakage and metadata coverage. In authoring modes, correct unsupported additions introduced by the work and duplicate current definitions within scope, leaving true choices explicitly open. For pre-existing conflicting or unverified decisions, report the gap and preserve their authority/history unless the request and evidence authorize changing them. In review-only modes, report findings and proposed corrections without writing any files or metadata.
5. Re-read corrected passages with their owners and dependent references to confirm the identified issues were addressed without losing supported decisions. If edits changed structural elements, rerun the structural validator. Report structural results separately from the semantic comparison actually performed, its sources and scope, and remaining open questions; do not claim either check from the other.

This pass requires an actual comparison, not another checklist declaration. It does not require a separate review file, a new tool, or a sub-agent. Apply the existing incomplete-draft and metadata contracts when input or verification is unavailable; a semantic pass alone does not establish implementation conformance.
