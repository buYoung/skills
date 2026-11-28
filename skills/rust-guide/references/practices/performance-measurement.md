# Performance Measurement

## Contents

- [Choose the Performance Objective](#choose-the-performance-objective)
- [From Mechanism to Measurement](#from-mechanism-to-measurement)
- [Confirm the Build](#confirm-the-build)
- [Benchmarking](#benchmarking)
- [Profiling](#profiling)
- [Interpret an Observation Before Choosing a Change](#interpret-an-observation-before-choosing-a-change)
- [Reporting Results](#reporting-results)
- [Common Mistakes](#common-mistakes)
- [Availability by Version](#availability-by-version)
- [Practical Boundaries](#practical-boundaries)

Examples use stable APIs unless marked otherwise; see [compatibility](../../SKILL.md#compatibility). Blocks marked `ignore` need a crate. Compiler and profile settings are in [build configuration](build-configuration.md); the mechanisms to change after measuring are in [performance optimization](performance-optimization.md) and, for build time, [compile times](compile-times.md).

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
| `divan` (crate) | Functions and small operations | Sampled timings (fastest, slowest, median, mean), argument parameterization, optional allocation profiling; registered with `#[divan::bench]`. Meets the [adoption floor](library-selection.md#admission-conditions); the catalog's benchmark harness candidate for a new suite |
| `criterion` (crate) | Functions and small operations | Statistical analysis, warm-up, outlier detection, HTML reports. Its current repository is below the [adoption floor](library-selection.md#admission-conditions), so it is not a new recommendation; existing criterion suites remain valid to maintain |
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

A harness crate replaces the libtest harness for its bench target, so the target sets `harness = false`:

```toml
[dev-dependencies]
divan = "0.1"

[[bench]]
name = "checksum"
harness = false
```

```rust,ignore
// benches/checksum.rs. A bench target is a separate crate, so it imports `checksum`
// (the function above, made `pub`) from the library under test, here named `checksum_lib`.
use checksum_lib::checksum;
use divan::{black_box, Bencher};

fn main() {
    divan::main();
}

#[divan::bench]
fn checksum_64_kib(bencher: Bencher) {
    let data = vec![7u8; 64 * 1024];
    bencher.bench(|| checksum(black_box(&data)));
}
```

Setup before `bencher.bench` is not timed. divan keeps the closure's return value from being optimized away and drops it outside the timed sample loop.

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

## Reporting Results

State the metric, the baseline, the new measurement, the variance, the machine, and the profile; "should be faster" is a hypothesis, not a result. Run the correctness tests in the same profile as the benchmark, because a change that speeds up a wrong answer is a regression. Keep the before and after profiles with the change so the next reader can see what moved.

## Common Mistakes

- Measuring a `dev` build, or a `release` build with `debug-assertions = true` left in a custom profile.
- Optimizing a function the profiler never showed.
- Switching to `parking_lot`, `rayon`, or a custom allocator without a before/after benchmark on the real workload.
- Reporting a speedup from a single run.

## Availability by Version

| Version | Addition |
|---|---|
| 1.97 | v0 symbol mangling default (readable profiles without extra flags) |

Per-release details live in [the versions index](../versions/index.md).

## Practical Boundaries

A useful comparison measures the objective that matters under equivalent workloads and build settings. Faster throughput can cost latency, memory, startup, or compilation time. Representative inputs, repeated runs, and environment details make the result interpretable.
