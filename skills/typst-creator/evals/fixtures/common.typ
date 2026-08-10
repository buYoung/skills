#set document(
  title: [Typst Compatibility Fixture],
  author: "Typst Creator Skill",
)
#set page(paper: "a4", margin: 2cm, numbering: "1")
#set text(size: 10pt, lang: "en")
#set par(justify: true, leading: 0.65em)

#let badge(body) = box(
  fill: luma(235),
  inset: (x: 0.5em, y: 0.2em),
  radius: 2pt,
  body,
)

= Common Compatibility

This #badge[fixture] uses APIs shared by Typst 0.13.1, 0.14.2, and 0.15.1.

#grid(
  columns: (1fr, 1fr),
  gutter: 1em,
  [Markup and layout],
  [$ sum_(i=1)^n i = (n(n + 1))/2 $],
)

#table(
  columns: (1fr, auto),
  table.header([*Item*], [*Value*]),
  [Alpha], [1],
  [Beta], [2],
)

#figure(
  rect(width: 35mm, height: 12mm, fill: luma(220)),
  caption: [A portable figure],
) <compat-figure>

See @compat-figure.
