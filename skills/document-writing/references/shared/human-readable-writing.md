# Human-readable writing

Use this reference for substantial creation, rewriting, and review. Judge the final text by whether its intended reader receives, finds, understands, and can use the information needed for the document's purpose.

## Basis and scope

This reference applies the four reader principles of ISO 24495-1:2023: provide relevant information, make it findable, make its meaning understandable, and make it usable for the intended outcome. The writing practices and review questions needed to apply them are included below.

These practices apply the principles within the selected document type's structure and requested operation; they are not a reproduction of the full standard or a conformity or certification assessment. Keep this review framework internal unless requested as a deliverable. Plain-language review complements the type's technical and accessibility checks.

## Reader outcomes

### Relevant: provide what this reader needs

- State the document's purpose and reader outcome near the beginning.
- Put the conclusion, recommendation, governing rule, or promised result before supporting detail when the document type allows it.
- Make audience, applicability, and material limits visible before nuance. Choose detail for the reader's starting knowledge and situation; an expert document need not use a beginner's vocabulary.
- Include necessary facts, conditions, and uncertainty even when readers may not know to ask for them. Remove repeated conclusions, throat-clearing, and optional template filler while retaining required coverage, evidence, limitations, and safety conditions.

### Findable: make the applicable answer easy to locate

- Use descriptive headings, labels, and link text that match the reader's task or lookup terms. Preserve required headings and stable lookup keys; add orientation within their established sections when needed.
- Order content by the reader's use, not the author's discovery process. Put prerequisites before dependent steps and evidence before interpretations that rely on it, while preserving meaningful chronology and the selected type's structure.
- Keep conditions, exceptions, and material limitations beside the claim, rule, or step they change. When detail belongs elsewhere, provide enough local context to avoid a misleading summary and a specific link to its authoritative owner.
- Use prose for connected explanation, numbered lists for an actual sequence, bullets for parallel items, and tables for genuinely comparable fields. Give links labels that reveal their destination rather than an unexplained "see above" or "see below".
- Do not fragment simple prose into excessive headings or bullets.

### Understandable: make the intended meaning explicit

- Prefer familiar words and direct verbs to vague abstractions and stacked nouns. Name the actor when supported and relevant; retain passive wording when the actor is unknown or the affected item is the useful focus. Do not invent responsibility to make a sentence active.
- Keep one main idea per paragraph. Split overloaded sentences when doing so clarifies the relationships, retaining the scope of conditions, negation, alternatives, and exceptions. Replace ambiguous pronouns with the relevant noun when readers could infer the wrong referent.
- Explain unfamiliar terms at their first useful appearance and use the same term consistently afterward. Retain necessary technical terms rather than replacing them with imprecise everyday synonyms.
- Match prose to the user's primary language. In Korean prose, when an unfamiliar concept has an established Korean term, introduce it once as `한국어 용어(English term)` and use the Korean term consistently afterward.
- Keep identity- or machine-significant text in its canonical form: product and feature names, code, commands, paths, identifiers, protocol/API/format tokens, schema fields, literal values, exact logs and quotations, and required template contracts. Do not translate or normalize them.
- Preserve obligations, permissions, recommendations, units, time boundaries, populations, and uncertainty. Plain wording must not turn permission into obligation or an observation into a causal claim.

### Usable: support the document's intended outcome

- At an action or decision point, connect the applicable condition to the supported action, choice, or consequence. Include a responsible role, timing, expected result, or recovery path only when supported and relevant; do not invent missing elements to complete a formula.
- For action documents, show what success looks like using supplied or verified observable results. Keep documented failure, stop, or escalation conditions beside the affected step.
- Use supported examples, values, or counterexamples when they resolve a real ambiguity. An example illustrates a governing rule; it does not silently broaden permission or define a new default.
- A summary, heading, table, or extracted step that stands alone must retain the material qualification that controls its meaning. A distant limitations section cannot repair a misleading local claim.
- Match use to the type: a reference supports exact lookup, a report supports interpretation within evidence limits, and a record supports faithful reconstruction. State an unresolved point's effect under the type's rules; do not manufacture a next action or approval request to make every ending actionable.

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

Use these qualitative questions within the selected type's review for the permitted scope:

| Outcome | Question to answer from the actual final text |
| --- | --- |
| Relevant | Does the text provide the necessary answer and its applicability, including material information the reader may not know to ask for? |
| Findable | Can the reader use headings, lookup keys, and links to locate the answer and its governing conditions? |
| Understandable | Can the reader interpret terms, actors, relationships, uncertainty, and normative meaning without guessing? |
| Usable | Can the reader reach the intended understanding, action, decision, or reconstruction without overlooking a prerequisite, exception, or limit? |

Identify the passage or missing information behind a weak assessment and trace it through the [drafting and revision sequence](drafting-and-revision.md#review-content-in-both-directions). Use relevant reader feedback when available, and distinguish observed reader use from an author's assessment. Claim only evaluation actually performed. Fixed word counts, sentence-length limits, and readability scores alone do not establish these outcomes; judge expression in the reader's language and context.
