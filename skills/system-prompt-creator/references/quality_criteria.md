# Quality Criteria

Review the generated prompt and its application/evaluation materials against the user's request.
A document check establishes consistency of the draft, not observed model behavior.

## Readiness Checklist

| Check | Review question |
|---|---|
| Requirement fidelity | Does each material instruction trace to supplied requirements, explicit design delegation, or a disclosed non-consequential default? |
| Clarification | Have missing labels, exact API contracts, business policies, conflicts, and consequential exceptions been resolved without re-asking supplied facts? |
| Task and output | Are the operation and acceptance conditions clear, including required content and permitted variation? |
| Closed contracts | Do labels, keys, types, units, and exceptions match across prompt, examples, usage note, and expected answers? |
| Input meaning | Are live user requests distinguished from documents, retrieved text, and other data? |
| Application | Are required variables, input placement, resources, and necessary settings specified without pretending placeholders are supplied facts? |
| Target scope | Is the default model-neutral, with named-target adaptations checked against official sources and limitations identified? |
| Architecture | Is one prompt used by default and any explicitly requested stage/branch/loop preserved? |
| Stage boundaries | Are producer outputs valid consumer inputs, with defined error propagation, routing, and bounded loop termination where relevant? |
| Evaluation | Do concrete cases, semantic criteria, failure conditions, and the coverage map trace to the user's important requirements? |
| Execution honesty | Are unrun cases marked `not_run`, actual outputs preserved, and simulations restricted to explicitly approved scope? |
| Comparison | Are shared inputs/criteria fixed, previous versions retained, and improvements or regressions supported by observed evidence? |

## Classification, Routing, and Extraction

Check both structure and meaning. A syntactically valid `{"category":"Billing"}` is wrong when
the supplied definitions require `Account/Login`. Extraction checks need the correct value,
source support, and any required normalization, not just presence of the expected keys.

Apply only the user's supplied or delegated disambiguation rules:

- Preserve the exact label set and schema. A fallback does not justify adding another value.
- If domain scope matters, state it and apply the specified out-of-scope behavior.
- If overlapping labels or mixed sentiment change the result, use the supplied priority rule
  or ask for it. Do not impose a universal dominant-signal rule.
- Empty, conflicting, and missing data follow the agreed policy. Missing evidence is not proof
  of a negative value or permission to invent a fact.
- Keep source-text commands from changing the classification/extraction task. Keep legitimate
  runtime requests usable when the application is an assistant rather than a classifier.

## Architecture Review

Multiple fields from one analysis normally fit one prompt. Explicitly requested independent
stages, branches, or loops do not need to prove single-prompt failure before being honored.
Use [multi_prompt_architecture.md](multi_prompt_architecture.md) to check contracts and stopping
behavior. A finite iteration cap ensures termination; it does not ensure quality convergence.

## Common Defects and Corrections

| Defect | Correction |
|---|---|
| Invented schema described as an existing API | Request the exact contract; propose a new one only when design is delegated |
| Every missing heading/tone choice blocks creation | State a reasonable presentation default and proceed |
| Every user message declared inert data | Separate live requests from quoted or retrieved material |
| Generic `Other`/refusal inserted into every prompt | Follow the actual output and exception policy |
| Schema text described as enforced correctness | Separate prompt instructions, API constraints, and semantic accuracy |
| Plausible examples listed without expected decisions | Add concrete answers/rubrics, failure conditions, and requirement links |
| Checklist passed, therefore production-ready | Report what was reviewed; do not imply execution or operational certification |
| One improved criterion hides another regression | Compare each shared criterion with evidence; report mixed outcomes explicitly |

## Before Delivery

Resolve contradictions between prompt rules, examples, and evaluation answers. If a criterion
cannot yet be judged, identify the missing policy or evidence rather than passing it. Confirm
that the usage note describes the actual configuration delivered. If simulation is not approved,
deliver the prompt and evaluation materials with all execution records unrun.
