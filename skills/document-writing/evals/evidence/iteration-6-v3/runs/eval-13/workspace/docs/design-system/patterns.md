# Patterns

## Pattern contract

Patterns describe composition and behavior that span components. They preserve the common direction—one clear primary action, quiet support, and structured density—while adapting to task complexity.

## Known patterns

### Settings task

- **Intent:** help a user review or change a bounded set of preferences.
- **Composition:** grouped settings, concise descriptions, local controls, and one clear commit or save action when a commit is required.
- **Variable:** groups may expand or contract with the number and dependency of settings.
- **Accessibility:** labels and descriptions remain programmatically associated; status and validation are announced through the common accessibility contract.
- **Verification:** in the validated simple settings situation, the user can identify the changed group and the primary commit action without scanning competing controls.

### Dense data view

- **Intent:** support comparison, scanning, and action over structured information.
- **Composition:** a stable heading and context, aligned columns, visible row or cell relationships, and actions placed where their scope is clear.
- **Variable:** row density and grouping may respond to information volume, but relationships and the primary action remain discoverable.
- **Accessibility:** the data structure and headers remain exposed to assistive technology; keyboard navigation and focus order follow the web adaptation.
- **Verification:** in the validated dense table situation, a user can locate the primary action and understand row/column relationships without relying on color alone.

## Cross-pattern rules

- Keep the primary action singular within a task context; if multiple actions are equally consequential, the unresolved hierarchy must be recorded rather than hidden.
- Place errors, confirmations, and status near the affected content while preserving the main task path.
- Adapt density to content, not to arbitrary visual sameness.
- Link component-level behavior to the canonical component contract when component files are added.

