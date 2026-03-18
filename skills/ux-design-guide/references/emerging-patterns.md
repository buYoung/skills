# Emerging Patterns

Guidelines for newer interaction paradigms including AI interfaces, spatial computing, sustainability, and specialized UX patterns. These rules address areas that are rapidly evolving and increasingly important in modern applications.

## AI Interaction

### Disclaimer

- **Severity**: High
- **Platform**: All
- **Description**: Users must know when they are interacting with AI-generated content. Transparency builds trust and sets appropriate expectations.
- **Do**: Clearly label AI-generated content with visible indicators.
- **Don't**: Present AI output as human-written without disclosure.
- **Good Example**: "AI Assistant" label on AI-generated responses
- **Bad Example**: Fake human name without AI label

### Streaming

- **Severity**: Medium
- **Platform**: All
- **Description**: Waiting for a full AI response before displaying it makes the interface feel unresponsive, especially for long outputs.
- **Do**: Stream text responses token by token with a typewriter effect.
- **Don't**: Show a loading spinner for 10+ seconds while waiting for the full response.
- **Good Example**: Typewriter streaming effect showing incremental output
- **Bad Example**: Spinner until 100% complete, then full text dump

### Feedback Loop

- **Severity**: Low
- **Platform**: All
- **Description**: AI systems improve through user feedback. Providing easy feedback mechanisms helps improve output quality over time.
- **Do**: Include thumbs up/down buttons or a "Regenerate" option on AI outputs.
- **Don't**: Display static, read-only AI output with no feedback mechanism.
- **Good Example**: Feedback component with rating and regenerate buttons
- **Bad Example**: Read-only text with no user feedback options

## Spatial UI

### Gaze Hover

- **Severity**: High
- **Platform**: VisionOS
- **Description**: In spatial computing, elements should respond to eye tracking (gaze) before the user performs a pinch gesture, providing discoverability.
- **Do**: Scale or highlight elements when the user looks at them.
- **Don't**: Keep elements static until pinch interaction.
- **Good Example**: `.hoverEffect()` modifier for gaze response
- **Bad Example**: `onTap` only with no gaze feedback

### Depth Layering

- **Severity**: Medium
- **Platform**: VisionOS
- **Description**: Spatial UI needs Z-depth to visually separate content from the environment and other UI layers.
- **Do**: Use glass materials and z-offset to create depth.
- **Don't**: Use flat, opaque panels that block the spatial view.
- **Good Example**: `.glassBackgroundEffect()` with depth offset
- **Bad Example**: `bg-white` flat panel in spatial environment

## Sustainability

### Auto-Play Video

- **Severity**: Medium
- **Platform**: Web
- **Description**: Auto-playing videos consume significant data and energy, especially on mobile connections and battery-powered devices.
- **Do**: Use click-to-play or pause video when it scrolls off-screen.
- **Don't**: Auto-play high-resolution video loops.
- **Good Example**: `<video playsInline muted preload="none">` with play button
- **Bad Example**: `<video autoplay loop>` with high-resolution content

### Asset Weight

- **Severity**: Medium
- **Platform**: Web
- **Description**: Heavy 3D models, uncompressed images, and large assets increase page weight, load times, and carbon footprint.
- **Do**: Compress assets and lazy load heavy resources like 3D models.
- **Don't**: Load uncompressed, full-size assets upfront.
- **Good Example**: Draco-compressed 3D models with lazy loading
- **Bad Example**: Raw `.obj` files loaded on page init

## Onboarding

### User Freedom

- **Severity**: Medium
- **Platform**: All
- **Description**: Users should always be able to skip or exit tutorials and onboarding flows. Forced tours frustrate returning users and power users.
- **Do**: Provide Skip and Back buttons on all onboarding steps.
- **Don't**: Force users through a linear, unskippable tour.
- **Good Example**: "Skip Tutorial" button visible on every step
- **Bad Example**: Locked overlay that cannot be dismissed until tutorial is finished

## Search

