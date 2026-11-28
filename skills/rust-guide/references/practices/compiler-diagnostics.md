# Compiler Diagnostics

## Contents

- [Interpreting a Diagnostic](#interpreting-a-diagnostic)
- [Borrow and Lifetime Constraints](#borrow-and-lifetime-constraints)
- [Async Bounds and Pinning](#async-bounds-and-pinning)
- [Follow a Borrow Error Through the Operation](#follow-a-borrow-error-through-the-operation)
- [A Lifetime Annotation Cannot Keep Local Storage Alive](#a-lifetime-annotation-cannot-keep-local-storage-alive)
- [Understand Which State Makes a Future Non-Send](#understand-which-state-makes-a-future-non-send)

Compiler errors describe requirements the program does not satisfy. Understanding the requirement connects a diagnostic to an appropriate Rust pattern. Lint groups, levels, and configuration are in [lints](lints.md).

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

The examples in [parameter and return types](ownership-and-borrowing.md#parameter-and-return-types), [interior mutability](ownership-and-borrowing.md#interior-mutability), and [moving out with mem::take](ownership-and-borrowing.md#moving-out-of-mut-with-memtake) show how those patterns preserve ownership. An annotation relates references; keeping the owner alive or returning an owned value addresses the storage lifetime.

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
