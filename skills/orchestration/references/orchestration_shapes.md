# Orchestration shapes (topologies)

The topology is the dependency structure between phases. It is the one thing that changes how Step 5 executes and whether Step 4's cheap-proof gate applies — everything else in the skill (manager-only, isolation, tiering, the two halts, re-versioning) is the same across all shapes. Pick the shape that fits the task's real dependency structure; do not default to fan-out because the origin pattern used it.

## How to choose

Read the dependency structure, then match:

- Phases form a chain, each needs the previous one's output → **linear pipeline**.
- The work splits into many independent items of the same kind → **parallel fan-out + reduce**.
- Phases have a partial order — some depend on others, some are independent → **dependency DAG**.
- A *phase* within the run is "produce, improve against a criterion, repeat" → **iterative loop** (nested; a whole-task loop is `delegated-review-loop`, not this skill).
- You cannot enumerate the phases up front; a phase will discover them → **recursive decomposition**.

When more than one fits, prefer the simplest that captures the real dependencies. Over-parallelizing a chain corrupts order; over-serializing independent work wastes time.

## Linear pipeline

Each phase consumes the prior phase's output and feeds the next: `A → B → C → D`.

- **Isolation:** each phase receives only the prior phase's output path (plus the immutable task), not the whole history. The orchestrator decides how far back each phase may see.
- **Tiering:** mixed per phase by the assignment rules — a draft phase may be WORKER, an evaluation phase JUDGE.
- **Cheap-proof gate (Step 4):** usually **skip** — there is no wide expensive step to commit to. Apply it only if one phase is itself very expensive.
- **Execution:** strictly sequential; a phase starts when its predecessor's output validates.
- **Aggregation:** the last phase's output is the result; no reduce needed.

## Parallel fan-out + reduce (map-reduce)

Split the task into many independent items, run them concurrently, then synthesize.

- **Isolation:** each item-phase sees only its own item and the immutable task — never sibling items' outputs. Sibling leakage biases items toward each other.
- **Tiering:** the map phases are often WORKER (one bounded item each); the reduce is usually JUDGE (it forms one conclusion from many).
- **Cheap-proof gate (Step 4):** **apply** — this is the expensive-commitment case. Run one representative item end-to-end first, halt for go/no-go, then commit the full fan-out.
- **Execution:** concurrent, but bound concurrency to what the host can sustain — stagger or cap parallel starts to avoid resource spikes; serialize when parallel load is the constraint.
- **Aggregation:** a dedicated JUDGE reduce phase that reads all item outputs (by path) and synthesizes. Do not let the orchestrator do the synthesis inline — that is phase work.

## Dependency DAG

Phases with a partial order: some parallel, some sequential, governed by who-needs-whose-output.

- **Isolation:** each phase receives the outputs of exactly its prerequisites — no more. The edge set is the isolation contract.
- **Tiering:** per phase by assignment rules.
- **Cheap-proof gate (Step 4):** **apply if a wide or expensive frontier exists** — prove one representative path through the graph before committing the rest.
- **Execution:** topological order; run all phases whose prerequisites are satisfied concurrently, respecting the concurrency cap. A failed phase blocks only its dependents (see the recovery policy in phase_protocol.md), not independent branches.
- **Aggregation:** the sink phase(s); synthesize if there is more than one sink.

## Iterative loop

Produce, evaluate against a criterion, refine, repeat until the criterion holds or a cap is hit.

- **Isolation:** the producer keeps its working context across iterations; the evaluator runs clean each round (it judges the current output, not the producer's reasoning). This mirrors the review-gate split — generation and judgment stay separate agents.
- **Tiering:** producer per the work; evaluator JUDGE.
- **Cheap-proof gate (Step 4):** usually **skip** unless each iteration is itself expensive; the loop cap is the cost bound.
- **Execution:** sequential rounds with a hard iteration cap; stop on the criterion or the cap, and report residuals honestly rather than spinning. Note: a pure single-artifact build-evaluate-improve loop is what `delegated-review-loop` already does — use the loop shape here only as *one phase* inside a larger heterogeneous run, not as the whole task.
- **Aggregation:** the final iteration's output.

## Recursive decomposition

A phase cannot be fully planned up front; it surveys and emits sub-phases the orchestrator then spawns.

- **Isolation:** the spawning phase returns a *plan* (sub-phase definitions and input paths), not the sub-results; the orchestrator runs the sub-phases under the same contract.
- **Tiering:** the survey/decompose phase is often JUDGE (it makes structural decisions); the spawned sub-phases per their own kind.
- **Cheap-proof gate (Step 4):** **apply** once the recursion reveals a wide expensive frontier.
- **Execution:** the orchestrator expands one level at a time, re-entering the workflow for the sub-phases. Cap recursion depth to avoid runaway expansion.
- **Aggregation:** synthesize up the tree — each level reduces its children before returning to its parent.

## Nesting

Real runs combine shapes: a fan-out whose every item is a small linear pipeline, or a DAG with one node that is an iterative loop. Nesting does not change the contract — each nested unit still runs as isolated phases under one run-id, and the cheap-proof gate still applies wherever a wide expensive step appears. Keep the nesting shallow and legible; deep nesting is usually a sign the decomposition (Step 1) cut the phases at the wrong boundaries.
