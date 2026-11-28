# Type Design

## Contents

- [Newtypes](#newtypes)
- [Enforce Invariants at the Boundary](#enforce-invariants-at-the-boundary)
- [Typestate](#typestate)
- [Composition, Not Deref Inheritance](#composition-not-deref-inheritance)
- [Builders and Optional Configuration](#builders-and-optional-configuration)
- [Extensible Types with non_exhaustive](#extensible-types-with-non_exhaustive)
- [Common Mistakes](#common-mistakes)
- [Availability by Version](#availability-by-version)
- [Practical Boundaries](#practical-boundaries)

Examples use stable APIs unless marked otherwise; see [compatibility](../../SKILL.md#compatibility). Ownership of the stored data is in [ownership and borrowing](ownership-and-borrowing.md); trait-based interfaces in [traits and dispatch](traits-and-dispatch.md); public-surface rules in [API design](api-design.md).

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

Derive `Clone`, `Copy` (for small values), `PartialEq`, `Eq`, `Hash`, `PartialOrd`, `Ord`, and `Debug` when the wrapped type has them and the semantics carry over; implement `Display` yourself. Do not derive `PartialOrd`/`Ord` for ids that have no meaningful order, and do not implement `Deref` to the inner type: implicit access to the inner API can bypass the wrapper's intended contract. Expose `get()`/`into_inner()` instead. Keep the field private when the type carries an invariant.

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

Typestate suits a small, fixed set of phases decided at compile time (builder stages, connection handshakes, request lifecycles). When phases are decided by runtime data, or the state set is large, use a state `enum` and return `Result` for invalid transitions. Runtime transitions need explicit validation because their legal sequence is not encoded in the type.

## Composition, Not Deref Inheritance

Rust has no struct inheritance. Implementing `Deref` to a field to "inherit" its methods is an anti-pattern: every method of the inner type leaks into the outer type's API, method resolution becomes surprising. Deref is most predictable for pointer-like access rather than domain inheritance. Compose and delegate the operations that make sense.

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

## Builders and Optional Configuration

For a type with several optional settings or multiple construction paths, a builder keeps the constructor signature stable and readable. For a few fields with sensible defaults, `Default` plus struct update syntax is enough.

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

## Common Mistakes

- Public struct fields that later need an invariant; start private with accessors when the type is in a public API.
- A `bool` or `Option<bool>` parameter whose meaning is only visible at the definition; use a two-variant enum.
- Deriving `PartialOrd` on a type whose ordering is meaningless, then depending on it in sorts.
- Implementing `Deref` on a newtype to forward all methods, which also forwards the ones that break the invariant.

## Availability by Version

| Version | Addition |
|---|---|
| 1.82 | `Option::is_none_or` |
| 1.100 | The never type `!` can be named anywhere and `Infallible` aliases it; never-type fallback is `!` in every edition |

Per-release details live in [the versions index](../versions/index.md).

## Practical Boundaries

Constructors and private fields can preserve invariants, while newtypes and typestate make them visible in APIs. Sealed traits and non_exhaustive types address specific extension policies rather than being mandatory on every public type.
