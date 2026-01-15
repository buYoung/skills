# Typst Styling Reference

Typst uses set rules and show rules for styling documents.

## Set Rules

Set rules apply property values to elements throughout the document or scope.

### Syntax

```typst
#set element(property: value)
```

### Common Set Rules

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

```typst
// Apply only within block
#[
  #set text(fill: blue)
  This text is blue.
]
This text is default color.
```

## Show Rules

Show rules transform how elements appear.

### Basic Show Rule

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

```typst
// Apply set rule to specific element
#show heading: set text(fill: navy)
#show raw: set text(font: "Fira Code")
```

### Show with Function

```typst
#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  set text(size: 18pt)
  block(it.body)
}
```

### Selector Types

| Selector | Example |
|----------|---------|
| Element | `#show heading: ...` |
| Text | `#show "word": ...` |
| Regex | `#show regex("\d+"): ...` |
| Label | `#show <label>: ...` |
| Where | `#show heading.where(level: 1): ...` |

## Document Setup Pattern

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
