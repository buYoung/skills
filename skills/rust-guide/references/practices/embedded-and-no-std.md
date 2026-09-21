# Embedded and no_std

## Contents

- [Language Facilities and Platform Responsibilities](#language-facilities-and-platform-responsibilities)
- [Classify the Actual Target](#classify-the-actual-target)
- [Keep the Portable Core Honest](#keep-the-portable-core-honest)
- [A Fixed-Capacity Protocol State Machine](#a-fixed-capacity-protocol-state-machine)
- [Driver, Board, and Application Boundaries](#driver-board-and-application-boundaries)
- [Memory and Execution Budgets](#memory-and-execution-budgets)
- [Interrupts, Atomics, and Shared State](#interrupts-atomics-and-shared-state)
- [DMA, Failure, and Hardware Validation](#dma-failure-and-hardware-validation)

## Language Facilities and Platform Responsibilities

`#![no_std]` selects core-based facilities instead of automatically linking std. Ownership, borrowing, traits, and ordinary Rust control flow remain available. `alloc` supplies allocating containers when the final environment provides a usable allocator; bare-metal startup, memory layout, peripherals, and panic behavior still belong to the platform integration.

Patterns such as caller-owned buffers, fixed-capacity queues, and explicit state machines make resource limits visible. Their benefit is predictable ownership and capacity, not a guarantee that any heap-free program meets a deadline or fits a device's memory.

## Classify the Actual Target

| Environment | Available foundation | Main constraints |
|---|---|---|
| Bare-metal, no allocator | `core`, static/inline storage | RAM/flash/stack budgets, interrupts, fixed capacities |
| no_std with an allocator | `core` + `alloc` | Allocation latency/failure, fragmentation, retained memory |
| Hosted embedded OS | Often `std`, subject to target support | OS capabilities, power, memory, scheduling and I/O limits |

Embedded is not synonymous with no_std, and no_std is not synonymous with no heap. Identify MCU/CPU, board, target triple, runtime/RTOS, startup/linker configuration, atomic support, and timing requirements.

## Keep the Portable Core Honest

Put data transformation and protocol state machines behind core-compatible types when shared across host and firmware. Hardware adapters own registers, clocks, interrupts, pins, and DMA configuration. A portable driver interface such as embedded-hal can help across supporting HAL implementations; it does not configure an arbitrary board for you.

```rust
// Rust 1.81+ for core::error::Error; compile as a library.
#![no_std]

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct FrameTooLarge;

impl core::fmt::Display for FrameTooLarge {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        f.write_str("frame exceeds output capacity")
    }
}

impl core::error::Error for FrameTooLarge {}

pub fn copy_frame(input: &[u8], output: &mut [u8]) -> Result<usize, FrameTooLarge> {
    if input.len() > output.len() {
        return Err(FrameTooLarge);
    }
    output[..input.len()].copy_from_slice(input);
    Ok(input.len())
}
```

This API allocates nothing and makes capacity failure explicit; the caller chooses where the storage lives. It is not a board driver. On older MSRVs the error can remain a concrete type without that Error implementation.

For a reusable crate, feature-gate `std` and `alloc` separately when both configurations are supported. Audit transitive/default features, not only imports. A host build with defaults disabled does not establish no_std target compatibility; workspace feature unification can hide an accidental std dependency. See [workspaces](workspaces-and-monorepos.md#feature-unification-and-portability).

## A Fixed-Capacity Protocol State Machine

A stream rarely delivers complete messages in one read. Preserve parse state across chunks, define what happens when capacity is exhausted, and resynchronize before accepting the next message. This core-only LF-delimited decoder rejects an oversized line once, discards its remainder, and resumes after the next delimiter.

```rust
#![no_std]

#[derive(Debug, PartialEq, Eq)]
pub enum Event<'a> {
    Pending,
    Line(&'a [u8]),
    TooLong,
}

pub struct Lines<const N: usize> {
    bytes: [u8; N],
    len: usize,
    discarding: bool,
}

impl<const N: usize> Lines<N> {
    pub const fn new() -> Self {
        Self { bytes: [0; N], len: 0, discarding: false }
    }

    pub fn push(&mut self, byte: u8) -> Event<'_> {
        if self.discarding {
            if byte == b'\n' {
                self.discarding = false;
            }
            return Event::Pending;
        }
        if byte == b'\n' {
            let used = self.len;
            self.len = 0;
            return Event::Line(&self.bytes[..used]);
        }
        if self.len == N {
            self.len = 0;
            self.discarding = true;
            return Event::TooLong;
        }
        self.bytes[self.len] = byte;
        self.len += 1;
        Event::Pending
    }
}
```

The returned line borrows the decoder. Consume it before pushing another byte; the type system prevents mutation while that view remains in use. Empty lines and exactly N-byte lines are valid. A line longer than N cannot be silently split into two valid messages. CRLF normalization, UTF-8 decoding, checksums, and escaping belong to the actual protocol and are deliberately separate from this byte-framing policy.

A UART/DMA adapter can feed bytes into this parser, while a host test or CLI can feed ordinary slices. Parsing needs neither a global buffer nor a board-specific register API. The adapter decides what to do with TooLong: count, report, or reset the connection according to its timing and logging budget.

## Driver, Board, and Application Boundaries

A practical package layout keeps reusable code independent of startup configuration:

```text
protocol/   byte framing and domain state, core-compatible
sensor/     device transactions over an embedded-hal interface
firmware/   target, linker memory layout, clocks, pins, interrupts, executor, panic handler
```

The board layer constructs a peripheral once and transfers it into the driver. This prevents unrelated code from reconfiguring the same peripheral behind the driver's back. Bus sharing is an explicit adapter with a locking/interrupt policy, not a reason to clone a raw peripheral handle.

For an illustrative device whose register 0x00 returns one ID byte, a blocking embedded-hal 1 driver can be complete without depending on a specific MCU:

```rust,deps
// Requires embedded-hal = "1"; usable in a no_std library.
use embedded_hal::i2c::I2c;

#[derive(Debug)]
pub struct InvalidAddress;

pub struct IdDevice<B> {
    bus: B,
    address: u8,
}

impl<B: I2c> IdDevice<B> {
    pub fn new(bus: B, address: u8) -> Result<Self, (InvalidAddress, B)> {
        if address > 0x7f {
            return Err((InvalidAddress, bus));
        }
        Ok(Self { bus, address })
    }

    pub fn read_id(&mut self) -> Result<u8, B::Error> {
        let mut id = [0_u8; 1];
        self.bus.write_read(self.address, &[0x00], &mut id)?;
        Ok(id[0])
    }

    pub fn release(self) -> B { self.bus }
}
```

An invalid address returns the bus with the error, so validation does not discard the caller's peripheral capability. write_read expresses one transaction with the write/read transition inside it; separate write and read calls can insert a stop between them. Real device addressing, registers, and timing still come from the device contract. This method blocks until its bus operation finishes; placing it inside async syntax would not change that. Use the target's async driver interface or a suitable execution context when blocking is unacceptable.

Startup and memory layout belong to the final firmware binary. Initialized globals use RAM plus an initialization image; zero-initialized globals use RAM cleared at startup; task state, interrupt stacks, queues, and any heap all share the remaining RAM budget. A const size bound makes one object's size predictable, not the total firmware footprint. Inspect section sizes and stack use on the selected target.

## Memory and Execution Budgets

Prefer fixed capacity where a maximum is credible, with an explicit full policy: reject, drop, overwrite, or defer according to the protocol. Eligible heapless collections can express capacity in types; arrays and caller-owned slices may already suffice. Large fixed arrays still consume memory wherever their owner lives.

Budget stacks, static task state, queues, buffers, and interrupt nesting together. Async tasks may retain large values across awaits; avoiding a heap does not make that memory free. Dynamic allocation can be appropriate when bounded latency and failure handling meet the target's requirements; see [allocation](memory-and-allocation.md).

| Work shape | Starting execution model | Change when |
|---|---|---|
| Small predictable polling sequence | Main loop/state machine | Waiting or response requirements demand asynchronous events |
| Short hardware event handling | Interrupt records state/enqueues bounded work | Heavy computation should run outside the handler |
| Multiple waiting peripherals/timers | Embassy where the target integration supports it | A simple loop is clearer or an existing RTOS owns scheduling |
| Hard deadlines | Analyze worst-case execution and blocking | Average throughput alone cannot establish a deadline guarantee |

Embassy tasks can be statically allocated without alloc; this does not promise hard real-time behavior for arbitrary task bodies. Long non-yielding work, priorities, interrupts, and driver behavior still matter.

## Interrupts, Atomics, and Shared State

One CPU core does not imply absence of concurrency: interrupts can preempt ordinary code. An interrupt spinning on a lock held by the interrupted code can deadlock. Keep critical sections short and use the target/HAL's documented synchronization contracts.

Interrupt masking on one core does not stop another core or DMA. Check `target_has_atomic`, operation width, and required ordering; do not assume desktop atomics or Arc are available. A manually declared Sync wrapper around RefCell/Cell is not a soundness proof.

Volatile accesses address specific MMIO/compiler-observation requirements, not mutual exclusion, atomicity, or general memory synchronization. Use the platform's required barriers and cache operations when interacting with devices.

### Coalesced Events Between an Interrupt and a Task

For targets with 32-bit atomics, an event bitset can communicate that work is pending without a blocking lock:

```rust
#[cfg(target_has_atomic = "32")]
pub mod events {
    use core::sync::atomic::{AtomicU32, Ordering};

    pub struct Pending(AtomicU32);

    impl Pending {
        pub const fn new() -> Self { Self(AtomicU32::new(0)) }
        pub fn notify(&self, mask: u32) {
            self.0.fetch_or(mask, Ordering::Relaxed);
        }
        pub fn take(&self) -> u32 {
            self.0.swap(0, Ordering::Relaxed)
        }
    }
}
```

The interrupt sets a bit; ordinary code atomically takes the pending set and performs the work outside the handler. Repeated notifications of one bit coalesce. This is suitable for “check this device” but not “process every sample exactly once.” A bounded queue or counter is needed when multiplicity or payload matters, along with an overflow policy.

Relaxed is sufficient here because the atomic value is the entire communicated state. It does not publish a separate mutable payload. A queue's synchronization must protect the queue storage, and hardware state may require separate barriers/cache operations. On targets without the needed atomics, use the HAL's critical-section mechanism; a busy-spin lock in an interrupt can deadlock against interrupted code on the same core.

An idle loop also needs a race-free sleep/wakeup protocol. Checking the bitset and then blindly sleeping can miss a notification between those operations. Use the runtime/HAL's event wait mechanism; the bitset alone is not a sleep primitive.

## DMA, Failure, and Hardware Validation

Keep DMA buffers alive and at a suitable address until transfer completion or confirmed stop; cancellation of a Rust future alone may not stop hardware. Respect alignment, accessible memory regions, cache coherence, and exclusive/shared access rules. Obtain details from the chosen device/HAL, not a generic Rust assumption.

Define panic behavior at the application boundary: halt, reset, or a documented recovery strategy. Return expected capacity/protocol errors normally. Keep error reporting and logging within the same allocation, timing, and interrupt constraints. Watchdog policy should account for expected long operations and failed progress.

Host checks exercise portable logic; cross-compilation checks target availability; measurements on hardware establish timing, stack use, peripheral/DMA behavior, and power effects. State which level was performed. SIMD/FPU/DSP capabilities differ among MCUs; see [SIMD](simd.md).

### DMA Ownership Through Completion and Cancellation

Treat a transfer as a state change in ownership, not just starting a register:

| State | Who may access the buffer? | Transition condition |
|---|---|---|
| CPU-owned | Ordinary Rust code according to its borrows | Prepare contents and hand ownership to the transfer |
| Device-owned | Only accesses allowed by the DMA/HAL contract | Device completion or a confirmed stop |
| Returning to CPU | Driver completes required barriers and cache maintenance | Hardware can no longer access the range |
| CPU-owned again | Rust receives the buffer back | Parsing or reuse may resume |

The HAL's transfer value should own the channel and buffer capability while hardware is active. Completion returns them. A cancellation request is not yet completion: abort acknowledgement, outstanding bus operations, and cache coherence can delay safe reuse.

A borrowed stack buffer guarded only by Drop is dangerous for an asynchronous DMA abstraction: safe code can forget a guard. Designs based on owned/static buffers can make forgetting a transfer leak resources while the storage remains alive, rather than allowing hardware to access a dead stack frame. Other sound designs need an equally strong lifetime argument. Pinning alone does not keep storage alive or stop DMA.

Use the concrete HAL's transfer/cancel/finish operations to implement these transitions. Alignment, accessible RAM banks, cache-line sharing, and peripheral direction are device-specific. The generic ownership model tells you what those operations must establish; it cannot supply their register sequence.

### Async Memory and Deadlines

An async task retains variables needed after an await in its future state. A large receive buffer retained across a wait remains allocated even while the task is idle. With a statically allocated executor such as Embassy, that cost can be in static task storage rather than a heap. Multiply it by the number of task instances, not just by the size of one function's visible locals.

Cooperative tasks yield only at operations that actually suspend. A long parse or a loop of immediately ready awaits can delay other work. Move a bounded amount of work per activation, keep interrupt handlers short, and choose priorities from response requirements. A high-priority task can still wait on a resource held by lower-priority code; blocking time and interrupt interference belong in deadline analysis.

A host run can establish parser behavior; target compilation can establish API/feature availability; only the device and its configuration can establish interrupt latency, DMA coherence, stack margins, and power behavior. Keep those conclusions distinct when applying the examples.