### Autocomplete

- **Severity**: Medium
- **Platform**: Web
- **Description**: Autocomplete predictions help users find results faster and reduce typing effort, especially on mobile.
- **Do**: Show search predictions as the user types with debounced API calls.
- **Don't**: Require users to type the full query and press enter.
- **Good Example**: Debounced fetch with dropdown suggestions
- **Bad Example**: No search suggestions until form submission

### No Results

- **Severity**: Medium
- **Platform**: Web
- **Description**: A blank "no results" screen is a dead end that frustrates users. Always provide next steps.
- **Do**: Show "No results" with alternative suggestions, popular items, or search tips.
- **Don't**: Display a blank screen or minimal "0 results" text.
- **Good Example**: "No results found. Try searching for X instead" with suggestions
- **Bad Example**: "No results found." with no further guidance

## Data Entry

### Bulk Actions

- **Severity**: Low
- **Platform**: Web
- **Description**: Editing items one by one in a list is tedious and time-consuming. Bulk operations dramatically improve efficiency for power users.
- **Do**: Allow multi-select with checkbox columns and bulk action bars.
- **Don't**: Limit users to single-row actions only.
- **Good Example**: Checkbox column + floating action bar for selected items
- **Bad Example**: Repeated individual actions on each row

## Dark Mode

### Color Token System

- **Severity**: High
- **Platform**: All
- **Description**: Dark mode requires a semantic color token system rather than hardcoded colors. Tokens ensure consistent theming and easy theme switching.
- **Do**: Use semantic color tokens (e.g., `--color-bg-primary`, `--color-text-primary`) that map to different values per theme.
- **Don't**: Hardcode hex colors directly in components.
- **Good Example**: `color: var(--color-text-primary)` with light/dark theme definitions
- **Bad Example**: `color: #333333` hardcoded throughout

### Contrast Ratio Maintenance

- **Severity**: High
- **Platform**: All
- **Description**: Dark backgrounds require careful contrast management. Colors that work on light backgrounds often fail WCAG contrast checks on dark backgrounds.
- **Do**: Verify contrast ratios separately for both light and dark themes; adjust token values per theme.
- **Don't**: Assume light-mode colors will have sufficient contrast in dark mode.
- **Good Example**: `--color-text-primary: #E0E0E0` (dark mode) vs `#1A1A1A` (light mode), both meeting 4.5:1
- **Bad Example**: Same `#666666` text color used in both themes (fails on dark backgrounds)

### Image and Media Handling

- **Severity**: Medium
- **Platform**: All
- **Description**: Images, logos, and media designed for light backgrounds can look jarring or unreadable on dark backgrounds.
- **Do**: Provide dark-mode variants for logos and illustrations; apply subtle background or border to images when needed.
- **Don't**: Display light-mode-only assets without adjustment in dark mode.
- **Good Example**: `<source srcset="logo-dark.svg" media="(prefers-color-scheme: dark)">`
- **Bad Example**: White-background logo displayed on dark surface with no adaptation

### System Preference Detection

- **Severity**: Medium
- **Platform**: All
- **Description**: Users set their preferred color scheme at the OS level. Applications should respect this preference by default while allowing manual override.
- **Do**: Detect `prefers-color-scheme` and apply the matching theme; provide a manual toggle that persists.
- **Don't**: Ignore system preferences or force a single theme.
- **Good Example**: `@media (prefers-color-scheme: dark) { :root { --color-bg: #121212; } }` + theme toggle
- **Bad Example**: Light mode only with no dark mode support

### Transition Animations

- **Severity**: Low
- **Platform**: All
- **Description**: Abrupt theme switches (light to dark or vice versa) can be visually jarring, especially in low-light environments.
- **Do**: Apply a smooth transition (150-300ms) on theme change for background and text colors.
- **Don't**: Switch themes instantly with no transition.
- **Good Example**: `body { transition: background-color 200ms ease, color 200ms ease; }`
- **Bad Example**: Instant theme swap with no easing
