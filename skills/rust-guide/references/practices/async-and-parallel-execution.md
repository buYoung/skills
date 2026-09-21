# Async and Parallel Execution

## Contents

- [Futures, Tasks, and Threads](#futures-tasks-and-threads)
- [Select the Execution Model](#select-the-execution-model)
- [Runtime and Library Boundaries](#runtime-and-library-boundaries)
- [Borrowing and Task Ownership](#borrowing-and-task-ownership)
- [Pin and Unpin](#pin-and-unpin)
- [Blocking and CPU Work](#blocking-and-cpu-work)
- [Bound Each Resource](#bound-each-resource)
- [Cancellation Is an Ownership Contract](#cancellation-is-an-ownership-contract)
- [A Bounded Supervisor That Drains Admitted Work](#a-bounded-supervisor-that-drains-admitted-work)
- [Preserve Partial I/O Progress Across a Timeout](#preserve-partial-io-progress-across-a-timeout)
- [A CPU Pool Bridge with Admission Ownership](#a-cpu-pool-bridge-with-admission-ownership)
- [Channels, Locks, and Shutdown](#channels-locks-and-shutdown)

## Futures, Tasks, and Threads

An async function returns a Future containing the state needed to finish its computation. Polling advances it until it returns a result or yields `Pending`; a Waker lets an event notify the executor that another poll may make progress. Waiting should release the executor thread to do other work rather than spin or block it.

A task is a scheduled computation; a thread is an execution resource. Awaiting a future composes its work into the current task and does not spawn a new thread. Spawning gives work a separate scheduling and ownership boundary. A current-thread executor can interleave many I/O waiters, while CPU work needs multiple execution threads to run on multiple cores. Awaiting an immediately ready operation need not yield to other tasks.

These mechanisms give libraries different roles: runtimes drive tasks and I/O, compute pools divide CPU work, channels transfer values, and future combinators compose asynchronous operations. They often work together. The following patterns build on that distinction rather than treating every concurrency crate as a runtime alternative.

## Select the Execution Model

| Work shape | Starting choice | Choose differently when |
|---|---|---|
| A few blocking tasks or a simple batch | std threads, including `thread::scope` for borrowed data | Long-lived dynamic compute scheduling or many I/O waiters justify a pool/runtime |
| Many operations waiting for network I/O | Tokio or smol, aligned with dependencies | The environment supplies its own event loop or cannot provide std |
| Large independent CPU transformations | Rayon | Splitting overhead dominates, ordering requires serial work, or data dependencies prevent parallelism |
| Synchronous pipeline / work distribution | std MPSC or Crossbeam MPMC | Fan-out, latest-value delivery, or async waits require different channel semantics |
| Sync/async message bridge | flume, or appropriate runtime channels | Existing facilities already provide the required ownership and backpressure |
| Futures scoped to one operation | `join`/Stream composition, often futures utilities | Independently scheduled tasks need their own ownership and shutdown tracking |

Crossbeam is a set of concurrency building blocks, not an async runtime or a ready-made compute pool. Tokio concurrency does not make a long CPU loop cooperative. `join` within one task enables concurrent progress, not automatic CPU parallelism. The [curated choices](library-selection.md) distinguish these roles.

## Runtime and Library Boundaries

Choose Tokio when required I/O libraries already depend on its drivers/task facilities; evaluate smol when its components and compatibility adapters fit. A common Future trait does not make socket/timer implementations runtime-independent. Tokio and futures I/O traits are also distinct interfaces.

A runtime-independent library can return futures or accept an appropriate I/O/spawn interface, but do not create a portability abstraction without actual consumers. Pure async computation can be runtime-neutral while a database client remains runtime-bound.

## Borrowing and Task Ownership

A future can borrow data when the owner remains alive while that future is used. Independently scheduled tasks often need owned state because the caller can return before the task ends. Tokio's `spawn` requires `Send + 'static` for both the future and its output, including on a current-thread runtime. `'static` here means the type does not borrow shorter-lived external data; it does not require the value to live forever. `async move` moves its captures, but moving a reference does not turn the referenced value into owned data.

```rust,deps
// Requires tokio's rt feature; spawn_owned must be called inside a Tokio runtime.
use tokio::task::JoinHandle;

async fn text_len(text: &str) -> usize {
    text.len()
}

async fn use_borrowed(text: &str) -> usize {
    text_len(text).await
}

fn spawn_owned(text: String) -> JoinHandle<usize> {
    tokio::spawn(async move { text_len(&text).await })
}
```

The first wrapper borrows within its caller's lifetime; the spawned task owns its String and releases it normally when done. Shared ownership is useful when several tasks need the same data, not an automatic requirement of async code.

Send requirements concern captured state and values retained across suspension points. Narrowing a guard's scope can avoid retaining it across an await; it does not make an inherently thread-affine resource transferable. Local task facilities permit non-Send futures on their designated thread, with their own lifetime requirements. See [Send and Sync](concurrency.md#send-and-sync) and [diagnostics](lints-and-diagnostics.md#async-bounds-and-pinning).

## Pin and Unpin

Some futures can contain state whose validity depends on its address, such as references into their own stored data. For a type that is not Unpin, pinning establishes a contract that the pointee stays valid at its address until destruction. Moving a pointer to that value is distinct from moving the value itself. Unpin means the type does not require these pinning restrictions; it does not mean the type is Copy or thread-safe.

Ordinary `.await` usually hides the pinning machinery. When an API needs a pinned future, `pin!` can pin a local value and `Box::pin` gives pinned heap ownership. Pinning itself does not require allocation. A `Pin<Box<dyn Future<Output = T>>>` also erases the future's concrete type; that is a separate purpose with separate costs. Prefer these safe facilities to handwritten pinning or field projection unless implementing such an abstraction is the task.

## Blocking and CPU Work

Distinguish submission from waiting: `thread::spawn` and `rayon::spawn` submit work; blocking `join`, channel `recv`, and a Rayon parallel iterator's synchronous completion can occupy the caller. Judge the operation, not the crate name.

Use async I/O where supported. Move bounded-duration blocking APIs off async workers. `spawn_blocking` has a large default thread limit and can queue additional work; it is not admission control for an unlimited CPU workload. Bound submissions or use a compute pool. Persistent blocking loops often deserve dedicated threads.

Rayon can send a result to an async receiver through oneshot. Bound admitted jobs and decide what happens when the receiver disappears: the computation does not automatically stop. Account for contention between runtime workers, compute workers, and foreign-library pools; more threads than the CPU quota can hurt latency.

## Bound Each Resource

Track input queue length/bytes, admitted tasks, active external operations, and completed results separately. A semaphore acquired inside unlimited spawned tasks bounds active work but not waiting tasks and their captured payloads. Acquire before spawning, or limit the task set itself.

```rust,deps
// Requires tokio's rt feature. The body is a stand-in for a real async operation.
use std::num::NonZeroUsize;
use tokio::task::{JoinError, JoinSet};

async fn process_all(
    items: impl IntoIterator<Item = String>,
    max_in_flight: NonZeroUsize,
) -> Result<Vec<usize>, JoinError> {
    let mut tasks = JoinSet::new();
    let mut results = Vec::new();
    for item in items {
        if tasks.len() >= max_in_flight.get() {
            if let Some(result) = tasks.join_next().await {
                results.push(result?);
            }
        }
        tasks.spawn(async move { item.len() });
    }
    while let Some(result) = tasks.join_next().await {
        results.push(result?);
    }
    Ok(results)
}
```

The nonzero bound prevents a zero-permit stall; joining while submitting bounds retained task entries. Results are in completion order and the returned Vec still grows with input size. Stream them to a consumer for a bounded-output design. Payload byte size needs its own limit. On early return/drop, JoinSet requests cancellation of its async tasks; this is not rollback of side effects or termination of started blocking jobs.

## Cancellation Is an Ownership Contract

| Action | What it means | What it does not guarantee |
|---|---|---|
| Drop an owned future | Stop polling that future; drop its owned state | Undo previous I/O or cancel separately spawned work |
| Drop Tokio/std JoinHandle | Detach the associated task/thread | Stop its execution |
| Abort a Tokio async task | Request cancellation at a point the runtime can act | Immediate completion, rollback, or interruption of non-yielding code |
| Abort started spawn_blocking work | Does not stop the running closure | A timeout is not forced termination either |
| Drop a oneshot receiver | The result cannot be delivered through it | Stop the producer's computation |

Await a task's termination when completion of cancellation matters. A timeout around an owned JoinHandle may detach the task when the timeout drops the handle. Keep the handle, request cancellation where supported, and join according to the operation's cleanup policy. Blocking work needs cooperative checks or an underlying API with a suitable cancellation contract.

`select!` drops its branch futures, but a branch can own only `&mut` of an externally owned future/handle. That underlying value survives. In repeated selection, check the operation's cancellation safety: restarting a partially progressed read/write can lose progress. Use documented cancellation-safe operations or preserve progress explicitly.

## A Bounded Supervisor That Drains Admitted Work

Task ownership becomes clearer when admission, execution, and shutdown live in one scope. This supervisor accepts a bounded input channel, runs at most max_in_flight timer jobs, stops admission when the shutdown value becomes true or its sender disappears, discards queued work, and waits for already admitted jobs. Timer jobs genuinely suspend, so other tasks can make progress during the wait.

```rust,deps
// Tokio features: rt, sync, time, macros. Call inside a Tokio runtime with time enabled.
use std::{num::NonZeroUsize, time::Duration};
use tokio::{sync::{mpsc, watch}, task::JoinSet};

pub struct Job {
    pub delay: Duration,
}

#[derive(Debug, Default)]
pub struct RunReport {
    pub completed: usize,
    pub failed: usize,
}

pub async fn supervise(
    mut input: mpsc::Receiver<Job>,
    mut shutdown: watch::Receiver<bool>,
    max_in_flight: NonZeroUsize,
) -> RunReport {
    let mut tasks = JoinSet::new();
    let mut report = RunReport::default();
    loop {
        if *shutdown.borrow() { break; }
        tokio::select! {
            biased;
            changed = shutdown.changed() => {
                if changed.is_err() || *shutdown.borrow() { break; }
            }
            result = tasks.join_next(), if !tasks.is_empty() => {
                match result {
                    Some(Ok(())) => report.completed += 1,
                    Some(Err(_)) => report.failed += 1,
                    None => {}
                }
            }
            job = input.recv(), if tasks.len() < max_in_flight.get() => {
                match job {
                    Some(job) => { tasks.spawn(async move { tokio::time::sleep(job.delay).await; }); }
                    None => break,
                }
            }
        }
    }
    input.close();
    drop(input); // queued jobs are discarded under this shutdown policy
    while let Some(result) = tasks.join_next().await {
        match result {
            Ok(()) => report.completed += 1,
            Err(_) => report.failed += 1,
        }
    }
    report
}
```

Create the channel with mpsc::channel(capacity); a producer's send().await then waits when the queue fills. The channel limit bounds queued jobs, and the JoinSet limit bounds admitted jobs; the producer may additionally own an item waiting to be sent. Real payload sizes and producer count need their own limits. This report stores counts rather than an ever-growing Vec of completed results.

The watch value is a monotonic shutdown request: set true once, then leave it true. The initial-value check matters if shutdown was already requested before supervise started. Biased selection gives a ready shutdown branch priority, while completed tasks are collected before new admission. Normal channel exhaustion also ends admission and drains the active set.

Draining is a policy choice, not a universal shutdown strategy. For cancel-and-join, request cancellation of async tasks and observe every join result. Started blocking jobs need cooperative cancellation. If the caller drops the supervisor itself, its JoinSet is dropped and requests cancellation instead of performing this drain loop; the outer owner must await the supervisor when graceful completion matters. A hard shutdown deadline cannot be promised for arbitrary uncancellable work.

## Preserve Partial I/O Progress Across a Timeout

A timeout drops the future it owns. If that future owns the only record of partial progress, restarting the operation may discard or duplicate data. Keep progress in caller-owned state and use an operation with suitable cancellation semantics. Tokio AsyncReadExt::read is cancellation-safe in select; read_exact does not provide the same progress guarantee.

```rust,deps
// Tokio features: io-util. A surrounding timeout additionally needs time and a runtime.
use tokio::io::{self, AsyncRead, AsyncReadExt};

pub async fn fill_frame<R: AsyncRead + Unpin>(
    reader: &mut R,
    bytes: &mut [u8],
    filled: &mut usize,
) -> io::Result<()> {
    if *filled > bytes.len() {
        return Err(io::Error::new(io::ErrorKind::InvalidInput, "invalid progress offset"));
    }
    while *filled < bytes.len() {
        let count = reader.read(&mut bytes[*filled..]).await?;
        if count == 0 {
            return Err(io::Error::new(io::ErrorKind::UnexpectedEof, "incomplete frame"));
        }
        *filled += count; // recorded before another suspension point
    }
    Ok(())
}
```

A caller retains the buffer and filled offset around timeout(duration, fill_frame(...)). On timeout, the already recorded prefix remains valid and a later call resumes from that offset. This pattern assumes the same reader, buffer contents, and framing contract survive. Replacing the connection, resetting the buffer, or changing frame length needs an explicit recovery policy. EOF and I/O errors are also different from a timeout.

Cancellation-safe read means losing a pending read does not consume bytes through that operation. It does not roll back earlier successful reads or prevent the remote peer from doing work. A write-side protocol may likewise need an offset and a decision about whether partially sent messages can be retried safely.

## A CPU Pool Bridge with Admission Ownership

An async semaphore can limit CPU jobs, but its permit must remain owned by the running job. Releasing it when an awaiting request times out would admit replacements while the old work is still running. This bridge keeps the permit inside a Rayon job and reports an unwinding panic as an error.

```rust,deps
// Requires rayon and Tokio features rt, sync.
use std::{panic::{catch_unwind, AssertUnwindSafe}, sync::Arc};
use tokio::sync::{oneshot, Semaphore};

#[derive(Debug)]
pub enum CpuError { AdmissionClosed, Panicked, ResultLost }

pub async fn run_cpu<F, T>(slots: Arc<Semaphore>, job: F) -> Result<T, CpuError>
where
    F: FnOnce() -> T + Send + 'static,
    T: Send + 'static,
{
    let permit = slots.acquire_owned().await.map_err(|_| CpuError::AdmissionClosed)?;
    let (send, receive) = oneshot::channel();
    rayon::spawn(move || {
        let _permit = permit;
        let result = catch_unwind(AssertUnwindSafe(job)).map_err(|_| CpuError::Panicked);
        let _ = send.send(result);
    });
    receive.await.map_err(|_| CpuError::ResultLost)?
}
```

Dropping the receiver makes delivery fail, but the job keeps its permit until it finishes. With panic=abort, catch_unwind cannot provide recovery. AssertUnwindSafe here allows converting a job's unwind into a result; shared state modified by that job still needs its own invariant/recovery policy. Unhandled Rayon spawn panics have a pool panic policy, which is why the boundary is explicit.

Initialize the semaphore with the intended positive job limit; zero permits intentionally prevents admission until permits are added. This bounds admitted CPU closures, not callers waiting for permits with large captured inputs. Bound the upstream queue too. A custom Rayon pool may be appropriate for CPU quotas or isolation; count its workers together with runtime and native-library workers. For a small number of blocking library calls, spawn_blocking can be simpler than introducing a separate compute pool.

## Channels, Locks, and Shutdown

Choose semantics: work queues deliver each message to one consumer; broadcast delivers to subscribers with lag policy; watch stores a latest value; oneshot returns one result. Bounded item count does not bound bytes for arbitrarily sized messages.

For a short uncontended data-only critical section without awaits, a std mutex can be appropriate inside async code. Consider an async mutex or a single owning task when waiting itself must yield or the protected operation spans awaits. Minimize contention instead of replacing every lock mechanically.

Shutdown needs: stop new admission, signal producers/workers, decide drain versus discard, handle outstanding side effects, and observe termination. Dropping one sender is insufficient when clones remain. Do not promise a bounded shutdown time for uncancellable blocking calls.

Embedded async and browser event loops have different facilities. Continue with [embedded](embedded-and-no-std.md) or [Wasm](webassembly.md), not a desktop-runtime assumption.
