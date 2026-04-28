# Next Edit Suggestions

## Contents

  - Public documentation boundary
  - Public API boundary
  - No-suggestions behavior
  - Implementation routing
  - Diagnostics checklist


Next Edit Suggestions share the inline editing UX surface with inline completion, but the
public IntelliJ Platform Plugin SDK documentation does not describe a stable third-party
provider API for implementing Next Edit Suggestions.

Use this reference when the user mentions Next Edit Suggestions, `InsertNextEditAction`,
"next edit", or asks whether a plugin can implement the same feature. If the user wants a
third-party suggestion source that can actually be implemented from a plugin, route the work
to `07_language_inline_completion.md`.

### Public documentation boundary

Treat Next Edit Suggestions as a JetBrains feature surface unless the user provides a public
SDK page, plugin API artifact, or project-local source proving otherwise. Do not assume the
user has an IDE source tree, and do not require one to use this skill.

The public extension point list exposes `com.intellij.inline.completion.provider` as a
third-party extension point and marks `com.intellij.inline.edit.awaiter` as internal. That
distinction matters: inline completion can be plugin-owned; Next Edit coordination should not
be treated as a public suggestion-provider contract.

### Public API boundary

Do not implement plugin code against `InlineEditAwaiter` for Next Edit behavior:

- `InlineEditAwaiter` is annotated `@ApiStatus.Internal`.
- The extension point `com.intellij.inline.edit.awaiter` exists so the platform can wait for
  inline edit sources, not as a documented public provider contract.
- Registering a custom awaiter would only report whether something was shown; it does not
  define the algorithm, rendering, insertion, or lifecycle of a Next Edit suggestion.
- `InsertNextEditAction` may appear in keymaps or IDE actions, but an action ID alone is not
  an API for producing Next Edit Suggestions.

For plugin-owned suggestions, use `InlineCompletionProvider` and document the behavior as
inline completion, not Next Edit Suggestions.

### No-suggestions behavior

When the user invokes inline suggestion behavior directly, the IDE may consider more than one
inline edit source before deciding whether to show a "No suggestions" hint. Do not couple a
plugin to internal notifier classes for this behavior. A plugin-owned provider should return
its own inline-completion result and let the IDE handle the surrounding hint lifecycle.

### Implementation routing

When a user asks to build Next Edit-like behavior:

- First explain that the public SDK does not expose a stable third-party Next
  Edit provider contract.
- If the requested behavior is "show a suggested edit at the caret", implement it with
  `InlineCompletionProvider`; see `07_language_inline_completion.md`.
- If the requested behavior is "jump to next changed location", that is a different IDE
  action family and not Next Edit Suggestions.
- If the requested behavior depends on JetBrains AI or LLM plugin internals, require the
  user to provide that plugin source or official API documentation before writing code.

### Diagnostics checklist

1. Check public SDK docs, extension point metadata, or user-provided project sources before
   assuming Next Edit provider API availability.
2. Treat `@ApiStatus.Internal` classes as forbidden for plugin code unless the user explicitly
   accepts branch-locked internal API risk.
3. Do not create a sample `next.edit.provider` EP; no such public EP was found in the
   public SDK documentation.
4. If the feature can be expressed as gray text at the caret, use
   `inline.completion.provider`.
5. Verify the resulting plugin with Plugin Verifier against the exact IDE branches the user
   supports.
