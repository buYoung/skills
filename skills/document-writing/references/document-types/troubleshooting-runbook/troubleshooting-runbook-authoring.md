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
- Preserve exact supplied commands, paths, identifiers, and values. Do not present derived command syntax as source-confirmed unless the command and target environment are supplied or verified. When the user prohibits unverified commands, describe the check or action in prose and omit derived syntax, but still name the supplied target, such as a container, file, or log line, and the observable state that confirms the result.
- Do not promise recovery without a verification step.
- When recovery requires waiting, polling, or retrying, preserve verified waiting limits, retry bounds, and stop or escalation criteria. If a material bound is unknown, mark it unresolved and direct the operator to the escalation owner before repeating an unbounded action; do not invent a duration or retry count.

## Avoid

- A flat list of possible causes
- "Restart everything" as the default
- Diagnostic branches based on guesses
- Escalation instructions that omit the evidence responders need
