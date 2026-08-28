# Storefront research

Use this reference only with the `app-store-page` prebuilt when at least one digital storefront is in scope. The workflow is open-ended: it supports any app, game, software, device, or publisher storefront that can be identified from the user's request and authoritative material. Examples or previously supported stores never form an allowlist.

## 1. Resolve the in-scope storefront set

Interpret the user's intended deliverables before extracting names:

- Include a storefront when the user requests a contract, update, review, or fact-check for it.
- Exclude a storefront that is explicitly out of scope or mentioned only as a comparison, counterexample, example, migration source, or background fact.
- Ask one concise question when inclusion materially changes the output and the wording does not establish intent.

Deduplicate multiple aliases only after confirming that they refer to the same official storefront. Do not normalize a broad or ambiguous retail brand into an app marketplace merely because the names are similar.

## 2. Identify the official storefront generically

For each in-scope target:

1. Start with an unambiguous official name supplied by the user or existing document.
2. When the name or product is uncertain, find the operator's official material using the participant and submission vocabulary that storefront actually uses. Depending on the product, this may be developer, publisher, partner, creator, artist, label, vendor, seller, channel, submission, help, or project documentation.
3. Derive a lowercase kebab-case slug from that official name for new files.
4. Record the official name, operator, product scope, and source used to establish identity.

This process applies equally to known and previously unseen storefronts. Do not maintain or infer a closed list of supported storefronts.

For a new file, use `stores/<official-storefront-slug>.md`. For update, rewrite, or normalize, first locate an existing file that represents the same storefront from its title, metadata, sources, and content. Reuse that path even when its filename is non-canonical; content normalization does not authorize a rename or duplicate. Rename only when the user explicitly requests a path migration.

## 3. Resolve applicability before values

Identify the product type, package or submission type, target device families, and locales that affect the storefront's visual asset requirements. Infer them from supplied material and the repository when safe.

Ask before selecting numeric requirements when an unresolved branch materially changes the contract. If no live user can answer, preserve the applicable branches as unresolved instead of silently choosing one.

Before drafting, map every material product, device, locale, placement, and media exception found in the accepted source. Record each applicable branch or explicitly mark why it is out of scope; do not collapse a source's conditional exception into one generic rule or omit it because the common case is already documented.

Do not infer a product branch from generic words such as app, listing, store, or marketplace. In particular, do not select app-only versus game-only guidance unless the supplied product evidence establishes that classification. Keep both branches conditional when the classification is unresolved, and do not present recommendation-eligibility guidance as a base submission requirement.

Separate storefront admission or product eligibility from visual-asset applicability. A visual rule for an exceptional, legacy, or already-listed product category does not prove that category is generally eligible for submission. Record the eligibility limitation when it directly controls whether the visual rule applies; otherwise leave the branch unresolved instead of presenting it as an ordinary supported path.

## 4. Acquire current first-party evidence

First check whether the environment can search and open current web sources.

When web research is available:

1. Search for the official storefront name together with its own participant or submission role terms and the relevant asset terms; do not assume every storefront calls its contributors developers or publishers.
2. Establish first-party control or an official project relationship before accepting requirements. Evidence may be an operator-controlled help property, authenticated official account, linked project site, or official source repository; a single dedicated documentation domain is not required.
3. Establish storefront identity and governance from an explicit first-party statement. A copyright footer, repository owner, hosting domain, or team label alone does not prove operator identity. Preserve relationships such as community-run, foundation-governed, vendor-hosted, or operator-provided as stated; do not force a single operator when the source does not.
4. Open the current first-party asset pages. A search-result snippet, cached summary, or remembered value is discovery evidence only.
5. Verify each material requirement in the opened source and record its URL and verification date near the requirement or in the source table.
6. Prefer the most specific current product, package, device, locale, or asset page over a general overview. Record unresolved conflicts between current first-party sources instead of choosing silently.
7. Preserve each source statement's normative strength and applicability. Do not merge adjacent requirements or recommendations into a stronger combined rule, and label team decisions separately from operator requirements.
8. Mirror normative verbs and status explicitly: `must`/required, `should`/recommended, and optional guidance remain distinct. Never place a `should` recommendation or visibility-quality suggestion under a required-submission heading or checklist item.

