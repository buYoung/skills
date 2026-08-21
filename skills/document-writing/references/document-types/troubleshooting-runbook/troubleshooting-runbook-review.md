# Reviewing a troubleshooting runbook

## Simulation test

Starting from each documented symptom, an operator should be able to select a safe first check, follow evidence-driven branches, recover or stop, verify the result, and escalate with useful context.

## Findings to surface

- Symptoms or severity are too vague to recognize.
- Mutation occurs before low-risk diagnosis.
- A branch lacks an observable condition.
- Recovery lacks verification or rollback.
- A destructive command has an unresolved or broad target.
- Escalation criteria or ownership is missing.
- Prevention work interrupts active recovery.
- The artifact is actually a normal guide, incident record, or analysis report.

## Quality bar

The runbook should reduce uncertainty and operational risk under pressure, not merely list expert knowledge.
