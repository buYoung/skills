---
name: delegated-review-loop
description: "Run a delegated build-review-improve loop when the user explicitly invokes this skill or explicitly asks to have sub-agents build and iteratively review the work. A worker sub-agent produces the artifact (with an optional scout sub-agent gathering context first), a task-matched panel of independent reviewer sub-agents critiques it in parallel, and the worker improves until the panel passes or the iteration cap is reached. All inter-agent content flows through documents in a per-session directory; the main agent orchestrates by passing file paths only and never writes the artifact itself. Applies to any deliverable: code changes, documents, designs, plans. Do not auto-trigger on ordinary requests; this is an explicit-invocation skill. Distinct from iterative-self-review, where the main agent holds the pen and a single blind verifier checks it."
---

# Delegated Review Loop

A quality loop built for users who want to describe what they need and get a result that has already survived scrutiny — without reading schemas, configuring panels, or supervising rounds. The main agent acts purely as an orchestrator: it delegates context-gathering to a scout, the work to a worker sub-agent, fans out an automatically-selected reviewer panel, routes findings back to the worker, and repeats until the panel passes.

Why the main agent never holds the pen: an author reviewing its own work in the same context inherits its own blind spots. Separating the worker (full task context, makes decisions) from the reviewers (clean context, see only the request and the artifact) keeps the critique honest, and keeping the main agent out of authorship keeps the orchestration judgment unbiased.

## When to use

Only when the user explicitly invokes this skill or explicitly asks for sub-agents to build and iteratively review/improve something. Never auto-trigger on ordinary implementation requests or on task completion.

If the user already has a finished artifact and only wants it verified — not rebuilt or improved by sub-agents — `iterative-self-review` is the right tool, not this one.

## Roles

| Role | Holds | Never does |
|------|-------|-----------|
| **Main agent (orchestrator)** | Session lifecycle, task classification, panel selection, finding merge, loop control, final summary | Write or edit the artifact; review it itself; inline document content into sub-agent prompts |
| **Scout sub-agent** (optional) | Read-only context gathering before the build | Edit anything; make implementation decisions |
| **Worker sub-agent** | Full task context; produces and improves the artifact | Grade its own work; talk to the user |
| **Reviewer sub-agents** | Clean context: task request + current artifact only | Edit anything; see the scout's notes, other reviewers' findings, or the worker's reasoning |

## Session directory and path-passing rule

All inter-agent content travels as documents inside one per-session directory under `.agents/agents-community/<session-id>/`, created by the main agent at the start and cleaned up by it at the end. The orchestration rule is strict and is what keeps the main agent's context lean:

- The main agent hands sub-agents **file paths only** — it never pastes document content into a prompt.
- Each sub-agent reads its inputs from the files itself and writes its output as a new document in the session directory, returning only the path.
- **Which paths the main agent hands to whom *is* the isolation contract.** A reviewer that receives the scout's notes or the worker's report path is no longer blind. The full layout and read-access matrix live in [session_protocol.md](references/session_protocol.md) — follow it exactly.

The deliverable itself (code, the actual document) lives at its real repository path; the session directory holds coordination documents only.

## Workflow

### Step 1 — Frame the task and open the session

Extract the substantive task request from the user's own words. If the invocation message itself is contentless (e.g., just the skill name), reconstruct the request from the user's earlier utterances — verbatim quotes only. Create the session directory per [session_protocol.md](references/session_protocol.md) and write the request to `task_request.md`. This file is immutable for the rest of the loop and is the one document every agent may read.

### Step 2 — Select the reviewer panel

Classify the deliverable (code / document / design or plan / mixed) and pick 2–4 review lenses from the roster in [reviewer_panel.md](references/reviewer_panel.md). Correctness and requirements-fit are always in; the rest depend on what the task actually risks. Don't pad the panel — every extra reviewer costs a full read of the artifact, so add a lens only when the task plausibly fails along it.

**Then, as a required action of this step — not a formality:** print the chosen panel to the user in one line (e.g., "리뷰어 패널: 정확성, 요구사항 충족, 단순성") **before spawning any sub-agent** (scout included). This line is one of only three things the user sees while the loop runs; skipping it leaves them watching an opaque, slow process with no idea what is happening. Selecting the panel silently and only revealing it in the final summary defeats the line's purpose. No further configuration dialog — defaults carry the rest.

### Step 3 — Scout gathers context, and the simplicity gate

If the task depends on context the worker would otherwise have to rediscover — an unfamiliar codebase area, related existing implementations, external constraints — spawn a read-only scout sub-agent first using the prompt in [worker_prompt.md](references/worker_prompt.md). It writes its findings to `research/context.md` and returns the path. Skip the scout for self-contained tasks; a one-file fix does not need a survey.

