# Typst Common Layout Reference

Page setup, positioning, and layout elements shared by stable Typst 0.13.0 through 0.15.1. Read the selected file under `versions/` before using version-specific page, list, image, or export features.

## Function Parameters

These functions control document structure, positioning, and visual layout. They are the foundation for page design and content arrangement.

### `page` Function

Configures page dimensions, margins, headers, footers, and numbering. This is typically one of the first set rules in a document.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `paper` | str | `"a4"` | `"a4"`, `"us-letter"`, `"a5"`, `"a3"`, etc. |
| `width` | auto \| length | `auto` | Custom page width |
| `height` | auto \| length | `auto` | Custom page height |
| `margin` | auto \| relative \| dictionary | `auto` | Margins: single value, `(x:, y:)`, or `(top:, bottom:, left:, right:)` |
| `columns` | int | `1` | Number of columns |
| `fill` | auto \| none \| color \| gradient \| tiling | `auto` | Page background fill; export targets interpret `auto` |
| `numbering` | none \| str \| function | `none` | Page number format: `"1"`, `"i"`, `"1 / 1"` |
| `number-align` | alignment | `center + bottom` | Page number alignment |
| `header` | none \| auto \| content | `auto` | Header content |
| `header-ascent` | relative | `30%` | Header distance from top |
| `footer` | none \| auto \| content | `auto` | Footer content |
| `footer-descent` | relative | `30%` | Footer distance from bottom |
| `background` | none \| content | `none` | Background content |
| `foreground` | none \| content | `none` | Foreground overlay |
| `flipped` | bool | `false` | Mirror inside/outside margins and binding |
| `binding` | auto \| alignment | `auto` | Binding side for two-sided layout |
| `supplement` | auto \| none \| content \| function | `auto` | Page-reference supplement |
| `body` | content | required | Page content |

### `grid` Function

Creates flexible multi-column/row layouts. Unlike tables, grids have no default styling—use them for pure layout without visual borders.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `columns` | auto \| int \| relative \| fraction \| array | `()` | Column widths: `3`, `(1fr, 2fr)`, `(auto, 1fr)` |
| `rows` | auto \| int \| relative \| fraction \| array | `()` | Row heights |
| `gutter` | auto \| int \| relative \| fraction \| array | `()` | Gap between cells |
| `column-gutter` | auto \| int \| relative \| fraction \| array | `()` | Column gap |
| `row-gutter` | auto \| int \| relative \| fraction \| array | `()` | Row gap |
| `fill` | none \| color \| gradient \| tiling \| array \| function | `none` | Cell fill, including `(x, y) => color` |
| `align` | auto \| alignment \| array \| function | `auto` | Cell alignment |
| `stroke` | none \| stroke \| array \| dictionary \| function | `none` | Cell borders |
| `inset` | relative \| array \| dictionary \| function | `(:)` | Cell padding |
| `children` | content | variadic | Grid cells |

### `table` Function

Creates data tables with automatic borders and styling. Tables are semantic containers for tabular data with built-in visual formatting.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `columns` | auto \| int \| relative \| fraction \| array | `()` | Column widths |
| `rows` | auto \| int \| relative \| fraction \| array | `()` | Row heights |
| `gutter` | auto \| int \| relative \| fraction \| array | `()` | Gap between cells |
| `column-gutter` | auto \| int \| relative \| fraction \| array | `()` | Column gap |
| `row-gutter` | auto \| int \| relative \| fraction \| array | `()` | Row gap |
| `fill` | none \| color \| gradient \| tiling \| array \| function | `none` | Cell fill, including `(x, y) => color` |
| `align` | auto \| alignment \| array \| function | `auto` | Cell alignment |
| `stroke` | none \| stroke \| array \| dictionary \| function | `1pt + black` | Cell borders |
| `inset` | relative \| array \| dictionary \| function | `5pt` | Cell padding |
| `children` | content | variadic | Table cells |

**`table.cell` Parameters:**

Use `table.cell` for fine control over individual cells, including spanning multiple rows or columns.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `x` | auto \| int | `auto` | Explicit column position |
| `y` | auto \| int | `auto` | Explicit row position |
| `colspan` | int | `1` | Columns to span |
| `rowspan` | int | `1` | Rows to span |
| `fill` | auto \| none \| color \| gradient \| tiling | `auto` | Cell fill |
| `align` | auto \| alignment | `auto` | Cell alignment |
| `inset` | auto \| relative \| dictionary | `auto` | Cell padding override |
| `stroke` | auto \| none \| stroke \| dictionary | `auto` | Cell border override |
| `breakable` | auto \| bool | `auto` | Allow the cell to break across pages |
| `body` | content | required | Cell content |

### `figure` Function

Wraps content (images, tables, code) with automatic numbering and captions. Figures can be referenced and appear in lists of figures.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `body` | content | required | Figure content |
| `caption` | none \| content | `none` | Caption text |
| `kind` | auto \| str \| function | `auto` | Figure type: `"image"`, `"table"`, `"raw"` |
| `supplement` | auto \| none \| content \| function | `auto` | Reference prefix: `"Figure"`, `"Table"` |
| `numbering` | none \| str \| function | `"1"` | Figure number format |
| `gap` | length | `0.65em` | Gap between body and caption |
| `placement` | none \| auto \| alignment | `none` | Float placement: `auto`, `top`, `bottom` |
| `scope` | str | `"local"` | Numbering scope |
| `outlined` | bool | `true` | Include the figure in an outline |

### `image` Function

Embeds external images in the document. Supports PNG, JPG, GIF, and SVG formats with automatic or manual sizing.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source` | str \| bytes | required | Image path string, encoded image bytes, or raw pixel bytes |
| `format` | auto \| str \| dictionary | `auto` | Encoded format or raw-pixel `(encoding:, width:, height:)` description |
| `width` | auto \| relative | `auto` | Image width |
| `height` | auto \| relative \| fraction | `auto` | Image height |
| `alt` | none \| str | `none` | Alt text for accessibility |
| `fit` | str | `"cover"` | `"cover"`, `"contain"`, `"stretch"` |
| `scaling` | auto \| str | `auto` | Pixel scaling behavior such as `"smooth"` or `"pixelated"` |
| `icc` | auto \| bytes | `auto` | Embedded or overridden ICC profile |

## Page Setup

Page configuration is typically done once at the document start. These settings affect all subsequent pages unless overridden.

### Basic Page Configuration

Set paper size and margins. Use dictionary syntax for asymmetric margins.

```typst
#set page(paper: "a4", margin: 2cm)

// Or configure horizontal and vertical margins separately.
#set page(margin: (x: 2cm, y: 3cm))

// Or configure each edge.
#set page(
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

## Length, Ratio, and Fraction Units

Typst distinguishes physical/font-relative lengths from ratios and layout fractions.

| Unit | Description |
|------|-------------|
| `pt` | Points (1/72 inch) |
| `mm` | Millimeters |
| `cm` | Centimeters |
| `in` | Inches |
| `em` | Relative to font size |

| Type | Syntax | Description |
|---|---|---|
| Ratio | `%` | Proportion relative to a contextual size |
| Fraction | `fr` | Share of remaining layout space |

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
