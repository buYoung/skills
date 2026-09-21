# Performance

## Contents

- [Choose the Performance Objective](#choose-the-performance-objective)
- [From Mechanism to Measurement](#from-mechanism-to-measurement)
- [Confirm the Build](#confirm-the-build)
- [Benchmarking](#benchmarking)
- [Profiling](#profiling)
- [Interpret an Observation Before Choosing a Change](#interpret-an-observation-before-choosing-a-change)
- [Algorithms and Data Structures First](#algorithms-and-data-structures-first)
- [Allocation](#allocation)
- [Cloning and Sharing](#cloning-and-sharing)
- [Type Sizes and Layout](#type-sizes-and-layout)
- [Iterators](#iterators)
- [Bounds Checks](#bounds-checks)
- [I/O](#io)
- [Logging and Assertions](#logging-and-assertions)
- [Inlining](#inlining)
- [Wrapper Types](#wrapper-types)
- [Parallelism](#parallelism)
- [Compile Times](#compile-times)
- [Clippy Performance Lints](#clippy-performance-lints)
- [Reporting Results](#reporting-results)
- [Common Mistakes](#common-mistakes)
- [Availability by Version](#availability-by-version)
- [Practical Boundaries](#practical-boundaries)

Examples use stable APIs unless marked otherwise; see [compatibility](../../SKILL.md#compatibility). Blocks marked `ignore` need a crate. Compiler and profile settings are in [build configuration](build-configuration.md); container choice in [collections](collections.md); lock contention in [concurrency](concurrency.md).

## Choose the Performance Objective

State whether the goal is throughput, tail latency, peak/retained memory, startup, binary size, or build time. Explain the suspected cost and a useful first change without claiming an unmeasured improvement. Optimization choices can improve one metric and worsen another. Allocation strategy is in [memory and allocation](memory-and-allocation.md); data-level vectorization in [SIMD](simd.md); target boundaries in [Wasm](webassembly.md) and [embedded](embedded-and-no-std.md).

## From Mechanism to Measurement

A performance explanation connects a suspected cost to observable work: repeated hashing, allocation, cache misses, lock waits, copies, or generated code. A profile can locate where that work matters; a benchmark compares the relevant objective under equivalent conditions.

Algorithm and representation changes often have the largest effect, while allocation, layout, I/O, dispatch, and compiler settings expose more specific trade-offs. This is a useful order of investigation, not a required edit sequence. The deployed configuration is the baseline, including intentional safety checks and diagnostic support. Evaluate a change against its actual objective rather than assuming every successful optimization must improve every metric.

Prioritize costs that dominate the chosen objective. Algorithmic work, repeated conversions, and avoidable I/O often offer clearer gains than instruction-level changes; combine profiling with representative measurements to identify which mechanism matters.

## Confirm the Build

Measure the intended deployment profile. By default, `cargo run` uses the dev profile and `cargo test` uses the test profile, which inherits dev settings. These normally disable optimization and enable debug assertions and overflow checks, so their timings do not represent a release build.

```rust
fn assert_release_build() {
    if cfg!(debug_assertions) {
        eprintln!("warning: running a debug build; timings are not representative");
    }
}
```

Check `cargo build --release -v` for the flags actually passed, and `cargo build --timings` for where build time goes. A benchmark harness must also run in release mode (`cargo bench` does; a hand-written `main` does only with `--release`).

## Benchmarking

| Tool | Scope | Notes |
|---|---|---|
| `criterion` (crate) | Functions and small operations | Statistical analysis, warm-up, outlier detection, HTML reports; suitable for comparing small operations |
| `divan` (crate) | Functions | Lighter setup, similar goals |
| `hyperfine` | Whole programs | Repeated runs with warm-up and statistics; compare two binaries side by side |
| Built-in `#[bench]` | Nightly only | Hard error on stable since 1.88 without `custom_test_frameworks` |

Keep inputs and outputs alive with `std::hint::black_box`, otherwise the optimizer removes the work you are timing.

```rust
use std::hint::black_box;
use std::time::{Duration, Instant};

fn checksum(data: &[u8]) -> u32 {
    data.iter().fold(0u32, |acc, &b| acc.wrapping_mul(31).wrapping_add(u32::from(b)))
}

fn time_checksum(data: &[u8], iterations: u32) -> Duration {
    let start = Instant::now();
    for _ in 0..iterations {
        black_box(checksum(black_box(data)));
    }
    start.elapsed() / iterations
}
```

```rust,ignore
use criterion::{criterion_group, criterion_main, Criterion};

fn bench_checksum(c: &mut Criterion) {
    let data = vec![7u8; 64 * 1024];
    c.bench_function("checksum 64 KiB", |b| b.iter(|| checksum(std::hint::black_box(&data))));
}

criterion_group!(benches, bench_checksum);
criterion_main!(benches);
```

Rules: same machine, same inputs, several runs, report the spread; benchmark the change in isolation; run correctness tests in the release profile too, because overflow checks and debug assertions are off there.

## Profiling

| Tool | Platform | Measures |
|---|---|---|
| `perf` with Hotspot or Firefox Profiler | Linux | CPU samples, hardware counters |
| `samply` | Linux, macOS, Windows | CPU samples, Firefox Profiler UI |
| Instruments | macOS | CPU, allocations, system calls |
| Intel VTune, AMD uProf | Linux, Windows | CPU, microarchitecture counters |
| `cargo flamegraph` | Linux, DTrace platforms | Flame graphs from `perf`/DTrace |
| Cachegrind, Callgrind | Linux | Instruction counts, simulated cache and branch behavior; deterministic |
| DHAT, `heaptrack`, `bytehound` | Linux | Heap allocations: count, size, lifetime, hot allocation sites |
| `counts` | any | Ad hoc counting of `eprintln!` output |

Give the profiled binary symbols and line tables without giving up optimization:

```toml
[profile.profiling]
inherits = "release"
debug = "line-tables-only"
strip = "none"
```

Build with `RUSTFLAGS="-C force-frame-pointers=yes" cargo build --profile profiling` when the profiler unwinds through frame pointers. Since 1.97 the default v0 symbol mangling produces readable names; on older toolchains add `-C symbol-mangling-version=v0`. Inlined functions disappear from call graphs; `#[inline(never)]` on a suspect function makes it visible temporarily.

## Interpret an Observation Before Choosing a Change

A tool output identifies activity, not its cause by itself. Connect the observation to a mechanism and a comparison that can distinguish competing explanations:

| Observation | Possible mechanism | Useful comparison and candidate |
|---|---|---|
| Runtime grows much faster than input size | Repeated scans, sorting, or copies | Compare operation counts/scaling; change the algorithm or representation before instruction tuning |
| Many allocations of similarly sized temporary objects | Rebuilt buffers or intermediate collections | Count allocations and peak live bytes; try streaming or bounded reuse while tracking retained capacity |
| RSS remains high after work finishes | Retained capacity or allocator pages, possibly a leak | Compare live allocations with process memory; releasing a Vec does not promise an RSS decrease |
| CPU use is low while latency grows | I/O wait, synchronization, or admission queues | Separate waiting from on-CPU time; narrow a lock or change queue ownership only when that is the cause |
| More threads stop improving throughput | Bandwidth, contention, quotas, or oversubscription | Sweep worker count and data size; more concurrency can increase tail latency |
| An intrinsic kernel wins alone but the application does not | Conversion, dispatch, or another stage dominates | Time the complete input-to-output path, including layout conversion and boundary copies |
| Clean builds improve while small edits get slower | Changed crate graph, generics, codegen units, or LTO | Compare clean and incremental timings separately; there is no single build-time metric |

For example, an allocation profile showing a temporary Vec per message suggests two different experiments: reuse a bounded scratch buffer or process without materializing the intermediate. Reuse can reduce allocator traffic while retaining a large buffer; streaming can reduce memory while complicating a consumer that needs random access. Measure the intended workload and keep the semantic requirement explicit.

Changing several mechanisms at once makes attribution difficult. Hold input, target, compiler, profile, and relevant concurrency limits constant for a comparison. Include cold-start behavior when the product cares about it; a warmed microbenchmark can hide initialization, code-page, and allocator costs. Report variability rather than treating one favorable run as a stable result.

## Algorithms and Data Structures First

Before touching allocation or layout, check the complexity of the hot path: a `Vec::contains` inside a loop (O(n²)) becomes a `HashSet` lookup; repeated sorting becomes a `BTreeMap`; a `LinkedList` becomes a `Vec`; `Vec::remove(0)` in a loop becomes `VecDeque::pop_front`. See [collections](collections.md) for the selection rules and cost table. Caching a small, high-locality lookup in front of a large structure and handling the common case before the general case can reduce repeated work, at the cost of additional state and invalidation rules.

## Allocation

Heap allocation can add allocator and memory-traffic costs; growth may reallocate and move contents. Measure the actual path, including retained capacity and allocation elimination. Reuse and reservation are useful candidates, not guarantees. See [memory and allocation](memory-and-allocation.md) for arenas, pools, failure handling, and allocator choice.

```rust
use std::fmt::Write as _;

fn render_csv(rows: &[(u32, &str)]) -> String {
    let mut out = String::with_capacity(rows.len() * 16);
    for (id, name) in rows {
        // write! appends to the existing buffer; format! per row would allocate a String each time.
        writeln!(out, "{id},{name}").expect("writing to a String cannot fail");
    }
    out
}

fn tokenize_all(lines: &[&str]) -> usize {
    let mut tokens: Vec<&str> = Vec::new();
    let mut total = 0;
    for line in lines {
        tokens.clear(); // capacity survives; no allocation after the first big line
        tokens.extend(line.split_whitespace());
        total += tokens.len();
    }
    total
}

fn collect_ids(records: &[(u32, bool)]) -> Vec<u32> {
    let mut ids = Vec::with_capacity(records.len());
    ids.extend(records.iter().filter(|(_, active)| *active).map(|(id, _)| *id));
    ids
}
```

- `Vec::with_capacity` when the count is known or bounded; `extend` into an existing collection instead of `collect` into a new one.
- `String` building with `write!`/`push_str`; `format!` only when a fresh `String` is the result. Since 1.98, `<{integer}>::format_into` formats integers into a stack buffer without dynamic dispatch.
- `Cow<'_, str>` returns borrowed input unchanged and allocates only for the modified case (see [ownership and type design](ownership-and-type-design.md#cow-for-sometimes-owned-data)).
- `Box<[T]>` instead of `Vec<T>` for frozen data drops the capacity word; `Box<str>` and `Arc<str>` do the same for strings.
- Eligible inline-storage choices such as smallvec can help mostly tiny sequences; fixed-capacity heapless storage serves bounded environments. Distinguish heap spill from a full-capacity error and account for containing-object size. See [library selection](library-selection.md).
- Allocator changes affect the final program globally; follow [allocator selection](memory-and-allocation.md#allocator-selection) and measure both latency and memory rather than recommending a wrapper by name.

Find allocation hot spots with DHAT or `heaptrack` before rewriting; the allocation you assume is hot is often not the one the profiler shows.

## Cloning and Sharing

A `clone()` of a `String`, `Vec`, or large struct on a hot path copies memory; a clone of `Rc`/`Arc` is a counter increment. Share immutable data instead of copying it.

```rust
use std::collections::HashMap;
use std::sync::Arc;

struct Interner {
    strings: HashMap<Arc<str>, u32>,
}

impl Interner {
    /// Returns a shared handle; callers store the cheap `Arc<str>` instead of cloning the text.
    fn intern(&mut self, text: &str) -> Arc<str> {
        if let Some((existing, _)) = self.strings.get_key_value(text) {
            return Arc::clone(existing);
        }
        let shared: Arc<str> = Arc::from(text);
        let id = u32::try_from(self.strings.len()).expect("interner capacity");
        self.strings.insert(Arc::clone(&shared), id);
        shared
    }
}
```

Look for `clone()` calls that exist to satisfy the borrow checker (see [ownership and type design](ownership-and-type-design.md#clones-deliberate-not-defensive)), `to_string()` or `to_owned()` used only to compare (Clippy `cmp_owned`, perf), and `iter().cloned()` before a `filter` that discards most items (Clippy `iter_overeager_cloned`, perf). Clippy `redundant_clone` (nursery, opt-in) finds clones of values dropped immediately.

## Type Sizes and Layout

Smaller types mean fewer cache lines and cheaper moves. The compiler reorders struct fields to minimize padding unless `#[repr(C)]` is used, so manual field ordering is unnecessary; enum size, however, is set by the largest variant.

```rust
use std::mem::size_of;

enum MessageBloated {
    Ping,
    Data([u8; 1024]), // every Ping is 1 KiB wide
}

enum Message {
    Ping,
    Data(Box<[u8; 1024]>), // rare large payload boxed: the enum is one word
}

const _: () = assert!(size_of::<Message>() <= 16);

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn message_stays_small() {
        assert!(size_of::<Message>() <= 16);
        assert!(size_of::<MessageBloated>() > 1024);
    }
}
```

- Boxing a rare large variant can shrink the enum and improve storage density, while adding an allocation and indirection for that variant. Compare the actual variant distribution and access pattern.
- `size_of::<T>()` in a test pins the size so a later field addition is noticed; `-Zprint-type-sizes` on nightly prints every type's layout and padding.
- `Option<Box<T>>`, `Option<&T>`, and `Option<NonZeroU32>` cost nothing extra (niche optimization); Option<u32> needs a separate absence representation and is commonly larger; inspect size_of on the actual target instead of treating an enum layout as a general ABI guarantee.
- Large arrays on the stack (`[u8; 1 << 20]`) risk stack overflow in threads with default stacks; Clippy `large_stack_arrays` and `large_stack_frames` (pedantic/nursery) flag them.
- Clippy `large_enum_variant` (perf) and `result_large_err` (perf) report the two most common cases.

## Iterators

Iterator chains can optimize into loops with eliminated bounds checks, but that is a compiler result rather than an Iterator contract. Fusion, inlining, aliasing, target features, and the operation itself affect the result. Avoid an intermediate Vec when the consumer can use the iterator directly; inspect generated code for a hot-path performance claim.

```rust
fn even_squares(values: &[u32]) -> impl Iterator<Item = u32> + '_ {
    values.iter().copied().filter(|v| v % 2 == 0).map(|v| v * v)
}

fn parse_valid<'a>(lines: &'a [&'a str]) -> impl Iterator<Item = u32> + 'a {
    lines.iter().filter_map(|line| line.parse().ok()) // one pass instead of filter + map
}

fn sum_le_u16(bytes: &[u8]) -> u32 {
    let chunks = bytes.chunks_exact(2); // fixed-size chunks let the compiler drop per-index checks
    let mut total: u32 = chunks.clone().map(|c| u32::from(u16::from_le_bytes([c[0], c[1]]))).sum();
    if let [last] = chunks.remainder() {
        total += u32::from(*last);
    }
    total
}

struct Countdown(u32);

impl Iterator for Countdown {
    type Item = u32;

    fn next(&mut self) -> Option<u32> {
        if self.0 == 0 {
            None
        } else {
            self.0 -= 1;
            Some(self.0 + 1)
        }
    }

    /// An exact size hint can help consumers reserve capacity; allocation is consumer-specific.
    fn size_hint(&self) -> (usize, Option<usize>) {
        (self.0 as usize, Some(self.0 as usize))
    }
}

impl ExactSizeIterator for Countdown {}
```

- `filter_map` over `filter().map()`; `copied()` over `cloned()` for `Copy` items; `chunks_exact` over `chunks` when the remainder is handled separately.
- Iterator adapters introduce different control flow. zip bounds iteration by the shorter input; an equal-length contract can expose further optimization opportunities, but neither syntax guarantees a particular machine-code sequence.
- Return `impl Iterator<Item = T>` when the caller will iterate; collect only when the caller needs a collection.
- Implement `size_hint` (and `ExactSizeIterator` when exact) on custom iterators.
- Floating-point reductions have numerical-order constraints; neither explicit SIMD nor Rayon permits silently changing required results. Element-wise loops/iterators can auto-vectorize. See [SIMD](simd.md).

## Bounds Checks

Indexing requires an in-bounds access; the optimizer can remove checks it proves unnecessary. Iterators, constrained slices, and an assertion at the boundary can expose that information. Keep the input and numerical contracts the same when comparing formulations.

```rust
fn dot_indexed(a: &[f32], b: &[f32]) -> f32 {
    assert_eq!(a.len(), b.len()); // one check; the loop below is then provably in bounds
    let n = a.len();
    let (a, b) = (&a[..n], &b[..n]);
    let mut sum = 0.0;
    for i in 0..n {
        sum += a[i] * b[i];
    }
    sum
}

fn dot_iter(a: &[f32], b: &[f32]) -> f32 {
    assert_eq!(a.len(), b.len()); // zip alone would silently truncate
    a.iter().zip(b).fold(0.0, |sum, (x, y)| sum + x * y)
}
```

Both functions reject unequal lengths and use the same accumulation order and initial value. The iterator form avoids explicit indexing, but its generated branches and vectorization still depend on the compiler and target. Inspect the emitted code before assuming either form removes a bottleneck.

`get_unchecked` requires an in-range index even when the result is not subsequently used. Consider it only when a measured bottleneck remains and the invariant can be maintained at every call. Miri can expose invalid operations on executed paths; passing a run does not replace the safety argument or establish a performance benefit.

## I/O

Repeated small, unbuffered file operations can spend substantial time in system calls. Buffering groups logical operations into larger transfers; the Read/Write traits themselves do not promise one system call per method. `print!`/`println!` acquire stdout's lock per call, so repeated output can benefit from holding a lock explicitly.

```rust
use std::io::{self, BufRead, BufReader, BufWriter, Write};
use std::path::Path;

fn count_error_lines(path: &Path) -> io::Result<usize> {
    let mut reader = BufReader::new(std::fs::File::open(path)?);
    let mut line = String::new();
    let mut count = 0;
    loop {
        line.clear(); // reuse one buffer; `lines()` would allocate a String per line
        if reader.read_line(&mut line)? == 0 {
            break;
        }
        if line.contains("ERROR") {
            count += 1;
        }
    }
    Ok(count)
}

fn write_report(path: &Path, rows: &[String]) -> io::Result<()> {
    let mut writer = BufWriter::new(std::fs::File::create(path)?);
    for row in rows {
        writer.write_all(row.as_bytes())?;
        writer.write_all(b"\n")?;
    }
    writer.flush() // explicit: an error during the implicit flush on Drop is silently dropped
}

fn print_lines(lines: &[String]) -> io::Result<()> {
    let stdout = io::stdout();
    let mut out = stdout.lock(); // one lock for the loop instead of one per println!
    for line in lines {
        writeln!(out, "{line}")?;
    }
    Ok(())
}
```

`BufReader::with_capacity` tunes the buffer for large sequential reads; `read_to_end` into a pre-sized `Vec` beats many small reads. Clippy `unbuffered_bytes` (perf) flags `Read::bytes()` on an unbuffered reader.

## Logging and Assertions

Logging that is disabled must cost nothing: gate the construction of the message, not just its emission.

```rust
#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
enum Level {
    Error,
    Info,
    Debug,
}

struct Logger {
    level: Level,
}

impl Logger {
    fn debug(&self, build_message: impl FnOnce() -> String) {
        if self.level >= Level::Debug {
            eprintln!("{}", build_message()); // the String exists only when it will be printed
        }
    }
}

fn hot_path(logger: &Logger, items: &[u64]) -> u64 {
    debug_assert!(items.iter().all(|&i| i < 1_000_000), "items must be pre-validated");
    logger.debug(|| format!("processing {} items: {items:?}", items.len()));
    items.iter().sum()
}
```

The `log` and `tracing` crates do this gating inside their macros; the message arguments are still evaluated only if the level is enabled. `assert!` runs in every build; `debug_assert!` only when `debug_assertions` is on. Keep assertions that guard memory safety or data integrity as `assert!`; downgrade hot, expensive sanity checks to `debug_assert!`.

## Inlining

| Attribute | Effect |
|---|---|
| none | The compiler decides, based on size, optimization level, and whether the function is generic or crate-local |
| `#[inline]` | A hint that also makes the function's body available to other crates without LTO |
| `#[inline(always)]` | A strong hint; reserve for tiny wrappers where the call is measurably hot |
| `#[inline(never)]` | Keeps a cold or large function out of callers; also makes it visible in profiles |
| `#[cold]` | Marks a function as rarely called, moving it out of the hot path's code layout |

Cross-crate inlining depends on body availability, compiler heuristics, attributes, generic instantiation, and LTO. Do not assume every crate boundary prevents inlining without LTO. Inlining "can also affect compile times, especially cross-crate inlining", so add attributes where a profile shows the call, not everywhere. `std::hint::cold_path` (1.95) marks an unlikely branch inside a function.

## Wrapper Types

Interior-mutability and synchronization wrappers have different costs: RefCell checks borrowing at runtime, locks acquire access, and atomics constrain concurrent operations according to their ordering. Grouping fields behind one wrapper can reduce repeated checks or lock acquisitions when they are accessed together, but can also enlarge a critical section. Cell needs no borrow flag for get/set-style access; the value and access pattern determine whether it fits.

## Parallelism

Identify enough independent work and the limiting resource before parallelizing. A hot CPU kernel can be a good candidate without first eliminating every scalar inefficiency. Splitting overhead, shared locks/atomics, quotas, and memory bandwidth can limit the gain.

Choose the tool by the shape of the work:

| Work shape | Tool |
|---|---|
| Split a slice or collection, reduce results, done before returning | `std::thread::scope` (no dependency) or `rayon` when work per item is uneven or the split is recursive |
| Many independent CPU tasks over time | `rayon::ThreadPool` or a `std` pool fed by a bounded channel |
| Stages that hand data forward | `std::sync::mpsc::sync_channel` (one consumer) or `crossbeam-channel` (many consumers, `select!`) |
| Many operations waiting on I/O | An async runtime (`tokio`), with CPU work moved to `spawn_blocking` or a `rayon` pool |
| Vectorizable inner loops | Compare scalar/auto-vectorized code, an eligible optimized operation, and supported core::arch intrinsics; see [SIMD](simd.md) for safety, dispatch, and stability |

```rust,deps
use rayon::prelude::*;

fn total_len(docs: &[String]) -> usize {
    docs.par_iter().map(|doc| doc.len()).sum()
}

fn checksums(blocks: &[Vec<u8>]) -> Vec<u32> {
    blocks
        .par_iter()
        .with_min_len(64) // avoid splitting tiny batches: per-task overhead dominates small inputs
        .map(|block| block.iter().fold(0u32, |acc, &b| acc.wrapping_mul(31).wrapping_add(u32::from(b))))
        .collect()
}
```

Rules: measure the parallel version against the serial one at the real input size, because splitting overhead makes small inputs slower; keep blocking I/O out of compute pools; expect floating-point reductions to change association order and therefore results. The full selection table for `rayon`, `crossbeam`, async runtimes, sharded maps, and lock replacements is in [concurrency: choosing a parallelism library](concurrency.md#choosing-a-parallelism-library); contention rules are in the same reference.

## Compile Times

- `cargo build --timings` renders a chart of crate compilation; crates on the critical path that block others are the ones to split or slim.
- `cargo llvm-lines` (crate) lists which functions generate the most LLVM IR; generic functions instantiated many times dominate. Move the non-generic body into an inner function:

```rust
use std::path::Path;

pub fn read_config(path: impl AsRef<Path>) -> std::io::Result<String> {
    // The generic shell is tiny and instantiated per caller type; the body compiles once.
    fn inner(path: &Path) -> std::io::Result<String> {
        std::fs::read_to_string(path)
    }
    inner(path.as_ref())
}
```

- Replace heavily instantiated generic helpers (`Option::map` with distinct closure types in a macro) with `match` where a macro expands thousands of times; `cargo expand` shows the generated code and `-Zmacro-stats` (nightly) counts it.
- Profile settings that cut compile time (`debug = false` or `"line-tables-only"` in dev, `codegen-units`, faster linkers, `build.build-dir`) are in [build configuration](build-configuration.md#faster-development-builds).
- `cargo check` for the edit loop; a full build only when running.

## Clippy Performance Lints

The `perf` group is warn-by-default and catches the common slowdowns without a profiler:

| Lint | Catches |
|---|---|
| `large_enum_variant` | An enum whose variants differ greatly in size |
| `result_large_err` | `Result` with a large `Err` type (default threshold 128 bytes) |
| `box_collection`, `boxed_local`, `redundant_allocation` | `Box<Vec<T>>`, boxing a local that never escapes, `Rc<Box<T>>`-style double indirection |
| `cmp_owned` | `to_string()`/`to_owned()` only to compare |
| `expect_fun_call`, `or_fun_call` (nursery) | Eager evaluation of `expect(format!(..))` and `unwrap_or(expensive())` |
| `map_entry` | `contains_key` followed by `insert` |
| `slow_vector_initialization`, `vec_init_then_push`, `useless_vec` | `Vec::new()` plus `resize`, pushes right after creation, `vec![]` where a slice works |
| `manual_memcpy` | Element-by-element copy loops instead of `copy_from_slice` |
| `unnecessary_to_owned` | Cloning to pass a value where a borrow works |
| `iter_overeager_cloned` | `cloned()` before a filtering adapter |
| `drain_collect`, `extend_with_drain` | `drain(..).collect()` instead of `mem::take`, `extend(v.drain(..))` instead of `append` |
| `regex_creation_in_loops` | Compiling a regex inside a loop |
| `readonly_write_lock` | `RwLock::write` guard used only for reading |
| `unbuffered_bytes` | `bytes()` on an unbuffered reader |
| `missing_spin_loop` | Busy-wait loops without `spin_loop()` |
| `waker_clone_wake` | Cloning a `Waker` only to call `wake()` |

`redundant_clone`, `needless_collect`, and `or_fun_call` live in the nursery group because of false positives; enable them selectively and assess the semantics of each suggestion.

## Reporting Results

State the metric, the baseline, the new measurement, the variance, the machine, and the profile; "should be faster" is a hypothesis, not a result. Run the correctness tests in the same profile as the benchmark, because a change that speeds up a wrong answer is a regression. Keep the before and after profiles with the change so the next reader can see what moved.

## Common Mistakes

- Measuring a `dev` build, or a `release` build with `debug-assertions = true` left in a custom profile.
- Optimizing a function the profiler never showed.
- Replacing `HashMap` with a faster hasher on untrusted keys (HashDoS).
- Adding `#[inline(always)]` everywhere, which bloats code and slows compilation without measured benefit.
- `collect()` into a `Vec` to call `.len()` or iterate once more.
- Switching to `parking_lot`, `rayon`, or a custom allocator without a before/after benchmark on the real workload.
- Using `unsafe` (`get_unchecked`, `transmute`) for speed before trying iterators and slicing, or without Miri coverage.
- Reporting a speedup from a single run.

## Availability by Version

| Version | Addition |
|---|---|
| 1.81 | New sort implementations (may panic on an inconsistent `Ord`) |
| 1.82 | `<[T]>::is_sorted` |
| 1.87 | Most `std::arch` intrinsics callable from safe code when the target feature is enabled |
| 1.88 | `hint::select_unpredictable`; `<[T]>::as_chunks` |
| 1.90 | `lld` default linker on `x86_64-unknown-linux-gnu` (faster links) |
| 1.94 | `<[T]>::array_windows` |
| 1.95 | `hint::cold_path`; `Vec::push_mut` |
| 1.97 | v0 symbol mangling default (readable profiles without extra flags) |
| 1.98 | `<{integer}>::format_into`; algebraic float operations (`algebraic_add` and friends allow reassociation, not bit-exact) |

Per-release details live in [the versions index](../versions/index.md).

## Practical Boundaries

A useful comparison measures the objective that matters under equivalent workloads and build settings. Faster throughput can cost latency, memory, startup, or compilation time. Representative inputs, repeated runs, and environment details make the result interpretable.

Algorithms and data representation often dominate; allocation, layout, dispatch, I/O, and code generation explain other costs. Iterators and direct loops can both optimize well. Buffer reuse, inlining, parallelism, and unsafe fast paths each have conditions and competing costs, so they are mechanisms to evaluate rather than universal improvements. Preserve required validation and safety checks while changing the implementation.
