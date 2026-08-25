# Storefront research

Use this reference only with the `app-store-page` prebuilt when the user explicitly names one or more app or game digital storefronts. Research every named storefront and create or update one storefront file for each. If no storefront is named, perform no storefront research and create no `stores/` file.

## 1. Resolve storefront identity

Canonicalize common aliases for new files:

| User wording | Canonical storefront | New file |
| --- | --- | --- |
| App Store, Apple Store, iOS App Store, Mac App Store | Apple App Store | `stores/apple-app-store.md` |
| Google Play, Play Store, Google Play Store | Google Play | `stores/google-play.md` |
| Microsoft Store, MS Store, Windows Store | Microsoft Store | `stores/microsoft-store.md` |
| Steam, Steam Store | Steam | `stores/steam.md` |

Deduplicate aliases that resolve to the same storefront. For another storefront, use an unambiguous current brand name supplied by the user or confirm its official name from first-party material, then convert that name to kebab-case. Ask one concise question if the identity remains materially ambiguous.

When updating an existing set, locate a file that already represents the same storefront from its title, metadata, sources, and content. Reuse that path even if its filename is non-canonical; do not silently rename it or create a canonical duplicate.

## 2. Resolve applicability before values

Identify the product type, package or submission type, target device families, and locales that affect the storefront's visual asset requirements. Infer them from user material and the repository when safe.

Ask before selecting numeric requirements when an unresolved branch materially changes the contract, such as Microsoft Store requirements for MSIX, MSI/EXE, or PWA submissions. If no live user can answer, preserve the applicable branches as unresolved instead of silently choosing one.

## 3. Research current first-party material

Search for and open the storefront operator's current developer, publisher, or partner documentation. A search-result snippet is discovery evidence, not support for a requirement. Verify each material requirement in the opened first-party source and record its URL and verification date near the requirement or in the source table.

Use these entry points as discovery seeds, not as frozen specifications:

### Apple App Store

- [Screenshot specifications](https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications/)
- [App Store asset best practices and resources](https://developer.apple.com/app-store/asset-best-practices/)

### Google Play

- [Preview asset guidance](https://support.google.com/googleplay/android-developer/answer/9866151)
- [Google Play icon design specifications](https://developer.android.com/distribute/google-play/resources/icon-design-specifications)

### Microsoft Store

- [Microsoft Store publishing](https://learn.microsoft.com/en-us/windows/apps/publish/get-started)
- [MSIX screenshots, images, and trailers](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/screenshots-and-images)

Follow the official branch for the actual package or submission type rather than carrying MSIX requirements into MSI/EXE or PWA documentation.

### Steam

- [Graphical assets overview](https://partner.steamgames.com/doc/store/assets?l=english)
- [Graphical asset rules](https://partner.steamgames.com/doc/store/assets/rules?l=english)
- [Trailers](https://partner.steamgames.com/doc/store/trailer)

For an unlisted storefront, find its equivalent first-party publisher documentation at generation time. Prefer the most specific current product, package, device, or asset page over a general overview. If current first-party sources conflict, record the conflict and applicability instead of choosing silently.

## 4. Keep research visual-only

Research only requirements that govern a visual asset:

- Canonical asset name, role, and placement
- Required, recommended, or optional status
- Dimensions, aspect ratio, crop, safe area, transparency, and scaling
- File format, file size, count, sequence, and upload grouping
- Asset-internal content restrictions and actual-product fidelity
- Device, locale, and regional variants
- Video, trailer, poster, and thumbnail requirements
- Dependencies between assets and conditions that affect whether an asset appears

Exclude listing titles, descriptions, feature text, tags, categories, search terms, pricing, packages, age-rating forms, certification steps, and legal submission fields. A text rule belongs in the storefront file only when it directly determines whether a visual asset is valid, such as a prohibition on promotional copy inside an image.

## 5. Write one file per storefront

Use this responsibility order in each `stores/<store-name>.md`:

1. Scope and applicability, including product, package, device, and locale boundaries
2. Research status, verification date, and first-party source list
3. Asset inventory
4. Asset-specific rules and exceptions
5. Cross-asset relationships and ordering
6. Device, locale, and regional variants
7. Delivery validation
8. Unresolved or conflicting requirements

The asset inventory should use applicable fields from: asset name, role or placement, status, dimensions or ratio, format, file-size limit, count, variant key, content restriction, and official source. Do not add empty fields or copy a storefront's vocabulary into another storefront.

Keep shared visual-language and delivery decisions in the common files. Storefront files own only verified storefront differences and link back to common owners instead of duplicating them.

## 6. Handle incomplete research

If first-party documentation is missing, inaccessible, or incomplete, continue with verified material. Record attempted official URLs, verification date, affected requirements, and the limitation. Mark unsupported requirements unresolved and report them at completion. Do not substitute third-party claims or remembered values.
