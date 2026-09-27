# Product UI component contracts and design previews

Use this reference with the `default` prebuilt to author or review component design decisions and the workflow for applying them to new UI. Apply it within the current operation's scope; a focused revision does not require rebuilding the inventory or adding an unrelated preview workflow. The [common rule contract](design-rule-contract.md) owns rationale and applicability, and the [direction workflow](design-direction-workflow.md) owns approval and representative validation.

## Identify the reusable units

Inspect the in-scope interface, implementation, and approved sources before choosing the component inventory. Distinguish basic controls, reusable composites, and screen-level composition patterns. A document for a whole form or dialog must not conceal the contracts of its material constituent controls. A native or library control still belongs in the inventory when readers must choose or configure it; it does not need a product-specific wrapper class to qualify.

Give each material component a stable name and a canonical file or addressable section linked from `components/index.md`. Small related controls may share a file when each retains its own design and usage contract. Record whether the source is platform-provided, library-provided, or product-specific, and connect composites to their constituent owners. Do not invent code APIs from document names, duplicate shared definitions, or expand the inventory to unrelated product surfaces.

## Make the design reproducible

Use the selected prebuilt's component section order, with prose or tables as appropriate. For each material component, establish the information that lets a reader select and compose it:

| Reader decision | Design information to provide |
| --- | --- |
| When to choose it | Purpose, application and non-application conditions, and supported alternatives, including the reason to prefer it over a similar control |
| What gives it its appearance | Relevant parts and hierarchy; label, icon, content and action placement; alignment, grouping, spacing, typography and color roles; shape or emphasis owned by this component |
| How it occupies space | Supported width and height behavior, such as intrinsic sizing, fixed or bounded sizing, or filling available space; relevant minimums, maximums, padding, gaps, units, scaling and content constraints |
| Which forms and states are supported | Meaningful variants and relevant default, focus, selection, disabled, error or loading states, with both their visible differences and behavioral consequences |
| How it combines with other elements | Relationships to adjacent labels, help, validation, actions and containers, and adaptations for constrained space or longer content |
| What implements the decision | Named supported control or reusable source, token or theme bindings, fixed mechanics, permitted customization and source-grounded usage examples |

For material information, distinguish an explicit system decision, an inherited rule with an identified source and local consequence, a necessary unresolved decision, and a genuinely non-applicable item. Unknown or inherited information is not the same as non-applicable information. Omit irrelevant headings without using that permission to omit needed design decisions. Business-value ranges, event flows, and source links support a contract but do not replace its visual and spatial rules.

State verified dimensions with their actual units and semantics: a preferred width is not a fixed width, character columns are not pixels, and a scale-aware source value is not a measured physical size. Do not invent size tiers, token values, exact geometry, or unsupported states to fill the table. If the implementation supports one size, explain that size behavior and its adaptations rather than fabricating small, medium, and large variants.

## Explain inherited appearance

When the platform or a library owns appearance, identify the supported control and relevant theme, layout, or token contract. Explain what it supplies and what the product chooses, such as label position, fill versus intrinsic width, adjacent-action placement, semantic emphasis, or allowed overrides. Link shared inherited rules once and state each component's consequence. “Use platform defaults” alone is insufficient when readers still have to make those choices.

Keep platform-owned metrics inherited when exact values vary with theme, scaling, or runtime. Do not transcribe speculative pixel values or treat one rendering as universal. Where existing sources show different compositions, explain the supported distinction or record the missing rationale; do not silently turn every observed variation into an approved design variant.

## Present design previews for new UI

For a new or substantially rewritten system, or an update specifically adding this workflow, put the following consumer workflow in `governance.md`, linking the relevant component and pattern owners. Make it discoverable from `index.md` for later UI work without requiring that work to invoke the document-writing skill.

1. For a new component, new UI surface, or material change to visual hierarchy, layout, or interaction composition, inspect the existing approved design and choose the closest applicable components and patterns. Preserve their visual language while adapting to the task; similarity alone does not establish that the same composition belongs in the new context.
2. Create a concrete visual draft in representative context and show it to the user before presenting the design as settled. Use an appropriate rendered prototype, mockup, or native preview that exposes the actual design choices. Show the changed states needed to judge the proposal; a component name, source-code snippet, prose plan, or inaccessible file path alone is not a preview.
3. Explain which existing rules the draft reuses, what changes, why those changes fit the task, and which details remain proposed or unverified. One coherent proposal is enough unless alternatives help resolve a material tradeoff or the user requests them. Label approximations when the preview cannot faithfully reproduce the target platform; do not report a mockup as runtime verification.
4. Apply the user's feedback and existing decision authority to the affected owners. Showing a preview is not approval, and an existing approval is not lost because a preview is requested. Request a decision only when an unresolved design choice requires one under the existing workflow; the preview requirement does not create a blanket implementation-approval gate.

A narrow correction or exact reuse in an unchanged composition does not need a fresh exploratory mockup when its appearance and behavior are already established. A new screen assembled from existing components still needs a preview of their composition. Honor an explicit user request for, or waiver of, a preview. If an authorized UI deliverable already provides a suitable rendered prototype, present that result rather than producing a duplicate artifact.

Preview production belongs to the UI or visual-production workflow. During document-only work, define this workflow and link any existing previews; do not silently generate assets or implement UI. For an authorized mixed request, route and complete the preview as its own deliverable, expose the usable result to the user, and report document and preview outputs separately. If production capability is unavailable, state the limitation and outstanding preview rather than substituting a promise or claiming visual validation.

Keep the preview requirement in the governance owner and each component's design decisions in its component owner. Reference actual previews and their decision status when available; do not create placeholder image paths or treat unapproved visual details as canonical rules.

## Check the resulting contract

Can an implementer find each material component, decide when to use or avoid it, reproduce its supported sizing and composition, and distinguish inherited appearance from product decisions and unresolved gaps? Check those answers across the actual owners, not just the presence of headings or a `components/` directory. Confirm that new UI work can find the preview workflow and that any claimed preview was actually presented with an honest validation scope.
