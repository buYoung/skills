# Papers and Long Documents

Checked: 2026-09-09. Core examples target stable 0.13.0–0.15.1; additions have explicit version notes.

## Structure Before Decoration

Use `heading`, `figure`, `table.header`, `footnote`, `cite`, and `bibliography` for their semantic roles. Large bold text alone is not a heading. Document metadata and the visible title are different: configure `document(title:, author:)` in every supported version; the dedicated `title()` element is available from 0.14.

For reusable formatting, accept a content body in a template function and apply it with `show: template.with(...)`. Keep content, bibliography data, and formatting independently editable. See [Styling](styling.md) for set/show scope and font setup.

## Outlines and References

```typst
#set page(numbering: "1")
#set heading(numbering: "1.1")
#outline(title: [Contents], depth: 2)

= Introduction <intro>
See @method and #ref(<method>, form: "page").
This detail belongs in a note.#footnote[Additional explanation.]

= Method <method>
Return to @intro.
```

Attach labels to the actual referenceable element and keep them unique. A heading needs numbering for a normal numbered reference; a page reference also requires page numbering to be enabled. Use `ref(form: "page")` when the page is the intended destination. Bibliography keys and document labels share reference syntax but serve different purposes; avoid ambiguous naming.

For a list of figures or tables, select the corresponding figure kind, for example `outline(target: figure.where(kind: table), title: [Tables])`. Tables gain captions and reference numbers by being wrapped in a `figure`.

The outline entry interface changed in 0.13. Use its documented methods (`prefix`, `body`, `page`, `inner`, `indented`) rather than removed fields when customizing it.

## Bibliography and Citation

Typst accepts BibLaTeX `.bib` and Hayagriva `.yaml`/`.yml` bibliographies. A bibliography makes its entries available through `@key` and `cite(<key>)`. Only cited entries appear by default; `full: true` includes every record.

Asset-dependent fragment; run beside `evals/fixtures/assets` or copy that directory with the snippet. The bundled bibliography contains the real record `knuth1984`:

```typst
The method is discussed in @knuth1984.
#cite(<knuth1984>, supplement: [p. 10])
#bibliography("assets/references.bib", style: "ieee")
```

Keep the requested citation style. Built-in style identifiers and custom CSL files are alternatives; a custom CSL path must resolve within the project. Do not fabricate missing publication metadata or references. Missing keys and unresolved destinations are errors to resolve, not warnings to conceal.

A complete example with a real bibliographic record is [long-document.typ](../evals/fixtures/long-document.typ); its assets live beside the fixture.

### Multiple Bibliographies: 0.15+

A single document can contain multiple bibliographies starting in 0.15. Citations are automatically assigned to a suitable bibliography (typically the nearest following one containing the key). Use `bibliography(target:)` to control which citations it collects and `group` to control shared/reset numeric labels. Do not emulate this by simply adding several bibliography calls for older targets. Read the [0.15 reference](versions/0.15.md) and official bibliography API when this feature is requested.

## Long Tables and Floating Figures

- Use `table.header(repeat: true, ...)` for a real header that repeats on later pages. Merely bolding the first row does not establish that role.
- Prefer `auto` row heights for flowing prose. Fixed row sizes, cell spanning and `table.cell(breakable:)` affect which portions can break.
- Figures are normally unbreakable. For a long table wrapped in a figure, apply `show figure.where(kind: table): set block(breakable: true)`.
- Put table captions above the table with `show figure.where(kind: table): set figure.caption(position: top)`.
- Use `placement: top` or `bottom` and `scope: "parent"` for a floating figure spanning columns. `scope` does nothing when placement is `none`.
- Keep source order meaningful for reading order. A figure floating to another position is still read where it occurs logically.

Multiple header groups and subheaders require 0.14+. Inspect that version's table rules before using them.

## Output Review

Check outline and reference destinations, displayed heading/figure/table numbers, footnotes at page boundaries, table headers on continuation pages, complete bibliography entries, glyph coverage, and overflow. Confirm that headers/footers do not replace or hide page numbering unintentionally. Read the [Tooling](tooling.md) reference for PDF accessibility and export-specific checks.

## Sources

- [Bibliography](https://typst.app/docs/reference/model/bibliography/)
- [Cite](https://typst.app/docs/reference/model/cite/)
- [Outline](https://typst.app/docs/reference/model/outline/)
- [Footnote](https://typst.app/docs/reference/model/footnote/)
- [Table guide](https://typst.app/docs/guides/tables/)
- [Figure](https://typst.app/docs/reference/model/figure/)
- [Accessibility](https://typst.app/docs/guides/accessibility/)
