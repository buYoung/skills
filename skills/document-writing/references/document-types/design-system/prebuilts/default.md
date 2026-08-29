# `default` prebuilt

## Purpose and default root

Use this prebuilt for a platform-neutral product UI design system covering an approved design direction, foundations, tokens, components, patterns, content, accessibility, and governance. Its default output root is `docs/design-system`.

## Base document set

```text
docs/design-system/
├── index.md
├── foundations.md
├── tokens.md
├── patterns.md
├── content.md
├── accessibility.md
├── governance.md
├── components/
│   ├── index.md
│   └── <component-name>.md
└── platforms/
    └── <platform-name>.md
```

The displayed root is replaced by the resolved output root and serves as a responsibility map, not a requirement to create empty files. Always create `index.md` for a new saved set. Create another common file only when it owns at least one supplied or verified decision, or a necessary unresolved decision readers must track. `platforms/` and component files remain conditional; never create literal placeholder files.

## File responsibilities

### `index.md`

Define the system's purpose, scope, readers, approved design direction in one or two sentences, direction authority, relevant axes, validation status, document map, authoritative sources, and precedence for resolving conflicts. Identify the canonical owner of each major decision area. Do not include rejected direction hypotheses.

### `foundations.md`

Own the upper-level visual principles and invariant decisions for color, typography, spacing, sizing, layout, shape, depth, icons and imagery, and motion. Identify which decisions may vary, the conditions that permit variation, prohibited expression, and observable verification criteria. Include only approved, supplied, or verified decisions; make absent necessary decisions explicit.

### `tokens.md`

Own approved token values and meanings, token hierarchy, naming, semantic mappings, aliases, themes or modes, and deprecation rules. Distinguish source tokens, semantic aliases, and component bindings when those layers are supported by the evidence. Do not use tokens to invent or stand in for an unapproved direction, and do not invent token names or values.

### `patterns.md`

Own reusable interaction and composition patterns that span components, including their intent, participating elements, states, behavior, responsive adaptation, relevant accessibility consequences, and how invariant direction principles permit contextual variation.

### `content.md`

Own interface voice, terminology, labels, instructions, validation and error language, formatting, localization-sensitive writing, and content use or avoidance rules that the supplied system actually defines.

### `accessibility.md`

Own cross-system accessibility requirements, including perception, keyboard and alternative input, semantics, focus, contrast, scaling, reduced motion, and testing expectations supported by the inputs. Explain where accessibility constrains or corrects the approved direction. Component-specific consequences remain in the component file and cross-reference this contract.

### `governance.md`

Own contribution, review, direction approval, representative validation, direction-change triggers, decision authority, status, release, adoption, compatibility, and deprecation processes. Record the approved direction and validation result without preserving rejected hypotheses unless the user requests a separate history. Do not assign owners or lifecycle states that were not supplied.

### `components/index.md`

Map the known component inventory, canonical names, status, owner when known, and links to component files. Mark unresolved inventory decisions without generating empty component documents.

### `components/<component-name>.md`

Use this order so component contracts remain comparable:

1. Purpose
2. Anatomy
3. Variants
4. Sizes
5. States
6. Token bindings
7. Behavior
8. Composition
9. Content
10. Adaptive rules
11. Accessibility
12. Motion
13. Usage and prohibited usage

Omit a non-applicable section instead of filling it ceremonially. Mark a necessary unresolved decision where readers need to see the gap.

State how the component preserves invariant direction principles, which variants or states are variable, which adaptations are conditional, what use is prohibited, and which observable cases verify the result. Do not force every component to use identical shape, density, or expression when its function requires a documented variation.

### `platforms/<platform-name>.md`

Create only for a platform explicitly named by the user. Record conditional input, navigation, units, native-component, accessibility, motion, density, and expression differences according to [platform-adaptation.md](../platform-adaptation.md), while preserving the approved upper-level direction. When no platform is specified, keep the common contract platform-neutral and create no platform file.
