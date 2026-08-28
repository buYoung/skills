# Reviewing a Design System Document

## Review boundary

Review or fact-check the document set against its selected prebuilt, stated sources, and requested platforms or storefronts. These operations are read-only: do not create, rename, delete, or edit any document file. If the user also requests corrections, finish the review findings first and treat the corrections as a separate update operation.

## Routing and location checks

- The artifact is a design-system decision source, not a UI implementation, asset-production request, FDD, or architecture design.
- Exactly one prebuilt fits each output set's purpose; a combined review repeats the checks independently for every set.
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
- `app-store-page` has no `stores/` file unless at least one storefront is in scope for the existing set.
- Every storefront represented by the set resolves to exactly one file after confirmed alias deduplication. Existing files outside the current review focus remain valid members of the set.
- Mutable visual asset sizes, counts, formats, placements, dependencies, and validity rules are supported by current first-party material checked for the document's revision.
- Storefront files exclude general listing copy, tags, categories, pricing, and legal submission fields.
- Inaccessible or conflicting official material is recorded as an explicit limitation; it is not silently replaced with third-party claims.
- Platform- or store-specific differences have not been generalized into the common contract.

Report missing or stale platform and storefront files as findings. Do not create them during review or fact-check, and do not treat valid pre-existing files outside the requested review focus as unrequested artifacts.

## Quality bar

A reader can start at `index.md`, locate any governed concept, identify its authority and current decision, and determine whether a platform or store overrides it without encountering duplicate or unsupported rules.
