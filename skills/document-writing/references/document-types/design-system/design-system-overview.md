# Design System Document

## Purpose

Discover and approve a coherent design direction, validate that direction in contrasting representative situations, and provide a durable, navigable source for the resulting reusable visual and interaction decisions. A Design System Document governs either product UI or any digital storefront's listing assets; it does not produce the interface or assets itself.

## Select this type when

- Product teams need shared foundations, tokens, components, content rules, accessibility decisions, or interaction patterns.
- Brand, product, marketing, or localization teams need one visual system for digital storefront icons, screenshots, previews or trailers, capsules, heroes, feature graphics, and other listing assets.
- Readers must know which document owns a decision and how common rules adapt to a named platform or store.
- Teams need to distinguish the upper-level direction that remains consistent from the forms, density, states, and platform or storefront behavior that should vary by context.

## Route elsewhere when

- The user wants UI code, a working interface, a component implementation, or a prototype.
- The user's only requested artifact is a mockup, image, icon, screenshot treatment, preview video, feature graphic, or promotional asset to create or edit.
- The artifact defines a software system or architecture rather than a visual and interaction system.
- The artifact defines one product feature's behavior and policy decisions for implementation: FDD.

## Select one prebuilt per output set

| Prebuilt ID | Select when | Default output root | Read |
| --- | --- | --- | --- |
| `default` | Product UI foundations, tokens, components, patterns, content, accessibility, and governance are the primary contract | `docs/design-system` | [prebuilts/default.md](prebuilts/default.md) |
| `app-store-page` | A digital storefront's operator-defined visual assets, localization, and delivery are the primary contract | `docs/design-system-visual-assets` | [prebuilts/app-store-page.md](prebuilts/app-store-page.md) |

Select from the requested artifact, not from its destination. A storefront visual asset system requested at `docs/marketing/store-assets` still uses `app-store-page` regardless of which operator owns the storefront.

Read only the selected prebuilt for each output set. When the user requests both product UI and storefront visual assets, create two coordinated sets and apply each prebuilt only to its own set; do not merge their file contracts.

## Resolve the output root

Use the first applicable location:

1. The path explicitly specified by the user
2. The location of the existing Design System Document being updated, rewritten, reviewed, fact-checked, or normalized
3. The selected prebuilt's default output root

Inspect an existing target before writing. Do not silently replace an unrelated document, and do not create `-v2`, `-final`, or date-suffixed paths to avoid resolving canonical ownership. Ask when a collision leaves canonical ownership materially ambiguous.

A prebuilt root is a directory because its output is a document set. For new creation, a user-specified `.md` path is not a root; ask whether its parent directory or another directory should own the set. When the path identifies an existing file, inspect its index and cross-references to resolve the established set root without moving it.

If the user explicitly asks for a chat-only draft, return the coordinated Markdown without creating files. Otherwise, a creation request with no path uses the selected prebuilt's default output root.

## Load next

- For every operation: read [design-direction-workflow.md](design-direction-workflow.md) and classify the maturity of each output set.
- For create, rewrite, update, or normalize: then read [design-system-authoring.md](design-system-authoring.md) and the selected prebuilt.
- For review or fact-check: then read [design-system-review.md](design-system-review.md) and the selected prebuilt.
- When a product platform is explicitly in scope for `default`: also read [platform-adaptation.md](platform-adaptation.md).
- When a storefront is in scope for `app-store-page`: also read [storefront-research.md](storefront-research.md). Its review and fact-check paths are read-only.
- When modifying or reviewing an existing set: also read the shared existing-document-edits reference.
- When claims depend on implementation, brand sources, or current external requirements: also read the shared source-grounding reference.

## Stable output contract

- Treat each output set as one coordinated document set with `index.md` as its map, not as unrelated Markdown files.
- Give each concept one stable name and one canonical owning file. Cross-reference that owner instead of copying the decision.
- Record only an approved direction, its rationale, and its representative validation; rejected hypotheses stay out of the canonical set unless the user requests a separate decision history.
- Classify direction-bearing decisions as invariant, variable, conditional, prohibited, or verification decisions. Preserve common rules separately from platform- or store-specific differences.
- Do not write a new or direction-changing set while direction approval or representative validation is still missing. Present direction hypotheses and the required user decision in the conversation instead.
- Reuse an explicit approved direction from an authoritative existing source. Do not infer approval from visual similarity alone or reopen broad exploration for a narrow change whose affected decision flow is already clear.
- For every in-scope storefront, create or update one storefront file only during create, update, rewrite, or normalize, after either current first-party research or the explicit capability-limited fallback. Review and fact-check report missing, stale, or conflicting storefront information without changing files.
- Do not invent tokens, values, sizes, policies, brand decisions, platform behavior, or marketplace requirements.
- Mark a necessary but unresolved decision explicitly. Do not create empty ceremonial sections or placeholder platform, store, or item files.
