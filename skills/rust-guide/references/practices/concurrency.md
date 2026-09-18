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
- [Review Checklist](#review-checklist)

Examples compile on stable Rust 1.80 or later with edition 2024 unless a version is stated. Blocks marked `ignore` need an async runtime crate. Manual `unsafe impl Send`/`Sync` continues in [unsafe and FFI](unsafe-and-ffi.md); contention found in a profile continues in [performance](performance.md).

## Choosing a Model

| Data movement | Default tool | Why |
|---|---|---|
| Hand work and its data to another thread, results come back later | `thread::spawn` + `mpsc` channel | Ownership moves; no shared state to protect |
| Split a slice or collection across threads and join before returning | `thread::scope` | Threads borrow the data; the compiler checks the borrow ends at the scope |
| Many threads read data that never changes after construction | `Arc<T>`, or a `static` with `LazyLock`/`OnceLock` | No lock needed; sharing is free after the clone |
| Many threads update one small piece of state | `Arc<Mutex<T>>` with short critical sections | Simple, correct; measure before anything fancier |
| Readers vastly outnumber a rare writer and read sections are long | `RwLock<T>` as a candidate | Only a benchmark decides whether it beats `Mutex` |
| A counter, a flag, a sequence number | Atomic integer or `AtomicBool` | No lock, no blocking |
| One thread waits for a condition another thread produces | `Condvar` or a channel | Blocking wait without spinning |
| Data-parallel loops | `rayon` (crate) | Work stealing and splitting done for you |
| Many concurrent I/O operations | An async runtime (crate) | Threads per connection do not scale |

Crate choices for each row (`rayon`, `crossbeam`, async runtimes, sharded maps, lock replacements) are in [Choosing a Parallelism Library](#choosing-a-parallelism-library).

When `Arc<Mutex<T>>` starts appearing on most types, the ownership tree is missing: give the data one owning thread or task and let others send messages to it. The Comprehensive Rust course frames it as channels for transfer, shared state only when data must truly be shared.

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
| Primitives, `String`, `Vec<T>`, `Box<T>`, `Option<T>`, tuples and arrays of such types | yes | yes | Plain data |
| `Arc<T>` (`T: Send + Sync`), `Mutex<T>` (`T: Send`), `RwLock<T>` (`T: Send + Sync`), atomics | yes | yes | Synchronized internally |
| `mpsc::Sender<T>` (1.72+), `SyncSender<T>` | yes | yes | Internally synchronized |
| `mpsc::Receiver<T>`, `Cell<T>`, `RefCell<T>`, `OnceCell<T>` | yes | no | Unsynchronized interior mutability; fine to move, not to share |
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
| `SeqCst` | any | `Acquire`/`Release` plus one global order of all `SeqCst` operations; needed only when a proof depends on that total order |

```rust
use std::sync::atomic::{AtomicBool, AtomicU32, AtomicU64, Ordering};

static REQUESTS: AtomicU64 = AtomicU64::new(0);

fn count_request() -> u64 {
    // Relaxed: nothing else is published through this counter.
    REQUESTS.fetch_add(1, Ordering::Relaxed) + 1
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
        (current < max).then_some(current + 1)
    })
}
```

Happens-before relationships you can rely on (from Rust Atomics and Locks): everything in a thread before `spawn` happens-before the spawned thread's body; the body happens-before `join` returns; unlocking a mutex happens-before the next lock of that mutex; an `Acquire` load that reads a `Release` store's value happens-after everything before that store.

Misconceptions the same book refutes:

- Stronger ordering does not make writes visible sooner; the model "doesn't say anything about timing at all". `Relaxed` stores are not delayed.
- Disabling optimizations or running on an in-order CPU does not remove the need for ordering; the compiler still reorders, and caches still reorder visibility.
- `Relaxed` is not free when several cores write the same cache line; the contention is the cost, not the instruction.
- `SeqCst` is not "the safe default": it is correct wherever a weaker ordering is correct, but it claims a global order the algorithm rarely needs and hides which operations synchronize. Treat it "as a warning sign" in review.
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

Rust has no built-in runtime: "a runtime is just another crate". Futures are inert until polled; nothing runs without an executor. This guide covers the language-level rules; task spawning, timers, and I/O types come from the runtime's documentation.

- Never block the executor. `std::thread::sleep`, synchronous file or socket I/O, and long CPU loops inside `async fn` stall every task on that worker. Use the runtime's async equivalents or move the work to its blocking pool.
- Do not hold a `std::sync::MutexGuard` (or a `RefCell` borrow) across `.await`: the task may be suspended while holding it, blocking other tasks, and on a multi-threaded runtime the future would not be `Send`. Clippy `await_holding_lock` and `await_holding_refcell_ref` (suspicious) flag it. Take the lock, copy what you need, drop the guard, then await; or use the runtime's async mutex when the lock must span an await.
- Cancellation is `drop`: a future dropped at an `.await` never resumes. Every await point is a possible exit, so avoid half-applied state across awaits, use guards for cleanup, and treat `select!` losers as cancelled work.
- Tasks on work-stealing runtimes need `Send` futures: values held across `.await` must be `Send`, which excludes `Rc`, `RefCell` borrows, and lock guards.
- `async fn` in traits (1.75) is not dyn-compatible without boxing; return `Pin<Box<dyn Future<Output = T> + Send + '_>>` or use the `async_trait` crate for trait objects. Async closures and `AsyncFn` bounds are stable since 1.85.
- `Pin` promises that a value "must remain, valid, at that same address in memory, until its `drop` handler is called"; self-referential futures rely on it. Application code rarely needs `Pin` beyond `Box::pin` and `pin!`.

```rust,ignore
// Blocking work inside an async context, Tokio shown as one runtime's spelling.
async fn checksum_file(path: std::path::PathBuf) -> std::io::Result<u32> {
    // Wrong: blocks the executor thread while the OS reads the file.
    // let bytes = std::fs::read(&path)?;

    // Right: the runtime's blocking pool runs the synchronous read.
    let bytes = tokio::task::spawn_blocking(move || std::fs::read(&path))
        .await
        .expect("blocking task panicked")?;
    Ok(bytes.iter().map(|&b| u32::from(b)).sum())
}
```

## Choosing a Parallelism Library

Start with `std`; add a crate only for a capability `std` lacks. Since 1.63 `std` has scoped threads, since 1.67 its `mpsc` channel is the `crossbeam-channel` design, and since 1.70/1.80 it has `OnceLock`/`LazyLock`, so several crates that used to be mandatory are now optional. Everything in this section is ecosystem material: verify the crate's current documentation for exact APIs, and treat any "faster" claim as `needs benchmark`.

| Work shape | `std` answer | Crate when `std` is not enough | Why the crate |
|---|---|---|---|
| Split a collection across cores and reduce | `thread::scope` over `chunks` | `rayon` (`par_iter`, `par_chunks`, `par_sort`, `join`, `scope`) | Work stealing balances uneven work and recursive splits; no hand-rolled pool |
| Pool of independent CPU tasks | `thread::scope` or `spawn` per batch | `rayon::ThreadPool`, `rayon::spawn` | Reusable pool with a fixed size |
| Pipeline with one consumer | `mpsc::sync_channel` | none | Bounded `std` channel already gives backpressure |
| Several consumers, waiting on many channels, timeouts | `Arc<Mutex<Receiver>>`, polling loops | `crossbeam-channel` (`select!`, `tick`, `after`, cloneable `Receiver`) or `flume` (same, plus async methods) | `std` has no stable multi-consumer channel or `select` |
| Thousands of concurrent I/O operations | none | `tokio` (default in the ecosystem), `smol` (small footprint); `async-std` is discontinued and its maintainers point to `smol` | Multiplexes many waiting operations on a few threads |
| CPU-heavy or blocking work from async code | none | `tokio::task::spawn_blocking` for blocking calls; a `rayon` pool bridged with `oneshot` for parallel compute | The executor must never block |
| Read-mostly shared configuration | `Arc<T>` swapped behind a `Mutex` | `arc-swap` (`ArcSwap<T>`: lock-free `load`, atomic `store`) | Readers never contend with the rare writer |
| Concurrent map with many writers from many threads | `Mutex<HashMap>` or hand-made sharding | `dashmap` (sharded `RwLock` map) | Per-shard locking; check its deadlock rules before use |
| Lock contention measured under `std::sync` | keep `Mutex`, shrink critical sections | `parking_lot` (`Mutex`, `RwLock`, `Condvar`; no poisoning, smaller, fair unlocking) | The Performance Book: "measure before switching to `parking_lot`" |
| Lock-free queues, memory reclamation for lock-free structures | none | `crossbeam-queue` (`ArrayQueue`, `SegQueue`), `crossbeam-epoch` | Only with a demonstrated need and Miri/`loom` coverage |
| 64-bit atomics on a 32-bit target, `no_std` synchronization | `cfg(target_has_atomic)` fallbacks | `portable-atomic`; `spin`, `critical-section`, `heapless` on embedded targets | Polyfills and interrupt-safe primitives |
| Testing lock-free protocols | many-thread tests, Miri | `loom` | Exhaustive interleaving model checking of `loom::sync` types |

Selection rules:

1. Shape first: data parallelism (`rayon`), message passing (`std` or `crossbeam` channels), I/O concurrency (an async runtime). A service usually needs an async runtime for I/O plus `spawn_blocking` or a compute pool for CPU work; a batch tool usually needs `rayon` and nothing async.
2. Blocking and async do not mix inside one thread: `rayon`, `std::thread`, and `crossbeam` block; calling them from an async task blocks that executor thread. Bridge with `spawn_blocking` or a `oneshot` channel.
3. Ecosystem decides the runtime: `hyper`, `axum`, `tonic`, `reqwest`, and most database drivers assume `tokio`. A library that must stay runtime-agnostic uses the `futures` traits and feature-flags its runtime integrations.
4. Prefer the `std` type until a measurement or a missing capability says otherwise; every crate here adds compile time and an upgrade surface.
5. Portability: `rayon` and async runtimes need `std`; embedded targets use `heapless` queues, `critical-section`, and `portable-atomic`.

### rayon

```rust,deps
use rayon::prelude::*;
use rayon::ThreadPoolBuilder;

fn total_len(docs: &[String]) -> usize {
    docs.par_iter().map(|doc| doc.len()).sum()
}

fn build_compute_pool(threads: usize) -> rayon::ThreadPool {
    ThreadPoolBuilder::new()
        .num_threads(threads)
        .thread_name(|index| format!("compute-{index}"))
        .build()
        .expect("thread pool")
}

fn sorted_on(pool: &rayon::ThreadPool, mut values: Vec<u64>) -> Vec<u64> {
    pool.install(|| {
        values.par_sort_unstable();
        values
    })
}
```

- `par_iter()` on slices, `Vec`, `HashMap`, ranges, and other indexed collections; `par_bridge()` adapts a serial iterator at a cost. `rayon::join(a, b)` and `rayon::scope` express recursive fork-join.
- The global pool is sized from `available_parallelism`; configure it once with `ThreadPoolBuilder::build_global`, or build a dedicated pool and run work inside `pool.install`.
- CPU-bound closures only. Blocking I/O or a lock wait inside a rayon task idles a pool thread and can deadlock when the pool is saturated.
- Splitting has overhead: small inputs run slower in parallel. Parallelize above a size threshold, tune granularity with `with_min_len`, and measure.
- Floating-point reductions change association order, so sums differ between runs and thread counts; use integer accumulation or accept the non-determinism explicitly.
- From `tokio`, run rayon work through `spawn_blocking` or a dedicated pool and return the result over a `oneshot` channel (example below).

### crossbeam

```rust,deps
use crossbeam_channel::{bounded, select, tick, Receiver, Sender};
use std::time::Duration;

fn worker(jobs: Receiver<u32>, results: Sender<u32>) {
    let heartbeat = tick(Duration::from_secs(5));
    loop {
        select! {
            recv(jobs) -> job => match job {
                Ok(job) => {
                    let _ = results.send(job * 2);
                }
                Err(_) => break, // every Sender dropped: shut down
            },
            recv(heartbeat) -> _ => {
                // periodic housekeeping while idle
            }
        }
    }
}

fn start_workers(count: usize) -> (Sender<u32>, Receiver<u32>) {
    let (job_tx, job_rx) = bounded::<u32>(64);
    let (result_tx, result_rx) = bounded::<u32>(64);
    for _ in 0..count {
        let (jobs, results) = (job_rx.clone(), result_tx.clone()); // Receiver is Clone: multi-consumer
        std::thread::spawn(move || worker(jobs, results));
    }
    (job_tx, result_rx)
}
```

- `crossbeam-channel`: `select!` over several receivers and senders, `tick`/`after` timer channels, `bounded(0)` rendezvous, cloneable receivers for worker pools. `flume` offers the same shape with `send_async`/`recv_async` when one side is async.
- `crossbeam-utils`: `CachePadded<T>` to keep hot atomics on separate cache lines, `AtomicCell<T>` for small `Copy` values; its scoped threads are superseded by `std::thread::scope`.
- `crossbeam-queue` and `crossbeam-epoch` are for building lock-free structures, not for application code that a `Mutex<VecDeque>` already serves.

### tokio and other async runtimes

```rust,deps
use std::sync::Arc;
use tokio::sync::{oneshot, Semaphore};
use tokio::task::JoinSet;

async fn parallel_sum(input: Vec<u64>) -> u64 {
    // Heavy compute goes to rayon; the async task only waits for the answer.
    let (tx, rx) = oneshot::channel();
    rayon::spawn(move || {
        use rayon::prelude::*;
        let sum: u64 = input.par_iter().sum();
        let _ = tx.send(sum); // Err means the awaiting task was cancelled: nothing to do
    });
    rx.await.expect("compute task dropped the sender")
}

async fn file_len(path: std::path::PathBuf) -> std::io::Result<u64> {
    // Blocking std I/O runs on the runtime's blocking pool, not on the async worker threads.
    tokio::task::spawn_blocking(move || std::fs::metadata(path).map(|m| m.len()))
        .await
        .expect("blocking task panicked")
}

async fn process_all(items: Vec<String>, max_in_flight: usize) -> Vec<usize> {
    let limit = Arc::new(Semaphore::new(max_in_flight));
    let mut tasks = JoinSet::new();
    for item in items {
        let permit = Arc::clone(&limit).acquire_owned().await.expect("semaphore closed");
        tasks.spawn(async move {
            let _permit = permit; // released when the task finishes
            item.len() // stand-in for an awaited request
        });
    }
    let mut results = Vec::new();
    while let Some(joined) = tasks.join_next().await {
        results.push(joined.expect("task panicked"));
    }
    results
}
```

- Runtime flavors: `multi_thread` (work stealing; spawned futures must be `Send + 'static`) and `current_thread` (single thread; `LocalSet` runs `!Send` tasks).
- `tokio::sync::Mutex` only when a guard must be held across an `.await`; for short sections the `std` (or `parking_lot`) mutex is correct and cheaper, as the tokio documentation itself advises.
- Channels by purpose: `mpsc` (bounded for backpressure), `oneshot` (one result), `broadcast` (fan-out; slow receivers lag and drop), `watch` (latest value, ideal for configuration), plus `Semaphore` to cap concurrency and `Notify` for wakeups.
- `JoinSet` tracks a dynamic group of tasks; `select!` drops the losing branches, so every future in it must be cancellation-safe (no half-applied state at an `.await`).
- `smol` provides a smaller runtime built from `async-executor`, `async-io`, and `blocking`; `async-std` is discontinued. Library authors code against the `futures` traits and let applications pick the runtime.

### Shared-state crates

```rust,deps
use arc_swap::ArcSwap;
use dashmap::DashMap;
use parking_lot::Mutex;
use std::sync::Arc;

struct Config {
    rate_limit: u32,
}

struct Service {
    config: ArcSwap<Config>,         // read-mostly: lock-free loads, atomic replacement
    sessions: DashMap<u64, String>,  // many writers from many threads
}

static RECENT: Mutex<Vec<u32>> = Mutex::new(Vec::new()); // parking_lot: const new, no poisoning

impl Service {
    fn new(config: Config) -> Self {
        Service { config: ArcSwap::from_pointee(config), sessions: DashMap::new() }
    }

    fn rate_limit(&self) -> u32 {
        self.config.load().rate_limit // no clone of Config, no lock
    }

    fn reload(&self, next: Config) {
        self.config.store(Arc::new(next)); // readers see the old or the new value, never a mix
    }

    fn touch(&self, id: u64, user: &str) {
        self.sessions
            .entry(id)
            .and_modify(|current| current.clear())
            .or_insert_with(|| user.to_owned());
        RECENT.lock().push(id as u32);
    }

    fn user(&self, id: u64) -> Option<String> {
        // Clone out and drop the Ref immediately: holding it while calling into the same map
        // again can deadlock on the shard lock, and it must never live across an .await.
        self.sessions.get(&id).map(|entry| entry.value().clone())
    }
}
```

- `arc-swap`: `load()` returns a cheap guard; `store` swaps the whole `Arc`; `rcu` performs read-copy-update. Fits configuration, routing tables, feature flags.
- `dashmap`: sharded map with a `HashMap`-like API; a `Ref`/`RefMut` holds a shard lock, so never hold one while touching the same map again or across `.await`; iteration locks shards one at a time. Not a replacement for a `Mutex<HashMap>` when the map is small or rarely contended.
- `parking_lot`: drop-in `Mutex`/`RwLock`/`Condvar` with no poisoning (a panic while locked leaves the data as is), one-byte mutexes, `ReentrantMutex`, and fair unlocking. Adopt only after measuring contention with `std::sync`.

### Embedded and testing crates

- `portable-atomic` supplies `AtomicU64`, `AtomicU128`, and float atomics on targets that lack them, with a critical-section fallback on single-core chips.
- `spin` gives spinlocks for `no_std`; on a preemptive OS a spinlock in user space is almost always the wrong choice.
- `heapless` provides fixed-capacity queues (`spsc::Queue`) and maps without allocation; `critical-section` abstracts interrupt masking for interrupt-safe sharing.
- `loom` runs a test body under every interleaving of its `loom::sync` replacements (`cfg(loom)` swaps the imports); use it for anything hand-built from atomics, alongside Miri for data-race detection.

```rust,ignore
#[cfg(loom)]
mod loom_tests {
    use loom::sync::atomic::{AtomicBool, Ordering};
    use loom::sync::Arc;

    #[test]
    fn flag_is_published() {
        loom::model(|| {
            let ready = Arc::new(AtomicBool::new(false));
            let writer = Arc::clone(&ready);
            loom::thread::spawn(move || writer.store(true, Ordering::Release));
            let _seen = ready.load(Ordering::Acquire); // loom explores both outcomes
        });
    }
}
```

## Deadlocks and Liveness

Deadlocks and leaks are not undefined behavior (the Reference lists them as safe), but they are bugs. Rules that prevent most of them:

- Acquire locks in one global order; document it where two locks are ever held together.
- Never call user callbacks, `Drop` implementations of foreign types, or async awaits while holding a lock.
- Prefer `try_lock` with a fallback where liveness matters more than throughput.
- Use channels or a single owner instead of two locks that reference each other.
- Every `Condvar::wait` sits in a predicate loop; every waiter has a notifier that runs after the predicate changes.
- The `parking_lot` crate offers `Mutex`/`RwLock` without poisoning and with different fairness; the Performance Book advises to "measure before switching" because std primitives have improved.

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

## Review Checklist

- Each shared value has a reason to be shared; transfers use channels or moves.
- Guards are named, short-lived, and never cross I/O, callbacks, or `.await`.
- Poisoning is handled deliberately (recover or propagate) rather than unwrapped by habit.
- `RwLock` choices and `parking_lot` replacements are backed by a benchmark.
- Every atomic's ordering is justified in a comment; `SeqCst` has a reason.
- Channel shutdown relies on sender/receiver drop, and bounded channels exist where backpressure matters.
- Async code never blocks the executor and never holds sync guards across awaits.
- Tests run under Miri for lock-free code and with more threads than cores for lock code.
