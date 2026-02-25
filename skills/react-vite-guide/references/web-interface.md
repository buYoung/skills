# Web Interface Patterns

UI/UX patterns for accessibility, forms, animation, performance, and content quality. Framework-agnostic patterns applicable to React + Vite SPA.

---

## Accessibility

- `aria-label` attribute provides accessible names for icon-only buttons
- `<label>` or `aria-label` associates form controls with descriptive text
- Keyboard handlers (`onKeyDown`/`onKeyUp`) enable keyboard interaction on interactive elements
- `<button>` is the semantic element for actions; `<a>`/`<Link>` is for navigation
- `alt` attribute describes image content (`alt=""` marks decorative images)
- `aria-hidden="true"` removes decorative icons from the accessibility tree
- `aria-live="polite"` announces async updates (toasts, validation) to screen readers
- Semantic HTML (`<button>`, `<a>`, `<label>`, `<table>`) provides built-in accessibility before ARIA
- Heading hierarchy (`<h1>`–`<h6>`) structures page content; skip links provide keyboard navigation to main content
- `scroll-margin-top` on heading anchors offsets fixed headers during anchor navigation

## Focus States

- `focus-visible:ring-*` or equivalent provides visible focus indicators on interactive elements
- `outline-none` / `outline: none` removes the default focus indicator; a replacement is required for accessibility
- `:focus-visible` triggers on keyboard focus only (not mouse clicks), unlike `:focus`
- `:focus-within` applies styles when any child receives focus, useful for compound controls

## Forms

- `autocomplete` and meaningful `name` attributes enable browser autofill
- Input `type` (`email`, `tel`, `url`, `number`) and `inputmode` trigger specialized mobile keyboards
- `onPaste` with `preventDefault()` blocks user paste functionality
- `htmlFor` or wrapping makes `<label>` clickable to focus its control
- `spellCheck={false}` disables spellcheck for emails, codes, and usernames
- Checkbox/radio label and control sharing a single hit target eliminates dead zones
- Submit buttons remain enabled until request starts; a spinner indicates in-flight state
- Inline errors next to fields with focus on first error provides immediate validation feedback
- Placeholders ending with `…` and showing example patterns guide input format
- `autocomplete="off"` on non-auth fields prevents password manager triggers
- `beforeunload` event or router guard warns before navigation with unsaved changes

## Animation

- `prefers-reduced-motion` media query detects user preference for reduced animation
- `transform` and `opacity` are compositor-friendly properties (GPU-accelerated)
- `transition: all` animates every property including layout-triggering ones; explicit property listing is more performant
- `transform-origin` determines the pivot point for transformations
- SVG transforms on `<g>` wrapper with `transform-box: fill-box; transform-origin: center` apply transformations relative to the element's bounding box
- Interruptible animations respond to user input mid-animation

## Typography

- `…` (ellipsis character) is the typographic standard; `...` (three dots) is not
- `"` `"` (curly quotes) are typographic standard; `"` (straight quotes) are not
- `&nbsp;` (non-breaking space) prevents line breaks: `10&nbsp;MB`, `⌘&nbsp;K`, brand names
- Loading states conventionally end with `…`: `"Loading…"`, `"Saving…"`
- `font-variant-numeric: tabular-nums` aligns numbers in columns and comparisons
- `text-wrap: balance` or `text-pretty` on headings distributes text evenly across lines

## Content Handling

- `truncate`, `line-clamp-*`, or `break-words` handle long content in text containers
- `min-w-0` on flex children enables text truncation within flex layouts
- Empty states (empty strings/arrays) require explicit handling to prevent broken UI
- User-generated content varies from short to very long inputs

## Images

- Explicit `width` and `height` on `<img>` prevents Cumulative Layout Shift (CLS)
- `loading="lazy"` defers loading for below-fold images
- `fetchpriority="high"` prioritizes loading for above-fold critical images

## Performance

- Virtualization (`virtua`, `content-visibility: auto`) handles large lists (>50 items) efficiently
- Layout reads (`getBoundingClientRect`, `offsetHeight`, `offsetWidth`, `scrollTop`) trigger forced reflow when called during render
- Batching DOM reads and writes separately avoids layout thrashing
- Uncontrolled inputs avoid re-render cost per keystroke; controlled inputs incur render cost on every change
- `<link rel="preconnect">` pre-establishes connections to CDN/asset domains
- `<link rel="preload" as="font">` with `font-display: swap` loads critical fonts early

## Navigation & State

- URL query params store UI state (filters, tabs, pagination, expanded panels) for shareability
- `<a>`/`<Link>` elements support Cmd/Ctrl+click and middle-click for new tab opening
- `nuqs` or similar libraries sync `useState` with URL parameters for deep-linkable UI
- Destructive actions support confirmation modals or undo windows

## Touch & Interaction

- `touch-action: manipulation` removes double-tap zoom delay on touch devices
- `-webkit-tap-highlight-color` controls the tap highlight color on iOS/Android
- `overscroll-behavior: contain` in modals/drawers/sheets prevents scroll chaining
- During drag operations: text selection is disabled, `inert` attribute disables interaction on dragged elements
- `autoFocus` triggers keyboard on mobile; suitable for desktop single primary inputs

## Safe Areas & Layout

- `env(safe-area-inset-*)` provides spacing values for device notches in full-bleed layouts
- `overflow-x-hidden` on containers prevents unwanted horizontal scrollbars
- CSS Flex/Grid provides layout without JavaScript measurement

## Dark Mode & Theming

- `color-scheme: dark` on `<html>` applies dark theme to native controls (scrollbar, inputs)
- `<meta name="theme-color">` sets the browser chrome color to match page background
- Native `<select>` requires explicit `background-color` and `color` for Windows dark mode

## Locale & i18n

- `Intl.DateTimeFormat` provides locale-aware date/time formatting
- `Intl.NumberFormat` provides locale-aware number/currency formatting
- `Accept-Language` header / `navigator.languages` detects user language preference

## Hover & Interactive States

- `hover:` state on buttons/links provides visual interaction feedback
- Progressive contrast increase across hover/active/focus states provides clearer state hierarchy

## Content & Copy

- Active voice pattern: "Install the CLI" vs passive "The CLI will be installed"
- Title Case (Chicago style) is the convention for headings and buttons
- Numerals represent counts: "8 deployments" vs "eight deployments"
- Specific button labels: "Save API Key" vs generic "Continue"
- Error messages include fix/next step information alongside the problem
- Second person is the standard voice; first person is not
- `&` replaces "and" in space-constrained contexts

---

## Known Anti-patterns

| Pattern | Effect |
|---------|--------|
| `user-scalable=no` / `maximum-scale=1` | Disables browser zoom |
| `onPaste` + `preventDefault` | Blocks paste functionality |
| `transition: all` | Animates layout-triggering properties |
| `outline-none` without `:focus-visible` replacement | Removes focus indicator |
| Inline `onClick` navigation without `<a>` | Breaks native link behavior |
| `<div>`/`<span>` with click handlers | Missing keyboard/screen reader support |
| Images without dimensions | Causes Cumulative Layout Shift |
| Large arrays `.map()` without virtualization | Performance degradation on >50 items |
| Form inputs without labels | Inaccessible to screen readers |
| Icon buttons without `aria-label` | Missing accessible name |
| Hardcoded date/number formats | Locale-incompatible |
| `autoFocus` without justification | Triggers mobile keyboard unexpectedly |
