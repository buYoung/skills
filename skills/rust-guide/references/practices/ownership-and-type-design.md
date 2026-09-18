# Ownership and Type Design

## Contents

- [Ownership Is a Tree](#ownership-is-a-tree)
- [Parameter and Return Types](#parameter-and-return-types)
- [Cow for Sometimes-Owned Data](#cow-for-sometimes-owned-data)
- [Clones: Deliberate, Not Defensive](#clones-deliberate-not-defensive)
- [Shared Ownership and Cycles](#shared-ownership-and-cycles)
- [Interior Mutability](#interior-mutability)
- [Newtypes](#newtypes)
- [Enforce Invariants at the Boundary](#enforce-invariants-at-the-boundary)
- [Typestate](#typestate)
- [RAII Guards and Drop](#raii-guards-and-drop)
- [Drop Order Rules](#drop-order-rules)
- [Moving Out of &mut with mem::take](#moving-out-of-mut-with-memtake)
- [Composition, Not Deref Inheritance](#composition-not-deref-inheritance)
- [Enum, Trait, Generic, or dyn](#enum-trait-generic-or-dyn)
- [Dyn Compatibility](#dyn-compatibility)
- [Sealed and Extension Traits](#sealed-and-extension-traits)
- [Builders and Optional Configuration](#builders-and-optional-configuration)
- [Extensible Types with non_exhaustive](#extensible-types-with-non_exhaustive)
- [Async Functions in Traits](#async-functions-in-traits)
- [Common Mistakes](#common-mistakes)
- [Availability by Version](#availability-by-version)
- [Review Checklist](#review-checklist)

Examples compile on stable Rust 1.80 or later with edition 2024 unless a version is stated. Thread-shared state continues in [concurrency](concurrency.md); public-surface rules in [API and crate design](api-and-crate-design.md).

## Ownership Is a Tree

"Every Rust value has precisely one owner at all times." A design that compiles easily has a tree: the application owns subsystems, subsystems own their state, functions borrow downward for the duration of a call. Borrows that must outlive the call, values with two owners, and back-references are where `Rc`, `Arc`, `RefCell`, lifetimes on structs, and `clone()` start to appear. Draw the tree before choosing any of those tools; most of the time the fix is to move the data to the component that actually owns it, or to pass a borrowed view down instead of storing it.

Questions that settle most designs:

1. Who creates the value, who mutates it, who reads it, and which of them lives longest?
2. Does the value cross threads? If so, `Send`/`Sync` decide between `Rc`/`RefCell` and `Arc`/`Mutex` immediately.
3. Is the set of variants or implementors closed (you control it) or open (users extend it)?
4. Which invariants must hold for every instance, and where are they checked today?

## Parameter and Return Types

Take the least specific borrowed view that does the job, and take ownership only when the function stores the value.

| Situation | Parameter type | Accepts |
|---|---|---|
| Read text | `&str` | `&String`, `&str`, `&Box<str>`, `&Cow<str>` through deref coercion |
| Read a sequence | `&[T]` | `&Vec<T>`, `&[T; N]`, `&Box<[T]>` |
| Read a path | `&Path` or `impl AsRef<Path>` | `&PathBuf`, `&str`, `&String`, `&OsStr` |
| Mutate in place | `&mut [T]`, `&mut String` | the owner's exclusive borrow |
| Store the value in `self` | `String`, `Vec<T>`, `PathBuf` (owned) or `impl Into<String>` | owned values; `impl Into` also accepts `&str` at the cost of a copy |
| Call a callback once | `impl FnOnce(..)` | closures that move captured state |
| Read a large `Copy` value | by value, not `&` | `Copy` types smaller than a pointer or two |

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

`&String`, `&Vec<T>`, and `&Box<T>` as parameters add an indirection and reject callers that hold a `&str`, an array, or a boxed slice; Clippy `ptr_arg` (style) reports them. The API Guidelines' C-CALLER-CONTROL principle: the caller decides where data is copied or placed, so a function that only reads should not force an allocation.

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

An arena of nodes indexed by a newtype (see [collections](collections.md#graphs-and-trees-without-reference-cycles)) avoids reference counting entirely and is the usual choice for graphs, ASTs, and entity systems. `Rc::make_mut`/`Arc::make_mut` give clone-on-write: they mutate in place when the count is one and clone otherwise.

## Interior Mutability

Interior mutability lets a `&T` mutate; it is the escape hatch for caches, counters, and lazy initialization behind shared references, not the default design.

| Type | For | Cost and rules | Threads |
|---|---|---|---|
| `Cell<T>` | `Copy` values (counters, flags) | `get`/`set`/`update`; no borrow tracking | `Send`, `!Sync` |
| `RefCell<T>` | Non-`Copy` values | `borrow`/`borrow_mut` checked at runtime; a second `borrow_mut` panics | `Send`, `!Sync` |
| `OnceCell<T>` | Set once, read many | `get_or_init`; initializer panic leaves it empty | `!Sync` |
| `LazyCell<T, F>` (1.80) | Lazily computed value | deref initializes | `!Sync` |
| `Mutex<T>`, `RwLock<T>` | Shared mutable state across threads | blocking locks, poisoning | `Sync` when `T: Send` |
| `OnceLock<T>`, `LazyLock<T, F>` | One-time init across threads | see [concurrency](concurrency.md) | `Sync` |
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

A `RefCell` borrow held across a call into unknown code is a latent panic; keep `borrow()` results in the smallest scope, and never return a `Ref`/`RefMut` from a public API. If a `RefCell` design later needs threads, every `RefCell` becomes a `Mutex` and every `Rc` an `Arc`; deciding thread-safety up front is cheaper.

## Newtypes

A newtype is a one-field struct that gives a plain value a distinct type. It prevents mixing ids, units, and encodings, and it lets you implement foreign traits on foreign types. Unlike a type alias, a newtype is not interchangeable with the wrapped type, and it forwards nothing by default: choose the traits and methods deliberately.

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub struct UserId(u64);

impl UserId {
    pub const fn new(raw: u64) -> Self {
        Self(raw)
    }
    pub const fn get(self) -> u64 {
        self.0
    }
}

impl std::fmt::Display for UserId {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "user-{}", self.0)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub struct OrderId(u64);

fn cancel_order(order: OrderId, requested_by: UserId) -> bool {
    order.0 != requested_by.0 // the compiler already prevents passing them swapped
}
```

Derive `Clone`, `Copy` (for small values), `PartialEq`, `Eq`, `Hash`, `PartialOrd`, `Ord`, and `Debug` when the wrapped type has them and the semantics carry over; implement `Display` yourself. Do not derive `PartialOrd`/`Ord` for ids that have no meaningful order, and do not implement `Deref` to the inner type: the API Guidelines reserve `Deref` for smart pointers, and it would forward every method, defeating the purpose. Expose `get()`/`into_inner()` instead. Keep the field private when the type carries an invariant.

## Enforce Invariants at the Boundary

Validate once where data enters, produce a type that can only hold valid values, and let the rest of the program rely on the type. Constructors return `Result`; the field stays private so no other path can create an invalid instance.

```rust
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Username(String);

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum UsernameError {
    Empty,
    TooLong(usize),
    InvalidChar(char),
}

impl Username {
    pub const MAX_CHARS: usize = 32;

    pub fn new(raw: &str) -> Result<Self, UsernameError> {
        let len = raw.chars().count();
        if len == 0 {
            return Err(UsernameError::Empty);
        }
        if len > Self::MAX_CHARS {
            return Err(UsernameError::TooLong(len));
        }
        if let Some(c) = raw.chars().find(|c| !c.is_ascii_alphanumeric() && *c != '_') {
            return Err(UsernameError::InvalidChar(c));
        }
        Ok(Self(raw.to_owned()))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl TryFrom<String> for Username {
    type Error = UsernameError;
    fn try_from(value: String) -> Result<Self, Self::Error> {
        Username::new(&value)
    }
}

impl std::fmt::Display for Username {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(&self.0)
    }
}

fn greet(user: &Username) -> String {
    format!("hello, {user}") // no re-validation anywhere downstream
}
```

Functions that take `&Username` instead of `&str` document and enforce the precondition in the signature. A `Deserialize` impl should go through `new` (serde's `try_from = "String"` attribute does this) so deserialized values obey the same rule. Mutation methods must preserve the invariant or return `Result`.

## Typestate

When an object moves through phases and some operations are valid only in some phases, encode the phase in the type. Misuse becomes a compile error instead of a runtime `Err` or a forgotten check.

```rust
use std::marker::PhantomData;

pub struct Draft;
pub struct Sent;

pub struct Email<State> {
    to: String,
    body: String,
    _state: PhantomData<State>,
}

impl Email<Draft> {
    pub fn new(to: impl Into<String>) -> Self {
        Email { to: to.into(), body: String::new(), _state: PhantomData }
    }

    pub fn body(mut self, body: &str) -> Self {
        self.body = body.to_owned();
        self
    }

    /// Consumes the draft; there is no way to edit or resend a sent email.
    pub fn send(self) -> Email<Sent> {
        Email { to: self.to, body: self.body, _state: PhantomData }
    }
}

impl Email<Sent> {
    pub fn recipient(&self) -> &str {
        &self.to
    }
}
```

Typestate suits a small, fixed set of phases decided at compile time (builder stages, connection handshakes, request lifecycles). When phases are decided by runtime data, or the state set is large, use a state `enum` and return `Result` for invalid transitions; the Comprehensive Rust course notes that a runtime flag design means "Rust's type system cannot help enforce the correctness of our state transitions."

## RAII Guards and Drop

Tie cleanup to a value's lifetime with `Drop` so callers cannot forget it. `Drop::drop` cannot return an error and cannot `.await`; when cleanup can fail or must be asynchronous, provide an explicit consuming method and keep `Drop` as the fallback.

```rust
use std::io::{self, Write};

#[must_use = "a Transaction that is dropped without commit() rolls back"]
pub struct Transaction<W: Write> {
    writer: W,
    committed: bool,
}

impl<W: Write> Transaction<W> {
    pub fn begin(mut writer: W) -> io::Result<Self> {
        writeln!(writer, "BEGIN")?;
        Ok(Self { writer, committed: false })
    }

    pub fn write(&mut self, statement: &str) -> io::Result<()> {
        writeln!(self.writer, "{statement}")
    }

    /// Fallible cleanup goes through an explicit method; errors reach the caller.
    pub fn commit(mut self) -> io::Result<()> {
        writeln!(self.writer, "COMMIT")?;
        self.committed = true;
        Ok(())
    }
}

impl<W: Write> Drop for Transaction<W> {
    fn drop(&mut self) {
        if !self.committed {
            // Drop cannot report failure. Log it or ignore it; never panic here, because a panic
            // during unwinding aborts the process.
            let _ = writeln!(self.writer, "ROLLBACK");
        }
    }
}
```

Rules from the API Guidelines: destructors never fail (C-DTOR-FAIL) and destructors that may block offer a non-blocking alternative (C-DTOR-BLOCK). `#[must_use]` on the guard type makes `Transaction::begin(w)?;` without a binding a warning. `mem::forget` and `ManuallyDrop` skip `Drop` without unsafety, so a guard cannot guarantee that cleanup runs; leaking is safe, it is just a bug.

## Drop Order Rules

- Local variables drop in reverse declaration order at the end of their block.
- Struct fields drop in declaration order; tuple elements in order; the active enum variant's fields in declaration order.
- Variables bound in one pattern drop in reverse order of declaration within the pattern.
- Temporaries drop at the end of the enclosing statement, except that edition 2024 drops `if let` scrutinee temporaries before the `else` branch and block tail-expression temporaries before the block's locals.
- `let _ = value;` drops immediately because `_` does not bind; `let _guard = value;` keeps it alive to the end of the scope.

```rust
struct Guard(&'static str);

impl Drop for Guard {
    fn drop(&mut self) {
        println!("drop {}", self.0);
    }
}

fn main() {
    let _first = Guard("first"); // dropped last
    let _second = Guard("second"); // dropped before `first`
    let _ = Guard("temporary"); // dropped right here
    println!("end of main");
}
// Output: drop temporary, end of main, drop second, drop first
```

Lock guards, spans, and timers depend on these rules; Clippy `let_underscore_lock` (correctness, deny) catches `let _ = mutex.lock()`.

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

## Composition, Not Deref Inheritance

Rust has no struct inheritance. Implementing `Deref` to a field to "inherit" its methods is an anti-pattern: every method of the inner type leaks into the outer type's API, method resolution becomes surprising, and the API Guidelines reserve `Deref` for smart pointers (C-DEREF). Compose and delegate the operations that make sense.

```rust
struct Engine {
    rpm: u32,
}

impl Engine {
    fn rev(&mut self) {
        self.rpm += 100;
    }
    fn rpm(&self) -> u32 {
        self.rpm
    }
}

struct Car {
    engine: Engine,
    gear: u8,
}

impl Car {
    fn accelerate(&mut self) {
        self.engine.rev();
        if self.engine.rpm() > 3000 && self.gear < 6 {
            self.gear += 1;
        }
    }

    fn rpm(&self) -> u32 {
        self.engine.rpm()
    }
}
```

Shared behavior across types goes into a trait with default methods; shared data goes into a struct that both types contain. When deriving traits on a composed struct, every field type must implement the trait.

## Enum, Trait, Generic, or dyn

| Need | Choose | Why |
|---|---|---|
| Closed set of alternatives you control | `enum` | Exhaustive `match`, no allocation, data per variant |
| Behavior others may implement | `trait` | Open extension; the trait is the contract |
| One concrete type per call site, hot path | generic `T: Trait` or `impl Trait` | Monomorphized and inlinable; "for each unique type that substitutes a parameter a new version of that function is generated" |
| Heterogeneous collection, plugin boundary, smaller binary | `dyn Trait` behind `Box`, `&`, `Rc`, `Arc` | One copy of the code, vtable call, type erased |
| Both open and restricted | sealed trait | Users can name and call it, cannot implement it |

```rust
// Closed set: an enum with data per variant.
enum Shape {
    Circle { radius: f64 },
    Rect { width: f64, height: f64 },
}

impl Shape {
    fn area(&self) -> f64 {
        match self {
            Shape::Circle { radius } => std::f64::consts::PI * radius * radius,
            Shape::Rect { width, height } => width * height,
        }
    }
}

// Open set: a trait others can implement.
trait Area {
    fn area(&self) -> f64;
}

impl Area for Shape {
    fn area(&self) -> f64 {
        Shape::area(self)
    }
}

// Static dispatch: one instantiation per T, fully inlinable.
fn total_area<T: Area>(items: &[T]) -> f64 {
    items.iter().map(Area::area).sum()
}

// Dynamic dispatch: one function, mixed concrete types, one vtable call per item.
fn total_area_dyn(items: &[Box<dyn Area>]) -> f64 {
    items.iter().map(|item| item.area()).sum()
}
```

Reaching for `dyn Trait` first is the pitfall the Comprehensive Rust course calls out: it trades knowledge the compiler and reader have for flexibility that may never be used, and it forces downcasts and allocations as soon as a type-specific operation is needed. Try an enum or generics first; use `dyn` when the set of types is open and heterogeneous at runtime, or when binary size matters more than the vtable call. Generic-heavy code pays in compile time and binary size; the Performance Book's `cargo llvm-lines` shows which generic functions are instantiated most.

## Dyn Compatibility

A trait is usable as `dyn Trait` only when every method is callable through a vtable: no generic methods, no `Self` by value in arguments or returns, no associated constants, and no `where Self: Sized` on the trait itself. Methods that break the rule can opt out individually with `where Self: Sized`.

```rust
trait Storage {
    fn get(&self, key: &str) -> Option<Vec<u8>>;
    fn put(&mut self, key: &str, value: Vec<u8>);

    /// Generic helper: excluded from the vtable so the trait stays dyn-compatible.
    fn get_as<T: From<Vec<u8>>>(&self, key: &str) -> Option<T>
    where
        Self: Sized,
    {
        self.get(key).map(T::from)
    }
}

fn read_all(stores: &[Box<dyn Storage>], key: &str) -> Vec<Vec<u8>> {
    stores.iter().filter_map(|s| s.get(key)).collect()
}
```

Since 1.86, `&dyn Sub` coerces to `&dyn Super` (trait upcasting), which removes the `fn as_super(&self) -> &dyn Super` boilerplate. Keep public traits dyn-compatible when trait objects are plausible for users (C-OBJECT); adding a generic method later without `where Self: Sized` is a breaking change for `dyn` users.

## Sealed and Extension Traits

A sealed trait is public but cannot be implemented outside the crate because it requires a private supertrait. Use it when downstream implementations would be unsound, unstable, or would prevent you from adding methods later.

```rust
mod sealed {
    pub trait Sealed {}
}

pub trait Backend: sealed::Sealed {
    fn name(&self) -> &'static str;
}

pub struct Postgres;
pub struct Sqlite;

impl sealed::Sealed for Postgres {}
impl sealed::Sealed for Sqlite {}

impl Backend for Postgres {
    fn name(&self) -> &'static str {
        "postgres"
    }
}

impl Backend for Sqlite {
    fn name(&self) -> &'static str {
        "sqlite"
    }
}
```

Compared with an enum, a sealed trait hides the list of implementors and monomorphizes per type; compared with an open trait, it keeps the right to add required methods in a minor release. An extension trait adds methods to a foreign type:

```rust
pub trait StrExt {
    fn is_blank(&self) -> bool;
}

impl StrExt for str {
    fn is_blank(&self) -> bool {
        self.trim().is_empty()
    }
}

fn check(input: &str) -> bool {
    input.is_blank()
}
```

Define an extension trait only when method syntax reads clearly better than a free function, and name it `<Type>Ext`; a later inherent method with the same name on the foreign type takes priority and silently changes behavior.

## Builders and Optional Configuration

For a type with several optional settings or multiple construction paths, a builder keeps the constructor signature stable and readable (C-BUILDER). For a few fields with sensible defaults, `Default` plus struct update syntax is enough.

```rust
#[derive(Debug, Clone)]
pub struct Server {
    host: String,
    port: u16,
    workers: usize,
    tls: bool,
}

#[must_use = "call build() to obtain the Server"]
pub struct ServerBuilder {
    host: String,
    port: u16,
    workers: usize,
    tls: bool,
}

impl Server {
    pub fn builder(host: impl Into<String>) -> ServerBuilder {
        ServerBuilder { host: host.into(), port: 8080, workers: 4, tls: false }
    }
}

impl ServerBuilder {
    pub fn port(mut self, port: u16) -> Self {
        self.port = port;
        self
    }
    pub fn workers(mut self, workers: usize) -> Self {
        self.workers = workers.max(1);
        self
    }
    pub fn tls(mut self, enabled: bool) -> Self {
        self.tls = enabled;
        self
    }
    pub fn build(self) -> Server {
        Server { host: self.host, port: self.port, workers: self.workers, tls: self.tls }
    }
}

#[derive(Debug, Clone, Default)]
pub struct RetryPolicy {
    pub attempts: u8,
    pub backoff_ms: u64,
}

fn aggressive() -> RetryPolicy {
    RetryPolicy { attempts: 8, ..RetryPolicy::default() }
}
```

Builders that validate return `Result` from `build()`. Required arguments belong to `builder(...)`, not to setters, so a half-configured builder cannot be built.

## Extensible Types with non_exhaustive

`#[non_exhaustive]` on a public enum, struct, or variant lets you add variants and fields later without a major version bump. Outside the defining crate, matches need a wildcard arm and structs cannot be built with literals, so add the attribute when the type is introduced; adding it later is itself a breaking change.

```rust
#[non_exhaustive]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Compression {
    None,
    Gzip,
    Zstd,
}

#[non_exhaustive]
#[derive(Debug, Clone, Default)]
pub struct Options {
    pub compression: Option<Compression>,
    pub retries: u8,
}

impl Options {
    pub fn new() -> Self {
        Self::default()
    }
}
```

Inside the crate the attribute has no effect. Public error enums are the most common place for it.

## Async Functions in Traits

`async fn` in traits is stable since 1.75. Two limits shape designs: the returned future captures all in-scope lifetimes (borrowing patterns across the call may not be expressible), and a trait with `async fn` is not dyn-compatible without boxing. For `dyn` use, return `Pin<Box<dyn Future<Output = T> + Send + '_>>` explicitly or use the `async_trait` crate, which performs that boxing with a macro. Specify `Send` bounds on the future when tasks run on a multi-threaded runtime. Details of futures and cancellation are in [concurrency](concurrency.md#async-boundary).

## Common Mistakes

- Storing `&'a str` in a long-lived struct to avoid a `String` allocation, then fighting lifetimes through the whole codebase. Own the data at the boundary; borrow inside functions.
- `Rc<RefCell<T>>` as the default way to share state between components, instead of one owner and message passing or borrowed views.
- Public struct fields that later need an invariant; start private with accessors when the type is in a public API.
- A `bool` or `Option<bool>` parameter whose meaning is only visible at the definition; use a two-variant enum (C-CUSTOM-TYPE).
- `impl Into<String>` on a function that only reads the string; it forces callers with a `&str` to allocate.
- Panicking in `Drop`; a panic while unwinding aborts the process.
- Deriving `PartialOrd` on a type whose ordering is meaningless, then depending on it in sorts.
- Implementing `Deref` on a newtype to forward all methods, which also forwards the ones that break the invariant.

## Availability by Version

| Version | Addition |
|---|---|
| 1.80 | `LazyCell`, `LazyLock` |
| 1.82 | `use<..>` precise capturing on `impl Trait` returns; `Option::is_none_or` |
| 1.85 | Async closures and `AsyncFn` traits; edition 2024 capture and drop-order rules |
| 1.86 | Trait upcasting `&dyn Sub` to `&dyn Super`; `<[T]>::get_disjoint_mut` |
| 1.87 | `use<..>` in trait definitions |
| 1.88 | `let` chains (edition 2024 only); `Cell::update` |
| 1.95 | `if let` guards in `match` |

Per-release details live in [the versions index](../versions/index.md).

## Review Checklist

- Each value has one obvious owner; borrows do not outlive the call unless a struct lifetime is deliberate.
- Parameters are borrowed views (`&str`, `&[T]`, `&Path`) unless the function stores the value.
- Every `clone()` on a non-`Copy`, non-refcounted value has a reason; none exist only to satisfy the borrow checker.
- Invariants live in constructors of private-field types; downstream code takes the validated type.
- `RefCell` borrows and lock guards are scoped tightly; no `let _ = guard`.
- `Drop` implementations cannot fail or panic; fallible cleanup has an explicit method.
- Traits meant for trait objects are dyn-compatible; traits users must not implement are sealed.
- Public enums and structs that may grow carry `#[non_exhaustive]` from the first release.
