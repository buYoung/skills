# Typst Layout Reference

Page setup, positioning, and layout elements.

## Page Setup

### Basic Page Configuration

```typst
#set page(
  paper: "a4",            // or "us-letter", "a5", etc.
  margin: 2cm,            // uniform margin
  margin: (x: 2cm, y: 3cm),  // horizontal/vertical
  margin: (top: 3cm, bottom: 2cm, left: 2.5cm, right: 2.5cm),
)
```

### Page Numbering

```typst
#set page(numbering: "1")           // 1, 2, 3...
#set page(numbering: "1 / 1")       // 1 / 10
#set page(numbering: "i")           // i, ii, iii...
#set page(number-align: center)     // alignment
```

### Header and Footer

```typst
#set page(
  header: [
    #set text(8pt)
    Document Title
    #h(1fr)
    #context counter(page).display()
  ],
  footer: [
    #set align(center)
    #set text(8pt)
    Page #context counter(page).display()
  ],
)
```

### Background and Foreground

```typst
#set page(
  background: place(center + horizon, 
    text(60pt, fill: luma(230))[DRAFT]
  ),
)
```

## Spacing

### Horizontal Spacing

```typst
#h(1cm)           // fixed space
#h(1fr)           // flexible space (fills remaining)
#h(2fr)           // twice as much flexible space
```

### Vertical Spacing

```typst
#v(1cm)           // fixed vertical space
#v(1fr)           // flexible vertical space
```

## Alignment

```typst
#set align(center)          // center align
#set align(left)            // left align
#set align(right)           // right align
#set align(center + horizon)  // center both axes

// Inline alignment
#align(center)[Centered text]
#align(right)[Right-aligned]
```

## Blocks and Boxes

### Block

```typst
#block(
  width: 100%,
  fill: luma(230),
  inset: 1em,
  radius: 4pt,
  [Block content]
)
```

### Box (Inline)

```typst
#box(
  fill: yellow,
  inset: 4pt,
  [Highlighted]
)
```

## Grid Layout

### Basic Grid

```typst
#grid(
  columns: (1fr, 1fr),      // two equal columns
  gutter: 1em,              // gap between cells
  [Column 1], [Column 2],
  [Row 2 Col 1], [Row 2 Col 2],
)
```

### Grid with Varying Columns

```typst
#grid(
  columns: (auto, 1fr, 2fr),  // auto + proportional
  rows: (auto, 1fr),
  [A], [B], [C],
  [D], [E], [F],
)
```

## Tables

### Basic Table

```typst
#table(
  columns: 3,
  [Header 1], [Header 2], [Header 3],
  [Cell 1], [Cell 2], [Cell 3],
  [Cell 4], [Cell 5], [Cell 6],
)
```

### Styled Table

```typst
#table(
  columns: (auto, 1fr, 1fr),
  inset: 10pt,
  align: horizon,
  fill: (x, y) => if y == 0 { luma(230) },
  table.header(
    [*Name*], [*Value*], [*Description*],
  ),
  [Item A], [100], [First item],
  [Item B], [200], [Second item],
)
```

### Table Spanning

```typst
#table(
  columns: 3,
  table.cell(colspan: 2)[Spans 2 columns], [Single],
  table.cell(rowspan: 2)[Spans 2 rows], [A], [B],
  [C], [D],
)
```

## Figures

```typst
#figure(
  image("diagram.png", width: 80%),
  caption: [A descriptive caption],
) <fig:diagram>

// Reference: @fig:diagram
```

## Columns

```typst
#set page(columns: 2)           // two-column layout

// Or inline
#columns(2, gutter: 1em)[
  First column content.
  #colbreak()
  Second column content.
]
```

## Positioning

### Place (Absolute Positioning)

```typst
#place(
  top + right,
  dx: -1cm,
  dy: 1cm,
  [Positioned element]
)
```

### Move (Relative Positioning)

```typst
#move(dx: 5pt, dy: -3pt)[Shifted text]
```

## Transforms

```typst
#rotate(45deg)[Rotated]
#scale(x: 150%, y: 100%)[Scaled]
#skew(ax: 10deg)[Skewed]
```

## Length Units

| Unit | Description |
|------|-------------|
| `pt` | Points (1/72 inch) |
| `mm` | Millimeters |
| `cm` | Centimeters |
| `in` | Inches |
| `em` | Relative to font size |
| `%` | Percentage of container |
| `fr` | Fraction of remaining space |

## Page Breaks

```typst
#pagebreak()              // force page break
#pagebreak(weak: true)    // only if needed
```

## Padding

```typst
#pad(x: 1em, y: 0.5em)[Padded content]
#pad(left: 2em)[Left-padded only]
```
