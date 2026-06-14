---
name: orchestration
description: "Orchestrate a multi-phase delegated pipeline when the user explicitly invokes this skill or asks to run a large task as a sequence of isolated sub-agent phases. The main agent decomposes the task into phases of different kinds (investigate -> produce -> run -> evaluate -> report), assigns each a capability-by-deliberation tier, proves the rig with one cheap slice before expensive fan-out, and halts for the user at exactly two points: sanity go/no-go and review accept/reject. Each phase is a fresh isolated sub-agent exchanging file paths only; the main agent never does phase work, and when a run condition changes it opens a new run id and supersedes the prior one. For large heterogeneous tasks: research sweeps, artifact generation, multi-variant runs, migrations, audits. Explicit-invocation only. Not for single-artifact build-review-improve loops (use delegated-review-loop) or single-answer blind verification (use iterative-self-review)."
---

# Delegated Pipeline Orchestration

A manager pattern for large tasks that break into a sequence of *different kinds* of work. The main agent stays a pure orchestrator: it decomposes the task into phases, assigns each phase a tier, runs phases as isolated sub-agents that exchange only file paths, proves the harness with one cheap slice before spending the expensive fan-out, and stops at two points to let the user judge. It never does the phase work itself, and it never decides on the user's behalf at those two points.

Why the main agent never does phase work: a manager that also produces, runs, or scores inherits the producer's blind spots and loses the lean context it needs to sequence the whole pipeline. Separating the orchestrator (sequences, gates, reports) from the phase agents (each owns one phase in a clean context) keeps both honest — and keeps the orchestrator's context small enough to run a long pipeline without drowning.

Why two user-judged stops and not zero or N: the value users want from this is a *long autonomous run* they can trust, not a babysat one. So most phases run on their own. But two judgments are not the orchestrator's to make — whether a sanity slice is good enough to commit the full fan-out, and whether review findings are real. Those go to the user. Halting everywhere destroys the autonomy; halting nowhere makes an orchestration grade its own homework.

## When to use

Only when the user explicitly invokes this skill or explicitly asks to run a task as a manager-driven sequence of sub-agent phases. Never auto-trigger on ordinary implementation requests or on task completion.

Use this when the task decomposes into **heterogeneous phases** — different *kinds* of work in sequence (investigate, then produce, then run, then evaluate, then report), often fanned out across many items or variants. If the task is a single artifact that needs to be built and then reviewed, `delegated-review-loop` is the right tool. If it is a single answer that needs blind verification, `iterative-self-review` is the right tool. This skill is the backbone for everything larger and more heterogeneous than those.

## Roles

