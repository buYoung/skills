# Typst Common Styling Reference

Checked: 2026-09-09. Tables summarize selected parameters; consult the official signature for positional/named and settable restrictions. Code blocks are independent snippets unless dependencies are stated.

Typst uses set rules and show rules for styling documents. This file contains styling patterns shared by stable Typst 0.13.0 through 0.15.1. Read the selected file under `versions/` before using version-specific properties such as Typst 0.15 variable-font variations.

## Function Parameters

These tables document the key styling functions. Use them with set rules to configure defaults or directly for inline styling.

### `text` Function

Controls typography including font family, size, color, and language settings. This is the most fundamental styling function for text appearance.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `font` | str \| array \| dictionary | `"libertinus serif"` | Font family, descriptor, or priority list |
| `size` | length | `11pt` | Font size |
| `fill` | color \| gradient \| tiling | `black` | Text fill |
| `weight` | int \| str | `"regular"` | Named weight from `"thin"` through `"black"` (including `"extralight"`, `"semibold"`, and `"extrabold"`), or 100-900 |
| `style` | str | `"normal"` | `"normal"`, `"italic"`, `"oblique"` |
| `lang` | str | `"en"` | Language code (e.g., `"ko"`, `"ja"`, `"zh"`) |
| `region` | str \| none | `none` | Region code (e.g., `"KR"`, `"US"`) |
| `hyphenate` | auto \| bool | `auto` | Enable hyphenation |
| `tracking` | length | `0pt` | Letter spacing |
| `spacing` | relative | `100%` | Word spacing |
| `baseline` | length | `0pt` | Baseline shift |
| `body` | content | `[]` | Content body; the constructor also has a separate positional string form, `text("...")` |

### `par` Function

Controls paragraph-level formatting including line spacing, justification, and indentation. Essential for achieving professional document layouts.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `leading` | length | `0.65em` | Line spacing (between lines) |
| `spacing` | length | `1.2em` | Paragraph spacing (between paragraphs) |
| `justify` | bool | `false` | Justify text |
| `linebreaks` | auto \| str | `auto` | `"simple"`, `"optimized"` |
| `first-line-indent` | length \| dictionary | `(amount: 0pt, all: false)` | Indent amount or `(amount:, all:)` configuration |
| `hanging-indent` | length | `0pt` | Hanging indent for subsequent lines |
| `body` | content | required | Paragraph content |

### `block` Function

Creates block-level containers with visual styling options like backgrounds, borders, and padding. Use for callout boxes, code blocks, or any content that needs visual separation.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `width` | auto \| relative | `auto` | Block width |
| `height` | auto \| relative \| fraction | `auto` | Block height |
| `fill` | none \| color \| gradient \| tiling | `none` | Background fill |
| `stroke` | none \| length \| color \| gradient \| stroke \| tiling \| dictionary | `(:)` | Border stroke |
| `radius` | relative \| dictionary | `(:)` | Corner radius |
| `inset` | relative \| dictionary | `(:)` | Inner padding |
| `outset` | relative \| dictionary | `(:)` | Outer expansion |
| `spacing` | auto \| relative \| fraction | `1.2em` | Spacing around block (sets above & below) |
| `above` | auto \| relative \| fraction | `auto` | Spacing above |
| `below` | auto \| relative \| fraction | `auto` | Spacing below |
| `breakable` | bool | `true` | Allow page breaks |
| `clip` | bool | `false` | Clip overflow content |
| `sticky` | bool | `false` | Stick to next block |
| `body` | none \| content | `none` | Block content |

## Set Rules

Set rules supply defaults from their position until the end of the current block or file. They do not restyle earlier content. Explicit function arguments override these defaults. Only parameters documented as settable (and supported shorthand parameters) can be configured with a set rule; required positional content is supplied at the call site.

### Syntax

```typst
#set text(fill: blue)
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

For property changes, prefer a show-set rule so later show-set rules can override the style. Use a transformation function only when the content representation itself changes; its `it` parameter receives the matched element. A set rule inside that function cannot be overridden by a later show-set rule outside it.

```typst
// Style all headings with an overridable rule
#show heading: set text(fill: blue)

// Transform specific element
#show "typst": [*Typst*]
```

### Show-Set Rule

A shorthand syntax that combines show rules with set rules. Use when you want to apply set rules only to specific elements without custom transformation logic.

```typst
// Apply set rule to specific element
#show heading: set text(fill: navy)
#show raw: set text(font: "DejaVu Sans Mono")
```

### Show with Function

For complex transformations, define a function that receives the element and returns modified content. Replacing its display with `it.body` alone omits its visible numbering. Reconstruct that display if needed; this does not imply that the original heading's semantic identity has disappeared. Keep ordinary styles in separate show-set rules.

```typst
#show heading.where(level: 1): set text(size: 18pt)
#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  block[
    #if it.numbering != none {
      counter(heading).display(it.numbering)
      h(0.3em)
    }
    #it.body
  ]
}
```

### Selector Types

Selectors determine which elements a show rule matches. Use `.where()` to filter element fields, not arbitrary computed styles. Show rules, like set rules, apply forward to the end of their block or file. Show rules provide style context, but location context requires a locatable matched element; see [Context](context.md).

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
  font: "NanumGothic", // Requires this font to be installed or provided.
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
#show raw: set text(font: "DejaVu Sans Mono")
#show heading: set block(above: 1.4em, below: 1em)
```

## Fonts and Multilingual Typography

Check `typst fonts` for the actual environment before selecting a family. CLI `--font-path` adds project fonts; the web app can discover uploaded font files. A language such as `lang: "ko"` controls language-sensitive behavior but does not install or select a Korean font.

Use an ordered font list for mixed scripts. Family descriptors can restrict coverage with `covers`; the common 0.13+ interface supports a Unicode-character regex or the documented `"latin-in-cjk"` coverage set. Verify fallback glyphs rather than assuming a successful compilation proves all characters are visible.

Environment-dependent example: both named families must be available. Replace the Korean family with one actually installed or supplied.

```typst
#set text(font: ("Libertinus Serif", "NanumGothic"), lang: "ko")
English and 한국어 can share a paragraph.
```

Math needs an OpenType math font. Configure it independently, for example `show math.equation: set text(font: "New Computer Modern Math")`. The font in a quoted math string does not automatically become the surrounding prose font; see [Math](math.md#text-in-math).

Typst 0.15 adds variable font axes through `text.variations` and normalizes family suffixes; consult the [0.15 reference](versions/0.15.md). Use static fonts for 0.13/0.14 compatibility. When diagnosing layout changes, compare the actual font files and versions as well as the compiler.

## Sources

- [Styling](https://typst.app/docs/reference/styling/)
- [Text and fonts](https://typst.app/docs/reference/text/text/)
- [Paragraph](https://typst.app/docs/reference/model/par/)
- [Block](https://typst.app/docs/reference/layout/block/)
