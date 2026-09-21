# Practical Examples and Contract Verification (2026-09-21)

## Scope

Expanded the seventeen practice references where explanations lacked mechanisms or adaptable examples. The entry point remains a topic-oriented Rust knowledge guide. This maintenance record is outside its runtime reference graph.

- SIMD now explains lanes, layout, vectorization legality and costs, with wrapping scalar semantics and a complete safe dispatch boundary over AVX2, NEON, and fallback kernels. It covers full-width bounds, tails, deployment features, numerical behavior, and interpreting generated code.
- Allocation now includes a fallible packet encoder and a bounded RAII buffer pool, with distinct allocation, retention, checked-out memory, and cleanup contracts. Arena lifetimes and allocator obligations are explained separately.
- Embedded material includes a fixed-capacity stream decoder, an embedded-hal driver retaining bus ownership, event-bit coalescing, DMA ownership transitions, and async memory/deadline analysis.
- Wasm now follows one pixel operation through native logic, wasm-bindgen boxed slices, retained linear-memory storage, a worker protocol, and a WASIp1 command. Mutable host access uses a mutable pointer; view lifetime, disposal, initialization, transfer, and admission contracts are explicit.
- Async material includes a bounded task supervisor, resumable partial reads, and a Rayon bridge whose admission permit stays with the actual CPU job after the caller cancels.
- Module and workspace material supplies concrete source layouts, manifests, public APIs, feature-gated implementations, and a missing-feature example that behaves differently in combined and isolated builds.
- Ownership, errors, diagnostics, and FFI gained concrete flows: borrowed-to-owned settings, static/dynamic future dispatch, opaque errors with stable recovery categories, compiler-error corrections, and an owning foreign-allocation handle.
- Existing claims about collection growth, automatic optimization, thread-safety bounds, constructor invariants, C absolute-value preconditions, and callback cleanup were corrected or narrowed. Remaining source-attribution prose was replaced with direct explanations.

The library popularity policy and candidate scope were preserved. No new adoption-count audit or broad dependency expansion was performed. Evaluation specifications were strengthened without recording fabricated model outputs or scores.

## Technical Sources Consulted

These links support maintenance and fact checking; the practice references contain the explanations themselves.

