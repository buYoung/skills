# Interaction & Touch

Guidelines for touch interactions and general interactive element states. Touch rules ensure usability on mobile devices, while interaction guidelines cover the visual feedback states that all interactive elements require.

## Touch

### Touch Target Size

- **Severity**: High
- **Platform**: Mobile
- **Description**: Small buttons and links are difficult to tap accurately, especially for users with motor impairments.
- **Do**: Use minimum 44x44px touch targets (WCAG recommendation).
- **Don't**: Create tiny clickable areas.
- **Good Example**: `min-h-[44px] min-w-[44px]`
- **Bad Example**: `w-6 h-6` (24px) buttons

### Touch Spacing

- **Severity**: Medium
- **Platform**: Mobile
- **Description**: Adjacent touch targets that are too close cause accidental taps on the wrong element.
- **Do**: Use minimum 8px gap between touch targets.
- **Don't**: Pack clickable elements tightly together.
- **Good Example**: `gap-2` between buttons
- **Bad Example**: `gap-0` or `gap-1` between interactive elements

### Gesture Conflicts

- **Severity**: Medium
- **Platform**: Mobile
- **Description**: Custom gestures can conflict with system-level gestures like swipe-to-go-back or swipe-to-navigate.
- **Do**: Avoid horizontal swipe on main content areas; prefer vertical scroll as primary interaction.
- **Don't**: Override system gestures with custom gesture handlers.
- **Good Example**: Vertical scroll as primary navigation
- **Bad Example**: Horizontal-swipe-only carousel blocking system back gesture

### Tap Delay

- **Severity**: Medium
- **Platform**: Mobile
- **Description**: The legacy 300ms tap delay on mobile browsers makes interactions feel laggy.
- **Do**: Use `touch-action` CSS property to eliminate tap delay.
- **Don't**: Accept the default mobile tap handling without optimization.
- **Good Example**: `touch-action: manipulation`
- **Bad Example**: No touch optimization, 300ms delay on every tap

### Pull to Refresh

- **Severity**: Low
- **Platform**: Mobile
- **Description**: Accidental pull-to-refresh can cause data loss or disrupt the user's current task.
- **Do**: Disable pull-to-refresh where it's not needed.
- **Don't**: Enable pull-to-refresh by default everywhere.
- **Good Example**: `overscroll-behavior: contain`
- **Bad Example**: Default overscroll behavior on form-heavy pages

### Haptic Feedback

- **Severity**: Low
- **Platform**: Mobile
- **Description**: Tactile feedback through vibration improves the feel of interactions and confirms actions.
- **Do**: Use haptic feedback sparingly for confirmations and important actions.
- **Don't**: Overuse vibration feedback on every tap.
- **Good Example**: `navigator.vibrate(10)` on confirmation
- **Bad Example**: Vibrate on every single tap interaction

## Interaction

### Focus States

- **Severity**: High
- **Platform**: All
- **Description**: Keyboard users rely on visible focus indicators to know which element is currently selected. Removing focus styles breaks keyboard navigation.
- **Do**: Use visible focus rings on all interactive elements.
- **Don't**: Remove the focus outline without providing a replacement.
- **Good Example**: `focus:ring-2 focus:ring-blue-500`
- **Bad Example**: `outline-none` without an alternative focus style

### Hover States

- **Severity**: Medium
- **Platform**: Web
- **Description**: Hover feedback tells users that an element is interactive before they click.
- **Do**: Change the cursor and add a subtle visual change on hover.
- **Don't**: Provide no hover feedback on clickable elements.
- **Good Example**: `hover:bg-gray-100 cursor-pointer`
- **Bad Example**: No hover style on interactive elements

### Active States

- **Severity**: Medium
- **Platform**: All
- **Description**: Users need immediate visual feedback when they press or click an element to confirm the interaction registered.
- **Do**: Add a pressed/active state visual change.
- **Don't**: Provide no feedback during the moment of interaction.
- **Good Example**: `active:scale-95`
- **Bad Example**: No active state feedback

### Disabled States

- **Severity**: Medium
- **Platform**: All
- **Description**: Disabled elements must be clearly distinguished from enabled ones to prevent user confusion.
- **Do**: Reduce opacity and change the cursor to indicate non-interactive state.
- **Don't**: Style disabled elements the same as enabled ones.
- **Good Example**: `opacity-50 cursor-not-allowed`
- **Bad Example**: Same style for both enabled and disabled states

### Loading Buttons

- **Severity**: High
- **Platform**: All
- **Description**: If a button remains clickable during an async operation, users may submit the same action multiple times.
- **Do**: Disable the button and show a loading indicator during processing.
- **Don't**: Allow multiple clicks during processing.
- **Good Example**: `disabled={loading}` with spinner icon
- **Bad Example**: Button remains clickable while request is in flight

### Error Feedback

- **Severity**: High
- **Platform**: All
- **Description**: Users must know when something fails so they can take corrective action.
- **Do**: Show clear error messages near the problem.
- **Don't**: Fail silently with no feedback.
- **Good Example**: Red border + descriptive error message below input
- **Bad Example**: No indication that an error occurred

### Success Feedback

- **Severity**: Medium
- **Platform**: All
- **Description**: Users need confirmation that their action completed successfully.
- **Do**: Show a success message or visual change after completed actions.
- **Don't**: Complete actions silently with no confirmation.
- **Good Example**: Toast notification or checkmark animation
- **Bad Example**: Action completes with no visible feedback

### Confirmation Dialogs

- **Severity**: High
- **Platform**: All
- **Description**: Destructive or irreversible actions should require explicit user confirmation to prevent accidental data loss.
- **Do**: Show a confirmation dialog before delete or irreversible actions.
- **Don't**: Execute destructive actions on a single click.
- **Good Example**: "Are you sure?" modal before deletion
- **Bad Example**: Direct delete on click with no confirmation
