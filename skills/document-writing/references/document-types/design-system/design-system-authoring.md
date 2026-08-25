# Authoring a Design System Document

## Required context

Establish the selected prebuilt, resolved output root, target product, intended readers, authoritative brand and product sources, existing design-system artifacts, and any explicitly supported platforms or storefronts. Distinguish supplied decisions from verified facts and unresolved choices.

## Authoring sequence

1. Confirm that the request is for a durable design-system document rather than UI or visual asset production.
2. Select one prebuilt from the artifact's purpose and resolve the output root using the overview precedence.
3. Inspect the complete existing document set and its authoritative inputs before an update, rewrite, or normalization.
4. For `app-store-page`, normalize and deduplicate every explicitly named storefront and identify any product, package, or device branch that changes its visual asset requirements.
5. Research each named storefront according to [storefront-research.md](storefront-research.md) before drafting its file.
6. Inventory concepts and assign one canonical owning file to each before drafting cross-references.
7. Create or update the selected prebuilt's common files with only supported decisions and explicit unresolved items.
8. Add only the platform or storefront files explicitly required by the request.
9. Check names, values, links, and ownership across the complete set.
10. For an existing set, compare the result with the original for accidental loss, changed meaning, and altered exact text.

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
