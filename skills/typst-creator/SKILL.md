---
name: typst-creator
description: Create, update, review, or diagnose Typst source for documents, reports, papers, and presentations. Use whenever a task needs Typst markup, styling, scripting, math, or layout; resolve the target compiler and generate code compatible with stable Typst 0.13.0 through 0.15.1, including a common mode for output that must work across multiple supported versions.
---

# Typst Document Creation

Generate `.typ` source with syntax and APIs valid for the resolved Typst compiler. This skill supports stable Typst 0.13.0 through 0.15.1.

## Resolve the Target Version

Resolve the exact compiler before choosing APIs. Use the first available source of evidence:

1. An exact version explicitly requested by the user.
2. An exact version pinned by project CI, build commands, or toolchain configuration.
3. `typst --version` from the active workspace.
4. Typst 0.15.1 when no exact version can be established.

Do not infer a version from document syntax. Interpret a minor-only target as its latest supported patch: `0.13` as `0.13.1`, `0.14` as `0.14.2`, and `0.15` as `0.15.1`.

If the resolved version is outside 0.13.0–0.15.1 or is a prerelease, do not claim compatibility. Ask the user to select a supported target or explicitly authorize best-effort output.

## Choose Compatibility Mode

- **Exact-version mode:** Generate for one resolved release. Read the relevant common topic references and exactly one minor-version reference.
- **Range mode:** Generate one source file for multiple supported releases. Read each minor-version reference crossed by the requested range, then use only the common subset that remains valid throughout the range.
- **Migration or review mode:** Read the source and destination minor-version references. Report deprecated, removed, or behavior-changing APIs before proposing code.

In range mode, prefer forward-compatible APIs available since 0.13, such as `curve` instead of the deprecated `path` element, `tiling` instead of `pattern`, and top-level data-loading functions instead of deprecated `.decode` functions.

## Route References

Read only the common topics needed for the task, plus the version references required by the selected compatibility mode.

| Need | Reference |
|---|---|
| Markup, mode switching, headings, lists, links, references | [Syntax](references/syntax.md) |
| Set/show rules, text, paragraphs, blocks | [Styling](references/styling.md) |
| Values, collections, functions, control flow, imports | [Scripting](references/scripting.md) |
| Equations, matrices, delimiters, symbols | [Math](references/math.md) |
| Pages, grids, tables, figures, images, positioning | [Layout](references/layout.md) |
| Typst 0.13.0–0.13.1 behavior and patch notes | [Typst 0.13](references/versions/0.13.md) |
| Typst 0.14.0–0.14.2 behavior and patch notes | [Typst 0.14](references/versions/0.14.md) |
| Typst 0.15.0–0.15.1 behavior and patch notes | [Typst 0.15](references/versions/0.15.md) |

The common references intentionally omit version-specific parameters and behavior. Do not add an API from current general knowledge without checking the selected version reference.

## Work Sequence

1. Resolve the target version and compatibility mode.
2. Read the smallest relevant set of common and version references.
3. Trace user-provided templates, imports, packages, fonts, assets, and compiler options before changing source.
4. Generate or revise Typst source without changing caller-owned options or unrelated document structure.
5. Compile with the resolved compiler when it is available. Treat compilation under another version as useful evidence only for that other version.
6. Report the resolved version, references used, compatibility limits, and verification evidence.

## Compatibility Guardrails

- Preserve user-selected fonts, page options, labels, bibliography data, package versions, and export targets unless the request changes them.
- Use forward slashes in file paths. Typst 0.15 rejects backslashes in paths, and forward slashes work across the supported range.
- Avoid deprecated APIs in new range-compatible output even when an older target still accepts them.
- Keep version-specific examples in the matching version reference rather than the common topic references.
- Do not describe a compiler bug fix as a language feature available in earlier patch releases.
- Most core features need no package, but do not claim that a task needs no package when the requested capability depends on one.

## Return Contract

Return the requested `.typ` source or edits, followed by a concise compatibility handoff containing:

- resolved Typst version or version range;
- selected common and version references;
- deprecated, removed, or fallback behavior that affected the result;
- compile command and result, or an explicit statement that verification was not run.
