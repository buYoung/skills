# Orchestration template: the phase prompt and platform notes

The single most load-bearing mechanic in this pattern is that **every** phase sub-agent is spawned with the same role-boundary preamble. It is what stops the orchestrator from drifting into doing the work, and what stops each phase from assuming the orchestrator already did its prep. This file gives the generalized template and notes on binding it to a runtime.

## The role-boundary preamble

Open every phase prompt with a boundary line that states, explicitly, that the main agent only orchestrates and this phase owns the actual work:

```text
You are the sub-agent for the "<phase name>" phase only. The main agent orchestrates
and does no phase work, so the actual <investigation / production / run / evaluation>
for this phase is yours alone to perform. Do not assume the main agent has done any of
it for you.
```

Two reasons this line is not optional:

- It blocks the orchestrator from quietly absorbing phase work — the boundary is restated at every spawn, so drift has nowhere to hide.
- It blocks the phase from under-doing its job on the assumption that the orchestrator prepared something. Each phase starts from a clean, self-reliant footing.

## The phase prompt skeleton

Build each phase prompt as a specification, not a vibe. The structure mirrors house prompt style (role, objective, context, separated input, stepwise task, rules, output format):

```text
# Role
You are the sub-agent for the "<phase>" phase only. <role-boundary preamble>

# Objective
Produce <the one concrete output of this phase>.

# Context
- run-id: <id>
- what earlier phases established (one or two lines), if this phase builds on them

# Inputs (paths only — open them yourself)
- <path to each input document>

# Task
1. <step>
2. <step>
3. <step>

# Tier
<JUDGE | WORKER> — bound to <runtime setting>.

# Allowed tools / surface
- <only the tools this phase may use>
- forbidden: <anything that would break isolation or the phase's purpose>

# Output
- write to: <path under the run directory>
- schema: <the exact shape of the output document>

# Constraints
- Read inputs only from the paths above; do not pull in unrelated context.
- If something required is missing, stop and report what is missing — do not invent it.
- Return only a short status plus the output path, not the full content.
```

Keep the **output schema explicit** for every phase. A phase whose output another phase or the final report must consume needs a fixed shape, or the consumer cannot rely on it. Where the runtime supports enforced structured output, prefer it over asking for a shape in prose.

## Reviewer prompt variant

Reviewer sub-agents use the same skeleton with two changes: the objective is to *find* (improve, for the constructive lens; refute, for the adversarial lens), and a hard rule that they **do not decide accept/reject and do not edit anything** — they emit evidence-bearing findings only. See [review_gate.md](review_gate.md).

## Tool-permission defaults

A phase gets the **least tool surface that lets it do its job** — not the orchestrator's full surface. Fill each prompt's `Allowed tools / surface` block from these defaults, then remove anything the specific phase does not need:

- **Read-only phases** (investigate, evaluate, review) get read/search/inspect tools only — no edit, no write outside their own output document, no state-mutating commands.
- **Producing phases** get write access to their deliverable path and their output document, plus whatever their work needs — nothing broader.
- **Command-running phases** get exactly the command surface their task names; forbid arbitrary shell beyond it where the runtime allows scoping.
- **Secrets stay out of outputs.** No phase prints credentials, tokens, or full environment into its output document or status.
- **No exfiltration of run-internal material.** A phase must not send the run's inputs, intermediate outputs, or sensitive artifacts to an external service. The external-reviewer caveat in [review_gate.md](review_gate.md) is the canonical rule; if an external call is blocked by policy, record the block and do not route around it.

These are defaults that reduce blast radius and accidental leakage, not a hardened sandbox — bind them to whatever permission controls the runtime actually provides.

## Binding to a runtime (notes, not core logic)

The skill itself never names a spawn API or a model. Bind at the edge:

- **Spawn mechanism.** Whatever the runtime calls "run a sub-agent with this prompt." Some runtimes expose an explicit spawn/wait/close lifecycle for persistent agents; others expose a one-shot agent call that auto-isolates and needs no close; others expose a workflow primitive that fans out and gathers. Map "run a phase" and "close a phase" (SKILL phase_protocol lifecycle) onto whichever the runtime provides.
- **Parallel vs serial.** Independent fan-out items run concurrently; dependent phases run in sequence. Express this with the runtime's concurrency primitive; the *decision* (independent → parallel, dependent or load-bound → serial) is platform-agnostic and lives in SKILL Step 5.
- **Tier setting.** Bind JUDGE/WORKER to the runtime's model and (if present) deliberation controls per [tiering.md](tiering.md).
- **Paths.** The run directory and path-passing contract (phase_protocol) are runtime-agnostic — any runtime with a shared filesystem supports them.

Treat all of the above as substitutable bindings. The workflow, the isolation contract, the tier assignment rules, the two halts, and the re-versioning discipline do not change when the runtime does.
