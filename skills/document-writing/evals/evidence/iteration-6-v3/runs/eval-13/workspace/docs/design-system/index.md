# Web Product Design System

## Purpose and scope

This document set is the platform-neutral source of truth for the product UI's visual foundations, tokens, reusable patterns, content, accessibility, and governance. It covers the web product only; iOS and Android are out of scope.

## Approved direction

The product is a calm, precise work tool in which one primary action remains legible first, even when information is complex. This direction is approved by the product owner and has been validated in a simple settings screen and an information-dense data table.

## Direction authority and validation

- **Authority:** Product-owner approval supplied in the design-system brief.
- **Representative situations checked:** simple settings screen; information-dense data table.
- **Maturity:** Design-system documentation.
- **Verification outcome:** The direction preserves clear task focus in the simple view and maintains a visible primary action and hierarchy under data density.

## Decision classes

- **Invariant:** calm precision, clear primary-action hierarchy, accessible perception and operation, and separation of common rules from web-specific behavior.
- **Variable:** density, grouping, and emphasis may respond to task complexity and information volume.
- **Conditional:** keyboard/pointer behavior, web navigation, CSS units, native element precedence, web semantics, and reduced-motion handling live in [platforms/web.md](platforms/web.md).
- **Prohibited:** decorative expression or competing emphasis that obscures the task's primary action; platform-specific rules generalized into the common contract.
- **Verification:** review both the simple settings screen and dense data table at their intended sizes and interaction states; confirm that the primary action is discoverable first and that content remains operable and perceivable.

## Document map and ownership

| Decision area | Canonical owner |
| --- | --- |
| Foundations and invariant direction | [foundations.md](foundations.md) |
| Token hierarchy and semantic mappings | [tokens.md](tokens.md) |
| Cross-component composition and interaction patterns | [patterns.md](patterns.md) |
| Interface voice and terminology | [content.md](content.md) |
| Cross-system accessibility contract | [accessibility.md](accessibility.md) |
| Component inventory | [components/index.md](components/index.md) |
| Web-specific adaptation | [platforms/web.md](platforms/web.md) |
| Contribution and lifecycle governance | [governance.md](governance.md) |

## Authoritative inputs and precedence

The product-owner direction and the two supplied validation situations establish the current approved direction. When sources conflict, use this precedence: explicit product-owner decisions, then verified product requirements and accessibility requirements, then this document set's common rules, then local component or pattern guidance. Record unresolved conflicts rather than silently choosing.

