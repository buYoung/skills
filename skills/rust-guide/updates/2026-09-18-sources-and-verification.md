# Sources and Verification Record (2026-09-18)

Maintenance material for `rust-guide`. It is not loaded when the skill runs; it records where each reference's content came from and how it was verified, so the next Rust release can be folded in without re-deriving everything.

## Verification Performed

- Every fenced Rust example in `references/` (81 blocks) was compiled with `rustc 1.95.0` (`--edition 2024`, `--emit=metadata`); examples marked `rust,deps` were checked in a scratch crate with `thiserror` 2.0.20, `anyhow` 1.0.104, `rayon` 1.12.0, `crossbeam-channel` 0.5.17, `tokio` 1.53.1 (`full`), `arc-swap` 1.9.2, `dashmap` 6.2.1, and `parking_lot` 0.12.5; examples marked `rust,ignore` (mimalloc, criterion, loom) were not compiled.
- Clippy lint groups and default levels in `lints-and-review.md`, `performance.md`, `concurrency.md`, and `unsafe-and-ffi.md` come from `cargo clippy -- -W help` on Clippy 0.1.95; the `clippy.toml` keys and `#[expect]` examples were executed against that Clippy.
- Release facts in `references/versions/` were taken from the release announcements and cross-checked against `RELEASES.md` in `rust-lang/rust` (fetched 2026-09-18); the `mismatched_lifetime_syntaxes` example was reproduced with the local compiler.
- Latest stable at the time of writing: 1.98.1 (2026-09-03); next scheduled: 1.99.0 (2026-10-01).

## Re-verification Procedure for a New Release

1. Read the release announcement and the version's section of `RELEASES.md` (including Compatibility Notes).
2. Add a file under `references/versions/` only when the release contains an official deprecation, removal, rename, or migration instruction; otherwise add an index row marked as having no such guidance.
3. Update the `Availability by Version` tables in the affected practice references and any `since` versions in the text.
4. Re-run `cargo clippy -- -W help` on the new toolchain and refresh the group placements in `lints-and-review.md`.
5. Recompile every Rust block (extract fenced blocks tagged `rust`/`rust,deps` and build with `--edition 2024`) on the new toolchain.

## Sources by Document

### `references/practices/api-and-crate-design.md`

