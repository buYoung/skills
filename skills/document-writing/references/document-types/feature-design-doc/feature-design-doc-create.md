# Creating a Feature Design Doc

Read the canonical template, section-responsibility map, implementation-leakage rules, validation instructions, and shared source-grounding reference before drafting.

## 1. Identify the source path

### Post-implementation

When the feature exists or was just built, treat the current implementation, session decisions, and relevant history as primary evidence. Harvest facts first and ask only for decisions that cannot be recovered.

### Pre-implementation

When the feature is still an idea, gather the minimum product decisions directly from the user before drafting.

## 2. Settle minimum inputs

Establish in one batched round:

1. Feature name
2. One-sentence definition
3. Problem statement
4. Primary users or actors
5. Target version or release boundary

For solo or continuous-delivery work without a release train, use "as implemented (YYYY-MM-DD)" when documenting current behavior.

If no live user can answer, infer only what evidence supports and mark true gaps with [NEEDS INPUT: ...].

## 3. Research before drafting

For an implemented feature:

- Read the implementation and relevant diff before relying on memory.
- Use scoped repository search such as rg to locate related concepts, schemas, configuration, and platform support.
- Compare session decisions with implemented behavior.
- Record material mismatches as deviations or open questions.
- Record alternatives only when traceable to conversation, history, or user-provided evidence.

Use external research only when the feature depends on an external standard, protocol, regulation, file format, cryptographic primitive, or platform API. Prefer primary sources. Skip generic web research for purely internal behavior.

## 4. Draft top-down

Follow the canonical template. Keep identity, non-goals, release scope, alternatives, policies, failure handling, and result states in their assigned sections.

For all cross-cutting concerns, provide concrete content or "Not applicable: <reason>". Do not leave silent gaps.

Use the full profile by default. Use compact only when all of these are true:

- One platform with no platform-conditional behavior
- No new or changed persisted data model
- No authentication or permission surface change
- No external standard or compliance involvement
- One primary user flow

## 5. Resolve and verify

Batch all remaining [NEEDS INPUT: ...] markers for the user. When no live user exists, retain the markers and identify the draft as incomplete.

Run the structural validator, fix critical findings, and either fix or explicitly accept each major finding with a reason. Then perform the semantic responsibility and implementation-leakage review.

## 6. Save and index

Save to `docs/FDD/<kebab-case-feature-name>.md`. If the file exists, stop and switch to Update. Do not create versioned or date-suffixed duplicates.

Maintain `docs/FDD/index.md` with one entry per FDD: linked feature name, one-sentence definition, profile, status, and last-verified date.
