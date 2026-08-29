# Design direction workflow

Use this workflow for both `default` and `app-store-page`. It determines whether a Design System Document is ready to be authored or finalized. Tokens, component rules, and asset specifications can preserve an approved direction, but they cannot substitute for choosing one.

## Classify the current maturity

Classify each output set before drafting:

| State | Evidence | Next action |
| --- | --- | --- |
| Direction exploration | No approved direction or authoritative record establishes one | Gather evidence and propose directions; do not write the document set |
| Direction comparison | Two or three materially different directions are ready, but none is approved | Recommend one direction and ask the user to approve or correct it |
| Selected-direction refinement | A direction is approved, but its rules or representative validation are incomplete | Resolve only the remaining contradiction or validation gap |
| Design-system documentation | The direction is approved and supported by representative validation | Author or finalize the document set |
| Existing-system review | An existing set is being reviewed or fact-checked | Stay read-only and report direction or validation gaps as findings |
| Existing-system revision | An approved existing set is being changed | Trace the affected decision flow and reopen exploration only if the change alters the direction |

An explicit approval recorded in an authoritative existing source counts as approval. A visually consistent collection without an approval record does not. For a narrow existing change, do not repeat broad exploration when the approved direction and affected decision chain are clear.

When two output sets govern the same product and brand, they may share one approved upper-level direction when authoritative evidence supports that relationship. Their contextual rules and representative validation remain separate.

## Gather evidence before asking

Inspect what is available before asking the user:

- Product purpose, primary users, tasks, environment, and platforms or storefronts
- Existing interface, brand, icon, logo, content, motion, and listing-asset material in scope
- Results the user liked or rejected and the context in which they were judged
- Approved brand or product decisions and their authority
- Existing documents, implementations, and representative results
- Technical, platform, accessibility, localization, and delivery constraints
- Relevant comparison material, treating it as evidence rather than a direction to copy

Ask only for preferences, priorities, or approval that the evidence cannot establish. Do not ask the user to repeat a fact available from the repository, supplied files, or authoritative sources.

## Ask in the user's language

Ask one to three important questions at a time. Give two or three choices that would materially change the result, put the recommended choice first, and explain the visible result and risk of each choice.

Ask blocking decisions in dependency order. Resolve a destination collision or invalid multi-file root before asking about scope, direction, or representative validation. When an earlier decision blocks the later work, ask only that earlier question and stop. This keeps the user from answering decisions that may become irrelevant.

Keep the diagnostic model internal. Do not ask the user to choose abstract axes such as “precise versus friendly” or to supply design terminology. Ask about a recognizable impression, task, or situation instead. For example, ask whether a first-time user should notice immediate task clarity or a memorable brand presence before translating that answer into the underlying design axis.

Hide the analytical axis, not the consequence. The user should understand what each option would change and what it could make harder.

Write every requested decision as an actual question ending in `?` or `？`. Do not hide the interaction itself inside an imperative such as “approve A, B, or C.” The analytical intent may stay hidden, but the user must be able to see exactly what response is requested.

Do not make the final question depend only on an option label such as “approve option 1?” Restate the recognizable outcome and its main tradeoff in the question itself—for example, ask whether the product should make the next action immediately obvious even if brand expression becomes quieter. Option names may follow as shorthand, but they cannot replace the user-visible consequence.

Use only the axes that materially affect the supplied system. Possible internal axes include:

- Precise to approachable
- Restrained to expressive
- Geometric to organic
- Dense to spacious
- Neutral to emotional
- Function-led to personality-led
- Platform-native to strongly branded
- Flat to dimensional
- Stable to dynamic
- Traditional to experimental

## Propose directions instead of outsourcing design judgment

When no direction is approved, derive two or three materially distinct hypotheses from the evidence. For each hypothesis, provide:

- A one-sentence character statement
- The core visual principles
- Shape character
- Color attitude
- Density and spacing
- Information hierarchy
- The relationship between brand expression and platform convention
- Benefits, risks, and suitable contexts

Recommend one hypothesis and explain why it best fits the product, users, and constraints. Present the hypotheses in the conversation only. Do not create or modify Design System Document files until the user explicitly approves a direction.

Make hypotheses distinct through relative tendencies, priority, placement, and user-visible consequences. Before approval, do not turn those tendencies into a prescribed palette, named color family, grid, motif, texture, token, component, or asset rule unless an authoritative supplied source already establishes it. For example, “expression is concentrated at meaningful transitions” is an appropriate hypothesis; a jewel-tone palette, asymmetric grid, or textured object language is a new design decision and must wait for approval or supporting evidence.

