# `app-store-page` prebuilt

## Purpose and default root

Use this prebuilt for an approved, coherent visual direction and reusable asset system for any digital storefront. The storefront may distribute apps, games, software, media, device experiences, or another product category; support is discovered from the requested scope and current authoritative material rather than a built-in store list. The prebuilt governs assets and their shared visual composition but does not create the assets itself. Its default output root is `docs/design-system-visual-assets`.

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

The displayed root is replaced by the resolved output root and serves as a responsibility map, not a requirement to create empty files. Replacing the root does not replace `index.md` with `README.md` or flatten the set into one file. Always create `index.md` for a new saved set. Create another common file only when it owns at least one supplied or verified decision, or a necessary unresolved decision readers must track. `stores/` remains conditional; every explicitly in-scope storefront owns one `stores/<store-name>.md`; never create literal placeholder files.

## File responsibilities

### `index.md`

Define the target product, audiences, supported storefronts, approved design direction in one or two sentences, direction authority, message priorities, validation status, asset map, authoritative brand sources, and precedence for resolving conflicts. Identify the canonical owner of each major decision area. Do not include rejected direction hypotheses.

### `visual-language.md`

Own upper-level visual principles and invariant decisions for color, typography, backgrounds, illustration, device frames, product-to-listing continuity, motion character, and other supplied brand continuity rules. Identify permitted variation, conditional adaptation, prohibited expression, and observable verification criteria. Do not derive visual choices or approval from store examples alone.

### `asset-system.md`

Own cross-storefront concepts and mappings such as product identity, captured product views, motion previews, promotional artwork, and shared source material. Explain how different asset types preserve the approved upper-level direction while adapting form, density, hierarchy, and brand emphasis to their function. Storefront files own each operator's official asset names, required status, specifications, placements, and storefront-specific relationships. Do not move those facts into the common contract or force every asset into one surface form.

### `screenshots-and-previews.md`

Own screen selection, sequence, narrative flow, fidelity to actual UI or gameplay, caption rules, and the relationship between static screenshots, previews, and trailers.

### `composition-and-copy.md`

Own visual hierarchy, safe areas, and copy embedded in or directly paired with visual assets. It does not own general storefront listing titles, descriptions, tags, or search metadata.

### `localization.md`

Own translation expansion, right-to-left layout, regional asset variants, cultural suitability, review, and fallback behavior. Keep locale-specific exceptions beside their locale or store consequence.

### `accessibility.md`

Own contrast, legibility, text dependence, captions, motion alternatives, meaningful sequencing, and other accessibility requirements for the listing asset system. Explain where these requirements constrain or correct the approved direction.

### `delivery-and-versioning.md`

Own source files, export formats, filenames, locale and store variants, representative validation records, direction approval and change review, release association, archival, and deprecation. Record only the approved direction and validation outcome, not rejected hypotheses. Do not invent tooling, owners, statuses, or formats.

When the user also requests an actual image or video, this file records the approved delivery contract while the production workflow creates the binary asset. The document set links to the resulting asset when available, but its completion report lists the document set and production asset as separate deliverables.

### `stores/<store-name>.md`

For every in-scope storefront, follow [storefront-research.md](../storefront-research.md). Mutating operations create or update one file per storefront after current first-party research or the documented web-unavailable fallback; review and fact-check report findings without changing files. Multiple storefronts require separate files, while aliases confirmed to represent the same official storefront share one file.

Keep storefront differences conditional. Record how official constraints change presentation, size, placement, or asset relationships without turning one storefront's implementation into the shared direction.

Keep the research visual-only. Storefront listing titles, descriptions, tags, categories, pricing, and legal submission fields do not belong here unless a rule directly determines whether a visual asset is valid.

If no storefront is specified, write only the storefront-neutral visual asset contract and do not research or invent mutable numeric requirements.
