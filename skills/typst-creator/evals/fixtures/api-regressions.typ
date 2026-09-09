#set page("a4", flipped: true, margin: 15mm, supplement: [p.])
#set heading(numbering: "1.")
#show heading: set text(fill: blue)
#show heading: set text(fill: navy)
#show heading.where(level: 1): it => block[
  #if it.numbering != none {
    counter(heading).display(it.numbering)
    h(0.3em)
  }
  #it.body
]

= API Regression Check <api-heading>

#figure(
  table(columns: 2, table.header([Name], [Value]), [Width], [297mm]),
  kind: table,
  caption: [Measured settings],
) <api-table>

#figure(
  image("assets/diagram.svg", width: 60mm, alt: "A circle points to a square."),
  caption: [A positional image source],
  placement: bottom,
  scope: "parent",
) <api-figure>

See @api-heading, @api-table, and @api-figure.

#let greet(name, greeting: "Hello") = [#greeting, #name!]
#greet("Reader", greeting: "Welcome")
#assert.eq("한".len(), 3)
#assert.eq("한".clusters().len(), 1)
#let body-text = text.with(font: "Libertinus Serif")
$ { a/b } quad x "where" x > 0 quad #body-text[body font] $
