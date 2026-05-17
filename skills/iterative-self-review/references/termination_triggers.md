# Termination Triggers

Three categories, nine triggers. Evaluate in priority order each iteration; the first trigger that fires ends or pauses the loop.

User clarification is **not** a termination trigger. It is a Phase B routing branch handled in `routing_rules.md`. If the current iteration accepted any non-minor fix, defer the user question until a new verification round confirms those fixes.

There is no hard iteration cap. The loop continues until every non-minor item is resolved, unless a defensive or convergence trigger proves the loop cannot currently make progress.

## Priority order

Evaluated in Step 6 of every iteration:

1. **Regression** (Defensive)
2. **Verifier invalid report** (Defensive)
3. **Sub-agent invocation failure** (Defensive)
4. **Oscillation** (Convergence)
5. **Stable findings** (Convergence)
6. **No-progress safeguard** (Convergence)
7. **Clean pass** (Positive)
8. **Severity floor** (Positive)
9. **No-op iteration** (Convergence)

Defensive triggers come first because rollback or failure reporting must outrank optimism. Convergence triggers that prove the loop cannot productively improve come before positive triggers so a stalled loop is not presented as success. There is intentionally no `hard_cap`: non-minor findings are retried until fixed, clarified, hedged, or blocked by a convergence/defensive trigger.

## Defensive triggers

### 1. Regression
- **Definition**: This iteration's response has more blocker- or major-severity issues than the previous valid iteration.
- **Detection**: Deterministic count.
- **Action**: Stop. Discard the current response and adopt the previous valid iteration's response as final. Surface the regression in metadata.

### 2. Verifier invalid report
- **Definition**: The sub-agent's report violates `report_format.md` enforcement for two consecutive attempts after re-call. Invalid examples include missing `artifact_inspections`, missing `skipped_artifacts`, missing direct-quote evidence, missing uncertainty fields, `verdict: clean` with non-empty findings, or `verdict: issues_found` with no reportable items.
- **Detection**: Deterministic schema and cross-field check against `report_format.md`.
- **Action**: Stop. Adopt the last iteration whose report was valid. If no prior valid iteration exists, adopt the current draft and surface the verifier failure in metadata.
- **Rationale**: Without a valid verifier report, no positive trigger can be trusted.

### 3. Sub-agent invocation failure

Sub-agent call failures are classified before they affect iteration state.

#### Transient / environmental failures

Retry with the byte-identical prompt for the same round, up to three attempts:

- Agent thread limit or capacity error.
- Rate limit.
- Network reset, gateway timeout, or 5xx provider/API failure.
- Spawn failure whose message indicates environment rather than malformed input.

If all three attempts fail, convert to `sub_agent_failure`, stop, and surface the retry log.

#### Permanent / content-driven failures

Stop the current round and surface `sub_agent_failure` without guessing or self-recovering:

- Empty response.
- Truncated response.
- Schema violation that persists after the allowed invalid-report re-call path.
- Banned tool attempt.
- Severity/count mismatch or other cross-field mismatch.
- Report with no inspection scope when inspectable artifacts were cited.

## Convergence triggers

### 4. Oscillation
- **Definition**: A semantic issue is accepted in one iteration and rejected, or rejected then accepted, in another iteration of the same loop. A single flip is sufficient. Uses the rejection log defined in `routing_rules.md`.
- **Detection**: The same semantic issue appears with opposing accept/reject decisions across any two iterations.
- **Action**: Stop. Adopt the response from the iteration where the main agent last rejected the oscillating finding, then surface the oscillation.

### 5. Stable findings
- **Definition**: The issues set is semantically identical to the previous iteration's.
- **Detection**: A separate sub-agent (equivalence judge) is asked, "Are these two issue sets semantically equivalent?" — yes/no only. No similarity scores or numeric thresholds. If ambiguous, treat as "not equivalent" and continue.
- **Action**: Stop. Further iterations would only reproduce the same findings.

