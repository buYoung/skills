---
name: rust-guide
description: Use for explaining, designing, implementing, reviewing, refactoring, optimizing, migrating, or diagnosing Rust code and Cargo projects on stable Rust 1.80+ whenever Rust-specific engineering judgment is needed: ownership and type design, collection selection, error handling, public API and crate design, threads/sync/atomics, performance and Cargo/rustc build configuration, unsafe/FFI soundness, Clippy-based review, and Rust release or Edition 2024 migration. Use it whenever the user asks which type, collection, lock, or profile setting to use, whether code is idiomatic, why Rust code is slow, or what changed since a given Rust version, even without saying "best practice". Not a Rust learning tutorial; excludes framework- or runtime-specific APIs (specific async runtimes, web frameworks, embedded HALs), nightly-only features, toolchains below 1.80, and non-Rust build systems.
license: MIT
---

# Rust Guide

Engineering advisor for production Rust on stable toolchains 1.80 and later, editions 2021 and 2024. It answers what to use, why, when to choose differently, and what the safety or performance trade-off is. It is not a tutorial: explain language semantics only as far as the decision in front of the user needs.

## Establish Evidence First

Collect what the project already fixes before recommending anything:

- Toolchain: `rust-toolchain.toml`, `rustup show active-toolchain`, `rustc --version`, CI toolchain pins.
- Manifest: `edition`, `rust-version` (MSRV), `resolver`, `[profile.*]`, `[lints]`, `[features]`, workspace layout, `Cargo.lock` version.
- Constraints: `std` vs `no_std`, target triples, FFI boundaries, async runtime in use, custom allocator.
- Existing diagnostics: `cargo build`, `cargo clippy`, test failures, benchmarks, profiles.

When facts are missing, continue with version-independent guidance and name the choice that depends on the missing fact. Do not assume the newest stable. Do not recommend an API without stating its stabilizing version when the project's MSRV could be below it. Treat nightly-only language and library features as out of scope unless the project already pins nightly; nightly-only verification tools such as Miri remain usable as checks.

## Route

Start with the closest reference; read a second one only when the task crosses topics. Each reference is self-contained: the rules, tables, and examples (which compile on stable Rust with edition 2024) are in the file; source URLs and verification notes are kept out of the skill text in `updates/`. The `versions/` directory has one file per release that carries an official deprecation or migration instruction; releases without one appear only in its index.

| Task signal | Read |
|---|---|
| `Vec`, `VecDeque`, `HashMap`, `BTreeMap`, `BinaryHeap` choice, capacity, hashing, iteration order | [collections](references/practices/collections.md) |
| Ownership hierarchy, owned vs borrowed types, `Rc`/`Arc`/indices, newtype, typestate, enum vs trait vs generic vs `dyn`, `clone` pressure, interior mutability | [ownership and type design](references/practices/ownership-and-type-design.md) |
| `Result`/`Option`/panic policy, error types for libraries vs applications, `?` conversions, reporting | [error handling](references/practices/error-handling.md) |
| Public API shape, naming, conversion traits, sealed traits, SemVer, features, MSRV policy, docs | [API and crate design](references/practices/api-and-crate-design.md) |
| Threads, channels, `Send`/`Sync`, `Mutex`/`RwLock`/`Condvar`, atomics and ordering, `Arc<Mutex<T>>` pressure, async boundary | [concurrency](references/practices/concurrency.md) |
| "Why is it slow", allocation, cloning, iterators, layout, profiling, any performance claim | [performance](references/practices/performance.md) |
| Release profile, LTO, `codegen-units`, `panic`, `strip`, PGO, `target-cpu`, binary size, compile time | [build configuration](references/practices/build-configuration.md) |
| `unsafe`, raw pointers, aliasing, `MaybeUninit`, manual `Send`/`Sync`, FFI, Miri | [unsafe and FFI](references/practices/unsafe-and-ffi.md) |
| Code review, Clippy groups, `[lints]`, `#[expect]`, lint policy for CI | [lints and review](references/practices/lints-and-review.md) |
| Moving a crate or workspace to edition 2024 | [Rust 1.85 and edition 2024](references/versions/1.85.md) |
| "What changed since 1.NN", deprecated or renamed APIs, new lints, behavior changes, toolchain upgrade planning | [versions index](references/versions/index.md), then the per-version files it lists for the range |

## Source Authority and Evidence Labels

Different questions have different authorities. Resolve conflicts upward and attach the label when stating a recommendation, so the user can tell a guarantee from an opinion.

| Question | Authority | Label |
|---|---|---|
| What the language or a std type guarantees | Rust Reference, std docs, Rustonomicon for `unsafe`, Edition Guide, release notes | `Rust guarantees`, `std documents` |
| How Cargo and rustc behave | Cargo Book, rustc Book | `Cargo documents`, `rustc documents` |
| Official ecosystem convention | Rust API Guidelines, Clippy, rustfmt style guide | `official guideline` |
| Recommended design under trade-offs | Google Comprehensive Rust (Idiomatic Rust, Concurrency), Rust Performance Book, Rust Atomics and Locks | Name the source: `Google recommends`, `Performance Book suggests`, `Atomics and Locks` |
| Community idiom | Rust Design Patterns (unofficial) | `community pattern` |
| Performance outcome on this workload | A measurement on this workload only | `needs benchmark` |

"Best practice" without one of these labels is not an answer. `RwLock` is a candidate when readers dominate; it is not "faster than `Mutex`" until measured, because `std` documents that its scheduling policy is platform-dependent.

## Decision Method

1. Semantics before performance: choose the type whose guarantees match the requirement (ordering, uniqueness, `Ord`/`Hash` availability, sharing across threads), then optimize inside that choice.
2. Ownership structure before synchronization: recurring `Arc<Mutex<T>>`, `Rc<RefCell<T>>`, or `clone()` to satisfy the borrow checker is a signal to redesign who owns what, not to add more locking.
3. Measure before optimizing: confirm a release build, profile the hot path, change algorithm or data structure first, then allocation, then layout, then micro-optimizations, then compiler flags.
4. Check Clippy before inventing a rule: if a lint already covers the pattern, cite it by name and group.
5. Version-gate every API: state the stabilizing version for anything newer than 1.80, and check the edition when a rule differs between 2021 and 2024.
6. Smallest reversible change: one design or configuration change at a time, verified against the same inputs.

## Boundary

The guide owns Rust language, `std`, Cargo, rustc, and Clippy decisions, including async fundamentals in `std` (`Future`, `Pin`, `IntoFuture`, `AsyncFn`) and their `Send`/blocking boundaries. Specific async runtimes, web frameworks, ORMs, embedded HALs, and other crates' APIs stay with that crate's own documentation; use this guide for the Rust-level judgment around them and say when a decision depends on the runtime. Nightly-only features and toolchains below 1.80 are out of scope; when a project pins one, say so and continue with version-independent guidance.

## Response Contract

Adapt to the request: give the decision, its evidence label, and the alternative that becomes correct when the stated assumption changes. Report changes or findings with the exact identifiers involved. Distinguish performed verification (`cargo check`, `cargo clippy`, `cargo test`, benchmarks, Miri) from remaining runtime risk. Claim a performance improvement only from a comparable before/after measurement. Never report a blocked, failed, or unrun check as passed.
