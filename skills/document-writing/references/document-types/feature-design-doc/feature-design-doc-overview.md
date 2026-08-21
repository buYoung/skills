# Feature Design Doc

A Feature Design Doc (FDD) is the current source of design decisions for one product feature. It tells implementers and code agents what the feature is and why without becoming an implementation plan.

## Scope gate

Use FDD only for one product feature whose behavior, user flows, domain concepts, policies, scope, alternatives, risks, or platform constraints must guide implementation.

Do not use FDD for:

- A feature introduction or explanatory overview
- A usage guide or troubleshooting runbook
- An API, database, or schema specification
- A proposal about whether to build or fund the feature
- A system or architecture design document
- An implementation plan, task list, PR sequence, or ticket breakdown

## Core boundary

FDD contains product and system design decisions. It does not contain implementation actions. Ask whether a downstream reader needs to understand or preserve a product decision, or perform a coding task. Only the first belongs in FDD.

## Select the mode

| Mode | Evidence | Read next |
| --- | --- | --- |
| Create | No FDD exists and the user wants a new or just-built feature documented | [feature-design-doc-create.md](feature-design-doc-create.md) |
| Update | The canonical FDD exists and behavior or decisions changed | [feature-design-doc-update.md](feature-design-doc-update.md) |
| Fact-check | The user asks to review, validate, audit, or verify an existing FDD | [feature-design-doc-fact-check.md](feature-design-doc-fact-check.md) |
| Normalize | Existing content mixes design and implementation or uses the wrong sections | [feature-design-doc-normalize.md](feature-design-doc-normalize.md) |

If the target path already exists, prefer Update over creating a parallel copy. Ask about mode only when the available artifact and request genuinely conflict.

## Required supporting references

Follow the selected mode. Load these only when that mode directs:

- [feature-design-doc-section-responsibilities.md](feature-design-doc-section-responsibilities.md)
- [feature-design-doc-implementation-leakage.md](feature-design-doc-implementation-leakage.md)
- [feature-design-doc-template.md](feature-design-doc-template.md)
- [feature-design-doc-validation.md](feature-design-doc-validation.md)

## Stable output contract

- Canonical path: `docs/FDD/<kebab-case-feature-name>.md`
- Index: `docs/FDD/index.md`
- Profiles: full or compact
- Body language: user's primary language
- Numbered template headings and frontmatter keys: preserve the canonical English contract
- Unknown decisions: mark explicitly rather than inventing
