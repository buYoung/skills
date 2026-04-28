# Highlighting Filters

Read this when a plugin must suppress false-positive syntax, annotator, or inspection
highlighting in a specific editor context.

## Choose filtering carefully

Highlight filtering is a last-mile visibility control. It hides existing `HighlightInfo`
results; it does not fix parsing, reference resolution, inspections, or project model data.
Use it only when another subsystem is correctly reporting a problem for normal code, but that
problem is invalid in a plugin-owned context.

Common examples include generated-language overlays, debugger editors, old VCS revisions, or
frameworks that make code valid through build-time generation.

## Extension points

Use `HighlightInfoFilter` through `com.intellij.daemon.highlightInfoFilter` to decide whether
a highlight should be visible. Use parser-specific syntax-error control only when the issue
is strictly parser error highlighting. Use `ExternalAnnotatorsFilter` when the goal is to
skip a specific external annotator for a file.

Keep `accept()` cheap. It runs in highlighting paths and should not perform broad PSI
resolution, index scans, or blocking I/O.

## Diagnostics checklist

1. Confirm the highlight is a false positive only in the target context.
2. Prefer fixing references, indexes, language level, or inspection logic before filtering.
3. Make the filter condition narrow: file type, editor kind, PSI context, or plugin marker.
4. Do not hide all errors for a file unless that file is not normal project source.
5. Restart highlighting with `DaemonCodeAnalyzer.restart()` after settings changes that
   affect the filter.

## Official docs

- https://plugins.jetbrains.com/docs/intellij/controlling-highlighting.html
- https://plugins.jetbrains.com/docs/intellij/syntax-highlighting-and-error-highlighting.html
