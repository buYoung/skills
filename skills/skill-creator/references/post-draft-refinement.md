# Post-Draft Refinement

Use this pass after the first complete draft and before the existing test-case and evaluation workflow. Its purpose is to explore independent improvements to one draft without repeating intake, research, or full evaluation for every candidate.

## Entry and limit

- Begin with a coherent package: `SKILL.md` and every reference, script, or asset its intended workflow needs. Resolve missing user-owned requirements before branching.
- A supplied complete draft is a valid starting point. Review its purpose and constraints, then use it directly.
- Run one round per requested skill-creation or improvement task, with five candidates unless the user specifies another count. Do not restart the round after integration, evaluator feedback, or ordinary follow-up edits. A new round requires a new user request.
- This pass belongs to the coordinator. Candidate authors do not invoke this workflow recursively, launch other candidates, run the full evaluation loop, or start a separate description-optimization loop.
- If independent agents are unavailable, explain that limitation. Do not represent sequential work by the same author as independent candidates or silently claim the requested pass completed.

## Freeze the shared input

Record a compact refinement brief outside the produced skill package. Include the requested purpose, activation and output expectations, scope, constraints, available source material, and common review criteria. Derive these from the request and the draft; do not prescribe a preferred solution.

Separate confirmed user requirements from design choices made in the draft. Define the common criteria in this brief once, using these questions to make them specific to the task:

- **User commitments**: Do instructions, exceptions, fallbacks, templates, or examples permit behavior or output the user excluded, or omit something they required? Judge the delivered result, including its contents, rather than only its label or location.
- **Instruction consistency**: Can the instructions and linked resources work together from activation to output? Check that a later check or fallback does not undo a required transformation or contradict an earlier decision.
- **Preservation and change**: What must remain accurate or exact, and what may need rewriting, removal, or restructuring to fulfill the task? Limit preservation rules to the necessary invariants so they do not block the intended work.
- **Constraint basis**: Is each mandatory restriction required by the request, an applicable source, or a concrete need of the task? Keep optional techniques and defaults adaptable to context.

Label source summaries as partial and retain the original locations (file or URL, section or page) and the range actually checked. An omission from a summary does not establish that the original source lacks a claim.

Snapshot the complete draft package and its required input material. Identify the version with a commit or file hashes. Use separate worktrees when the relevant files are tracked, or separate directory copies of the same snapshot otherwise. A commit alone does not capture untracked or uncommitted draft content.

Place refinement artifacts under `<skill-name>-workspace/refinement-1/`, separate from `iteration-N/eval-*` results. Give each candidate its own package and report paths. Keep the shared draft read-only. Never place refinement workspaces inside the final package.

Use a fresh conversation context for each author. Provide the same brief, snapshot, and source material; do not forward the coordinator's conversation, anticipated answer, other candidates, intermediate reports, or selection opinions. Use equivalent model and tool settings where possible and record differences that affect comparability. File isolation does not establish context isolation.

## Assign the candidates

Launch independent authors in parallel when capacity permits. If capacity is lower than the candidate count, use isolated batches without sharing earlier results. Do not silently reduce the requested count. The coordinator handles the shared assignment and result collection; it does not coach individual designs or reconcile candidates while they are being written.

Use this bounded assignment, replacing the paths and brief:

```text
Role: candidate author for one post-draft refinement pass.

Shared brief: <path>
Read-only draft package: <path>
Common source material: <paths>
Your writable candidate package: <path>
Your report: <path outside the candidate package>

Revise the supplied draft once into a coherent skill that meets the shared
brief. Use its common review criteria to check the complete candidate,
including linked resources. Change only your assigned candidate package.

Do not delete or reclassify content solely because a source summary omits
it. Flag the claim and original location for the coordinator to verify.
Distinguish factual corrections from editorial choices. Do not change
scope solely because the user's examples omit an existing boundary.

Make your own decisions. Do not read other candidates or reports, inherit
the coordinator's conversation, interview the user, or expand the scope.
Do not invoke skill-creator's management workflow, spawn further authors,
run model-based evaluations, start a feedback loop, or start the separate
description-optimization loop.
You may perform relevant existing local structural or deterministic checks.

Return the complete candidate package and a concise report containing:
- changed files and intended behavioral differences;
- reasons and material tradeoffs;
- original-source locations checked for factual corrections, or unresolved
  source questions; the user intent supporting any scope change;
- checks actually performed, their results, and remaining uncertainty.

If the draft already meets the brief, return it unchanged with your reason.
Keep process reports and candidate-management instructions outside the
produced skill, unless that process is itself the requested skill behavior.
```

If a common requirement changes, establish one revised input version before comparing affected candidates. Do not compare candidates silently built against different requirements. Record incomplete or failed candidates as such; a missing report is not a successful candidate.

## Compare and integrate

After all assignments finish or are explicitly accounted for, inspect the complete candidate packages against the brief's common review criteria. Use reports to locate changes, then verify their effects in the files. Also assess clarity, completeness, unnecessary repetition, avoidable steps, actual verification evidence, tradeoffs, and unresolved assumptions.

Treat repeated suggestions as signals to inspect, not votes or proof of quality. A required contract failure is not offset by a high average score. Candidate self-reports are evidence about their work, not independent performance measurements.

Before accepting changes, resolve these questions where they arise:

- **Source-dependent changes**: for proposed factual deletions, weakened claims, or source reclassifications, check the cited original and nearby context. Reuse that check across candidates instead of repeating research for every author. If access is unavailable, record the uncertainty and avoid accepting a supposed correction based only on a summary's omission. Editorial cuts remain valid when justified by relevance and preservation of required meaning; do not describe them as factual corrections.
- **Scope changes**: compare disagreements with the user's stated intent, including the reasoning from minority candidates. An omitted item in a non-exhaustive list is not a direction to broaden or narrow activation. Explicit limits on what may be changed still apply when the skill activates.

Select a coherent base and incorporate only compatible changes supported by the review. A text merge alone does not establish behavioral consistency. No change, or retaining the shared draft, is valid when the candidates provide no justified improvement.

Save the integration decision outside the produced package. Name accepted and rejected changes, their reasons, source candidates, and remaining limits. For disputed facts or scope, include the evidence checked and why it resolves the disagreement; leave unresolved changes out of the integration unless they can preserve the required behavior and accurately express the uncertainty. Keep the comparison proportional; do not create separate grading agents or five full evaluation loops for this drafting pass.

## Return to the existing workflow

Check the integrated package's frontmatter, references, and any changed executable behavior with the relevant existing checks. Apply the brief's common criteria once across the final activation-to-output path, including linked resources. Candidate checks do not prove the integrated combination works.

Continue `Test Cases` and the existing evaluation workflow once for the integrated package. For an existing-skill improvement, retain the original pre-change baseline; for a new skill, retain the existing no-skill baseline. If the user requested creation/refinement only, stop at that boundary and report that execution quality remains unmeasured.

Refinement reports are not `grading.json` or benchmark runs. Keep them separate from the two-configuration benchmark interface. Later evaluation may revise the integrated skill through the existing loop, without restarting candidate generation.

Record token usage and timing only when the host supplies them. Preserve available input, output, cache, and subagent usage fields and their source. If unavailable, say so; do not substitute characters, file counts, or estimates for measured tokens. Distinguish drafting/refinement cost from evaluation cost, and do not claim an efficiency gain from candidate agreement or structural checks.
