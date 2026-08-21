# Authoring an action guide

## Required context

Identify the target outcome, starting state, reader permissions, environment, required tools, and supported versions.

## Drafting sequence

1. State what the reader will have when finished.
2. List only prerequisites that must be satisfied before step one.
3. Write the shortest safe path to the outcome.
4. Put setup before actions that depend on it.
5. Add expected results at checkpoints where failure could otherwise go unnoticed.
6. Add a final end-to-end verification.
7. Add local troubleshooting only for likely failures.

## Command and UI guidance

- Preserve exact commands, paths, identifiers, labels, and values.
- Treat a prose action as a requirement, not as an exact command. Do not present derived command syntax as source-confirmed unless the command and target environment are supplied or verified. When the user prohibits unverified commands, keep an unverified action in prose and omit derived syntax.
- Explain placeholders before the command that uses them.
- Separate commands that run in different directories or environments.
- Warn before destructive, irreversible, or service-disrupting actions.
- Offer rollback when a step changes durable state and rollback is practical.

## Avoid

- Conceptual essays between steps
- Hidden prerequisites
- Steps that say only "configure as needed"
- Success claims without an observable check
- Several alternative paths without identifying the default
