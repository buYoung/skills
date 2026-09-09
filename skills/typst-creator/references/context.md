# Context, State, and Queries

Checked: 2026-09-09. The examples below use APIs shared by stable 0.13.0–0.15.1. They are independent snippets unless a dependency is stated.

## Context Produces Content

A context expression can use styles and location at the position where its result is inserted. The result itself is opaque content. Do not assign `context counter(page).get()` to a variable and then try to index or compare it outside the context. Keep dependent computation inside:

```typst
#context {
  let page-number = counter(page).get().first()
  if calc.even(page-number) [Even page] else [Odd page]
}
```

Context can be evaluated zero, one, or several times as content is laid out. It is not a one-time imperative execution block. A show rule establishes style context; location-dependent operations additionally require a locatable matched element. The locatable element set expanded in 0.14, so check the target reference before relying on an unlabelled element's location.

## Counters and Document Order

Counters return arrays because some, such as headings, are hierarchical. Prefer `display` for formatted output and `get` for computations. Insert an update's returned content where the change should take effect.

```typst
#set heading(numbering: "1.1")
= First
#context [Heading: #counter(heading).display()]
#counter(page).update(1)
#context [Logical page: #counter(page).display("1")]
```

Resetting the page counter changes logical numbering, not the physical index of pages in a PDF. `counter(page).final()` is the final counter value, not necessarily a physical page count after resets.

## State for Placement-Dependent Values

Functions cannot mutate captured outer variables. Use normal returned values for ordinary calculations and `state` for values that evolve in document order.

```typst
#let total = state("running-total", 0)
#let add(amount) = total.update(previous => previous + amount)

#add(2)
#context [First total: #total.get()]
#add(3)
#context [Final total: #total.get()]
```

State updates run in layout order, which may differ from source evaluation order. `let change = total.update(2)` has no effect until `change` is inserted. Prefer `update(previous => ...)` to reading a contextual value and feeding it back into the update.

## Queries and Locations

Use stable labels for specific destinations. Use selectors to collect document elements, and location values for position-sensitive operations. A query can observe matching elements later in the document.

```typst
#set heading(numbering: "1.")
= Method <method>
= Results <results>

#context {
  let headings = query(heading)
  [There are #headings.len() headings.]
  [Method appears on page #locate(<method>).page().]
}
```

Use `here()` for the current location; use `counter(...).at(location)` to inspect a counter elsewhere. Do not pass the removed explicit current-location arguments to `query`, `state.at`, or `counter.at`. The desired target location is still required by `at`; what was removed in 0.13 was an extra argument supplying the current context location.

For 0.15-only descendant queries, see `selector.within` in [0.15](versions/0.15.md). It is not a show-rule selector.

## Convergence and Troubleshooting

Typst may lay out a document repeatedly to resolve context and introspection. If output depends on a future state which that same output changes, it can fail to converge. A query-driven list that creates more elements matching its own query is another common cause.

Keep the content determining a query or state update independent of its own result, narrow selectors, and use an update callback's previous value. Read convergence diagnostics rather than assuming one more compiler invocation will fix the dependency. Starting with 0.15, diagnostics provide more detail about non-convergence.

## Sources

- [Context](https://typst.app/docs/reference/context/)
- [Counters](https://typst.app/docs/reference/introspection/counter/)
- [State](https://typst.app/docs/reference/introspection/state/)
- [Query](https://typst.app/docs/reference/introspection/query/)
- [0.13 removals](https://typst.app/docs/changelog/0.13.0/#removals)
