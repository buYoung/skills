# Guideline Redesign and Research Record (2026-09-21)

## Scope

Reorganized the guide around conditional engineering decisions. Added dedicated routing and references for library selection, async/parallel execution, allocation, module/crate boundaries, workspaces/monorepos, WebAssembly, embedded/no_std, and SIMD. Existing language/API material remains available by topic.

Corrected error-erasure claims, universal error-enum/bounds rules, future versus handle cancellation, std-only runtime assumptions, MSRV resolution guarantees, workspace/version assumptions, and several ownership/allocation generalizations. Edition-2024 examples no longer claim Rust 1.80 compatibility.

This record describes this revision only. The 2026-09-18 compilation record is historical and does not validate changed examples.

## Adoption Snapshot

Public metadata was read from `https://crates.io/api/v1/crates/<name>` and `https://api.github.com/repos/<owner>/<repository>`. Downloads below are the API's recent_downloads field (90 days); stars are repository-wide. Monorepo stars must not be interpreted as package-specific adoption. Counts include transitive/CI downloads, not unique users.

The editorial floor is 1,000 stars AND 100,000 recent downloads, with no announced discontinuation/archive. This is a selection filter, not a safety or quality certification. Relevance and maintenance still determine whether an eligible package should be recommended. Existing dependencies are not banned by this rule.

### Execution and Platform Candidates