When web research is unavailable:

- If the storefront identity is also unclear and no current official material was supplied, create neither a storefront file nor a common partial set. Respond in conversation only: state that online research is unavailable, request the operator identity or official publisher guide, state that mutable requirements remain unverified, and do not invent a site, URL, source title, verification date, or specification.
- Ask the user for current official URLs or supplied first-party material when a live answer is possible.
- Do not invent an official domain, attempted URL, source title, verification result, or mutable requirement.
- Do not turn the local file-reading date or document-writing date into a storefront verification date. Omit the verification date unless it is stated by the supplied source or a current first-party source was actually opened and verified during this operation.
- In the storefront file and user-facing completion, state that live or online research was unavailable. Saying only that external verification was not performed does not establish the capability limitation.
- For create, update, rewrite, or normalize, a storefront file may still be produced when its identity is clear, but it must contain only supplied or previously verified facts plus an explicit research limitation and unresolved requirements.
- For review or fact-check, report the research limitation and unverifiable claims as findings without changing files.

## 5. Keep research visual-only

Research only requirements that govern a visual asset:

- Canonical asset name, role, and placement
- Required, recommended, or optional status
- Dimensions, aspect ratio, crop, safe area, transparency, and scaling
- File format, file size, count, sequence, and upload grouping
- Asset-internal content restrictions and actual-product fidelity
- Device, locale, and regional variants
- Video, trailer, poster, and thumbnail requirements
- Dependencies between assets and conditions that affect whether an asset appears

Exclude listing titles, descriptions, feature text, tags, categories, search terms, pricing, packages, age-rating forms, certification steps, and legal submission fields. A text rule belongs in the storefront file only when it directly determines whether a visual asset is valid.

Also exclude general application eligibility, complete UI localization, desktop metadata translation, and other non-visual product requirements merely encountered on an asset source page. Include only the narrow applicability consequence needed to decide whether a visual-asset rule applies, and link or mark the wider product requirement out of scope rather than restating it.

## 6. Apply operation-specific behavior

For create, update, rewrite, or normalize, create or update one file for each in-scope storefront according to the path rules above. Preserve other existing storefront files outside the change scope.

For review or fact-check, inspect the existing files and current evidence, then report missing files, stale claims, conflicts, and limitations. Do not create, rename, delete, or edit storefront files.

## 7. Storefront file responsibilities

Use this responsibility order in each storefront file:

1. Scope and applicability, including product, package, device, and locale boundaries
2. Research status and first-party source list; include a verification date only for live-opened current evidence, not merely supplied offline material
3. Asset inventory
4. Asset-specific rules and exceptions
5. Storefront-specific asset relationships and ordering
6. Device, locale, and regional variants
7. Delivery validation
8. Unresolved or conflicting requirements

The asset inventory should use applicable fields from: asset name, role or placement, status, dimensions or ratio, format, file-size limit, count, variant key, content restriction, and official source. Do not add empty fields or copy one storefront's vocabulary into another.

The common `asset-system.md` owns only cross-storefront concepts and mappings. A storefront file owns the operator's official asset names, required status, specifications, placements, and relationships. Link to the common concept without moving storefront-specific facts into it.

## 8. Handle incomplete research

Continue with verified or supplied material when first-party documentation is inaccessible or incomplete. Record the actual capability limitation, verified or supplied sources, affected requirements, and unresolved decisions. Distinguish supplied-source provenance from live verification, and omit a storefront verification date when no current first-party source was opened. Record an attempted URL only when it was actually discovered and opened. Never substitute third-party claims or remembered values.
