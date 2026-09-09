# Compatibility Fixtures

These files are executable examples for the supported stable releases. Paths are relative to the fixture file; keep `assets/` beside it. No external Typst packages are required. The SVG is a package-authored diagram and the BibLaTeX record is a real bibliographic entry.

## PDF Matrix

Run from the skill directory with Python 3.9+:

```sh
python3 scripts/validate_version_support.py --compiler 0.13.0=/path/to/typst-0.13.0
python3 -m unittest discover -s scripts -p 'test_*.py'
```

Repeat `--compiler VERSION=PATH` for 0.13.0, 0.13.1, 0.14.0, 0.14.1, 0.14.2, 0.15.0 and 0.15.1, then add `--require-all`. The three legacy `--typst-0.13`, `--typst-0.14` and `--typst-0.15` options mean 0.13.1, 0.14.2 and 0.15.1 respectively. Duplicate releases are rejected. The compiler version must match the requested release exactly; prereleases are rejected.

| Fixture | Releases | Expected behavior |
|---|---|---|
| `common.typ` | All seven | One A4 page with a grid, captioned figure and table |
| `api-regressions.typ` | All seven | One landscape A4 page; heading/table/figure numbered references; positional image; named argument; UTF-8 length assertions |
| `context.typ` | All seven | State totals 2 then 5; one heading and matching query; contextual counter assertions |
| `long-document.typ` | All seven | A5 report; 60 rows and repeated headers across pages; outline, footnote, caption and IEEE reference |
| `presentation.typ` | All seven | Exactly three 16:9 slides; no initial blank page; visible slide numbers, diagram, equation |
| `resources.typ` | All seven | Specific, wildcard and aliased imports; caller-loaded bytes passed to a helper; computed value 84 |
| `typst-0.13.typ` | 0.13.0 and later | Reversed list and JSON decoded from bytes |
| `typst-0.14.typ` | 0.14.0 and later | Dedicated title and skewed fractions |
| `typst-0.15.typ` | 0.15.0 and later | A4 trim with 3mm bleed on every edge; divider and inclusive sequence 1, 2, 3 |
| `typst-0.15-path.typ` | 0.15.0 and later | Caller-created path passed to a helper in another directory; decoded value 42 |

The validator checks compiler identity, exit status and a newly created nonempty PDF. It preserves warnings and reports unchecked releases. It does not install executables, assert all rendered values, check PDF/UA conformance, or prove pixel identity.

## Inspect the Output

To retain a PDF for inspection, compile a fixture directly with the chosen executable. From the skill directory:

```sh
typst compile --root . evals/fixtures/long-document.typ /tmp/long-document.pdf
pdfinfo -box /tmp/long-document.pdf
pdftotext -layout /tmp/long-document.pdf -
pdftoppm -png -scale-to 1000 /tmp/long-document.pdf /tmp/long-document
```

Inspect every representative page for clipping, overlap, glyph coverage, table continuation, numbered references and footnotes. Count all 60 observations, confirm the header repeats, and check that the bibliography entry and reference destinations exist. Inspect the page aspect ratio and numbers on all three slides.

For the bleed fixture, compare `MediaBox` and `TrimBox`: each trim edge is inset by approximately 8.504pt (3mm). Text extraction should show the inclusive range's endpoints and all three values. Check a real `divider()` call, since inserting its function value can compile while displaying the word `divider`.

Font-dependent snippets in the references require the named static fonts or suitable replacements established through `typst fonts`. Compiler/font differences can legitimately change pagination; assess the required layout properties rather than demanding pixel equality for arbitrary documents.

## Experimental Export Fixtures

These checks are separate from the PDF validator. From the skill directory:

```sh
typst compile --features html --root . evals/fixtures/html.typ /tmp/typst-check.html
typst compile --features bundle,html --format bundle --root . evals/fixtures/bundle.typ /tmp/typst-bundle-check
```

The HTML fixture supports all seven releases; inspect its heading, paragraph, emphasis and list elements. The bundle fixture requires 0.15.0 or 0.15.1 and should produce linked `index.html` and `details.html` files. Experimental-export warnings are expected and should remain visible. These fixtures do not certify arbitrary HTML layouts or production readiness.

## Reference Snippets and Behavioral Evaluations

Independent `typst` code blocks in the references can be compiled separately with their documented target and resources. The import, bibliography, image, and 0.15 helper/path fragments require the bundled `assets/` directory. Run their source beside that directory (as the complete fixtures do), or copy the directory with the snippet. They are not self-contained files, but their dependencies are supplied. Use `resources.typ` and `typst-0.15-path.typ` to verify imports and cross-file loading through the final consumer.

The prompts in [evals.json](../evals.json) assess source generation, migration, editing, compiler absence and output review. Keep those behavioral results separate from fixed-fixture compilation. For old/new comparisons, use the same inputs and exact executables, record missing runs as infrastructure limitations, and compare only matching completed pairs.

See the [2026-09-09 validation record](../../updates/2026-09-09-validation.md) for measured results and limitations of this revision.
