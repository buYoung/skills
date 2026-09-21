# Concurrency

## Contents

- [Choosing a Model](#choosing-a-model)
- [Threads: spawn, scope, Builder](#threads-spawn-scope-builder)
- [Channels](#channels)
- [Send and Sync](#send-and-sync)
- [Mutex](#mutex)
- [RwLock](#rwlock)
- [Condvar](#condvar)
- [One-Time and Lazy Initialization](#one-time-and-lazy-initialization)
- [Atomics and Memory Ordering](#atomics-and-memory-ordering)
- [Sizing Thread Pools](#sizing-thread-pools)
- [Async Boundary](#async-boundary)
- [Choosing a Parallelism Library](#choosing-a-parallelism-library)
- [Deadlocks and Liveness](#deadlocks-and-liveness)
- [Common Mistakes](#common-mistakes)
- [Availability by Version](#availability-by-version)
- [Practical Boundaries](#practical-boundaries)

Examples use stable APIs unless marked otherwise; see [compatibility](../../SKILL.md#compatibility). Blocks marked `ignore` need an async runtime crate. Manual `unsafe impl Send`/`Sync` continues in [unsafe and FFI](unsafe-and-ffi.md); async execution is explained in [futures, tasks, and threads](async-and-parallel-execution.md#futures-tasks-and-threads).

## Choosing a Model

| Data movement | Default tool | Why |
|---|---|---|
| Hand work and its data to another thread, results come back later | `thread::spawn` + `mpsc` channel | Ownership moves; no shared state to protect |
| Split a slice or collection across threads and join before returning | `thread::scope` | Threads borrow the data; the compiler checks the borrow ends at the scope |
| Many threads read data that never changes after construction | `Arc<T>`, or a `static` with `LazyLock`/`OnceLock` | No data lock for immutable contents; reference counts and memory access still have costs |
| Many threads update one small piece of state | `Arc<Mutex<T>>` with short critical sections | Simple, correct; measure before anything fancier |
| Readers vastly outnumber a rare writer and read sections are long | `RwLock<T>` as a candidate | Only a benchmark decides whether it beats `Mutex` |
| A counter, a flag, a sequence number | Atomic integer or `AtomicBool` | No lock, no blocking |
| One thread waits for a condition another thread produces | `Condvar` or a channel | Blocking wait without spinning |
| Data-parallel loops | `rayon` (crate) | Work stealing and splitting done for you |
| Many concurrent I/O operations | An async runtime (crate) | Threads per connection do not scale |

Crate choices for each row (`rayon`, `crossbeam`, async runtimes, sharded maps, lock replacements) are in [Choosing a Parallelism Library](#choosing-a-parallelism-library).

Widespread `Arc<Mutex<T>>` can indicate unclear ownership, but it can also represent genuinely shared mutable state. An owning task with message passing suits serialized updates; shared state suits overlapping access when its synchronization and lifetime are deliberate.

## Threads: spawn, scope, Builder

`thread::spawn` requires `'static` closures because the thread may outlive the caller. `thread::scope` (1.63) joins every spawned thread before returning, so closures may borrow local data.

```rust
use std::thread;

fn parallel_sum(values: &[u64], workers: usize) -> u64 {
    let chunk_len = values.len().div_ceil(workers.max(1)).max(1);
    thread::scope(|scope| {
        let handles: Vec<_> = values
            .chunks(chunk_len)
            .map(|chunk| scope.spawn(move || chunk.iter().sum::<u64>()))
            .collect();
        handles.into_iter().map(|h| h.join().expect("worker panicked")).sum()
    })
}

fn spawn_indexer(root: std::path::PathBuf) -> std::io::Result<thread::JoinHandle<usize>> {
    thread::Builder::new()
        .name("indexer".to_owned()) // shows up in panic messages and debuggers
        .stack_size(8 * 1024 * 1024) // deep recursion needs more than the 2 MiB default
        .spawn(move || std::fs::read_dir(root).map(|d| d.count()).unwrap_or(0))
}
```

- `JoinHandle::join` returns `Err(payload)` when the thread panicked (with `panic = "unwind"`); with `panic = "abort"` the process ends instead.
- Threads spawned with `spawn` are detached from their creator; a thread that outlives `main` is killed when the process exits.
- Since 1.91 a failure to set the stack size is returned as an error from `spawn`, and panic messages include the thread ID.
- Name long-lived threads; unnamed threads make profiles and crash logs hard to read.

## Channels

`std::sync::mpsc` gives multi-producer, single-consumer channels. `channel()` is unbounded (sends never block; memory grows if the consumer is slow); `sync_channel(n)` blocks the sender when `n` messages are queued, and `sync_channel(0)` is a rendezvous where each send waits for a receive.

```rust
use std::sync::mpsc;
use std::thread;

fn fan_in(inputs: Vec<Vec<u32>>) -> u32 {
    let (tx, rx) = mpsc::channel::<u32>();
    for input in inputs {
        let tx = tx.clone(); // multi-producer: one clone per worker
        thread::spawn(move || {
            let partial: u32 = input.iter().sum();
            let _ = tx.send(partial); // Err only when the receiver is gone
        });
    }
    drop(tx); // when the last Sender drops, `rx.iter()` ends
    rx.iter().sum()
}

fn bounded_pipeline(items: Vec<String>) -> usize {
    let (tx, rx) = mpsc::sync_channel::<String>(16); // backpressure at 16 queued items
    let producer = thread::spawn(move || {
        for item in items {
            if tx.send(item).is_err() {
                break; // consumer hung up: stop producing
            }
        }
    });
    let processed = rx.iter().filter(|s| !s.is_empty()).count();
    producer.join().expect("producer panicked");
    processed
}
```

- Dropping all senders ends `recv()`/`iter()` with `Err`/`None`; dropping the receiver makes `send` fail. Use these as the shutdown protocol instead of separate flags.
- `Receiver` is `Send` but not `Sync`: share it between worker threads with `Arc<Mutex<Receiver<T>>>`, or use a multi-consumer channel from `crossbeam` (`std::sync::mpmc` is unstable).
- `recv_timeout` and `try_recv` support polling loops; prefer blocking `recv` in a dedicated thread.
- Bounded channels turn a slow consumer into visible backpressure; unbounded channels turn it into memory growth.

## Send and Sync

`Send` means a value can move to another thread; `Sync` means `&T` can be shared between threads (`T: Sync` if and only if `&T: Send`). Both are auto traits: a type has them when all its fields do.

| Types | `Send` | `Sync` | Reason |
|---|---|---|---|
| Primitives and String | yes | yes | Transfer and shared access are supported |
| Vec<T>, Box<T>, Option<T>, arrays and tuples | if their elements/fields are Send | if their elements/fields are Sync | A container does not make its payload thread-safe |
| `Arc<T>` (`T: Send + Sync`), `Mutex<T>` (`T: Send`), `RwLock<T>` (`T: Send + Sync`), atomics | yes | yes | Synchronized internally |
| `mpsc::Sender<T>` (1.72+), `SyncSender<T>` | if T: Send | if T: Send | Messages move between threads; sender access is synchronized |
| `mpsc::Receiver<T>`, `Cell<T>`, `RefCell<T>`, `OnceCell<T>` | if T: Send | no | Transfer is different from concurrent shared access |
| `MutexGuard<T>`, `RwLockReadGuard<T>` | no | yes (if `T: Sync`) | Must be released on the locking thread |
| `Rc<T>`, `rc::Weak<T>` | no | no | Non-atomic reference count |
| `*const T`, `*mut T` | no | no | The compiler cannot know what the pointer protects |

Consequences: `Rc<RefCell<T>>` in a struct removes `Send`, so a later `thread::spawn` fails to compile; a `MutexGuard` cannot be held across an `.await` on a work-stealing runtime because the task may resume on another thread. A generic type's auto traits follow its parameters (`Vec<Rc<T>>` is not `Send`). Implementing `Send`/`Sync` by hand is `unsafe` and covered in [unsafe and FFI](unsafe-and-ffi.md#sharing-raw-pointers-across-threads).

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

## Sizing Thread Pools

`thread::available_parallelism()` estimates usable parallelism from the affinity mask and cgroup quota where the platform exposes them; it can over-count in containers and VMs, does not reflect current load, and is not cached. Query it once at startup and provide a configuration override.

```rust
use std::num::NonZeroUsize;
use std::thread;

fn worker_count(configured: Option<usize>) -> usize {
    configured
        .filter(|&n| n > 0)
        .unwrap_or_else(|| thread::available_parallelism().map(NonZeroUsize::get).unwrap_or(1))
}
```

CPU-bound pools use about one thread per core; blocking-I/O pools are sized by concurrency needs, not cores.

## Async Boundary

Choose the execution model, admission limits, cancellation ownership, and shutdown policy together. [Async and parallel execution](async-and-parallel-execution.md) contains the runtime comparison and a bounded task example.

- Long CPU loops, blocking I/O, and synchronous waits can monopolize an executor worker. Task submission and blocking for completion are different operations.
- Keep synchronous lock guards and RefCell borrows out of awaits that allow competing access. Local tasks remove some Send constraints, not the deadlock/reentrancy risk.
- Dropping an owned future stops polling it. Dropping a Tokio/std JoinHandle detaches its task/thread; it does not stop that work. Started spawn_blocking work cannot be aborted by dropping or aborting its handle.
- Read the cancellation-safety contract of operations used in select loops; an externally owned future borrowed into a branch can survive selection.
- Desktop runtime assumptions do not apply to browser event loops or embedded executors. Async does not inherently require std.

## Choosing a Parallelism Library

Use the [curated library policy](library-selection.md) and [execution-model comparison](async-and-parallel-execution.md). Start from the simplest design meeting the requirement, including the cost of maintaining std-only scheduling or synchronization code.

| Need | Starting choice | Reason to change |
|---|---|---|
| A small borrowed batch | std::thread::scope | Rayon can manage uneven/recursive CPU work and reusable pools |
| One-consumer bounded pipeline | std::sync::mpsc::sync_channel | Crossbeam adds multiple consumers and channel selection; flume adds sync/async bridging |
| Many I/O waiters | Tokio or smol according to integrations | Existing runtime, host event loop, or no_std may dictate another execution model |
| Shared map | `Mutex<HashMap<..>>` with a small critical section | Measured contention may justify partitioning, ownership transfer, or an eligible concurrent map |
| Rarely replaced immutable configuration | Arc snapshot with a short synchronization boundary | arc-swap can provide a specialized publication mechanism |

Third-party shared-state choices are conditional: parking_lot changes locking/poisoning behavior, dashmap uses shard locks with guard/deadlock constraints, and arc-swap serves snapshot publication. They are not interchangeable performance upgrades. Keep callbacks and unrelated waits outside guards; understand the chosen crate's lock order and snapshot consistency.

Crossbeam's queues and epoch reclamation are building blocks for specialized structures; prefer an ordinary lock or channel when it meets the contract. For custom atomic protocols, loom can explore modeled interleavings and Miri can detect some execution violations; neither proves arbitrary lock-free code correct.

For interrupt sharing and missing atomics, follow the actual target/HAL synchronization contract in [embedded guidance](embedded-and-no-std.md). Do not replace it with a spinlock or unsafe Sync declaration solely to satisfy the type checker.

## Deadlocks and Liveness

Deadlocks and leaks are not undefined behavior but they are bugs. Rules that prevent most of them:

- Acquire locks in one global order; document it where two locks are ever held together.
- Avoid callbacks and foreign destructors while holding locks. Do not suspend with a synchronous guard that competing work needs; an async guard across await requires a deliberate locking design.
- Prefer `try_lock` with a fallback where liveness matters more than throughput.
- Use channels or a single owner instead of two locks that reference each other.
- Every `Condvar::wait` sits in a predicate loop; every waiter has a notifier that runs after the predicate changes.
- `parking_lot` offers Mutex/RwLock variants with different poisoning and fairness behavior. Compare the relevant contention pattern before changing synchronization libraries; the replacement also changes semantics.

## Common Mistakes

- `Arc<Mutex<T>>` where a single owning thread with a channel would remove the lock entirely.
- Holding a guard across I/O, a callback, or `.await`.
- `let _ = lock.lock()`, which releases the lock on the same line.
- Choosing `RwLock` for "read-heavy" code without measuring; nesting `read()` calls.
- `SeqCst` everywhere as a substitute for understanding which operations pair.
- Spinning on an atomic without `std::hint::spin_loop()` or a fallback to blocking (Clippy `missing_spin_loop`, perf).
- Unbounded channels feeding a consumer that can fall behind.
- Wrapping a non-`Send`/`Sync` type in `Arc` and expecting thread safety (Clippy `arc_with_non_send_sync`, suspicious).
- Assuming `available_parallelism()` equals physical cores inside a container.

## Availability by Version

| Version | Addition |
|---|---|
| 1.63 | `thread::scope`; const `Mutex::new`, `RwLock::new`, `Condvar::new` |
| 1.70 | `OnceLock`, `OnceCell` |
| 1.72 | `mpsc::Sender` is `Sync` |
| 1.77 | `Mutex::clear_poison` |
| 1.80 | `LazyLock`, `LazyCell` |
| 1.81 | `AtomicBool::fetch_not` |
| 1.85 | Async closures, `AsyncFn` traits; `Future`/`IntoFuture` in the edition 2024 prelude |
| 1.86 | `Once::wait`, `OnceLock::wait` |
| 1.91 | `AtomicPtr::fetch_ptr_add` and bitwise `fetch_*`; thread ID in panic messages; `Builder::stack_size` errors instead of panicking |
| 1.92 | `RwLockWriteGuard::downgrade` |
| 1.94 | `LazyLock::get`, `get_mut`, `force_mut` |
| 1.95 | `Atomic*::update`, `try_update` |
| 1.98 | `Atomic<T>::from_mut`, `from_mut_slice`, `get_mut_slice` |

Per-release details live in [the versions index](../versions/index.md).

## Practical Boundaries

A synchronization primitive protects a particular access protocol. Guard lifetime, lock ordering, callback reentrancy, and panic recovery affect that protocol independently of the primitive's throughput. RwLock is useful for some read-heavy access patterns, but its scheduling and contention costs still matter.

Atomic ordering describes synchronization between operations; it does not turn a sequence of updates into a transaction. Queues and task limits also bound different resources: item count, payload bytes, waiting work, and retained results may each need a limit. Shutdown behavior follows ownership of senders, workers, and in-progress side effects.

Interleaving exploration and Miri can exercise supported synchronization behavior; neither replaces the protocol's argument or establishes every application execution. See [execution patterns](async-and-parallel-execution.md) for async-specific boundaries.
