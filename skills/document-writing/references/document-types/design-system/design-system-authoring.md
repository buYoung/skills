# Authoring a Design System Document

## Required context

For each output set, establish its selected prebuilt, resolved root, target product, intended readers, authoritative brand and product sources, existing design-system artifacts, and supported platforms or storefronts. Distinguish supplied decisions from verified facts and unresolved choices, and repeat the workflow independently for every requested set.

## Authoring sequence

1. Confirm that the request contains a durable design-system document deliverable. Separate any UI or visual asset production deliverable instead of treating the two as mutually exclusive.
2. Select one prebuilt for the current output set and resolve that set's root using the overview precedence.
3. Inspect the complete existing document set and its authoritative inputs before an update, rewrite, or normalization.
4. For `app-store-page`, separate in-scope storefronts from excluded, comparison-only, example, and background mentions; then normalize and deduplicate only the in-scope targets.
5. Follow [storefront-research.md](storefront-research.md) for each in-scope storefront before drafting its file, including its web-unavailable behavior.
6. Inventory concepts and assign one canonical owning file to each before drafting cross-references.
7. Create or update the selected prebuilt's common files with only supported decisions and explicit unresolved items.
8. Add only the platform or storefront files explicitly required by the request.
9. Check names, values, links, and ownership across the complete set.
10. For an existing set, compare the result with the original for accidental loss, changed meaning, and altered exact text.
11. Before completion, compare the selected prebuilt's owner map and promised output paths with the final tree. Confirm that each substantive supplied decision is in its canonical owner, every required owner is linked from `index.md`, and no unsupported value or policy was introduced. Fix a mismatch before reporting completion; if it cannot be fixed, report the set as incomplete.

Preserve valid existing platform, storefront, and custom files that are outside the current change scope. A focused update changes only the requested owners and cross-references affected by those changes.

For an existing set, the selected prebuilt's file responsibilities still determine canonical ownership. When the requested update supplies substantive decisions for a responsibility whose owner file is missing, create that owner file at the established root and link it from `index.md`. Do not inline those decisions into `index.md` merely to avoid creating a file. Do not create an owner file when no supported or necessary unresolved decision belongs there.

## Canonical ownership

- Use one term for one concept throughout the set.
- Define a decision once in the file responsible for it; other files link to that definition and state only their local consequence.
- Make `index.md` identify the document map, authoritative inputs, and precedence for resolving conflicting sources.
- Keep common rules platform- or store-neutral. Put only genuine differences in conditional files.
- If existing sources disagree and no authority resolves them, preserve the conflict as an explicit unresolved decision instead of choosing silently.

## Evidence and unknowns

- Do not derive token values, dimensions, breakpoints, durations, asset counts, formats, policies, or brand rules from convention or examples.
- Preserve exact values, fenced code blocks, identifiers, filenames, links, and user-owned content from existing sources unless the user requests a change.
- When a required decision is missing, name the decision, its owner if known, and the evidence needed to resolve it. Do not add an empty heading merely to mirror a template.
- Treat mutable storefront requirements as current facts that need first-party verification at document-generation time.

## Scope control

Document how UI or listing assets should remain coherent. Storefront-specific research covers visual assets only; exclude listing titles, descriptions, tags, categories, pricing, and legal submission fields unless a rule directly determines whether a visual asset is valid. Do not implement components, generate mockups or images, capture screenshots, edit videos, or create deliverable assets as part of this document operation.
