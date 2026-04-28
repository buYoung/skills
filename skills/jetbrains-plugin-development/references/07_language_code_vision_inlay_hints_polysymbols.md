# Code Vision, Inlay Hints, and Polysymbols

### Code Vision and Inlay Hints

- **Inlay Hints** (`<inlayHintsProvider>` for the legacy API; `DeclarativeInlayHintsProvider`
  for 2023.2+): inline visual hints (parameter names, types).
- **Code Vision** (`<codeVision.provider>`): contextual line-level annotations (usages
  count, references).

Both run off the EDT and report via small data structures the platform schedules and
re-computes incrementally.

### Polysymbols

A unified symbol model used across plugins (Vue, Angular, Astro, etc.). Useful when you
want to interoperate with web-style polyglot files. Verify the API against the target IDE
branch before implementation.
