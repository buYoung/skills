# Reference Sources and Maintenance Data (2026-09-21)

Maintenance material for rust-guide. Sources are indexed by the reference they support. This inventory preserves existing provenance; it does not claim a new source audit, example compilation, or model evaluation.

## Sources by Reference

### `references/practices/api-and-crate-design.md`

- [API Guidelines](https://rust-lang.github.io/api-guidelines/checklist.html)
- [Cargo SemVer](https://doc.rust-lang.org/cargo/reference/semver.html)
- [features](https://doc.rust-lang.org/cargo/reference/features.html)
- [API Guidelines](https://rust-lang.github.io/api-guidelines/predictability.html#functions-do-not-take-out-parameters-c-no-out)

### `references/practices/async-and-parallel-execution.md`

- [Future contract](https://doc.rust-lang.org/std/future/trait.Future.html)
- [Tokio CPU work](https://docs.rs/tokio/latest/tokio/index.html#cpu-bound-tasks-and-blocking-code)
- [Rayon](https://docs.rs/rayon/)
- [Task ownership and bounds](https://tokio.rs/tokio/tutorial/spawning)
- [Pin and Unpin](https://doc.rust-lang.org/std/pin/index.html)
- [spawn_blocking contract](https://docs.rs/tokio/latest/tokio/task/fn.spawn_blocking.html)
- [JoinSet](https://docs.rs/tokio/latest/tokio/task/struct.JoinSet.html)
- [JoinHandle](https://docs.rs/tokio/latest/tokio/task/struct.JoinHandle.html)
- [select cancellation safety](https://docs.rs/tokio/latest/tokio/macro.select.html#cancellation-safety)
- [Tokio mutex guidance](https://docs.rs/tokio/latest/tokio/sync/struct.Mutex.html)
- [Tokio shutdown](https://tokio.rs/tokio/topics/shutdown)

### `references/practices/build-configuration.md`

- [Cargo profiles](https://doc.rust-lang.org/cargo/reference/profiles.html)
- [rustc codegen options](https://doc.rust-lang.org/rustc/codegen-options/index.html)
- [target CPU options](https://doc.rust-lang.org/rustc/codegen-options/index.html#target-cpu)

### `references/practices/collections.md`

- [std collections](https://doc.rust-lang.org/std/collections/index.html)
- [Vec guarantees](https://doc.rust-lang.org/std/vec/struct.Vec.html#guarantees)

### `references/practices/concurrency.md`

- [std synchronization](https://doc.rust-lang.org/std/sync/index.html)
- [atomic ordering](https://doc.rust-lang.org/std/sync/atomic/enum.Ordering.html)
- [Eager and lazy bool helpers](https://doc.rust-lang.org/std/primitive.bool.html#method.then_some)
- [Tokio JoinHandle](https://docs.rs/tokio/latest/tokio/task/struct.JoinHandle.html)
- [spawn_blocking](https://docs.rs/tokio/latest/tokio/task/fn.spawn_blocking.html)
- [select](https://docs.rs/tokio/latest/tokio/macro.select.html#cancellation-safety)
- [parking_lot](https://docs.rs/parking_lot/)
- [dashmap](https://docs.rs/dashmap/)
- [arc-swap](https://docs.rs/arc-swap/)
- [loom](https://docs.rs/loom/)

### `references/practices/embedded-and-no-std.md`

- [no_std environment](https://doc.rust-lang.org/embedded-book/intro/no-std.html)
- [alloc](https://doc.rust-lang.org/alloc/)
- [embedded-hal](https://docs.rs/embedded-hal/)
- [heapless](https://docs.rs/heapless/)
- [Embassy executor](https://docs.embassy.dev/embassy-executor/)
- [Embedded concurrency](https://docs.rust-embedded.org/book/concurrency/index.html)
- [read_volatile contract](https://doc.rust-lang.org/core/ptr/fn.read_volatile.html)

### `references/practices/error-handling.md`

- [Result](https://doc.rust-lang.org/std/result/)
- [Error](https://doc.rust-lang.org/std/error/trait.Error.html)
- [thiserror](https://docs.rs/thiserror/)
- [Downcasting](https://doc.rust-lang.org/std/error/trait.Error.html#method.downcast_ref)
- [Slice construction requirements](https://doc.rust-lang.org/std/slice/fn.from_raw_parts.html#safety)

### `references/practices/library-selection.md`

- [RustSec](https://rustsec.org/)
- [build-script documentation](https://doc.rust-lang.org/cargo/reference/build-scripts.html)
- [Reference](https://doc.rust-lang.org/reference/procedural-macros.html)
- [crates.io ranking rationale](https://rust-lang.github.io/rfcs/1824-crates.io-default-ranking.html)
- [Tokio](https://docs.rs/tokio/)
- [smol](https://docs.rs/smol/)
- [Rayon](https://docs.rs/rayon/)
- [Crossbeam channel](https://docs.rs/crossbeam-channel/)
- [flume](https://docs.rs/flume/)
- [futures](https://docs.rs/futures/)
- [wasm-bindgen ecosystem](https://docs.rs/wasm-bindgen-futures/)
- [Embassy](https://docs.embassy.dev/embassy-executor/)
- [thiserror](https://docs.rs/thiserror/)
- [anyhow](https://docs.rs/anyhow/)
- [smallvec](https://docs.rs/smallvec/)
- [heapless](https://docs.rs/heapless/)
- [embedded-hal](https://docs.rs/embedded-hal/)
- [memchr](https://docs.rs/memchr/)
- [parking_lot](https://docs.rs/parking_lot/)
- [arc-swap](https://docs.rs/arc-swap/)
- [dashmap](https://docs.rs/dashmap/)
- [serde](https://docs.rs/serde/)
- [loom](https://docs.rs/loom/)
- [official notice](https://docs.rs/async-std/)

### `references/practices/lints-and-diagnostics.md`

- [Rust error codes](https://doc.rust-lang.org/error_codes/)
- [Clippy documentation](https://doc.rust-lang.org/clippy/)
- [lint catalog](https://rust-lang.github.io/rust-clippy/master/index.html)
- [lifetime model](https://doc.rust-lang.org/book/ch10-03-lifetime-syntax.html)
- [rustc lint levels](https://doc.rust-lang.org/rustc/lints/levels.html)

### `references/practices/memory-and-allocation.md`

- [Vec guarantees](https://doc.rust-lang.org/std/vec/struct.Vec.html#guarantees)
- [allocation](https://doc.rust-lang.org/std/alloc/index.html)
- [API Guidelines: caller control](https://rust-lang.github.io/api-guidelines/flexibility.html#caller-decides-where-to-copy-and-place-data-c-caller-control)

### `references/practices/modules-and-crate-boundaries.md`

- [Cargo layout](https://doc.rust-lang.org/cargo/guide/project-layout.html)
- [Rust visibility](https://doc.rust-lang.org/reference/visibility-and-privacy.html)
- [Inline attributes](https://doc.rust-lang.org/reference/attributes/codegen.html#the-inline-attribute)

### `references/practices/ownership-and-type-design.md`

- [API Guidelines](https://rust-lang.github.io/api-guidelines/flexibility.html)
- [Arc](https://doc.rust-lang.org/std/sync/struct.Arc.html)
- [RefCell](https://doc.rust-lang.org/std/cell/struct.RefCell.html)
- [Ownership](https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html)
- [borrowing](https://doc.rust-lang.org/book/ch04-02-references-and-borrowing.html)
- [lifetimes](https://doc.rust-lang.org/book/ch10-03-lifetime-syntax.html)

### `references/practices/performance.md`

- [Rust Performance Book](https://nnethercote.github.io/perf-book/)
- [codegen attributes](https://doc.rust-lang.org/reference/attributes/codegen.html)

### `references/practices/simd.md`

- [core::simd](https://doc.rust-lang.org/core/simd/index.html)
- [core::arch](https://doc.rust-lang.org/core/arch/index.html)
- [Reference: target_feature](https://doc.rust-lang.org/reference/attributes/codegen.html#the-target_feature-attribute)
- [memchr](https://docs.rs/memchr/)

### `references/practices/unsafe-and-ffi.md`

- [Cell Send/Sync implementations](https://doc.rust-lang.org/std/cell/struct.Cell.html)
- [RefCell Send/Sync implementations](https://doc.rust-lang.org/std/cell/struct.RefCell.html)
- [Mutex transfer and sharing requirements](https://doc.rust-lang.org/std/sync/struct.Mutex.html)
- [Rust Reference: undefined behavior](https://doc.rust-lang.org/reference/behavior-considered-undefined.html)
- [Rustonomicon FFI](https://doc.rust-lang.org/nomicon/ffi.html)
- [Edition rules](https://doc.rust-lang.org/edition-guide/rust-2024/unsafe-op-in-unsafe-fn.html)

### `references/practices/webassembly.md`

- [Rust Wasm target](https://doc.rust-lang.org/rustc/platform-support/wasm32-unknown-unknown.html)
- [WASIp1](https://doc.rust-lang.org/rustc/platform-support/wasm32-wasip1.html)
- [WASIp2](https://doc.rust-lang.org/rustc/platform-support/wasm32-wasip2.html)
- [String bindings](https://wasm-bindgen.github.io/wasm-bindgen/reference/types/str.html)
- [serde conversion trade-offs](https://wasm-bindgen.github.io/wasm-bindgen/reference/arbitrary-data-with-serde.html)
- [Uint8Array view safety](https://wasm-bindgen.github.io/wasm-bindgen/api/js_sys/struct.Uint8Array.html#method.view)
- [Memory.grow](https://developer.mozilla.org/en-US/docs/WebAssembly/Reference/JavaScript_interface/Memory/grow)
- [Future/Promise integration](https://docs.rs/wasm-bindgen-futures/)
- [SharedArrayBuffer requirements](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/SharedArrayBuffer)
- [Rust Wasm feature rules](https://doc.rust-lang.org/rustc/platform-support/wasm32-unknown-unknown.html#enabled-webassembly-features)
- [Cargo profiles](https://doc.rust-lang.org/cargo/reference/profiles.html#opt-level)

### `references/practices/workspaces-and-monorepos.md`

- [Cargo workspaces](https://doc.rust-lang.org/cargo/reference/workspaces.html)
- [Cargo feature resolution](https://doc.rust-lang.org/cargo/reference/resolver.html#features)
- [Rust version resolution](https://doc.rust-lang.org/cargo/reference/resolver.html#rust-version)
- [Cargo multiple locations](https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html#multiple-locations)

## Lint Catalog Metadata

The group/default snapshot below comes from Clippy 0.1.95 (Rust 1.95). Groups and defaults change; `cargo clippy -- -W help` describes the installed toolchain. Topic references explain the semantics behind individual lints.

| Group | Default | Count (0.1.95) | Meaning (Clippy book) |
|---|---|---|---|
| `clippy::correctness` | deny | 68 | "Code that is outright wrong or useless" |
| `clippy::suspicious` | warn | 82 | "Code that is most likely wrong or useless" |
| `clippy::style` | warn | 157 | A more idiomatic way exists |
| `clippy::complexity` | warn | 136 | Something simple done in a complex way |
| `clippy::perf` | warn | 36 | "Code that can be written to run faster" |
| `clippy::pedantic` | allow | 140 | Strict, or occasional false positives; enable individually |
| `clippy::restriction` | allow | 130 | Forbids language or library features; never enable the whole group (`blanket_clippy_restriction_lints` in `suspicious` fires when you try) |
| `clippy::nursery` | allow | 52 | Under development; false positives expected |
| `clippy::cargo` | allow | 5 | Manifest metadata checks |

## Library Catalog Dispositions

- `async-std`: discontinued; do not recommend for new adoption. Its [official notice](https://docs.rs/async-std/) points to smol.
- `glommio`: below the recent-download floor in this snapshot.
- `futures-lite`, `futures-concurrency`, `async-executor`, `async-io`, `async-channel`: below the GitHub-star floor; not standalone catalog recommendations, even though several are widely used components.
- `arrayvec`, `wide`, `pulp`, `critical-section`, `portable-atomic`, `mimalloc`, `tikv-jemallocator`: below that same star floor in the extension audit. Teach fixed storage, SIMD, synchronization, and allocator mechanisms without promoting these wrappers as defaults. Existing HAL-provided synchronization remains usable.
- Monoio, Compio, and tokio-uring met the numerical floor but stay outside the basic comparison. Consider them only for an explicit completion-I/O/thread-per-core requirement, with platform, compatibility, and maintenance checks. Numerical popularity is not a performance result.

The shortlist can change. Retain a dated rationale for additions/removals instead of silently growing into a catalog of every known crate.

## Release Calendar Metadata

- `1.80.md`: Released 2024-07-25; point release 1.80.1 on 2024-08-08.
- `1.81.md`: Released 2024-09-05.
- `1.82.md`: Released 2024-10-17.
- `1.84.md`: Released 2025-01-09; point release 1.84.1 on 2025-01-30.
- `1.85.md`: Released 2025-02-20; point release 1.85.1 on 2025-03-18. Edition 2024 ships with this release: `edition = "2024"` requires Rust 1.85.0 or later, so a library that adopts it raises its MSRV to at least 1.85.
- `1.86.md`: Released 2025-04-03.
- `1.87.md`: Released 2025-05-15.
- `1.88.md`: Released 2025-06-26.
- `1.89.md`: Released 2025-08-07.
- `1.90.md`: Released 2025-09-18.
- `1.91.md`: Released 2025-10-30; point release 1.91.1 on 2025-11-10.
- `1.92.md`: Released 2025-12-11.
- `1.96.md`: Released 2026-05-28; point release 1.96.1 on 2026-06-30.
- `1.97.md`: Released 2026-07-09; point release 1.97.1 on 2026-07-16.

## Source-Specific Performance Observations

These observations were present in the previous reference text and describe source-specific workloads, not measurements made for this revision.

- `build-configuration.md`: debug = "line-tables-only"   # 20-40% faster dev builds than full debuginfo per the Performance Book
- `build-configuration.md`: PGO compiles twice: an instrumented build collects execution profiles, the final build uses them for inlining and layout decisions. The Performance Book cites gains of "10% or more" on suitable workloads.
- `performance.md`: The first pitfall the book names is measuring a non-release build. `cargo run` and `cargo test` use the `dev` profile (`opt-level = 0`, debug assertions and overflow checks on), which is often 10 to 100 times slower.

## Recorded API Stability

As checked on 2026-09-21, [core::simd](https://doc.rust-lang.org/core/simd/index.html) still requires the nightly `portable_simd` feature. [core::arch](https://doc.rust-lang.org/core/arch/index.html) provides target-specific APIs, some stable and some individually experimental. no_std does not prevent using supported core intrinsics.
