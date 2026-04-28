# Inline Completion

## Contents

  - What this feature is
  - Registration
  - Provider shape
  - Events and request lifecycle
  - Debouncing and cancellation
  - Rendering elements
  - Direct calls
  - Diagnostics checklist


Inline completion is the gray, in-editor suggestion surface that appears at the caret. It is
separate from popup completion (`CompletionContributor`): popup completion produces lookup
items, while inline completion streams `InlineCompletionElement`s through an
`InlineCompletionProvider`.

Use this reference when the user asks for "ghost text", gray inline suggestions, AI-style
editor completions, direct inline completion invocation, or a provider that reacts to typing
without opening the lookup popup. Use `07_language_completion.md` instead for `Ctrl+Space` lookup items.

### Registration

Register a provider with the `com.intellij.inline.completion.provider` extension point.
The provider's `id` property should match the extension `id`. Prefer the fully-qualified
provider class name so two plugins do not collide on a short id.

The public extension point list declares this EP with `InlineCompletionProvider` as its
implementation class. Do not use nearby internal inline-completion EPs unless the user
explicitly accepts branch-locked internal API risk.

### Provider shape

Implement `InlineCompletionProvider` for plugin-owned gray text suggestions. Keep
`isEnabled(event)` cheap: check settings, editor kind, file type, or event type only. Do PSI
walking, network calls, model inference, or expensive text analysis inside the suspending
suggestion computation, with cancellation respected.

If code is needed for a task, put the runnable provider skeleton under `examples/` and link
to it from this file instead of embedding the sample here.

### Events and request lifecycle

`InlineCompletionEvent` creates the `InlineCompletionRequest`. The request carries the
`file`, `editor`, `document`, `startOffset`, `endOffset`, the triggering event, and sometimes
a `lookupElement`.

Important event handling rules from the platform implementation:

- `DocumentChange` is created by the platform after typing. A third-party plugin should type
  check it but not construct it.
- `DirectCall` is used by the IDE's inline completion action. Its constructor is deprecated
  for external creation and scheduled to become internal.
- `ManualCall` is the public-style path for manually targeting a specific provider. The
  provider still has to return `true` from `isEnabled`.
- Newer requests cancel and hide older inline completion proposals.
- Requests are canceled if inline completion is already in rendering mode.
- `restartOn(event)` lets a provider restart an existing session when a later event should
  recompute the shown suggestion.

### Debouncing and cancellation

Typing can generate a request per character. If proposal computation is expensive, extend
`DebouncedInlineCompletionProvider` instead of implementing delay by hand. Avoid using
deprecated forcing hooks; branch against the debounce API available in the target IDE branch.

### Rendering elements

Most providers start with `InlineCompletionGrayTextElement`. Build a single variant with
`InlineCompletionSingleSuggestion.build { emit(...) }`. Use the lower-level
`InlineCompletionSuggestion` builder only when you need multiple variants or streaming.

If text is inserted and the provider needs cleanup or custom insertion behavior, override
`insertHandler`. If already-rendered elements should update while the user types, override
`suggestionUpdateManager`.

### Direct calls

The IDE action calls `InlineCompletionEvent.DirectCall` through `CallInlineCompletionAction`.
Plugins should not create `DirectCall` directly. For plugin-owned manual invocation, use
`InlineCompletionEvent.ManualCall` and the provider id so only the intended provider is
queried.

When a direct call returns no result, the platform's no-suggestions handler waits for inline
completion and Next Edit sources before showing the "No suggestions" hint. See
`07_language_next_edit_suggestions.md` for that integration point.

### Diagnostics checklist

1. Confirm the `plugin.xml` tag uses `inline.completion.provider`, not
   `completion.contributor`.
2. Confirm the extension `id` equals `InlineCompletionProvider.id.id`.
3. Confirm `isEnabled(event)` returns true for the event the user is exercising.
4. Confirm `getSuggestion` returns at least one variant and at least one element.
5. Confirm no previous request is being canceled by a newer request before rendering.
6. For typing-driven providers, add debounce before expensive computation.
7. For direct invocation, do not construct `DirectCall`; use the platform action or
   `ManualCall`.
8. Run Plugin Verifier against target IDE builds because parts of this surface are still
   branch-sensitive.
