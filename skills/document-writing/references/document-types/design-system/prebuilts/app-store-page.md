# `app-store-page` prebuilt

## Purpose and default root

Use this prebuilt for a coherent visual asset system for an app or game digital storefront such as Apple App Store, Google Play, Microsoft Store, or Steam. It governs assets and their shared visual composition but does not create icons, screenshots, videos, capsules, heroes, feature graphics, or promotional artwork. Its default output root is `docs/design-system-visual-assets`.

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

The displayed root is replaced by the resolved output root. `stores/` and its files are conditional; do not create a literal placeholder file.

## File responsibilities

### `index.md`

Define the target product, audiences, supported storefronts, message priorities, asset map, authoritative brand sources, and precedence for resolving conflicts. Identify the canonical owner of each major decision area.

### `visual-language.md`

Own color, typography, backgrounds, illustration, device frames, product-to-listing continuity, and other supplied brand continuity rules. Do not derive visual choices from store examples alone.

### `asset-system.md`

Own the role and relationship of icons, screenshots, preview videos or trailers, feature graphics, capsules, heroes, library art, and other storefront-defined assets. Distinguish shared source material, storefront variants, locale variants, and asset-specific decisions without inventing required deliverables.

### `screenshots-and-previews.md`

Own screen selection, sequence, narrative flow, fidelity to actual UI or gameplay, caption rules, and the relationship between static screenshots, previews, and trailers.

### `composition-and-copy.md`

Own visual hierarchy, safe areas, text placement, message length, composition rules, and usage or prohibited-usage examples supported by the brand and product sources.

### `localization.md`

Own translation expansion, right-to-left layout, regional asset variants, cultural suitability, review, and fallback behavior. Keep locale-specific exceptions beside their locale or store consequence.

### `accessibility.md`

Own contrast, legibility, text dependence, captions, motion alternatives, meaningful sequencing, and other accessibility requirements for the listing asset system.

### `delivery-and-versioning.md`

Own source files, export formats, filenames, locale and store variants, review status, approval, release association, archival, and deprecation. Do not invent tooling, owners, statuses, or formats.

### `stores/<store-name>.md`

For every explicitly named storefront, follow [storefront-research.md](../storefront-research.md) and create or update exactly one storefront file after current first-party research. Multiple storefronts require separate files; aliases for the same storefront require one file.

Keep the research visual-only. Storefront listing titles, descriptions, tags, categories, pricing, and legal submission fields do not belong here unless a rule directly determines whether a visual asset is valid.

If no storefront is specified, write only the storefront-neutral visual asset contract and do not research or invent mutable numeric requirements.
