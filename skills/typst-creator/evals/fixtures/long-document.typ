#set document(title: [Reproducible Experiment Report], author: "Typst Creator")
#set page("a5", margin: 14mm, numbering: "1 / 1")
#set text(size: 10pt)
#set heading(numbering: "1.")
#show figure.where(kind: table): set block(breakable: true)
#show figure.where(kind: table): set figure.caption(position: top)

#align(center)[
  #text(18pt, weight: "bold")[Reproducible Experiment Report]
]
#outline(title: [Contents])

= Overview <overview>
This report checks document structure, references, and table continuation.
The reference is a real bibliographic record. @knuth1984
A note remains attached to this paragraph.#footnote[Fixture note.]

#figure(
  image("assets/diagram.svg", width: 70%, alt: "A circle points to a square."),
  caption: [Processing stages],
) <stages>
See @stages and @results.

#pagebreak()
= Results <results>
#figure(
  table(
    columns: (auto, 1fr, auto),
    inset: 5pt,
    table.header(repeat: true, [*Trial*], [*Observation*], [*Score*]),
    ..range(1, 61).map(i => ([#i], [Recorded observation #i], [#(i * 2)])).flatten(),
  ),
  kind: table,
  caption: [All sixty observations],
) <results-table>

= Interpretation
All sixty trials are shown in @results-table.
The procedure is described in @overview.

#bibliography("assets/references.bib", style: "ieee")
