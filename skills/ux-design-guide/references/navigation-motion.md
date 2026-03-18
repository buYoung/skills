# Navigation & Motion

Guidelines for navigation patterns and animation behavior. Navigation ensures users can move through an application predictably, while motion guidelines ensure animations enhance rather than hinder the experience.

## Navigation

### Smooth Scroll

- **Severity**: High
- **Platform**: Web
- **Description**: Anchor links should scroll smoothly to the target section rather than jumping abruptly, providing spatial context for the user.
- **Do**: Use `scroll-behavior: smooth` on the html element.
- **Don't**: Jump directly without transition.
- **Good Example**: `html { scroll-behavior: smooth; }`
- **Bad Example**: `<a href='#section'>` without CSS smooth scroll

### Sticky Navigation

- **Severity**: Medium
- **Platform**: Web
- **Description**: Fixed navigation bars should not obscure page content. When a nav is pinned to the top, the content below must account for the nav's height.
- **Do**: Add `padding-top` to the body equal to the nav height.
- **Don't**: Let the nav overlap the first section of content.
- **Good Example**: `pt-20` (if nav is `h-20`)
- **Bad Example**: No padding compensation for fixed nav

### Active State

- **Severity**: Medium
- **Platform**: All
- **Description**: The current page or section should be visually indicated so users always know where they are in the application.
- **Do**: Highlight the active nav item with color or underline.
- **Don't**: Leave all navigation links styled identically with no visual feedback on current location.
- **Good Example**: `text-primary border-b-2`
- **Bad Example**: All links same style regardless of current page

### Back Button

- **Severity**: High
- **Platform**: Mobile
- **Description**: Users expect the back button to work predictably, returning them to the previous state or screen without data loss.
- **Do**: Preserve navigation history properly using `history.pushState()`.
- **Don't**: Break browser or app back button behavior with `location.replace()`.
- **Good Example**: `history.pushState()`
- **Bad Example**: `location.replace()` destroying back history

### Deep Linking

- **Severity**: Medium
- **Platform**: All
- **Description**: URLs should reflect the current application state so users can share or bookmark specific views.
- **Do**: Update the URL on state and view changes using query params or hash.
- **Don't**: Use static URLs for dynamic content.
- **Good Example**: Use query params or hash routing
- **Bad Example**: Single URL for all application states

### Breadcrumbs

- **Severity**: Low
- **Platform**: Web
- **Description**: Breadcrumbs show the user's location in the site hierarchy and provide quick navigation to parent levels.
- **Do**: Use breadcrumbs for sites with 3+ levels of navigation depth.
- **Don't**: Use breadcrumbs for flat, single-level sites where they add no value.
- **Good Example**: `Home > Category > Product`
- **Bad Example**: Breadcrumbs only on deep nested pages with no parent links

## Animation

### Excessive Motion

- **Severity**: High
- **Platform**: All
- **Description**: Too many simultaneous animations cause distraction and can trigger motion sickness in sensitive users.
- **Do**: Animate 1-2 key elements per view maximum.
- **Don't**: Animate everything that moves.
- **Good Example**: Single hero animation on page load
- **Bad Example**: `animate-bounce` on 5+ elements simultaneously

### Duration Timing

- **Severity**: Medium
- **Platform**: All
- **Description**: Animations should feel responsive, not sluggish. Overly long animations slow down the perceived interaction speed.
- **Do**: Use 150-300ms for micro-interactions.
- **Don't**: Use animations longer than 500ms for UI transitions.
- **Good Example**: `transition-all duration-200`
- **Bad Example**: `duration-1000` making UI feel laggy

### Reduced Motion

- **Severity**: High
- **Platform**: All
- **Description**: Users with vestibular disorders or motion sensitivity can configure their OS to prefer reduced motion. Applications must respect this setting.
- **Do**: Check `prefers-reduced-motion` media query and provide alternatives.
- **Don't**: Ignore accessibility motion settings.
- **Good Example**: `@media (prefers-reduced-motion: reduce) { * { animation: none; } }`
- **Bad Example**: No motion query check at all

### Loading States

- **Severity**: High
- **Platform**: All
- **Description**: Users need feedback during asynchronous operations to know the system is working.
- **Do**: Use skeleton screens or spinners to indicate loading progress.
- **Don't**: Leave the UI frozen with no feedback.
- **Good Example**: `animate-pulse` skeleton placeholder
- **Bad Example**: Blank screen while loading data

### Hover vs Tap

- **Severity**: High
- **Platform**: All
- **Description**: Hover effects don't work on touch devices. Critical interactions must not depend on hover alone.
- **Do**: Use click/tap handlers for primary interactions.
- **Don't**: Rely only on hover for important actions.
- **Good Example**: `onClick` handler for all interactive elements
- **Bad Example**: `onMouseEnter` only with no tap alternative

### Continuous Animation

- **Severity**: Medium
- **Platform**: All
- **Description**: Infinite animations are distracting and consume battery/CPU. They should be reserved for functional indicators.
- **Do**: Use continuous animation for loading indicators only.
- **Don't**: Use continuous animation for decorative elements.
- **Good Example**: `animate-spin` on a loading spinner
- **Bad Example**: `animate-bounce` on decorative icons

### Transform Performance

- **Severity**: Medium
- **Platform**: Web
- **Description**: Some CSS properties trigger expensive layout recalculations and repaints. Using transform and opacity leverages GPU acceleration.
- **Do**: Use `transform` and `opacity` for animations.
- **Don't**: Animate `width`, `height`, `top`, or `left` properties.
- **Good Example**: `transform: translateY(10px)`
- **Bad Example**: `top: 10px` animation triggering layout recalculation

### Easing Functions

- **Severity**: Low
- **Platform**: All
- **Description**: Linear motion feels robotic and unnatural. Easing functions create more natural-feeling animations.
- **Do**: Use `ease-out` for entering elements and `ease-in` for exiting elements.
- **Don't**: Use `linear` for UI transitions.
- **Good Example**: `transition-timing-function: ease-out`
- **Bad Example**: `transition-timing-function: linear` for UI elements
