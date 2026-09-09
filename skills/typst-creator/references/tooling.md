# Compiler, Resources, and Export

Checked: 2026-09-09. Use the exact target executable for each command. Paths below are placeholders for the actual project; do not claim they exist.

## Establish the Environment

Inspect `typst --version`, project build commands, the entry file, and `typst fonts`. A compiler on PATH is not evidence that it matches the requested target. Inspect that executable's `compile --help` before using version-specific flags.

Record the entry file, project root, font paths, imported packages and exact package versions, assets, input values, and export target. Resolve a missing tool or resource before interpreting the resulting failure as a source-language defect.

## Project and Package Paths

Relative strings resolve against the Typst source file that performs the file-loading call. A leading `/` means the Typst project root, not the operating system root. The CLI root defaults to the main file's directory and can be set with `--root`; every input must remain inside it. Packages have separate roots, so a string loaded inside a package can resolve somewhere different from the caller's project.

In 0.13/0.14, load bytes or create image/content values in the caller and pass those to a package API that accepts them. In 0.15, construct a `path` value in the caller to preserve that origin; see the [version-specific example](versions/0.15.md#path-values-across-files).

Pin a package import's version and inspect its documented minimum compiler and API before use. Preserve supplied templates and package configuration. An uncached package may require a network download; distinguish package-fetch failures from compiler errors. The fixtures in this skill need no external packages.

## External Inputs

CLI inputs are strings even when they look numeric or boolean. Parse deliberately:

```typst
#let limit = int(sys.inputs.at("limit", default: "10"))
#assert(limit > 0, message: "limit must be positive")
Limit: #limit
Compiler: #sys.version
```

Invoke with `typst compile --input limit=12 main.typ report.pdf`. In source, `sys.version` is a version value; compare it to a version value if an explicitly selected version-dependent implementation needs a branch. Shared-range generation normally uses the common API subset instead.

## Export Commands

Commands are templates for a project with `main.typ`. Quote multi-page output patterns so the shell does not expand them.

```sh
typst compile --root . main.typ report.pdf
typst compile --root . main.typ 'page-{p}.png'
typst compile --root . main.typ 'page-{p}.svg'
typst compile --features html --root . main.typ report.html
```

PDF is a paginated document; PNG and SVG are visual page exports. HTML exports semantic structure and does not reproduce arbitrary page layout or automatically generate matching CSS. HTML is experimental throughout this skill's supported range and still requires `--features html`; 0.14 adds typed HTML elements and 0.15 adds MathML output for equations.

### Bundle: 0.15+ Only

Bundle export is experimental and is not supported in the web app. For HTML documents in a bundle, enable both features:

```sh
typst compile --features bundle,html --format bundle main.typ site
```

Use `document("index.html", title: [...])[...]` to emit a document and `asset` for raw files. The complete [bundle fixture](../evals/fixtures/bundle.typ) emits two linked pages. Labels, queries, heading counters and states span the bundle; the page counter is per document. Do not assume documents automatically isolate all state.

### PDF Standards and Accessibility

Starting in 0.14, PDF output is tagged by default and supports PDF/UA-1 and the expanded PDF/A options. Select `--pdf-standard` values from the exact compiler's help and the requested standard; 0.15 can target multiple standards together. Compilation is only one part of conformance checking.

Use real headings and table headers, set document language and metadata, and give meaningful images alternative descriptions. Use `math.equation(alt:)` from 0.14 for textual equation descriptions. Avoid giving a whole figure alternative text when that would hide an already accessible table/code body. Keep essential information in the document body, since page headers, footers and decoration layers are not read as body content by assistive technology. Check exported reading order and links when relevant.

## Diagnose and Verify

1. Read the compiler exit status and complete diagnostics, including successful-compilation warnings.
2. Classify the failure: syntax/type, missing asset, font coverage, package/version, unsupported export, or context convergence. Fix the actual cause.
3. Recompile with the intended executable and inputs.
4. When layout matters, inspect rendered pages, text extraction, page sizes, numbering, repeated headers and reference destinations. A clean compile does not detect every clipped or missing glyph.
5. Report actual commands, compiler versions, unresolved warnings and unperformed checks.

A PDF can be rendered with an available PDF renderer, or directly export Typst pages to PNG. Compare relevant pages across requested releases without requiring pixel identity: math fonts, baselines and bug fixes can change legitimate output.

For introspection, 0.13/0.14 use `typst query`; 0.15 adds the more general `typst eval`. Prefer 0.15.1 for automated evaluation because 0.15.0 could return a successful exit status when expression evaluation failed. 0.14 introduces `--deps --deps-format make` in place of deprecated `--make-deps`. Other CLI additions and exact flags belong in the target version's help, not in a cross-version command copied blindly.

## Sources

- [Official compiler and CLI](https://github.com/typst/typst)
- [Paths and roots](https://typst.app/docs/reference/foundations/path/)
- [Package resources](https://github.com/typst/packages/blob/main/docs/resources.md)
- [System inputs](https://typst.app/docs/reference/foundations/sys/)
- [PDF](https://typst.app/docs/reference/pdf/)
- [HTML](https://typst.app/docs/reference/html/)
- [Bundle](https://typst.app/docs/reference/bundle/)
- [Accessibility](https://typst.app/docs/guides/accessibility/)
- [0.15.1 diagnostics fix](https://typst.app/docs/changelog/0.15.1/)
