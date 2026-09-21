# Memory and Allocation

## Contents

- [Storage, Allocation, and Release](#storage-allocation-and-release)
- [Choose Storage and Lifetime Together](#choose-storage-and-lifetime-together)
- [Find the Actual Allocation Path](#find-the-actual-allocation-path)
- [Reuse Without Unbounded Retention](#reuse-without-unbounded-retention)
- [Fallible Allocation at an Input Boundary](#fallible-allocation-at-an-input-boundary)
- [A Bounded Buffer Pool with Automatic Return](#a-bounded-buffer-pool-with-automatic-return)
- [Arena and Pool Trade-offs](#arena-and-pool-trade-offs)
- [Allocator Selection](#allocator-selection)
- [Target and API Boundaries](#target-and-api-boundaries)

## Storage, Allocation, and Release

Ownership identifies who manages a value; its representation determines where its storage lives. Inline data lives inside its owner, which may itself be local, static, or heap allocated. Vec and String own a separately allocated buffer when capacity is needed, while a slice or string reference describes borrowed storage. A move transfers ownership rather than duplicating that buffer.

Growth beyond capacity may allocate and relocate a buffer. `clear` drops elements while retaining capacity; dropping the owning collection releases its allocation to the allocator. Neither action promises an immediate reduction in process RSS. This distinction explains why reuse helps repeated work yet can retain an unusually large allocation.

Evaluate allocation frequency, bytes per allocation, peak live data, and retained capacity separately. Eliminating a copy can extend the lifetime of a much larger owner; using a large inline buffer can move pressure to stacks or containing objects. The patterns below trade these costs rather than treating zero allocations as a universal objective.

## Choose Storage and Lifetime Together

Start with lifetime and memory budget, then allocation count. Fewer allocator calls can mean more retained memory; copying a small result can release a large backing buffer sooner.

| Situation | Starting choice | Change the choice when |
|---|---|---|
| Read only during a call | Borrow a slice, string, or domain view | The result outlives the source or needs independent mutation |
| Fixed maximum size and predictable storage | Array or fixed-capacity collection | The bound is wasteful or cannot be justified |
| Variable-size owned sequence | `Vec<T>` with a justified capacity | Growth ends, sharing is required, or spare capacity matters |
| Owned immutable-length contents | `Box<[T]>` / `Box<str>` | Growth remains part of the API |
| Large immutable data shared by tasks | Scoped borrowing, otherwise `Arc<T>` where supported | A small copy avoids retaining a large allocation |
| Temporary objects die together | Consider an arena after measuring | Objects need individual destruction or escape the arena |
| Repeated objects with expensive setup | Consider a bounded pool | Reset costs, contention, or retained capacity outweigh reuse |
| Mostly tiny variable sequences | Evaluate eligible inline storage such as `smallvec` | Larger containing types hurt locality |

An array is inline in its owner, not necessarily on the stack: `Box<[T; N]>` owns one on the heap. A Vec's handle and element buffer have different storage. Empty vectors and zero-sized elements are exceptions to "every Vec allocates" reasoning. A Vec with positive capacity for a non-zero-sized element type owns a buffer; an empty Vec may still retain such a buffer.

## Find the Actual Allocation Path

Trace input, transformation, serialization, queues, and output. Inspect new `String`/`Vec` values, repeated `format!`, intermediate `collect`, boxed futures, and shared owners retaining buffers. `Arc::clone` increments a reference count instead of copying the payload; `clone` cost depends on its type.

Distinguish allocation count/bytes, peak live memory, retained capacity, and process RSS. Freeing Rust values does not necessarily return pages to the OS. Compiler optimization also prevents equating source-level allocations with measured allocator calls. Use [allocation profiling](performance.md#profiling) to distinguish those effects.

## Reuse Without Unbounded Retention

Reserve when the size estimate is credible. Validate untrusted lengths and account for element size and arithmetic overflow before reserving. `clear()` retains capacity; decide whether an unusually large buffer should survive the request.

```rust
fn join_lines(lines: &[&str], output: &mut String) {
    output.clear();
    for (index, line) in lines.iter().enumerate() {
        if index != 0 {
            output.push('\n');
        }
        output.push_str(line);
    }
}

fn release_oversized_buffer(output: &mut String, max_retained_bytes: usize) {
    if output.capacity() > max_retained_bytes {
        *output = String::new();
    } else {
        output.clear();
    }
}
```

Apply retention policy after the consumer finishes. Replacing the string gives up its allocation but does not guarantee lower RSS. `shrink_to_fit` also does not guarantee OS memory return.

Use `try_reserve` when reservation failure is recoverable. This covers that reservation, not every later allocation, dependency, or error-reporting path. An end-to-end recoverable out-of-memory contract requires auditing those other paths too.

## Fallible Allocation at an Input Boundary

A reservation error can be handled only before an infallible allocation occurs. Validate application limits and length arithmetic first, reserve storage with try_reserve, then use operations whose remaining capacity is sufficient. Formatting an error into a new String can itself allocate, so a recoverable allocation boundary should keep its immediate error representation small.

This packet encoder writes a little-endian u32 byte length followed by the payload. Its limit is supplied by the application; the wire length and total capacity are checked separately.

```rust
#[derive(Debug)]
pub enum EncodeError {
    TooLarge,
    CapacityOverflow,
    Allocation(std::collections::TryReserveError),
}

pub fn encode_packet(payload: &[u8], max_payload_bytes: usize) -> Result<Vec<u8>, EncodeError> {
    if payload.len() > max_payload_bytes {
        return Err(EncodeError::TooLarge);
    }
    let length = u32::try_from(payload.len()).map_err(|_| EncodeError::TooLarge)?;
    let capacity = payload.len().checked_add(4).ok_or(EncodeError::CapacityOverflow)?;
    let mut output = Vec::new();
    output.try_reserve_exact(capacity).map_err(EncodeError::Allocation)?;
    for byte in length.to_le_bytes() {
        output.push(byte);
    }
    for &byte in payload {
        output.push(byte);
    }
    Ok(output)
}
```

The push operations cannot need more than the reserved capacity. This establishes a narrow contract for constructing this Vec; it does not establish recoverable out-of-memory behavior for the surrounding process, allocator, runtime, logging, or dependencies. try_reserve can also fail for capacity constraints, not just physical-memory exhaustion.

For repeated writes, accept a caller-owned buffer and document whether an error leaves it empty, unchanged, or partially written. Reserving before mutation can preserve the old contents on a reservation failure. In-place reuse may still need an upper bound on retained capacity after an unusually large request.

## A Bounded Buffer Pool with Automatic Return

A pool is useful when buffers are repeatedly acquired and returned, and their retained capacity saves allocation work. It also retains memory while idle. The following worker-local pool permits several outstanding leases, returns storage during normal destruction/unwinding, and discards oversized backing buffers on return.

```rust
use std::cell::RefCell;

pub struct BufferPool {
    free: RefCell<Vec<Vec<u8>>>,
    max_retained_bytes: usize,
}

pub struct BufferLease<'a> {
    pool: &'a BufferPool,
    buffer: Option<Vec<u8>>,
}

impl BufferPool {
    pub fn new(slots: usize, max_retained_bytes: usize) -> Self {
        Self {
            free: RefCell::new((0..slots).map(|_| Vec::new()).collect()),
            max_retained_bytes,
        }
    }

    pub fn checkout(&self) -> Option<BufferLease<'_>> {
        let buffer = self.free.borrow_mut().pop()?;
        Some(BufferLease { pool: self, buffer: Some(buffer) })
    }
}

impl BufferLease<'_> {
    pub fn bytes(&mut self) -> &mut Vec<u8> {
        self.buffer.as_mut().expect("a live lease owns its buffer")
    }
}

impl Drop for BufferLease<'_> {
    fn drop(&mut self) {
        if let Some(mut buffer) = self.buffer.take() {
            buffer.clear();
            if buffer.capacity() > self.pool.max_retained_bytes {
                buffer = Vec::new();
            }
            self.pool.free.borrow_mut().push(buffer);
        }
    }
}
```

The pool's internal RefCell borrow lasts only for pop/push, not for the lease lifetime. No callback runs while that borrow is held. Its free-list capacity is allocated at construction; the private lease constructor ensures returning leases cannot exceed the original slot count. This pool is intentionally local to one thread: sharing it would require a different synchronization contract.

```rust
// Use with the BufferPool definition above.
fn encode_with_pool(pool: &BufferPool, input: &[u8], output: &mut Vec<u8>) -> bool {
    let Some(mut lease) = pool.checkout() else { return false };
    let scratch = lease.bytes();
    scratch.extend(input.iter().copied().filter(u8::is_ascii_alphanumeric));
    output.extend_from_slice(scratch);
    true // lease returns automatically, including if surrounding code unwinds
}
```

The slot limit bounds outstanding pooled buffers, not bytes in use. A checked-out Vec can grow beyond max_retained_bytes; that limit applies only on return. The example copy into output also allocates if necessary. Enforce request/output size limits separately for a bounded-memory service. Pool exhaustion can mean wait, reject, or use temporary storage; choose explicitly rather than hiding an unbounded fallback allocation.

RAII is not guaranteed to run on abort or mem::forget. Forgetting a lease leaks that buffer and permanently consumes a pool slot, but cannot expose freed memory. Resetting bytes with clear does not securely erase their old contents. Pools for secret data or resources with fallible reset need different policies.

## Arena and Pool Trade-offs

- An arena fits request-, parse-, frame-, or batch-scoped values. Check destructor behavior, reset rules, and escaping handles. Faster allocation does not justify unnecessarily extending object lifetimes.
- A pool needs bounded capacity, checkout/return ownership, state reset, exhaustion handling, and cancellation/panic cleanup. Shared pools add contention; per-worker pools can retain more memory overall.
- Ordinary owned values are often simpler for small counts or unrelated lifetimes. Do not build an unsafe allocator for an unmeasured cost. New dependencies follow [library selection](library-selection.md).

### Arena Lifetime: A Parse Request

For a parser, a request can own one arena of syntax nodes, with nodes referring to one another by arena-local indices. Appending to a Vec may move its buffer, but indices still identify the same elements if no elements are removed or reordered. References into that Vec cannot be kept across a potentially reallocating mutation.

```text
request owns input and node storage
    -> parse appends nodes and connects indices
    -> analysis borrows nodes while storage is stable
    -> export an owned result or keep the whole request alive
    -> drop/reset storage only after its users finish
```

An index newtype prevents confusing a node index with a byte offset; it does not automatically distinguish two arenas or detect a stale handle after reset. Keep handles private to their owner or add an owner/generation scheme when they cross boundaries. Individual deletion and reuse require an explicit stale-handle policy.

An ordinary Vec<Node> runs each node's destructor when cleared or dropped. Some bump allocation APIs reclaim bytes without running each object's Drop. That difference matters for files, locks, and nested heap allocations stored in nodes. Grouped lifetimes can simplify cleanup without justifying an unsafe allocator implementation.

Bulk reset also has a retention choice: keeping a parse arena at the largest document ever seen can dominate idle memory. Retain common capacities, discard outliers, and account for exported results that keep the original input or arena alive. Independent small owned results may use less long-lived memory than an otherwise zero-copy view.

## Allocator Selection

Establish whether allocation is the bottleneck before replacing an allocator. Compare representative size distributions, lifetimes, thread counts, and cross-thread frees. Measure throughput, tail latency, peak/RSS, fragmentation, startup, and binary size. Results from a server do not automatically apply to a CLI or firmware.

A global allocator must satisfy allocation layout/alignment, deallocation, and reallocation contracts across the whole program. Allocation methods must not unwind; logging or allocating recursively inside them can re-enter the allocator. `#[global_allocator]` is a final-program integration choice. A reusable library should leave that policy to consumers instead of imposing it as a hidden side effect. The default allocator is target/build dependent, not universally the OS allocator.

For an allocator integration, check supported targets, threading and cross-thread deallocation, linking, and allocation/deallocation ownership at FFI boundaries. New wrapper recommendations follow [library selection](library-selection.md); the underlying allocator's reputation does not establish a wrapper's compatibility. Existing allocator choices can remain appropriate for their measured workload.

## Target and API Boundaries

- `no_std` can use `alloc` with an allocator; see [embedded guidance](embedded-and-no-std.md).
- Wasm memory growth can invalidate JS views; see [WebAssembly](webassembly.md#memory-and-js-views).
- FFI allocation and deallocation need compatible owners and APIs.
- `&dyn Trait` need not allocate. Boxing and dynamic dispatch are separate decisions.
- Caller-owned output buffers and iterators can enable reuse; an owned result can be a better simple API.

State ownership, release point, common/worst-case size, full-buffer behavior, and retention policy. Check actual stack use before replacing heap storage with large local arrays.
