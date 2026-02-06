# System Prompt Structure

Building blocks and assembly order used when assembling a system prompt.

## Building Blocks

A system prompt is composed of a combination of the blocks below. Not all blocks are mandatory; select only the blocks needed based on the nature of the task.

```yaml
- block: Role
  role: Model's identity and expertise
  required: Recommended
- block: Context
  role: Domain background, terminology, and rules
  required: Case-by-case
- block: Task
  role: Clear description of the task to be performed
  required: Required
- block: Input Format
  role: Definition of the input data format
  required: When input exists
- block: Output Format
  role: Definition of the output form and structure
  required: Recommended
- block: Examples
  role: Demonstration of input-output pairs
  required: When pattern guidance is needed
- block: Guardrails
  role: Scope limits, error handling, and safety
  required: Case-by-case
```

## Assembly Order

```text
[Role]        → Who am I
[Context]     → What is the situation
[Task]        → What am I doing
[Input]       → What am I receiving
[Output]      → What am I outputting
[Examples]    → Showing how it's done
[Guardrails]  → What NOT to do / Exception handling
```

This order is designed to help the model build context cumulatively: "I am who → The situation is this → The task is this → The input is this → The output is this."

## Block Details

### Role

Assigning an identity to the model activates domain-specific vocabulary and perspectives.

```text
You are a [Title/Role] with expertise in [Expertise Area].
```

- The more specific the role, the deeper the response.
- If tone/style is important, specify it in the Role: "in a direct, technical style"
- If multiple perspectives are needed, separate primary and secondary roles.

### Context

Background information for the task. Unlike the Role, this changes dynamically per task.

```text
Context:
- [Domain Background]
- [Current Situation/Conditions]
- [Target User Characteristics]
- [Characteristics of Data to be Processed]
```

### Task

Describes the work to be performed. **Prioritize using positive instructions.**

```yaml
- method: Instruction (Positive)
  example: "Summarize into 3 items"
  priority: Use first
- method: Constraint (Negative)
  example: "Do not include personal information"
  priority: Only for safety/format requirements
```

Starting with a verb makes it clear: Analyze, Classify, Compare, Create, Extract, Generate, Identify, List, Parse, Rank, Summarize, Translate.

### Input Format

Specify the format when the input is structured. Using variables increases prompt reusability.

```text
Input:
- Type: [text / JSON / code / table]
- Variable: {input_text}
```

### Output Format

Specifying the output structure reduces hallucinations and ensures consistency.

- Providing a Schema can enforce the output structure.
- For format selection when including data within a prompt, refer to [data_format_selection.md](data_format_selection.md).

### Examples

Including input-output examples helps guide the model's output pattern.

- **Quantity**: At least 3–5; more for complex tasks
- **Diversity**: For classification, include each class evenly and mix the order
- **Edge Cases**: Include methods for handling unstructured input
- **Quality**: An error in a single example can contaminate the entire output

### Guardrails

Scope limits and exception handling. Concentrated placement of Constraints here.

- **Scope**: "Respond only within the scope of the provided data"
- **Fallback**: "If unable to judge, return 'Indeterminable'"
- **Safety**: "Respond in a respectful manner"

## Minimal vs Full Prompt

### Minimal (Simple Tasks)

```text
[Role] + [Task] + [Output Format]
```

### Standard (Most Tasks)

```text
[Role] + [Context] + [Task] + [Output Format] + [Guardrails]
```

### Full (Complex Tasks)

```text
[Role] + [Context] + [Task] + [Input Format] + [Output Format] + [Examples] + [Guardrails]
```
