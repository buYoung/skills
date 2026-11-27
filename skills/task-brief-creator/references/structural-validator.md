# Structural Validator Scope

`scripts/validate_brief.py` is a stand-alone Python 3 script (no external deps) that verifies structural conformity of a saved brief.
It runs as step 5 of Stage 5 (save + validate) but can also be run ad-hoc against any existing brief.
`SKILL.md` gives the commands and exit codes; this file lists what the validator checks and what stays on content review.
For the briefset parent validator, see the Validator Scope section in `briefset.md`.

## What `validate_brief.py` Checks

The checks are deliberately structural only:

- Filename pattern, exactly one H1 title outside fenced code, title format, type coherence across filename / title / section value, and slug length.
- Presence and template order of all nine required H2 sections + exactly one `In Scope` then `Out of Scope` H3; duplicate H2 sections are rejected. Fenced examples do not establish sections or checklist items.
- `[confirmed]` / `[inferred]` prefixes in `Current State (As-Is)`, unique consecutive execution-stage headings with required fields, and structured non-blocking `Open Questions` shape.
- Type-conditional section (`Reproduction` / `Baseline Measurement` / `Behavior Contract`) present and populated for the matching type; `- N/A — <reason>` cannot be mixed with other bullets.
- Top-level bullet content in narrative sections; top-level `- [ ]` items in checklist sections; populated `Open Questions` with `- None — <reason>` when no questions remain.
- `Related Files / Entry Points` validates file tokens before the first prose-separating em dash outside inline code. At least one existing file/directory or adjacent `(proposed)` path is required. Root files, including dotfiles, resolve on disk. URLs and ``- Route: `/path` — <purpose>`` entries are supplementary and do not satisfy the file-entry requirement. Descriptive inline code after the separator is not checked as a file.
- Optional `--repo-root` lets isolated brief artifacts validate their entry points against the actual target checkout.
- Optional `Constraints` heading shape.
- Every top-level `Out of Scope` exclusion needs `[hard]` or `[deferred]`; a sole `- None — <reason>` means no exclusions. Missing labels fail. Other warnings also make validation fail; semantic correctness remains a content-review responsibility.

## What Stays on Content Review

Whether evidence labels are truthful, stage outcomes and handoffs are executable, Out-of-Scope entries are real guardrails vs. filler, entry points are *good*, Acceptance Criteria are measurable, and the type-conditional section's content is sufficient.
