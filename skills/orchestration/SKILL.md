---
name: orchestration
description: "Orchestrate a large task as a manager-run sequence of isolated sub-agent phases when the user explicitly invokes this skill or asks for this. The main agent decomposes the task into phases of different kinds, picks the topology that fits (linear pipeline, parallel fan-out, dependency DAG, or iterative loop), assigns each phase a capability-by-deliberation tier, and runs each as a fresh isolated sub-agent exchanging file paths only -- never doing phase work itself. It proves any expensive step cheaply before committing, and halts for the user at up to two points: go/no-go before that commitment, and accept/reject on review findings. Runs are resumable by run id; a changed condition re-versions the prior run. For large heterogeneous work: research sweeps, multi-variant runs, migrations, audits. Explicit-invocation only. Not for single-artifact build-review-improve loops (use delegated-review-loop) or single-answer blind verification (use iterative-self-review)."
---

# Orchestration

A manager pattern for large tasks that break into a sequence of *different kinds* of work. The main agent stays a pure orchestrator: it decomposes the task, picks the topology that fits (a linear pipeline, a parallel fan-out, a dependency DAG, or an iterative loop), assigns each phase a tier, and runs phases as isolated sub-agents that exchange only file paths. It proves any expensive step cheaply before committing to it, validates each phase's output, surfaces progress as it goes, and stops at up to two points to let the user judge. It never does the phase work itself, and it never decides those points on the user's behalf.

Why the main agent never does phase work: a manager that also produces, runs, or scores inherits the producer's blind spots and loses the lean context it needs to sequence the whole run. Separating the orchestrator (decomposes, sequences, gates, reports) from the phase agents (each owns one phase in a clean context) keeps both honest — and keeps the orchestrator's context small enough to run a long task without drowning.

Why at most two user-judged stops, never more: the value is a *long autonomous run* the user can trust, not a babysat one. Most phases run on their own, and a run with no expensive step and no review halts zero times. But when those two judgments do arise — whether a cheap proof is good enough to commit the expensive step, and whether review findings are real — they are not the orchestrator's to make. Halting at every phase destroys the autonomy; folding either of these two into the orchestration makes it grade its own homework.

## When to use

Only when the user explicitly invokes this skill or explicitly asks to run a task as a manager-driven sequence of sub-agent phases. Never auto-trigger on ordinary implementation requests or on task completion.

Use this when the task decomposes into **heterogeneous phases** — different *kinds* of work (investigate, produce, run, evaluate, report), in whatever topology fits. If the task is a single artifact that needs to be built and then reviewed, `delegated-review-loop` is the right tool. If it is a single answer that needs blind verification, `iterative-self-review` is the right tool. This skill is the backbone for everything larger and more heterogeneous than those.

## Roles

