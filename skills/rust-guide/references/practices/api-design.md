# API Design

## Contents

- [Naming Conventions](#naming-conventions)
- [Constructors, Getters, and Conversions](#constructors-getters-and-conversions)
- [Traits Every Public Type Should Consider](#traits-every-public-type-should-consider)
- [Conversion Traits](#conversion-traits)
- [Collections and Iterators in APIs](#collections-and-iterators-in-apis)
- [Documentation](#documentation)
- [Common Mistakes](#common-mistakes)
- [Availability by Version](#availability-by-version)

Examples use stable APIs unless marked otherwise. Edition 2024 requires Rust 1.85; use edition 2021 and compatible APIs for older MSRVs. TOML snippets illustrate the indicated manifest sections. Internal type structure is in [type design](type-design.md); error types in [error types](error-types.md); SemVer, features, and MSRV in [crate compatibility](crate-compatibility.md).

## Naming Conventions

Follow standard-library naming patterns so a name communicates ownership, mutability, and conversion behavior.

| Item | Convention | Examples |
|---|---|---|
| Types, traits, enum variants | `UpperCamelCase` | `HashMap`, `IntoIterator`, `Ordering::Less` |
| Functions, methods, modules, locals | `snake_case` | `read_to_string`, `std::sync::mpsc` |
| Constants and statics | `SCREAMING_SNAKE_CASE` | `MAX_LEN`, `EPSILON` |
| Acronyms | Treated as one word | `Uuid`, `HttpClient`, `TcpStream`, not `UUID` or `HTTPClient` |
| Free borrow-to-borrow conversion | `as_` | `as_str`, `as_bytes`, `as_path` |
| Expensive or owning conversion | `to_` | `to_string`, `to_vec`, `to_lowercase` |
| Consuming conversion | `into_` | `into_inner`, `into_boxed_slice`, `into_iter` |
| Getter | field name, no `get_`; `_mut` for the mutable pair | `len()`, `capacity()`, `first_mut()` |
| Iterator producers | `iter`, `iter_mut`, `into_iter`, plus domain names returning iterators | `chars()`, `lines()`, `keys()` |
| Iterator types | Named after the producing method | `IntoIter`, `Chars`, `Keys` |
| Fallible constructor | `try_` prefix or `from_*` returning `Result` | `try_from`, `from_str` |
| Feature names | No placeholder words | `std`, `serde`, not `use-std`, `with-serde` |
| Word order | Consistent verb-object-error order | `ParseIntError`, `TryFromIntError`, `RecvTimeoutError` |
| Booleans | `is_`, `has_`, `can_`, `should_` for predicates | `is_empty`, `has_children` |

## Constructors, Getters, and Conversions

Constructors are inherent associated functions; `new` takes the required inputs, `with_*`/`from_*` name alternatives, `default()` comes from `Default`.

```rust
use std::path::{Path, PathBuf};

pub struct Workspace {
    root: PathBuf,
    members: Vec<String>,
}

impl Workspace {
    /// Required inputs go through `new`; `impl Into<PathBuf>` accepts `&str`, `String`, `PathBuf`.
    pub fn new(root: impl Into<PathBuf>) -> Self {
        Workspace { root: root.into(), members: Vec::new() }
    }

    /// Alternative constructor with a descriptive prefix.
    pub fn with_members(root: impl Into<PathBuf>, members: Vec<String>) -> Self {
        Workspace { root: root.into(), members }
    }

    /// Getter: field name, borrowed view, no `get_` prefix.
    pub fn root(&self) -> &Path {
        &self.root
    }

    /// `as_`: free conversion from one borrow to another.
    pub fn as_path(&self) -> &Path {
        &self.root
    }

    /// `to_`: allocates a new owned value.
    pub fn to_manifest_path(&self) -> PathBuf {
        self.root.join("Cargo.toml")
    }

    /// `into_`: consumes `self` and releases the owned value.
    pub fn into_root(self) -> PathBuf {
        self.root
    }

    /// Iterator-returning method: the concrete iterator type stays private.
    pub fn members(&self) -> impl Iterator<Item = &str> + '_ {
        self.members.iter().map(String::as_str)
    }

    /// Mutable access with the `_mut` suffix.
    pub fn members_mut(&mut self) -> &mut Vec<String> {
        &mut self.members
    }
}
```

For multiple return values, prefer a tuple or struct. Mutating caller-owned data is a different contract: an output buffer can support reuse, fixed-capacity storage, or allocation control. See [buffer reuse](memory-and-allocation.md#reuse-without-unbounded-retention) and [embedded buffers](embedded-and-no-std.md#keep-the-portable-core-honest). Functions with a clear receiver are methods; functions that produce a value from nothing related to an instance are associated functions.

## Traits Every Public Type Should Consider

Users compose your type with the standard library and with other crates through traits; a missing `Debug` or `Clone` cannot be added from outside (orphan rule). Implement eagerly where the semantics fit.

| Trait | Implement when | Note |
|---|---|---|
| `Debug` | Always for public types | Derive; hand-write to hide secrets. Never empty output |
| `Clone` | The value can be duplicated meaningfully | Derive; skip for unique handles (sockets, guards) |
| `Copy` | Small plain data (a few words) with `Clone` | Adding `Copy` later is compatible; removing it is breaking |
| `PartialEq`, `Eq` | Values can be compared for equality | `Eq` only for total equality (not floats) |
| `PartialOrd`, `Ord` | The order is meaningful | Keep consistent with `PartialEq` |
| `Hash` | Used as a map key | Must agree with `Eq` |
| `Default` | A sensible zero configuration exists | Enables `..Default::default()` |
| `Display` | Users show the value | Human text, no debug syntax |
| `FromStr` | The value has a textual form | Pairs with `Display` |
| `From`/`TryFrom` | Lossless or checked conversions exist | Gives `Into`/`TryInto` for free |
| `AsRef<T>`/`Borrow<T>` | Cheap view of an inner type | `Borrow` requires equal `Eq`/`Hash` behavior |
| `Send`, `Sync` | Automatically, unless a field prevents it | Part of the API; see below |
| `serde::Serialize`/`Deserialize` | Data types | Behind a `serde` feature |
| `std::error::Error` | Error types | See [error types](error-types.md) |

```rust
use std::fmt;
use std::str::FromStr;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord, Default)]
pub struct Percent(u8);

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParsePercentError {
    NotANumber,
    OutOfRange(u16),
}

impl fmt::Display for ParsePercentError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ParsePercentError::NotANumber => f.write_str("expected a number"),
            ParsePercentError::OutOfRange(v) => write!(f, "{v} is not within 0..=100"),
        }
    }
}

impl std::error::Error for ParsePercentError {}

impl TryFrom<u16> for Percent {
    type Error = ParsePercentError;
    fn try_from(value: u16) -> Result<Self, Self::Error> {
        u8::try_from(value)
            .ok()
            .filter(|v| *v <= 100)
            .map(Percent)
            .ok_or(ParsePercentError::OutOfRange(value))
    }
}

impl From<Percent> for u8 {
    fn from(percent: Percent) -> u8 {
        percent.0
    }
}

impl fmt::Display for Percent {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}%", self.0)
    }
}

impl FromStr for Percent {
    type Err = ParsePercentError;
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let digits = s.trim().strip_suffix('%').unwrap_or(s.trim());
        let value: u16 = digits.parse().map_err(|_| ParsePercentError::NotANumber)?;
        Percent::try_from(value)
    }
}
```

Only smart pointers implement `Deref`; operator overloads follow the arithmetic meaning users expect.

## Conversion Traits

Implement `From<A> for B` for infallible, meaning-preserving conversions and `TryFrom` for checked ones. From supplies Into through a blanket implementation; generic callers can accept Into to support either implementation path. Keep the implementation with the owned domain type: `impl From<Percent> for u8` lives with `Percent`, not with `u8`. `AsRef<str>`/`AsRef<Path>` in argument position accepts borrowed views without requiring allocation; `impl Into<String>` is useful when the function needs an owned string. Prefer a named method when several conversions have different meanings.

## Collections and Iterators in APIs

A collection type implements `FromIterator` and `Extend`, provides `iter()`/`iter_mut()`/`into_iter()`, and implements `IntoIterator` for `&T`, `&mut T`, and `T` so it works in `for` loops.

```rust
pub struct Playlist {
    tracks: Vec<String>,
}

impl Playlist {
    pub fn iter(&self) -> std::slice::Iter<'_, String> {
        self.tracks.iter()
    }
}

impl<'a> IntoIterator for &'a Playlist {
    type Item = &'a String;
    type IntoIter = std::slice::Iter<'a, String>;
    fn into_iter(self) -> Self::IntoIter {
        self.tracks.iter()
    }
}

impl IntoIterator for Playlist {
    type Item = String;
    type IntoIter = std::vec::IntoIter<String>;
    fn into_iter(self) -> Self::IntoIter {
        self.tracks.into_iter()
    }
}

impl FromIterator<String> for Playlist {
    fn from_iter<I: IntoIterator<Item = String>>(iter: I) -> Self {
        Playlist { tracks: iter.into_iter().collect() }
    }
}

impl Extend<String> for Playlist {
    fn extend<I: IntoIterator<Item = String>>(&mut self, iter: I) {
        self.tracks.extend(iter)
    }
}
```

Functions that produce sequences return `impl Iterator<Item = T>` when callers usually iterate, and `Vec<T>` when they usually index or keep the data. Accept `impl IntoIterator<Item = T>` for inputs so callers can pass arrays, vectors, or iterator chains. Expose intermediate results instead of recomputing: `parse()` that also validated should return the validated structure, not a `bool`.

## Documentation

Every public item gets a doc comment; `#![warn(missing_docs)]` in `lib.rs` enforces it. The crate root documents purpose, a quick-start example, and feature flags. Item docs follow a fixed shape: one summary sentence, details, then `# Examples`, `# Errors`, `# Panics`, `# Safety` as applicable. Examples use `?` rather than `unwrap()`. Intra-doc links (`[`Type`]`, `[`module::function`]`) are checked by rustdoc. Hide implementation details that must be `pub` for macros with `#[doc(hidden)]`.

Google's course adds the reader's perspective: write "what and why, not how and where"; a doc comment that restates the signature ("Returns the name") adds nothing. Library docs describe contracts; application docs describe operation.

```toml
[package]
name = "rate-limiter"
version = "0.3.1"
edition = "2024"
rust-version = "1.85"
description = "Token-bucket rate limiting for sync and async callers"
license = "MIT OR Apache-2.0"
repository = "https://github.com/example/rate-limiter"
documentation = "https://docs.rs/rate-limiter"
readme = "README.md"
keywords = ["rate-limit", "throttle"]
categories = ["asynchronous", "network-programming"]

[package.metadata.docs.rs]
all-features = true
```

`cargo doc --no-deps` with `RUSTDOCFLAGS="-D warnings"` fails on broken links. In edition 2024 rustdoc compiles doctests together; a doctest that depends on `std::panic::Location` line numbers or `std::any::type_name` output needs the `standalone_crate` attribute.

## Common Mistakes

- `get_` prefixes on getters and `into_` methods that take `&self`; Clippy `wrong_self_convention` (style) checks the receiver against the prefix.
- Missing `Debug` on a public type; users cannot add it (`missing_debug_implementations` rustc lint, allow by default, enforces it).
- Exposing `Vec<T>` fields as `pub` and later needing an invariant; start with private fields and accessors.
- Implementing `Into` instead of `From`, which loses the `From` impl.

## Availability by Version

| Version | Addition |
|---|---|
| 1.82 | `use<..>` precise capturing controls what `impl Trait` returns capture (a SemVer-visible property) |
| 1.85 | Edition 2024: `impl Trait` captures all in-scope lifetimes by default |
| 1.86 | Trait upcasting lets you delete `as_super()`-style methods (deleting them is still a major change) |
| 1.87 | `use<..>` in trait definitions |
| 1.100 | `Infallible` is an alias of `!` |

Per-release details live in [the versions index](../versions/index.md).
