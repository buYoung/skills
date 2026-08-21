# Reviewing an action guide

## Walkthrough test

Review the guide as a reader who has the stated prerequisites but no author context. Check whether every input, location, and transition is available when needed.

## Findings to surface

- The promised outcome is unclear.
- A prerequisite appears after the step that needs it.
- A command uses an unexplained placeholder.
- A step lacks an expected result where silent failure is possible.
- The final verification checks only an intermediate state.
- A destructive action lacks a warning or rollback.
- Troubleshooting dominates enough that the artifact should be a runbook.
- Version or environment assumptions are unstated.

## Quality bar

A capable reader should be able to follow the default path without guessing and know whether the task actually succeeded.