- SIMD feature and intrinsic contracts: [core::arch](https://doc.rust-lang.org/core/arch/index.html), [core::simd](https://doc.rust-lang.org/core/simd/index.html), and [LLVM vectorizers](https://llvm.org/docs/Vectorizers.html).
- Storage, pointer access, and allocation contracts: [Vec](https://doc.rust-lang.org/std/vec/struct.Vec.html), [collections](https://doc.rust-lang.org/std/collections/index.html), and [GlobalAlloc safety](https://doc.rust-lang.org/std/alloc/trait.GlobalAlloc.html#safety).
- Wasm boundary conversions: [numeric slices](https://wasm-bindgen.github.io/wasm-bindgen/reference/types/number-slices.html) and [boxed numeric slices](https://wasm-bindgen.github.io/wasm-bindgen/reference/types/boxed-number-slices.html).
- Driver transactions: [embedded-hal 1.0 I2c](https://docs.rs/embedded-hal/1.0.0/embedded_hal/i2c/trait.I2c.html).
- Execution and cancellation: [Tokio AsyncReadExt::read](https://docs.rs/tokio/latest/tokio/io/trait.AsyncReadExt.html#method.read), [JoinSet](https://docs.rs/tokio/latest/tokio/task/struct.JoinSet.html), and [Rayon spawn](https://docs.rs/rayon/latest/rayon/fn.spawn.html).
- Type and conversion contracts: [dyn compatibility](https://doc.rust-lang.org/reference/items/traits.html#dyn-compatibility) and [From](https://doc.rust-lang.org/std/convert/trait.From.html).
- FFI and cleanup: [FFI contracts](https://doc.rust-lang.org/nomicon/ffi.html), [resource leaks and destructor limits](https://doc.rust-lang.org/nomicon/leaking.html), [catch_unwind](https://doc.rust-lang.org/std/panic/fn.catch_unwind.html), and [C absolute-value representability](https://ftp.gnu.org/pub/old-gnu/Manuals/glibc-2.2.3/html_chapter/libc_20.html).
- Build composition: [Cargo features](https://doc.rust-lang.org/cargo/reference/features.html), [workspace resolution](https://doc.rust-lang.org/cargo/reference/resolver.html), and [linker-plugin LTO](https://doc.rust-lang.org/rustc/linker-plugin-lto.html).

## Local Verification

Environment: rustc 1.95.0, Cargo 1.95.0, aarch64-apple-darwin, Node 24.14.0. Dependency-backed examples used Tokio 1.53.1, Rayon 1.12.0, embedded-hal 1.0.0, and wasm-bindgen 0.2.126. Compilation and execution scaffolding stayed in temporary directories rather than becoming package dependencies or automation.

### Compilation and Diagnostics

- Twenty changed standalone std/core blocks compiled, including the later callback and equivalent dot-product corrections. The buffer-pool usage block was combined with its preceding pool definition.
- Five dependency-backed blocks compiled. Three intentionally invalid examples produced the documented borrow, lifetime, and non-Send diagnostics.
- Multipart module, workspace, and Wasm examples were assembled with their documented source relationships and manifests. The Celsius example also compiled with its std/alloc feature configuration.
- The AVX2 implementation cross-compiled for x86_64-pc-windows-gnu. Optimized native assembly contained NEON packed addition. This establishes compilation/code generation, not an AVX2 runtime result or a speedup.

### Executed Behavior

- SIMD matched the scalar reference for lengths 0 through 97 and 255/256/257, offset subslices, wrapping arithmetic, and output sentinels. Length errors preserved output. The fallback was exercised separately; the native optimized path was NEON. The indexed/iterator dot-product examples also matched their initial-value and length-error contracts.
- Allocation examples handled empty/limited packets, pool exhaustion, ordinary return, oversized-buffer discard, and return during unwinding. Allocation failure was not induced.
- The embedded decoder handled empty and exact-capacity lines, overflow discard, delimiter resynchronization, and zero capacity. Event bits coalesced and drained. A mock I2C implementation checked transaction shape and bus return on invalid input.
- Async examples drained admitted jobs, rejected further input on initial shutdown, preserved partial-read progress across a timeout, and resumed the frame. The CPU bridge returned values and caught a panic; cancelling its caller left the permit held until the Rayon job ended.
- Foreign-buffer allocation/mutation/ownership transfer, C string handling, exclusion of c_int::MIN, and callback overflow recovery ran with valid pointer contracts. Error examples preserved classifications and source chains; owned settings survived source disposal; static/dynamic in-memory futures returned the same bytes.
- The CLI package accepted a valid port and rejected zero. The workspace's incomplete consumer passed when built with a feature-enabling sibling, failed alone, then passed after declaring its own required feature. Core-only, alloc, and std configurations compiled independently.
- The pixel kernel preserved alpha and validated input shape. The retained Frame pointer/operation sequence executed natively. The WASIp1 release binary ran under Node's preview1 host with both valid bytes and an invalid-input exit.
- Four JavaScript blocks passed syntax checks. Node host mocks exercised pending/failed worker initialization, one-request admission, numeric/size rejection, view-copy/transfer ownership, and worker failure. These mocks are not browser-worker execution.

### Document Integrity

Checked frontmatter YAML, package-local Markdown links and anchors, fence pairing, the sixteen evaluation records, and whitespace errors. Runtime Markdown has no external reference links or routing into updates/evals. Repository/documentation URL values inside the illustrative Cargo manifest remain example data.

## Limits

No generated browser glue was executed in a browser, no MCU target or hardware was tested, and AVX2 was not executed. The browser target and a bare-metal target were not installed locally. Hardware timing, cache/DMA behavior, browser memory growth, and cross-engine deployment remain target-specific checks.

No comparative performance benchmark, full MSRV matrix, exhaustive concurrency exploration, or independent model evaluation was run. Compilation and focused executions do not validate every unchanged historical example or establish that every workload benefits from a pattern.
