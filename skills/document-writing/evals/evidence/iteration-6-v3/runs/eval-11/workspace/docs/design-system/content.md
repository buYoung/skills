# Content

This file owns the interface content contract for Acme Console. It applies to labels, instructions, validation messages, errors, empty states, confirmations, and other text users need to understand or act.

## Content principles

### Invariant

- Put the user's task or outcome first. Use the same term for the same product concept throughout a flow.
- Make the next action explicit in controls and instructions; do not rely on color, position, or an icon alone to convey meaning.
- Prefer short, concrete sentences and name the affected object or result when the context does not make it obvious.
- Keep labels, helper text, validation messages, and errors adjacent to the control or state they explain.

### Variable

- Adjust detail to the user's decision: a compact label may be sufficient in a familiar control, while a destructive or irreversible action may need an explanation and confirmation.
- Use the product's established terminology and the available space to determine whether a message is inline, summarized, or expanded.

### Conditional

- For validation, identify what is wrong and how to correct it; preserve the user's entered value when the flow permits.
- For errors, describe the user-visible impact and a recoverable next step. If no user action can resolve the issue, say what will happen next or where to get help.
- For empty states, distinguish “not started,” “no results,” and “unavailable” so the user can choose the appropriate next action.

### Prohibited

- Do not use unexplained internal identifiers, implementation terms, or team shorthand in user-facing copy.
- Do not use vague failure language such as “Something went wrong” without a useful next step when one is available.
- Do not encode meaning only through capitalization, punctuation, color, iconography, or placement.
- Do not change established product names, token names, URLs, code, or integration terminology while editing this document set.

## Terminology and localization

Use one canonical term per concept. If a term is not established in the supplied sources, mark it as unresolved instead of inventing a preferred synonym. Keep text that may expand in translation free of assumptions about fixed width, word order, or grammatical gender; verify the result in the supported locales before release.

## Verification

Review representative content in at least two contrasting situations: a compact, information-dense view and a validation or error state. Confirm that the purpose, affected object, required action, and recovery path are understandable without relying on visual styling alone. The supplied set contains no recorded validation results, so those checks remain to be performed.

## Unresolved decisions

- The authoritative product glossary and supported locale list are not present in the supplied set.
- The exact voice, terminology approvals, and localization review owner are not recorded. Resolve these before treating this contract as a finalized content direction.
