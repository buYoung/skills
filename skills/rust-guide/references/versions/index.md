# Rust Versions Since 1.80

## Read When

Use this index for toolchain upgrades, MSRV compatibility, edition changes, removed or renamed APIs, and newly introduced diagnostics. Coverage is Rust 1.80 through 1.98.1.

Version links provide the relevant migration and behavior details. Other rows summarize changes without a separate migration procedure. For an upgrade, consider applicable changes between the current and target versions; for an API question, read only the relevant version and practice section.

## Version Index

| Version | File | Official deprecation or migration content | Additions without required action |
|---|---|---|---|
| 1.80.0 | [1.80](1.80.md) | `unexpected_cfgs` requires declaring custom cfgs; 1.80.1 fixes a float miscompilation | `LazyLock`/`LazyCell`, exclusive range patterns, `size_of` in the prelude |
| 1.81.0 | [1.81](1.81.md) | `PanicInfo` renamed; `wasm32-wasi` deprecated; sorts panic on inconsistent `Ord`; panics abort at `extern "C"` | `#[expect]`, `core::error::Error`, `fs::exists` |
| 1.82.0 | [1.82](1.82.md) | Edition 2024 preparation: `&raw`, `unsafe extern`, `#[unsafe(...)]` attributes | `use<..>`, `Option::is_none_or`, `cargo info`, `aarch64-apple-darwin` Tier 1 |
| 1.83.0 | none | No official deprecation or migration guidance | Const eval with `&mut` and statics, new `io::ErrorKind` variants, `Option::get_or_insert_default` |
| 1.84.0 | [1.84](1.84.md) | `wasm32-wasi` removed; MSRV-aware resolver opt-in; new coherence errors | Strict provenance APIs, `isqrt` |
| 1.85.0 | [1.85](1.85.md) | Edition 2024 migration; `set_var`/`remove_var` unsafe in 2024; `home_dir` Windows fix | Async closures, `AsyncFn`, tuple `FromIterator` |
| 1.86.0 | [1.86](1.86.md) | `missing_abi` warns; `i586-pc-windows-msvc` removal announced; debug null-pointer checks | Trait upcasting, `get_disjoint_mut`, safe `#[target_feature]` |
| 1.87.0 | [1.87](1.87.md) | `i586-pc-windows-msvc` removed; `env::home_dir` undeprecated; safe intrinsics trigger `unused_unsafe` | `Vec::extract_if`, anonymous pipes, `use<..>` in traits |
| 1.88.0 | [1.88](1.88.md) | `--nocapture` deprecated; `#[bench]` hard error; Cargo cache GC opt-out; `dangerous_implicit_autorefs` warns | `let` chains (edition 2024), `cfg(true)`, naked functions |
| 1.89.0 | [1.89](1.89.md) | `elided_named_lifetimes` superseded; `dangerous_implicit_autorefs` deny; `missing_fragment_specifier` hard error; wasm C ABI change; last Tier 1 `x86_64-apple-darwin` | `_` const arguments, file locks, `Result::flatten` |
| 1.90.0 | [1.90](1.90.md) | `lld` default linker with opt-out; `x86_64-apple-darwin` Tier 2; `MSG_NOSIGNAL`; `home_dir` with empty `HOME` | `cargo publish --workspace` |
| 1.91.0 | [1.91](1.91.md) | `semicolon_in_expressions_from_macros` deny; binding drop order; new pointer lints; 1.91.1 fixes | `Path::file_prefix`, `BTreeMap::extract_if`, `build.build-dir` |
| 1.92.0 | [1.92](1.92.md) | Never-type fallback lints deny; `invalid_macro_export_arguments` deny; `panic=abort` unwind tables with opt-out | `RwLockWriteGuard::downgrade`, `new_zeroed` |
| 1.93.0 | none | No official deprecation or migration guidance; bundled musl is 1.2.5; 1.93.1 fixes an ICE and a Clippy false positive | `MaybeUninit` slice APIs, `Vec::into_raw_parts`, `VecDeque::pop_front_if` |
| 1.94.0 | none | No official deprecation or migration guidance; 1.94.1 fixes regressions and bundled tar CVEs | `<[T]>::array_windows`, `LazyLock::get`, Cargo config `include` |
| 1.95.0 | none | Custom target-spec JSON no longer accepted on stable, stated as no action for stable users | `cfg_select!`, `if let` guards, `Vec::push_mut`, `hint::cold_path` |
| 1.96.0 | [1.96](1.96.md) | wasm undefined symbols become link errors, with the official restore flag; `core::range` migration deferred to a future edition; registry CVEs | `core::range` types, `assert_matches!` |
| 1.97.0 | [1.97](1.97.md) | v0 symbol mangling default, legacy scheme nightly-only; `linker_messages` lint | `CARGO_BUILD_WARNINGS`, bit-isolation integer APIs |
| 1.98.0 | none | No official deprecation or migration guidance; 1.98.1 fixes a vtable miscompilation, so update rather than pin 1.98.0 | Algebraic float operations, `format_into` |

## MSRV and Upgrade Policy

- Declare `rust-version` in every published `Cargo.toml`; Cargo refuses older toolchains with a clear error, `cargo add` picks compatible dependency versions, and resolver 3 prefers MSRV-compatible dependencies but can fall back to incompatible versions when no compatible candidate satisfies the requirements.
- Publish an MSRV policy (for example "latest minus two releases") so downstream users can plan. An MSRV increase can accompany a minor release under that policy, but it still prevents older compilers from building the new version; announce the requirement explicitly.
- Set `msrv = "1.NN"` in `clippy.toml` so Clippy suggestions respect the MSRV, and run one CI job on the MSRV toolchain with `--locked`.
- Upgrade in two steps: move the toolchain and read the new warnings from the files above, then raise `rust-version` and adopt replacement APIs only where they remove code or a dependency.

## Verify

`cargo +<target> build --all-targets`, `cargo +<target> clippy --all-targets`, `cargo +<target> test`, plus the benchmarks when a version file lists a behavior change in sorting, linking, or allocation. For a library, also `cargo +<msrv> check --locked`.
