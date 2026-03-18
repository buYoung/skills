# Visual & Feedback

Guidelines for typography, content presentation, and user feedback. Typography rules ensure readability across devices, feedback guidelines ensure users always understand system status, and content rules handle data display patterns.

## Typography

### Line Height

- **Severity**: Medium
- **Platform**: All
- **Description**: Adequate line height (leading) improves readability by giving each line of text enough breathing room.
- **Do**: Use 1.5-1.75 line height for body text.
- **Don't**: Use cramped or excessive line height.
- **Good Example**: `leading-relaxed` (1.625)
- **Bad Example**: `leading-none` (1.0) making text hard to read

### Line Length

- **Severity**: Medium
- **Platform**: Web
- **Description**: Lines that are too long force the eye to travel too far, making it easy to lose track of which line comes next.
- **Do**: Limit to 65-75 characters per line.
- **Don't**: Allow full-width text on large screens.
- **Good Example**: `max-w-prose` (65ch)
- **Bad Example**: Full viewport width text on a 1440px monitor

### Font Size Scale

- **Severity**: Medium
- **Platform**: All
- **Description**: A consistent typographic scale creates visual hierarchy and helps users scan content efficiently.
- **Do**: Use a consistent modular scale (e.g., 12, 14, 16, 18, 24, 32).
- **Don't**: Use random, arbitrary font sizes.
- **Good Example**: Defined type scale system
- **Bad Example**: Arbitrary sizes with no pattern

### Font Loading

- **Severity**: Medium
- **Platform**: Web
- **Description**: When custom fonts load, they can cause layout shift if the fallback font has significantly different metrics.
- **Do**: Reserve space with a similar fallback font to minimize shift.
- **Don't**: Allow layout shift when fonts load.
- **Good Example**: `font-display: swap` + size-adjusted fallback font
- **Bad Example**: No fallback font, text reflows on font load

### Contrast Readability

- **Severity**: High
- **Platform**: All
- **Description**: Body text needs high contrast against its background for comfortable reading. Low-contrast text causes eye strain.
- **Do**: Use dark text on light backgrounds (or vice versa) with sufficient contrast.
- **Don't**: Use gray text on gray backgrounds.
- **Good Example**: `text-gray-900` on white background
- **Bad Example**: `text-gray-400` on `gray-100` background

### Heading Clarity

- **Severity**: Medium
- **Platform**: All
- **Description**: Headings must be visually distinct from body text to provide clear content hierarchy and scannability.
- **Do**: Use clear size and weight differences between headings and body.
- **Don't**: Style headings similarly to body text.
- **Good Example**: Bold + noticeably larger size for headings
- **Bad Example**: Headings the same size as body text

## Feedback

### Loading Indicators

- **Severity**: High
- **Platform**: All
- **Description**: Users need to know the system is working during operations that take longer than ~300ms.
- **Do**: Show a spinner or skeleton screen for operations exceeding 300ms.
- **Don't**: Leave the UI frozen with no feedback during loading.
- **Good Example**: Skeleton loader or spinner for async content
- **Bad Example**: Frozen UI with no loading indication

### Empty States

- **Severity**: Medium
- **Platform**: All
- **Description**: When there is no content to display, a blank screen is confusing. Empty states should guide users toward their next action.
- **Do**: Show a helpful message and a call-to-action.
- **Don't**: Display a blank, empty screen.
- **Good Example**: "No items yet. Create one!" with a create button
- **Bad Example**: Empty white space with no explanation

### Error Recovery

- **Severity**: Medium
- **Platform**: All
- **Description**: Error messages alone are not enough; users need clear next steps to recover from the error.
- **Do**: Provide clear recovery actions (retry button, help link, alternative path).
- **Don't**: Show an error message with no recovery path.
- **Good Example**: "Something went wrong. Try again" button + help link
- **Bad Example**: Error message with no actionable guidance

### Progress Indicators

- **Severity**: Medium
- **Platform**: All
- **Description**: Multi-step processes should show users where they are and how much remains.
- **Do**: Use step indicators or a progress bar.
- **Don't**: Provide no indication of progress through a multi-step flow.
- **Good Example**: "Step 2 of 4" with visual progress bar
- **Bad Example**: No step information in a wizard flow

### Toast Notifications

- **Severity**: Medium
- **Platform**: All
- **Description**: Toast messages for non-critical information should auto-dismiss to avoid cluttering the interface.
- **Do**: Auto-dismiss toasts after 3-5 seconds.
- **Don't**: Show toasts that never disappear.
- **Good Example**: Auto-dismiss toast after 4 seconds
- **Bad Example**: Persistent toast that blocks interaction

### Confirmation Messages

- **Severity**: Medium
- **Platform**: All
- **Description**: After a successful action, a brief confirmation message reassures users that their action was completed.
- **Do**: Show a brief success message.
- **Don't**: Complete actions silently.
- **Good Example**: "Saved successfully" toast notification
- **Bad Example**: No confirmation after a save action

## Content

### Truncation

- **Severity**: Medium
- **Platform**: All
- **Description**: Long content should be handled gracefully without breaking the layout. Truncated content should be expandable.
- **Do**: Truncate with ellipsis and provide an expand option.
- **Don't**: Let content overflow or get cut off without indication.
- **Good Example**: `line-clamp-2` with "Show more" expand
- **Bad Example**: Content overflows or is cut off mid-word

### Date Formatting

- **Severity**: Low
- **Platform**: All
- **Description**: Date formats vary by locale. Ambiguous formats (01/02/03) cause confusion across regions.
- **Do**: Use relative dates ("2 hours ago") or locale-aware formatting.
- **Don't**: Use ambiguous date formats.
- **Good Example**: "2 hours ago" or locale-formatted date
- **Bad Example**: `01/02/03` (ambiguous month/day/year)

### Number Formatting

- **Severity**: Low
- **Platform**: All
- **Description**: Large numbers without formatting are hard to read and compare.
- **Do**: Use thousand separators or abbreviations.
- **Don't**: Display long unformatted numbers.
- **Good Example**: `1.2K` or `1,234`
- **Bad Example**: `1234567` without formatting

### Placeholder Content

- **Severity**: Low
- **Platform**: All
- **Description**: Lorem ipsum in development makes it hard to evaluate real-world content behavior like truncation and overflow.
- **Do**: Use realistic sample data during development.
- **Don't**: Use Lorem ipsum everywhere.
- **Good Example**: Real sample content matching expected data patterns
- **Bad Example**: Lorem ipsum placeholder text
