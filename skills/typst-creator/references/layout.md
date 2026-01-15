# Typst Layout Reference

Page setup, positioning, and layout elements.

## Function Parameters

### `page` Function

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `paper` | str | `"a4"` | `"a4"`, `"us-letter"`, `"a5"`, `"a3"`, etc. |
| `width` | auto \| length | `auto` | Custom page width |
| `height` | auto \| length | `auto` | Custom page height |
| `margin` | auto \| relative \| dict | `auto` | Margins: single value, `(x:, y:)`, or `(top:, bottom:, left:, right:)` |
| `columns` | int | `1` | Number of columns |
| `fill` | none \| color | `none` | Background color |
| `numbering` | none \| str \| func | `none` | Page number format: `"1"`, `"i"`, `"1 / 1"` |
| `number-align` | alignment | `center + bottom` | Page number alignment |
| `header` | none \| auto \| content | `auto` | Header content |
| `header-ascent` | relative | `30%` | Header distance from top |
| `footer` | none \| auto \| content | `auto` | Footer content |
| `footer-descent` | relative | `30%` | Footer distance from bottom |
| `background` | none \| content | `none` | Background content |
| `foreground` | none \| content | `none` | Foreground overlay |
| `body` | content | required | Page content |

### `grid` Function

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `columns` | auto \| int \| array | `()` | Column widths: `3`, `(1fr, 2fr)`, `(auto, 1fr)` |
| `rows` | auto \| int \| array | `()` | Row heights |
| `gutter` | auto \| length \| array | `0pt` | Gap between cells |
| `column-gutter` | auto \| length \| array | `auto` | Column gap |
| `row-gutter` | auto \| length \| array | `auto` | Row gap |
| `fill` | none \| color \| func | `none` | Cell fill: `(x, y) => color` |
| `align` | auto \| alignment \| func | `auto` | Cell alignment |
| `stroke` | none \| stroke | `none` | Cell borders |
| `inset` | relative \| dict | `0pt` | Cell padding |
| `children` | content | required | Grid cells |

### `table` Function

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `columns` | auto \| int \| array | `()` | Column widths |
| `rows` | auto \| int \| array | `()` | Row heights |
| `gutter` | auto \| length \| array | `0pt` | Gap between cells |
| `fill` | none \| color \| func | `none` | Cell fill: `(x, y) => color` |
| `align` | auto \| alignment \| func | `auto` | Cell alignment |
| `stroke` | none \| stroke | `1pt + black` | Cell borders |
| `inset` | relative \| dict | `5pt` | Cell padding |
| `children` | content | required | Table cells |

**`table.cell` Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `colspan` | int | `1` | Columns to span |
| `rowspan` | int | `1` | Rows to span |
| `fill` | auto \| none \| color | `auto` | Cell fill |
| `align` | auto \| alignment | `auto` | Cell alignment |
| `body` | content | required | Cell content |

### `figure` Function

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `body` | content | required | Figure content |
| `caption` | none \| content | `none` | Caption text |
| `kind` | auto \| str \| func | `auto` | Figure type: `"image"`, `"table"`, `"raw"` |
| `supplement` | auto \| none \| content | `auto` | Reference prefix: `"Figure"`, `"Table"` |
| `numbering` | none \| str \| func | `"1"` | Figure number format |
| `gap` | length | `0.65em` | Gap between body and caption |
| `placement` | none \| auto \| alignment | `none` | Float placement: `auto`, `top`, `bottom` |

### `image` Function

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | str | required | Image file path |
| `format` | auto \| str | `auto` | `"png"`, `"jpg"`, `"gif"`, `"svg"` |
| `width` | auto \| relative | `auto` | Image width |
| `height` | auto \| relative | `auto` | Image height |
| `alt` | none \| str | `none` | Alt text for accessibility |
| `fit` | str | `"cover"` | `"cover"`, `"contain"`, `"stretch"` |

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
