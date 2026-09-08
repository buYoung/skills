# Reusable design rules

Use this contract when authoring or reviewing substantive reusable rules in either prebuilt. Keep each decision in its existing canonical owner; this reference adds no output file, document type, production task, or approval gate. The [direction workflow](design-direction-workflow.md) owns direction approval, decision classes, and representative validation.

## Ground the rule and its scope

Connect a material rule's applicable context, intent and rationale, observable outcome, permitted variation or exceptions, and authority. Use prose, examples, or a compact table as useful; do not require a fixed record shape or fill every field for every minor rule.

Distinguish approved decisions, observed implementation facts, interpretations, and unresolved questions. Record exact values and identifiers only when supplied or verified. A shipped implementation establishes what exists, not automatically what is approved. An example's appearance or another brand's choices must not become a universal requirement.

## Connect supported implementation and assets

When an implementation or approved asset exists, connect its canonical name and location, supported variants, token bindings where relevant, and supported usage examples to the responsible component, token, or asset document. Separate the public usage contract from internal implementation details. Trace aliases and bindings through to the consumer without copying their canonical definitions into every owner.

Flag conflicts between implementation examples and approved guidance; do not silently promote a stale example to authority. Do not invent component names, classes, APIs, tokens, asset paths, or exact values. If implementation is absent or inaccessible, state what remains unverified and continue supported document work under the existing operation gate. Do not introduce a whole-set stop solely for that gap. Do not make one CSS delivery mechanism or web technology the default for every platform.

### Reuse mechanics instead of reconstructing them

Identify which recurring decisions the supplied implementation or approved template already fixes, which variations its public contract supports, and which changes require a separate approved revision. Typography, spacing, recurring composition, and asset treatment owned by that reusable source should be applied through it rather than reconstructed from prose or overridden ad hoc. Keep judgment in the document and repeatable mechanics with their existing implementation or asset owner. When that owner cannot express a needed approved variation, record the specific gap and route it to that owner; do not invent a replacement API or silently broaden the document task into implementation.

When a template's named regions guide placement, map them to the source coordinate space and verified bounds, then describe the scale or transform for each supported variant. Distinguish an observed outline, an actual content slot, and an approved exclusion area; do not infer that every visible line is prohibited decoration. State unresolved region roles explicitly. A link to the original alone does not communicate a placement contract. Keep content within supported slots and explain how captions and product evidence avoid collisions without altering fixed source geometry.

Verify usage examples against the source's language, invocation form, parameters, return shape, and consumer expectations. A matching name and option list alone is insufficient: an ordinary function returning a data object is not thereby a JSX component. Inspect the actual declaration and a supported caller when available. Distinguish a supplied example, a newly source-checked example, and an example whose execution remains unverified. Do not claim compilation, rendering, or runtime behavior from source inspection alone.

## Explain task and information placement

In composition and interaction patterns, connect the user's task to the information or action needed first, the reason for its placement, and the conditions that permit a different composition. For example, comparison needs discoverable correspondence between alternatives; manipulation needs a legible relationship between inputs and results. Ground the actual arrangement in this system's evidence rather than prescribing universal screen templates.

When readers need both a quick scan and detailed evidence, explain how the two paths connect. Keep material conditions, units, and uncertainty visible during summarization. Shared brand principles can support different information priorities and compositions for different tasks.

## Record failures and approved improvements

For a confirmed failure or prohibited use, describe its recognizable symptom, user impact, conditions under which it fails, and the supported alternative. Avoid unexplained bans and rules derived from a single preference.

Classify recurring feedback by its remedy: document judgment, implementation or asset correction, an existing automatic check, or an execution-tool issue. An implementation defect may require fixing the consumer rather than changing a correct design rule. This classification does not authorize implementation, asset production, or new automation.

Record the rationale for an approved correction and its actual verification result in `governance.md` or `delivery-and-versioning.md`, with links to affected rule owners. Keep one-off preferences and unapproved interpretations out of the canonical rules. Distinguish supplied validation records, document-level checks, and any unperformed visual or runtime checks.

### Check whether the correction holds

For recurring feedback, connect the symptom and occurrence context to the exact supplied result, the accepted correction, and comparable follow-up evidence. Preserve the task, inputs, document or asset version, and relevant viewing or interaction conditions when they are available. Record what was checked mechanically and what a reviewer judged; preserve failed observations alongside successful ones. A supplied approval or an earlier pass is not evidence that later use improved.

Compare recurrence only across genuinely comparable work and keep the observation period and denominator when provided. Do not invent counts, a review cadence, or a decrease in failures. If the problem persists, distinguish unclear guidance, a missing reference/load, a reusable primitive that cannot express the rule, and a mechanical-check gap before choosing the remedy. A single model-specific failure needs repeated evidence before becoming a shared design rule. Record the next check and unresolved cause without treating a hypothesis as approved.

These records belong to the existing governance or delivery owner. They may describe an authorized separate production comparison, but do not make new rendering, automation, broad reapproval, or a fixed record template mandatory for ordinary document work.

## Reference scope

[How our agents build on-brand pages with design.md](https://vercel.com/blog/how-our-agents-build-on-brand-pages-with-design-md) is the methodological reference: connect reader-centered judgment, bounded reusable mechanics, and evidence from recurring corrections. Apply these practices within the existing repository document owners. The article's public distribution model, Vercel brand choices, implementation stack, and evaluation tooling are not requirements of this skill. Reading Vercel's rule file is not an authoring prerequisite.