The scout's notes go to the **worker only**. Reviewers never receive this path — they verify reality with their own read-only tools, and feeding them the scout's framing would bias them toward the worker's assumptions.

**Simplicity gate.** A worker plus a multi-reviewer panel is heavy machinery, and spending it on a trivial task wastes the user's time and tokens. The complexity judgment happens at this step, on whichever path applies:

- Scout ran → its report ends with a complexity verdict (`simple` or `substantial`), judged per the criteria in its prompt.
- Scout skipped → the orchestrator judges directly, using the same criteria: the task is `simple` when it is a small, localized change with no new behavior, no trust-boundary contact, and no realistic way for a reviewer panel to find something a careful single pass would not.

When the verdict is `simple`, pause and ask the user with the question tool before spawning anything further — one question, plain language: this task looks simple; run the full build-review loop anyway, or handle it normally without the loop? If the user declines, stop the skill: delete the session directory and carry out the task as an ordinary request outside this skill. If the user approves, continue to Step 4 without asking anything again. `substantial` tasks never ask — they proceed directly.

### Step 4 — Worker builds

Spawn the worker sub-agent with the prompt in [worker_prompt.md](references/worker_prompt.md), handing it the paths to `task_request.md` and (if produced) `research/context.md`. The worker has normal tool access and full freedom in how it builds. It writes its report to `worker_report_0.md` and returns the path.

### Step 5 — Panel reviews in parallel

Spawn all reviewers in the same turn, one per selected lens, using the reviewer prompt in [reviewer_panel.md](references/reviewer_panel.md). Each reviewer receives exactly two paths — `task_request.md` and the artifact's real location — plus read-only tool access to inspect reality. No scout notes, no worker report, no other reviewers' output, no prior-round findings. Each writes its report to `reviews/<lens>_<round>.md` and returns the path.

### Step 6 — Merge and route

Read the panel's reports and merge them per [loop_rules.md](references/loop_rules.md): deduplicate overlapping findings, resolve contradictions, drop findings without evidence, classify each as blocker / major / minor. Write the merged result to `merged_findings_<round>.md`.

- Any blocker or major remains → continue to Step 7.
- Only minors remain (or nothing) → the panel passes; go to Step 8.

### Step 7 — Worker improves, panel re-checks

Hand the `merged_findings_<round>.md` path back to the **same** worker (continue it with SendMessage so it keeps its build context; if the original worker is unavailable, spawn a fresh one and additionally hand it the previous `worker_report_<n>.md` path so it inherits the prior decisions). The worker fixes or, with stated reasons, rebuts, and writes `worker_report_<n+1>.md`.

Then re-review in **focused mode**: each reviewer receives the path to its own previous review file and re-checks only its previously-flagged items plus a quick scan for newly-introduced breakage — not a full re-read. This keeps round 2+ cheap.

Loop back to Step 6. Maximum 3 improvement rounds; on hitting the cap, stop and report residuals honestly rather than spinning.

### Step 8 — Summary and session cleanup

Close with the short summary format in [loop_rules.md](references/loop_rules.md): what was built, what the panel caught and the worker fixed, what minor items remain, and how many rounds it took. Written for someone who will not read transcripts — no internal vocabulary, no schemas, in the user's language.

Then settle the session directory per [session_protocol.md](references/session_protocol.md): **delete it on a clean pass; preserve it and print its path in the summary on any other termination**, so the user can trace what got stuck.

## Defaults that keep this vibe-coder friendly

- Zero configuration: panel composition, scout activation, round cap, and severity handling are all automatic.
- The user sees at most three things: the one-line panel announcement up front, the simplicity-gate question (only when the task looks trivial), and the final summary.
- Minor findings never trigger another round — they ride along in the summary as "알아두면 좋은 것" items.
- If the worker and a reviewer disagree and the worker's rebuttal is reasonable, the orchestrator decides; it escalates to the user only when the disagreement changes what the user would receive.
- The session plumbing stays invisible: its path surfaces only when something went wrong and the trail is worth keeping.

## Reference files

| File | When to read |
|------|--------------|
| [session_protocol.md](references/session_protocol.md) | Step 1 and Step 8 — directory layout, read-access matrix, session naming, cleanup rules |
| [reviewer_panel.md](references/reviewer_panel.md) | Step 2 and Step 5 — lens roster, selection rules, reviewer prompt template |
| [worker_prompt.md](references/worker_prompt.md) | Step 3, Step 4, Step 7 — scout prompt, worker build prompt, improvement-round prompt |
| [loop_rules.md](references/loop_rules.md) | Step 6 to Step 8 — merge rules, severity definitions, termination, summary format |
