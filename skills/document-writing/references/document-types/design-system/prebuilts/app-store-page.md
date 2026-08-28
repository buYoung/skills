# `app-store-page` prebuilt

## Purpose and default root

Use this prebuilt for a coherent visual asset system for any digital storefront. The storefront may distribute apps, games, software, media, device experiences, or another product category; support is discovered from the requested scope and current authoritative material rather than a built-in store list. The prebuilt governs assets and their shared visual composition but does not create the assets themselves. Its default output root is `docs/design-system-visual-assets`.

## Base document set

```text
docs/design-system-visual-assets/
├── index.md
├── visual-language.md
├── asset-system.md
├── screenshots-and-previews.md
├── composition-and-copy.md
├── localization.md
├── accessibility.md
├── delivery-and-versioning.md
└── stores/
    └── <store-name>.md
```

The displayed root is replaced by the resolved output root and serves as a responsibility map, not a requirement to create empty files. Always create `index.md` for a new saved set. Create another common file only when it owns at least one supplied or verified decision, or a necessary unresolved decision readers must track. `stores/` remains conditional; never create literal placeholder files.

## File responsibilities

### `index.md`

Define the target product, audiences, supported storefronts, message priorities, asset map, authoritative brand sources, and precedence for resolving conflicts. Identify the canonical owner of each major decision area.

### `visual-language.md`

Own color, typography, backgrounds, illustration, device frames, product-to-listing continuity, and other supplied brand continuity rules. Do not derive visual choices from store examples alone.

### `asset-system.md`

Own cross-storefront concepts and mappings such as product identity, captured product views, motion previews, promotional artwork, and shared source material. Storefront files own each operator's official asset names, required status, specifications, placements, and storefront-specific relationships. Do not move those facts into the common contract.

### `screenshots-and-previews.md`

Own screen selection, sequence, narrative flow, fidelity to actual UI or gameplay, caption rules, and the relationship between static screenshots, previews, and trailers.

### `composition-and-copy.md`

Own visual hierarchy, safe areas, and copy embedded in or directly paired with visual assets. It does not own general storefront listing titles, descriptions, tags, or search metadata.

### `localization.md`

Own translation expansion, right-to-left layout, regional asset variants, cultural suitability, review, and fallback behavior. Keep locale-specific exceptions beside their locale or store consequence.

### `accessibility.md`

Own contrast, legibility, text dependence, captions, motion alternatives, meaningful sequencing, and other accessibility requirements for the listing asset system.

### `delivery-and-versioning.md`

Own source files, export formats, filenames, locale and store variants, review status, approval, release association, archival, and deprecation. Do not invent tooling, owners, statuses, or formats.

### `stores/<store-name>.md`

For every in-scope storefront, follow [storefront-research.md](../storefront-research.md). Mutating operations create or update one file per storefront after current first-party research or the documented web-unavailable fallback; review and fact-check report findings without changing files. Multiple storefronts require separate files, while aliases confirmed to represent the same official storefront share one file.

Keep the research visual-only. Storefront listing titles, descriptions, tags, categories, pricing, and legal submission fields do not belong here unless a rule directly determines whether a visual asset is valid.

If no storefront is specified, write only the storefront-neutral visual asset contract and do not research or invent mutable numeric requirements.
