# Crate Compatibility and Releases

## Contents

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

Examples use stable APIs unless marked otherwise. Edition 2024 requires Rust 1.85; use edition 2021 and compatible APIs for older MSRVs. TOML snippets illustrate the indicated manifest sections. Naming, traits, conversions, and documentation of the public surface are in [API design](api-design.md); error types in [error types](error-types.md).

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
- Choose documented error variants or opaque accessors when callers need recovery. Dynamic errors and intentionally public dependency types can be valid, but convenience alone is not a public-API design. See [error types](error-types.md#design-the-failure-boundary).
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

- A `default` feature that turns on heavy dependencies users cannot opt out of without `default-features = false` and a long list of re-enabled features.
- Optional dependencies without `dep:`, exposing crate names as features that later cannot be removed.
- Bumping `rust-version` in a patch release without a stated policy.
- Returning a dependency's type from a public function without re-exporting the dependency.

## Availability by Version

| Version | Addition |
|---|---|
| 1.74 | `[lints]` and `[workspace.lints]` tables |
| 1.81 | `core::error::Error` for `no_std` error types |
| 1.84 | `resolver = "3"`; `rust-version`-aware dependency resolution |
| 1.85 | Edition 2024: new Cargo key names required; `default-features` inheritance rule |
| 1.90 | `cargo publish --workspace` |
| 1.91 | `build.build-dir`; `cargo publish` no longer leaves `.crate` files in `target/package` when `build-dir` is set |
| 1.99 | Edition 2024 members can turn off `default-features` inherited from `[workspace.dependencies]` |
| 1.100 | `[lints.cargo]` and `cargo::unused_dependencies` |

Per-release details live in [the versions index](../versions/index.md).
