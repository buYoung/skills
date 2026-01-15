# Typst Syntax Reference

Typst has three syntactical modes: Markup, Math, and Code.

## Function Parameters

These tables provide quick reference for the most commonly used markup functions and their configurable options.

### `heading` Function

Defines document structure with hierarchical sections. The number of `=` signs determines the heading level.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `level` | auto \| int | `auto` | Heading level (1-6), auto-detected from `=` count |
| `depth` | int | - | (read-only) Nesting depth relative to `offset` |
| `offset` | int | `0` | Starting level offset for numbering |
| `numbering` | none \| str \| func | `none` | Number format: `"1."`, `"1.1"`, `"I.a"` |
| `supplement` | auto \| none \| content | `auto` | Reference prefix (e.g., "Section") |
| `outlined` | bool | `true` | Include in outline |
| `bookmarked` | auto \| bool | `auto` | Include in PDF bookmarks |
| `hanging-indent` | auto \| length | `auto` | Indent for wrapped lines |
| `body` | content | required | Heading text |

### `list` Function (Bullet List)

Creates unordered lists with customizable bullet markers. Use `-` in markup mode for quick list creation.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tight` | bool | `true` | Reduce spacing between items |
| `marker` | content \| array \| func | `[•]` | Bullet marker(s) per level |
| `indent` | length | `0pt` | Indent from left |
| `body-indent` | length | `0.5em` | Gap between marker and text |
| `spacing` | auto \| relative | `auto` | Space between items |
| `children` | content | required | List items |

### `enum` Function (Numbered List)

Creates ordered lists with automatic numbering. Use `+` in markup mode. Supports various numbering formats including letters and roman numerals.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tight` | bool | `true` | Reduce spacing between items |
| `numbering` | str \| func | `"1."` | Number format: `"1."`, `"a)"`, `"(i)"` |
| `start` | int | `1` | Starting number |
| `full` | bool | `false` | Show full numbering (e.g., "1.1.1") |
| `indent` | length | `0pt` | Indent from left |
| `body-indent` | length | `0.5em` | Gap between number and text |
| `spacing` | auto \| relative | `auto` | Space between items |
| `children` | content | required | List items |

### `raw` Function (Code Block)

Displays text exactly as written without interpretation. Use backticks in markup mode for inline code or triple backticks for code blocks with syntax highlighting.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | str | required | Raw text content |
| `block` | bool | `false` | Display as block (true for fenced blocks) |
| `lang` | none \| str | `none` | Language for syntax highlighting |
| `align` | alignment | `start` | Text alignment |
| `syntaxes` | str \| array | `()` | Additional syntax definition files |
| `theme` | auto \| str \| none | `auto` | Syntax highlighting theme |
| `tab-size` | int | `2` | Tab width in spaces |

### `link` Function

Creates clickable hyperlinks to URLs, labels, or document locations. URLs are automatically detected in markup mode.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dest` | str \| label \| location \| dict | required | URL, label, or location |
| `body` | auto \| content | `auto` | Link text (auto shows URL) |

### `ref` Function

Creates cross-references to labeled elements like headings, figures, or equations. Use `@label` syntax in markup mode.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `target` | label | required | Target label |
| `supplement` | auto \| none \| content | `auto` | Reference prefix |

## Mode Switching

Typst has three syntactical modes that you can switch between at any point. Understanding mode transitions is essential for combining text, math, and logic.

| New Mode | Syntax | Example |
|----------|--------|---------|
| Code | Prefix with `#` | `Number: #(1 + 2)` |
| Math | Surround with `$...$` | `$-x$ is the opposite of $x$` |
| Markup | Surround with `[..]` | `let name = [*Typst!*]` |

## Markup Mode Syntax

Markup mode is the default in a Typst document. It provides lightweight syntax for common document elements, with each shorthand corresponding to a function.

| Element | Syntax | Function |
|---------|--------|----------|
| Paragraph break | Blank line | `parbreak` |
| Strong emphasis | `*strong*` | `strong` |
| Emphasis | `_emphasis_` | `emph` |
| Raw text | `` `code` `` | `raw` |
| Link | `https://typst.app/` | `link` |
| Label | `<intro>` | `label` |
| Reference | `@intro` | `ref` |
| Heading | `= Heading` | `heading` |
| Bullet list | `- item` | `list` |
| Numbered list | `+ item` | `enum` |
| Term list | `/ Term: description` | `terms` |
| Line break | `\` | `linebreak` |
| Smart quote | `'single'` or `"double"` | `smartquote` |
| Comment | `/* block */` or `// line` | - |

### Heading Levels

The number of `=` signs determines the heading depth. Add more `=` for deeper nesting levels.

```typst
= Level 1 Heading
== Level 2 Heading
=== Level 3 Heading
```

### Lists

Typst supports bullet lists (`-`), numbered lists (`+`), and term/definition lists (`/`). Indent with spaces for nested items.

```typst
- Bullet item 1
- Bullet item 2
  - Nested item

+ Numbered item 1
+ Numbered item 2

/ Term: Definition of the term
/ Another: Its definition
```

## Math Mode Syntax

Math mode is entered by wrapping equations in `$` characters. The equation becomes a block if it has spaces after `$` and before the closing `$`; otherwise it renders inline.

| Element | Syntax | Example |
|---------|--------|---------|
| Inline math | `$...$` (no spaces) | `$x^2$` |
| Block math | `$ ... $` (with spaces) | `$ x^2 $` |
| Subscript | `_` | `$x_1$` |
| Superscript | `^` | `$x^2$` |
| Fraction | `/` | `$(a+b)/5$` |
| Alignment | `&` | `$x &= 2 \ &= 3$` |
| Line break | `\` | `$x \ y$` |

### Math Examples

These examples demonstrate common mathematical notation patterns including inline equations, block equations, matrices, and aligned multi-line equations.

```typst
// Inline equation
The formula $a^2 + b^2 = c^2$ is famous.

// Block equation
$ sum_(i=1)^n i = (n(n+1))/2 $

// Matrix
$ mat(1, 2; 3, 4) $

// Aligned equations
$ x &= 2 + 3 \
    &= 5 $
```

## Code Mode Syntax

Code mode lets you use Typst's scripting features. Prefix with `#` to enter code mode from markup. Once in code mode, you don't need additional hashes until switching back.

| Element | Syntax |
|---------|--------|
| Variable binding | `#let x = 1` |
| Function call | `#func(arg)` |
| Code block | `#{ ... }` |
| Content block | `#[ ... ]` |
| Conditional | `#if cond { } else { }` |
| Loop | `#for x in items { }` |

### Code Examples

These examples show variable definitions, loops, and conditionals. Content blocks `[...]` are used to return markup from code.

```typst
#let title = "My Document"
#let items = (1, 2, 3)

#for item in items {
  [Item: #item]
}

#if items.len() > 0 {
  [Has items]
} else {
  [Empty]
}
```

## Escape Sequences

Use backslash to escape special characters that would otherwise be interpreted as markup syntax.

| Character | Escape |
|-----------|--------|
| `\` | `\\` |
| `#` | `\#` |
| `*` | `\*` |
| `_` | `\_` |
| `$` | `\$` |
| `<` | `\<` |
| `>` | `\>` |
| `@` | `\@` |

## Symbol Shorthands

Typst provides convenient shortcuts for commonly used typographic symbols. These work in both markup and math modes.

| Symbol | Shorthand |
|--------|-----------|
| Non-breaking space | `~` |
| Em dash | `---` |
| En dash | `--` |
| Ellipsis | `...` |
| Arrow right | `->` |
| Arrow left | `<-` |
| Double arrow | `<->` |
