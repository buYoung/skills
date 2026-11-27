#set page(paper: "a4", margin: 2cm, bleed: 3mm)

= Typst 0.15 Fixture

#let values = range(1, 3, inclusive: true)

Values: #values.map(str).join(", ")

#divider()

#[
  #set par(first-line-indent: (amount: 1em))
  #set par(first-line-indent: (all: true))
  #context assert.eq(par.first-line-indent, (amount: 1em, all: true))
]

Content after the thematic divider.
