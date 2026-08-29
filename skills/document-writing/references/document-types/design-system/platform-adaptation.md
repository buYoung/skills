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

Do not add a `platforms/` document when no platform is specified.

Treat collective labels such as mobile, desktop, or console as scope labels, not automatic filenames. Resolve the concrete platforms from supplied material or ask once when their differences matter. Put one direct, user-answerable either/or question in the user-facing response; recording only a decision-needed note inside `index.md` does not satisfy this clarification. Create `platforms/mobile.md` or another collective file only when the user explicitly defines that collective platform as one canonical target.

## Digital storefronts for `app-store-page`

Do not apply product-platform adaptation rules to a storefront. Follow [storefront-research.md](storefront-research.md), which owns storefront naming, official research, visual-only scope, file creation, and unresolved-source behavior.
