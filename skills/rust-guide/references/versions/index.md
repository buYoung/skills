# Rust Versions Since 1.80

## Read When

Read for a toolchain upgrade, an MSRV decision, "what changed since 1.NN", a deprecated or renamed API, a lint or error that appeared after `rustup update`, or a check that an API exists at the project's MSRV. Covers stable releases 1.80.0 (2024-07-25) through 1.98.1 (2026-09-03), the latest stable when this index was written; 1.99.0 is scheduled for 2026-10-01. Anything newer must be checked against the release blog or `RELEASES.md`.

## How This Directory Works

One file per minor version in which the Rust project itself deprecates, removes, or renames something, or gives a migration instruction (release notes, compatibility notes, edition guide). A release that only added features has no file; its row below says so, and the release announcement is the source for its additions. Point releases fold into their minor's file. Read the files for every version in the range (current, target], newest last.

## Version Index

| Version | Date | File | Official deprecation or migration content | Additions without required action |
|---|---|---|---|---|
| 1.80.0 | 2024-07-25 | [1.80](1.80.md) | `unexpected_cfgs` requires declaring custom cfgs; 1.80.1 fixes a float miscompilation | `LazyLock`/`LazyCell`, exclusive range patterns, `size_of` in the prelude |
| 1.81.0 | 2024-09-05 | [1.81](1.81.md) | `PanicInfo` renamed; `wasm32-wasi` deprecated; sorts panic on inconsistent `Ord`; panics abort at `extern "C"` | `#[expect]`, `core::error::Error`, `fs::exists` |
| 1.82.0 | 2024-10-17 | [1.82](1.82.md) | Edition 2024 preparation: `&raw`, `unsafe extern`, `#[unsafe(...)]` attributes | `use<..>`, `Option::is_none_or`, `cargo info`, `aarch64-apple-darwin` Tier 1 |
| 1.83.0 | 2024-11-28 | none | No official deprecation or migration guidance | Const eval with `&mut` and statics, new `io::ErrorKind` variants, `Option::get_or_insert_default` |
| 1.84.0 | 2025-01-09 | [1.84](1.84.md) | `wasm32-wasi` removed; MSRV-aware resolver opt-in; new coherence errors | Strict provenance APIs, `isqrt` |
| 1.85.0 | 2025-02-20 | [1.85](1.85.md) | Edition 2024 migration; `set_var`/`remove_var` unsafe in 2024; `home_dir` Windows fix | Async closures, `AsyncFn`, tuple `FromIterator` |
| 1.86.0 | 2025-04-03 | [1.86](1.86.md) | `missing_abi` warns; `i586-pc-windows-msvc` removal announced; debug null-pointer checks | Trait upcasting, `get_disjoint_mut`, safe `#[target_feature]` |
| 1.87.0 | 2025-05-15 | [1.87](1.87.md) | `i586-pc-windows-msvc` removed; `env::home_dir` undeprecated; safe intrinsics trigger `unused_unsafe` | `Vec::extract_if`, anonymous pipes, `use<..>` in traits |
| 1.88.0 | 2025-06-26 | [1.88](1.88.md) | `--nocapture` deprecated; `#[bench]` hard error; Cargo cache GC opt-out; `dangerous_implicit_autorefs` warns | `let` chains (edition 2024), `cfg(true)`, naked functions |
| 1.89.0 | 2025-08-07 | [1.89](1.89.md) | `elided_named_lifetimes` superseded; `dangerous_implicit_autorefs` deny; `missing_fragment_specifier` hard error; wasm C ABI change; last Tier 1 `x86_64-apple-darwin` | `_` const arguments, file locks, `Result::flatten` |
| 1.90.0 | 2025-09-18 | [1.90](1.90.md) | `lld` default linker with opt-out; `x86_64-apple-darwin` Tier 2; `MSG_NOSIGNAL`; `home_dir` with empty `HOME` | `cargo publish --workspace` |
| 1.91.0 | 2025-10-30 | [1.91](1.91.md) | `semicolon_in_expressions_from_macros` deny; binding drop order; new pointer lints; 1.91.1 fixes | `Path::file_prefix`, `BTreeMap::extract_if`, `build.build-dir` |
| 1.92.0 | 2025-12-11 | [1.92](1.92.md) | Never-type fallback lints deny; `invalid_macro_export_arguments` deny; `panic=abort` unwind tables with opt-out | `RwLockWriteGuard::downgrade`, `new_zeroed` |
| 1.93.0 | 2026-01-22 | none | No official deprecation or migration guidance; bundled musl is 1.2.5; 1.93.1 fixes an ICE and a Clippy false positive | `MaybeUninit` slice APIs, `Vec::into_raw_parts`, `VecDeque::pop_front_if` |
| 1.94.0 | 2026-03-05 | none | No official deprecation or migration guidance; 1.94.1 fixes regressions and bundled tar CVEs | `<[T]>::array_windows`, `LazyLock::get`, Cargo config `include` |
| 1.95.0 | 2026-04-16 | none | Custom target-spec JSON no longer accepted on stable, stated as no action for stable users | `cfg_select!`, `if let` guards, `Vec::push_mut`, `hint::cold_path` |
| 1.96.0 | 2026-05-28 | [1.96](1.96.md) | wasm undefined symbols become link errors, with the official restore flag; `core::range` migration deferred to a future edition; registry CVEs | `core::range` types, `assert_matches!` |
| 1.97.0 | 2026-07-09 | [1.97](1.97.md) | v0 symbol mangling default, legacy scheme nightly-only; `linker_messages` lint | `CARGO_BUILD_WARNINGS`, bit-isolation integer APIs |
| 1.98.0 | 2026-08-20 | none | No official deprecation or migration guidance; 1.98.1 fixes a vtable miscompilation, so update rather than pin 1.98.0 | Algebraic float operations, `format_into` |

## MSRV and Upgrade Policy

- Declare `rust-version` in every published `Cargo.toml`; Cargo refuses older toolchains with a clear error, `cargo add` picks compatible dependency versions, and `resolver = "3"` keeps resolution inside the MSRV.
- Cargo's SemVer chapter treats raising `rust-version` as a minor-version change; publish the policy (for example "latest minus two releases") so downstream users can plan.
- Set `msrv = "1.NN"` in `clippy.toml` so Clippy suggestions respect the MSRV, and run one CI job on the MSRV toolchain with `--locked`.
- Upgrade in two steps: move the toolchain and read the new warnings from the files above, then raise `rust-version` and adopt replacement APIs only where they remove code or a dependency.

## Verify

`cargo +<target> build --all-targets`, `cargo +<target> clippy --all-targets`, `cargo +<target> test`, plus the benchmarks when a version file lists a behavior change in sorting, linking, or allocation. For a library, also `cargo +<msrv> check --locked`.
