---
name: typst-creator
description: Create, update, review, migrate, or diagnose Typst (.typ) source for documents, reports, papers, and presentations. Use for Typst markup, styling, scripting, math, layout, bibliography, and compiler/export issues. Resolve the compiler and generate source for stable Typst 0.13.0 through 0.15.1, including source shared across supported releases.
---

# Typst Document Creation

Create the requested Typst source using the resolved compiler's language and export capabilities. This skill covers stable 0.13.0, 0.13.1, 0.14.0, 0.14.1, 0.14.2, 0.15.0, and 0.15.1. Sources were checked on 2026-09-09; this is a documented support range, not a promise about later releases.

## Resolve the Target

Use the first applicable evidence: the user's requested version, a project toolchain/CI pin, then the active compiler's `typst --version`. Resolve a minor-only request to its supported latest patch: `0.13 → 0.13.1`, `0.14 → 0.14.2`, `0.15 → 0.15.1`. If none is established, use **0.15.1 as an assumed target**, not as a detected installation.

Record both the requested target and the executable actually available. If they differ, compilation with the available executable verifies only that version. For an unsupported release or prerelease, explain the boundary and establish a supported target or explicitly qualified best-effort work before claiming compatibility.

Establish the export target from the request or existing build. Default document creation to `.typ` source intended for PDF; preserve an existing export target. HTML and bundle export have experimental feature flags and distinct semantics.

## Select Knowledge by Task and Version

1. Open the [compatibility index](references/versions/index.md) to locate relevant additions, removals, and migration boundaries.
2. Read only the needed topic references from the table below.
3. Apply the mode-specific version route:
   - **Exact version:** Read the target minor's reference and any earlier reference the index points to for a needed feature. Earlier additions remain available unless a later change removes or alters them.
   - **Version range:** Read all minor references crossed by the range. Use the common API subset for that range. If it cannot satisfy a requested capability, explain why and offer version-specific alternatives.
   - **Migration or review:** Inspect the source and destination and every intervening minor boundary in either direction. Identify removed APIs, changed semantics, and necessary replacements.
4. A reference's restrictions on newer APIs apply only when its own minor line is the final target. They are not global prohibitions when reading that reference for an inherited feature.

For example, a 0.15 document using `title` and `frac.style` needs their 0.14 details as well as the 0.15 migration constraints. Do not interpret a missing entry as evidence that an API is unsupported.

| Task | Read |
|---|---|
| Markup, modes, headings, lists, links and labels | [Syntax](references/syntax.md) |
| Set/show rules, text, fonts and multilingual typography | [Styling](references/styling.md) |
| Values, functions, collections, imports and data | [Scripting](references/scripting.md) |
| Equations, symbols, delimiters and math fonts | [Math](references/math.md) |
| Pages, grids, tables, figures and positioning | [Layout](references/layout.md) |
| Counters, state, location, queries and convergence | [Context](references/context.md) |
| Papers, outlines, citations, footnotes and long documents | [Documents](references/documents.md) |
| Compiler, roots, packages, inputs, exports and diagnostics | [Tooling](references/tooling.md) |
| Slide pages, reusable layouts and presentation packages | [Presentations](references/presentations.md) |

### When Local Knowledge Is Insufficient

Check the target release's official changelog and source tag, and the relevant official API documentation. Current API pages describe the current release, so establish introduction/removal boundaries before applying them to older targets. Record material uncertainty if the target's behavior cannot be confirmed. Topic references are curated starting points, not exhaustive API specifications.

Use the image source as a positional argument, distinguish drawing `curve` from 0.15 file `path`, and prefer `tiling` and top-level byte-loading functions over deprecated names in new source.

## Work Sequence

1. Resolve the compiler, compatibility mode, and requested output.
2. Read the relevant references and inspect the existing template, imports, fonts, assets, labels, bibliography and export settings.
3. Write or revise source. Separate content from reusable formatting; preserve the existing document's meaningful structure and selected resources unless the requested change affects them.
4. Compile with the exact target when available and inspect diagnostics, including warnings. If unavailable, deliver source with explicit verification limits rather than inventing a successful run.
5. For document layout work, render and inspect the output for clipping, overlaps, table continuation, numbering, references and glyph coverage. For syntax-only questions, use a small compilation check when helpful without creating a full document workflow.
6. Return the source/edits and the compatibility handoff below. Provide rendered files when the task calls for them.

Successful compilation does not establish identical rendering between releases or conformance to an accessibility standard. Check the properties the user requested in the final output.

## Compatibility Handoff

Include each of the following, briefly, outside the document body unless the user wants this information in the document:

- The exact target or range, whether it was requested, pinned, detected or assumed, and the executable actually used.
- The common/topic references and minor-version references actually consulted, using their relative filenames. This makes feature provenance reviewable, including features inherited from an earlier minor release.
- Material replacements, fallbacks or export limitations; the actual compile command and result; warnings and unperformed checks.
- For range work, list the releases compiled and separately state whether rendered output was compared. Explicitly distinguish successful compilation across releases from a guarantee of identical rendering.

## Bundled Verification

The [validator](scripts/validate_version_support.py) uses Python 3.9+ and supplied Typst executables; it does not install compilers. It compiles common fixtures on each selected release and earlier feature fixtures on later releases. This is a compilation check, not a semantic or visual judge.

From the skill directory:

```sh
python3 scripts/validate_version_support.py --compiler 0.15.1=/path/to/typst
python3 scripts/validate_version_support.py --typst-0.14 /path/to/typst-0.14.2
```

Repeat `--compiler VERSION=PATH` for the seven exact releases and add `--require-all` for full coverage. Legacy minor flags retain their latest-patch meaning. Exit codes: 0 for success, 1 for verification failure, 2 for invalid arguments. Warnings and unchecked releases remain visible; a partial run is not a full-range result. Version queries time out after 10 seconds and individual compilations after 60 seconds.

See [fixture instructions](evals/fixtures/README.md) for assets, expected output, HTML/bundle checks and visual checks; [evaluation prompts](evals/evals.json) exercise the skill's behavior beyond compilation.

## Official Entry Points

- [Typst reference](https://typst.app/docs/reference/)
- [Changelog and release-specific migration notes](https://typst.app/docs/changelog/)
- [Official compiler releases](https://github.com/typst/typst/releases)
