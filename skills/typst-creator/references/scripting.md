# Typst Scripting Reference

Typst includes a built-in scripting language for logic and data manipulation.

## Variables

### Let Bindings

```typst
#let name = "Alice"
#let count = 42
#let ratio = 3.14
#let active = true
#let items = (1, 2, 3)
#let person = (name: "Bob", age: 30)
```

### Destructuring

```typst
#let (a, b) = (1, 2)
#let (name: n, age: a) = (name: "Alice", age: 25)
```

## Data Types

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

```typst
#let arr = (1, 2, 3, 4, 5)

arr.len()           // 5
arr.first()         // 1
arr.last()          // 5
arr.at(2)           // 3
arr.slice(1, 3)     // (2, 3)
arr.contains(3)     // true
arr.map(x => x * 2) // (2, 4, 6, 8, 10)
arr.filter(x => x > 2)  // (3, 4, 5)
arr.fold(0, (a, b) => a + b)  // 15
arr.join(", ")      // "1, 2, 3, 4, 5"
```

## Dictionaries

```typst
#let dict = (name: "Alice", age: 25)

dict.name           // "Alice"
dict.at("age")      // 25
dict.keys()         // ("name", "age")
dict.values()       // ("Alice", 25)
dict.pairs()        // (("name", "Alice"), ("age", 25))
```

## Functions

### Function Definition

```typst
#let greet(name) = [Hello, #name!]
#let add(a, b) = a + b
```

### Default Parameters

```typst
#let greet(name, greeting: "Hello") = [#greeting, #name!]
#greet("Alice")                    // Hello, Alice!
#greet("Bob", greeting: "Hi")      // Hi, Bob!
```

### Named Parameters

```typst
#let rect-area(width: 10, height: 5) = width * height
#rect-area()                // 50
#rect-area(width: 20)       // 100
#rect-area(height: 10)      // 100
```

### Content Functions

```typst
#let highlight(body) = {
  set text(fill: red)
  body
}

#highlight[Important text]
```

## Control Flow

### Conditionals

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

```typst
#let i = 0
#while i < 3 {
  [#i ]
  i = i + 1
}
```

## Operators

| Operator | Description |
|----------|-------------|
| `+`, `-`, `*`, `/` | Arithmetic |
| `==`, `!=` | Equality |
| `<`, `>`, `<=`, `>=` | Comparison |
| `and`, `or`, `not` | Logical |
| `in`, `not in` | Membership |
| `+=` | Addition assignment |

## String Operations

```typst
#let s = "Hello, World!"

s.len()             // 13
s.contains("World") // true
s.starts-with("He") // true
s.ends-with("!")    // true
s.replace("World", "Typst")  // "Hello, Typst!"
s.split(", ")       // ("Hello", "World!")
s.trim()            // removes whitespace
upper(s)            // "HELLO, WORLD!"
lower(s)            // "hello, world!"
```

## Import and Modules

```typst
// Import from file
#import "template.typ": conf, title

// Import all
#import "utils.typ": *

// Import with alias
#import "math.typ": formula as f
```

## Context

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
