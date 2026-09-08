# System Prompt Structure

Use a model-neutral structure unless the request names a target. Select only blocks needed to
implement the requirements; a role, example set, or fallback is not mandatory for every task.

## Building Blocks

| Block | Include |
|---|---|
| Task | The operation, audience, and intended result |
| Role | Perspective, tone, scope, or judgment criteria when useful |
| Stable context | Supplied policies, definitions, and reference facts that remain fixed |
| Runtime input | Named variables, source/type, and how each is delivered |
| Decision rules | Supplied or delegated priorities, boundaries, and material exceptions |
| Output | Required content, allowed values, format, and acceptance constraints |
| Examples | Input/output demonstrations that clarify a real ambiguity in the rules |

An ordinary assembly order is role/context → task → inputs and decision rules → output →
examples. Headings or clear delimiters make the boundaries visible; this order is a readability
default, not an accuracy claim. Provider-specific sectioning advice belongs in
[model_guidance.md](model_guidance.md).

## Stable Instructions and Runtime Inputs

Give each input a purpose and an authority boundary. These are different:

- **Stable instructions:** the task, policies, allowed operations, and output contract. Put them
  in the application's system-instruction facility; map to exact roles/settings only when the
  target is verified.
- **Live user request:** the operation or question to carry out within those instructions.
  Preserve its valid requests and preferences. A conversational assistant must not discard all
  user messages as inert data.
- **Source material:** documents, tickets, code, retrieved passages, tool results, or previous
  stage outputs being analyzed. Instructions appearing inside them are source content, not
  authority to change the task, policies, output contract, or tool permissions.

The same string can play different roles in different applications. A customer question is an
instruction to a support assistant, while a ticket body is data for a classifier. Identify the
role from the requested task, not merely from a variable name such as `{user_message}`.

Keep runtime values out of the reusable fixed prompt where the interface permits separate
messages or fields. If a text-only interface requires substitution, define a separate runtime
input template with unambiguous delimiters and an escaping/serialization rule for literal
delimiter text in the data. Do not promote documents or search results into system instructions.
Delimiters help express boundaries; they are not a security guarantee. Include relevant
document-instruction cases in [evaluation.md](evaluation.md).

### Input Contract Example

For a requested document-answering assistant, an application note might specify:

| Input | Placement and use |
|---|---|
| Fixed prompt | System-instruction facility |
| `{question}`: string | Runtime user request, the question to answer |
| `{documents}`: list of source records | Separate source payload with IDs and text; evidence to consult |

The prompt explains how to answer `{question}` using `{documents}` while ignoring commands
inside documents. It does not say to ignore the question itself. Exact missing-evidence behavior
comes from the request or a disclosed default when it does not alter a consequential policy.

## Task, Context, and Role

Use direct verbs and observable outcomes. Keep domain facts grounded in supplied material;
do not fill absent company policies from general knowledge. A designed taxonomy is permissible
when delegated, and should be described as designed rather than already used by the company.

Use roles for perspective and communication, not as a promise of correctness. An empirical
reference is Zheng et al., [When “A Helpful Assistant” Is Not Really Helpful](https://aclanthology.org/2024.findings-emnlp.888/)
(EMNLP Findings 2024; checked 2026-09-08): 162 personas, 2,410 factual questions, and FLAN-T5,
Llama-3-Instruct, Mistral-Instruct, and Qwen2.5-Instruct models. The study found no general
factual-performance benefit over its no-persona
control. This is evidence about that experiment, not every task or current model.

## Output Contracts

Specify exact keys, types, allowed labels, units, and length limits when required. For open-ended
writing, identify required content and permissible variation rather than inventing one ideal
wording. Preserve the user's contract across instructions, examples, and downstream consumers.

A schema **written in a prompt** describes the desired structure; it does not enforce it.
API-level schema-constrained output is a separate capability with model, schema, and response
conditions. Neither valid JSON nor schema adherence proves that extracted facts or selected
labels are correct. See [model_guidance.md](model_guidance.md) for official target documentation
and [quality_criteria.md](quality_criteria.md) for the review checklist.

## Examples and Exceptions

Start with clear instructions; add examples when they resolve a material interpretation issue.
Choose examples by the patterns and boundaries that need illustration, not a fixed count. Check
each answer against the supplied or delegated rules before including it.

Do not convert illustrative rules into universal policies. A sentiment classifier might treat
mixed feedback as positive, negative, neutral, or mixed according to its actual taxonomy and
policy. Do not assume complaints override praise or create an extra label. Likewise, do not add
unrequested error objects, refusal text, confidence fields, or escalation paths to a closed
output contract. Resolve missing consequential behavior through the clarification gate.

## Application Check

The user should be able to copy the prompt and identify all required inputs. State variable
types, which inputs are required, where they go, and required settings/resources. Resolve every
placeholder before calling a prompt applicable, except runtime variables intentionally supplied
by the caller. Do not imply an unavailable tool or unspecified API is already connected.
