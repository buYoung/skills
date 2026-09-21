# Library Selection

## Roles, Capabilities, and Adoption

Explain the capability and practical pattern before introducing implementations. A runtime, a compute pool, and a channel are different components and can coexist. Find candidates from that role, not only names supplied in the question, and keep comparisons to a few alternatives with materially different strengths.

Compare std/core with the dependency's capabilities, documentation, portability, feature footprint, maintenance, public-type exposure, and the cost of maintaining equivalent code. Existing integrations matter: an otherwise appealing runtime may require adapters for the application's I/O libraries.

## Practical Dependency Conditions

| Condition | What it changes |
|---|---|
| MSRV, target, runtime, and default/optional features | Whether the required capability exists in the intended build, including no_std and cross-compilation |
| Public types and feature exposure | Compatibility obligations for downstream users and how easily the dependency can later be replaced |
| License and distribution requirements | Compatibility with the project's permitted licenses and distribution model; inspect actual package/native-component licenses rather than only a repository label |
| Known security advisories | Whether the resolved version and enabled functionality are affected, and whether a fix or relevant mitigation exists |
| Native libraries and linking | Required compiler, headers, system packages, static/dynamic linking, deployment libraries, and target support |
| Build scripts and procedural macros | Build-host execution, generated code, reproducibility inputs, build time, and additional toolchain requirements |
| Maintenance and documentation | Clarity of contracts, supported platforms, upgrade paths, and the cost of depending on unresolved limitations |

RustSec supplies advisories for Rust packages; absence of an advisory is not proof of safety. Build scripts and procedural macros execute on the build host; native compilation additionally needs tools and libraries suitable for the target. These conditions are relevant to dependency adoption, not prerequisites for answering ordinary language questions.

## Admission Conditions

New independent library recommendations require both **at least 1,000 GitHub repository stars** and **at least 100,000 crates.io downloads in the last 90 days**, with no announced discontinuation or archive. This is an editorial popularity floor, not a correctness or security guarantee.

The figures apply to the actual Rust package and its repository. A monorepo's stars cover multiple packages; downloads include transitive dependencies and CI, so neither figure counts unique users. A popular upstream native library does not establish its Rust wrapper's adoption.

Use the shortlist by role and technical fit. A candidate passing the floor still needs compatible features, targets, maintenance, and integration requirements. If no admitted candidate fits, explain the std/core approach or the capability gap. Existing or explicitly requested dependencies remain valid subjects of technical guidance; popularity alone does not justify a migration. Do not claim an additional candidate meets the floor without adequate adoption information.

## Primary Execution Shortlist

| Role | Candidates | Decision boundary |
|---|---|---|
| Concurrent I/O and task scheduling | Tokio, smol | Ecosystem integration versus a composable runtime; verify required I/O adapters and deployment constraints |
| CPU data parallelism and reusable compute pool | Rayon | Enough independent work to justify splitting; use std threads for simple, explicitly managed work |
| Synchronous MPMC channels and selection | Crossbeam channel | More consumers or channel-selection needs than std MPSC provides |
| Synchronous/asynchronous channel bridge | flume | Choose its sync/async operations deliberately; do not block an executor through a synchronous receive |
| Future/Stream/Sink composition | futures | Group work without necessarily spawning tasks; its utilities are not an OS I/O runtime replacement |
| Browser Future/Promise boundary | wasm-bindgen ecosystem | Use host event-loop integration; current wasm-bindgen-futures re-exports js-sys futures functionality |
| Embedded async | Embassy | Target-supported async execution with static task allocation; a simple loop may still suffice |

Use [async and parallel execution](async-and-parallel-execution.md) for lifetimes, limits, and shutdown.

## Topic-Specific Candidates

Read only the relevant row; these are not additional runtime alternatives.

