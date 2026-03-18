# Forms

Guidelines for designing usable, accessible, and error-resistant forms. Forms are a primary point of user interaction and data entry—getting them right directly impacts conversion rates and user satisfaction.

## Input Labels

- **Severity**: High
- **Platform**: All
- **Description**: Every input needs a visible, persistent label. Labels tell users what information is expected and remain visible even after the field is filled.
- **Do**: Always show a label above or beside the input.
- **Don't**: Use placeholder text as the only label (it disappears on input).
- **Good Example**: `<label>Email</label><input type="email">`
- **Bad Example**: `placeholder="Email"` as the only indicator

## Error Placement

- **Severity**: Medium
- **Platform**: All
- **Description**: Error messages should appear near the problematic field so users can immediately see what needs fixing.
- **Do**: Show the error message directly below the related input.
- **Don't**: Show a single error summary only at the top of the form.
- **Good Example**: Error text under each invalid field
- **Bad Example**: All errors listed at the top of the form only

## Inline Validation

- **Severity**: Medium
- **Platform**: All
- **Description**: Validating as the user types or when they leave a field provides immediate feedback, reducing form submission errors.
- **Do**: Validate on blur for most fields.
- **Don't**: Validate only on form submission.
- **Good Example**: `onBlur` validation showing inline feedback
- **Bad Example**: Submit-only validation with delayed error discovery

## Input Types

- **Severity**: Medium
- **Platform**: All
- **Description**: Using the correct HTML input type enables browser features like appropriate keyboards, autofill, and built-in validation.
- **Do**: Use `email`, `tel`, `number`, `url`, and other semantic input types.
- **Don't**: Use `type="text"` for everything.
- **Good Example**: `type="email"` for email fields
- **Bad Example**: `type="text"` for email addresses

## Autofill Support

- **Severity**: Medium
- **Platform**: Web
- **Description**: Browser autofill saves users time and reduces errors. Proper `autocomplete` attributes help browsers fill fields correctly.
- **Do**: Use the `autocomplete` attribute properly (e.g., `autocomplete="email"`).
- **Don't**: Block or disable autofill with `autocomplete="off"` everywhere.
- **Good Example**: `autocomplete="email"` on email fields
- **Bad Example**: `autocomplete="off"` on every input

## Required Indicators

- **Severity**: Medium
- **Platform**: All
- **Description**: Users should clearly know which fields are mandatory before they start filling out the form.
- **Do**: Mark required fields with an asterisk (*) or "(required)" text.
- **Don't**: Leave users guessing which fields are required.
- **Good Example**: `* required` indicator next to label
- **Bad Example**: No indication of which fields are required

## Password Visibility

- **Severity**: Medium
- **Platform**: All
- **Description**: Allowing users to toggle password visibility reduces typos and frustration, especially on mobile.
- **Do**: Provide a toggle button to show/hide the password.
- **Don't**: Force the password to always be hidden.
- **Good Example**: Show/hide password toggle button
- **Bad Example**: Password field with no visibility option

## Submit Feedback

- **Severity**: High
- **Platform**: All
- **Description**: After submitting a form, users need to know whether the submission succeeded, failed, or is still processing.
- **Do**: Show loading state, then success or error message.
- **Don't**: Provide no feedback after the submit button is clicked.
- **Good Example**: Loading spinner → "Saved successfully" message
- **Bad Example**: Button click with no visible response

## Input Affordance

- **Severity**: Medium
- **Platform**: All
- **Description**: Form inputs should look visually distinct from static text so users know they are interactive.
- **Do**: Use clear borders, backgrounds, or other visual cues on inputs.
- **Don't**: Style inputs to look like plain text.
- **Good Example**: Inputs with visible border or background
- **Bad Example**: Borderless inputs indistinguishable from text

## Mobile Keyboards

- **Severity**: Medium
- **Platform**: Mobile
- **Description**: Mobile devices can show specialized keyboards (numeric, email, phone) based on the input type, reducing typing errors.
- **Do**: Use the `inputmode` attribute to specify the appropriate keyboard.
- **Don't**: Show the default text keyboard for all input types.
- **Good Example**: `inputmode="numeric"` for number-only fields
- **Bad Example**: Default text keyboard for phone number input
