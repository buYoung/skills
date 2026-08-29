# Product UI Design System

## Purpose and scope

This is the shared visual and interaction source of truth for the web administrator product, the iOS app, the product logo, and feature icons. It defines what remains coherent across contexts and where platform, scale, density, and task flow require a different expression.

## Approved direction

The system is calm and precise, with information hierarchy visible first; corners and motion add a small amount of friendliness without turning functional UI into decoration. This direction is authoritative because it was explicitly approved and checked in a dense web data table, a short iOS completion flow, a large header logo, and 16px feature icons.

## Validation and maturity

Maturity: design-system documentation. The contrasting validation situations are: (1) a dense web administrator data table, where hierarchy and scanability must survive compact presentation; (2) a short iOS completion flow, where the next action and completion state must remain clear; (3) a large header logo, where brand presence must scale without disrupting hierarchy; and (4) 16px feature icons, where function must remain legible at small size.

## Decision classes

- **Invariant:** calm precision, visible information hierarchy, restrained friendliness in corners and motion, and a clear separation between brand expression and functional meaning.
- **Variable:** density, scale, spacing, logo prominence, and motion amplitude may change with task, viewport, and size.
- **Conditional:** web administrator layouts may remain dense for scanning; iOS may use platform-native navigation and completion conventions; the 16px icon size is a small-size condition, not a universal component size.
- **Prohibited:** decorative expression that competes with the next action or data hierarchy; identical density or identical geometry across web, iOS, logo, and icons; motion that is required to understand state.
- **Verification:** reviewers compare a dense table, a short completion flow, a large logo, and a 16px icon against the common principles and the relevant conditional owner.

## Document map and ownership

| Decision area | Canonical owner |
| --- | --- |
| Visual principles and invariant/variable rules | [foundations.md](foundations.md) |
| Approved token values and mappings | [tokens.md](tokens.md) |
| Cross-component composition and flows | [patterns.md](patterns.md) |
| Interface language and labels | [content.md](content.md) |
| Cross-system accessibility | [accessibility.md](accessibility.md) |
| Contribution, approval, and validation | [governance.md](governance.md) |
| Component inventory | [components/index.md](components/index.md) |
| Logo contract | [components/logo.md](components/logo.md) |
| Feature icon contract | [components/feature-icon.md](components/feature-icon.md) |
| Web administrator adaptation | [platforms/web.md](platforms/web.md) |
| iOS adaptation | [platforms/ios.md](platforms/ios.md) |

## Authority and precedence

The explicit approved direction and representative checks in the request are the direction authority. This set is the durable interpretation of that direction. If later platform guidance or implementation evidence conflicts with a common rule, resolve the conflict at the narrowest owner: platform-specific constraints belong in `platforms/`, component behavior belongs in its component file, and a change to the upper-level character requires governance review and new contrasting validation.

## Open decisions

Exact color, typography, spacing, motion-duration, breakpoint, and logo geometry values were not supplied or verified here. Their values remain an implementation decision owned by [tokens.md](tokens.md) or the relevant component owner; this document does not invent them.
