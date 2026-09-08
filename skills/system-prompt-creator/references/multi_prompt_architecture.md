# Multi-Prompt Architecture

Default to one prompt. Multiple output fields or the possibility of decomposing a task do not
alone justify multiple prompts. Honor explicitly requested stages, independent outputs,
branches, and bounded revision loops without demanding evidence that one prompt failed.

## Choose from the Requested Flow

| Requested behavior | Configuration | Boundary to specify |
|---|---|---|
| One transformation, possibly several fields | Single prompt | Runtime input → final output |
| Ordered stages whose outputs feed the next | Sequential pipeline | Producer output → consumer input |
| Independent views of the same input | Parallel split | Shared input and separate outputs |
| Route to distinct handlers | Conditional branch | Allowed routing values → exact handlers |
| Draft, critique, revise repeatedly | Iterative refinement | Feedback contract and bounded termination |
| Explicit principles extraction before a task | Step-back pipeline | Principles and evidence → main task |
| Split input, process pieces, merge | Fan-out / fan-in | Chunk identity/context → merge rules |

A specialized domain or a request for "high quality" does not itself require step-back or
iteration. When several structures are explicitly needed, compose them and show the data flow.
Ask only for missing consequential decisions, not for the user to select a pattern name.

## Shared Contract for Every Boundary

For each stage and edge, define:

- Required inputs, field names/types, units, allowed values, and any optional values.
- Output fields and semantics, with the exact mapping to the next stage's inputs.
- Original request and source evidence the consumer still needs; do not lose necessary context.
- Validation responsibility and what happens to missing, invalid, or failed upstream output.
- Error representation and propagation to the final caller, including whether later stages run.
- Which decisions are model instructions and which must be enforced by the host application.

Preserve existing schemas. If exact integration or material error behavior is missing, ask for
it. If the user delegates a new contract, design and disclose it. Do not add a confidence field,
an error object, a default category, or an escalation path solely because an example uses one.
Treat stage output as data under the receiving stage's instructions, not as higher authority.

For programmatically parsed output, follow the host's required format, commonly JSON. If the
next model reads prose or structured text directly, choose for clarity and data shape using
[data_format_selection.md](data_format_selection.md). Reading-format benchmarks do not prove
generation/parsing reliability. API schema constraints require a supported target and separate
configuration; see [model_guidance.md](model_guidance.md).

## Pattern Details

### Sequential Pipeline

```text
runtime input → A output → B output → C final output
```

Give each requested transformation its own prompt and explicit contract. Propagate validation
failures according to the agreed policy instead of silently filling missing facts. For example,
"extract → normalize → format for our existing quoting API" still needs that API's schema and
normalization/error rules; the architecture does not supply missing contract details.

### Parallel Split

```text
shared input → B1 → independent result 1
             → B2 → independent result 2
```

Specify that all branches receive the same input and do not consume each other's answers.
Keep their requested criteria distinct. Add an aggregator only if requested or necessary for a
specified final output. Define how missing or failed branches appear to the final consumer.

### Conditional Branch

```text
runtime input → router → allowed label → corresponding handler
```

Define the label-to-handler mapping and any priority for overlapping conditions from the user's
policy. Every possible router result must have defined handling. Do not automatically add
`OTHER` or a human-escalation route. If unmatched/ambiguous input has no defined behavior and
matters for this task, ask for it. Handler knowledge bases or business policies must be supplied
as fixed content or explicitly required runtime inputs, not invented.

### Iterative Refinement

```text
request → writer → draft → critic → verdict + feedback
                       ↑                 |
                       └── revision ─────┘
```

Specify the writer's original and revision inputs: original request, latest draft, and critic
feedback. The critic uses the agreed rubric and returns a gradable verdict with concrete fixes.
The host controls iteration and preserves the latest draft and result.

Define all of the following from supplied rules or explicit design delegation:

- What counts as an iteration, including whether the initial draft is counted.
- Success/approval criterion and the finite maximum number of iterations.
- What is returned on approval, at the cap without approval, and after an invalid/failed stage.
- Whether any retry consumes the same iteration budget.

"Repeat until good" is incomplete. A cap bounds execution but does not guarantee convergence or
quality. Do not execute this designed pipeline while creating its prompts; any evaluation
simulation follows [evaluation.md](evaluation.md).

### Step-back Pipeline

```text
request + evidence → principles stage → request + principles + evidence → main stage
```

Preserve source grounding when passing principles. Do not let generated principles override
supplied facts or policy. Include this stage when requested or when the requirement establishes
a separate consumer/need for it; domain complexity alone is not enough.

### Fan-out / Fan-in

```text
input → chunks with IDs/context → per-chunk results → merge → final output
```

Define splitting ownership, boundary context, ordering, duplicate handling, completeness checks,
and missing/failed chunk behavior. Use user-supplied rules or disclosed delegated design.
Do not imply a prompt alone schedules concurrent calls or enforces context limits.

## Delivery and Evaluation

Deliver each prompt in a separate labeled block plus the shared contracts and necessary host
instructions. Check each producer-consumer pair, branch, and stop path. Derive cases for stage
behavior and end-to-end output, including errors and iteration limits. Keep generated prompts
and designed orchestration distinct from actual execution; no run is implied by the diagram.
