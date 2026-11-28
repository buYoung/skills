# Ownership and Borrowing

## Contents

- [Ownership, Borrowing, and Resource Lifetimes](#ownership-borrowing-and-resource-lifetimes)
- [Choose an Ownership Structure](#choose-an-ownership-structure)
- [Parameter and Return Types](#parameter-and-return-types)
- [Cow for Sometimes-Owned Data](#cow-for-sometimes-owned-data)
- [Borrow While Parsing, Own at a Retention Boundary](#borrow-while-parsing-own-at-a-retention-boundary)
- [Clones: Deliberate, Not Defensive](#clones-deliberate-not-defensive)
- [Shared Ownership and Cycles](#shared-ownership-and-cycles)
- [Interior Mutability](#interior-mutability)
- [Moving Out of &mut with mem::take](#moving-out-of-mut-with-memtake)
- [Common Mistakes](#common-mistakes)
- [Availability by Version](#availability-by-version)
- [Practical Boundaries](#practical-boundaries)

Examples use stable APIs unless marked otherwise; see [compatibility](../../SKILL.md#compatibility). Cleanup and drop order continue in [RAII and Drop](raii-and-drop.md); thread-shared state in [concurrency](concurrency.md); invariants and type patterns in [type design](type-design.md); dispatch choices in [traits and dispatch](traits-and-dispatch.md).

## Ownership, Borrowing, and Resource Lifetimes

Ownership determines responsibility for a value and its resources. Moving a `String` transfers that responsibility without cloning its text buffer. `Copy` permits implicit duplication; `Clone` is an explicit, type-defined operation whose cost and sharing behavior depend on the implementation. Ownership transfer, payload copying, and heap allocation are separate concepts.

A reference provides access without taking ownership. Shared references permit shared access, with mutation available only through appropriate interior-mutability abstractions. An exclusive borrow provides mutable access while preventing conflicting accesses for the borrow's duration. Borrows of separate fields or disjoint slices can coexist when their separation is established.

Lifetime annotations describe relationships between references; they do not keep an owner alive or extend a local variable's lifetime. Borrowing is useful for temporary access or a deliberate view into a longer-lived owner. Owned results fit freshly created data and independent lifetimes. A struct containing references also makes those lifetime relationships part of its API.

Resource lifetime includes lock guards, files, and foreign handles as well as heap memory. RAII ties ordinary cleanup to destruction; early returns and unwinding therefore affect resource release. Process abort does not run destructors. Fallible completion, such as flushing a writer, often needs an explicit operation in addition to `Drop`. See [RAII](raii-and-drop.md#raii-guards-and-drop) and [memory allocation](memory-and-allocation.md#storage-allocation-and-release).

## Choose an Ownership Structure

A clear ownership hierarchy is a useful starting point: components own state and functions borrow it for bounded work. Shared graphs, caches, and retained views can legitimately use Rc, Arc, interior mutability, indices, or arena handles. Choose those mechanisms from lifetime and mutation requirements rather than forcing every design into a tree or treating every clone as a defect. See [allocation](memory-and-allocation.md) for storage costs and [module boundaries](modules-and-crate-boundaries.md) for component ownership.

Questions that settle most designs:

1. Who creates the value, who mutates it, who reads it, and which of them lives longest?
2. Does the value cross threads? If so, `Send`/`Sync` decide between `Rc`/`RefCell` and `Arc`/`Mutex` immediately.
3. Is the set of variants or implementors closed (you control it) or open (users extend it)?
4. Which invariants must hold for every instance, and where are they checked today?

## Parameter and Return Types

Borrow when the operation only needs access; take ownership when it stores, consumes, transforms, or transfers the value. A small Copy value can simply be passed by value.

| Situation | Parameter type | Accepts |
|---|---|---|
| Read text | `&str` | `&String`, `&str`, `&Box<str>`, `&Cow<str>` through deref coercion |
| Read a sequence | `&[T]` | `&Vec<T>`, `&[T; N]`, `&Box<[T]>` |
| Read a path | `&Path` or `impl AsRef<Path>` | `&PathBuf`, `&str`, `&String`, `&OsStr` |
| Mutate in place | `&mut [T]`, `&mut String` | the owner's exclusive borrow |
| Store the value in `self` | `String`, `Vec<T>`, `PathBuf` (owned) or `impl Into<String>` | owned values; `impl Into` also accepts `&str` at the cost of a copy |
| Call a callback once | `impl FnOnce(..)` | closures that move captured state |
| Read a small Copy value | Usually by value | For large Copy values, consider access patterns and copying cost |

```rust
use std::path::Path;

fn line_count(text: &str) -> usize {
    text.lines().count()
}

fn checksum(bytes: &[u8]) -> u32 {
    bytes.iter().map(|&b| u32::from(b)).sum()
}

fn read_config(path: impl AsRef<Path>) -> std::io::Result<String> {
    std::fs::read_to_string(path)
}

struct Service {
    name: String,
}

impl Service {
    /// Stores `name`, so it takes ownership; `impl Into<String>` lets callers pass `&str` or `String`.
    fn new(name: impl Into<String>) -> Self {
        Service { name: name.into() }
    }

    /// Returns a view; callers that need an owned copy call `.to_owned()` themselves.
    fn name(&self) -> &str {
        &self.name
    }
}
```

Parameters such as `&String` and `&Vec<T>` require a particular owning representation even when the function needs only a string or slice view. Clippy `ptr_arg` (style) identifies common cases where a borrowed view would accept more callers. Ownership-specific operations such as changing a Vec's capacity still need that concrete type. A borrowed-view API leaves copying and storage choices to the caller.

Return borrowed data when it lives inside `self` or an argument and the caller can hold the borrow; return owned data when it is freshly computed. A returned `&str` tied to a local `String` does not compile, which is the borrow checker telling you the value needs an owner.

## Cow for Sometimes-Owned Data

When most inputs pass through unchanged and a few need modification, `Cow` avoids allocating in the common case.

```rust
use std::borrow::Cow;

fn normalize_newlines(input: &str) -> Cow<'_, str> {
    if input.contains("\r\n") {
        Cow::Owned(input.replace("\r\n", "\n"))
    } else {
        Cow::Borrowed(input)
    }
}

struct Label<'a> {
    text: Cow<'a, str>, // borrowed from config, or owned when computed at runtime
}

impl<'a> Label<'a> {
    fn from_static(text: &'a str) -> Self {
        Label { text: Cow::Borrowed(text) }
    }
    fn computed(prefix: &str, n: u32) -> Label<'static> {
        Label { text: Cow::Owned(format!("{prefix}-{n}")) }
    }
    fn into_owned(self) -> String {
        self.text.into_owned()
    }
}
```

`Cow<'a, [T]>` and `Cow<'a, Path>` work the same way. `to_mut()` converts to the owned variant on demand.

## Borrow While Parsing, Own at a Retention Boundary

Borrowed views avoid copying data while its input owner is already available. A long-lived cache or independent task may instead need a small owned result so a large input allocation can be released. Make that transition explicit in the API rather than extending lifetimes throughout unrelated layers.

```rust
#[derive(Debug, PartialEq, Eq)]
pub struct SettingView<'a> { pub key: &'a str, pub value: &'a str }
#[derive(Debug, PartialEq, Eq)]
pub struct Setting { pub key: String, pub value: String }

pub fn parse_setting(line: &str) -> Option<SettingView<'_>> {
    let (key, value) = line.split_once('=')?;
    let key = key.trim();
    if key.is_empty() { return None; }
    Some(SettingView { key, value: value.trim() })
}

impl SettingView<'_> {
    pub fn into_owned(self) -> Setting {
        Setting { key: self.key.to_owned(), value: self.value.to_owned() }
    }
}

pub fn retained_setting(config: &str, wanted: &str) -> Option<Setting> {
    config.lines().filter_map(parse_setting)
        .find(|entry| entry.key == wanted).map(SettingView::into_owned)
}
```

This parser treats a malformed line as absent from a search; a configuration validator needing line-specific failures should return a structured Result instead. The view's fields point into config. The owned setting contains only the selected strings and can outlive config, allowing the caller to drop a large input. Keeping Arc<String> plus offsets would avoid those small copies while retaining the entire allocation; that can be appropriate when many views share most of the input.

A self-referential struct containing both a String and references into itself is not created merely by adding a lifetime parameter. Owned storage plus checked offsets/indices can represent that relationship without internal references. Mutation, reallocation, and UTF-8 character boundaries still constrain how those offsets may be used. Pin is not a general repair for a poorly chosen ownership boundary.

## Clones: Deliberate, Not Defensive

`clone()` inserted to make a borrow error go away is a recognized anti-pattern: the copy silently forks state, so later mutations no longer agree, and the cost hides in hot paths. Reorder the operations or shorten the borrow instead.

```rust
struct Inventory {
    items: Vec<String>,
}

// Before: the clone exists only to release the borrow on `inv.items`.
fn audit_before(inv: &mut Inventory) -> usize {
    let items = inv.items.clone(); // copies every String
    inv.items.push("audit".to_owned());
    items.len()
}

// After: read what is needed, end the borrow, then mutate.
fn audit_after(inv: &mut Inventory) -> usize {
    let count = inv.items.len();
    inv.items.push("audit".to_owned());
    count
}
```

Clones that are fine: `Rc::clone`/`Arc::clone` (a reference-count increment, no data copy), `Copy` types, small strings on cold paths, and clones that intentionally snapshot state. When a clone stays, name the reason in a comment. Clippy `redundant_clone` (nursery, opt-in) finds clones of values that are dropped immediately.

## Shared Ownership and Cycles

`Rc<T>` gives shared ownership on one thread; `Arc<T>` uses atomic counts and works across threads at a small cost per clone and drop. Neither allows mutation through the shared handle; pair with `RefCell` (single thread) or `Mutex`/`RwLock`/atomics (threads). A strong cycle is never freed, so back-references use `Weak`.

```rust
use std::cell::RefCell;
use std::rc::{Rc, Weak};

struct Node {
    name: String,
    parent: RefCell<Weak<Node>>,
    children: RefCell<Vec<Rc<Node>>>,
}

fn new_node(name: &str) -> Rc<Node> {
    Rc::new(Node {
        name: name.to_owned(),
        parent: RefCell::new(Weak::new()),
        children: RefCell::new(Vec::new()),
    })
}

fn add_child(parent: &Rc<Node>, name: &str) -> Rc<Node> {
    let child = new_node(name);
    *child.parent.borrow_mut() = Rc::downgrade(parent); // Weak: does not keep the parent alive
    parent.children.borrow_mut().push(Rc::clone(&child)); // strong: parent owns children
    child
}

fn parent_name(node: &Node) -> Option<String> {
    node.parent.borrow().upgrade().map(|p| p.name.clone())
}
```

An arena of nodes indexed by a newtype (see [graphs and trees](graphs-and-trees.md#graphs-and-trees-without-reference-cycles)) avoids reference counting entirely and is the usual choice for graphs, ASTs, and entity systems. `Rc::make_mut`/`Arc::make_mut` give clone-on-write: they mutate in place when the count is one and clone otherwise.

## Interior Mutability

Interior mutability lets a `&T` mutate; it is the escape hatch for caches, counters, and lazy initialization behind shared references, not the default design.

| Type | For | Cost and rules | Threads |
|---|---|---|---|
| `Cell<T>` | Move/replace values; Copy permits get | No runtime borrow tracking | Send if T: Send; not Sync |
| `RefCell<T>` | Runtime-checked borrowing | Conflicting borrows panic; try_borrow variants report failure | Send if T: Send; not Sync |
| `OnceCell<T>` | Set once, read many | `get_or_init`; initializer panic leaves it empty | `!Sync` |
| `LazyCell<T, F>` (1.80) | Lazily computed value | deref initializes | `!Sync` |
| `Mutex<T>`, `RwLock<T>` | Shared mutable state across threads | Blocking locks, poisoning | Mutex: Sync if T: Send; RwLock additionally needs T: Sync |
| `OnceLock<T>`, `LazyLock<T, F>` | One-time init across threads | see [synchronization](synchronization.md#one-time-and-lazy-initialization) | `Sync` |
| Atomics | Counters and flags across threads | lock-free | `Sync` |

```rust
use std::cell::{Cell, OnceCell, RefCell};

struct Metrics {
    hits: Cell<u64>,
    recent: RefCell<Vec<String>>,
    label: OnceCell<String>,
}

impl Metrics {
    fn record(&self, name: &str) {
        self.hits.set(self.hits.get() + 1);
        self.recent.borrow_mut().push(name.to_owned());
    }

    fn label(&self) -> &str {
        self.label.get_or_init(|| format!("metrics-{}", self.hits.get()))
    }

    fn last(&self) -> Option<String> {
        // Copy the value out so the RefCell borrow ends here, not at the caller.
        self.recent.borrow().last().cloned()
    }
}
```

A RefCell borrow crossing unknown callbacks can cause reentrant borrow failures. Returning Ref/RefMut is possible but exposes a guard lifetime callers must understand. If sharing later crosses threads, reconsider ownership, messages, snapshots, or locks; mechanically replacing every Rc/RefCell with Arc/Mutex can preserve an unsuitable design.

## Moving Out of &mut with mem::take

You cannot move a field out of `&mut self` and leave a hole, but you can swap in a placeholder. `mem::take` uses `Default`, `mem::replace` takes an explicit replacement. This avoids cloning during state transitions.

```rust
use std::mem;

enum Connection {
    Idle { buffer: Vec<u8> },
    Sending { buffer: Vec<u8>, sent: usize },
    Closed,
}

fn start_sending(conn: &mut Connection) {
    if let Connection::Idle { buffer } = conn {
        let buffer = mem::take(buffer); // Vec::new() does not allocate
        *conn = Connection::Sending { buffer, sent: 0 };
    }
}

fn close(conn: &mut Connection) -> Option<Vec<u8>> {
    match mem::replace(conn, Connection::Closed) {
        Connection::Idle { buffer } | Connection::Sending { buffer, .. } => Some(buffer),
        Connection::Closed => None,
    }
}
```

`Option::take` is the same idea for optional fields.

## Common Mistakes

- Storing `&'a str` in a long-lived struct to avoid a `String` allocation, then fighting lifetimes through the whole codebase. Own the data at the boundary; borrow inside functions.
- `Rc<RefCell<T>>` as the default way to share state between components, instead of one owner and message passing or borrowed views.
- `impl Into<String>` on a function that only reads the string; it forces callers with a `&str` to allocate.

## Availability by Version

| Version | Addition |
|---|---|
| 1.80 | `LazyCell`, `LazyLock` |
| 1.86 | `<[T]>::get_disjoint_mut` |
| 1.88 | `let` chains (edition 2024 only); `Cell::update` |
| 1.100 | `Box::map`, `Rc::map`, `Arc::map` |

Per-release details live in [the versions index](../versions/index.md).

## Practical Boundaries

Borrowing keeps access tied to an owner; shared ownership makes a different lifetime contract. A clone can simplify that contract or avoid retaining unrelated data. Evaluate the actual type and access pattern before exchanging one for the other.
