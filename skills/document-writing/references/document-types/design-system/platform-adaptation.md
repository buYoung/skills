# Platform and store adaptation

Use this reference when the user explicitly names a product platform for `default`. For an `app-store-page` storefront, use [storefront-research.md](storefront-research.md) instead.

## Common separation rule

- Keep the shared contract neutral; do not make one platform the implicit default.
- Preserve the approved upper-level design direction while adapting only what the platform or storefront context genuinely changes.
- Put only differences, constraints, mappings, and exceptions in the conditional file.
- Link to the canonical common decision instead of duplicating it.
- Do not generalize one platform requirement into the shared system.
- Do not treat a necessary platform difference as visual inconsistency or force identical form across different input, density, scale, or native-control contexts.
- Use stable kebab-case filenames based on the canonical platform name. Normalize browser products, web admin tools, and web dashboards to `platforms/web.md`; product purpose or audience does not create `web-admin.md` or `dashboard.md`. Keep product-subtype differences as sections or conditions inside the canonical platform file.

## Product platforms for `default`

Create `platforms/<platform-name>.md` only for an explicitly supported platform such as web, Android, or iOS. Record applicable differences in:

- Input methods and interaction states
- Navigation and presentation conventions
- Units, density, scaling, and layout behavior
- Native components and when they take precedence
- Accessibility APIs, semantics, and user settings
- Motion capabilities and reduced-motion behavior

Verify a platform requirement against current first-party platform documentation or a primary standard when the document states an exact value or rule readers must match, such as a required size, color, file or naming convention, or a mandatory native-control rule. Adaptation guidance that asserts no such requirement, such as preferring native controls for familiar behavior, is a design decision and needs no platform citation. When a requirement needs verification, first check whether the environment can open current web sources and whether the user or task permits web access. When it can, verify each material constraint in the opened source and record its URL and check date beside the constraint or in a source table. When it cannot, use supplied documentation or repository evidence, mark the platform guidance as unverified, and record the capability limitation; do not use the file-reading or writing date as a check date. Repository assets show how the product currently behaves, not what the platform requires, so do not present one as the other.

Do not add a `platforms/` document when no platform is specified.

Treat collective labels such as mobile, desktop, or console as scope labels, not automatic filenames. Resolve the concrete platforms from supplied material or ask once when their differences matter. Put one direct, user-answerable either/or question in the user-facing response; recording only a decision-needed note inside `index.md` does not satisfy this clarification. Create `platforms/mobile.md` or another collective file only when the user explicitly defines that collective platform as one canonical target.

## Digital storefronts for `app-store-page`

Do not apply product-platform adaptation rules to a storefront. Follow [storefront-research.md](storefront-research.md), which owns storefront naming, official research, visual-only scope, file creation, and unresolved-source behavior.
