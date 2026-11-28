# Synchronization

## Contents

- [Mutex](#mutex)
- [RwLock](#rwlock)
- [Condvar](#condvar)
- [One-Time and Lazy Initialization](#one-time-and-lazy-initialization)
- [Atomics and Memory Ordering](#atomics-and-memory-ordering)
- [Deadlocks and Liveness](#deadlocks-and-liveness)
- [Common Mistakes](#common-mistakes)
- [Availability by Version](#availability-by-version)
- [Practical Boundaries](#practical-boundaries)

Examples use stable APIs unless marked otherwise; see [compatibility](../../SKILL.md#compatibility). The choice between message passing, shared state, and atomics starts in [concurrency](concurrency.md#choosing-a-model), which also covers threads, channels, and `Send`/`Sync`.

## Mutex

`Mutex<T>` owns its data; the only way to reach `T` is through the guard returned by `lock()`, so forgetting to lock is impossible. The guard releases the lock when dropped.

```rust
use std::collections::HashMap;
use std::sync::{Arc, Mutex, PoisonError};
use std::thread;

type Registry = Arc<Mutex<HashMap<String, u32>>>;

fn bump(registry: &Registry, key: &str) -> u32 {
    let mut map = registry.lock().unwrap_or_else(PoisonError::into_inner);
    let counter = map.entry(key.to_owned()).or_insert(0);
    *counter += 1;
    *counter
} // guard dropped here, lock released

fn snapshot(registry: &Registry) -> Vec<(String, u32)> {
    let map = registry.lock().unwrap_or_else(PoisonError::into_inner);
    let mut pairs: Vec<_> = map.iter().map(|(k, v)| (k.clone(), *v)).collect();
    drop(map); // release before the sort: nothing below needs the lock
    pairs.sort();
    pairs
}

fn run_workers() -> Vec<(String, u32)> {
    let registry: Registry = Arc::new(Mutex::new(HashMap::new()));
    let handles: Vec<_> = (0..4)
        .map(|i| {
            let registry = Arc::clone(&registry);
            thread::spawn(move || bump(&registry, if i % 2 == 0 { "even" } else { "odd" }))
        })
        .collect();
    for handle in handles {
        handle.join().expect("worker panicked");
    }
    snapshot(&registry)
}

static ACTIVE_SESSIONS: Mutex<Vec<String>> = Mutex::new(Vec::new()); // const constructors since 1.63

fn register_session(id: &str) {
    ACTIVE_SESSIONS
        .lock()
        .unwrap_or_else(PoisonError::into_inner)
        .push(id.to_owned());
}
```

Rules:

- Keep the guard's scope to the lines that need the data; copy values out and drop the guard before slow work, I/O, callbacks, or `.await`.
- `let _ = m.lock()` drops the guard immediately and protects nothing (Clippy `let_underscore_lock`, correctness, deny). Bind it with a name.
- Poisoning: a panic while the lock is held marks it poisoned, and later `lock()` calls return `Err(PoisonError)`. Recover with `into_inner` when the data is self-consistent (counters, caches); propagate or reset when a multi-step update may be half done. `clear_poison` (1.77) resets the flag after repair. Poisoning is advisory: `unsafe` code must not depend on it for soundness.
- Locking the same `Mutex` twice on one thread is unspecified (it may panic or deadlock); never call out to code that may take the same lock while holding it.
- `Mutex::get_mut` and `into_inner` skip locking when you have `&mut Mutex<T>` or own it.
- `Mutex<T>` is `Sync` when `T: Send`, so `Arc<Mutex<T>>` is the standard shape for shared mutable state.

## RwLock

`RwLock<T>` allows many readers or one writer. It is a candidate when reads dominate and hold the lock long enough that serializing them costs, not a default upgrade from `Mutex`: the std docs state that "the priority policy of the lock is dependent on the underlying operating system's implementation", and short critical sections often run faster under a `Mutex` because the reader accounting is cheaper.

```rust
use std::sync::{PoisonError, RwLock};

struct Rules {
    inner: RwLock<Vec<String>>,
}

impl Rules {
    fn matches(&self, needle: &str) -> usize {
        let rules = self.inner.read().unwrap_or_else(PoisonError::into_inner);
        rules.iter().filter(|r| r.contains(needle)).count()
    }

    fn replace(&self, rules: Vec<String>) {
        *self.inner.write().unwrap_or_else(PoisonError::into_inner) = rules;
    }

    // Deadlock hazard documented by std: a thread holding a read guard that takes a second read
    // guard can block forever if a writer is queued between the two acquisitions on a
    // writer-preferring platform. Never nest read() while holding a read guard.
    fn matches_twice_wrong(&self, needle: &str) -> usize {
        let first = self.inner.read().unwrap_or_else(PoisonError::into_inner);
        let second = self.inner.read().unwrap_or_else(PoisonError::into_inner); // do not do this
        first.len() + second.iter().filter(|r| r.contains(needle)).count()
    }
}
```

- Since 1.92 `RwLockWriteGuard::downgrade` converts a write guard into a read guard without releasing, for "write then verify" sequences.
- Clippy `readonly_write_lock` (perf) flags a write guard that is only read.
- Alternatives when a benchmark shows contention: shard the data across several locks by key, keep an immutable `Arc<Snapshot>` behind a `Mutex` and swap it on write (readers clone the `Arc` and release the lock immediately), or use an atomic-pointer swap crate.

## Condvar

A `Condvar` pairs with a `Mutex`-protected predicate. `wait` can return spuriously, so the predicate is always checked in a loop; `wait_while` and `wait_timeout_while` encode the loop.

```rust
use std::sync::{Condvar, Mutex, PoisonError};
use std::time::Duration;

struct Gate {
    open: Mutex<bool>,
    changed: Condvar,
}

impl Gate {
    fn wait(&self) {
        let mut open = self.open.lock().unwrap_or_else(PoisonError::into_inner);
        while !*open {
            open = self.changed.wait(open).unwrap_or_else(PoisonError::into_inner);
        }
    }

    fn wait_timeout(&self, timeout: Duration) -> bool {
        let open = self.open.lock().unwrap_or_else(PoisonError::into_inner);
        let (open, result) = self
            .changed
            .wait_timeout_while(open, timeout, |open| !*open)
            .unwrap_or_else(PoisonError::into_inner);
        *open && !result.timed_out()
    }

    fn release(&self) {
        *self.open.lock().unwrap_or_else(PoisonError::into_inner) = true;
        self.changed.notify_all();
    }
}
```

Notify while holding the lock or right after releasing it; both are correct, and the waiter re-acquires the lock before `wait` returns. `notify_one` wakes one waiter; use `notify_all` when several waiters check different predicates. A channel often expresses the same hand-off with less code.

## One-Time and Lazy Initialization

| Type | Since | Use | On initializer panic |
|---|---|---|---|
| `OnceLock<T>` | 1.70 | Set once at runtime from data that arrives later (`set`, `get_or_init`) | Panic propagates to the caller; the cell stays empty and can be retried |
| `LazyLock<T, F>` | 1.80 | A `static` computed on first access from a zero-argument closure | The lock is poisoned; every later access panics (unrecoverable) |
| `OnceCell` / `LazyCell` | 1.70 / 1.80 | Single-thread versions | Same rules; `!Sync` |
| `Once` | 1.0 | Run a routine exactly once (FFI init) | Poisoned; `call_once_force` can retry |

```rust
use std::collections::HashMap;
use std::sync::{LazyLock, OnceLock};

static CONFIG: OnceLock<HashMap<String, String>> = OnceLock::new();

fn init_config(values: HashMap<String, String>) -> Result<(), &'static str> {
    CONFIG.set(values).map_err(|_| "config already initialized")
}

fn config(key: &str) -> Option<&'static str> {
    CONFIG.get()?.get(key).map(String::as_str)
}

static KEYWORDS: LazyLock<Vec<&'static str>> = LazyLock::new(|| {
    let mut words = vec!["fn", "let", "match", "impl", "struct"];
    words.sort_unstable();
    words
});

fn is_keyword(word: &str) -> bool {
    KEYWORDS.binary_search(&word).is_ok()
}
```

These replace `lazy_static!` and `once_cell` for new code. `OnceLock::get_or_init` must not re-enter itself from the initializer. Since 1.94 `LazyLock::get` returns `Some` only if initialization already happened, which helps shutdown code avoid triggering an expensive init.

## Atomics and Memory Ordering

Atomics provide lock-free counters, flags, and the building blocks of locks. Rust follows the C++20 memory model. Every atomic has a single modification order all threads agree on; `Ordering` decides what other memory becomes visible along with an atomic operation.

| Ordering | Applies to | Guarantee |
|---|---|---|
| `Relaxed` | any | Atomicity only; no ordering with other memory. Right for counters and statistics that synchronize nothing else |
| `Release` | stores and read-modify-write | Writes before this store become visible to a thread that `Acquire`-loads the stored value |
| `Acquire` | loads and read-modify-write | Reads after this load see everything before the matching `Release` store |
| `AcqRel` | read-modify-write | Both, for operations that read and write (`fetch_add`, `compare_exchange`) |
| `SeqCst` | any | `Acquire`/`Release` plus one global order of all `SeqCst` operations; useful when the protocol relies on that order; does not repair a flawed protocol |

```rust
use std::sync::atomic::{AtomicBool, AtomicU32, AtomicU64, Ordering};

static REQUESTS: AtomicU64 = AtomicU64::new(0);

fn count_request() -> u64 {
    // Relaxed: nothing else is published through this counter.
    REQUESTS.fetch_add(1, Ordering::Relaxed).wrapping_add(1)
}

static STATS: [AtomicU64; 4] = [const { AtomicU64::new(0) }; 4];
static STATS_READY: AtomicBool = AtomicBool::new(false);

fn publish(values: [u64; 4]) {
    for (slot, value) in STATS.iter().zip(values) {
        slot.store(value, Ordering::Relaxed); // data writes
    }
    STATS_READY.store(true, Ordering::Release); // publishes the writes above
}

fn read_stats() -> Option<[u64; 4]> {
    if !STATS_READY.load(Ordering::Acquire) {
        return None; // an Acquire load that sees `true` also sees every write before the Release store
    }
    Some([0, 1, 2, 3].map(|i| STATS[i].load(Ordering::Relaxed)))
}

fn saturating_increment(counter: &AtomicU32, max: u32) -> Result<u32, u32> {
    // Compare-and-swap loop; returns the previous value on success, the current value on failure.
    counter.fetch_update(Ordering::AcqRel, Ordering::Acquire, |current| {
        (current < max).then(|| current + 1)
    })
}
```

The publication example assumes one initialization before readers consume the data; repeated writers need a protocol that preserves snapshot consistency. The bounded increment uses lazy `then` so the addition is evaluated only below the bound, including when the current value is `u32::MAX`.

Synchronization relationships: everything in a thread before `spawn` happens-before the spawned thread's body; the body happens-before `join` returns; unlocking a mutex happens-before the next lock of that mutex; an `Acquire` load that reads a `Release` store's value happens-after everything before that store.

Memory-ordering pitfalls:

- Stronger ordering does not make writes visible sooner; the model "doesn't say anything about timing at all". `Relaxed` stores are not delayed.
- Disabling optimizations or running on an in-order CPU does not remove the need for ordering; the compiler still reorders, and caches still reorder visibility.
- `Relaxed` is not free when several cores write the same cache line; the contention is the cost, not the instruction.
- `SeqCst` supplies a single total order for sequentially consistent operations in addition to their acquire/release effects. It is a reasonable conservative choice when that order is useful; weaker orderings require an argument about the protocol's synchronization. Strong ordering alone does not make a multi-step algorithm correct.
- There is no `Release` load and no `Acquire` store; `SeqCst` cannot manufacture one.

Portability: `AtomicU64`/`AtomicI64` are absent on some 32-bit targets; gate with `#[cfg(target_has_atomic = "64")]`. All std atomics are lock-free where present, not necessarily wait-free. Since 1.95 `Atomic*::update`/`try_update` wrap the compare-and-swap loop.

## Deadlocks and Liveness

Deadlocks and leaks are not undefined behavior but they are bugs. Rules that prevent most of them:

- Acquire locks in one global order; document it where two locks are ever held together.
- Avoid callbacks and foreign destructors while holding locks. Do not suspend with a synchronous guard that competing work needs; an async guard across await requires a deliberate locking design.
- Prefer `try_lock` with a fallback where liveness matters more than throughput.
- Use channels or a single owner instead of two locks that reference each other.
- Every `Condvar::wait` sits in a predicate loop; every waiter has a notifier that runs after the predicate changes.
- `parking_lot` offers Mutex/RwLock variants with different poisoning and fairness behavior. Compare the relevant contention pattern before changing synchronization libraries; the replacement also changes semantics.

## Common Mistakes

- Holding a guard across I/O, a callback, or `.await`.
- `let _ = lock.lock()`, which releases the lock on the same line.
- Choosing `RwLock` for "read-heavy" code without measuring; nesting `read()` calls.
- `SeqCst` everywhere as a substitute for understanding which operations pair.
- Spinning on an atomic without `std::hint::spin_loop()` or a fallback to blocking (Clippy `missing_spin_loop`, perf).

## Availability by Version

| Version | Addition |
|---|---|
| 1.63 | Const `Mutex::new`, `RwLock::new`, `Condvar::new` |
| 1.70 | `OnceLock`, `OnceCell` |
| 1.77 | `Mutex::clear_poison` |
| 1.80 | `LazyLock`, `LazyCell` |
| 1.81 | `AtomicBool::fetch_not` |
| 1.86 | `Once::wait`, `OnceLock::wait` |
| 1.91 | `AtomicPtr::fetch_ptr_add` and bitwise `fetch_*` |
| 1.92 | `RwLockWriteGuard::downgrade` |
| 1.94 | `LazyLock::get`, `get_mut`, `force_mut` |
| 1.95 | `Atomic*::update`, `try_update` |
| 1.98 | `Atomic<T>::from_mut`, `from_mut_slice`, `get_mut_slice` |

Per-release details live in [the versions index](../versions/index.md).

## Practical Boundaries

A synchronization primitive protects a particular access protocol. Guard lifetime, lock ordering, callback reentrancy, and panic recovery affect that protocol independently of the primitive's throughput. RwLock is useful for some read-heavy access patterns, but its scheduling and contention costs still matter.

Atomic ordering describes synchronization between operations; it does not turn a sequence of updates into a transaction.

Interleaving exploration and Miri can exercise supported synchronization behavior; neither replaces the protocol's argument or establishes every application execution.
