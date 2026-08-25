# Reviewing a Design System Document

## Review boundary

Review the document set against its selected prebuilt, stated sources, and requested platforms or stores. Report findings without rewriting unless the user requested an update, rewrite, or normalization.

## Routing and location checks

- The artifact is a design-system decision source, not a UI implementation, asset-production request, FDD, or architecture design.
- Exactly one prebuilt fits the artifact's purpose.
- A custom path has not changed the selected prebuilt.
- The root follows user-specified path, existing-set location, then prebuilt default order.
- No unrelated document was overwritten and no arbitrary versioned duplicate was introduced.

## Contract checks

- `index.md` identifies scope, audience, document map, authoritative sources, and precedence.
- Each decision has one canonical owner and one stable name.
- Cross-references resolve and do not restate contradictory copies.
- Common files contain common rules; platform and store differences remain conditional.
- No token, value, size, policy, brand decision, behavior, or external requirement was invented.
- Missing necessary decisions are explicit, while empty ceremonial sections and placeholder item files are absent.
- Existing exact values, code blocks, identifiers, links, and user-owned content remain intact unless change was requested.

## Conditional checks

- `default` has no `platforms/` file unless at least one platform is explicitly in scope, and each file covers only that platform.
- `app-store-page` has no `stores/` file unless at least one storefront is explicitly in scope.
- Every named storefront resolves to exactly one file after alias deduplication, and no unrequested storefront file exists.
- Mutable visual asset sizes, counts, formats, placements, dependencies, and validity rules are supported by current first-party material checked for the document's revision.
- Storefront files exclude general listing copy, tags, categories, pricing, and legal submission fields.
- Inaccessible or conflicting official material is recorded as an explicit limitation; it is not silently replaced with third-party claims.
- Platform- or store-specific differences have not been generalized into the common contract.

## Quality bar

A reader can start at `index.md`, locate any governed concept, identify its authority and current decision, and determine whether a platform or store overrides it without encountering duplicate or unsupported rules.
