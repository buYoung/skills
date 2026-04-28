# Inspection Options and Suppression

Read this when a plugin adds configurable inspection options, migration from Swing options
panels, suppression behavior, or inspection descriptions.

## Declarative options

For 2023.1+ targets, prefer declarative inspection options through
`InspectionProfileEntry.getOptionsPane()`. The platform renders consistent settings UI and
binds controls to inspection fields or a custom `OptionController`.

Use a custom option controller when options live in maps, nested settings objects, or shared
persistent state. Use Swing-based `createOptionsPanel()` only for older branches or complex
legacy UI. If both declarative and Swing options are present, modern branches prefer the
declarative pane.

## Shared and custom option UI

For options shared with other features, store settings in a service or persistent component
and expose controls from the inspection settings page. Experimental custom component APIs
exist for non-standard controls; treat them as branch-sensitive.

## Suppression and descriptions

Keep inspection names, messages, quick-fix labels, and descriptions short and problem-focused.
Provide an HTML description under `inspectionDescriptions/` using the inspection short name.

When implementing suppression, ensure the suppression ID matches the registered inspection
and does not suppress unrelated inspections. Suppression should be explicit and reversible.

## Diagnostics checklist

1. Prefer declarative options on 2023.1+ target branches.
2. Confirm option binding identifiers match real fields or a custom controller.
3. Confirm option changes restart analysis when the inspection result depends on them.
4. Confirm the description file name matches the inspection short name.
5. Confirm suppression IDs and scope affect only the intended inspection.

## Official docs

- https://plugins.jetbrains.com/docs/intellij/inspection-options.html
- https://plugins.jetbrains.com/docs/intellij/code-inspections.html
- https://plugins.jetbrains.com/docs/intellij/inspections.html
