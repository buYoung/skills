# FDD validation

The structural validator lives at scripts/validate_fdd.py inside the installed document-writing skill package.

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

A structural pass is not a semantic pass. Never report the FDD as fully verified when only the script ran.
