# Compatibility Index

Checked: 2026-09-09. Supported stable releases: 0.13.0, 0.13.1, 0.14.0, 0.14.1, 0.14.2, 0.15.0, 0.15.1.

Use this index to find feature details without mistaking a release's changes for its entire API. The rows are selected compatibility boundaries, not a complete function inventory. Common topic examples use the 0.13+ subset unless labelled otherwise.

## Feature Routes

| Capability | Available from | Read for detail | Later boundary |
|---|---|---|---|
| Proper paragraphs, configurable first-line indentation, outline entry methods | 0.13.0 | [0.13](0.13.md) | 0.15 folds partial indentation dictionaries |
| Page references, reversed enums, document description | 0.13.0 | [0.13](0.13.md) | Still available in 0.14 and 0.15 |
| `curve`, `tiling`, encoded bytes passed to loaders | 0.13.0 | [0.13](0.13.md) | Old aliases removed in 0.15 |
| PDF attachments | 0.13.0 | [0.13](0.13.md), [0.14](0.14.md) | `pdf.embed` renamed to `pdf.attach` in 0.14; old alias removed in 0.15 |
| `title`, multiple table headers, `math.frac.style`, equation alternative descriptions | 0.14.0 | [0.14](0.14.md) | Available in 0.15 too |
| Character justification limits, PDF/WebP images | 0.14.0 | [0.14](0.14.md) | PDF image source needs correct page selection |
| `array.sorted(by:)`, `str.normalize`, module membership, selected method defaults | 0.14.0 | [0.14](0.14.md) | Check which method has the parameter; do not generalize to every method |
| Tagged PDF, PDF/UA-1 and expanded PDF/A support | 0.14.0 | [0.14](0.14.md), [Tooling](../tooling.md) | Tagging alone does not prove accessibility |
| Experimental HTML | 0.13.0 | [Tooling](../tooling.md) | Typed elements in 0.14; MathML in 0.15; feature flag still required |
| File `path` values, `divider`, variable fonts, bleed, marker alignment | 0.15.0 | [0.15](0.15.md) | Not common to the entire supported range |
| `selector.within`, `counter.display(at:)`, dictionary/arguments map/filter, inclusive range | 0.15.0 | [0.15](0.15.md) | `within` works in introspection, not show rules |
| Multiple bibliographies, experimental bundle export | 0.15.0 | [0.15](0.15.md), [Documents](../documents.md), [Tooling](../tooling.md) | Bundle requires feature flags |
| `typst eval` CLI | 0.15.0 | [0.15](0.15.md) | Evaluation-failure exit status fixed in 0.15.1 |

## Apply the Final Target

An exact 0.15 task using `title` reads the 0.14 addition plus the 0.15 reference. The sentence in the 0.14 reference excluding 0.15-only features governs a **0.14 final target**, not that 0.15 task.

For 0.13–0.15 shared source, draw with `curve`, use `tiling`, and decode via `json(bytes(...))`. Do not add `title`, `page.bleed`, or `path` values to that common source. There is no single unchanged attachment API across the entire range; report that boundary rather than silently dropping attachments.

For migration, read every boundary between the source and destination. Rendering differences and compiler bug fixes can require output inspection even when the source API remains valid.

## Sources and Unknown APIs

- [0.13.0 changelog](https://typst.app/docs/changelog/0.13.0/)
- [0.14.0 changelog](https://typst.app/docs/changelog/0.14.0/)
- [0.15.0 changelog](https://typst.app/docs/changelog/0.15.0/)
- [Official source tags](https://github.com/typst/typst/tags)

If an API is absent here, use the relevant official API page and establish its availability against the target release's changelog or tagged source. Absence from this curated table is not proof of non-support.
