# Multi-Prompt Architecture

Defines architecture patterns for complex tasks requiring multiple system prompts.

## Table of Contents

- [Architecture Patterns](#architecture-patterns)
- [1. Sequential Pipeline](#1-sequential-pipeline)
- [2. Parallel Split](#2-parallel-split)
- [3. Conditional Branch](#3-conditional-branch)
- [4. Iterative Refinement](#4-iterative-refinement)
- [5. Step-back Pipeline](#5-step-back-pipeline)
- [6. Fan-out / Fan-in](#6-fan-out--fan-in)
- [Pattern Selection Matrix](#pattern-selection-matrix)
- [Inter-Prompt Data Contract](#inter-prompt-data-contract)
- [Architecture Design Process](#architecture-design-process)
- [Examples](#examples)

## Architecture Patterns

### Notation Legend

To avoid ambiguity, the structures in this section use the notation below.

- `A`, `B`, `C`: Generic prompt nodes executed in sequence or branches
- `S`: Step-back prompt node (extracts general principles before the main task)
- `B₁..Bₙ`: Multiple parallel prompt nodes of the same role/type
- `X`: Routing condition or classification result used for branching
- `Input`: Raw user/task input entering the architecture
- `Output`: Final result returned to the caller
- `intermediate_*`: Structured intermediate artifact passed between prompts
- `→`: Data flow between prompt nodes
- `[B, C, D]`: Parallel branches receiving the same upstream input
- `(loop)`: Iterative cycle that repeats until a termination condition is met

Prompt counts (`2~N`, `3~N`) indicate the number of distinct system prompts in the architecture template, not the number of runtime executions.

```yaml
- pattern: Sequential Pipeline
  structure: A → B → C
  prompts: 2~N
  use_case: Step-by-step transformation/processing
- pattern: Parallel Split
  structure: A → [B, C, D]
  prompts: 2~N
  use_case: Processing the same input from multiple perspectives
- pattern: Conditional Branch
  structure: A → if X then B else C
  prompts: 2~N
  use_case: Branching based on input conditions
- pattern: Iterative Refinement
  structure: A → B → A (loop)
  prompts: 2 (repeated)
  use_case: Quality improvement loop
- pattern: Step-back Pipeline
  structure: S → A (→ B optional)
  prompts: 2~N
  use_case: Working after activating background knowledge, then optional post-processing
- pattern: Fan-out / Fan-in
  structure: "A → [B₁..Bₙ] → C"
  prompts: 3~N
  use_case: Integration after distributed processing
```

## 1. Sequential Pipeline

The most basic multi-prompt pattern for sequentially transforming inputs.

### Structure

```text
Step 1: Input --> [Prompt A] --> intermediate_1
Step 2: intermediate_1 --> [Prompt B] --> intermediate_2
Step 3: intermediate_2 --> [Prompt C] --> Output
```

### Characteristics

- **Data Flow**: Unidirectional, linear
- **Role of each prompt**: Receives the output of the previous step as input and transforms it
- **Error Propagation**: Errors in early stages propagate to subsequent stages
- **Suitable Tasks**: Analysis → Transformation → Formatting, Extraction → Classification → Summarization

### Design Principles

- **Single Responsibility**: Each prompt performs only one transformation
- **Explicit Output Format**: Explicitly define the output format of each prompt to be used as input for the next
- **Error Boundary**: Include input validation at each step
- **Intermediate Format**: Structured formats (JSON, YAML) are recommended for intermediate data

## 2. Parallel Split

A pattern where multiple prompts process the same input simultaneously.

### Structure

```text
Input --> [Prompt B1] --> Output1
Input --> [Prompt B2] --> Output2
Input --> [Prompt B3] --> Output3
(all branches receive the same Input, executed independently)
```

### Characteristics

- **Data Flow**: 1:N branch
- **Role of each prompt**: Processes the same input from different perspectives/roles
- **Independence**: Each branch is independent of the others
- **Suitable Tasks**: Multi-persona interpretation, multi-language translation, multi-format generation

### Design Principles

- **Shared Input Contract**: All branch prompts receive the same input format
- **Role Differentiation**: Each prompt has a unique role/perspective
- **Output Independence**: Each output can be used independently

## 3. Conditional Branch

A pattern that branches into different prompts based on the characteristics of the input.

### Structure

```text
Step 1: Input --> [Prompt A: Router] --> category label
Step 2: Route by category:
  - Type X --> [Prompt B]
  - Type Y --> [Prompt C]
  - Type Z --> [Prompt D]
```

### Characteristics

- **Data Flow**: Conditional branching
- **Role of Router prompt**: Classifies input and selects the appropriate path
- **Suitable Tasks**: Specialized processing by input type, processing branches by complexity

### Router Prompt Design

```text
Classify the following input into one of these categories:
- TYPE_A: [description]
- TYPE_B: [description]
- TYPE_C: [description]

Return only the category label.

Input: {input}
Category:
```

## 4. Iterative Refinement

A pattern where two prompts execute alternately to gradually improve output quality.

### Structure

```text
Step 1: Input --> [Prompt A: Generator] --> draft
Step 2: draft --> [Prompt B: Critic] --> feedback
Step 3: Input + feedback --> [Prompt A: Generator] --> revised draft
Repeat Step 2-3 until termination condition (max N iterations or Critic approval)
```

### Characteristics

- **Data Flow**: Cyclic (Generator ↔ Critic)
- **Termination Condition**: Fixed number of iterations or Critic's approval
- **Suitable Tasks**: High-quality document generation, code review/correction, translation verification

### Design Principles

- **Generator Role**: Generates initial draft or revision reflecting feedback
- **Critic Role**: Evaluates quality and provides specific improvement points
- **Convergence**: Set an upper limit on the number of iterations (to prevent infinite loops)
- **Feedback Format**: Structured feedback (score + itemized comments)

## 5. Step-back Pipeline

A pattern that first reasons through general principles and then uses the results as context to perform specific tasks.

### Structure

```text
Step 1: Input --> [Prompt S: Step-back] --> general_principles
Step 2: Input + general_principles --> [Prompt A: Main Task] --> Output
Optional Step 3: Output --> [Prompt B: Post-Processor/Verifier] --> Final Output
```

### Characteristics

- **Data Flow**: 2-step sequential (abstract → concrete), with optional 3rd post-processing step
- **Role of Step-back prompt**: Extracts general principles/core elements of the domain
- **Role of Main prompt**: Performs specific tasks using the Step-back result as context
- **Role of Optional prompt B**: Reformats, validates, or quality-checks the main output when needed
- **Suitable Tasks**: Expert analysis, creative content generation, strategy development

## 6. Fan-out / Fan-in

A pattern that splits input for parallel processing and then integrates the results.

### Structure

```text
Step 1: Input --> [Prompt A: Splitter] --> [chunk1, chunk2, ..., chunkN]
Step 2: chunk1 --> [Prompt B] --> result1
        chunk2 --> [Prompt B] --> result2
        chunkN --> [Prompt B] --> resultN
        (all chunks processed independently with the same Prompt B)
Step 3: [result1, result2, ..., resultN] --> [Prompt C: Aggregator] --> Output
```

### Characteristics

- **Data Flow**: Split → Parallel processing → Integration
- **Suitable Tasks**: Large-volume text processing, multi-source analysis
- **Caution**: Potential context loss at split boundaries

## Pattern Selection Matrix

Guide for pattern selection based on requirements:

```yaml
- requirement: Step-by-step transformation required
  pattern: Sequential Pipeline
  rationale: Optimize each step independently
- requirement: Same data from different perspectives
  pattern: Parallel Split
  rationale: Specialized prompt for each perspective
- requirement: Diverse input types
  pattern: Conditional Branch
  rationale: Optimal processing for each type
- requirement: High output quality required
  pattern: Iterative Refinement
  rationale: Iterative quality improvement
- requirement: Complex domain analysis
  pattern: Step-back Pipeline
  rationale: Activate background knowledge
- requirement: Large-volume input processing
  pattern: Fan-out / Fan-in
  rationale: Parallel distributed processing
- requirement: Combination of patterns required
  pattern: Hybrid (Composite)
  rationale: Combine patterns as nodes
```

## Inter-Prompt Data Contract

Data transfer protocols between multiple prompts:

### Recommended Intermediate Data Formats

```yaml
- priority: 1st
  format: YAML
  use_case: Nested structure data (62.1% accuracy)
- priority: 2nd
  format: Markdown-KV
  use_case: 1D key-value data (60.7% accuracy)
- priority: 3rd
  format: JSON
  use_case: Cases requiring programming integration (50.3~52.3% accuracy)
```

### Data Contract Definition Pattern

```text
# Prompt A Output Contract
## Output Format: YAML
## Fields:
- analysis_result: string (summary of analysis result)
- categories: list[string] (classification results)
- confidence: float (0.0~1.0)
- details: map[string, string] (itemized detailed explanation)
```

## Architecture Design Process

Judgment criteria when designing a multi-prompt architecture:

```yaml
- step: 1
  question: Can the task be solved with a single prompt?
  decision: "Yes → Single prompt, No → Next"
- step: 2
  question: Can the task be decomposed into independent steps?
  decision: "Yes → Sequential Pipeline"
- step: 3
  question: Are multiple perspectives required for the same input?
  decision: "Yes → Parallel Split"
- step: 4
  question: Does processing differ based on the input type?
  decision: "Yes → Conditional Branch"
- step: 5
  question: Is iterative improvement of output quality required?
  decision: "Yes → Iterative Refinement"
- step: 6
  question: Is activation of domain expert knowledge required?
  decision: "Yes → Step-back Pipeline"
- step: 7
  question: Should the above patterns be combined?
  decision: "Yes → Hybrid"
```

## Examples

### Example 1: Code → Multi-audience Documentation

A 2-step architecture that analyzes code and transforms it into language understandable by QA/PMs/Designers.

```text
Architecture: Sequential Pipeline + Parallel Split

Step 1: [Prompt A - Code Analyzer]
  Input: Source code
  Output: Structured analysis (YAML)
    - functionality summary
    - data flow
    - UI interactions
    - business rules
    - edge cases

Step 2: [Parallel Split]
  Input: Step 1 output
  
  [Prompt B₁ - QA Translator]
    Role: Senior QA Engineer
    Output: Test scenarios, edge cases, regression points
  
  [Prompt B₂ - PM Translator]
    Role: Product Manager
    Output: Feature description, user stories, acceptance criteria
  
  [Prompt B₃ - Designer Translator]
    Role: UX Designer
    Output: Interaction flows, UI states, accessibility notes
```

### Example 2: Customer Inquiry Router

A conditional branch architecture that handles customer inquiries according to their type.

```text
Architecture: Conditional Branch

[Prompt A - Router]
  Input: Customer message
  Output: Category (BILLING | TECHNICAL | GENERAL | COMPLAINT)

[Prompt B₁ - Billing Handler]
  Role: Billing specialist
  Context: Pricing plans, refund policy
  
[Prompt B₂ - Technical Handler]
  Role: Technical support engineer
  Context: Product docs, known issues
  
[Prompt B₃ - General Handler]
  Role: Customer service representative
  
[Prompt B₄ - Complaint Handler]
  Role: Customer relations manager
  Context: Escalation policy, compensation guidelines
```

### Example 3: High-quality Document Generator

An iterative refinement architecture that generates high-quality documents through repeated improvements.

```text
Architecture: Step-back + Iterative Refinement

[Prompt S - Step-back]
  Input: Document topic + requirements
  Output: Domain principles, key aspects, quality criteria

[Prompt A - Generator]
  Input: Topic + Step-back output + (previous feedback if any)
  Output: Document draft

[Prompt B - Critic]
  Input: Draft + quality criteria from Step-back
  Output: Score (1-10) + itemized feedback
  Termination: Score >= 8 or max 3 iterations

Loop: A --> B --> A --> B --> ... --> Final Output
```
