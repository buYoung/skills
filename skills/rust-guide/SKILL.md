---
name: rust-guide
description: Use to explain Rust language characteristics and established practical patterns, and to apply that knowledge in Rust development. Covers ownership, borrowing, lifetimes, traits and API design, collections, memory allocation, error handling, async execution and CPU parallelism, synchronization, module and crate boundaries, Cargo workspaces and monorepos, library selection, performance and SIMD, WebAssembly, embedded/no_std, unsafe/FFI, compiler diagnostics, build configuration, and MSRV/edition compatibility. Use for questions about how Rust works, idiomatic ways to structure code, why a compiler constraint exists, when a pattern or library fits, and its costs and exceptions. Connects mechanisms to practical examples, including std/core approaches and curated ecosystem libraries. Uses stable Rust with explicit API, edition, and target requirements; explains relevant nightly alternatives separately.
license: MIT
---

# Rust Guide

Explain Rust's characteristics and established practical patterns by topic. Connect how the language and libraries work to recommended usage, applicable conditions, costs, pitfalls, and exceptions. Use examples that make these relationships concrete.

## Explain the Topic

Start with the concept needed to answer the question, then connect it to practice. For a substantial topic, cover **mechanism → practical pattern → applicable conditions → pitfalls and exceptions → example**. This is a way to develop the explanation, not a required response template. A narrow question may need only a paragraph or a small example.

- Explain why a pattern works: ownership and resource lifetime, type guarantees, execution and synchronization, memory representation, or compilation behavior.
- Develop the suitable std/core approach where it is useful. Explain what a dependency adds and what maintaining an equivalent implementation would cost; fewer dependencies alone do not justify writing a scheduler or unsafe allocator.
- Treat `clone`, `dyn Trait`, `Arc<Mutex<T>>`, allocation, and abstractions according to their semantics and costs. A useful default has conditions and exceptions.
- Use comparisons when the question involves alternatives. Classify their roles before comparing names, and use the [library selection policy](references/practices/library-selection.md) for new dependency recommendations.
- Relate examples to observable behavior: who owns a buffer, which failure a caller can handle, when a task ends, or which configuration reaches a target.

Match depth to the reader's question. Explain the underlying constraint when discussing a diagnostic; connect an established pattern to the supplied code when application is requested. Keep small examples focused, and explain any omitted runtime, device setup, dependency features, or failure handling that matters to their use.

## Account for the Environment

Bring in environmental facts when they change the explanation: `core`/`alloc`/`std`, host and target, OS threads or interrupts, runtime, MSRV and edition, dependency features, public API, and deployment CPU baseline. A general language question needs no repository inspection. Use supplied code and manifests for project-specific questions, and state assumptions where relevant facts are unavailable.

Distinguish workload costs such as I/O waiting, computation, contention, retained memory, startup, and build time. Explain the likely mechanism before suggesting a measurement; a performance hypothesis becomes a speedup claim only with comparable results.

## Route by the Question

Read the relevant section of the closest reference first. Long references have contents tables; expand to neighboring sections only when their concepts are needed. Follow cross-topic links for relationships such as ownership and allocation, async and cancellation, or workspace features and no_std.

