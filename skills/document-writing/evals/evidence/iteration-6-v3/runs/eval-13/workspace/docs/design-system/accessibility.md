# Accessibility

## Contract

Accessibility is an invariant constraint on the approved calm-precision direction. Clear hierarchy must remain perceivable, operable, understandable, and robust when users change input method, zoom, contrast, motion, or assistive technology settings.

## Requirements

- **Perception:** do not communicate meaning through color, shape, position, or motion alone; preserve readable text and distinguishable states.
- **Keyboard and alternative input:** every task and control must be operable without a pointer; focus must be visible and follow a meaningful order. Web-specific details are in [platforms/web.md](platforms/web.md).
- **Semantics:** expose native or equivalent roles, names, values, relationships, and state changes to assistive technology.
- **Focus:** keep focus visible, stable through updates, and placed at the next meaningful context after a transient surface closes or content changes.
- **Scaling and reflow:** content and controls must remain usable when text or viewport presentation changes; dense layouts must not hide required information.
- **Reduced motion:** honor the user's reduced-motion preference and preserve orientation without relying on animation.
- **Testing:** verify the simple settings screen and dense data table with keyboard-only operation, assistive technology semantics, zoom/reflow, contrast/state perception, and reduced motion.

## Component consequence

Component documents must state their names, roles, states, focus behavior, keyboard behavior, and motion behavior, and link back to this contract. Platform-specific semantics and native-element precedence remain conditional in the web document.

