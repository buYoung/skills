# Build Configuration

## Contents

- [Profile Defaults](#profile-defaults)
- [What the Settings Change](#what-the-settings-change)
- [Recipes](#recipes)
- [Compare Settings by the Cost They Change](#compare-settings-by-the-cost-they-change)
- [Setting Reference](#setting-reference)
- [Overrides and Precedence](#overrides-and-precedence)
- [.cargo/config.toml](#cargoconfigtoml)
- [Linkers](#linkers)
- [Profile-Guided Optimization](#profile-guided-optimization)
- [Cross-Language LTO](#cross-language-lto)
- [Allocators](#allocators)
- [Backtraces, Symbols, and panic=abort](#backtraces-symbols-and-panicabort)
- [Faster Development Builds](#faster-development-builds)
- [CI Flags](#ci-flags)
- [Verification](#verification)
- [Common Mistakes](#common-mistakes)
- [Availability by Version](#availability-by-version)

TOML blocks are fragments of `Cargo.toml` or `.cargo/config.toml` as labelled. Code-level optimization is in [performance](performance.md).

## Profile Defaults

| Setting | `dev` | `release` |
|---|---|---|
| `opt-level` | `0` | `3` |
| `debug` | `true` (full) | `false` |
| `split-debuginfo` | platform default | platform default |
| `strip` | `"none"` | `"none"`; since Cargo 1.77 debuginfo is stripped from the final binary when `debug` is off (reverted on Windows in 1.77.2) |
| `debug-assertions` | `true` | `false` |
| `overflow-checks` | `true` | `false` |
| `lto` | `false` | `false` |
| `panic` | `"unwind"` | `"unwind"` |
| `incremental` | `true` | `false` |
| `codegen-units` | `256` | `16` |
| `rpath` | `false` | `false` |

`test` inherits `dev`, `bench` inherits `release`, `cargo install` builds `release`. `cargo build --release` is shorthand for `--profile release`; custom profiles are selected with `--profile <name>` and output to `target/<name>/`.

## What the Settings Change

A profile controls several independent costs. Optimization level changes the compiler's transformation budget; LTO expands cross-unit optimization opportunities; codegen units trade parallel compilation against optimization opportunities. Debug information and symbol handling affect build/output size and diagnostics. Panic strategy changes unwinding behavior as well as generated code. Target features define which machines can execute the result.

These controls can interact, so a throughput-oriented setting can increase build time or binary size, and a size-oriented setting can reduce runtime optimization opportunities. The Cargo defaults are a useful baseline. Evaluate only the settings relevant to the workload and deployment, retaining required error recovery and diagnostic behavior.

## Recipes

Each recipe is a starting point for comparison. Its effect depends on the workload, compiler, target, and deployment constraints.

Throughput-oriented settings to evaluate:

```toml
[profile.release]
codegen-units = 1     # one unit: better optimization, slower compile
lto = "fat"           # start with "thin" if compile time matters; compare "fat" only if its extra build cost is justified
panic = "abort"       # only when catch_unwind and unwinding-based recovery are not used
# add PGO and a benchmark-chosen allocator on top (see below)
```

Size-oriented settings to compare:

```toml
[profile.release]
opt-level = "z"       # or "s" for slightly more inlining and vectorization
codegen-units = 1
lto = "fat"
panic = "abort"
strip = "symbols"
```

On Linux with `panic = "abort"`, Rust 1.92 and later emit unwind tables by default so backtraces work; pass `-C force-unwind-tables=no` to drop them for the smallest output.

Release build that stays debuggable (crash reports with file and line):

```toml
[profile.release]
debug = "line-tables-only"   # file:line for backtraces, no variable info
strip = "none"               # keep symbols; Cargo would otherwise strip debuginfo when debug is off
split-debuginfo = "packed"   # separate .dSYM/.dwp/.pdb to ship symbols out of band (platform dependent)
```

Profiling build (optimized like release, symbolized like debug):

```toml
[profile.profiling]
inherits = "release"
debug = "line-tables-only"
strip = "none"
```

Faster development iteration:

```toml
[profile.dev]
debug = "line-tables-only"   # less debug information to generate; no variable-level debugging

[profile.dev.package."*"]
opt-level = 2                # dependencies optimized once; your own crate stays at opt-level 0
```

Reproducible CI (see [CI Flags](#ci-flags)): a pinned `rust-toolchain.toml`, `--locked`, and warnings denied from the environment rather than from source.

## Compare Settings by the Cost They Change

Use the existing deployment profile as the baseline and vary one relevant setting at a time. Preserve required semantics such as unwinding recovery and supported CPU features while comparing optimization settings.

| Objective | Candidate comparison | Cost or condition to retain |
|---|---|---|
| Runtime throughput | Default release versus thin LTO, then a justified fat-LTO comparison | Link/build time and code size; a whole-program optimization is not always a runtime improvement |
| Small distributed binary | opt-level s versus z, selected stripping and LTO | z disables loop vectorization; stripping changes diagnostic artifacts, and panic policy changes recovery |
| Fast development iteration | Debug information level and selected dependency optimization | Dependency rebuild frequency and incremental behavior; optimizing every dependency can slow clean builds |
| Actionable crash reports | Line tables/full symbols and platform symbol-file packaging | The exact matching debug artifacts must remain available for the deployed binary |
| A known deployment CPU | A fixed target CPU/feature baseline | Build-machine native settings are unsuitable when deployment CPUs differ |

`cargo build --timings` exposes compilation and linking contributions. `cargo build --release -v` shows the effective rustc invocations. A setting in Cargo.toml can be overridden by a profile override, config file, environment, or explicit flags; compare the effective build rather than the text of one manifest.

Keep separate records for clean build time, incremental edit time, final artifact size, first use, and steady-state performance. A faster link and a faster application are different outcomes. Linker or LTO changes also need compatible native objects and build assumptions; cross-language optimization is not enabled just by adding lto to the Rust profile.

## Setting Reference

| Setting | Values | Semantics |
|---|---|---|
| `opt-level` | `0`, `1`, `2`, `3`, `"s"`, `"z"` | `"s"` optimizes for size, `"z"` also disables loop vectorization. Cargo: "There may be surprising results, such as level 3 being slower than 2." |
| `lto` | `false`, `true`/`"fat"`, `"thin"`, `"off"` | `false` = thin local LTO within the crate (rustc skips it at `codegen-units = 1` or `opt-level = 0`); `"thin"` = cross-crate thin LTO, faster than fat with similar gains; `"fat"` = whole-program; `"off"` = none |
| `codegen-units` | integer ≥ 1 | Fewer units, better optimization, less parallelism |
| `panic` | `"unwind"`, `"abort"` | `abort` is ignored for tests, benches, build scripts, and proc macros; the final target and panic runtime must support the chosen strategy; `catch_unwind` cannot catch under `abort` |
| `debug` | `0`/`false`/`"none"`, `"line-directives-only"`, `"line-tables-only"`, `1`/`"limited"`, `2`/`true`/`"full"` | `"line-tables-only"` is enough for backtraces and most profilers |
| `split-debuginfo` | `"off"`, `"packed"`, `"unpacked"` | rustc defaults: `packed` on MSVC and macOS, `off` on ELF |
| `strip` | `"none"`, `"debuginfo"`, `"symbols"`, `true` (= symbols), `false` (= none) | Symbols stripped means no names in backtraces or profiles |
| `debug-assertions` | bool | Controls `debug_assert!` and `cfg(debug_assertions)` |
| `overflow-checks` | bool | Panic on integer overflow; off in release means two's-complement wrap |
| `incremental` | bool | Faster rebuilds, less optimization; `CARGO_INCREMENTAL` env overrides |
| `rpath` | bool | Embed library search paths |

rustc-level flags without a profile key go through `RUSTFLAGS` or `.cargo/config.toml`: `-C target-cpu=<cpu>` (`native` binds the binary to the build host), `-C target-feature=+avx2` (unsafe: running without the feature is undefined behavior), `-C force-frame-pointers=yes`, `-C force-unwind-tables=no`, `-C dwarf-version=5` (1.88), `-C symbol-mangling-version=v0` (default since 1.97), `-C link-arg=...`, `-C linker=...`, `-C embed-bitcode=no` (incompatible with LTO), `-C profile-generate`/`-C profile-use` (PGO).

## Overrides and Precedence

```toml
[profile.release.package.image-decoder]   # one dependency
opt-level = 3

[profile.dev.package."*"]                 # all dependencies, not workspace members
opt-level = 2

[profile.release.build-override]          # build scripts and proc macros
opt-level = 0
codegen-units = 256

[profile.release-lto]                     # custom profile
inherits = "release"
lto = "fat"
codegen-units = 1
```

Precedence, first match wins: `package.<name>`, then `package."*"`, then `build-override`, then the profile itself, then Cargo defaults. Overrides cannot set `panic`, `lto`, or `rpath`; those are whole-program settings. Changing a `package."*"` override rebuilds every dependency.

## .cargo/config.toml

Settings that belong to a machine or a CI environment rather than to the crate live in `.cargo/config.toml` (project, home, or `--config` on the command line):

```toml
[build]
rustflags = ["-C", "force-frame-pointers=yes"]
# build-dir = "/fast-disk/cargo-build"    # 1.91: intermediate artifacts separate from target/

[target.x86_64-unknown-linux-gnu]
rustflags = ["-C", "target-cpu=x86-64-v3"]   # deployment baseline instead of native
linker = "clang"

[target.aarch64-apple-darwin]
rustflags = ["-C", "link-arg=-Wl,-dead_strip"]

[profile.release]              # profiles may also be set here
lto = "thin"

[net]
retry = 3
```

`RUSTFLAGS` in the environment replaces `build.rustflags` entirely; `target.<triple>.rustflags` and `build.rustflags` do not merge either. Pick one place per environment, because different flags between CI and local builds invalidate the cache and hide flag drift. Cargo 1.94 supports `include` to compose config files and TOML 1.1 syntax.

## Linkers

- Since 1.90, `lld` is the default linker on `x86_64-unknown-linux-gnu`. Opt out with `-C linker-features=-lld` when a linker script or plugin depends on GNU `ld`.
- Where supported, `-C link-arg=-fuse-ld=lld` or a compatible linker such as mold can reduce link time. Linker scripts, plugins, available flags, and deployment requirements can constrain compatibility.
- Since 1.97 the `linker_messages` lint (warn) surfaces linker stderr that used to be hidden on success. Read the message; allow it per crate with `[lints.rust] linker_messages = "allow"` only when it is understood.
- Unsupported `extern "<abi>"` strings are rejected consistently since 1.90; ABI typos that only failed in some positions now always fail.

## Profile-Guided Optimization

PGO first produces an instrumented build that collects execution profiles. A subsequent optimized build uses representative profiles to guide inlining and layout. The benefit depends on how closely the training workload matches deployment.

```sh
rm -rf /tmp/pgo-data
RUSTFLAGS="-C profile-generate=/tmp/pgo-data" cargo build --release --target x86_64-unknown-linux-gnu
./target/x86_64-unknown-linux-gnu/release/app --representative-workload   # run several typical scenarios
llvm-profdata merge -o /tmp/pgo-data/merged.profdata /tmp/pgo-data
RUSTFLAGS="-C profile-use=/tmp/pgo-data/merged.profdata" cargo build --release --target x86_64-unknown-linux-gnu
```

`llvm-profdata` comes from `rustup component add llvm-tools-preview` and lives under `~/.rustup/toolchains/<toolchain>/lib/rustlib/<host>/bin/`. Every other rustc flag must be identical between the two builds. Stale or unrepresentative profiles make code slower, so regenerate them when the hot paths change; `cargo-pgo` (crate) automates the sequence.

## Cross-Language LTO

Inlining across Rust and C/C++ requires both sides to emit compatible LLVM bitcode and use a consistent LTO mode: compile C with `clang -flto=thin`, and build Rust with `-C linker-plugin-lto -C linker=clang -C link-arg=-fuse-ld=lld`. For full LTO, use `-flto=full` on the C side and add `-C lto=fat` on the Rust side. Linker support and platform flags still depend on the target. Prefer rustc, clang, and the linker plugin built on the same LLVM version; a newer plugin alone is not a compatibility proof. `rustc -vV` prints the LLVM version.

## Allocators

Use [memory and allocation](memory-and-allocation.md#allocator-selection) for allocator policy. Defaults depend on the target/build; a reusable library should not impose a global allocator on consumers. Compare the actual workload's latency, throughput, memory retention, and fragmentation before replacement. No alternate allocator wrapper is currently a default catalog recommendation under the [selection policy](library-selection.md).

## Backtraces, Symbols, and panic=abort

| Requirement | Settings |
|---|---|
| File and line in production backtraces | `debug = "line-tables-only"`, `strip = "none"` or `"debuginfo"` kept out-of-band with `split-debuginfo`, `RUST_BACKTRACE=1` at runtime |
| Readable function names in profiles | Do not `strip = "symbols"`; v0 mangling is default since 1.97 |
| Smallest binary and no unwinding | `panic = "abort"`, `strip = "symbols"`, and `-C force-unwind-tables=no` on Linux (1.92 emits tables by default) |
| Panic recovery inside the process | `panic = "unwind"`; `catch_unwind` and `JoinHandle::join` errors require it |
| Reproducible symbol names across builds | `-C symbol-mangling-version=v0` on toolchains before 1.97 |

`panic = "abort"` also means a panicking thread takes the whole process down; services that isolate failures per request keep `unwind`.

## Faster Development Builds

- `debug = "line-tables-only"` or `debug = false` in `[profile.dev]`.
- `[profile.dev.package."*"] opt-level = 2` so dependencies are compiled once with optimization while the workspace stays at `opt-level = 0`.
- `cargo check` in the edit loop; `cargo build --timings` to find the crates that serialize the build; split crates on the critical path.
- A faster linker (`lld` is default on x86_64 Linux since 1.90; `mold` where available).
- `build.build-dir` (1.91) on a fast disk shared across worktrees; `CARGO_INCREMENTAL=1` is already the dev default.
- Trim dependency features (`default-features = false` plus the needed features) and remove unused dependencies (`cargo-udeps`, `cargo-machete` from the ecosystem).
- Nightly-only: the parallel front end (`-Z threads=8`) and the Cranelift backend for dev builds; do not depend on them in a stable toolchain.

## CI Flags

- Pin the toolchain with `rust-toolchain.toml` (`channel = "1.98.1"` or `"stable"` with a documented upgrade routine).
- `cargo build --locked` and `cargo test --locked` fail when `Cargo.lock` would change, so CI does not silently resolve new versions.
- A command-line or CI warning policy can be tied to a known toolchain: `CARGO_BUILD_WARNINGS=deny` (1.97) or `RUSTFLAGS="-D warnings"`. Broad in-source `deny(warnings)` can break local builds when new lints appear; dependency lint caps can lower configured severity. Use the scope that matches the intended policy.
- `cargo clippy --all-targets --all-features -- -D warnings` on supported feature/target combinations with the chosen toolchain (see [lint configuration](lints-and-diagnostics.md#configuring-lints-in-cargotoml)). Use a feature matrix where all-features does not represent supported builds.
- Cache `~/.cargo/registry`, `~/.cargo/git`, and `target/` keyed by lockfile hash; Cargo 1.88+ garbage-collects the global cache automatically (files unused for 3 months from the network, 1 month if regenerable), which a shared CI cache must tolerate.

## Verification

- `cargo build --release -vv` shows the exact `rustc` invocations and flags.
- Compare artifact size (`ls -l target/release/<bin>`) and the benchmark before and after each setting; change one setting at a time.
- With debuggability requirements, panic deliberately (`RUST_BACKTRACE=1`) and confirm file and line appear.
- `cargo test --release` (or `--profile <name>`) after changing `overflow-checks`, `debug-assertions`, or `panic`, because behavior differs from `dev`.
- After any `target-cpu`/`target-feature` change, run the binary on the oldest CPU in the deployment fleet.

## Common Mistakes

- Tuning `opt-level = 3` and `lto = "fat"` without a benchmark; sometimes `opt-level = 2` or `"thin"` is faster or identical at a fraction of the compile time.
- `strip = "symbols"` or `panic = "abort"` in a service that needs crash backtraces or per-request panic isolation.
- `-C target-cpu=native` in a binary shipped to other machines.
- Setting `panic`, `lto`, or `rpath` inside a `package` override (rejected by Cargo).
- Mixing `RUSTFLAGS` in CI with `build.rustflags` locally, which causes full rebuilds and different codegen between the two.
- `#![deny(warnings)]` in `lib.rs`.
- Forgetting that tests and benches ignore `panic = "abort"`, then being surprised by different behavior in production.
- Expecting `cargo install` to honor `Cargo.lock` without `--locked`.

## Availability by Version

| Version | Change |
|---|---|
| 1.77 | Release binaries have debuginfo stripped by default when `debug` is off (Windows reverted in 1.77.2) |
| 1.84 | `resolver = "3"` for MSRV-aware dependency resolution |
| 1.88 | `-C dwarf-version` stable; Cargo cache garbage collection on by default |
| 1.90 | `lld` default on `x86_64-unknown-linux-gnu`; `cargo publish --workspace` |
| 1.91 | `build.build-dir` |
| 1.92 | `panic=abort` builds on Linux emit unwind tables by default; `-C force-unwind-tables=no` opts out |
| 1.94 | Cargo config `include`; TOML 1.1 |
| 1.95 | Custom target-spec JSON removed from stable |
| 1.96 | wasm targets no longer pass `--allow-undefined`; `-C link-arg=--allow-undefined` restores it |
| 1.97 | v0 symbol mangling default; `CARGO_BUILD_WARNINGS`; `linker_messages` lint |

Per-release details live in [the versions index](../versions/index.md).
