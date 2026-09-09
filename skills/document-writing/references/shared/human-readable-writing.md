# Human-readable writing

Use this reference for substantial creation, rewriting, and review. Readability is not decoration; it is whether the intended reader can find the point, build the right mental model, and take the intended action without rereading.

## Evaluation dimensions

### Immediate orientation

- State the document's purpose and reader outcome near the beginning.
- Put the conclusion, recommendation, governing rule, or promised result before supporting detail when the document type allows it.
- Make scope and audience visible before nuance.

### Scanability

- Use descriptive headings that reveal the argument or workflow.
- Keep one main idea per paragraph.
- Prefer short lists or tables for repeated fields and exact comparisons.
- Do not fragment simple prose into excessive headings or bullets.

### Information order

- Order content by the reader's task, not by the author's discovery process.
- Explain prerequisites before dependent steps.
- Place evidence before interpretations that rely on it.
- Keep exceptions near the rule or step they modify.

### Concreteness

- Replace vague abstractions with examples, values, observable results, or counterexamples when useful.
- For action documents, show what success looks like.
- Define unfamiliar terms once and use the same term consistently afterward.
- Match prose to the user's primary language. In Korean prose, when an unfamiliar concept has an established Korean term, introduce it once as `한국어 용어(English term)` and use the Korean term consistently afterward.
- Keep identity- or machine-significant text in its canonical form: product and feature names, code, commands, paths, identifiers, protocol/API/format tokens, schema fields, literal values, exact logs and quotations, and required template contracts. Do not translate or normalize them.

### Economy

- Remove repeated conclusions, throat-clearing, and template filler.
- Omit optional sections that provide no reader value.
- Keep necessary nuance, limitations, and safety conditions even when they make the document longer.

## Evidence-preserving editing examples

These are illustrative inputs, not claims about a real system. Use the [drafting and revision sequence](drafting-and-revision.md#edit-prose-then-check-meaning) to review content before polishing and recheck meaning afterward.

### Keep an observation within its evidence

- Supplied evidence: during a pilot, some participants completed tasks faster; the cause was not established.
- Before: "The tool makes users faster."
- After: "Some pilot participants completed tasks faster; the pilot did not establish whether the tool caused the change."
- Why: the revision restores the observed population and uncertainty instead of making an unsupported general causal claim.
- Limit: do not invent a percentage or a wider population to sound concrete. Broader claims require additional evidence.

### Preserve the condition for permission

- Supplied rule: engineers may use production access only after manager approval.
- Before: "Engineers are permitted to use production access only in cases where approval has first been obtained from their manager."
- After: "Engineers may use production access only after manager approval."
- Why: shorter wording retains both permission and its prerequisite.
- Limit: deleting "only after manager approval" would change the policy. Other roles or emergency exceptions require their own supporting authority.

### Connect an action to a supplied result

- Supplied instructions: once the server is running, request `GET /health`; the expected response is `{"status":"ok"}`.
- Before: "Check that the server works."
- After: "Once the server is running, request `GET /health` and confirm that the response is `{"status":"ok"}`."
- Why: the reader can identify the starting condition, action, and observable result from supplied information.
- Limit: this confirms the documented health check, not every application feature. Do not derive an unverified shell command or invent recovery steps.

## Human review rubric

Rate each dimension as strong, acceptable, or weak:

1. A reader can identify the purpose and main point from the opening.
2. A reader can scan headings and predict where information lives.
3. Paragraphs and bullets carry one clear responsibility.
4. The order matches how the reader understands or acts.
5. Examples, expected results, and exceptions are concrete.
6. Terminology is consistent and unexplained jargon is limited.
7. The document avoids repetition and empty structure.
8. The ending leaves the reader with the intended understanding, action, decision, or next step.

Treat these as qualitative criteria. Do not turn subjective prose quality into arbitrary mechanical assertions.
