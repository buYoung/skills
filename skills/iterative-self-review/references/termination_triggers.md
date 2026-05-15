# Termination Triggers

Three categories, eight triggers. Evaluate in priority order each iteration; the first trigger that fires ends the loop.

User clarification is **not** a termination trigger — it is a routing branch handled in `routing_rules.md` (pause → ask user → resume from Step 1 without resetting the iteration counter).

## Priority order

Evaluated in Step 6 of every iteration:

1. **Regression** (Defensive)
2. **Verifier invalid report** (Defensive)
3. **Oscillation** (Convergence)
4. **Stable findings** (Convergence)
5. **Clean pass** (Positive)
6. **Severity floor** (Positive)
7. **No-op iteration** (Convergence)
8. **Hard cap** (Fallback)

Defensive triggers come first because rollback must outrank any optimistic "one more pass might help" instinct. Convergence triggers that prove the loop cannot productively improve come before Positive triggers so that a stalled loop is not mistakenly closed as a success. `no_op` sits after Positive triggers because zero-accept is only a stop signal once "clean" and "severity floor" have been ruled out. Hard cap is last — fallback, not a preferred outcome.

## Defensive triggers

### 1. Regression
- **Definition**: This iteration's response has *more* blocker- or major-severity issues than the previous iteration.
- **Detection**: Deterministic count.
- **Action**: Stop. Discard the current response and adopt the previous iteration's response as final.

### 2. Verifier invalid report
- **Definition**: The sub-agent's report violates `report_format.md` enforcement (missing `artifact_inspections` for cited artifacts, missing `evidence` direct quotes on `issues`/`missing`, or missing `source_of_uncertainty`/`affects_direction` on `unverified_assertions`) for **two consecutive iterations** after re-call.
- **Detection**: Deterministic schema check against `report_format.md`.
- **Action**: Stop. Adopt the last iteration whose report was valid. If no prior valid iteration exists, adopt the current draft and surface the verifier failure in metadata.
- **Rationale**: Without a valid verifier report, no Positive trigger can be trusted. Repeated invalid reports indicate the loop cannot be salvaged by another re-call.

## Convergence triggers (loop end when iteration cannot productively improve)

### 3. Oscillation
- **Definition**: A semantic issue is accepted in one iteration and rejected (or vice versa) in another iteration of the same loop. A **single flip** is sufficient. Uses the rejection log defined in `routing_rules.md`.
- **Detection**: The same semantic issue appears with opposing accept/reject decisions across any two iterations.
- **Action**: Stop. Adopt the response from the iteration where the main agent last **rejected** the oscillating finding (the conservative side of the flip).
- **Rationale**: A flip already proves the main agent cannot stably decide on the finding; further iterations will only repeat the flip.

### 4. Stable findings
- **Definition**: The issues set is *semantically identical* to the previous iteration's.
- **Detection**: A separate sub-agent (equivalence judge) is asked, "Are these two issue sets semantically equivalent?" — yes/no only. **No similarity scores, no numeric thresholds.** If ambiguous, treat as "not equivalent" and continue.
- **Action**: Stop. Further iterations would only reproduce the same findings.

## Positive triggers (normal termination)

**Gating precondition for every Positive trigger:** The Step 5.5 routing-completion gate (defined canonically in `routing_rules.md`) must have passed for the current iteration. If the gate has not passed, no Positive trigger may fire this iteration.

**Verdict gate:** If the sub-agent's report this iteration has `verdict: issues_found`, no Positive trigger may fire. `severity_floor` applies only **after** routing has downgraded or rejected every remaining issue to `minor`.

### 5. Clean pass
- **Definition**: Sub-agent report has `verdict: clean`, `issues=[]`, `missing=[]`, a complete `artifact_inspections` manifest for all cited artifacts, **and** the Step 5.5 routing-completion gate passed.
- **Action**: Stop. Adopt the current response.

### 6. Severity floor
- **Definition**: All remaining issues are `minor`, and main-agent routing downgraded or rejected all of them, **and** the Step 5.5 routing-completion gate passed.
- **Action**: Stop. Adopt the current response.

## Convergence (post-positive)

### 7. No-op iteration
- **Definition**: Routing produced **zero** accepted items this iteration (everything rejected or downgraded), and no Positive trigger fired.
- **Action**: Stop. Adopt the current response.
- **Distinction from Stable findings**: Stable = same issue set across iterations (sub-agent output signal); No-op = zero accepted items this iteration (main-agent decision signal).

## Fallback

### 8. Hard cap
- **Definition**: Iteration count reaches **8** (default).
- **Action**: Stop. Adopt the current response.
- **Override**: Increase only when the user explicitly asks for a deeper loop and the task value justifies it.

## Equivalence-judge sub-agent call (for Stable findings)

When the main agent needs to evaluate trigger #4, invoke a **separate sub-agent** with the two issue sets and the following constraints:

- Inputs: only the two YAML issue sets (current iteration and previous iteration). No reasoning, no draft, no prior verdicts.
- Question (verbatim): *"Are these two issue sets semantically equivalent? Answer `yes` or `no` only. If uncertain, answer `no`."*
- Output: a single token — `yes` or `no`.
- Forbidden: numeric scores, similarity ratios, partial answers, explanations, or any other text.

This sub-agent is distinct from the verification sub-agent and exists to keep equivalence judgments independent of the main agent's self-bias.

## Final response metadata schema

Append to the final response:

```yaml
termination:
  trigger: clean_pass | severity_floor | regression | verifier_invalid_report | oscillation | stable_findings | no_op | hard_cap
  iterations: <count>
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

The trigger name alone identifies the termination category (Defensive / Convergence / Positive / Fallback) via the priority table above. Surface `regression`, `verifier_invalid_report`, `oscillation`, `stable_findings`, `no_op`, and `hard_cap` to the user — do not hide them behind a normal-looking response. Only `clean_pass` and `severity_floor` represent successful termination.

`user_clarifications[]` records any pause/ask/resume events that occurred during the loop. Use empty arrays for unused fields.

## Continue conditions

All must hold to proceed to the next iteration:

- No trigger from the eight above has fired.
- The issues set changed semantically since the previous iteration (no Stable findings).
- Routing produced at least one accepted item (no No-op).
- Iteration count < 8 (no Hard cap).
