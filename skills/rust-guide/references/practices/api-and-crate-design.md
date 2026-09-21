# API and Crate Design

## Contents

- [Naming Conventions](#naming-conventions)
- [Constructors, Getters, and Conversions](#constructors-getters-and-conversions)
- [Traits Every Public Type Should Consider](#traits-every-public-type-should-consider)
- [Conversion Traits](#conversion-traits)
- [Collections and Iterators in APIs](#collections-and-iterators-in-apis)
- [Documentation](#documentation)
- [SemVer: What Breaks and What Does Not](#semver-what-breaks-and-what-does-not)
- [Deprecating Without Breaking](#deprecating-without-breaking)
- [Cargo Features](#cargo-features)
- [Supporting no_std](#supporting-no_std)
- [Workspaces](#workspaces)
- [MSRV Policy](#msrv-policy)
- [Public Dependencies and Cargo.lock](#public-dependencies-and-cargolock)
- [Auto Traits Are Part of the API](#auto-traits-are-part-of-the-api)
- [Release Compatibility](#release-compatibility)
- [Common Mistakes](#common-mistakes)
- [Availability by Version](#availability-by-version)

Examples use stable APIs unless marked otherwise. Edition 2024 requires Rust 1.85; use edition 2021 and compatible APIs for older MSRVs. TOML snippets illustrate the indicated manifest sections. Internal type structure is in [ownership and type design](ownership-and-type-design.md); error types in [error handling](error-handling.md).

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
| `std::error::Error` | Error types | See [error handling](error-handling.md) |

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

## SemVer: What Breaks and What Does Not

Classify each change by its effect on existing consumers before choosing the version bump:

| Change | Class |
|---|---|
| Remove, rename, or move a public item without a re-export | Major |
| Add a private field to a struct whose fields were all public; add a public field to a struct without private fields | Major |
| Add a variant to an enum without `#[non_exhaustive]`; add a field to a variant | Major |
| Add a required (non-defaulted) trait item; change a trait item's signature | Major |
| Add an item that makes a trait dyn-incompatible | Major |
| Tighten a generic bound; add a function parameter; make an `impl Trait` return capture more generic parameters | Major |
| Stop supporting `no_std`; add `#[non_exhaustive]` to an existing all-public type; add `repr(packed)` or `repr(align)` | Major |
| Remove a Cargo feature, or remove a feature from another feature's list | Major |
| Add a public item; add a private field when private fields already exist; add a defaulted type parameter; loosen a bound | Minor |
| Make an `impl Trait` return capture fewer parameters; add `repr(C)`, `repr(<int>)`, or `repr(transparent)` to a default-repr type | Minor |
| Add a feature; add a dependency; introduce a new lint; change an `unsafe fn` to safe | Minor |
| Add a defaulted trait item (glob-import ambiguity risk); add a generic parameter to a function (turbofish callers) | Possibly breaking, usually shipped as minor |
| Remove an optional dependency that doubled as an implicit feature | Possibly breaking; avoid by using `dep:` syntax |
| Raise `rust-version` | Possibly breaking; Cargo says it "is assumed to be a minor incompatibility" |

Mitigations: `#[non_exhaustive]` on types introduced now, `#[deprecated]` plus re-exports for renames, sealed traits when downstream impls would block evolution, `dep:` feature syntax, `#[doc(hidden)]` for items that are public only for macros. Binaries have no SemVer rules for their code; version them by user-visible behavior.

## Deprecating Without Breaking

Keep the old name working for at least one minor release cycle, point at the replacement, and remove in the next major.

```rust
pub mod net {
    pub struct Listener {
        addr: String,
    }

    impl Listener {
        pub fn bind(addr: &str) -> Listener {
            Listener { addr: addr.to_owned() }
        }

        #[deprecated(since = "1.4.0", note = "use `bind`, which validates the address")]
        pub fn open(addr: &str) -> Listener {
            Listener::bind(addr)
        }

        pub fn addr(&self) -> &str {
            &self.addr
        }
    }
}

/// Old name kept as a deprecated alias; users see the note on every use.
#[deprecated(since = "1.4.0", note = "renamed to `net::Listener`; the alias goes away in 2.0")]
pub type TcpListener = net::Listener;
```

`#[deprecated]` applies to functions, methods, types, fields, variants, constants, and modules; a re-export via `pub use` does not carry its own deprecation, so alias a type with `pub type` or wrap a function. Document removed items in the changelog.

## Cargo Features

Design reusable features as additive capabilities because dependency feature requests can be unified. Avoid mutually exclusive features where possible; document and validate supported combinations when target/back-end constraints require them. Use dep: when a dependency name should not itself become a public feature. Treat changes to defaults as compatibility decisions.

```toml
[features]
default = ["std"]
std = ["alloc"]
tokio-runtime = ["std", "dep:tokio"]
alloc = []
serde = ["dep:serde"]
# A capability, not a crate name: users enable `metrics`, not `prometheus-client`.
metrics = ["dep:prometheus-client"]

[dependencies]
serde = { version = "1", optional = true, default-features = false, features = ["derive"] }
tokio = { version = "1", optional = true, features = ["rt"] }
prometheus-client = { version = "0.22", optional = true }
```

```rust
#[cfg(feature = "serde")]
mod serde_support {
    // impls that exist only when the feature is on
}

pub struct Limiter {
    per_second: u32,
}

impl Limiter {
    pub fn new(per_second: u32) -> Self {
        Limiter { per_second }
    }
}

#[cfg(feature = "std")]
impl Limiter {
    /// Available only with `std`: uses `std::time::Instant`.
    pub fn wait(&self) -> std::time::Duration {
        std::time::Duration::from_secs(1) / self.per_second.max(1)
    }
}
```

Check documented no-default, full, target-specific, and isolated-package combinations as applicable; one workspace-wide all-features build can hide missing feature declarations. Clippy `negative_feature_names` (cargo group) flags `no-std`-style names; name the positive capability.

## Supporting no_std

For a library promising optional std, gate it behind a feature, use core/alloc as appropriate, and keep compatible APIs where practical. A core-only crate need not introduce a default std feature. See [embedded and no_std](embedded-and-no-std.md) for target, allocator, interrupt, and hardware boundaries. `core::error::Error` (1.81) lets error types implement `Error` without `std`.

```rust
#![cfg_attr(not(feature = "std"), no_std)]

#[cfg(feature = "alloc")]
extern crate alloc;

use core::fmt;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Celsius(i32);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct OutOfRange;

impl fmt::Display for OutOfRange {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("temperature out of range")
    }
}

impl core::error::Error for OutOfRange {}

impl Celsius {
    pub const fn degrees(self) -> i32 { self.0 }

    pub const fn new(degrees: i32) -> Result<Self, OutOfRange> {
        if degrees < -273 { Err(OutOfRange) } else { Ok(Celsius(degrees)) }
    }
}

#[cfg(feature = "std")]
pub fn read_sensor(path: &std::path::Path) -> std::io::Result<Celsius> {
    let text = std::fs::read_to_string(path)?;
    let degrees = text.trim().parse::<i32>().map_err(std::io::Error::other)?;
    Celsius::new(degrees).map_err(std::io::Error::other)
}
```

Build the `no_std` configuration in CI with a target that has no `std`, for example `cargo check --no-default-features --target thumbv7em-none-eabi`, because `cargo check --no-default-features` on a hosted target does not catch accidental `std` use.

## Workspaces

Use [workspaces and monorepos](workspaces-and-monorepos.md) for root/member configuration, shared or independent versioning, resolver/MSRV behavior, feature unification, publishing, and affected-package validation. Use [module and crate boundaries](modules-and-crate-boundaries.md) to decide which packages should exist.

A workspace coordinates packages; it does not require identical versions, features, or targets. Settings inherited with workspace = true are opt-in. Crate splitting has build and public-API costs, and a crate boundary does not universally prevent inlining without LTO.

## MSRV Policy

- Declare `rust-version` in every published manifest. Cargo reports a clear error on older toolchains, `cargo add` selects compatible dependency versions, and resolver 3 (Cargo 1.84+) prefers MSRV-compatible dependencies but can fall back to incompatible versions when requirements leave no compatible solution.
- Publish the policy: which release you support and when you bump (for example "the latest stable minus two", or "supported for 6 months"). Cargo treats a bump as a minor change, but users with a lower toolchain still get stuck, so a stated policy prevents surprises.
- Verify it: a CI job on the MSRV toolchain with `cargo check --locked --all-features` and `cargo test`, plus `msrv = "1.85"` in `clippy.toml` so Clippy does not suggest newer APIs.
- Keep the lockfile format and selected dependencies usable by the MSRV. A locked build cannot silently replace dependencies with older compatible ones; separately assess the locked graph and fresh resolution.

## Public Dependencies and Cargo.lock

- Dependency types in public signatures create compatibility obligations. Re-export selected types when it helps callers name the intended version; do not automatically re-export entire dependency crates. Evaluate a dependency upgrade by its impact on the public contract.
- Choose documented error variants or opaque accessors when callers need recovery. Dynamic errors and intentionally public dependency types can be valid, but convenience alone is not a public-API design. See [error handling](error-handling.md#design-the-failure-boundary).
- `Cargo.lock`: `cargo new` tracks it for libraries and binaries alike. Commit it so CI, `git bisect`, and the MSRV job are reproducible. It does not affect users of a library (only `Cargo.toml` does), and `cargo install` ignores it unless `--locked` is passed. Use a scheduled CI job with `cargo update` to catch breakage from newer dependency versions.

## Auto Traits Are Part of the API

`Send`, `Sync`, `Unpin`, and `UnwindSafe` are inferred from fields. Changing fields can alter auto traits: Rc/raw pointers can remove Send and Sync, while `RefCell<T>` is not `Sync` but can be `Send` when `T: Send`. Losing a promised bound breaks consumers that rely on it. Pin the guarantee with a test.

```rust
use std::sync::{Arc, Mutex};

pub struct Client {
    connections: Arc<Mutex<Vec<String>>>,
}

#[cfg(test)]
mod tests {
    #[test]
    fn client_is_send_and_sync() {
        fn assert_send_sync<T: Send + Sync>() {}
        assert_send_sync::<super::Client>();
    }
}
```

The same applies to `impl Trait` return types: the concrete type's auto traits leak to callers, so a change from `Vec::into_iter` to an `Rc`-based iterator is a breaking change even though the signature is unchanged.

## Release Compatibility

A library's contract includes documented behavior, public types and trait implementations, supported feature/target combinations, and its MSRV policy. Building the whole workspace on one recent compiler does not exercise all those promises. Documentation examples and isolated consumer builds can reveal different compatibility problems.

Package contents matter independently of local compilation: `cargo package --list` shows the distribution contents, and `cargo publish --dry-run` exercises packaging without publishing. Private implementation changes, new variants, deprecations, re-exports, and dependency types crossing the API have different SemVer implications. Use the [SemVer rules](#semver-what-breaks-and-what-does-not) and choose non_exhaustive or opaque types according to the intended extension policy.

## Common Mistakes

- `get_` prefixes on getters and `into_` methods that take `&self`; Clippy `wrong_self_convention` (style) checks the receiver against the prefix.
- Missing `Debug` on a public type; users cannot add it (`missing_debug_implementations` rustc lint, allow by default, enforces it).
- Exposing `Vec<T>` fields as `pub` and later needing an invariant; start with private fields and accessors.
- Implementing `Into` instead of `From`, which loses the `From` impl.
- A `default` feature that turns on heavy dependencies users cannot opt out of without `default-features = false` and a long list of re-enabled features.
- Optional dependencies without `dep:`, exposing crate names as features that later cannot be removed.
- Bumping `rust-version` in a patch release without a stated policy.
- Returning a dependency's type from a public function without re-exporting the dependency.

## Availability by Version

| Version | Addition |
|---|---|
| 1.74 | `[lints]` and `[workspace.lints]` tables |
| 1.81 | `core::error::Error` for `no_std` error types |
| 1.82 | `use<..>` precise capturing controls what `impl Trait` returns capture (a SemVer-visible property) |
| 1.84 | `resolver = "3"`; `rust-version`-aware dependency resolution |
| 1.85 | Edition 2024: `impl Trait` captures all in-scope lifetimes by default; new Cargo key names required; `default-features` inheritance rule |
| 1.86 | Trait upcasting lets you delete `as_super()`-style methods (deleting them is still a major change) |
| 1.87 | `use<..>` in trait definitions |
| 1.90 | `cargo publish --workspace` |
| 1.91 | `build.build-dir`; `cargo publish` no longer leaves `.crate` files in `target/package` when `build-dir` is set |

Per-release details live in [the versions index](../versions/index.md).
