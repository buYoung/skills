# Layout & Responsive

Guidelines for managing layout systems and building responsive interfaces. Layout rules prevent visual bugs from stacking contexts and overflow issues, while responsive guidelines ensure the UI adapts gracefully across screen sizes.

## Layout

### Z-Index Management

- **Severity**: High
- **Platform**: Web
- **Description**: Stacking context conflicts cause hidden or overlapping elements. A defined scale prevents z-index wars.
- **Do**: Define a z-index scale system (10, 20, 30, 50).
- **Don't**: Use arbitrary large z-index values.
- **Good Example**: `z-10 z-20 z-50` (systematic scale)
- **Bad Example**: `z-[9999]` scattered throughout codebase

### Overflow Hidden

- **Severity**: Medium
- **Platform**: Web
- **Description**: Hidden overflow can clip important content like dropdowns, tooltips, or error messages without the developer noticing.
- **Do**: Test that all content fits within containers; use `overflow-auto` with scroll when needed.
- **Don't**: Blindly apply `overflow-hidden` without checking content.
- **Good Example**: `overflow-auto` with visible scrollbar
- **Bad Example**: `overflow-hidden` silently truncating content

### Fixed Positioning

- **Severity**: Medium
- **Platform**: Web
- **Description**: Fixed elements can overlap each other or become inaccessible, especially on mobile with safe areas.
- **Do**: Account for safe areas and other fixed elements; ensure they don't stack carelessly.
- **Don't**: Stack multiple fixed elements without considering their overlap.
- **Good Example**: Fixed nav + fixed bottom bar with adequate gap
- **Bad Example**: Multiple overlapping fixed elements

### Stacking Context

- **Severity**: Medium
- **Platform**: Web
- **Description**: New stacking contexts reset z-index scope. Properties like `transform`, `opacity < 1`, and `position: fixed` create new contexts.
- **Do**: Understand what creates new stacking contexts and plan accordingly.
- **Don't**: Expect z-index to work across different stacking contexts.
- **Good Example**: Parent with z-index properly isolating children
- **Bad Example**: `z-index: 9999` not working because of stacking context boundary

### Content Jumping

- **Severity**: High
- **Platform**: Web
- **Description**: Layout shift when content loads is jarring and disorienting. It causes accidental clicks and poor perceived performance (CLS).
- **Do**: Reserve space for async content using aspect-ratio or fixed dimensions.
- **Don't**: Let images or dynamic content push the layout around.
- **Good Example**: `aspect-ratio: 16/9` or fixed height placeholders
- **Bad Example**: No dimensions on images causing layout shift

### Viewport Units

- **Severity**: Medium
- **Platform**: Web
- **Description**: `100vh` is problematic on mobile browsers because the browser chrome (address bar, toolbar) is not accounted for.
- **Do**: Use `dvh` (dynamic viewport height) or account for mobile browser chrome.
- **Don't**: Use `100vh` for full-screen mobile layouts.
- **Good Example**: `min-h-dvh` or JavaScript-based viewport calculation
- **Bad Example**: `h-screen` on mobile causing content to hide behind browser chrome

### Container Width

- **Severity**: Medium
- **Platform**: Web
- **Description**: Text content that spans the full viewport width is hard to read. Optimal line length is 65-75 characters.
- **Do**: Limit `max-width` for text content.
- **Don't**: Let text span the full viewport width on large screens.
- **Good Example**: `max-w-prose` or `max-w-3xl`
- **Bad Example**: Full-width paragraphs on wide monitors

## Responsive

### Mobile First

- **Severity**: Medium
- **Platform**: Web
- **Description**: Designing for mobile first and enhancing for larger screens produces cleaner, more maintainable CSS.
- **Do**: Start with mobile styles, then add breakpoints for larger screens.
- **Don't**: Design desktop-first, causing mobile layout issues.
- **Good Example**: Default mobile styles + `md:` `lg:` `xl:` breakpoints
- **Bad Example**: Desktop default + `max-width` queries for mobile

### Breakpoint Testing

- **Severity**: Medium
- **Platform**: Web
- **Description**: Testing only on your own device misses layout bugs at other common screen sizes.
- **Do**: Test at 320, 375, 414, 768, 1024, and 1440px widths.
- **Don't**: Only test on your device.
- **Good Example**: Multiple device/viewport testing across breakpoints
- **Bad Example**: Single device development and testing

### Touch Friendly

- **Severity**: High
- **Platform**: Web
- **Description**: Mobile web layouts need touch-sized interactive targets even if they appear on a web page.
- **Do**: Increase touch target sizes on mobile breakpoints.
- **Don't**: Keep the same tiny desktop-sized buttons on mobile.
- **Good Example**: Larger buttons on mobile via responsive classes
- **Bad Example**: Desktop-sized targets on mobile viewports

### Readable Font Size

- **Severity**: High
- **Platform**: All
- **Description**: Text must be readable on all devices without zooming. Small text causes eye strain and accessibility failures.
- **Do**: Use minimum 16px body text on mobile.
- **Don't**: Use tiny text on mobile.
- **Good Example**: `text-base` (16px) or larger for body text
- **Bad Example**: `text-xs` (12px) for body text on mobile

### Viewport Meta

- **Severity**: High
- **Platform**: Web
- **Description**: The viewport meta tag is required for proper mobile rendering. Without it, mobile browsers render at desktop width.
- **Do**: Use `width=device-width, initial-scale=1`.
- **Don't**: Omit the viewport meta tag.
- **Good Example**: `<meta name="viewport" content="width=device-width, initial-scale=1">`
- **Bad Example**: No viewport meta tag in the HTML head

### Horizontal Scroll

- **Severity**: High
- **Platform**: Web
- **Description**: Horizontal scrolling is unexpected on most pages and indicates layout overflow bugs.
- **Do**: Ensure all content fits within the viewport width.
- **Don't**: Allow content wider than the viewport.
- **Good Example**: `max-w-full overflow-x-hidden`
- **Bad Example**: Horizontal scrollbar appearing on mobile

### Image Scaling

- **Severity**: Medium
- **Platform**: Web
- **Description**: Fixed-width images overflow their containers on smaller screens.
- **Do**: Use `max-width: 100%` on images so they scale with their container.
- **Don't**: Use fixed pixel widths on images.
- **Good Example**: `max-w-full h-auto`
- **Bad Example**: `width="800"` fixed on an image tag

### Table Handling

- **Severity**: Medium
- **Platform**: Web
- **Description**: Wide tables overflow their containers on mobile screens, breaking the layout.
- **Do**: Use horizontal scroll wrapper or card layout for tables on mobile.
- **Don't**: Let wide tables break the viewport.
- **Good Example**: `overflow-x-auto` wrapper around tables
- **Bad Example**: Table overflowing the viewport with no scroll wrapper
