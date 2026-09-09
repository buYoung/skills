#set document(title: [Experiment Review], author: "Typst Creator")
#set page(paper: "presentation-16-9", margin: 15mm, numbering: "1")
#set text(size: 20pt)
#set heading(numbering: none)
#show heading.where(level: 1): set text(size: 30pt, fill: rgb("#244967"))

#let slide(title, body) = [
  #pagebreak(weak: true)
  #heading(level: 1, title)
  #v(0.5em)
  #body
]

#slide[Experiment Review][
  A short presentation with a reusable layout.
  #v(1em)
  #text(14pt)[One source, explicit page boundaries.]
]
#slide[Method][
  #grid(
    columns: (1fr, 1fr),
    gutter: 12mm,
    [- Observe
     - Record
     - Compare],
    image("assets/diagram.svg", width: 100%, alt: "A circle points to a square."),
  )
]
#slide[Results][
  #table(columns: (1fr, 1fr), table.header([Trial], [Result]), [A], [12], [B], [18])
  #v(0.5em)
  $ x = (12 + 18) / 2 = 15 $
]
