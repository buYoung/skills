# Design System Document

## Purpose

Provide a durable, navigable source for reusable visual and interaction decisions. A Design System Document governs either product UI or app/game digital storefront listing assets; it does not produce the interface or assets themselves.

## Select this type when

- Product teams need shared foundations, tokens, components, content rules, accessibility decisions, or interaction patterns.
- Brand, product, marketing, or localization teams need one visual system for digital storefront icons, screenshots, previews or trailers, capsules, heroes, feature graphics, and other listing assets.
- Readers must know which document owns a decision and how common rules adapt to a named platform or store.

## Route elsewhere when

- The user wants UI code, a working interface, a component implementation, or a prototype.
- The user wants a mockup, image, icon, screenshot treatment, preview video, feature graphic, or promotional asset created or edited.
- The artifact defines a software system or architecture rather than a visual and interaction system.
- The artifact defines one product feature's behavior and policy decisions for implementation: FDD.

## Select exactly one prebuilt

| Prebuilt ID | Select when | Default output root | Read |
| --- | --- | --- | --- |
| `default` | Product UI foundations, tokens, components, patterns, content, accessibility, and governance are the primary contract | `docs/design-system` | [prebuilts/default.md](prebuilts/default.md) |
| `app-store-page` | App or game storefront listing icons, screenshots, previews or trailers, capsules, heroes, feature graphics, localization, and delivery are the primary contract | `docs/design-system-visual-assets` | [prebuilts/app-store-page.md](prebuilts/app-store-page.md) |

Select from the requested artifact, not from its destination. For example, a Steam visual asset system requested at `docs/marketing/store-assets` still uses `app-store-page`.

Read only the selected prebuilt. Do not load the other prebuilt for comparison, inspiration, or fallback.

## Resolve the output root

Use the first applicable location:

1. The path explicitly specified by the user
2. The location of the existing Design System Document being updated, rewritten, reviewed, fact-checked, or normalized
3. The selected prebuilt's default output root

Inspect an existing target before writing. Do not silently replace an unrelated document, and do not create `-v2`, `-final`, or date-suffixed paths to avoid resolving canonical ownership. Ask when a collision leaves canonical ownership materially ambiguous.

If the user explicitly asks for a chat-only draft, return the coordinated Markdown without creating files. Otherwise, a creation request with no path uses the selected prebuilt's default output root.

## Load next

- For create, rewrite, update, or normalize: read [design-system-authoring.md](design-system-authoring.md) and the selected prebuilt.
- For review or fact-check: read [design-system-review.md](design-system-review.md) and the selected prebuilt.
- When a product platform is explicitly in scope for `default`: also read [platform-adaptation.md](platform-adaptation.md).
- When a storefront is explicitly in scope for `app-store-page`: also read [storefront-research.md](storefront-research.md).
- When modifying or reviewing an existing set: also read the shared existing-document-edits reference.
- When claims depend on implementation, brand sources, or current external requirements: also read the shared source-grounding reference.

## Stable output contract

- Treat the output as one coordinated document set with `index.md` as its map, not as unrelated Markdown files.
- Give each concept one stable name and one canonical owning file. Cross-reference that owner instead of copying the decision.
- Preserve common rules separately from platform- or store-specific differences.
- For every explicitly named storefront, create or update exactly one canonical storefront file after current official research.
- Do not invent tokens, values, sizes, policies, brand decisions, platform behavior, or marketplace requirements.
- Mark a necessary but unresolved decision explicitly. Do not create empty ceremonial sections or placeholder platform, store, or item files.