| Package | Repository stars | Recent downloads | Decision |
|---|---:|---:|---|
| [tokio](https://crates.io/crates/tokio) | [33195](https://github.com/tokio-rs/tokio) | 227687041 | Primary |
| [smol](https://crates.io/crates/smol) | [5070](https://github.com/smol-rs/smol) | 4930533 | Primary |
| [rayon](https://crates.io/crates/rayon) | [13325](https://github.com/rayon-rs/rayon) | 123723743 | Primary |
| [crossbeam-channel](https://crates.io/crates/crossbeam-channel) | [8582](https://github.com/crossbeam-rs/crossbeam) | 116468326 | Primary |
| [futures](https://crates.io/crates/futures) | [5927](https://github.com/rust-lang/futures-rs) | 171486805 | Primary |
| [flume](https://crates.io/crates/flume) | [3074](https://github.com/zesterer/flume) | 54506964 | Primary |
| [wasm-bindgen-futures](https://crates.io/crates/wasm-bindgen-futures) | [9153](https://github.com/wasm-bindgen/wasm-bindgen) | 82128669 | Wasm only |
| [embassy-executor](https://crates.io/crates/embassy-executor) | [9862](https://github.com/embassy-rs/embassy) | 769738 | Embedded only |
| [futures-lite](https://crates.io/crates/futures-lite) | [545](https://github.com/smol-rs/futures-lite) | 54998640 | Below star floor |
| [futures-concurrency](https://crates.io/crates/futures-concurrency) | [501](https://github.com/yoshuawuyts/futures-concurrency) | 4696755 | Below star floor |
| [async-channel](https://crates.io/crates/async-channel) | [948](https://github.com/smol-rs/async-channel) | 63835439 | Below star floor |
| [async-executor](https://crates.io/crates/async-executor) | [459](https://github.com/smol-rs/async-executor) | 31890225 | Below star floor |
| [async-io](https://crates.io/crates/async-io) | [615](https://github.com/smol-rs/async-io) | 39696504 | Below star floor |
| [monoio](https://crates.io/crates/monoio) | [5113](https://github.com/monoio-rs/monoio) | 510061 | Explicit specialized requirement only |
| [compio](https://crates.io/crates/compio) | [1892](https://github.com/compio-rs/compio) | 443905 | Explicit specialized requirement only |
| [tokio-uring](https://crates.io/crates/tokio-uring) | [1498](https://github.com/tokio-rs/tokio-uring) | 1059860 | Specialized; recheck maintenance before adoption |
| [glommio](https://crates.io/crates/glommio) | [3657](https://github.com/DataDog/glommio) | 24657 | Below recent-download floor |

async-std is excluded for new adoption because its [official documentation](https://docs.rs/async-std/) announces discontinuation and recommends smol. It is not excluded on an invented popularity count.

### Additional Topic Audit

| Package | Repository stars | Recent downloads | Decision |
|---|---:|---:|---|
| [thiserror](https://crates.io/crates/thiserror) | [5551](https://github.com/dtolnay/thiserror) | 367583482 | Eligible for a relevant topic |
| [anyhow](https://crates.io/crates/anyhow) | [6656](https://github.com/dtolnay/anyhow) | 214973643 | Eligible for a relevant topic |
| [mimalloc](https://crates.io/crates/mimalloc) | [833](https://github.com/purpleprotocol/mimalloc_rust) | 15878807 | Below star floor |
| [tikv-jemallocator](https://crates.io/crates/tikv-jemallocator) | [545](https://github.com/tikv/jemallocator) | 20640469 | Below star floor |
| [smallvec](https://crates.io/crates/smallvec) | [1735](https://github.com/servo/rust-smallvec) | 282273859 | Eligible for a relevant topic |
| [arrayvec](https://crates.io/crates/arrayvec) | [907](https://github.com/bluss/arrayvec) | 127500310 | Below star floor |
| [heapless](https://crates.io/crates/heapless) | [2022](https://github.com/rust-embedded/heapless) | 43606340 | Eligible for a relevant topic |
| [embedded-hal](https://crates.io/crates/embedded-hal) | [2652](https://github.com/rust-embedded/embedded-hal) | 5262225 | Eligible for a relevant topic |
| [critical-section](https://crates.io/crates/critical-section) | [173](https://github.com/rust-embedded/critical-section) | 33183857 | Below star floor |
| [portable-atomic](https://crates.io/crates/portable-atomic) | [252](https://github.com/taiki-e/portable-atomic) | 134840155 | Below star floor |
| [wide](https://crates.io/crates/wide) | [553](https://github.com/Lokathor/wide) | 17680534 | Below star floor |
| [pulp](https://crates.io/crates/pulp) | [365](https://github.com/sarah-quinones/pulp/) | 11253365 | Below star floor |
| [memchr](https://crates.io/crates/memchr) | [1563](https://github.com/BurntSushi/memchr) | 356873670 | Eligible for a relevant topic |
| [parking_lot](https://crates.io/crates/parking_lot) | [3411](https://github.com/Amanieu/parking_lot) | 215896704 | Eligible for a relevant topic |
| [arc-swap](https://crates.io/crates/arc-swap) | [1415](https://github.com/vorner/arc-swap) | 83623701 | Eligible for a relevant topic |
| [dashmap](https://crates.io/crates/dashmap) | [4115](https://github.com/xacrimon/dashmap) | 82887479 | Eligible for a relevant topic |
| [serde](https://crates.io/crates/serde) | [10829](https://github.com/serde-rs/serde) | 313522518 | Eligible for a relevant topic |
| [loom](https://crates.io/crates/loom) | [2824](https://github.com/tokio-rs/loom) | 13841329 | Eligible for a relevant topic |

The APIs reported the repositories above as not archived when queried. Repository activity and published release dates are different signals; no claim was made that every dependency has undergone a security or issue-triage audit.

## Technical Sources

Sources used for the topic references:
- [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/flexibility.html), [Error](https://doc.rust-lang.org/std/error/trait.Error.html), [thiserror](https://docs.rs/thiserror/), [anyhow](https://docs.rs/anyhow/).
- [Cargo workspaces](https://doc.rust-lang.org/cargo/reference/workspaces.html), [feature/MSRV resolution](https://doc.rust-lang.org/cargo/reference/resolver.html), [dependency locations](https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html#multiple-locations), [profiles](https://doc.rust-lang.org/cargo/reference/profiles.html).
- [Tokio task cancellation](https://docs.rs/tokio/latest/tokio/task/struct.JoinHandle.html), [blocking work](https://docs.rs/tokio/latest/tokio/task/fn.spawn_blocking.html), [JoinSet](https://docs.rs/tokio/latest/tokio/task/struct.JoinSet.html), [select](https://docs.rs/tokio/latest/tokio/macro.select.html), [shutdown](https://tokio.rs/tokio/topics/shutdown).
- [Vec](https://doc.rust-lang.org/std/vec/struct.Vec.html), [allocation](https://doc.rust-lang.org/std/alloc/index.html), [visibility](https://doc.rust-lang.org/reference/visibility-and-privacy.html), [codegen attributes](https://doc.rust-lang.org/reference/attributes/codegen.html).
- [Embedded environment](https://doc.rust-lang.org/embedded-book/intro/no-std.html), [embedded concurrency](https://docs.rust-embedded.org/book/concurrency/index.html), [volatile access](https://doc.rust-lang.org/core/ptr/fn.read_volatile.html), [Embassy](https://docs.embassy.dev/embassy-executor/), [heapless](https://docs.rs/heapless/), [embedded-hal](https://docs.rs/embedded-hal/).
- [Wasm target](https://doc.rust-lang.org/rustc/platform-support/wasm32-unknown-unknown.html), [wasm-bindgen views](https://wasm-bindgen.github.io/wasm-bindgen/api/js_sys/struct.Uint8Array.html#method.view), [memory growth](https://developer.mozilla.org/en-US/docs/WebAssembly/Reference/JavaScript_interface/Memory/grow), [shared memory](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/SharedArrayBuffer).
- [core::arch](https://doc.rust-lang.org/core/arch/index.html), [core::simd](https://doc.rust-lang.org/core/simd/index.html), [memchr](https://docs.rs/memchr/).

## Verification

Performed locally with rustc 1.95.0 and Cargo 1.95.0:

- Frontmatter: YAML parsed successfully with the installed Ruby YAML parser, then checked against the skill-creator field/name/description constraints; description length is 892 characters. The original quick_validate.py could not run under python3 because PyYAML was not installed. No new dependency was installed to work around that limitation.
- Sixteen std/core Rust blocks from the allocation, module-boundary, embedded, SIMD, and error references compiled as libraries with edition 2024 and --emit=metadata. This includes the corrected error line context.
- Three dependency-backed blocks from error handling and async execution passed cargo check --offline in a temporary crate with Tokio 1.53.1 (rt only), thiserror 2.0.20, and anyhow 1.0.104.
- The three example workspace manifests were assembled with minimal temporary Rust targets. Both cargo check --offline --workspace and the isolated engine package with --no-default-features passed. These checks validate manifest inheritance and host compilation, not an actual firmware build.
- Local Markdown links/anchors, fence pairing, evaluation JSON shape/unique IDs, and git diff --check were checked after editing. There are 16 prompt scenarios; no scenario is reported as an executed model evaluation.

All compilation scaffolding was temporary and is not part of the package. No comparative model benchmark, runtime cancellation/memory stress run, SIMD performance measurement, browser/engine execution, bare-metal cross-build, or hardware test was performed. No claim is made that all unchanged historical examples or every supported MSRV were recompiled. Source/API checks establish the documented contract, not workload performance.
