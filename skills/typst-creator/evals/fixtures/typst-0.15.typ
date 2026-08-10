#set page(paper: "a4", margin: 2cm, bleed: 3mm)

= Typst 0.15 Fixture

#let values = range(1, 3, inclusive: true)

Values: #values.map(str).join(", ")

#divider()

Content after the thematic divider.
