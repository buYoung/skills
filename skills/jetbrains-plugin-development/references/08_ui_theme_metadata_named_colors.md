# Theme Metadata and Named Colors

Read this when a plugin exposes custom UI color keys, supports third-party themes, or fixes
hard-coded colors in custom Swing UI.

## Color usage

Use `JBColor` instead of raw `java.awt.Color` for UI colors. For theme-customizable colors,
retrieve colors by key with `JBColor.namedColor()`. If a color is read in one place and used
later during painting, use `JBColor.lazy()` so theme changes are reflected.

Do not cache a resolved color if it must react to theme or scheme changes.

## Metadata

Expose custom color keys through theme metadata so theme authors can discover and override
them. Use lower camel case and descriptive names. Prefer names that describe the component
and role, such as background, border color, or disabled foreground. Avoid names tied to
specific look-and-feel themes.

Keep metadata descriptions clear enough for theme authors. Include `since` and deprecation
metadata when applicable.

## Diagnostics checklist

1. Search custom UI for raw `Color` usage and replace with `JBColor` where appropriate.
2. Confirm every plugin-owned named color key has metadata.
3. Confirm keys are stable and not tied to Darcula, Light, or a temporary component name.
4. Test at least one light theme, one dark theme, high contrast, and the current default UI
   theme of the target branch.
5. Use UI Inspector to identify existing platform color keys before inventing new ones.

## Official docs

- https://plugins.jetbrains.com/docs/intellij/ui-faq.html
- https://plugins.jetbrains.com/docs/intellij/themes-metadata.html
- https://plugins.jetbrains.com/docs/intellij/platform-theme-colors.html
