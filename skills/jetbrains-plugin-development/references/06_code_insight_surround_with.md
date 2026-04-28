# Surround With

Read this when a plugin adds entries to Code | Surround With for selected expressions,
statements, blocks, or language-specific fragments.

## Registration and shape

Register `SurroundDescriptor` with `com.intellij.lang.surroundDescriptor`. A descriptor
identifies which selected PSI elements can be surrounded and returns applicable `Surrounder`
objects. Each surrounder performs one transformation such as wrapping a statement in an
`if`, `try`, loop, region, or language-specific construct.

Use Surround With when the user starts with an explicit selection. Use postfix templates
when the user types a suffix after an expression. Use live templates when the feature is
primarily template insertion instead of selection transformation.

## Selection and PSI rules

`getElementsToSurround()` should return meaningful PSI fragments, not arbitrary text ranges.
The resulting write must preserve formatting, undo, and caret placement. If the selected
range crosses invalid PSI boundaries, decline the action rather than trying to patch raw text.

## Diagnostics checklist

1. Confirm the language has a registered `surroundDescriptor`.
2. Confirm the selected text maps to valid PSI elements.
3. Confirm `isApplicable()` rejects invalid fragment shapes.
4. Confirm the transformation runs inside a write command and keeps undo working.
5. Confirm formatting and caret placement after expansion.

## Official docs

- https://plugins.jetbrains.com/docs/intellij/surround-with.html
