# Lints and Review

## Contents

- [Review Order](#review-order)
- [Clippy Lint Groups](#clippy-lint-groups)
- [Lint Levels and rustc Groups](#lint-levels-and-rustc-groups)
- [Configuring Lints in Cargo.toml](#configuring-lints-in-cargotoml)
- [clippy.toml](#clippytoml)
- [expect Instead of allow](#expect-instead-of-allow)
- [CI Invocation](#ci-invocation)
- [Curated Lints by Concern](#curated-lints-by-concern)
- [rustc Lints Worth Enabling](#rustc-lints-worth-enabling)
- [After a Toolchain Upgrade](#after-a-toolchain-upgrade)
- [Reviewing Without a Lint](#reviewing-without-a-lint)
- [Common Mistakes](#common-mistakes)
- [Availability by Version](#availability-by-version)

Lint groups and default levels below were taken from `cargo clippy -- -W help` on Clippy 0.1.95 (Rust 1.95). Lints move between groups across releases and new ones arrive every six weeks, so re-run that command on the project's toolchain when a group placement matters. Topic references own the judgment behind each lint; this file owns the tooling and the review order.

## Review Order

1. Soundness and correctness: Clippy `correctness` (deny) and `suspicious` findings, then every `unsafe` block against [unsafe and FFI](unsafe-and-ffi.md).
2. Ownership and concurrency: guards held across `.await` or slow work, `Arc<Mutex<T>>` sprawl, clones that exist to satisfy the borrow checker ([ownership and type design](ownership-and-type-design.md), [concurrency](concurrency.md)).
3. Public API and SemVer: naming, `#[non_exhaustive]`, sealed traits, capture rules, auto traits ([API and crate design](api-and-crate-design.md)).
4. Error handling: `unwrap` policy, error types, documented `# Errors` and `# Panics` ([error handling](error-handling.md)).
5. Performance only with a profile ([performance](performance.md)); style and complexity last, and only where the lint output is not already in the pull request.

A review comment cites the lint name and group when one exists ("`await_holding_lock` (suspicious)") so the author can look it up and the team can decide whether to enforce it in configuration.

## Clippy Lint Groups

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

`clippy::all` is the union of the on-by-default groups (correctness, suspicious, style, complexity, perf).

## Lint Levels and rustc Groups

| Level | Meaning |
|---|---|
| `allow` | Silent |
| `expect` | Silent, but warns (`unfulfilled_lint_expectations`) if the lint does not fire |
| `warn` | Warning |
| `force-warn` | Warning that `--cap-lints` and `allow` cannot suppress |
| `deny` | Error, but a nested `allow` can still lower it |
| `forbid` | Error that nothing below can lower |

`--cap-lints warn` (which Cargo applies to dependencies) caps everything except `force-warn`, so a lint your crate denies never breaks a downstream build. rustc groups worth knowing: `warnings` (everything at warn), `unused`, `future-incompatible`, `rust-2024-compatibility` (edition migration lints), `nonstandard-style`, `deprecated-safe`, `let-underscore`, `keyword-idents`, `refining-impl-trait`. `rustc -W help` prints the full list for the installed toolchain.

## Configuring Lints in Cargo.toml

Lint policy belongs in the manifest, inherited across a workspace (1.74+), so every crate and every developer run the same set. Groups get a lower `priority` than individual lints so the individual settings win; getting this wrong is itself a deny-level Clippy correctness lint (`lint_groups_priority`).

```toml
# Workspace root Cargo.toml
[workspace.lints.rust]
unsafe_op_in_unsafe_fn = "warn"          # default warn only in edition 2024; make it explicit everywhere
missing_docs = "warn"                    # libraries
missing_debug_implementations = "warn"   # every public type gets Debug (API guideline C-DEBUG)
unreachable_pub = "warn"                 # pub items that are not actually exported
rust_2024_compatibility = { level = "warn", priority = -1 }   # before an edition migration

[workspace.lints.clippy]
all = { level = "warn", priority = -1 }  # the default groups, stated explicitly
pedantic = { level = "warn", priority = -1 }   # optional: only if the team triages false positives
module_name_repetitions = "allow"        # pedantic lints the team disagrees with, listed individually
missing_errors_doc = "allow"
undocumented_unsafe_blocks = "warn"      # restriction lints worth enabling one by one
unwrap_used = "warn"
dbg_macro = "warn"
print_stdout = "warn"
```

```toml
# Every member Cargo.toml
[lints]
workspace = true
```

Rules:

- Lints in `[lints]` apply to the current package only, never to dependencies.
- The tool namespace is the part before `::`; `unsafe_code` goes under `[lints.rust]`, `clippy::foo` under `[lints.clippy]`, `rustdoc::broken_intra_doc_links` under `[lints.rustdoc]`.
- `level = "forbid"` in the manifest cannot be lowered anywhere in the crate; use it only for policies without exceptions (`unsafe_code = "forbid"` in crates that must stay free of `unsafe`).
- Tests often need `unwrap` and `dbg!`: put `#![cfg_attr(test, allow(clippy::unwrap_used))]` at the crate root, or scope the restriction lints to non-test builds.

## clippy.toml

`clippy.toml` (or `.clippy.toml`) next to `Cargo.toml` configures lint behavior rather than levels.

```toml
msrv = "1.85"                 # suggestions respect the MSRV; incompatible_msrv (suspicious) flags std APIs newer than this
avoid-breaking-exported-api = false   # let API-shape lints (wrong_self_convention, new_ret_no_self) fire on pub items too
too-many-arguments-threshold = 7
cognitive-complexity-threshold = 25
allow-unwrap-in-tests = true
allow-expect-in-tests = true
allow-dbg-in-tests = true
allow-print-in-tests = true

# Ban types and calls with a project-specific replacement.
disallowed-types = [
    { path = "std::collections::HashMap", reason = "use crate::FastMap (keys are trusted ids)" },
]
disallowed-methods = [
    { path = "std::env::set_var", reason = "unsafe on edition 2024; pass configuration explicitly" },
    { path = "std::thread::sleep", reason = "blocks the async executor; use the runtime's sleep" },
]
```

`disallowed-types` and `disallowed-methods` (style, warn) are the mechanism for team conventions that no built-in lint covers; the Performance Book uses them to enforce a faster hasher. `disallowed-macros` and `disallowed-names` exist as well. `msrv` doubles as documentation: Clippy will not suggest `LazyLock` to a crate whose `msrv` is below 1.80.

## expect Instead of allow

`#[allow]` silences a lint forever, including after the code changed and the lint would no longer fire. `#[expect]` (1.81) silences it while it fires and warns when it stops, so dead suppressions get cleaned up. Give every suppression a `reason`.

```rust
#[expect(dead_code, reason = "used by the `metrics` feature; kept in the default build for layout tests")]
fn histogram_bucket_count() -> usize {
    64
}

pub fn parse_header(bytes: &[u8]) -> Option<u32> {
    #[expect(clippy::indexing_slicing, reason = "length checked on the previous line")]
    if bytes.len() >= 4 {
        Some(u32::from_le_bytes([bytes[0], bytes[1], bytes[2], bytes[3]]))
    } else {
        None
    }
}
```

Clippy's `allow_attributes` and `allow_attributes_without_reason` (restriction) turn this into policy. Suppress at the smallest scope: an expression or item, not the module or crate.

## CI Invocation

```sh
cargo clippy --all-targets --all-features --locked -- -D warnings
cargo clippy --all-targets --no-default-features --locked -- -D warnings   # feature matrix, at least the extremes
cargo doc --no-deps --all-features   # with RUSTDOCFLAGS="-D warnings" for broken intra-doc links
```

- Run Clippy from the toolchain the crate compiles with; the Clippy book recommends the same channel, because lints differ between versions. Pin it in `rust-toolchain.toml`.
- Deny warnings from the command line or `CARGO_BUILD_WARNINGS=deny` (1.97), not with `#![deny(warnings)]` in source. In-source `deny(warnings)` breaks the build for every consumer on every new lint, which the Rust Design Patterns book lists as an anti-pattern, and Cargo's SemVer guide counts a new lint as a minor change in a dependency for the same reason.
- An optional job on the `beta` or `nightly` toolchain that is allowed to fail previews upcoming lints and edition-compatibility warnings.
- `cargo clippy --fix` applies machine-applicable suggestions; review the diff, since suggestions can change semantics (`needless_range_loop` rewrites index arithmetic).

## Curated Lints by Concern

Groups and defaults from Clippy 0.1.95. Lints in `restriction`, `pedantic`, and `nursery` are opt-in.

Concurrency:

| Lint | Group | What it catches |
|---|---|---|
| `let_underscore_lock` | correctness (deny) | `let _ = mutex.lock()`: the guard drops immediately |
| `if_let_mutex` | correctness (deny) | Locking a mutex in an `if let` scrutinee and again in the body (deadlock) |
| `await_holding_lock`, `await_holding_refcell_ref` | suspicious | A `MutexGuard` or `RefCell` borrow held across `.await` |
| `arc_with_non_send_sync` | suspicious | `Arc<T>` where `T` is neither `Send` nor `Sync` (`Rc` would do; the `Arc` cannot be shared anyway) |
| `rc_clone_in_vec_init` | suspicious | `vec![Rc::new(x); n]` clones one pointer instead of creating `n` values |
| `let_underscore_future` | suspicious | A future dropped without being awaited |
| `readonly_write_lock` | perf | A `RwLock::write` guard used only for reading |
| `missing_spin_loop` | perf | A busy-wait loop without `std::hint::spin_loop()` |
| `mutex_atomic`, `mutex_integer` | restriction | `Mutex<bool>`/`Mutex<usize>` where an atomic suffices (policy, not always right) |
| `rc_mutex` | restriction | `Rc<Mutex<T>>`: a mutex on a single-threaded pointer |
| `future_not_send` | nursery | A public future that is not `Send` (matters for work-stealing runtimes) |
| `significant_drop_tightening`, `significant_drop_in_scrutinee` | nursery | Guards held longer than needed or in `match` scrutinees |

Unsafe:

| Lint | Group | What it catches |
|---|---|---|
| `not_unsafe_ptr_arg_deref` | correctness (deny) | A safe `pub fn` dereferencing a raw-pointer argument |
| `uninit_vec`, `mem_replace_with_uninit`, `uninit_assumed_init` | correctness (deny) | Creating values from uninitialized memory |
| `unsound_collection_transmute`, `wrong_transmute`, `transmuting_null`, `cast_slice_different_sizes` | correctness (deny) | Layout-incompatible or invalid transmutes and casts |
| `zst_offset`, `size_of_in_element_count` | correctness (deny) | Pointer arithmetic on zero-sized types; `size_of` used where an element count is expected |
| `missing_transmute_annotations`, `macro_metavars_in_unsafe` | suspicious | Inferred transmute types; macro inputs expanded inside `unsafe` blocks |
| `transmute_ptr_to_ref` | complexity | `transmute` where `&*ptr` is the idiom |
| `missing_safety_doc` | style | `pub unsafe fn` without a `# Safety` section |
| `cast_ptr_alignment`, `ptr_as_ptr`, `borrow_as_ptr` | pedantic | Alignment-changing casts; `as` between raw pointers; `&x as *const _` instead of `&raw const` |
| `undocumented_unsafe_blocks`, `multiple_unsafe_ops_per_block` | restriction | Missing `// SAFETY:` comments; several operations under one comment |
| `mem_forget`, `as_conversions` | restriction | `mem::forget` on `Drop` types; silent `as` casts |

Collections and trait consistency:

| Lint | Group | What it catches |
|---|---|---|
| `derive_ord_xor_partial_ord`, `derived_hash_with_manual_eq` | correctness (deny) | Derived and hand-written impls that can disagree |
| `unit_hash`, `unit_cmp` | correctness (deny) | Hashing or comparing `()` |
| `mutable_key_type` | suspicious | Map or set keys with interior mutability |
| `declare_interior_mutable_const` | suspicious | A `const` holding a `Cell`/atomic (each use is a fresh copy) |
| `map_entry` | perf | `contains_key` followed by `insert` |
| `linkedlist` | pedantic | `LinkedList` where `Vec`/`VecDeque` is almost always faster |

Performance (the full `perf` group is listed in [performance](performance.md#clippy-performance-lints)):

| Lint | Group | What it catches |
|---|---|---|
| `large_enum_variant`, `result_large_err`, `large_const_arrays` | perf | Oversized enums, `Err` types, and const arrays |
| `box_collection`, `boxed_local`, `redundant_allocation` | perf | Unnecessary heap indirection |
| `cmp_owned`, `unnecessary_to_owned`, `iter_overeager_cloned` | perf | Allocation or cloning only to compare or filter |
| `expect_fun_call` | perf | `expect(&format!(..))` evaluated eagerly |
| `slow_vector_initialization`, `vec_init_then_push`, `useless_vec`, `manual_memcpy`, `manual_retain`, `manual_str_repeat` | perf | Hand-written loops with faster std equivalents |
| `drain_collect`, `extend_with_drain` | perf | `drain(..).collect()` and `extend(v.drain(..))` instead of `mem::take` and `append` |
| `regex_creation_in_loops`, `unbuffered_bytes`, `waker_clone_wake` | perf | Regex compiled per iteration; `bytes()` on unbuffered readers; needless `Waker` clone |
| `redundant_clone`, `needless_collect`, `or_fun_call`, `option_if_let_else` | nursery | Opt in for a review pass; read each report |
| `format_collect`, `single_char_pattern`, `large_futures`, `large_stack_arrays`, `large_types_passed_by_value`, `needless_pass_by_value`, `trivially_copy_pass_by_ref`, `cloned_instead_of_copied`, `implicit_clone`, `inefficient_to_string` | pedantic | Parameter passing and small inefficiencies with occasional false positives |

API shape and documentation:

| Lint | Group | What it catches |
|---|---|---|
| `ptr_arg` | style | `&Vec<T>`, `&String`, `&PathBuf` parameters instead of `&[T]`, `&str`, `&Path` |
| `should_implement_trait` | style | An inherent method named like a std trait method (`from_str`, `default`, `add`) |
| `wrong_self_convention` | style | `into_*` taking `&self`, `as_*` taking `self`, and similar receiver mismatches |
| `new_without_default` | style | `pub fn new() -> Self` without a `Default` impl |
| `len_without_is_empty` | style | A public `len()` without `is_empty()` |
| `inherent_to_string`, `inherent_to_string_shadow_display` | style, correctness | An inherent `to_string` instead of `Display` |
| `mem_replace_with_default` | style | `mem::replace(x, Default::default())` instead of `mem::take` |
| `must_use_candidate`, `missing_errors_doc`, `missing_panics_doc`, `unnecessary_wraps`, `unused_async`, `wildcard_imports`, `enum_glob_use` | pedantic | API polish and documentation completeness |
| `exhaustive_enums`, `exhaustive_structs`, `missing_inline_in_public_items` | restriction | Enforce `#[non_exhaustive]` or `#[inline]` policies in libraries |
| `cargo_common_metadata`, `multiple_crate_versions`, `wildcard_dependencies`, `negative_feature_names` | cargo | Manifest metadata, duplicate dependency versions, `*` requirements, `no-std`-style feature names |

Error and panic policy:

| Lint | Group | What it catches |
|---|---|---|
| `panicking_unwrap`, `unused_io_amount`, `absurd_extreme_comparisons`, `eq_op`, `invalid_regex` | correctness (deny) | Unwraps that always fail; ignored `read`/`write` byte counts; comparisons that are always true or false; invalid regex literals |
| `unwrap_used`, `expect_used`, `unwrap_in_result` | restriction | Panic-on-error in production code |
| `indexing_slicing`, `arithmetic_side_effects` | restriction | Panicking indexing and arithmetic in critical paths |
| `dbg_macro`, `todo`, `unimplemented`, `print_stdout`, `print_stderr` | restriction | Debugging aids and placeholders that must not ship |

## rustc Lints Worth Enabling

| Lint | Default | Why enable |
|---|---|---|
| `unsafe_op_in_unsafe_fn` | warn in edition 2024, allow before | One `unsafe {}` and one justification per operation inside `unsafe fn` |
| `missing_docs` | allow | Every public item documented |
| `missing_debug_implementations` | allow | `Debug` on every public type |
| `unreachable_pub` | allow | Distinguish crate-internal `pub(crate)` from real exports |
| `unused_qualifications` | allow | Cleaner paths after refactors |
| `let_underscore_drop` | allow | `let _ = value` on a type with a destructor (guards, files) |
| `rust_2024_compatibility` | allow | Preview edition 2024 migration lints before migrating |
| `unexpected_cfgs` | warn | Typos in `cfg` names; declare custom cfgs with `check-cfg` (see [1.80](../versions/1.80.md)) |
| `missing_abi` | warn since 1.86 | `extern` without an explicit ABI string |
| `mismatched_lifetime_syntaxes` | warn since 1.89 | Inconsistent lifetime elision between inputs and outputs |
| `linker_messages` | warn since 1.97 | Linker warnings that used to be hidden |

## After a Toolchain Upgrade

A new stable release adds lints and can promote existing ones (for example `dangerous_implicit_autorefs` went from warn in 1.88 to deny in 1.89, and `never_type_fallback_flowing_into_unsafe` became deny in 1.92). Treat the new output as review items:

1. Run `cargo clippy --all-targets --all-features` on the new toolchain without `-D warnings` and collect the diff.
2. Fix mechanically applicable suggestions with `cargo clippy --fix`, then read the diff.
3. For each remaining warning decide fix, `#[expect(..., reason)]` at the smallest scope, or a manifest-level `allow` with a comment; never blanket-allow a group.
4. Check the release's version file under [versions](../versions/index.md) for renamed lints (`elided_named_lifetimes` became `mismatched_lifetime_syntaxes` in 1.89) and update `[lints]` names so `unknown_lints` stays quiet.
5. Re-enable `-D warnings` in CI only once the tree is clean on the pinned toolchain.

## Reviewing Without a Lint

Lints cover patterns, not intent. Questions that catch what Clippy cannot:

- Does every `unsafe` block's `// SAFETY:` claim follow from an invariant stated somewhere, and does the public API preserve that invariant?
- Which thread or task owns each piece of shared state, and is every lock guard released before I/O, callbacks, and awaits?
- Does each public type carry `#[non_exhaustive]`, private fields, and the derives users will need, and is every SemVer-visible change classified?
- Are error variants structured for callers, and does every `expect` name an invariant rather than a failure?
- Is every performance change backed by a measurement in the shipping profile?
- Does the code use APIs above the crate's `rust-version` (`incompatible_msrv` catches std; dependencies need the MSRV CI job)?

## Common Mistakes

- `#![deny(warnings)]` or `#![deny(clippy::all)]` in source; use CI flags.
- `#![warn(clippy::restriction)]` as a group; the group contradicts itself.
- `#[allow]` without a reason, left behind after the code changed.
- Group and individual lint at the same `priority` in `[lints]`, so the group overrides the intended exception (`lint_groups_priority` catches it).
- Running Clippy on a different toolchain than the build, then chasing lints the shipping compiler does not have.
- Treating `nursery` output as authoritative; read each report.
- Suppressing `unused_must_use` with `let _ =` on a `Result` instead of handling or documenting the decision.
- Disabling `unsafe_op_in_unsafe_fn` to make an edition migration compile instead of adding the blocks and comments.

## Availability by Version

| Version | Change |
|---|---|
| 1.74 | `[lints]` and `[workspace.lints]` in Cargo |
| 1.80 | `unexpected_cfgs` with always-on check-cfg |
| 1.81 | `#[expect]` and lint `reason`; Clippy `allow_attributes`, `allow_attributes_without_reason` |
| 1.86 | `missing_abi` warns by default |
| 1.88 | `dangerous_implicit_autorefs` (warn), `invalid_null_arguments` |
| 1.89 | `mismatched_lifetime_syntaxes` supersedes `elided_named_lifetimes`; `dangerous_implicit_autorefs` deny; `missing_fragment_specifier` hard error |
| 1.91 | `dangling_pointers_from_locals`, `integer_to_ptr_transmutes`; `semicolon_in_expressions_from_macros` deny |
| 1.92 | Never-type fallback lints deny; `invalid_macro_export_arguments` deny |
| 1.97 | `linker_messages`; `CARGO_BUILD_WARNINGS` |

Per-release details live in [the versions index](../versions/index.md).