[Rust API Guidelines](https://rust-lang.github.io/api-guidelines/checklist.html), [Cargo SemVer compatibility](https://doc.rust-lang.org/cargo/reference/semver.html), [Cargo features](https://doc.rust-lang.org/cargo/reference/features.html), [Cargo workspaces](https://doc.rust-lang.org/cargo/reference/workspaces.html), [Cargo `rust-version`](https://doc.rust-lang.org/cargo/reference/rust-version.html), [Cargo resolver versions](https://doc.rust-lang.org/cargo/reference/resolver.html#resolver-versions), [Cargo FAQ: Cargo.lock](https://doc.rust-lang.org/cargo/faq.html#why-have-cargolock-in-version-control), [Reference: `#[deprecated]`](https://doc.rust-lang.org/reference/attributes/diagnostics.html#the-deprecated-attribute), [Comprehensive Rust: Foundations of API Design](https://google.github.io/comprehensive-rust/idiomatic/foundations-api-design.html), [Rust Design Patterns: Prefer small crates](https://rust-unofficial.github.io/patterns/patterns/structural/small-crates.html), [Edition Guide: Cargo changes](https://doc.rust-lang.org/edition-guide/rust-2024/cargo-inherited-default-features.html).

### `references/practices/build-configuration.md`

[Cargo profiles](https://doc.rust-lang.org/cargo/reference/profiles.html), [Cargo configuration](https://doc.rust-lang.org/cargo/reference/config.html), [rustc codegen options](https://doc.rust-lang.org/rustc/codegen-options/index.html), [rustc profile-guided optimization](https://doc.rust-lang.org/rustc/profile-guided-optimization.html), [rustc linker-plugin LTO](https://doc.rust-lang.org/rustc/linker-plugin-lto.html), [Rust Performance Book: Build Configuration](https://nnethercote.github.io/perf-book/build-configuration.html), [RELEASES.md](https://github.com/rust-lang/rust/blob/master/RELEASES.md) (1.77.0, 1.77.2, 1.88.0, 1.90.0, 1.91.0, 1.92.0, 1.97.0), [Rust Design Patterns: `#![deny(warnings)]`](https://rust-unofficial.github.io/patterns/anti_patterns/deny-warnings.html).

### `references/practices/collections.md`

[std::collections](https://doc.rust-lang.org/std/collections/index.html), [HashMap](https://doc.rust-lang.org/std/collections/struct.HashMap.html), [BTreeMap](https://doc.rust-lang.org/std/collections/struct.BTreeMap.html), [BinaryHeap](https://doc.rust-lang.org/std/collections/struct.BinaryHeap.html), [Vec](https://doc.rust-lang.org/std/vec/struct.Vec.html), [std::hash](https://doc.rust-lang.org/std/hash/index.html), [Rust Performance Book: Hashing](https://nnethercote.github.io/perf-book/hashing.html), [Heap Allocations](https://nnethercote.github.io/perf-book/heap-allocations.html), [Reference: behavior not considered unsafe](https://doc.rust-lang.org/reference/behavior-not-considered-unsafe.html).

### `references/practices/concurrency.md`

[std::sync](https://doc.rust-lang.org/std/sync/index.html), [Mutex](https://doc.rust-lang.org/std/sync/struct.Mutex.html), [RwLock](https://doc.rust-lang.org/std/sync/struct.RwLock.html), [Condvar](https://doc.rust-lang.org/std/sync/struct.Condvar.html), [mpsc](https://doc.rust-lang.org/std/sync/mpsc/index.html), [OnceLock](https://doc.rust-lang.org/std/sync/struct.OnceLock.html), [LazyLock](https://doc.rust-lang.org/std/sync/struct.LazyLock.html), [std::thread](https://doc.rust-lang.org/std/thread/index.html), [std::sync::atomic](https://doc.rust-lang.org/std/sync/atomic/index.html), [std::pin](https://doc.rust-lang.org/std/pin/index.html), [Comprehensive Rust: Concurrency](https://google.github.io/comprehensive-rust/concurrency/welcome.html) (threads, channels, Send/Sync examples, shared state, async runtimes, blocking the executor, cancellation, async traits), [Rust Atomics and Locks: Memory Ordering](https://marabos.nl/atomics/memory-ordering.html), [Rustonomicon: Send and Sync](https://doc.rust-lang.org/nomicon/send-and-sync.html), [Reference: behavior not considered unsafe](https://doc.rust-lang.org/reference/behavior-not-considered-unsafe.html), [Performance Book: Standard Library Types](https://nnethercote.github.io/perf-book/standard-library-types.html).

### `references/practices/error-handling.md`

[std::error::Error](https://doc.rust-lang.org/std/error/trait.Error.html), [core::error](https://doc.rust-lang.org/core/error/index.html), [Result](https://doc.rust-lang.org/std/result/enum.Result.html), [Option](https://doc.rust-lang.org/std/option/enum.Option.html), [std::io::ErrorKind](https://doc.rust-lang.org/std/io/enum.ErrorKind.html), [std::process::ExitCode](https://doc.rust-lang.org/std/process/struct.ExitCode.html), [Comprehensive Rust: Error Handling](https://google.github.io/comprehensive-rust/error-handling/result.html) (`error.md`, `thiserror.md`, `anyhow.md`), [Rust API Guidelines: C-GOOD-ERR, C-FAILURE, C-QUESTION-MARK](https://rust-lang.github.io/api-guidelines/checklist.html), [Cargo SemVer compatibility](https://doc.rust-lang.org/cargo/reference/semver.html), [Rustonomicon: FFI](https://doc.rust-lang.org/nomicon/ffi.html), [thiserror](https://docs.rs/thiserror), [anyhow](https://docs.rs/anyhow).

### `references/practices/lints-and-review.md`

[Clippy book](https://doc.rust-lang.org/clippy/) (lint groups, [configuration](https://doc.rust-lang.org/clippy/configuration.html), [continuous integration](https://doc.rust-lang.org/clippy/continuous_integration/index.html)), [Clippy lint list](https://rust-lang.github.io/rust-clippy/master/index.html), `cargo clippy -- -W help` on Clippy 0.1.95, [rustc lint levels](https://doc.rust-lang.org/rustc/lints/levels.html), [rustc lint groups](https://doc.rust-lang.org/rustc/lints/groups.html), [Cargo `[lints]`](https://doc.rust-lang.org/cargo/reference/manifest.html#the-lints-section), [Cargo workspace lints](https://doc.rust-lang.org/cargo/reference/workspaces.html#the-lints-table), [Rust 1.81.0 announcement](https://blog.rust-lang.org/2024/09/05/Rust-1.81.0/) (`#[expect]`), [Rust Design Patterns: `#![deny(warnings)]`](https://rust-unofficial.github.io/patterns/anti_patterns/deny-warnings.html), [Cargo SemVer compatibility: lints](https://doc.rust-lang.org/cargo/reference/semver.html).

### `references/practices/ownership-and-type-design.md`

[Comprehensive Rust: Idiomatic Rust](https://google.github.io/comprehensive-rust/idiomatic/welcome.html) (newtype pattern, enforce invariants, RAII, typestate, extension traits, polymorphism, sealed traits), [Comprehensive Rust: Ownership](https://google.github.io/comprehensive-rust/memory-management/ownership.html), [Rc](https://google.github.io/comprehensive-rust/smart-pointers/rc.html), [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/checklist.html) (C-CALLER-CONTROL, C-DEREF, C-OBJECT, C-BUILDER, C-CUSTOM-TYPE, C-DTOR-FAIL, C-DTOR-BLOCK, C-SEALED), [Rust Design Patterns](https://rust-unofficial.github.io/patterns/) (clone to satisfy the borrow checker, `Deref` polymorphism, use borrowed types for arguments, `mem::take`), [Reference: destructors](https://doc.rust-lang.org/reference/destructors.html), [Reference: `#[non_exhaustive]`](https://doc.rust-lang.org/reference/attributes/type_system.html), [Arc](https://doc.rust-lang.org/std/sync/struct.Arc.html), [Cow](https://doc.rust-lang.org/std/borrow/enum.Cow.html).

### `references/practices/performance.md`

[The Rust Performance Book](https://nnethercote.github.io/perf-book/) (General Tips, Benchmarking, Profiling, Inlining, Hashing, Heap Allocations, Type Sizes, Standard Library Types, Iterators, Bounds Checks, I/O, Logging and Debugging, Wrapper Types, Parallelism, Compile Times), [std::hint](https://doc.rust-lang.org/std/hint/index.html), [std::io::BufReader](https://doc.rust-lang.org/std/io/struct.BufReader.html), [std::mem::size_of](https://doc.rust-lang.org/std/mem/fn.size_of.html), [Cargo profiles](https://doc.rust-lang.org/cargo/reference/profiles.html), Clippy `perf` group from `cargo clippy -- -W help` (Clippy 0.1.95).

### `references/practices/unsafe-and-ffi.md`

[Rustonomicon: What Unsafe Rust Can Do](https://doc.rust-lang.org/nomicon/what-unsafe-does.html), [Working with Unsafe](https://doc.rust-lang.org/nomicon/working-with-unsafe.html), [Send and Sync](https://doc.rust-lang.org/nomicon/send-and-sync.html), [PhantomData](https://doc.rust-lang.org/nomicon/phantom-data.html), [Transmutes](https://doc.rust-lang.org/nomicon/transmutes.html), [FFI](https://doc.rust-lang.org/nomicon/ffi.html), [Reference: behavior considered undefined](https://doc.rust-lang.org/reference/behavior-considered-undefined.html), [Reference: behavior not considered unsafe](https://doc.rust-lang.org/reference/behavior-not-considered-unsafe.html), [std::mem::MaybeUninit](https://doc.rust-lang.org/std/mem/union.MaybeUninit.html), [std::ptr](https://doc.rust-lang.org/std/ptr/index.html), [std::ffi](https://doc.rust-lang.org/std/ffi/index.html), [Miri](https://github.com/rust-lang/miri), [Edition Guide: unsafe changes](https://doc.rust-lang.org/edition-guide/rust-2024/unsafe-op-in-unsafe-fn.html), [Rust Design Patterns: Contain unsafety in small modules](https://rust-unofficial.github.io/patterns/patterns/structural/unsafe-mods.html).

### `references/versions/1.80.md`

[Rust 1.80.0 announcement](https://blog.rust-lang.org/2024/07/25/Rust-1.80.0/), [Rust 1.80.1 announcement](https://blog.rust-lang.org/2024/08/08/Rust-1.80.1/), [RELEASES.md 1.80.0](https://github.com/rust-lang/rust/blob/master/RELEASES.md).

### `references/versions/1.81.md`

[Rust 1.81.0 announcement](https://blog.rust-lang.org/2024/09/05/Rust-1.81.0/), [RELEASES.md 1.81.0](https://github.com/rust-lang/rust/blob/master/RELEASES.md).

### `references/versions/1.82.md`

[Rust 1.82.0 announcement](https://blog.rust-lang.org/2024/10/17/Rust-1.82.0/), [Edition Guide: unsafe extern blocks](https://doc.rust-lang.org/edition-guide/rust-2024/unsafe-extern.html), [Edition Guide: unsafe attributes](https://doc.rust-lang.org/edition-guide/rust-2024/unsafe-attributes.html).

### `references/versions/1.84.md`

[Rust 1.84.0 announcement](https://blog.rust-lang.org/2025/01/09/Rust-1.84.0/), [Rust 1.84.1 announcement](https://blog.rust-lang.org/2025/01/30/Rust-1.84.1/), [RELEASES.md 1.84.0](https://github.com/rust-lang/rust/blob/master/RELEASES.md), [Cargo resolver versions](https://doc.rust-lang.org/cargo/reference/resolver.html#resolver-versions).

### `references/versions/1.85.md`

[Rust 1.85.0 announcement](https://blog.rust-lang.org/2025/02/20/Rust-1.85.0/), [Rust 2024 Edition Guide](https://doc.rust-lang.org/edition-guide/rust-2024/index.html), [Transitioning to a new edition](https://doc.rust-lang.org/edition-guide/editions/transitioning-an-existing-project-to-a-new-edition.html), [RELEASES.md 1.85.0](https://github.com/rust-lang/rust/blob/master/RELEASES.md), [Rust 1.88.0 announcement](https://blog.rust-lang.org/2025/06/26/Rust-1.88.0/) for `let` chains, [Rust 1.95.0 announcement](https://blog.rust-lang.org/2026/04/16/Rust-1.95.0/) for `if let` guards.

### `references/versions/1.86.md`

[Rust 1.86.0 announcement](https://blog.rust-lang.org/2025/04/03/Rust-1.86.0/), [RELEASES.md 1.86.0](https://github.com/rust-lang/rust/blob/master/RELEASES.md).

### `references/versions/1.87.md`

[Rust 1.87.0 announcement](https://blog.rust-lang.org/2025/05/15/Rust-1.87.0/), [RELEASES.md 1.87.0](https://github.com/rust-lang/rust/blob/master/RELEASES.md).

### `references/versions/1.88.md`

[Rust 1.88.0 announcement](https://blog.rust-lang.org/2025/06/26/Rust-1.88.0/), [RELEASES.md 1.88.0](https://github.com/rust-lang/rust/blob/master/RELEASES.md).

### `references/versions/1.89.md`

[Rust 1.89.0 announcement](https://blog.rust-lang.org/2025/08/07/Rust-1.89.0/), [RELEASES.md 1.89.0](https://github.com/rust-lang/rust/blob/master/RELEASES.md).

### `references/versions/1.90.md`

[Rust 1.90.0 announcement](https://blog.rust-lang.org/2025/09/18/Rust-1.90.0/), [RELEASES.md 1.90.0](https://github.com/rust-lang/rust/blob/master/RELEASES.md).

### `references/versions/1.91.md`

[Rust 1.91.0 announcement](https://blog.rust-lang.org/2025/10/30/Rust-1.91.0/), [Rust 1.91.1 announcement](https://blog.rust-lang.org/2025/11/10/Rust-1.91.1/), [RELEASES.md 1.91.0](https://github.com/rust-lang/rust/blob/master/RELEASES.md).

### `references/versions/1.92.md`

[Rust 1.92.0 announcement](https://blog.rust-lang.org/2025/12/11/Rust-1.92.0/), [RELEASES.md 1.92.0](https://github.com/rust-lang/rust/blob/master/RELEASES.md).

### `references/versions/1.96.md`

[Rust 1.96.0 announcement](https://blog.rust-lang.org/2026/05/28/Rust-1.96.0/), [Rust 1.96.1 announcement](https://blog.rust-lang.org/2026/06/30/Rust-1.96.1/), [RELEASES.md 1.96.0](https://github.com/rust-lang/rust/blob/master/RELEASES.md).

### `references/versions/1.97.md`

[Rust 1.97.0 announcement](https://blog.rust-lang.org/2026/07/09/Rust-1.97.0/), [Rust 1.97.1 announcement](https://blog.rust-lang.org/2026/07/16/Rust-1.97.1/), [RELEASES.md 1.97.0](https://github.com/rust-lang/rust/blob/master/RELEASES.md).

### `references/versions/index.md`

[Rust release blog](https://blog.rust-lang.org/releases/) posts 1.80.0 through 1.98.1, [RELEASES.md](https://github.com/rust-lang/rust/blob/master/RELEASES.md) compatibility notes, [releases.rs](https://releases.rs/) for the schedule, [Cargo SemVer compatibility](https://doc.rust-lang.org/cargo/reference/semver.html), [Cargo `rust-version`](https://doc.rust-lang.org/cargo/reference/rust-version.html), [Cargo resolver](https://doc.rust-lang.org/cargo/reference/resolver.html).

### `references/practices/concurrency.md` (Choosing a Parallelism Library) and `references/practices/performance.md` (Parallelism)

Ecosystem crate guidance; verify against current crate documentation when versions move: [rayon](https://docs.rs/rayon), [crossbeam-channel](https://docs.rs/crossbeam-channel), [crossbeam-utils](https://docs.rs/crossbeam-utils), [tokio](https://docs.rs/tokio) (runtime flavors, `spawn_blocking`, `tokio::sync`, `JoinSet`), [smol](https://docs.rs/smol), [async-std](https://docs.rs/async-std) (discontinuation notice), [futures](https://docs.rs/futures), [flume](https://docs.rs/flume), [arc-swap](https://docs.rs/arc-swap), [dashmap](https://docs.rs/dashmap), [parking_lot](https://docs.rs/parking_lot), [portable-atomic](https://docs.rs/portable-atomic), [spin](https://docs.rs/spin), [heapless](https://docs.rs/heapless), [critical-section](https://docs.rs/critical-section), [loom](https://docs.rs/loom), [wide](https://docs.rs/wide); `std::sync::mpsc` adopting the crossbeam-channel implementation: [Rust 1.67.0 announcement](https://blog.rust-lang.org/2023/01/26/Rust-1.67.0.html); "measure before switching to `parking_lot`": [Rust Performance Book: Standard Library Types](https://nnethercote.github.io/perf-book/standard-library-types.html).

### `SKILL.md`

Source priority and evidence labels follow the plan that introduced the skill: Rust Reference and std docs for guarantees, Cargo and rustc books for build behavior, Rust API Guidelines and Clippy for official convention, Google Comprehensive Rust, the Rust Performance Book, and Rust Atomics and Locks for design recommendations, Rust Design Patterns as community material, and measurements for performance claims.
