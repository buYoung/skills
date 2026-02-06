# Quality Criteria

Quality standards and checklists for production-ready system prompts.

## Production-Ready Checklist

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
  criteria: Does the structure produce consistent output for the same input?
- check: Variable Separation
  criteria: Are dynamic inputs separated into variables without hardcoding?
- check: Self-Containment
  criteria: Can the task be performed using only the prompt without external explanation?
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
  fix: Add 3–5 input-output examples
- pattern: Erroneous Examples
  problem: Typos/logic errors in examples → Model learns error patterns
  fix: Directly verify examples before including them
```

## Single vs. Multi-Prompt Decision Criteria

A multi-prompt architecture is needed when a single system prompt cannot solve the task.

- **Task can be completed with a single role**: Single
- **Input → Output is a single transformation**: Single
- **Intermediate transformation steps exist (A→B→C)**: Multi: Sequential
- **Processing the same input from different perspectives**: Multi: Parallel
- **Processing differs based on the input type**: Multi: Conditional
- **Iterative draft → review → revision cycle is needed**: Multi: Iterative

For multi-prompt design, refer to [multi_prompt_architecture.md](multi_prompt_architecture.md).

## Principles for Writing Instructions

- **Positive First**: "Do X" > "Don't do Y"
- **Start with a Verb**: Analyze, Classify, Extract, Generate, Summarize, etc.
- **Specific Length**: "3 items", "2 paragraphs", "Within 100 characters"
- **Processing Order**: "First perform A, then perform B based on the result"
- **Scope Specification**: "Only within the given text", "Based on the data below"

## Methods for Ensuring Output Quality

```yaml
- method: Enforce Structured Format (JSON, YAML)
  effect: Reduces hallucinations, ensures consistency
  when: During programming integration
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
