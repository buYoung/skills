# Web platform adaptation

This file records only web-specific differences from the common contract in [../index.md](../index.md). The approved direction remains calm and precise, with one primary action visible first.

## Input and interaction

- Support keyboard and pointer input as first-class paths; do not make hover the only way to reveal meaning or actions.
- Provide visible focus for keyboard users and preserve a logical focus order through menus, dialogs, popovers, and dynamic updates.
- Pointer hover, press, drag, and target-size behavior may add web-specific states, but every essential operation must have a keyboard-accessible equivalent.

## Navigation and presentation

- Use the web document structure and browser history expectations for page, dialog, disclosure, and in-page navigation.
- Preserve the user's location and context when content updates; move focus only when the interaction changes context in a way the user must understand.
- Responsive layouts may change grouping and density with viewport width, but they must retain the task's primary action and information relationships.

## Units, density, and CSS

- Use CSS-relative sizing and layout behavior so text scaling, zoom, reflow, and viewport changes do not make required content unavailable.
- Do not treat a fixed pixel value as the common design-system contract. Any approved CSS values belong in the token owner and must be tested at the intended zoom and text scale.
- Dense tables may use tighter web layouts than settings views only when rows, columns, headers, focus, and actions remain perceivable and operable.

## Native elements first

- Prefer semantic native HTML controls and document structure when they provide the required behavior and accessibility semantics.
- Use a custom control only when the product behavior cannot be represented by an appropriate native element; preserve equivalent name, role, value, state, keyboard, and focus behavior.
- Do not replace native browser interaction with styling alone when doing so removes expected semantics or user settings support.

## Accessibility semantics

- Expose headings, landmarks, form labels, descriptions, table relationships, and live state changes through the web accessibility tree.
- Use the browser's native semantics before adding ARIA; ARIA supplements a missing semantic and must not contradict the element's behavior.
- Ensure validation, loading, expansion, selection, and disabled states are both visually clear and programmatically available.

## Reduced motion

- Respect the user's reduced-motion preference in web media and runtime behavior.
- Reduce or remove non-essential transitions, parallax, autoplay, and attention-seeking motion; retain only the minimum change cue needed to preserve orientation.
- Never make the primary action, status, or essential content depend on animation to become discoverable.

## Verification

Validate both the simple settings screen and information-dense data table with keyboard-only and pointer interaction, browser zoom/text scaling, responsive reflow, native semantics or equivalent accessible names and relationships, visible focus, and reduced-motion preferences. A web adaptation passes when it preserves the common direction while the task remains understandable and operable in each tested context.

