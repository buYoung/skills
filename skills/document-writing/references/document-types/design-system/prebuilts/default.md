# `default` prebuilt

## Purpose and default root

Use this prebuilt for a platform-neutral product UI design system covering foundations, tokens, components, patterns, content, accessibility, and governance. Its default output root is `docs/design-system`.

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

Define the system's purpose, scope, readers, principles, document map, authoritative sources, and precedence for resolving conflicts. Identify the canonical owner of each major decision area.

### `foundations.md`

Own the supported foundations for color, typography, spacing, sizing, layout, shape, depth, icons and imagery, and motion. Include only supplied or verified decisions; make absent necessary decisions explicit.

### `tokens.md`

Own token hierarchy, naming, semantic mappings, aliases, themes or modes, and deprecation rules. Distinguish source tokens, semantic aliases, and component bindings when those layers are supported by the evidence. Do not invent token names or values.

### `patterns.md`

Own reusable interaction and composition patterns that span components, including their intent, participating elements, states, behavior, responsive adaptation, and relevant accessibility consequences.

### `content.md`

Own interface voice, terminology, labels, instructions, validation and error language, formatting, localization-sensitive writing, and content use or avoidance rules that the supplied system actually defines.

### `accessibility.md`

Own cross-system accessibility requirements, including perception, keyboard and alternative input, semantics, focus, contrast, scaling, reduced motion, and testing expectations supported by the inputs. Component-specific consequences remain in the component file and cross-reference this contract.

### `governance.md`

Own contribution, review, decision authority, status, release, adoption, change, compatibility, and deprecation processes. Do not assign owners or lifecycle states that were not supplied.

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

### `platforms/<platform-name>.md`

Create only for a platform explicitly named by the user. Record that platform's input, navigation, units, native-component, accessibility, and motion differences according to [platform-adaptation.md](../platform-adaptation.md). When no platform is specified, keep the common contract platform-neutral and create no platform file.
