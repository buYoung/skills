# Presentations

Checked: 2026-09-09. Basic slide source below uses the 0.13.0–0.15.1 common subset and needs no package.

## Choose the Presentation Form

Use ordinary Typst pages for static PDF slides with explicit boundaries and repeated styling. For overlays, reveal sequences, themes or speaker-note workflows, inspect a suitable presentation package such as [Touying](https://typst.app/universe/package/touying/) or [Polylux](https://typst.app/universe/package/polylux/). Follow its official versioned documentation, pin the import, and confirm its compiler requirements. Do not invent a package version or mix one package's API with another's.

An existing template takes precedence over a new slide system. Typst's result is source and rendered slides; an editable PowerPoint deck is a separate deliverable, not implied by PDF slides.

## Reusable Static Slides

```typst
#set document(title: [Project Review])
#set page(paper: "presentation-16-9", margin: 15mm, numbering: "1")
#set text(size: 20pt)
#show heading.where(level: 1): set text(size: 30pt)

#let slide(title, body) = [
  #pagebreak(weak: true)
  #heading(level: 1, title)
  #v(0.5em)
  #body
]

#slide[Project Review][
  A concise overview.
]
#slide[Next Steps][
  - Review the findings
  - Agree on the next milestone
]
```

A weak page break starts each slide without introducing an initial blank page. This pattern does not constrain overflowing content to one slide automatically: check the rendered page count. Use `presentation-4-3` only when the requested display requires it.

Keep one main message per slide, use a small number of consistent layouts, and let grids divide text and visuals. Keep dense tables and derivations on additional slides rather than shrinking all text. These are defaults for readability, not a requirement to rewrite an existing presentation's content.

## Check the Actual Slides

Verify the intended number of pages and aspect ratio, readable font sizes, no clipped equations or images, consistent margins and page numbers, and no unintentional continuation pages. Inspect every slide after changing the layout. A complete three-slide example with a local image asset is [presentation.typ](../evals/fixtures/presentation.typ).

For reveal/overlay packages, verify which PDF pages correspond to one logical slide and how counters and notes are handled. Package version support is separate from the compiler compatibility of the static fixture above.

## Sources

- [Page sizes](https://typst.app/docs/reference/layout/page/)
- [Page breaks](https://typst.app/docs/reference/layout/pagebreak/)
- [Grid](https://typst.app/docs/reference/layout/grid/)
- [Touying package](https://typst.app/universe/package/touying/)
- [Polylux package](https://typst.app/universe/package/polylux/)
