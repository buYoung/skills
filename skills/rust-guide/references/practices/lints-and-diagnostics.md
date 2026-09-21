# Compiler Diagnostics and Lints

## Contents

- [Interpreting a Diagnostic](#interpreting-a-diagnostic)
- [Borrow and Lifetime Constraints](#borrow-and-lifetime-constraints)
- [Async Bounds and Pinning](#async-bounds-and-pinning)
- [Follow a Borrow Error Through the Operation](#follow-a-borrow-error-through-the-operation)
- [A Lifetime Annotation Cannot Keep Local Storage Alive](#a-lifetime-annotation-cannot-keep-local-storage-alive)
- [Understand Which State Makes a Future Non-Send](#understand-which-state-makes-a-future-non-send)
- [Clippy Lint Groups](#clippy-lint-groups)
- [Lint Levels and rustc Groups](#lint-levels-and-rustc-groups)
- [Configuring Lints in Cargo.toml](#configuring-lints-in-cargotoml)
- [clippy.toml](#clippytoml)
- [expect Instead of allow](#expect-instead-of-allow)
- [CI Invocation](#ci-invocation)
- [Curated Lints by Concern](#curated-lints-by-concern)
- [rustc Lints Worth Enabling](#rustc-lints-worth-enabling)
- [After a Toolchain Upgrade](#after-a-toolchain-upgrade)
- [What Lints Establish](#what-lints-establish)
- [Common Mistakes](#common-mistakes)
- [Availability by Version](#availability-by-version)

Compiler errors describe requirements the program does not satisfy; lints additionally identify patterns that may be incorrect, confusing, or unnecessarily costly. Understanding the requirement connects a diagnostic to an appropriate Rust pattern.

## Interpreting a Diagnostic

Read the expected and actual types together with the spans and notes that introduced the constraint. The final line may be where a mismatch becomes visible rather than where ownership was transferred or a bound was required. `rustc --explain E0382`, for example, explains the moved-value rule independently of a particular application.

Separate the language rule from the intended API: a borrowing operation, consuming operation, independently owned result, and shared handle can each be correct for different uses. A suggested conversion that compiles may change copying, lifetime, or error semantics. Explain that consequence alongside the relevant pattern.

## Borrow and Lifetime Constraints

| Diagnostic situation | Underlying requirement | Useful patterns and limits |
|---|---|---|
| A value is used after a move, such as E0382 | Ownership was transferred before the later use | Borrow when the callee needs temporary access; consume deliberately when it owns the operation; clone when independent ownership or a snapshot is required |
| Mutable and shared borrows overlap, such as E0502/E0499 | Conflicting accesses overlap while the earlier borrow remains in use | Finish the earlier use, borrow disjoint fields/slices through suitable APIs, or reorganize the operation; RefCell replaces static enforcement with runtime checks and can panic |
| A returned or stored reference outlives its owner, such as E0515/E0597 | Referenced storage must survive every permitted use | Return owned data, keep the owner at a longer-lived boundary, or express a genuine input/output lifetime relationship; adding a lifetime name does not extend storage lifetime |
| A generic bound or associated type does not match | The caller or implementation promised a different type-level contract | Locate the bound's origin; use an appropriate adapter, implementation, or narrower contract rather than adding unrelated bounds everywhere |

The examples in [parameter and return types](ownership-and-type-design.md#parameter-and-return-types), [interior mutability](ownership-and-type-design.md#interior-mutability), and [moving out with mem::take](ownership-and-type-design.md#moving-out-of-mut-with-memtake) show how those patterns preserve ownership. An annotation relates references; keeping the owner alive or returning an owned value addresses the storage lifetime.

## Async Bounds and Pinning

| Constraint | Meaning | Pattern |
|---|---|---|
| A spawned future is not Send | Captured or retained state prevents transfer between threads | Identify the reported value and its suspension scope; use transferable ownership or a suitable local executor when thread affinity is intended |
| Borrowed data does not satisfy a task's 'static bound | The task may outlive the external owner | Await within the owner's lifetime, move owned state into the task, or share it deliberately; moving a borrowed reference does not extend its lifetime |
| A Future API needs Unpin or a pinned reference | Address-sensitive state must retain its pinning guarantees | Use safe local pinning or Box::pin as the API requires; Unpin, allocation, type erasure, and Send are separate properties |

See [task ownership](async-and-parallel-execution.md#borrowing-and-task-ownership) for a borrowed/owned example and [Pin and Unpin](async-and-parallel-execution.md#pin-and-unpin) for the memory contract. Adding `unsafe impl Send` or `impl Unpin` is not a general repair for a mismatched abstraction.

## Follow a Borrow Error Through the Operation

This code cannot preserve a reference into Vec while performing a mutation that may reallocate it. The later use of first keeps the shared borrow live across push.

```rust,compile_fail
fn hold_element_across_growth() {
    let mut values = vec![10, 20];
    let first = &values[0];
    values.push(30);
    println!("{first}");
}
```

If the operation needs the old integer value, copy that value rather than cloning the whole collection. If it needs a view, finish using the view before mutation or obtain a new view afterward. Those patterns have different semantics when the mutation changes the referenced element.

```rust
fn keep_value_then_grow() -> (i32, Vec<i32>) {
    let mut values = vec![10, 20];
    let first = values[0]; // i32 is Copy; the snapshot is independent of the Vec
    values.push(30);
    (first, values)
}

fn use_view_then_grow(values: &mut Vec<i32>) {
    if let Some(first) = values.first() {
        println!("{first}"); // the shared borrow's last use precedes push
    }
    values.push(30);
}
```

Moving the println without considering when its data should be observed can change behavior. Interior mutability is not an automatic solution either: a RefCell replaces this static conflict with a runtime borrowing rule. For independent regions, disjoint-field borrowing or split_at_mut can express separation without copying or dynamic checks.

## A Lifetime Annotation Cannot Keep Local Storage Alive

```rust,compile_fail
fn word() -> &'static str {
    let text = String::from("alpha beta");
    text.split_whitespace().next().unwrap()
}
```

The returned reference points into text, whose owner is dropped on return. Writing static in the signature asserts a relationship the implementation does not satisfy. It neither leaks the String nor changes its storage duration.

```rust
fn first_word(text: &str) -> Option<&str> {
    text.split_whitespace().next()
}

fn make_word() -> String {
    let text = String::from("alpha beta");
    text.split_whitespace().next().unwrap_or("").to_owned()
}
```

The first function borrows caller-owned input and ties the result to that input. The second produces independent storage. Returning a String, borrowing a caller's String, or retaining an Arc owner can each be valid; the intended result lifetime determines which contract fits. Leaking storage to manufacture static is appropriate only when permanent retention is actually the intended resource policy.

## Understand Which State Makes a Future Non-Send

The spawned future below retains a standard MutexGuard across a suspension point. Moving the Arc into the task satisfies ownership of the mutex, but does not change the guard's transfer requirements.

```rust,deps,compile_fail
// Tokio feature: rt.
use std::sync::{Arc, Mutex};
fn start(counter: Arc<Mutex<u32>>) {
    tokio::spawn(async move {
        let mut guard = counter.lock().unwrap();
        *guard += 1;
        tokio::task::yield_now().await;
        drop(guard);
    });
}
```

When the protected operation is just the counter update, its guard can end before yielding:

```rust,deps
// Tokio feature: rt. Call inside a runtime.
use std::sync::{Arc, Mutex};
fn start(counter: Arc<Mutex<u32>>) -> tokio::task::JoinHandle<()> {
    tokio::spawn(async move {
        {
            let mut guard = counter.lock().unwrap();
            *guard = guard.wrapping_add(1);
        }
        tokio::task::yield_now().await;
    })
}
```

The example assumes poisoning is an invariant failure and therefore unwraps the lock result; a recoverable application needs a deliberate poison policy. If a logical operation genuinely needs exclusive access across an await, shortening the guard may break its invariant. An async mutex or an owning actor can then fit. A local executor permits some non-Send futures but does not remove deadlock risks from blocking or reentrant locking.

For an Unpin diagnostic, the relevant property is address stability rather than transfer between threads. A borrowed future can be pinned locally without allocating:

```rust
async fn use_local_pin() -> u32 {
    let future = async { 42_u32 };
    let mut pinned = std::pin::pin!(future);
    (&mut pinned).await
}
```

Pinning does not convert borrowed data to owned data, make Rc thread-safe, or extend a task's lifetime. Read the particular bound named by the diagnostic and keep these contracts separate.

## Clippy Lint Groups

Lint availability and group membership depend on the installed toolchain. `cargo clippy -- -W help` lists its diagnostics and defaults. The categories below explain the purpose of each group.

| Group | Default | Meaning |
|---|---|---|
| `clippy::correctness` | deny | "Code that is outright wrong or useless" |
| `clippy::suspicious` | warn | "Code that is most likely wrong or useless" |
| `clippy::style` | warn | A more idiomatic way exists |
| `clippy::complexity` | warn | Something simple done in a complex way |
| `clippy::perf` | warn | "Code that can be written to run faster" |
| `clippy::pedantic` | allow | Strict, or occasional false positives; enable individually |
| `clippy::restriction` | allow | Forbids language or library features; never enable the whole group (`blanket_clippy_restriction_lints` in `suspicious` fires when you try) |
| `clippy::nursery` | allow | Under development; false positives expected |
| `clippy::cargo` | allow | Manifest metadata checks |

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

`--cap-lints` limits lint severity; Cargo uses lint caps for dependencies. `force-warn` is not suppressed by those caps. A lint's configured level is distinct from a hard compiler error. Useful rustc groups include `warnings`, `unused`, `future-incompatible`, `rust-2024-compatibility`, `nonstandard-style`, `deprecated-safe`, `let-underscore`, `keyword-idents`, and `refining-impl-trait`. `rustc -W help` lists the installed toolchain's lints.

## Configuring Lints in Cargo.toml

A manifest can centralize lint levels, and workspace members can opt into inheritance (1.74+). Different package roles can need different policies. Groups get a lower `priority` than individual lints so the individual settings win; getting this wrong is itself a deny-level Clippy correctness lint (`lint_groups_priority`). The following settings illustrate inheritance and overrides; select restriction and pedantic lints according to the package's purpose.

```toml
# Workspace root Cargo.toml
[workspace.lints.rust]
unsafe_op_in_unsafe_fn = "warn"          # default warn only in edition 2024; make it explicit everywhere
missing_docs = "warn"                    # libraries
missing_debug_implementations = "warn"   # public types should support useful debug output
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

`clippy.toml` (or `.clippy.toml`) next to `Cargo.toml` configures lint behavior rather than levels. The disallowed items below illustrate project-specific conventions, not general bans on HashMap or synchronous code.

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

`disallowed-types` and `disallowed-methods` (style, warn) are the mechanism for team conventions that no built-in lint covers. These rules express a project-specific API or library convention. `disallowed-macros` and `disallowed-names` exist as well. `msrv` doubles as documentation: Clippy will not suggest `LazyLock` to a crate whose `msrv` is below 1.80.

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

These invocations illustrate feature coverage and warning policy. Use supported target/feature combinations; `--all-features` alone does not represent every package's supported configuration.

```sh
cargo clippy --all-targets --all-features --locked -- -D warnings
cargo clippy --all-targets --no-default-features --locked -- -D warnings   # feature matrix, at least the extremes
cargo doc --no-deps --all-features   # with RUSTDOCFLAGS="-D warnings" for broken intra-doc links
```

- Run Clippy from the toolchain the crate compiles with; lints differ between versions. Pin it in `rust-toolchain.toml`.
- A command-line warning policy, or `CARGO_BUILD_WARNINGS=deny` (1.97), can keep strict checks tied to a known toolchain. Broad in-source `deny(warnings)` can make fresh lint warnings break builds where lint caps do not apply, including local development on a newer compiler.
- An optional job on the `beta` or `nightly` toolchain that is allowed to fail previews upcoming lints and edition-compatibility warnings.
- `cargo clippy --fix` applies machine-applicable suggestions; understand the resulting changes because compiling successfully does not establish the intended behavior.

## Curated Lints by Concern

Lints in `restriction`, `pedantic`, and `nursery` are opt-in.

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
| `redundant_clone`, `needless_collect`, `or_fun_call`, `option_if_let_else` | nursery | Optional diagnostics; assess each suggestion's semantics and cost |
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
| `let_underscore_drop` | allow | A temporary with a destructor discarded by an underscore binding |
| `rust_2024_compatibility` | allow | Preview edition 2024 migration lints before migrating |
| `unexpected_cfgs` | warn | Typos in `cfg` names; declare custom cfgs with `check-cfg` (see [1.80](../versions/1.80.md)) |
| `missing_abi` | warn since 1.86 | `extern` without an explicit ABI string |
| `mismatched_lifetime_syntaxes` | warn since 1.89 | Inconsistent lifetime elision between inputs and outputs |
| `linker_messages` | warn since 1.97 | Linker warnings that used to be hidden |

## After a Toolchain Upgrade

A new stable release can add lints, rename them, or change their defaults. An upgrade can therefore produce diagnostics without a source change. Compare the relevant [release notes](../versions/index.md) and the installed lint catalog before treating a new warning as a new language rule.

Suggestions can justify a code change, a narrow `expect` with a reason, or an intentional lint-level setting. A pinned CI toolchain makes a strict warning policy reproducible; target and feature coverage remain separate concerns.

## What Lints Establish

Lints recognize supported patterns. They cannot establish arbitrary FFI contracts, absence of deadlocks, an application's recovery policy, or a performance gain. `incompatible_msrv` covers supported API diagnostics rather than proving the whole dependency graph builds on the declared MSRV. Match the explanation to the relevant [safety contract](unsafe-and-ffi.md), [ownership pattern](ownership-and-type-design.md), or [performance mechanism](performance.md), using lint output as supporting evidence.

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
