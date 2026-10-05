# Reader-Centred Brief Writing

Use this reference when drafting, patching, and self-checking a saved single plan or a briefset parent and its children. The intended reader needs to execute or review the work without the author's conversation history.

This guidance applies the four principles described in the public overview of ISO 24495-1:2023. The rules below are applications to implementation briefs, not a claim of certification or a substitute for the full standard.

## Relevant: include what enables the work

- Lead each section with the outcome, condition, or action the reader needs most. Keep facts that determine scope, compatibility, execution, and acceptance.
- Remove author deliberations, exploration logs, repeated explanations, and incidental findings that do not change the work. Preserve required concerns and meaningful exclusions; clarity does not justify dropping them.
- Describe the task and its technical actors. Do not add agent assignments, model names, spawn counts, prompts, worktree logistics, or commentary about applying this writing style unless those details are themselves part of the requested deliverable.
- Include a brief reason when it prevents a wrong action or explains a necessary constraint. Do not fill sections with the history of how the author reached a decision.

## Findable: put information where the reader expects it

- Keep the required headings, labels, section order, and checklist structure. Use concrete titles and stage names that identify the result or work surface.
- Put current facts in `Current State`, actions in `Execution Plan`, stage completion under `Ends when`, and whole-work completion in `Acceptance Criteria`.
- Give each coherent obligation its own bullet. Use existing lists and white space to expose actions and conditions; do not turn a required field into a paragraph of unrelated instructions.
- Keep child-local details in the child. The parent carries cross-child starts, dependencies, shared constraints, conflict rules, and the combined completion result. Repeat only the constraints a child needs to stand alone.

## Understandable: make meaning explicit

- Prefer familiar words and specific verbs. Name the affected component, action, and result; avoid vague phrases such as “handle appropriately” or “update related logic”.
- Explain an unfamiliar task-specific term at its first useful occurrence. Preserve exact paths, identifiers, code, messages, units, thresholds, and contract terms.
- State conditions, negation, uncertainty, and obligation explicitly. Keep ordering words when they carry a dependency. Name the actor when two components could perform the action.
- Keep one main idea per sentence or fragment. Sentence length and reading-grade scores are not acceptance thresholds; judge whether the intended reader can recover the meaning.
- Caveman mode may use concise fragments, but the action, target, condition, and sequence must stay clear. Restore normal prose for a field or bullet when compression makes the reader infer any of them.

## Usable: let the reader act and know when to stop

- Make the first action and its entry point obvious. State required inputs, deliverables, handoffs, and replan conditions using the existing fields.
- Pair each check with its target and observable result. Distinguish inspected facts from an expected result that has not been verified.
- For briefsets, show which children can start together and the actual conditions that block a child. Default to concurrent independent work; do not create waiting rules to mimic the author's drafting order.
- In the save report, give the artifact path, outcome, actual validation result, and any unresolved decision or failure. Keep internal process details out of the artifact and report unless they affect the reader's next action.

## Review before handoff

Use the existing Stage 5.6 pass; do not create a new output section or separate review loop. Can the reader find the required information, explain the instruction without guessing, begin the right action, and recognize completion? If not, revise the affected wording or placement while preserving the content inventory and structural contract.

A self-check is an author assessment, not measured reader testing. Do not describe a structural pass or a self-check as proof of ISO conformity.

## Sources

- [ISO 24495-1:2023 overview](https://www.iso.org/standard/78907.html) — scope, languages, and technical-writing applicability.
- [International Plain Language Federation: ISO standard](https://www.iplfederation.org/iso-standard/) — public summary of the four principles.
- [International Plain Language Federation: plain language](https://www.iplfederation.org/plain-language/) — reader needs, wording, structure, design, and evaluation with readers.
