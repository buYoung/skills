# Termination Triggers

Four categories, nine triggers. Evaluate in priority order each iteration; the first trigger that fires ends the loop.

## Priority order

Evaluated in Step 6 of every iteration:

1. **Regression** (Defensive)
2. **Oscillation** (Convergence)
3. **Stable findings** (Convergence)
4. **Clean pass** (Positive)
5. **Severity floor** (Positive)
6. **No-op iteration** (Convergence)
7. **Diminishing returns** (Convergence)
8. **User clarification needed** (User-clarification)
9. **Hard cap** (Fallback)

Regression is first because rollback must outrank any optimistic "one more pass might help" instinct. Convergence triggers come next because a non-progressing loop cannot be salvaged by continuing. Hard cap is last because it is a fallback, not a preferred outcome.

## Defensive triggers

### 1. Regression
- **Definition**: This iteration's response has *more* blocker- or major-severity issues than the previous iteration.
- **Detection**: Deterministic count.
- **Action**: Stop. Discard the current response and adopt the previous iteration's response as final.

## Convergence triggers (loop end when iteration cannot productively improve)

### 2. Oscillation
- **Definition**: The same issue is being accepted → rejected → accepted (or vice versa) across iterations. Uses the rejection log defined in `routing_rules.md`.
- **Detection**: The same semantic issue appears in 3+ iterations with alternating accept/reject decisions.
- **Action**: Stop. Adopt the response from the iteration where the main agent last rejected the oscillating finding.

### 3. Stable findings
- **Definition**: The issues set is *semantically identical* to the previous iteration's.
- **Detection**: A separate LLM judge is asked, "Are these two issue sets semantically equivalent?" — yes/no only. **No similarity scores.** If ambiguous, treat as "not equivalent" and continue.
- **Action**: Stop. Further iterations would only reproduce the same findings.

## Positive triggers (normal termination)

### 4. Clean pass
- **Definition**: Sub-agent report has `verdict: clean`, `issues=[]`, `missing=[]`.
- **Action**: Stop. Adopt the current response.

### 5. Severity floor
- **Definition**: All remaining issues are `minor`, and main-agent routing downgraded or rejected all of them.
- **Action**: Stop. Adopt the current response.

### 6. No-op iteration
- **Definition**: Routing produced **zero** accepted items this iteration (everything rejected or downgraded).
- **Action**: Stop. Adopt the current response.
- **Distinction from Stable findings**: Stable = same issue set across iterations; No-op = zero accepted items this iteration regardless of whether the set changed.

### 7. Diminishing returns
- **Definition**: For two consecutive iterations, the count of accepted items is ≤ 1.
- **Detection**: Deterministic count from the routing log.
- **Action**: Stop. Adopt the current response.

### 8. User clarification needed
- **Definition**: Routing produced at least one item with `source_of_uncertainty: user_input_ambiguity` and `affects_direction: true`.
- **Action**: Pause the loop, ask the user (batch multiple questions), resume from Step 1 with their answer. The iteration counter is **not reset**. The final metadata records this as `user_clarified`.

## Fallback

### 9. Hard cap
- **Definition**: Iteration count reaches **8** (default).
- **Action**: Stop. Adopt the current response. Metadata classified as `hard_cap`.
- **Override**: Increase only when the user explicitly asks for a deeper loop and the task value justifies it.

## Final response metadata schema

Append to the final response:

```yaml
termination:
  trigger: clean_pass | severity_floor | user_clarified | regression | oscillation | stable_findings | no_op | diminishing_returns | hard_cap
  iterations: <count>
  classification: normal | defensive | hard_cap
  residual_issues:
    - severity: minor
      problem: <one-line description>
  rejected_findings:
    - problem: <one-line description>
      reason: scope_creep | redundant | factually_wrong | weak_evidence
  user_clarifications:
    - question: <asked>
      answer: <user's answer>
```

Use empty arrays for unused fields.

### Classification mapping

| Trigger | Classification |
|---------|----------------|
| `clean_pass` | normal |
| `severity_floor` | normal |
| `user_clarified` | normal |
| `regression` | defensive |
| `oscillation` | defensive |
| `stable_findings` | defensive |
| `no_op` | defensive |
| `diminishing_returns` | defensive |
| `hard_cap` | hard_cap |

Only `normal` means "successful termination". `defensive` and `hard_cap` signal "automatic improvement has stalled" — the main agent must surface this to the user, not hide it.

## Stable-findings equivalence (re-emphasized)

- Show the two issue sets to a separate LLM judge and accept a **yes/no** answer only.
- No similarity thresholds, no text-match ratios, no numeric comparisons.
- If the judge is uncertain, treat as "not equivalent" and continue iterating.

## Continue conditions

All must hold to proceed to the next iteration:

- No trigger from the nine above has fired (Regression always ends the loop with rollback).
- The issues set changed semantically since the previous iteration (no Stable findings).
- Routing produced at least one accepted item (no No-op).
- Iteration count < 8 (no Hard cap).
