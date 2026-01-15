# Typst Styling Reference

Typst uses set rules and show rules for styling documents.

## Function Parameters

These tables document the key styling functions. Use them with set rules to configure defaults or directly for inline styling.

### `text` Function

Controls typography including font family, size, color, and language settings. This is the most fundamental styling function for text appearance.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `font` | str \| array | `"libertinus serif"` | Font family or priority list |
| `size` | length | `11pt` | Font size |
| `fill` | color | `black` | Text color |
| `weight` | int \| str | `"regular"` | `"thin"`, `"light"`, `"regular"`, `"medium"`, `"bold"`, or 100-900 |
| `style` | str | `"normal"` | `"normal"`, `"italic"`, `"oblique"` |
| `lang` | str | `"en"` | Language code (e.g., `"ko"`, `"ja"`, `"zh"`) |
| `region` | str \| none | `none` | Region code (e.g., `"KR"`, `"US"`) |
| `hyphenate` | auto \| bool | `auto` | Enable hyphenation |
| `tracking` | length | `0pt` | Letter spacing |
| `spacing` | relative | `100%` | Word spacing |
| `baseline` | length | `0pt` | Baseline shift |
| `body` | content | required | Text content |

### `par` Function

Controls paragraph-level formatting including line spacing, justification, and indentation. Essential for achieving professional document layouts.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `leading` | length | `0.65em` | Line spacing (between lines) |
| `spacing` | length | `1.2em` | Paragraph spacing (between paragraphs) |
| `justify` | bool | `false` | Justify text |
| `linebreaks` | auto \| str | `auto` | `"simple"`, `"optimized"` |
| `first-line-indent` | length | `0pt` | First line indentation |
| `hanging-indent` | length | `0pt` | Hanging indent for subsequent lines |
| `body` | content | required | Paragraph content |

### `block` Function

Creates block-level containers with visual styling options like backgrounds, borders, and padding. Use for callout boxes, code blocks, or any content that needs visual separation.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `width` | auto \| relative | `auto` | Block width |
| `height` | auto \| relative | `auto` | Block height |
| `fill` | none \| color | `none` | Background color |
| `stroke` | none \| stroke | `none` | Border stroke |
| `radius` | relative \| dict | `(:)` | Corner radius |
| `inset` | relative \| dict | `(:)` | Inner padding |
| `outset` | relative \| dict | `(:)` | Outer expansion |
| `spacing` | relative | `1.2em` | Spacing around block (sets above & below) |
| `above` | auto \| relative | `auto` | Spacing above |
| `below` | auto \| relative | `auto` | Spacing below |
| `breakable` | bool | `true` | Allow page breaks |
| `clip` | bool | `false` | Clip overflow content |
| `sticky` | bool | `false` | Stick to next block |
| `body` | content | `none` | Block content |

## Set Rules

Set rules apply default property values to all instances of an element within a scope. They cascade like CSS and are the primary mechanism for consistent document styling.

### Syntax

```typst
#set element(property: value)
```

### Common Set Rules

These examples show the most frequently used set rules for document configuration. Set rules can be placed at the document start for global effect or within content blocks for local scope.

```typst
// Text styling
#set text(font: "New Computer Modern", size: 11pt)
#set text(lang: "ko")  // Korean language

// Paragraph styling
#set par(justify: true, leading: 0.65em, first-line-indent: 1em)

// Page setup
#set page(paper: "a4", margin: 2cm)
#set page(numbering: "1")

// Heading numbering
#set heading(numbering: "1.1")

// List styling
#set list(marker: [•])
#set enum(numbering: "1.a)")
```

### Scoped Set Rules

Wrap content in `#[...]` to create a scope where set rules only apply locally. This is useful for applying temporary styles without affecting the rest of the document.

```typst
// Apply only within block
#[
  #set text(fill: blue)
  This text is blue.
]
This text is default color.
```

## Show Rules

Show rules transform how elements are displayed. Unlike set rules which configure properties, show rules can completely redefine an element's appearance using custom logic.

### Basic Show Rule

The basic form takes an element type and a transformation function. The `it` parameter receives the matched element.

```typst
// Transform all headings
#show heading: it => {
  set text(fill: blue)
  it
}

// Transform specific element
#show "typst": [*Typst*]
```

### Show-Set Rule

A shorthand syntax that combines show rules with set rules. Use when you want to apply set rules only to specific elements without custom transformation logic.

```typst
// Apply set rule to specific element
#show heading: set text(fill: navy)
#show raw: set text(font: "Fira Code")
```

### Show with Function

For complex transformations, define a function that receives the element and returns modified content. Access element properties through the `it` parameter.

```typst
#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  set text(size: 18pt)
  block(it.body)
}
```

### Selector Types

Selectors determine which elements a show rule matches. Use `.where()` to filter by specific property values.

| Selector | Example |
|----------|---------|
| Element | `#show heading: ...` |
| Text | `#show "word": ...` |
| Regex | `#show regex("\d+"): ...` |
| Label | `#show <label>: ...` |
| Where | `#show heading.where(level: 1): ...` |

## Document Setup Pattern

A typical document preamble combines set rules and show rules to establish consistent styling. Place these at the document start before any content.

```typst
// Typical document setup
#set document(
  title: "Document Title",
  author: "Author Name",
)

#set page(
  paper: "a4",
  margin: (x: 2.5cm, y: 3cm),
  header: [
    #set text(8pt)
    Document Title
    #h(1fr)
    #context counter(page).display()
  ],
)

#set text(
  font: "Noto Sans KR",
  size: 10pt,
  lang: "ko",
)

#set par(
  justify: true,
  leading: 0.8em,
)

#set heading(numbering: "1.1")
#show heading.where(level: 1): set text(size: 16pt)
#show heading.where(level: 2): set text(size: 14pt)
```

## LaTeX-like Styling

To achieve a classic academic paper appearance similar to LaTeX defaults, use these settings with Computer Modern fonts. Adjust margins and spacing to match your target style.

```typst
// Achieve LaTeX look
#set page(margin: 1.75in)
#set par(
  leading: 0.55em,
  spacing: 0.55em,
  first-line-indent: 1.8em,
  justify: true,
)
#set text(font: "New Computer Modern")
#show raw: set text(font: "New Computer Modern Mono")
#show heading: set block(above: 1.4em, below: 1em)
```