| Task signal | Read |
|---|---|
| Ownership, borrowing, lifetimes, shared ownership, interior mutability | [Ownership and borrowing](references/practices/ownership-and-borrowing.md#ownership-borrowing-and-resource-lifetimes), then [parameter and return types](references/practices/ownership-and-borrowing.md#parameter-and-return-types) or [shared ownership](references/practices/ownership-and-borrowing.md#shared-ownership-and-cycles) |
| Drop, drop order, RAII guards, cleanup on scope exit | [RAII and Drop](references/practices/raii-and-drop.md) |
| Newtype, invariants, typestate, builders, non_exhaustive | [Type patterns](references/practices/type-design.md#newtypes) |
| Enum/generic/dyn, dyn compatibility, sealed traits, async fn in traits | [Dispatch](references/practices/traits-and-dispatch.md#enum-trait-generic-or-dyn) |
| Lookup, ordering, queues, hashing, collection capacity | [Collection semantics and representation](references/practices/collections.md#semantics-representation-and-cost), then the relevant operation |
| Graphs, trees, parent pointers, cyclic structures | [Graphs and trees](references/practices/graphs-and-trees.md) |
| Allocation, buffer reuse, arena/pool, allocator, retained memory | [Memory and allocation](references/practices/memory-and-allocation.md#storage-allocation-and-release) |
| Error types, std-only implementations, thiserror, stable recovery information | [The error model](references/practices/error-types.md#values-propagation-and-error-information), then [manual implementation](references/practices/error-types.md#anatomy-of-a-library-error-type) |
| `?` and From conversions, anyhow, error context and chains, exit codes | [Propagation](references/practices/error-propagation-and-reporting.md#propagation-with--and-from) or [reporting](references/practices/error-propagation-and-reporting.md#application-errors-with-anyhow) |
| Panic or Result, unwinding, abort, catch_unwind | [Panics](references/practices/panics.md) |
| Function/module/crate separation, visibility, core and adapters | [Modules and crate boundaries](references/practices/modules-and-crate-boundaries.md) |
| Public API naming, traits, conversions, documentation | [API design](references/practices/api-design.md) |
| SemVer, deprecation, Cargo features, MSRV, public dependencies | [Crate compatibility](references/practices/crate-compatibility.md) |
| Workspace, monorepo, feature unification, shared versions/releases | [Workspaces and monorepos](references/practices/workspaces-and-monorepos.md) |
| Crate comparisons, std versus dependencies, adoption/maintenance | [Library selection](references/practices/library-selection.md) |
| Future/task/thread, Tokio/smol, Rayon/Crossbeam, blocking and limits | [Execution model and patterns](references/practices/async-and-parallel-execution.md#futures-tasks-and-threads) |
| Async borrowing, Send, 'static, Pin/Unpin | [Task ownership](references/practices/async-and-parallel-execution.md#borrowing-and-task-ownership), [pinning](references/practices/async-and-parallel-execution.md#pin-and-unpin) |
| Cancellation, timeouts, shutdown | [Cancellation](references/practices/async-and-parallel-execution.md#cancellation-is-an-ownership-contract), [shutdown](references/practices/async-and-parallel-execution.md#channels-locks-and-shutdown) |
| Threads, channels, Send/Sync, thread pools | [Concurrency](references/practices/concurrency.md#choosing-a-model); use its contents for the specific primitive |
| Locks, lazy initialization, atomics, deadlocks, contention | [Synchronization](references/practices/synchronization.md); start from [choosing a model](references/practices/concurrency.md#choosing-a-model) when the primitive is undecided |
| Benchmarking, profiling, interpreting measurements | [Performance measurement](references/practices/performance-measurement.md) |
| Algorithms, allocation, layout, iterators, I/O, runtime bottlenecks | [Performance optimization](references/practices/performance-optimization.md) |
| Slow builds, compile times, generic instantiation | [Compile times](references/practices/compile-times.md), then [build settings](references/practices/build-configuration.md#faster-development-builds) |
| Auto-vectorization, SIMD intrinsics, CPU detection, fallback | [SIMD](references/practices/simd.md) |
| Browser/WASI, JS boundary, Wasm memory, workers and size | [WebAssembly](references/practices/webassembly.md) |
| Firmware, no_std, no heap, interrupts, HAL, DMA, embedded async | [Embedded and no_std](references/practices/embedded-and-no-std.md) |
| Cargo profiles, LTO, symbols, panic, PGO, compiler flags | [Build configuration](references/practices/build-configuration.md) |
| Raw pointers, layout, aliasing, initialization | [Safety contracts](references/practices/unsafe-rust.md#unsafe-fn-unsafe-blocks-and-safety-comments), then the relevant memory section |
| FFI, extern blocks, callbacks, foreign allocations and handles | [FFI](references/practices/ffi.md), with [safety contracts](references/practices/unsafe-rust.md#unsafe-fn-unsafe-blocks-and-safety-comments) for its unsafe operations |
| Compiler errors, borrow/lifetime/Send diagnostics | [Compiler diagnostics](references/practices/compiler-diagnostics.md) |
| Clippy diagnostics, lint configuration | [Lints](references/practices/lints.md) |
| Edition 2024 migration | [Edition migration](references/versions/1.85.md) |
| Toolchain upgrade and release compatibility | [Versions index](references/versions/index.md), then the relevant release files |

## Compatibility

- Use the relevant topic's explanation, conditions, and examples to answer the question. Distinguish language/API guarantees, conditional practices, and measured outcomes.
- Match APIs and dependencies to the project's features, MSRV, target, and runtime. Explain relevant nightly alternatives separately from the stable approach.
- Release references cover Rust 1.80 through 1.100.0; for a later release, read its official release notes before relying on version-specific claims. Each example has its own API requirements; edition 2024 requires Rust 1.85 even when its APIs are older. An older MSRV needs a supported edition and compatible APIs.
- Apply the library catalog's role and suitability conditions. Popularity narrows candidates; it does not establish correctness or a performance benefit.
- State assumptions and unresolved version or target constraints where they affect the answer. Describe compilation, target execution, and measured behavior only to the extent actually established.
