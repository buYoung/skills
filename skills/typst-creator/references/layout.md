# Typst Layout Reference

Page setup, positioning, and layout elements.

## Function Parameters

These functions control document structure, positioning, and visual layout. They are the foundation for page design and content arrangement.

### `page` Function

Configures page dimensions, margins, headers, footers, and numbering. This is typically one of the first set rules in a document.

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

Creates flexible multi-column/row layouts. Unlike tables, grids have no default styling—use them for pure layout without visual borders.

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

Creates data tables with automatic borders and styling. Tables are semantic containers for tabular data with built-in visual formatting.

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

Use `table.cell` for fine control over individual cells, including spanning multiple rows or columns.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `colspan` | int | `1` | Columns to span |
| `rowspan` | int | `1` | Rows to span |
| `fill` | auto \| none \| color | `auto` | Cell fill |
| `align` | auto \| alignment | `auto` | Cell alignment |
| `body` | content | required | Cell content |

### `figure` Function

Wraps content (images, tables, code) with automatic numbering and captions. Figures can be referenced and appear in lists of figures.

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

Embeds external images in the document. Supports PNG, JPG, GIF, and SVG formats with automatic or manual sizing.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | str | required | Image file path |
| `format` | auto \| str | `auto` | `"png"`, `"jpg"`, `"gif"`, `"svg"` |
| `width` | auto \| relative | `auto` | Image width |
| `height` | auto \| relative | `auto` | Image height |
| `alt` | none \| str | `none` | Alt text for accessibility |
| `fit` | str | `"cover"` | `"cover"`, `"contain"`, `"stretch"` |

## Page Setup

Page configuration is typically done once at the document start. These settings affect all subsequent pages unless overridden.

### Basic Page Configuration

Set paper size and margins. Use dictionary syntax for asymmetric margins.

```typst
#set page(
  paper: "a4",            // or "us-letter", "a5", etc.
  margin: 2cm,            // uniform margin
  margin: (x: 2cm, y: 3cm),  // horizontal/vertical
  margin: (top: 3cm, bottom: 2cm, left: 2.5cm, right: 2.5cm),
)
```

### Page Numbering

Automatic page numbers with customizable format. Use `"1"` for arabic, `"i"` for roman numerals, or combine with total count.

```typst
#set page(numbering: "1")           // 1, 2, 3...
#set page(numbering: "1 / 1")       // 1 / 10
#set page(numbering: "i")           // i, ii, iii...
#set page(number-align: center)     // alignment
```

### Header and Footer

Headers and footers accept arbitrary content. Use `context` to access the current page number and other document state.

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

Add watermarks, decorations, or overlays. Background renders behind content; foreground renders on top.

```typst
#set page(
  background: place(center + horizon, 
    text(60pt, fill: luma(230))[DRAFT]
  ),
)
```

## Spacing

Control whitespace between elements. The `fr` unit is particularly powerful for flexible layouts.

### Horizontal Spacing

Use `h()` for horizontal gaps. The `fr` (fraction) unit distributes remaining space proportionally.

```typst
#h(1cm)           // fixed space
#h(1fr)           // flexible space (fills remaining)
#h(2fr)           // twice as much flexible space
```

### Vertical Spacing

Use `v()` for vertical gaps between block elements. Works the same as horizontal spacing.

```typst
#v(1cm)           // fixed vertical space
#v(1fr)           // flexible vertical space
```

## Alignment

Control content positioning within its container. Combine horizontal and vertical alignment with `+`.

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

Containers for grouping and styling content. Blocks are block-level (cause line breaks); boxes are inline.

### Block

Block-level containers with optional background, border, and padding. Use for callouts, sidebars, or any visually distinct sections.

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

Inline containers that flow with text. Use for highlighting words or adding inline decorations.

```typst
#box(
  fill: yellow,
  inset: 4pt,
  [Highlighted]
)
```

## Grid Layout

Grids arrange content in rows and columns without table styling. Ideal for multi-column layouts, card layouts, or any structured arrangement.

### Basic Grid

Specify column widths as an array. Content fills cells left-to-right, top-to-bottom.

```typst
#grid(
  columns: (1fr, 1fr),      // two equal columns
  gutter: 1em,              // gap between cells
  [Column 1], [Column 2],
  [Row 2 Col 1], [Row 2 Col 2],
)
```

### Grid with Varying Columns

Mix `auto` (content-sized), fixed lengths, and `fr` (fractional) units for flexible layouts.

```typst
#grid(
  columns: (auto, 1fr, 2fr),  // auto + proportional
  rows: (auto, 1fr),
  [A], [B], [C],
  [D], [E], [F],
)
```

## Tables

Tables include default borders and padding. Use for displaying structured data that benefits from visual separation.

### Basic Table

Specify column count or widths. Content is placed sequentially into cells.

```typst
#table(
  columns: 3,
  [Header 1], [Header 2], [Header 3],
  [Cell 1], [Cell 2], [Cell 3],
  [Cell 4], [Cell 5], [Cell 6],
)
```

### Styled Table

Customize appearance with fill functions (for alternating rows), alignment, and header styling.

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

Use `table.cell` with `colspan` or `rowspan` to merge cells across columns or rows.

```typst
#table(
  columns: 3,
  table.cell(colspan: 2)[Spans 2 columns], [Single],
  table.cell(rowspan: 2)[Spans 2 rows], [A], [B],
  [C], [D],
)
```

## Figures

Figures wrap content with automatic numbering and captions. Add labels for cross-referencing with `@label` syntax.

```typst
#figure(
  image("diagram.png", width: 80%),
  caption: [A descriptive caption],
) <fig:diagram>

// Reference: @fig:diagram
```

## Columns

Create multi-column text flow. Use `colbreak()` to force content to the next column.

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

Control exact element placement when automatic flow isn't sufficient.

### Place (Absolute Positioning)

Position elements relative to page or container edges. Does not affect document flow.

```typst
#place(
  top + right,
  dx: -1cm,
  dy: 1cm,
  [Positioned element]
)
```

### Move (Relative Positioning)

Shift elements from their natural position while maintaining document flow.

```typst
#move(dx: 5pt, dy: -3pt)[Shifted text]
```

## Transforms

Apply geometric transformations to content. Useful for decorative effects or specialized layouts.

```typst
#rotate(45deg)[Rotated]
#scale(x: 150%, y: 100%)[Scaled]
#skew(ax: 10deg)[Skewed]
```

## Length Units

Typst supports both absolute and relative length units. Use `em` for font-relative sizing, `fr` for flexible space distribution.

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

Control page flow. Use `weak: true` to only break if there's already content on the page.

```typst
#pagebreak()              // force page break
#pagebreak(weak: true)    // only if needed
```

## Padding

Add space around content. Use named parameters for asymmetric padding.

```typst
#pad(x: 1em, y: 0.5em)[Padded content]
#pad(left: 2em)[Left-padded only]
```
