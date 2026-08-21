# Authoring a troubleshooting runbook

## Required context

Identify the system, supported environment, symptoms, impact, observability sources, likely causes, safe checks, recovery actions, rollback, and escalation owner.

## Drafting sequence

1. Define recognizable symptoms and severity.
2. Put immediate safety or containment before diagnosis.
3. Order checks by low risk, low cost, and high diagnostic value.
4. Branch only on observable evidence.
5. Pair each diagnosed condition with a bounded recovery action.
6. Verify service and user-visible recovery.
7. Define rollback before high-risk changes.
8. Define when to stop and escalate, including evidence to attach.
9. Separate post-incident prevention from active recovery.

## Safety rules

- Never overwrite existing cancellation, maintenance, or caller safety controls.
- Warn before destructive, irreversible, or service-disrupting actions.
- Prefer read-only checks before mutations.
- Avoid commands with unresolved targets or broad globs.
- Do not promise recovery without a verification step.

## Avoid

- A flat list of possible causes
- "Restart everything" as the default
- Diagnostic branches based on guesses
- Escalation instructions that omit the evidence responders need