### 6. No-progress safeguard
- **Definition**: For two consecutive iterations, at least one accepted non-minor fix was applied, but the total `blocker + major` count did not decrease.
- **Detection**: Deterministic count across valid iterations.
- **Action**: Pause the loop and report the stall to the user. The fix may not address the root cause, or the finding may require user intent that has not been supplied.
- **Rationale**: This replaces a hard cap without allowing silent infinite churn.

## Positive triggers

**Gating precondition for every positive trigger:** The Step 5.5 routing-completion gate in `routing_rules.md` must have passed for the current iteration, and there must be no pending Phase B user-decision item. If the gate has not passed or a user decision is still pending, no positive trigger may fire.

**Verdict handling:** `clean_pass` requires `verdict: clean`. `severity_floor` may evaluate a report with `verdict: issues_found`, but only after routing has resolved, downgraded, rejected, or completed user decisions for every non-minor issue.

### 7. Clean pass
- **Definition**: Sub-agent report has `verdict: clean`, `issues=[]`, `missing=[]`, `unverified_assertions=[]`, a complete `artifact_inspections` manifest, present `skipped_artifacts`, and the Step 5.5 routing-completion gate passed.
- **Action**: Stop. Adopt the current response.

### 8. Severity floor
- **Definition**: All remaining findings are `minor`, all non-minor findings are resolved or rejected with logged reasons, all Phase B user decisions are completed, and the Step 5.5 routing-completion gate passed.
- **Action**: Stop. Adopt the current response and surface residual minor items only when useful.

## Post-positive convergence

### 9. No-op iteration
- **Definition**: Routing produced zero accepted items this iteration, no Phase B user-decision item remains, and no positive trigger fired.
- **Action**: Stop. Adopt the current response and surface why the loop stopped.
- **Distinction from Stable findings**: Stable = same issue set across iterations (sub-agent output signal); no-op = zero accepted items this iteration (main-agent routing signal).

## Equivalence-judge sub-agent call (for Stable findings)

When the main agent needs to evaluate trigger #5, invoke a separate sub-agent with the two issue sets and the following constraints:

- Inputs: only the two YAML issue sets (current iteration and previous iteration). No reasoning, no draft, no prior verdicts.
- Question (verbatim): *"Are these two issue sets semantically equivalent? Answer `yes` or `no` only. If uncertain, answer `no`."*
- Output: a single token — `yes` or `no`.
- Forbidden: numeric scores, similarity ratios, partial answers, explanations, or any other text.

This sub-agent is distinct from the verification sub-agent and exists to keep equivalence judgments independent of the main agent's self-bias.

## Final response metadata schema

Append to the final response:

```yaml
termination:
  trigger: clean_pass | severity_floor | regression | verifier_invalid_report | sub_agent_failure | oscillation | stable_findings | no_progress | no_op
  iterations: <count>
  residual_issues:
    - severity: minor
      problem: <one-line description>
  rejected_findings:
    - problem: <one-line description>
      reason: scope_creep | redundant | factually_wrong | weak_evidence
  user_decisions:
    - question: <asked>
      answer: <user's answer>
  failure_log:
    - type: transient | permanent
      cause: <one-line description>
      attempt: <number>
```

The trigger name identifies the category via the priority table above. Surface `regression`, `verifier_invalid_report`, `sub_agent_failure`, `oscillation`, `stable_findings`, `no_progress`, and `no_op` to the user; do not hide them behind a normal-looking response. Only `clean_pass` and `severity_floor` represent successful termination.

Use empty arrays for unused metadata fields.

## Continue conditions

All must hold to proceed to the next iteration:

- No defensive trigger has fired.
- No convergence trigger has proven the loop is stalled.
- The Step 5.5 routing-completion gate has either produced at least one accepted item to integrate or identified a Phase B user-decision item.
- If an accepted non-minor item was integrated, the next round is mandatory before surfacing Phase B items.