| Role | Holds | Never does |
|------|-------|-----------|
| **Main agent (orchestrator)** | Run id and session lifecycle, decomposition, topology choice, tier assignment, sequencing, cheap-proof framing, review-material routing, progress and reports, re-versioning on change | Perform phase work (investigate / produce / run / evaluate / analyze); decide a review finding's accept/reject for the user; inline phase content into a sub-agent prompt |
| **Phase sub-agent** (one per phase or per fanned-out item) | One phase's full working context and its own tools; writes its output as documents and returns paths | Run a different phase; talk to the user; inherit another phase's working context |
| **Reviewer sub-agents** (constructive and adversarial, optional) | The material to critique, received as paths; one lens each | Decide accept/reject (that is the user's judgment); edit the work; act on their own findings |

## Run directory and path-passing

All inter-phase content travels as documents inside one per-run directory, `.agents/orchestration/<run-id>/`, created by the orchestrator at the start. The isolation contract keeps the orchestrator's context lean and keeps phases from contaminating each other:

- The orchestrator hands sub-agents **file paths only** — it never pastes phase content into a prompt.
- Each phase reads its inputs from files itself and writes its output as new documents in the run directory, returning only the path.
- **Which paths the orchestrator hands to whom is the isolation contract.** A phase that receives another phase's working notes is no longer isolated. The full layout, lifecycle, resume, validation, and run-id/superseded rules live in [phase_protocol.md](references/phase_protocol.md) — follow it exactly.

Deliverables (code, artifacts, reports the user keeps) live at their real paths; the run directory holds coordination documents only.

## Choosing a topology

The topology is the shape of the dependency structure between phases, and it decides how Step 5 executes and whether Step 4 applies. Pick the one that fits — do not default to fan-out:

- **Linear pipeline** — each phase feeds the next (investigate → draft → edit → publish). No fan-out.
- **Parallel fan-out + reduce** — split into independent items, run them concurrently, synthesize the results.
- **Dependency DAG** — phases with a partial order; some parallel, some sequential (a migration touching dependent modules).
- **Iterative loop** (nested only) — produce → critique → refine until a criterion holds, as *one phase* inside a larger run. A whole-task build-review-improve loop is `delegated-review-loop`, not this skill.
- **Recursive decomposition** — a phase discovers sub-phases and the orchestrator spawns them.

A run may nest these (a fan-out whose items are each a small pipeline). The per-topology rules for isolation, tiering, the cheap-proof gate, execution order, and aggregation are in [orchestration_shapes.md](references/orchestration_shapes.md).

## Workflow

### Step 1 — Frame, decompose, open the run

Extract the substantive task from the user's own words (reconstruct from earlier utterances with verbatim quotes if the invocation is contentless). Decompose it into **phases** — each phase is one *kind* of work with a clear completion condition. Decomposition heuristics: a phase should be one kind of work, one completion condition, and one tier; **split** a phase that spans two tiers or has independent failure modes; **merge** phases that always succeed or fail together. Create the run directory and a `run-id` per [phase_protocol.md](references/phase_protocol.md). Write the task and phase plan to `run_plan.md`. The plan is a working hypothesis, not a fixed conveyor — phases may be added, split, or re-versioned as the run learns (Step 8).

### Step 2 — Pick the topology and assign tiers

Pick the topology (above; details in [orchestration_shapes.md](references/orchestration_shapes.md)) that matches the phases' dependency structure. Then assign each phase a tier by the **assignment rules** in [tiering.md](references/tiering.md) — judgment-heavy work (design, evaluation, adversarial review, synthesis) to the high tier; mechanical work (investigation, command execution, transformation, aggregation) to the standard tier.

### Step 3 — Investigate (optional, cheap)

If the decomposition depends on facts you do not yet have — how many items a fan-out covers, what the dependency graph is, what scope each phase faces — spawn one low-cost investigation phase first. It surveys and returns a topology/phase recommendation; it does not produce deliverables. Skip this when the shape is already known.

### Step 4 — Cheap proof before an expensive commitment  ·  HALT (go / no-go)  ·  conditional

This applies **only when the run has an expensive step to commit to** — a wide fan-out, a long DAG, many loop iterations. Run the **cheapest representative slice** exactly as the full step would (one item per branch, or one phase end-to-end on a single input), then evaluate it for *harness* failures distinct from *work* failures (defined in [phase_protocol.md](references/phase_protocol.md)).

This is **halt type 1**. Present the slice result and a go/no-go recommendation; do not commit the expensive step until the user approves. A slice that surfaces harness bugs is the gate working — fix the rig and re-slice rather than spending the full step on a broken one. If the topology has **no** expensive step (a short linear pipeline), skip this halt and say so in the plan.

### Step 5 — Execute per topology

Run the phases in the topology's order — concurrently for independent fan-out items, sequentially for a linear pipeline, in dependency order for a DAG, repeat-until-criterion for a loop (per [orchestration_shapes.md](references/orchestration_shapes.md)). For each phase:

- Run it in a **fresh isolated sub-agent**, paths only, writing outputs as documents and returning paths.
- **Validate the output against its contract.** On a contract violation (malformed, missing required fields, empty where output was required), retry up to the cap, then escalate — rules in [phase_protocol.md](references/phase_protocol.md).
- **Be resume-aware:** skip phases already completed under this run-id; continue from the first incomplete phase ([phase_protocol.md](references/phase_protocol.md)).
- **Close on completion** and account every spawn with a close; leave no orphaned agents.

### Step 6 — Review checkpoint  ·  HALT (user judges)  ·  optional

When the output warrants scrutiny, spawn reviewer sub-agents to **generate** material — at minimum a constructive lens (what to improve) and an adversarial lens (what is wrong or invalid), as distinct agents so one does not soften the other. They produce evidence-bearing findings and return paths ([review_gate.md](references/review_gate.md)).

This is **halt type 2**. The orchestration **generates** review material but does not act on it: present the findings and let the user decide accept/reject. The orchestrator may merge, deduplicate, and rank for readability, but never auto-accepts a finding or proceeds on its own verdict. Accept/reject is the user's. If you judge review unwarranted for this run, say so and why rather than skipping it silently.

### Step 7 — Aggregate and report

Aggregate the phase outputs per the topology — concatenate independent results, or synthesize them with a JUDGE-tier reduce phase when they must become one conclusion ([orchestration_shapes.md](references/orchestration_shapes.md)). Report: outcome, per-phase or per-item results, and artifacts by path. Label every load-bearing claim `confirmed` (backed by an artifact/log/path) or `inferred` (plausible, needs more). Surface progress throughout the run, not only here — see **Progress and cost**. Close with the termination block below.

### Step 8 — Feedback, re-versioning, resume

Apply user feedback. If feedback changes any **run condition** — inputs, item set, topology, tier assignment, allowed tools, evaluation criteria, prompts — open a **new run-id**, mark the prior run `superseded`, record the change in `change_log.md`, and re-run the affected scope under the new conditions (details in [phase_protocol.md](references/phase_protocol.md)). If the run was **interrupted** mid-flight, treat the interruption as feedback: re-version if it changed a condition, otherwise **resume** from the last completed phase.

## Progress and cost

- **Progress (surfaced):** keep a live plan — the phase list with each phase's status — and emit a short checkpoint when each phase completes (what finished, what is next). A long autonomous run must be legible without reading transcripts.
- **Cost (observed, never a governor):** surface an estimate — expected phase/agent count and JUDGE-tier calls — at the plan and again before any expensive commitment. Cost **informs** the user; it does **not** add a halt, cap the run, or change tier/topology choices. The orchestration proceeds on correctness, not on cost.

## Halt conditions

At most two phases halt for the user — possibly zero. Everything else runs autonomously.

1. **Go/no-go** (Step 4) — before committing an expensive step. Skipped when the topology has no expensive step.
2. **Review accept/reject** (Step 6) — the user judges review findings; the orchestration never decides them itself. Optional per run, but a skip is **stated with its reason**, never silent — deciding *not* to review is adjacent to the judgment that belongs to the user.

Do not add halts at other phases — extra halts destroy the long-autonomous-run value. Do not turn these two into autonomous decisions — that makes the orchestration its own judge.

## Output contract

Every run ends with a `termination:` block. It reuses the block convention and the shared field names (`trigger`, `user_decisions`, `residual_issues`, `failure_log`) from the ecosystem's review skills, extended with the fields a multi-phase run needs:

```yaml
termination:
  trigger: completed | halted_for_user | aborted
  run_id: <id>
  resumed_from: <prior run-id or null>
  topology: linear | fan_out | dag | loop | recursive | nested
  phases_run: <count>
  user_decisions:                 # the two halts surface here
    - gate: go_no_go | review_accept_reject
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
- **One backbone, topology as a parameter.** The workflow, isolation contract, tier rules, two halts, and re-versioning do not change with the shape; the topology only changes Step 5's execution order and whether Step 4 applies. Do not fork into separate procedures per shape.
- **Portable by construction.** This skill is instructions an agent follows, not orchestration code. Keep core logic free of any specific runtime's primitives or model names; concrete spawn mechanisms, tier bindings, and tool-permission defaults live as *examples* in the reference files.
- **Cost never governs**, and the **orchestrator does no phase work** and **decides neither halt** for the user.

## Reference files

| File | When to read |
|------|--------------|
| [orchestration_shapes.md](references/orchestration_shapes.md) | Step 2 and Step 5 — the topologies, how each maps isolation, tiering, the cheap-proof gate, execution order, and aggregation |
| [tiering.md](references/tiering.md) | Step 2 — capability-by-deliberation tiers, the assignment rules, platform binding examples, and why the cheap-proof gate re-validates the binding |
| [phase_protocol.md](references/phase_protocol.md) | Steps 1, 4, 5, 8 — run directory layout, per-phase isolation, lifecycle and orphan accounting, output-contract validation and retry, resume protocol, harness-vs-work failure split, recovery policy, run-id/superseded discipline |
| [review_gate.md](references/review_gate.md) | Step 6 — constructive and adversarial generation, the user-judged halt, what to present, and the self-marking rationale |
| [orchestration_template.md](references/orchestration_template.md) | Steps 3, 5, 6 — the role-boundary phase-prompt template, tool-permission defaults, and platform-primitive notes |
