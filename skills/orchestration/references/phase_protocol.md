# Phase protocol: isolation, lifecycle, validation, resume, recovery, re-versioning

This file is the mechanical contract behind the workflow. It covers the run directory, how phases stay isolated, how their lifecycle is accounted for, how a phase's output is validated and retried, how a run resumes after interruption, how to tell a harness failure from a work failure and recover from each, and how to re-version when conditions change.

## Run directory layout

The orchestrator creates one directory per run and keeps all coordination documents there. Deliverables live at their real paths; this directory holds only the documents phases pass to each other.

```text
.agents/orchestration/<run-id>/
  run_plan.md            # task, phase plan, topology, tier assignments (Step 1-2)
  state.json             # phase status ledger: each phase's status + output path (resume/progress)
  change_log.md          # every condition change and re-version reason (Step 8)
  investigate/           # optional survey output (Step 3)
  proof/                 # cheap representative-slice outputs and the go/no-go material (Step 4)
  phases/<phase>/        # per-phase or per-item outputs (Step 5)
  reviews/<lens>.md      # constructive / adversarial findings (Step 6)
  report.md              # the user-facing report and termination block (Step 7)
```

`<run-id>` is a stable, human-readable id chosen at Step 1 (for example a short task slug plus a sequence number). It never changes within a run; a changed condition opens a *new* run-id (see "Re-versioning").

## Per-phase isolation

- **Paths only.** The orchestrator hands each sub-agent the *paths* to its inputs, never the inputs' content pasted into the prompt. The sub-agent opens the files itself.
- **Outputs are documents.** Each phase writes its result as one or more documents under the run directory and returns the path(s). It returns a short status to the orchestrator, not the full content.
- **The path set is the isolation boundary.** A phase only sees what its input paths expose. Do not hand a phase another phase's working notes unless that phase is *meant* to build on them — that decision is the isolation contract, and getting it wrong silently contaminates the phase.
- **Fresh context per phase.** Each phase runs in its own sub-agent with no inherited working context from sibling phases. On runtimes where sub-agents are one-shot and auto-isolated this is automatic; on runtimes where agents persist, the orchestrator enforces it (see Lifecycle).

## Lifecycle and orphan accounting

State the lifecycle as *intent*, then bind it to the runtime:

- **Intent:** each phase runs in a fresh isolated context; when it completes, its working context is discarded so nothing leaks into the next phase, and no agent is left running.
- **Binding:** on a one-shot sub-agent runtime, a phase call already satisfies this — there is nothing to close. On a persistent-agent runtime, the orchestrator must explicitly close each agent when its phase completes.
- **Account every spawn with a close.** On persistent runtimes, orphaned agents accumulate (a common, real failure: dozens of agents left open mid-run, consuming resources). Track spawns and closes; reconcile them at the end of each fan-out so the count is zero. Closing an already-finished agent is a safe no-op — prefer over-closing to leaking.

## Output-contract validation and retry

Every phase declares an output contract (the schema in its prompt, per orchestration_template.md). The orchestrator validates the returned output against it before treating the phase as done:

- **Validate** structure, required fields, and non-emptiness where output is required. The short status the agent returns is not the output — read the written document and check it.
- **On a contract violation, retry** the phase with the same inputs, up to a cap (default 2 retries). A contract violation is a malformed, missing, or empty output — *not* a work failure; the agent may simply have returned the wrong shape.
- **After the cap, escalate** to the user rather than spinning or accepting a broken output. Record the violation in `failure_log`.
- **Distinguish from work failure:** retrying is for *shape* problems only. Do not auto-retry a genuine work failure (a real but wrong answer) to mask it — that is exactly the masking the harness-vs-work split forbids.

## Resume protocol

A long run must survive interruption — a crash, a kill, a deliberate pause — without restarting from zero. The run directory is the durable state:

- **`state.json` is the ledger.** Each phase records `pending | running | done | failed` plus its output path when done. The orchestrator updates it as phases complete.
- **Re-entry skips completed phases.** On resume under the same run-id, read `state.json`, treat `done` phases as final (their outputs are on disk), and continue from the first `pending`/`failed` phase. Never re-run a `done` phase — its output is authoritative.
- **A `running` phase at resume is indeterminate** — its agent died mid-flight, so re-run it from scratch and discard the partial output; a half-written output is not a `done` output.
- **Resume is not re-versioning.** Resume continues the *same* run under unchanged conditions. If a condition changed, that is re-versioning (a new run-id), not resume. Record the resume in the termination block's `resumed_from`.

## Harness failure vs work failure

A phase can fail two very different ways, and conflating them corrupts every downstream conclusion. Define the split before the run and apply it mechanically:

- **Harness failure** — the phase failed *before the work could happen*: wrong working directory, missing or unreadable inputs, a prompt that never reached the agent, a tool-surface violation, an empty capture where output was required, a quoting/config error in the invocation. The work was never actually attempted under valid conditions.
- **Work failure** — the phase ran under valid conditions and the *result* was wrong, incomplete, empty-by-the-agent's-choice, or timed out after a genuine attempt.

Rules:

- A harness failure is **invalid**, not a work failure. It does not count against the phase's quality; it means the rig is broken. Fix the rig and re-run that slice.
- A work failure **counts** as a real outcome. Do not silently retry it to hide it.
- The cheap-proof gate (SKILL Step 4) exists to surface harness failures on a cheap slice *before* the expensive step inherits them.
- When in doubt, keep raw captures (stdout/stderr, exit code, the exact prompt the agent received) so the split can be made from evidence, not guessed.

## Recovery policy

When a phase genuinely fails after validation and retries are exhausted, what the run does next depends on the topology (orchestration_shapes.md):

- **Fan-out item fails** → record it, **continue** the other items, and report the failed item in `failure_log`. One bad item does not abort the batch; the reduce phase works with what completed and notes the gap.
- **Linear-pipeline phase fails** → the chain cannot continue past it. **Halt and escalate** — downstream phases depend on the missing output.
- **DAG phase fails** → block **only its dependents**; independent branches continue. Escalate with the blocked sub-graph identified.
- **Loop iteration fails** → stop the loop, keep the last good iteration, report residuals.

In every case, never silently drop a failure from the final report: report how many phases failed and why, separately from the successful results.

## Re-versioning (superseded discipline)

The spine of a long, evolving run. The moment any **run condition** changes, the old and new results stop being comparable — so do not pool them.

A run condition is any of: the inputs or item set, the variant set, a tier assignment, the allowed tool surface, the evaluation criteria, or the phase prompts.

When one changes:

1. Open a **new `run-id`**. Do not edit the old run's outputs in place.
2. Mark the prior run **`superseded`** in its report and in the termination block.
3. Record the change and its reason in `change_log.md` — what changed, why, and which run-ids it spans.
4. Re-run the **affected scope** under the new conditions, not just the one item that triggered the change. For a comparative run that means every compared branch under identical conditions; for a migration or audit, the portion the change touches.
5. Do not place superseded results and current results in the same comparison table. Reference superseded numbers separately, if at all.

This is deliberately strict: it is what lets a run absorb mid-flight corrections (a fixed harness, an added variant, a corrected criterion) without the final report quietly mixing apples from three different rigs.
