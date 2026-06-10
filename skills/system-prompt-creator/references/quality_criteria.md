# Quality Criteria

Quality standards and readiness checklists for system prompts. Passing the checklist below means a
prompt is **ready for evaluation**, not certified production-ready — see the note at the end.

## Readiness Checklist

```yaml
- check: Task Clarity
  criteria: Is the task to be performed by the model described without ambiguity?
- check: Output Definition
  criteria: Are the form, structure, and length of the output specified?
- check: Scope Limitation
  criteria: Is the range within which the model should respond clearly bounded?
- check: Fallback Handling
  criteria: Is the response defined for inputs that cannot be processed?
- check: Reproducibility
  criteria: Are decision rules, tie-breaks, and format constraints explicit enough that no
    output-shaping choice (format, length, label) is left for the model to improvise per run?
- check: Variable Separation
  criteria: Are dynamic inputs separated into variables without hardcoding?
- check: Self-Containment
  criteria: Can the task be performed using only the prompt without external explanation?
- check: Disambiguation (labeling/extraction)
  criteria: For classification/routing/extraction prompts, are out-of-scope inputs guarded to the
    fallback value AND ambiguous or multi-signal inputs resolved by an explicit dominant-signal
    tie-break (stated in the prompt, not left to the model to infer)?
- check: Untrusted Input Isolation
  criteria: When a variable carries end-user or third-party text, is it wrapped in explicit
    delimiters with an instruction that its content is data to process, never instructions to
    follow? (See the Guardrails block in prompt_structure.md.)
```

## Quality Degradation Patterns

```yaml
- pattern: Ambiguous Task
  problem: "Write a good article" → Model interprets arbitrarily
  fix: Specify concrete verbs + length + target
- pattern: Undefined Output
  problem: Output format changes every time
  fix: Specify structure/format/length
- pattern: Excessive Constraints
  problem: "Listing only 'Do not...' → Unclear what the model can do"
  fix: Prioritize positive instructions; use constraints only for safety
- pattern: Unbounded Scope
  problem: Model generates freely from all training data → Hallucination
  fix: "Only within the scope of the provided input"
- pattern: Missing Examples
  problem: Conveying complex output patterns through explanation only
  fix: Add 2–5 input-output examples (see prompt_structure.md — start zero-shot first)
- pattern: Erroneous Examples
  problem: Typos/logic errors in examples → Model learns error patterns
  fix: Directly verify examples before including them
```

## Disambiguation Rules (classification / extraction / labeling prompts)

When a generated prompt assigns a label, category, or fixed-schema field, ambiguous or adversarial
inputs cause errors unless the prompt states the tie-break **explicitly** — a strong model will not
reliably infer it. For these prompts, encode the following rules in the prompt itself:

- **Scope guard (required — distinct from the generic fallback)**: a bare "if it doesn't fit any
  category → Other" catch-all is NOT enough, because it misses input that *keyword-matches a category
  but is out of scope*. Add an explicit line mapping out-of-domain input to the fallback **even when
  it contains a category trigger word**, and keep it even in a "tight" prompt — it is one sentence.
  Template to adapt: *"If the message is not about &lt;this product/service&gt;, output &lt;fallback&gt;
  even if it mentions &lt;trigger words like refund, charge, account, login&gt;."* e.g. a "refund"
  request for an unrelated or physical purchase → `Other`, not `Billing`.
- **Classify by the reported subject, not surface keywords**: with multiple cues, decide on the
  actual symptom/subject. e.g. "the upload finished but playback is a black screen" is a *playback*
  issue despite the word "upload".
- **Dominant-signal tie-break for mixed input**: when signals conflict, state which wins. For
  sentiment, an actionable defect/complaint governs over incidental praise (praise + damage →
  negative). For a "main attribute", choose what the author is actually evaluating; a number or term
  that is only context (e.g. an "$18" mention inside a taste review) is **not** the attribute.
- **Reserve `neutral` / `none`** for genuinely flat input — do not let it absorb ambiguity.

Encode these as explicit rules in the prompt, then confirm they hold on adversarial inputs with an
eval — see [evaluation.md](evaluation.md).

## Single vs. Multi-Prompt Decision Criteria

A multi-prompt architecture is needed **only when a single system prompt cannot solve the
task**. Failure signals: an intermediate artifact is consumed or retried independently by an
external system, the steps require instructions that conflict within one prompt, the context
budget is exceeded, or a measured eval shows a single prompt underperforming. Each added prompt
costs latency, money, and error propagation — the burden of proof is on splitting.

**Over-splitting guard**: N output fields from one analysis of one input (e.g. sentiment +
attribute + note from a single review) is **one prompt with an output schema** — "multiple
aspects" alone never justifies a split.

Pattern signals (apply only after the gate above says a single prompt is insufficient):

- **Task can be completed with a single role**: Single
- **Input → Output is a single transformation (even with multiple output fields)**: Single
- **Intermediate transformation steps exist (A→B→C)**: Multi: Sequential
- **Independent perspectives whose outputs are consumed separately**: Multi: Parallel
- **Processing differs based on the input type**: Multi: Conditional
- **Iterative draft → review → revision cycle is needed**: Multi: Iterative
- **General principles must be extracted before the main task**: Multi: Step-back
- **Input must be split into chunks, processed independently, then merged**: Multi: Fan-out/Fan-in

This list is the summary; the canonical walkthrough is the Architecture Design Process in
[multi_prompt_architecture.md](multi_prompt_architecture.md).

## Principles for Writing Instructions

- **Positive First**: "Do X" > "Don't do Y"
- **Start with a Verb**: Analyze, Classify, Extract, Generate, Summarize, etc.
- **Specific Length**: "3 items", "2 paragraphs", "Within 100 characters"
- **Processing Order**: "First perform A, then perform B based on the result"
- **Scope Specification**: "Only within the given text", "Based on the data below"

## Methods for Ensuring Output Quality

```yaml
- method: Enforce Structured Format (JSON, YAML)
  effect: Improves consistency of machine-readable output
  when: During programming integration
- method: Use API-level schema enforcement (Structured Outputs / strict function calling)
  effect: Guarantees valid structure, enums, and required keys more reliably than asking for
    JSON in the prompt
  when: Production integrations that must parse the output programmatically
- method: Provide Schema
  effect: Strictly enforces output structure
  when: When outputting complex structures
- method: Include Examples (Few-shot)
  effect: Maximizes consistency through pattern learning
  when: When outputting unstructured patterns
- method: Specify Length
  effect: Prevents unnecessarily long responses
  when: Always recommended
```

> A generated prompt is only "production-ready" once it has been measured against a test set,
> not when the checklist above passes. See [evaluation.md](evaluation.md) for the success
> criteria, dataset, grading, baseline, and regression loop.
