# Typst Common Scripting Reference

Typst includes a built-in scripting language for logic and data manipulation. This file contains scripting constructs shared by stable Typst 0.13.0 through 0.15.1. Read the selected file under `versions/` before using version-specific collection, path, or conversion APIs.

## Variables

Variables store values for reuse throughout a document. Create a binding with `let`; reassign a mutable local binding with `=` when the algorithm requires it.

### Let Bindings

Use `let` to create named bindings. Variable names can contain letters, numbers, underscores, and hyphens and must start with a letter or underscore.

```typst
#let name = "Alice"
#let count = 42
#let ratio = 3.14
#let active = true
#let items = (1, 2, 3)
#let person = (name: "Bob", age: 30)
```

### Destructuring

Extract multiple values from arrays or dictionaries in a single statement. Pattern matching makes it easy to work with structured data.

```typst
#let (a, b) = (1, 2)
#let (name: n, age: a) = (name: "Alice", age: 25)
```

## Data Types

Typst is dynamically typed. Common built-in value types include the following; this is not an exhaustive inventory.

| Type | Example |
|------|---------|
| Integer | `42`, `-10` |
| Float | `3.14`, `1e-5` |
| String | `"hello"` |
| Boolean | `true`, `false` |
| Array | `(1, 2, 3)` |
| Dictionary | `(key: "value")` |
| Content | `[*bold*]` |
| None | `none` |
| Auto | `auto` |

## Arrays

Ordered collections of values. Arrays support functional methods like `map`, `filter`, and `fold` for data transformation.

```typst
#let arr = (1, 2, 3, 4, 5)

#let length = arr.len()
#let first = arr.first()
#let last = arr.last()
#let third = arr.at(2)
#let middle = arr.slice(1, 3)
#let has-three = arr.contains(3)
#let doubled = arr.map(x => x * 2)
#let greater-than-two = arr.filter(x => x > 2)
#let sum = arr.fold(0, (a, b) => a + b)
#let joined = arr.map(str).join(", ")
```

## Dictionaries

Key-value pairs for structured data. Access values using dot notation or the `at()` method. Keys are always strings.

```typst
#let dict = (name: "Alice", age: 25)

#let name = dict.name
#let age = dict.at("age")
#let keys = dict.keys()
#let values = dict.values()
#let pairs = dict.pairs()
```

## Functions

Functions encapsulate reusable logic and can return both values and content. Define them with `let` and call them with parentheses.

### Function Definition

Named functions use `let name(parameters) = expression`. Arrow syntax creates an anonymous function, as in `x => x * 2`.

```typst
#let greet(name) = [Hello, #name!]
#let add(a, b) = a + b
```

### Default Parameters

Provide fallback values with `:` syntax. Parameters with defaults become optional when calling the function.

```typst
#let greet(name, greeting: "Hello") = [#greeting, #name!]
#greet("Alice")                    // Hello, Alice!
#greet("Bob", greeting: "Hi")      // Hi, Bob!
```

### Named Parameters

Use named arguments for clarity when calling functions with many parameters. Order doesn't matter for named arguments.

```typst
#let rect-area(width: 10, height: 5) = width * height
#rect-area()                // 50
#rect-area(width: 20)       // 100
#rect-area(height: 10)      // 100
```

### Content Functions

Functions that return styled content are the foundation of Typst templates. Use set rules inside to affect only the function's scope.

```typst
#let highlight(body) = {
  set text(fill: red)
  body
}

#highlight[Important text]
```

## Control Flow

Control the execution flow with conditionals and loops. All control structures are expressions that return values.

### Conditionals

`if` expressions evaluate to their branch's value. Use for conditional content or computation.

```typst
#let x = 5

#if x > 0 {
  [Positive]
} else if x < 0 {
  [Negative]
} else {
  [Zero]
}
```

### For Loops

Iterate over arrays, ranges, or dictionary pairs. The loop body is evaluated for each element and results are joined.

```typst
#for i in range(5) {
  [Item #i ]
}

#for (key, value) in (a: 1, b: 2) {
  [#key: #value ]
}

#for item in ("apple", "banana", "cherry") {
  list.item(item)
}
```

### While Loops

Repeat while a condition is true. Be careful to ensure the condition eventually becomes false to avoid infinite loops.

```typst
#let i = 0
#while i < 3 {
  [#i ]
  i = i + 1
}
```

## Operators

Standard operators for arithmetic, comparison, and logical operations. Note that Typst uses `and`, `or`, `not` instead of symbols for logical operators.

| Operator | Description |
|----------|-------------|
| `+`, `-`, `*`, `/` | Arithmetic |
| `==`, `!=` | Equality |
| `<`, `>`, `<=`, `>=` | Comparison |
| `and`, `or`, `not` | Logical |
| `in`, `not in` | Membership |
| `+=`, `-=`, `*=`, `/=` | Compound assignment |

## String Operations

Strings are immutable sequences of characters. Methods return new strings rather than modifying in place.

```typst
#let s = "Hello, World!"

#let length = s.len()
#let contains-world = s.contains("World")
#let starts-correctly = s.starts-with("He")
#let ends-correctly = s.ends-with("!")
#let replaced = s.replace("World", "Typst")
#let parts = s.split(", ")
#let trimmed = s.trim()
#let uppercase = upper(s)
#let lowercase = lower(s)
```

## Import and Modules

Organize code across files using imports. Import specific items or use `*` to import everything from a module.

```typst
// Import from file
#import "template.typ": conf, title

// Import all
#import "utils.typ": *

// Import with alias
#import "math.typ": formula as f
```

## Data Loading

The top-level data-loading functions accept either a forward-slash path string or encoded bytes throughout the supported range. A string is treated as a path; wrap inline serialized data in `bytes` before decoding it.

```typst
#let inline = json(bytes("{\"enabled\": true}"))

Enabled: #inline.enabled
```

Use a forward-slash path such as `json("data/example.json")` when the file exists. Use the same top-level pattern for `cbor`, `csv`, `image`, `toml`, `xml`, and `yaml`. Do not generate deprecated calls such as `json.decode` or `image.decode` for new source.

## Type Checks

Compare types to type values rather than their string names. String compatibility comparisons were deprecated in 0.13 and removed in 0.14.

```typst
#let value = (enabled: true)
#if type(value) == dictionary [Dictionary value]
```

## Context

The `context` keyword provides access to document state that depends on location, such as page numbers, counters, and current styles. Required for introspection queries.

```typst
// Access current location/state
#context {
  let current-page = counter(page).get()
  [Page: #current-page.first()]
}

// Access set rule values
#set text(lang: "ko")
#context text.lang  // "ko"
```
