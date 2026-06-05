# Reviewer Panel

## Lens roster

Two lenses are mandatory for every panel; the rest are selected by what the task plausibly risks. A lens earns its seat only when the deliverable could realistically fail along it — every reviewer is a full read of the artifact.

### Always included

| Lens | What it asks |
|------|--------------|
| **Correctness** | Does the artifact actually work / hold up? Code: does it run, handle the obvious inputs, avoid logic errors? Document or plan: are the claims accurate and the reasoning sound? |
| **Requirements fit** | Did the worker do everything the user asked, exactly as asked — nothing missing, nothing invented? Reads only the `task_request` as the contract. |

### Selected by task type

| Lens | Add when | What it asks |
|------|----------|--------------|
| **Simplicity** | Code, designs | Is anything over-engineered? Could the same outcome ship with less mechanism? Flags speculative abstraction, dead flexibility, unnecessary dependencies. |
| **Security** | Code touching auth, user input, network, secrets, file paths, or shell execution | Injection, secret exposure, unsafe deserialization, path traversal, missing validation at trust boundaries. |
| **Regression risk** | Edits to existing code | Do the changes break callers, shared abstractions, or public contracts? Inspects usage sites, not just the diff. |
| **Clarity** | Documents, user-facing text | Will the intended reader understand it on first pass? Structure, flow, jargon, missing context. |
| **Feasibility** | Plans, designs, proposals | Can this actually be executed as written? Hidden dependencies, missing steps, optimistic estimates, unstated assumptions. |

### Selection guide

- **New code** → Correctness, Requirements fit, Simplicity (+ Security if it touches a trust boundary)
- **Edit to existing code** → Correctness, Requirements fit, Regression risk (+ Security per above)
- **Document** → Correctness, Requirements fit, Clarity
- **Plan / design** → Correctness, Requirements fit, Feasibility (+ Simplicity if the design is structural)
- **Mixed deliverable** → pick per the dominant artifact; cap at 4 lenses total

When in doubt between two optional lenses, pick the one whose failure the user would notice later and blame the result for.

When a lens's "add when" condition matches the task but you exclude it anyway (e.g., a CLI takes user-supplied file paths but it is a local single-user tool, so Security feels like overkill), record the reason in one line alongside the panel announcement. The exclusion stays your call — but an unrecorded exclusion is indistinguishable from an overlooked one, both to the user and to anyone auditing the run later.

## Reviewer prompt template

Spawn one reviewer per lens, all in the same turn. Each prompt contains exactly the blocks below — never the scout's notes, the worker's reasoning, other reviewers' lenses or findings, or prior-round results. The reviewer must form its opinion from the request and the artifact alone; anything else anchors it. Per [session_protocol.md](session_protocol.md), insert **paths only** — the reviewer reads the files itself.

```
You are an independent reviewer. You did not write this artifact and you must
not edit it. Your only job is to critique it through one lens and report back.

## Inputs (read these files yourself)
- Task request (the contract): {{TASK_REQUEST_PATH}}
- Artifact under review: {{ARTIFACT_PATHS}}

You have read-only tool access — read the actual files and any
directly-related code or material needed to verify a specific concern. Do not
wander beyond what a finding requires.

## Your lens: {{LENS_NAME}}
{{LENS_QUESTION}}

Review ONLY through this lens. Findings outside your lens are someone else's
job — do not report them.

## Rules
- Every finding needs concrete evidence: a quoted line, a file:line reference,
  or a reproducible observation. A hunch without evidence is not a finding.
- Classify each finding:
  - blocker — the artifact fails the task request or is broken
  - major — works, but a real problem the user would want fixed before accepting
  - minor — worth knowing, not worth another round
- Never edit files. Never write the final response. Report findings only.
- If you find nothing through your lens, say so plainly — do not invent
  findings to look thorough.

## Report
Write your review to: {{SESSION_DIR}}/reviews/{{LENS}}_{{ROUND}}.md
For each finding:
- severity: blocker | major | minor
- problem: one or two sentences
- evidence: quote or file:line
- suggestion: (optional) one sentence on the fix direction

End the file with: PASS (no blocker/major findings) or FAIL (at least one).
Your final message to the orchestrator is just the report path plus the
PASS/FAIL verdict.
```

## Focused re-check prompt (round 2+)

Re-reviews check resolution, not rediscovery — a full re-read every round triples the cost for little gain. Append this block to the same reviewer prompt, replacing the full review instruction:

```
## Focused re-check
This is a re-review. Your previous review of this artifact is at:
{{OWN_PREVIOUS_REVIEW_PATH}}
Read it yourself, then:

1. For each item you previously flagged: verify in the updated artifact
   whether it is resolved. Report resolved / not resolved, with evidence.
2. Quick scan ONLY the changed portions for newly-introduced problems through
   your lens. Do not re-litigate parts you already passed.
```

Note this is the one sanctioned exception in the read-access matrix: a reviewer may read *its own* previous review file in focused mode, because checking resolution requires knowing what was flagged. It still never sees another lens's file or any worker/scout document.
