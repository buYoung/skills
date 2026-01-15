# Typst Syntax Reference

Typst has three syntactical modes: Markup, Math, and Code.

## Mode Switching

| New Mode | Syntax | Example |
|----------|--------|---------|
| Code | Prefix with `#` | `Number: #(1 + 2)` |
| Math | Surround with `$...$` | `$-x$ is the opposite of $x$` |
| Markup | Surround with `[..]` | `let name = [*Typst!*]` |

## Markup Mode Syntax

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

```typst
= Level 1 Heading
== Level 2 Heading
=== Level 3 Heading
```

### Lists

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

| Element | Syntax |
|---------|--------|
| Variable binding | `#let x = 1` |
| Function call | `#func(arg)` |
| Code block | `#{ ... }` |
| Content block | `#[ ... ]` |
| Conditional | `#if cond { } else { }` |
| Loop | `#for x in items { }` |

### Code Examples

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

| Symbol | Shorthand |
|--------|-----------|
| Non-breaking space | `~` |
| Em dash | `---` |
| En dash | `--` |
| Ellipsis | `...` |
| Arrow right | `->` |
| Arrow left | `<-` |
| Double arrow | `<->` |
