# Panics

## Contents

- [Panics: When and How](#panics-when-and-how)
- [Panic Strategy and Boundaries](#panic-strategy-and-boundaries)
- [Lint Policy](#lint-policy)
- [Common Mistakes](#common-mistakes)
- [Availability by Version](#availability-by-version)
- [Practical Boundaries](#practical-boundaries)

Examples use stable APIs unless marked otherwise; see [compatibility](../../SKILL.md#compatibility). The choice between `Option`, `Result`, and a panic starts in [error types](error-types.md#option-result-or-panic); panics across `extern "C"` continue in [FFI](ffi.md).

## Panics: When and How

Panic for bugs: a violated invariant, an impossible state, an index the code just proved in range. Do not panic for input validation, I/O failure, or anything the caller could reasonably handle.

- `expect("...")` with a message that states the invariant ("config validated at startup"), not the failure ("failed to unwrap").
- `assert!`/`assert_eq!` for cheap checks that guard soundness or correctness; `debug_assert!` for expensive checks that only need to run in debug builds.
- `unreachable!("...")` for match arms the type system cannot rule out but the logic does.
- `todo!()` and `unimplemented!()` never ship; Clippy `todo` and `unimplemented` (restriction) can enforce this per crate.
- Library code avoids `unwrap()` on values that depend on inputs; `unwrap()` on a value that a previous line established is acceptable with a comment, or better, restructure so the value is proven by the type.

```rust
fn median(sorted: &[u32]) -> u32 {
    assert!(!sorted.is_empty(), "median of an empty slice is undefined");
    debug_assert!(sorted.is_sorted(), "caller must pass a sorted slice"); // is_sorted: 1.82
    sorted[sorted.len() / 2]
}
```

Since 1.81 the standard sorts may panic when an `Ord` implementation is not a total order, which turns silently wrong orderings into visible bugs.

## Panic Strategy and Boundaries

| Setting or boundary | Effect |
|---|---|
| `panic = "unwind"` (default) | Destructors run while unwinding; `catch_unwind` works; a panicking thread returns `Err(payload)` from `JoinHandle::join` |
| `panic = "abort"` | Smaller binary, no unwinding; `catch_unwind` cannot catch; any panic ends the process; tests and benches ignore the setting |
| Panic reaching `extern "C"` | The process aborts (1.81+); use `catch_unwind` inside the function or declare `extern "C-unwind"` when both sides support unwinding |
| Panic inside `Drop` during unwinding | Abort |
| Panic while holding a `Mutex` | The mutex is poisoned; other threads see `Err(PoisonError)` |

```rust
use std::panic::{catch_unwind, AssertUnwindSafe};
use std::sync::{Mutex, PoisonError};
use std::thread;

fn worker_result() -> Result<u32, String> {
    let handle = thread::spawn(|| -> u32 { 41 + 1 });
    handle.join().map_err(|payload| {
        payload
            .downcast_ref::<&str>()
            .map(|s| s.to_string())
            .or_else(|| payload.downcast_ref::<String>().cloned())
            .unwrap_or_else(|| "worker panicked".to_owned())
    })
}

fn read_counter(counter: &Mutex<u64>) -> u64 {
    // A poisoned lock means another thread panicked while holding it. A plain counter is still
    // meaningful, so recover; for multi-step invariants, propagate the error instead.
    *counter.lock().unwrap_or_else(PoisonError::into_inner)
}

fn checksum(bytes: &[u8]) -> u32 {
    bytes.iter().map(|&b| u32::from(b)).sum()
}

/// Computes a checksum, returning -1 for null pointers and -2 for an unwinding panic.
///
/// # Safety
/// If both pointers are non-null, `ptr` must identify `len` initialized readable
/// bytes within one allocation, with `len <= isize::MAX`. The input must remain
/// valid and unmodified during this call. Even for zero length, it must be a
/// properly aligned, non-null pointer suitable for an empty slice.
/// `out` must be aligned and valid for writing one u32, must not overlap the input,
/// and must permit exclusive access for the duration of the call.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn checksum_bytes(ptr: *const u8, len: usize, out: *mut u32) -> i32 {
    if ptr.is_null() || out.is_null() {
        return -1;
    }
    // SAFETY: the caller guarantees a valid, initialized, immutable input range.
    let bytes = unsafe { std::slice::from_raw_parts(ptr, len) };
    match catch_unwind(AssertUnwindSafe(|| checksum(bytes))) {
        Ok(sum) => {
            // SAFETY: the caller guarantees aligned, exclusive writable output storage.
            unsafe { out.write(sum) };
            0
        }
        Err(_) => -2,
    }
}
```

The unsafe signature makes the caller's obligations explicit to Rust callers too; C callers must uphold the same contract. Null checks cannot validate an arbitrary non-null pointer. `catch_unwind` handles unwinding panics, not undefined behavior or `panic = "abort"`.

Set a panic hook (`std::panic::set_hook`) in binaries that need structured crash logs; since 1.81 the hook receives `PanicHookInfo`, and 1.91 adds `payload_as_str()`.

## Lint Policy

| Lint | Group | Default | Use |
|---|---|---|---|
| `unwrap_used`, `expect_used` | restriction | allow | Enable per crate where panics are forbidden (services, libraries); allow in tests |
| `panicking_unwrap` | correctness | deny | `unwrap` on a value known to be `None`/`Err` |
| `indexing_slicing`, `arithmetic_side_effects` | restriction | allow | Panic-free arithmetic and indexing in critical paths |
| `todo`, `unimplemented`, `dbg_macro`, `print_stdout` | restriction | allow | Keep debugging aids out of release code |

## Common Mistakes

- `unwrap()` in a request handler on a value derived from user input.
- Using `panic = "abort"` and still expecting `catch_unwind` or `join()` error recovery to work.

## Availability by Version

| Version | Addition |
|---|---|
| 1.81 | `PanicHookInfo`; panics abort at `extern "C"`; sorts may panic on invalid `Ord` |
| 1.91 | `PanicHookInfo::payload_as_str`; panic messages include the thread ID |

Per-release details live in [the versions index](../versions/index.md).

## Practical Boundaries

Expected input and capacity failures usually belong in Result. An expect can express an established invariant, but it should not stand in for validation of an external condition. Error propagation, task/thread failure, panic unwinding, process abort, and foreign calls have different behavior; an application's failure policy must account for the boundaries it actually crosses.
