# Inline Completion

## API boundary and version

This guidance is checked against IntelliJ Community `idea/2026.3` at commit
`c91871ae2864649d952825cff72569e3db0e7ac6`. The
[`InlineCompletionProvider` declaration](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/platform-impl/codeinsight-inline/src/com/intellij/codeInsight/inline/completion/InlineCompletionProvider.kt)
and [`com.intellij.inline.completion.provider` EP metadata](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/lang-impl/resources/intellij.platform.lang.impl.xml)
are external-plugin API in that version.
[`InlineCompletionEvent.ManualCall`](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/platform-impl/codeinsight-inline/src/com/intellij/codeInsight/inline/completion/InlineCompletionEvent.kt)
is public but `@ApiStatus.Experimental`; use it only with an explicit minimum IDE version and
expect source and binary changes. Internal neighboring EPs and members remain forbidden.

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
implementation class. Do not use nearby internal inline-completion EPs, their implementation
classes, or reflection-based workarounds.

### Provider shape

Implement `InlineCompletionProvider` for plugin-owned gray text suggestions. Keep
`isEnabled(event)` cheap: check settings, editor kind, file type, or event type only. Do PSI
walking, network calls, model inference, or expensive text analysis inside the suspending
suggestion computation, with cancellation respected.

For a minimal provider and its `plugin.xml` registration, see
[`examples/inline_completion_provider/`](../examples/inline_completion_provider/).
Compile it with the Kotlin `jvmDefault` setting from `01_core_gradle_project.md`; otherwise
the compiler bridges the internal `isEditorTypeSupported` default into the provider class and
`verifyPlugin` fails on internal API usage.

### Events and request lifecycle

`InlineCompletionEvent` creates the `InlineCompletionRequest`. The request carries the
`file`, `editor`, `document`, `startOffset`, `endOffset`, the triggering event, and sometimes
a `lookupElement`.

Important event handling rules from the platform implementation:

- `DocumentChange` is created by the platform after typing. A third-party plugin should type
  check it but not construct it.
- `DirectCall` is used by the IDE's inline completion action. Its constructor is deprecated
  for external creation and scheduled to become internal.
- `ManualCall` is the public, experimental path for manually targeting a specific provider in
  2026.2.2 and 2026.3. The provider still has to return `true` from `isEnabled`. Pass the
  provider id to its constructor, but do not read `providerId` back: that getter is
  `@ApiStatus.Internal`.
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
Plugins should not create `DirectCall` directly. For plugin-owned manual invocation on
2026.2.2 and 2026.3, use the experimental `InlineCompletionEvent.ManualCall` and the
provider id so only the intended provider is queried. Prefer typing-triggered completion when the plugin does not
need a manual action.

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
