# Authoring a Design System Document

## Required context

For each output set, establish its selected prebuilt, resolved root, target product, intended readers, authoritative brand and product sources, existing design-system artifacts, supported platforms or storefronts, maturity state, and direction authority. Distinguish supplied decisions from verified facts and unresolved choices. Follow [design-direction-workflow.md](design-direction-workflow.md) before drafting.

When coordinated sets govern the same product and brand, reuse an explicitly approved upper-level direction rather than asking twice. Keep each set's contextual rules and representative validation independent.

## Authoring sequence

1. Confirm that the request contains a durable design-system document deliverable. Separate any UI or visual asset production deliverable instead of treating the two as mutually exclusive, and keep their completion records distinct.
2. Select one prebuilt and resolve the set root before direction exploration. If the requested path is a single Markdown filename for a multi-file set, or the destination belongs to an unrelated document, ask exactly one destination question and stop without asking later scope or direction questions.
3. If direction approval is missing, analyze the evidence and present two or three materially different hypotheses plus one recommendation in the conversation. Ask only the smallest plain-language decision needed, write no Design System Document file, and stop.
4. If direction is approved but fewer than two contrasting representative results or authoritative validation records exist, propose the representative situations and ask for existing results or separate production authorization. Write no Design System Document file and stop.
5. Translate confirmed qualitative feedback into invariant, variable, conditional, prohibited, and verification decisions. Locate each decision's canonical owning file before drafting cross-references.
6. For `app-store-page`, separate in-scope storefronts from excluded, comparison-only, example, and background mentions; normalize and deduplicate only in-scope targets, then follow [storefront-research.md](storefront-research.md) for each target. Before completion, sweep every common owner: storefront names may appear only in scope maps and links, while official URLs, mutable dimensions, counts, device branches, safe areas, placement, and ordering stay exclusively in `stores/<store>.md`.
7. Create or update only the selected prebuilt owners supported by approved decisions, verified facts, or necessary unresolved implementation details. Add only explicitly required platform or storefront files. If one conditional platform remains unresolved, complete the confirmed common and platform owners before asking, record the pending branch in `index.md`, and omit only the unresolved platform file.
8. Validate common language and appropriate contextual variation against the approved representative situations. Attribute a failure to direction, a shared rule, a component or asset rule, or platform or storefront adaptation, then revise the owning level.
9. Check names, values, links, decision classes, and ownership across the complete set. For an existing set, also compare against the original for accidental loss, changed meaning, and altered exact text.
10. Before completion, compare the owner map and promised paths with the final tree. A user-specified directory replaces only the prebuilt root, so a new saved set still requires `index.md` and every explicitly in-scope platform or storefront owner. Confirm that the approved direction, representative validation, every substantive supplied decision, and every required owner are present without unsupported values or policies. Fix a mismatch before reporting completion; if it cannot be fixed, report the set as incomplete.

Preserve valid existing platform, storefront, and custom files that are outside the current change scope. A focused update changes only the requested owners and cross-references affected by those changes.

For a focused existing revision, inventory the complete existing document tree and follow `index.md` links before concluding that an approved value is unavailable. Inspect likely authority owners whose names or headings indicate approval, change, decision, or governance. Then trace the changed value or rule from that authoritative source through aliases, component or asset bindings, and final consumers. Reopen direction exploration only when the requested change contradicts or replaces the approved upper-level direction. Otherwise validate only the affected representative states or contexts.

For an existing set, the selected prebuilt's file responsibilities still determine canonical ownership. When the requested update supplies substantive decisions for a responsibility whose owner file is missing, create that owner file at the established root and link it from `index.md`. Do not inline those decisions into `index.md` merely to avoid creating a file. Do not create an owner file when no supported or necessary unresolved decision belongs there.

## Canonical ownership

- Use one term for one concept throughout the set.
- Define a decision once in the file responsible for it; other files link to that definition and state only their local consequence.
- Make `index.md` identify the document map, authoritative inputs, and precedence for resolving conflicting sources.
- Keep common rules platform- or store-neutral. Put only genuine differences in conditional files. Common storefront files may define asset roles and upper-level principles and link to store owners, but must not copy a store's official URL, size, count, device condition, safe area, placement, or sequence rule.
- State which rules are invariant, variable, conditional, prohibited, or used for verification. Do not use “consistent” as a substitute for an observable contract.
- If existing sources disagree and no authority resolves them, preserve the conflict as an explicit unresolved decision instead of choosing silently.

## Evidence and unknowns

- Do not derive token values, dimensions, breakpoints, durations, asset counts, formats, policies, or brand rules from convention or examples.
- Preserve exact values, fenced code blocks, identifiers, filenames, links, and user-owned content from existing sources unless the user requests a change.
- When a required decision is missing, name the decision, its owner if known, and the evidence needed to resolve it. Do not add an empty heading merely to mirror a template.
- Treat mutable storefront requirements as current facts that need first-party verification at document-generation time.
- Treat an explicit approval record as direction authority. Similar-looking existing results are evidence for a hypothesis, not proof of approval.

## Scope control

Document how UI or listing assets should remain coherent. Storefront-specific research covers visual assets only; exclude listing titles, descriptions, tags, categories, pricing, and legal submission fields unless a rule directly determines whether a visual asset is valid. Do not implement components, generate mockups or images, capture screenshots, edit videos, or create deliverable assets as part of this document operation.
