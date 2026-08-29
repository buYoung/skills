# Accessibility

This file owns cross-system accessibility requirements for Acme Console. Component-specific behavior belongs in the component's canonical file and should link back here.

## Requirements

### Invariant

- Every task and state must be understandable without relying on color, shape, position, sound, or motion alone.
- All interactive functions must be available by keyboard or an equivalent alternative input, with a visible focus indication and a logical navigation order.
- Controls, status messages, errors, and relationships must expose an accurate name, role, state, and value to assistive technology.
- Text and essential non-text information must remain perceivable when users enlarge text or use high-contrast or otherwise constrained display settings.
- Focus must not be moved unexpectedly, trapped without an intentional escape, or hidden behind persistent interface chrome.

### Variable

- Density, layout, and message length may adapt to viewport size, zoom, content length, and input method while preserving task order and meaning.
- A component may use a different presentation for touch, pointer, keyboard, or assistive input when the same operation and state remain available.

### Conditional

- Provide an equivalent text alternative for meaningful imagery, icon-only controls, and non-text status indicators; treat purely decorative imagery as non-semantic.
- Announce dynamic changes only when users need the update to continue their task, and place the announcement at the relevant context rather than interrupting unrelated work.
- Respect a user's reduced-motion preference by removing non-essential motion and preserving equivalent state and feedback.
- Pair every error with the affected field or region and a programmatically discoverable explanation of how to recover.

### Prohibited

- Do not make a control, status, or error distinguishable only by color or animation.
- Do not remove focus indicators, disable keyboard access, or create keyboard traps to preserve a visual layout.
- Do not autoplay essential motion or audio, flash content, or use motion as the only way to communicate progress or change.
- Do not add an accessibility exception for a component merely because its current visual treatment is difficult to implement.

## Verification

Check at least two contrasting situations: a default interactive flow and an error or dynamic-update flow. In each, verify keyboard traversal and focus visibility, the accessible name and state of controls, error association and recovery guidance, text and non-text perception, zoom or reflow behavior, and reduced-motion behavior where motion exists. Record the tested environment and any unresolved limitation; the supplied set contains no completed validation record.

## Ownership and unresolved decisions

Accessibility is a cross-system contract. Component owners must document local consequences and link here rather than redefine the common rule. The supplied set does not identify a conformance target, supported assistive-technology matrix, browser/platform matrix, or accessibility review owner; these decisions remain unresolved and require explicit product ownership.
