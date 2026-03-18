# Accessibility

Guidelines for ensuring interfaces are usable by everyone, including people with disabilities. These rules cover visual, motor, cognitive, and assistive technology requirements based on WCAG standards.

## Color Contrast

- **Severity**: High
- **Platform**: All
- **Description**: Text must be readable against its background. WCAG AA requires a minimum 4.5:1 contrast ratio for normal text and 3:1 for large text.
- **Do**: Ensure minimum 4.5:1 contrast ratio for normal text.
- **Don't**: Use low-contrast text that is difficult to read.
- **Good Example**: `#333` on white background (7:1 ratio)
- **Bad Example**: `#999` on white background (2.8:1 ratio)

## Color Only

- **Severity**: High
- **Platform**: All
- **Description**: Color-blind users cannot distinguish information conveyed by color alone. Always use additional indicators like icons, text, or patterns.
- **Do**: Use icons and text labels in addition to color changes.
- **Don't**: Use red/green color as the only indicator for error/success.
- **Good Example**: Red text + error icon for validation errors
- **Bad Example**: Red border only with no icon or text

## Alt Text

- **Severity**: High
- **Platform**: All
- **Description**: Screen readers read alt text to describe images. Without it, visually impaired users miss the image's content or purpose.
- **Do**: Provide descriptive alt text for all meaningful images.
- **Don't**: Leave alt attributes empty or missing on content images.
- **Good Example**: `alt="Dog playing in park"`
- **Bad Example**: `alt=""` on a content-relevant image

## Heading Hierarchy

- **Severity**: Medium
- **Platform**: Web
- **Description**: Screen readers use heading levels for page navigation. Skipping levels or misusing headings for styling breaks this navigation.
- **Do**: Use sequential heading levels: h1, then h2, then h3.
- **Don't**: Skip heading levels or use headings purely for visual styling.
- **Good Example**: `h1` followed by `h2` followed by `h3`
- **Bad Example**: `h1` followed directly by `h4`

## ARIA Labels

- **Severity**: High
- **Platform**: All
- **Description**: Interactive elements that lack visible text (e.g., icon-only buttons) need accessible names for screen readers.
- **Do**: Add `aria-label` for icon-only buttons and non-text interactive elements.
- **Don't**: Create icon buttons without any accessible label.
- **Good Example**: `aria-label="Close menu"` on an icon button
- **Bad Example**: `<button><Icon /></button>` with no label

## Keyboard Navigation

- **Severity**: High
- **Platform**: Web
- **Description**: All functionality must be accessible via keyboard for users who cannot use a mouse or touch screen.
- **Do**: Ensure tab order matches visual order; all interactive elements are reachable.
- **Don't**: Create keyboard traps or illogical tab order.
- **Good Example**: Logical `tabIndex` for custom interactive elements
- **Bad Example**: Unreachable elements or keyboard traps in modals

## Screen Reader

- **Severity**: Medium
- **Platform**: All
- **Description**: Content should make sense when read aloud by a screen reader. Semantic HTML provides inherent meaning; div-soup does not.
- **Do**: Use semantic HTML elements (`<nav>`, `<main>`, `<article>`) and proper ARIA roles.
- **Don't**: Build everything with `<div>` and no semantics.
- **Good Example**: `<nav>`, `<main>`, `<article>`, `<aside>`
- **Bad Example**: `<div>` for everything with no semantic meaning

## Form Labels

- **Severity**: High
- **Platform**: All
- **Description**: Every input must have an associated label. Screen readers announce the label when a user focuses the input. Placeholder text alone is not sufficient.
- **Do**: Use `<label>` with `for` attribute or wrap the input inside a `<label>`.
- **Don't**: Use placeholder as the only input label.
- **Good Example**: `<label for="email">Email</label><input id="email">`
- **Bad Example**: `placeholder="Email"` as the only label

## Error Messages

- **Severity**: High
- **Platform**: All
- **Description**: Error messages must be announced to screen reader users, not just visually displayed.
- **Do**: Use `aria-live` regions or `role="alert"` for dynamic error messages.
- **Don't**: Display errors visually only without announcing them.
- **Good Example**: `<div role="alert">Password is required</div>`
- **Bad Example**: Red border only with no programmatic announcement

## Skip Links

- **Severity**: Medium
- **Platform**: Web
- **Description**: Keyboard users should be able to skip repetitive navigation blocks to reach the main content quickly.
- **Do**: Provide a "Skip to main content" link as the first focusable element.
- **Don't**: Force keyboard users to tab through all navigation items on every page.
- **Good Example**: `<a href="#main" class="sr-only focus:not-sr-only">Skip to main content</a>`
- **Bad Example**: 100+ tab presses required to reach main content

## Motion Sensitivity

- **Severity**: High
- **Platform**: All
- **Description**: Parallax effects and scroll-jacking can cause nausea and disorientation for users with vestibular disorders.
- **Do**: Respect `prefers-reduced-motion` and disable parallax/scroll effects when set.
- **Don't**: Force scroll-based effects on all users.
- **Good Example**: `@media (prefers-reduced-motion: reduce) { .parallax { transform: none; } }`
- **Bad Example**: `ScrollTrigger.create()` with no reduced-motion check