| Need | Eligible examples | Why / when to stay with std/core |
|---|---|---|
| Typed error boilerplate / application reporting | thiserror, anyhow | Manual small error types remain sufficient; choose by recovery and reporting boundary |
| Inline or fixed-capacity collections | smallvec, heapless | Distinguish spill-to-heap from fixed capacity and explicit full handling |
| Embedded driver interfaces | embedded-hal | Reusable drivers across implementing HALs; board-specific setup still needs its own documentation |
| Optimized byte search | memchr | Existing SIMD-backed operation before a custom unsafe kernel; a simple loop can suffice for tiny input |
| Proven shared-state need | parking_lot, arc-swap, dashmap | Distinct lock, snapshot, and concurrent-map roles; first assess ownership and std synchronization |
| Serialization already required by the task | serde | Check concrete format, allocation, borrowing, and no_std features separately |
| A custom synchronization protocol needs exploration | loom | Model supported interleavings; not proof of arbitrary application correctness |

## Specialized Execution Models

Completion-I/O and thread-per-core runtimes can fit an explicit platform and workload requirement, but change task mobility, buffer lifetime, I/O integration, and operational assumptions. They are additional execution models to understand rather than interchangeable upgrades for a general async runtime. Apply the same admission and suitability conditions before introducing a specialized implementation.

## Compare Implementations Within Their Role

The shortlist becomes useful when a concrete requirement is mapped to a contract:

| Comparison | Practical difference | Typical consequence |
|---|---|---|
| std threads versus an async runtime | Blocking call stacks and borrowed scoped work versus cooperatively polled tasks and runtime I/O drivers | A few blocking operations can be simpler as threads; many waiting connections can justify async integration |
| Tokio versus smol | Integrated runtime/I/O facilities and runtime-bound ecosystem APIs versus composable execution/I/O components | A client using Tokio's socket/timer facilities needs that integration; implementing Future alone does not make it runnable with arbitrary I/O drivers |
| Rayon versus runtime blocking work | Reusable CPU scheduling and data-parallel decomposition versus isolating blocking calls from async workers | Rayon fits partitionable CPU work; a few bounded blocking APIs can fit spawn_blocking; admission remains a separate limit |
| std mpsc versus Crossbeam channel | Single receiver versus cloneable multi-consumer endpoints and channel selection facilities | Match worker distribution and shutdown semantics rather than replacing a queue because another crate is popular |
| Crossbeam channel versus flume/runtime channels | Blocking channel operations versus chosen async wait interfaces | A blocking receive can stall an async worker even if sending occurred in async code |
| futures combinators versus spawning | Child futures polled within a containing operation versus independently scheduled owned tasks | Composition can retain borrowed data; spawning introduces ownership, Send/static, result tracking, and shutdown requirements |
| Mutex versus snapshot/map-specific tools | Exclusive data access versus immutable publication or sharded operations | A snapshot reader, a compound map transaction, and a short counter update need different consistency contracts |

For a runtime library, establish who owns the executor and I/O resources. A reusable crate can accept a handle or return futures without constructing a new runtime per operation. A timer or socket still needs its intended driver context. Wrapping incompatible I/O types in an adapter can bridge traits without changing every runtime-specific behavior.

Feature flags also affect adoption. Tokio's rt, net, time, sync, and macros capabilities are separate; a small example using tasks and channels need not enable full. Derive/procedural macros can simplify source while adding build work. A no_std claim must cover the enabled features and transitive dependencies, not just the crate's headline description.

Three example compositions:

- A CLI processing a handful of files can start with sequential or scoped-thread work; a large independent transformation can justify Rayon without adding an async runtime.
- A network service can use Tokio for sockets/timers and a bounded CPU bridge for expensive transforms. The CPU pool does not replace the network runtime, and request cancellation does not automatically stop submitted computation.
- A library used on host and firmware can keep a core API over slices, make allocation an explicit capability, and leave runtime/HAL integration to adapters. A portability trait is useful when it has real consumers and a precise contract.

These comparisons explain fit and cost; they do not rank every candidate on one speed scale. See [execution examples](async-and-parallel-execution.md) for the ownership and resource boundaries of the compositions.