If no live user can approve a direction, state that the work is incomplete and name the unresolved decision. Do not write a provisional document set or silently select the recommendation.

Once direction and representative validation are approved, a local uncertainty does not block unrelated confirmed owners. Write the common contract and every confirmed conditional adaptation, record the unresolved branch in `index.md`, omit that branch's conditional file, and ask one question about that branch. This applies when, for example, web is confirmed but “mobile” has not yet been resolved to iOS, Android, or an internal platform name.

Treat this as a partial-authoring rule, not a clarification stop: confirmed common and platform files must exist before the response asks about the unresolved branch. A response-only clarification is correct only when the unresolved decision blocks the whole set rather than one conditional owner.

## Translate qualitative feedback

Treat reactions such as “cramped,” “cold,” “toy-like,” “flat,” “inconsistent,” or “I like this one” as evidence to interpret, not final design rules. Compare the relevant results and break the reaction into observable causes such as:

- Shape grammar and the balance of curves and straight lines
- Visual weight
- Spacing and density
- Contrast and color roles
- Information hierarchy
- Compositional complexity and rendering style
- Size, position, and treatment of recurring elements

Use relative language when a visual cause does not require a measurement. State an exact size, distance, count, ratio, or color value only when it is directly verified from the supplied source or a reliable inspection result; do not estimate a precise value from appearance.

Do not copy the preferred result's surface form across every asset. Infer the upper-level principle that explains the preference. When that inference changes the direction or a shared rule, summarize it in plain language—“I understand this as …”—and ask the user to confirm or correct it before treating it as approved.

When the user asks for one confirmation question, combine confirmation and correction into one answerable sentence with one question mark. Do not split “is this right?” and “what should change?” into separate questions or append another choice request.

## Separate consistency from sameness

Different contexts may require different forms, sizes, density, and platform behavior. Preserve consistency through shared upper-level principles instead of forcing identical output.

Classify the approved decisions:

| Decision class | Meaning |
| --- | --- |
| Invariant | A principle that remains the same across every governed context |
| Variable | A decision that may change with content, function, or context |
| Conditional | A change permitted only for a named platform, storefront, state, size, or environment |
| Prohibited | An expression that is incompatible with the approved direction |
| Verification | An observable test for whether a result still follows the direction |

“Keep it consistent” is not a complete rule. Name what remains stable, what may vary, the condition for variation, and how a reviewer can tell.

## Validate representative results

Do not finalize a direction from prose alone or from one favorable result. Validate at least two contrasting representative situations chosen for the governed system, such as:

- Simple and information-dense views
- Default and interaction or error states
- Small and large presentation sizes
- Simple and composite components
- Function-led and brand-led assets
- Light and dark environments
- A common platform and a materially different platform or storefront

Use existing representative results or authoritative validation records when available. If fewer than two contrasting results are available, propose the situations and ask the user either to provide existing results or authorize separate production. Production belongs to the appropriate capability and remains a separate deliverable; resume document finalization only after its results can be inspected.

Check common visual language, appropriate contextual variation, accessibility, information delivery, scale, density, function-versus-brand balance, and platform or storefront constraints.

When validation fails, locate the failure before changing rules:

1. Direction: the selected character does not fit the product or audience.
2. Shared rule: an invariant or common relationship is wrong or incomplete.
3. Component or asset rule: a local application contradicts the shared direction.
4. Platform or storefront adaptation: a genuine contextual constraint was omitted or over-generalized.

Revise at the owning level and repeat the affected representative checks. Do not patch one result while leaving the failed shared rule unchanged.

## Ready-to-document gate

Proceed to authoring or finalization only when all of these are true:

- An authoritative existing source or the user explicitly approves one design direction.
- The direction can be stated in one or two sentences.
- The relevant design axes and core principles are clear.
- Invariant, variable, conditional, prohibited, and verification decisions are distinguishable.
- At least two contrasting representative situations support the direction.
- Platform- or storefront-specific adaptation is separate from the common direction.
- Material qualitative feedback has been translated into confirmed rules.
- Any remaining decision is explicitly unresolved rather than hidden.

Record only the approved direction, its supporting rationale, and validation result in the canonical document set. Do not preserve rejected direction hypotheses in the final source of truth unless the user explicitly asks for a separate decision history.
