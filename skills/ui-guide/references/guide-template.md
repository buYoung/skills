# Guide Template

Use this template structure when generating the UI style guide. Replace all `{placeholder}` values with actual data from the codebase scan. Remove any section that has no relevant data in the project.

---

## Template Start

```markdown
# UI Style Guide — {Project Name}

> Auto-generated from codebase analysis. Last updated: {YYYY-MM-DD}
>
> **Stack:** {framework} + {css-approach} | **Component Library:** {library or "Custom"}

---

## Table of Contents

- [Colors](#colors)
- [Typography](#typography)
- [Spacing](#spacing)
- [Layout](#layout)
- [Components](#components)
- [Icons](#icons)
- [Dark Mode](#dark-mode)
- [Accessibility](#accessibility)
- [Conventions](#conventions)

---

## Colors

### Primary Palette

| Token | Value | Preview | Usage |
|-------|-------|---------|-------|
| `--primary` | {value} | ![](https://via.placeholder.com/16/{hex}?text=+) | Buttons, links, key actions |
| `--secondary` | {value} | | Supporting elements |
| `--accent` | {value} | | Highlights, badges |
| `--destructive` | {value} | | Errors, delete actions |

### Neutral Palette

| Token | Value | Usage |
|-------|-------|-------|
| `--background` | {value} | Page background |
| `--foreground` | {value} | Primary text |
| `--muted` | {value} | Secondary text, borders |
| `--card` | {value} | Card backgrounds |
| `--border` | {value} | Dividers, input borders |

### Semantic Colors

| Purpose | Light | Dark |
|---------|-------|------|
| Success | {value} | {value} |
| Warning | {value} | {value} |
| Error | {value} | {value} |
| Info | {value} | {value} |

### Usage Guidelines

- Use `--primary` for main CTAs and interactive elements
- {Additional guidelines based on actual usage patterns}
- {Flag any inconsistencies found}

---

## Typography

### Font Stack

| Role | Family | Import |
|------|--------|--------|
| Heading | {font} | `{import statement}` |
| Body | {font} | `{import statement}` |
| Mono | {font} | `{import statement}` |

### Type Scale

| Name | Size | Weight | Line Height | Usage |
|------|------|--------|-------------|-------|
| `display` | {value} | {weight} | {lh} | Hero headlines |
| `h1` | {value} | {weight} | {lh} | Page titles |
| `h2` | {value} | {weight} | {lh} | Section titles |
| `h3` | {value} | {weight} | {lh} | Card titles |
| `body` | {value} | {weight} | {lh} | Default text |
| `small` | {value} | {weight} | {lh} | Labels, captions |

### Usage

```{css-or-tailwind}
{Example code showing how to apply each type style}
```

---

## Spacing

### Scale

| Token | Value | Common Usage |
|-------|-------|-------------|
| `1` | 4px / 0.25rem | Tight gaps |
| `2` | 8px / 0.5rem | Icon gaps, inline spacing |
| `4` | 16px / 1rem | Component padding |
| `6` | 24px / 1.5rem | Card padding |
| `8` | 32px / 2rem | Section gaps |
| `16` | 64px / 4rem | Section padding |

### Patterns

| Context | Horizontal | Vertical | Gap |
|---------|-----------|----------|-----|
| Cards | `p-{x}` | `p-{y}` | `gap-{n}` |
| Sections | `px-{x}` | `py-{y}` | — |
| Form fields | — | — | `space-y-{n}` |
| Button groups | — | — | `gap-{n}` |

---

## Layout

### Breakpoints

| Name | Min Width | Target |
|------|-----------|--------|
| `sm` | {value} | Mobile landscape |
| `md` | {value} | Tablet |
| `lg` | {value} | Desktop |
| `xl` | {value} | Wide desktop |
| `2xl` | {value} | Ultra-wide |

### Container

```{css-or-tailwind}
{Container setup — max-width, margin, padding}
```

### Grid Patterns

```{css-or-tailwind}
{Most common grid patterns used in the project}
```

---

## Components

### Inventory

| Component | Location | Variants | Notes |
|-----------|----------|----------|-------|
| Button | `{path}` | {variants} | {notes} |
| Card | `{path}` | {variants} | {notes} |
| Input | `{path}` | {variants} | {notes} |
| {etc.} | | | |

### Naming Convention

- File naming: `{pattern}` (e.g., PascalCase.tsx)
- Component naming: `{pattern}`
- Props interface: `{pattern}` (e.g., `{Name}Props`)

### Common Props Pattern

```typescript
{Example of the typical props pattern used in this project}
```

---

## Icons

### Library

- **Primary:** {library name} ({package})
- **Size convention:** {default size class}
- **Color:** {how colors are applied — currentColor, explicit, etc.}

### Usage

```{tsx-or-jsx}
{Example of correct icon usage in this project}
```

### Custom Icons

{Count} custom SVG icons in `{path}`. Follow the same size and color conventions.

---

## Dark Mode

### Strategy

- **Method:** {class-based / media-query / data-attribute}
- **Toggle:** {next-themes / custom / system-only}
- **Default:** {light / dark / system}

### Token Mapping

| Token | Light | Dark |
|-------|-------|------|
| `--background` | {value} | {value} |
| `--foreground` | {value} | {value} |
| `--card` | {value} | {value} |
| {etc.} | | |

### Implementation

```{css-or-tailwind}
{How to apply dark mode variants in this project}
```

---

## Accessibility

### Focus Styles

```{css-or-tailwind}
{Focus ring/outline pattern used in this project}
```

### ARIA Patterns

{Common ARIA usage found in components}

### Motion

- Reduced motion: {supported / not supported}
- Animation library: {framer-motion / CSS / none}

```{css-or-tailwind}
{Motion-safe/motion-reduce pattern if present}
```

### Checklist

- [ ] Color contrast ratio meets WCAG AA (4.5:1 for text)
- [ ] All interactive elements have visible focus indicators
- [ ] Images have alt text
- [ ] Form inputs have associated labels
- [ ] Skip navigation link present
- [ ] Reduced motion preference respected

---

## Conventions

### File Organization

```
{Actual file structure pattern for UI-related files}
```

### Import Order

```typescript
{Import ordering convention observed in the project}
```

### Style Application

{How styles are applied — utility classes, CSS modules, styled-components, etc. with examples}

---

> **Recommendations:** {Any improvement suggestions based on best practices}
>
> **Inconsistencies Found:** {Any conflicting patterns that should be resolved}
```

## Template End

---

## Customization Notes

- Remove sections that don't apply (e.g., no Dark Mode section if the project doesn't support it)
- Add project-specific sections as needed (e.g., Animation, Theming, Brand Colors)
- The `Preview` column in color tables uses placeholder images — the user can replace with actual swatches in their documentation tool
- Keep code examples in the project's actual syntax (Tailwind classes, CSS, SCSS, etc.)