| Role | Holds | Never does |
|------|-------|-----------|
| **Main agent (orchestrator)** | Run id and session lifecycle, task decomposition, tier assignment, phase sequencing, sanity-gate framing, review-material routing, user reports, re-versioning on change | Perform phase work (investigate / produce / run / evaluate / analyze); decide a review finding's accept/reject for the user; inline phase content into a sub-agent prompt |
| **Phase sub-agent** (one per phase or per fanned-out item) | One phase's full working context and its own tools; writes its output as documents and returns paths | Run a different phase; talk to the user; inherit another phase's working context |
| **Reviewer sub-agents** (constructive and adversarial, optional) | The material to critique, received as paths; one lens each | Decide accept/reject (that is the user's judgment); edit the work; act on their own findings |

## Path-passing and per-phase isolation

All inter-phase content travels as documents inside one per-run directory, `.agents/pipeline/<run-id>/`, created by the orchestrator at the start. The isolation contract is what keeps the orchestrator's context lean and keeps phases from contaminating each other:

- The orchestrator hands sub-agents **file paths only** — it never pastes phase content into a prompt.
- Each phase reads its inputs from files itself and writes its output as new documents in the run directory, returning only the path.
- **Which paths the orchestrator hands to whom is the isolation contract.** A phase that receives another phase's working notes is no longer isolated. The full layout, lifecycle, and run-id/superseded rules live in [phase_protocol.md](references/phase_protocol.md) — follow it exactly.

Deliverables (code, datasets, reports the user keeps) live at their real paths; the run directory holds coordination documents only.

## Workflow

### Step 1 — Frame, decompose, open the run

Extract the substantive task from the user's own words (reconstruct from earlier utterances with verbatim quotes if the invocation message is contentless). Decompose it into **phases** — each phase is one *kind* of work, with a clear completion condition. Create the run directory and assign a `run-id` per [phase_protocol.md](references/phase_protocol.md). Write the task and the phase plan to `run_plan.md`.

A phase plan is a working hypothesis, not a fixed conveyor. Phases may be added, split, or re-versioned as the run learns something (Step 8). Do not over-specify the count up front; if the decomposition itself is uncertain, that is what Step 2's investigate phase is for.

### Step 2 — Assign tiers

For each phase, assign a tier by the **assignment rules** in [tiering.md](references/tiering.md) — judgment-heavy work (design, evaluation, adversarial review, synthesis) to the high tier; mechanical work (investigation, command execution, transformation, aggregation) to the standard tier. Tier is `capability x deliberation`, bound to concrete runtime settings per the table in `tiering.md`. The binding is an approximation on runtimes without per-agent deliberation control, and the sanity gate (Step 4) is what re-validates it.

### Step 3 — Investigate (optional, cheap)

If the decomposition depends on facts you do not yet have — how many items the fan-out covers, which variants exist, what scope each phase faces — spawn one low-cost investigation phase first. It surveys and returns a phase/fan-out recommendation; it does not produce deliverables. Skip this for tasks whose shape is already known.

### Step 4 — Sanity gate  ·  HALT (go / no-go)

Before any expensive fan-out, run the **cheapest representative slice** — one item per variant, or one phase end-to-end on a single input — exactly as the full run would. Then evaluate it for *harness* failures distinct from *work* failures (the distinction is defined in [phase_protocol.md](references/phase_protocol.md)): missing outputs, wrong working directory, empty captures, tool-surface violations, prompt-delivery errors.

This is **halt type 1**. Present the sanity result and a go/no-go recommendation to the user. Do not start the full fan-out until the user approves. A sanity slice that surfaces harness bugs is the gate working as intended — fix the harness and re-slice rather than spending the full fan-out on a broken rig.

### Step 5 — Fan-out execution

On go, run the full work. Fan out **in parallel where items are independent**; run **serially where phases depend on each other or where parallel load is a real constraint**. Each phase or item runs in a fresh isolated sub-agent (Step's isolation contract), writes its outputs as documents, returns paths, and is closed on completion per the lifecycle rules in [phase_protocol.md](references/phase_protocol.md). Account for every spawn with a close; leave no orphaned agents.

### Step 6 — Review checkpoint  ·  HALT (user judges)  ·  optional

When the run's output warrants scrutiny, spawn reviewer sub-agents to **generate** material — at minimum a constructive lens (what to improve) and an adversarial lens (what is wrong or invalid), as distinct agents so one does not soften the other. They produce findings with evidence and return paths. Details in [review_gate.md](references/review_gate.md).

This is **halt type 2**. The orchestration **generates** review material but does not act on it: present the findings to the user and let the user decide accept/reject. The orchestrator may merge, deduplicate, and rank for readability, but it never auto-accepts a finding or proceeds on its own verdict. Accept/reject is the user's.

### Step 7 — Aggregate and report

Synthesize results into a user-facing report: outcome, per-variant or per-phase results, and the run's artifacts by path. Label every load-bearing claim `confirmed` (backed by an artifact/log/path) or `inferred` (plausible from current evidence, needs more). Close with the termination block in the **Output contract** below.

### Step 8 — Feedback and re-versioning (the adaptive spine)

Apply user feedback. If feedback changes any run condition — inputs, variant set, tier assignment, allowed tools, evaluation criteria, prompts — do **not** mix the new results with the old. Open a **new run-id**, mark the prior run `superseded`, record the change and its reason in `change_log.md`, and re-run the affected scope under the new conditions — for a comparative run, every compared branch; for a migration or audit, the portion the change touches. This re-versioning discipline is not an edge case; it is the spine that keeps a long, evolving run interpretable. The rules are in [phase_protocol.md](references/phase_protocol.md).

## Halt conditions

Exactly two phases halt for the user. Everything else runs autonomously.

1. **Sanity go/no-go** (Step 4) — before committing the expensive fan-out.
2. **Review accept/reject** (Step 6) — the user judges review findings; the orchestration never decides them itself.

Do not add halts at other phases — extra halts destroy the long-autonomous-run value. Do not remove these two — removing them makes the orchestration its own judge.

## Output contract

Every run ends with a `termination:` block. It reuses the block convention and the shared field names (`trigger`, `user_decisions`, `residual_issues`, `failure_log`) from the ecosystem's review skills, extended with the pipeline-specific fields a multi-phase run needs:

```yaml
termination:
  trigger: completed | halted_for_user | aborted
  run_id: <id>
  phases_run: <count>
  fan_out: <count of items across the run>
  user_decisions:                 # the two halts surface here
    - gate: sanity_go_no_go | review_accept_reject
      question: <what was asked>
      answer: <what the user decided>
  superseded_runs:                # prior runs this run retroactively replaced
    - run_id: <prior id>
      reason: <one line>
  residual_issues:
    - severity: minor
      problem: <one line>
  failure_log:                    # harness vs work failures encountered
    - type: harness | work
      cause: <one line>
      phase: <which phase or item>
  artifacts:
    - <path>
```

Only `completed` is a clean finish. Surface `halted_for_user` and `aborted` plainly — never behind a normal-looking report. A run never declares itself `superseded`; it becomes superseded later, retroactively, when a successor run replaces it (Step 8).

## Scope and guardrails

- **Explicit-invocation only.** Never auto-trigger.
- **Not** a single-artifact build-review-improve loop (`delegated-review-loop`) and **not** single-answer verification (`iterative-self-review`).
- **Portable by construction.** This skill is instructions an agent follows, not orchestration code. Keep core logic free of any specific runtime's primitives or model names; concrete spawn mechanisms and tier bindings live as *examples* in the reference files (see [orchestration_template.md](references/orchestration_template.md) and [tiering.md](references/tiering.md)).
- **Orchestrator does no phase work**, and **decides neither halt** for the user.

## Reference files

| File | When to read |
|------|--------------|
| [tiering.md](references/tiering.md) | Step 2 — capability-by-deliberation tiers, the assignment rules, platform binding examples, and why the sanity gate re-validates the binding |
| [phase_protocol.md](references/phase_protocol.md) | Steps 1, 4, 5, 8 — run directory layout, per-phase isolation, lifecycle and orphan accounting, harness-vs-work failure split, run-id/superseded discipline |
| [review_gate.md](references/review_gate.md) | Step 6 — constructive and adversarial generation, the user-judged halt, what to present, and the self-marking rationale |
| [orchestration_template.md](references/orchestration_template.md) | Steps 3, 5, 6 — the role-boundary phase-prompt template and platform-primitive notes |
