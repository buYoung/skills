# Concurrency

## Contents

- [Choosing a Model](#choosing-a-model)
- [Threads: spawn, scope, Builder](#threads-spawn-scope-builder)
- [Channels](#channels)
- [Send and Sync](#send-and-sync)
- [Sizing Thread Pools](#sizing-thread-pools)
- [Async Boundary](#async-boundary)
- [Choosing a Parallelism Library](#choosing-a-parallelism-library)
- [Common Mistakes](#common-mistakes)
- [Availability by Version](#availability-by-version)
- [Practical Boundaries](#practical-boundaries)

Examples use stable APIs unless marked otherwise; see [compatibility](../../SKILL.md#compatibility). Locks, lazy initialization, and atomics continue in [synchronization](synchronization.md); manual `unsafe impl Send`/`Sync` in [FFI](ffi.md#sharing-raw-pointers-across-threads); async execution is explained in [futures, tasks, and threads](async-and-parallel-execution.md#futures-tasks-and-threads).

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
| Many concurrent I/O operations | An async runtime (crate) | Each waiting operation would otherwise hold a thread and its stack; a few blocking operations can stay on threads |

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
- A thread started with `spawn` runs independently of its creator. Dropping its `JoinHandle` detaches the thread instead of stopping it, and a thread that outlives `main` is killed when the process exits.
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

Consequences: `Rc<RefCell<T>>` in a struct removes `Send`, so a later `thread::spawn` fails to compile; a `MutexGuard` cannot be held across an `.await` on a work-stealing runtime because the task may resume on another thread. A generic type's auto traits follow its parameters (`Vec<Rc<T>>` is not `Send`). Implementing `Send`/`Sync` by hand is `unsafe` and covered in [FFI](ffi.md#sharing-raw-pointers-across-threads).

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

## Common Mistakes

- `Arc<Mutex<T>>` where a single owning thread with a channel would remove the lock entirely.
- Unbounded channels feeding a consumer that can fall behind.
- Wrapping a non-`Send`/`Sync` type in `Arc` and expecting thread safety (Clippy `arc_with_non_send_sync`, suspicious).
- Assuming `available_parallelism()` equals physical cores inside a container.

## Availability by Version

| Version | Addition |
|---|---|
| 1.63 | `thread::scope` |
| 1.72 | `mpsc::Sender` is `Sync` |
| 1.85 | Async closures, `AsyncFn` traits; `Future`/`IntoFuture` in the edition 2024 prelude |
| 1.91 | Thread ID in panic messages; `Builder::stack_size` errors instead of panicking |

Per-release details live in [the versions index](../versions/index.md).

## Practical Boundaries

Queues and task limits bound different resources: item count, payload bytes, waiting work, and retained results may each need a limit. Shutdown behavior follows ownership of senders, workers, and in-progress side effects. See [execution patterns](async-and-parallel-execution.md) for async-specific boundaries.
