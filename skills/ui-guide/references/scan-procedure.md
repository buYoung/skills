# Scan Procedure

Step-by-step procedure for extracting UI style information from a codebase. Follow these steps in order — skip any that don't apply to the detected stack.

## 1. Color Extraction

### Tailwind Projects
```bash
# Find Tailwind config
glob: tailwind.config.{js,ts,mjs,cjs}

# Read theme.extend.colors (or theme.colors) from config
# Extract all custom color definitions
```

Look for:
- `theme.extend.colors` — custom color tokens
- `theme.colors` — full color override
- CSS variable references: `var(--color-*)` in Tailwind config

### CSS/SCSS Projects
```bash
# Find global style files
glob: **/globals.css, **/global.css, **/variables.css, **/variables.scss, **/theme.css
glob: **/_variables.scss, **/_colors.scss, **/tokens.css

# Search for CSS custom property definitions
grep: --[a-zA-Z]+-*[a-zA-Z]*\s*: in *.css, *.scss files
```

Look for:
- `:root { --primary: ...; }` — CSS custom properties
- `$primary: ...;` — SCSS variables
- Design token files (JSON/JS/TS exporting color objects)

### Component Library Themes
```bash
# shadcn/ui
glob: **/components/ui/*, app/globals.css
# Look for @layer base { :root { ... } } and .dark { ... }

# MUI
grep: createTheme|ThemeProvider in *.tsx, *.jsx
# Read palette configuration

# Ant Design
grep: ConfigProvider|theme in *.tsx, *.jsx
```

### Output Format
For each color, record:
- **Token name** (e.g., `--primary`, `colors.brand.500`)
- **Value** (hex, hsl, rgb, oklch)
- **Usage context** (background, text, border, accent)
- **Dark mode variant** if exists

## 2. Typography Extraction

```bash
# Google Fonts imports
grep: fonts.googleapis.com|@font-face in *.css, *.html, *.tsx, *.jsx
grep: next/font|@next/font in *.ts, *.tsx, *.js, *.jsx

# Tailwind font config
# Read theme.extend.fontFamily from tailwind config

# Font size scale
grep: fontSize|font-size in tailwind.config.* or theme files

# CSS font definitions
grep: font-family|font-size|font-weight|line-height in globals/variables files
```

Record:
- **Font families** — heading font, body font, mono font
- **Size scale** — all defined sizes with their pixel/rem values
- **Weight scale** — which weights are used and where
- **Line heights** — corresponding to each size
- **Import method** — Google Fonts link, next/font, @font-face

## 3. Spacing Extraction

```bash
# Tailwind spacing overrides
# Read theme.extend.spacing from tailwind config

# Common spacing patterns in components
grep: (p|m|gap|space)-\d+ in *.tsx, *.jsx, *.vue, *.svelte (sample 10-20 files)
# Tally the most frequently used spacing values
```

Record:
- **Base unit** (typically 4px / 0.25rem in Tailwind)
- **Most used values** — top 10 spacing values by frequency
- **Consistent patterns** — e.g., "cards always use p-6", "sections use py-16"

## 4. Component Pattern Extraction

```bash
# Find component directories
glob: **/components/**/*.{tsx,jsx,vue,svelte}
glob: **/ui/**/*.{tsx,jsx,vue,svelte}

# Count components and categorize
# Read a sample of 5-10 key components to understand patterns
```

Record:
- **Component inventory** — list all reusable components
- **Naming convention** — PascalCase, kebab-case, file structure
- **Props pattern** — TypeScript interfaces, default props, variants
- **Composition pattern** — compound components, render props, slots

## 5. Layout Extraction

```bash
# Breakpoint definitions
# Read theme.extend.screens from tailwind config
grep: @media|breakpoint|screens in config and CSS files

# Container/max-width patterns
grep: max-w-|container|max-width in layout files

# Grid/flex patterns (sample layout components)
grep: grid-cols|grid-rows|flex|gap in layout files
```

Record:
- **Breakpoints** — all defined breakpoints with px values
- **Container strategy** — max-width, padding, centering approach
- **Grid system** — column counts, gap sizes, common patterns
- **Responsive approach** — mobile-first vs desktop-first

## 6. Icon Extraction

```bash
# Icon library detection
grep: lucide-react|@heroicons|react-icons|@phosphor-icons|@tabler/icons in package.json
grep: import.*Icon|import.*icon in *.tsx, *.jsx (sample)

# Custom SVG icons
glob: **/icons/**/*.svg, **/assets/icons/*
```

Record:
- **Library** — which icon library/libraries are used
- **Size convention** — default sizes (w-4 h-4, w-5 h-5, etc.)
- **Custom icons** — count and location of custom SVGs

## 7. Dark Mode Extraction

```bash
# Detection strategy
grep: dark:|\.dark|prefers-color-scheme|data-theme in *.css, *.tsx, *.jsx, *.vue
grep: darkMode|dark_mode in tailwind.config.*, next.config.*

# Token switching
# Compare :root vs .dark CSS custom properties
```

Record:
- **Strategy** — class-based (`dark:` prefix), media query, data attribute
- **Toggle mechanism** — next-themes, custom toggle, system preference
- **Token mapping** — which tokens change between light and dark
- **Coverage** — which components properly support dark mode

## 8. Accessibility Scan

```bash
# Focus styles
grep: focus:|focus-visible:|:focus|outline in *.css, tailwind.config.*
grep: ring-|outline-|focus: in *.tsx, *.jsx (sample)

# ARIA usage
grep: aria-|role= in *.tsx, *.jsx, *.vue (sample)

# Reduced motion support
grep: motion-reduce|prefers-reduced-motion in *.css, *.tsx

# Skip navigation
grep: skip-to|skip-nav|skipnav in *.tsx, *.jsx
```

Record:
- **Focus style** — ring, outline, custom style
- **ARIA patterns** — commonly used roles and aria attributes
- **Motion** — reduced motion support present/absent
- **Keyboard navigation** — skip links, tab order management

## Scan Tips

- **Don't read every file.** Sample 10-20 representative component files to identify patterns. Only read more if patterns are unclear.
- **Prioritize config files.** Tailwind config, theme files, and global CSS contain 80% of the design system information.
- **Note inconsistencies.** If you find conflicting patterns (e.g., some components use `p-4` and others use `p-5` for the same purpose), document both and flag it.
- **Check `package.json`** for UI-related dependencies — this quickly reveals the component library, icon library, and animation approach.
