# Unsafe and FFI

## Contents

- [What unsafe Unlocks](#what-unsafe-unlocks)
- [Undefined Behavior](#undefined-behavior)
- [Not Undefined Behavior](#not-undefined-behavior)
- [unsafe fn, unsafe Blocks, and SAFETY Comments](#unsafe-fn-unsafe-blocks-and-safety-comments)
- [Safe Abstractions Over unsafe](#safe-abstractions-over-unsafe)
- [Uninitialized Memory](#uninitialized-memory)
- [Raw Pointers, Alignment, and Provenance](#raw-pointers-alignment-and-provenance)
- [Reinterpreting Bytes Without transmute](#reinterpreting-bytes-without-transmute)
- [Replacing static mut](#replacing-static-mut)
- [FFI: Declaring and Calling C](#ffi-declaring-and-calling-c)
- [FFI: Callbacks and Panics](#ffi-callbacks-and-panics)
- [FFI: Types and Ownership Across the Boundary](#ffi-types-and-ownership-across-the-boundary)
- [Own a Foreign Allocation with a Rust Handle](#own-a-foreign-allocation-with-a-rust-handle)
- [Sharing Raw Pointers Across Threads](#sharing-raw-pointers-across-threads)
- [PhantomData](#phantomdata)
- [Verification with Miri and Lints](#verification-with-miri-and-lints)
- [Common Mistakes](#common-mistakes)
- [Availability by Version](#availability-by-version)
- [Practical Boundaries](#practical-boundaries)

Edition-2024 examples require Rust 1.85 or later, subject to any newer API version stated beside an example. That edition requires `unsafe extern` blocks and unsafe attributes such as `#[unsafe(no_mangle)]`. Omitting explicit `unsafe {}` around unsafe operations in an unsafe function triggers the default-warning `unsafe_op_in_unsafe_fn` lint; a deny setting makes it an error. Explicit blocks separate the caller's safety contract from the implementation's unsafe operations. Lock and atomic semantics are in [concurrency](concurrency.md); migration details are in [Rust 1.85 and edition 2024](../versions/1.85.md).

## What unsafe Unlocks

Unsafe operations include the following; each has additional validity requirements that the caller or implementation must uphold:

1. Dereference raw pointers.
2. Call `unsafe` functions, including C functions, compiler intrinsics, and the raw allocator.
3. Implement `unsafe` traits (`Send`, `Sync`, `GlobalAlloc`, and others).
4. Access or modify mutable statics.
5. Access fields of unions.

Everything else, including integer overflow, leaks, and deadlocks, is safe Rust. The keyword marks where the compiler stops checking and the author takes over; the author's job is to keep the program free of the behaviors listed next.

## Undefined Behavior

Executing undefined behavior invalidates Rust's guarantees for that execution. Important cases include:

- Data races.
- Reading or writing through a dangling or misaligned pointer, or projecting a field or index out of bounds.
- Breaking the aliasing rules: memory reachable through a live `&T` must not be mutated (except inside `UnsafeCell`); memory reachable through a live `&mut T` must not be read or written through any other pointer. `Box<T>` counts like `&mut T`.
- Mutating immutable bytes: constants, promoted values, bytes behind a shared reference, the contents of an immutable `static`.
- Invoking undefined behavior through intrinsics; running code compiled for a target feature the CPU lacks.
- Calling a function through the wrong ABI, or unwinding through a frame that does not permit it (a panic escaping `extern "C"`).
- Producing an invalid value: a `bool` other than 0 or 1, an `enum` with an invalid discriminant, a null `fn` pointer, a `char` outside the valid ranges, any value of type `!`, an integer, float, or pointer read from uninitialized memory, a `str` that is not UTF-8, a dangling or misaligned reference or `Box`, a wide pointer with invalid metadata, a `NonNull` that is null. "Producing" includes assigning, reading from a place, passing, and returning.
- Incorrect inline assembly.
- Violating runtime assumptions such as unwinding or `longjmp` over Rust frames without running destructors.

Memorize the invalid-value rule: `MaybeUninit<T>` exists because a `let x: u32;` that is read before assignment is already undefined behavior, not "garbage data".

## Not Undefined Behavior

Deadlocks, resource leaks, and exiting without destructors are not undefined behavior. Ordinary integer overflow is also not UB: checks can panic, and unchecked ordinary arithmetic wraps. Incorrect Eq/Hash/Ord implementations are logic errors that safe abstractions must handle without memory unsafety. Unsafe code cannot assume these conditions never occur; in particular, a guard cannot rely on Drop running because safe code can forget it.

## unsafe fn, unsafe Blocks, and SAFETY Comments

An `unsafe fn` declares obligations the caller must meet; an `unsafe {}` block claims the obligations of everything inside it are met. Since edition 2024 the body of an `unsafe fn` is not implicitly an unsafe block (`unsafe_op_in_unsafe_fn` warns), so each operation gets its own block and its own justification.

```rust
/// Returns the element at `index` without a bounds check.
///
/// # Safety
///
/// `index` must be less than `slice.len()`.
pub unsafe fn element_unchecked(slice: &[u32], index: usize) -> u32 {
    debug_assert!(index < slice.len(), "element_unchecked: index out of range");
    // SAFETY: the caller guarantees `index < slice.len()`, which is exactly the precondition
    // of `get_unchecked`.
    unsafe { *slice.get_unchecked(index) }
}

pub fn third_or_zero(slice: &[u32]) -> u32 {
    if slice.len() > 2 {
        // SAFETY: the length check on the previous line establishes `2 < slice.len()`.
        unsafe { element_unchecked(slice, 2) }
    } else {
        0
    }
}
```

Conventions:

- A `// SAFETY:` comment directly above every `unsafe` block names the invariant and where it is established. Clippy `undocumented_unsafe_blocks` (restriction) enforces the comment; `multiple_unsafe_ops_per_block` (restriction) keeps one operation per block so each comment covers one claim.
- Every `pub unsafe fn` documents its preconditions under `# Safety` (Clippy `missing_safety_doc`, style, warns otherwise).
- A `debug_assert!` of the precondition inside the `unsafe fn` catches misuse in tests at no release cost.
- A function is `unsafe` only when the caller can cause undefined behavior by misusing it. A function that is merely dangerous (deletes files) is safe.
- A safe function must be sound for every possible argument, including ones the author considers absurd: `pub fn read(ptr: *const u8) -> u8 { unsafe { *ptr } }` is unsound (Clippy `not_unsafe_ptr_arg_deref`, correctness, deny).

## Safe Abstractions Over unsafe

Keep invariant-bearing fields private and place unsafe operations inside a module whose safe API preserves those invariants. This makes the safety argument local: callers can use the API without recreating the raw-pointer proof. Public safe operations must still remain sound under every interaction their types permit.

```rust
use std::mem::MaybeUninit;

/// A fixed-capacity vector stored inline. Invariant: `items[..len]` are initialized.
pub struct FixedVec<T, const N: usize> {
    items: [MaybeUninit<T>; N],
    len: usize,
}

impl<T, const N: usize> FixedVec<T, N> {
    pub const fn new() -> Self {
        Self { items: [const { MaybeUninit::uninit() }; N], len: 0 }
    }

    pub fn push(&mut self, value: T) -> Result<(), T> {
        if self.len == N {
            return Err(value);
        }
        self.items[self.len].write(value); // safe: writing never reads the old bytes
        self.len += 1;
        Ok(())
    }

    pub fn pop(&mut self) -> Option<T> {
        if self.len == 0 {
            return None;
        }
        self.len -= 1;
        // SAFETY: index `len` was initialized by `push` and is now outside the initialized
        // prefix, so this reads the value exactly once and nothing else will drop it.
        Some(unsafe { self.items[self.len].assume_init_read() })
    }

    pub fn as_slice(&self) -> &[T] {
        // SAFETY: `items[..len]` are initialized (the struct invariant) and `MaybeUninit<T>`
        // has the same layout as `T`, so the cast pointer addresses `len` valid `T`s.
        unsafe { std::slice::from_raw_parts(self.items.as_ptr().cast::<T>(), self.len) }
    }

    pub fn len(&self) -> usize {
        self.len
    }

    pub fn is_empty(&self) -> bool {
        self.len == 0
    }
}

impl<T, const N: usize> Drop for FixedVec<T, N> {
    fn drop(&mut self) {
        for item in &mut self.items[..self.len] {
            // SAFETY: every element of the initialized prefix is dropped exactly once here.
            unsafe { item.assume_init_drop() };
        }
    }
}

impl<T, const N: usize> Default for FixedVec<T, N> {
    fn default() -> Self {
        Self::new()
    }
}
```

The invariant is stated once on the struct, every `unsafe` block refers to it, and no public method can break it. Since 1.93, `<[MaybeUninit<T>]>::assume_init_ref` and `assume_init_drop` express the slice operations directly. A String similarly keeps its UTF-8 invariant behind operations that preserve it, rather than letting callers mutate arbitrary bytes through a safe API.

## Uninitialized Memory

Never create an integer, reference, or `bool` from uninitialized bytes, even to overwrite it. Safe tools cover most needs:

| Need | Safe tool |
|---|---|
| Zero-filled buffer | `vec![0u8; n]`, `[0u8; N]`, `Box::new_zeroed` (1.92) for zeroed allocation; it still returns MaybeUninit storage whose conversion to T needs valid zero bits |
| Buffer filled by a reader | `Vec::with_capacity(n)` plus `Read::read_to_end`, or `resize(n, 0)` then `read_exact` |
| Array built element by element | `std::array::from_fn(|i| ...)` |
| Partially initialized storage | `MaybeUninit<T>` with `write`, then `assume_init*` under a documented invariant, as in `FixedVec` above |
| Spare capacity of a `Vec` | `spare_capacity_mut()` returns `&mut [MaybeUninit<T>]`; `set_len` afterwards is `unsafe` and requires every element written |

`mem::zeroed::<T>()` is valid only when all-zero bytes represent a valid T. Zero is valid for integers, floats, bool (false), char (NUL), and nullable representations such as Option<Box<T>>. It is invalid for references and NonNull, and can be invalid for an enum with no zero discriminant. Check the actual type and representation rather than assuming every struct or enum permits zero initialization. `mem::uninitialized` is deprecated and unsound for almost every type.

## Raw Pointers, Alignment, and Provenance

Creating a reference to misaligned or uninitialized memory is undefined behavior even if the reference is never used; raw pointers have no such requirement until dereferenced. `&raw const place` and `&raw mut place` (1.82) create raw pointers without going through a reference, which is what packed structs and uninitialized fields need.

```rust
#[repr(C, packed)]
struct Header {
    magic: u8,
    length: u32, // misaligned: offset 1
}

fn header_length(header: &Header) -> u32 {
    let field = &raw const header.length; // a reference `&header.length` is a compile error
    // SAFETY: `field` points into the live `Header` behind `header`; `read_unaligned` tolerates the
    // 1-byte alignment of a packed field.
    unsafe { field.read_unaligned() }
}

fn tag_pointer(ptr: *const u8, tag: usize) -> *const u8 {
    // Strict provenance (1.84): keep the allocation the pointer belongs to, change only address bits.
    ptr.map_addr(|addr| addr | (tag & 0b11))
}

fn untag_pointer(ptr: *const u8) -> *const u8 {
    ptr.map_addr(|addr| addr & !0b11)
}
```

Rules:

- Pointer arithmetic (`add`, `offset`, `sub`) must stay within one allocation, including one-past-the-end; `wrapping_add` allows arbitrary arithmetic but the result is only dereferenceable if it lands back in bounds.
- Do not cast pointers to integers and back to smuggle them; use `addr()`, `with_addr`, `map_addr`, and `expose_provenance`/`with_exposed_provenance` (1.84) so the compiler keeps provenance. The rustc lint `integer_to_ptr_transmutes` (1.91) flags the transmute form, and `dangling_pointers_from_locals` (1.91) flags returning a pointer to a local.
- `ptr.cast::<U>()` changes the pointee type without an `as` chain; alignment of `U` must hold before dereferencing (Clippy `cast_ptr_alignment`, pedantic).
- Debug builds insert null checks on reads, writes, and reborrows through raw pointers since 1.86; a panic there is the debug build catching undefined behavior early, not a false alarm.
- `dangerous_implicit_autorefs` (deny since 1.89) flags `(*ptr).field.len()`-style implicit references through a raw pointer; write the reborrow explicitly and justify it.

## Reinterpreting Bytes Without transmute

`mem::transmute` between references is almost always wrong: `&[u8]` to `&[u32]` produces a slice with the wrong length (the length counts elements, not bytes) and possibly misaligned data. Decode explicitly, or use `align_to` when zero-copy is required.

```rust
fn decode_u32_le(bytes: &[u8]) -> Vec<u32> {
    bytes
        .chunks_exact(4)
        .map(|chunk| u32::from_le_bytes([chunk[0], chunk[1], chunk[2], chunk[3]]))
        .collect()
}

fn as_u32_slice(bytes: &[u8]) -> Option<&[u32]> {
    // SAFETY: `align_to` yields a middle slice that is correctly aligned for u32, and every bit
    // pattern is a valid u32, so viewing those bytes as u32 values is sound.
    let (prefix, middle, suffix) = unsafe { bytes.align_to::<u32>() };
    (prefix.is_empty() && suffix.is_empty()).then_some(middle)
}

fn f32_bits(value: f32) -> u32 {
    value.to_bits() // instead of transmute::<f32, u32>
}
```

For transmute, the types must have the same size; the result must be a valid value (transmuting `3u8` to `bool` is undefined behavior); `&T` to `&mut T` is "always Undefined Behavior"; a transmuted reference without an explicit lifetime gets an unbounded one; compound types need identical layout, which the default `repr(Rust)` does not guarantee even between two identical-looking structs. The `bytemuck` and `zerocopy` crates provide checked casts for plain-old-data types and are the ecosystem answer to most byte-reinterpretation needs. Clippy `missing_transmute_annotations` (suspicious) asks for explicit type arguments so inference cannot pick a surprising type.

## Replacing static mut

Edition 2024 denies references to `static mut` (`static_mut_refs`), because two references to the same mutable static alias by construction. Replace it with a synchronized type; a raw pointer through `&raw` is the last resort.

```rust
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::{Mutex, OnceLock, PoisonError};

// Before: `static mut COUNTER: usize = 0;` plus `unsafe { COUNTER += 1 }` everywhere.
static COUNTER: AtomicUsize = AtomicUsize::new(0);
static LOG: Mutex<Vec<String>> = Mutex::new(Vec::new());
static HOSTNAME: OnceLock<String> = OnceLock::new();

fn record(entry: &str) {
    COUNTER.fetch_add(1, Ordering::Relaxed);
    LOG.lock().unwrap_or_else(PoisonError::into_inner).push(entry.to_owned());
}

fn hostname() -> &'static str {
    HOSTNAME.get_or_init(|| std::env::var("HOSTNAME").unwrap_or_else(|_| "localhost".to_owned()))
}
```

For embedded targets, use a synchronization abstraction justified for the actual interrupt/core/DMA model. One core can still be preempted by interrupts; wrapping Cell/RefCell in an unsafe Sync implementation does not establish safety. Follow the target/HAL critical-section contract in [embedded guidance](embedded-and-no-std.md#interrupts-atomics-and-shared-state).

## FFI: Declaring and Calling C

Foreign functions are declared in an `unsafe extern` block (mandatory in edition 2024, available since 1.82). The declaration is a promise about the C signature that the compiler cannot verify; every mistake there is undefined behavior at the call.

```rust
use std::ffi::{c_char, c_int, CStr, CString};

#[repr(C)]
pub struct Point {
    pub x: f64,
    pub y: f64,
}

unsafe extern "C" {
    // Signatures must match the C header exactly.
    fn strlen(s: *const c_char) -> usize;
    // The absolute value must be representable as c_int.
    fn abs(value: c_int) -> c_int;
}

fn c_length(text: &str) -> Result<usize, std::ffi::NulError> {
    let owned = CString::new(text)?; // interior NUL bytes are rejected here
    // SAFETY: `owned` is a valid NUL-terminated string that lives until after the call returns.
    Ok(unsafe { strlen(owned.as_ptr()) })
}

/// # Safety
/// A non-null pointer must identify a live, readable NUL-terminated string that
/// remains unmodified for this call. The terminator must be within its allocation and the total range must fit in isize::MAX bytes.
unsafe fn string_from_c(ptr: *const c_char) -> Option<String> {
    if ptr.is_null() {
        return None;
    }
    // SAFETY: the caller guarantees `ptr` points to a NUL-terminated string that stays valid and
    // unmodified for the duration of this call.
    let text = unsafe { CStr::from_ptr(ptr) };
    Some(text.to_string_lossy().into_owned())
}

fn magnitude(value: c_int) -> Option<c_int> {
    if value == c_int::MIN { return None; }
    // SAFETY: excluding MIN makes the mathematical absolute value representable.
    Some(unsafe { abs(value) })
}
```

- Use `core::ffi`/`std::ffi` integer aliases (`c_int`, `c_long`, `c_char`, `c_void`) so widths follow the platform; `i128`/`u128` are C-compatible with `__int128` since 1.89.
- `#[repr(C)]` on every struct that crosses the boundary; the default representation may reorder fields.
- C strings: `CString` to hand text to C, `CStr` to read it; `c"literal"` (1.77) for compile-time C string constants. A `String` is not NUL-terminated and a `&str` may contain interior NULs.
- `Option<extern "C" fn(...)>` and `Option<&T>` are guaranteed to have the same layout as a nullable pointer, so they model nullable function pointers and pointers without extra flags.
- Since 1.87, most `std::arch` intrinsics without pointer arguments are safe when the target feature is enabled; keep `unsafe` only where the compiler still requires it (`unused_unsafe` warns otherwise).
- Link attributes: `#[link(name = "foo")]` on the block; `#[unsafe(no_mangle)]`, `#[unsafe(export_name)]`, `#[unsafe(link_section)]` on exported items (edition 2024 requires the `unsafe(...)` wrapper).

## FFI: Callbacks and Panics

A Rust panic escaping an `extern "C"` boundary aborts rather than unwinding into C. Where recovery is valid, catch an unwinding panic inside the callback and translate it to the foreign error protocol. catch_unwind cannot recover from panic=abort or undefined behavior. Use `extern "C-unwind"` only when the complete foreign-call path supports the intended unwinding behavior.

```rust
use std::ffi::c_void;
use std::panic::{catch_unwind, AssertUnwindSafe};

type ValueCallback = unsafe extern "C" fn(user_data: *mut c_void, value: i32) -> i32;

struct Accumulator {
    total: i64,
}

/// # Safety
/// user_data must point to a live, initialized, aligned Accumulator, with exclusive
/// access for this call. No concurrent or reentrant callback may access that value.
unsafe extern "C" fn on_value(user_data: *mut c_void, value: i32) -> i32 {
    // SAFETY: the callback's caller establishes the lifetime and exclusive-access contract.
    let accumulator = unsafe { &mut *user_data.cast::<Accumulator>() };
    match catch_unwind(AssertUnwindSafe(|| {
        accumulator.total += i64::from(value);
    })) {
        Ok(()) => 0,
        Err(payload) => {
            // Dropping an arbitrary panic payload could itself panic.
            std::mem::forget(payload);
            -1
        }
    }
}

fn callback_parts(accumulator: &mut Accumulator) -> (ValueCallback, *mut c_void) {
    (on_value, std::ptr::from_mut(accumulator).cast::<c_void>())
}
```

callback_parts only constructs the raw arguments; it does not register anything or extend the accumulator's lifetime. Invoke the returned callback only under its unsafe contract. A foreign API retaining these arguments needs an owning registration wrapper, as described under [foreign ownership](#own-a-foreign-allocation-with-a-rust-handle).

- Establish that callbacks have stopped before releasing their state. Drop can request unregistration, but the foreign API must establish completion; safe code can also forget a registration handle.
- Exclusive access includes same-thread reentrancy, not only parallel threads. Synchronization can protect shared state, but calling back while holding the same non-reentrant mutex can deadlock.
- AssertUnwindSafe asserts that the captured state remains usable after an unwind; it does not roll back a partial update. This example has one integer assignment, and deliberately leaks a caught payload to avoid a second panic while reporting the failure. Panic hooks still run before a panic is caught.

## FFI: Types and Ownership Across the Boundary

| Rust side | C side | Rule |
|---|---|---|
| `#[repr(C)] struct` | `struct` | Same field order and types; padding follows C |
| `#[repr(u8)] enum` with all values known | `enum`/`uint8_t` | Only when C can never pass an out-of-range value; otherwise accept the integer and convert with `TryFrom`, because an invalid discriminant is undefined behavior |
| `Box<T>` via `Box::into_raw` | opaque pointer | Freed only by Rust through `Box::from_raw` with the same `T`; never `free()`d by C |
| Memory from `malloc` | pointer | Freed only by C (`free`); Rust never `Box::from_raw`s it |
| `&[u8]` | `const uint8_t*` + length | Pass pointer and length separately; slices have no C layout |
| `*const T` | `const T*` | Null is representable; check before dereferencing |
| `bool` | `bool`/`_Bool` | Same layout; a C `int` used as boolean must be converted |
| `usize` | `size_t` | Same width on all supported targets |

Ownership crosses the boundary explicitly: a `Box::into_raw` handed to C is leaked until C returns it to a Rust function that calls `Box::from_raw`. Two allocators must never free each other's memory. Since 1.91 C-variadic functions can be declared (not defined) for `sysv64`, `win64`, `efiapi`, and `aapcs`.

## Own a Foreign Allocation with a Rust Handle

A safe wrapper needs an ownership protocol as well as a pointer validity check. This hosted example uses C malloc/free, initializes the bytes before creating Rust slices, and frees through the allocator that created the allocation. It requires those C functions to be linked by the target environment.

```rust
use std::{ffi::c_void, num::NonZeroUsize, ptr::NonNull};

unsafe extern "C" {
    fn malloc(size: usize) -> *mut c_void;
    fn free(pointer: *mut c_void);
}

#[derive(Debug, PartialEq, Eq)]
pub enum AllocationError { TooLarge, Failed }

pub struct ForeignBuffer {
    pointer: NonNull<u8>,
    len: usize,
}

impl ForeignBuffer {
    pub fn zeroed(len: NonZeroUsize) -> Result<Self, AllocationError> {
        let len = len.get();
        if len > isize::MAX as usize { return Err(AllocationError::TooLarge); }
        // SAFETY: malloc accepts this size; its null result is handled below.
        let raw = unsafe { malloc(len) }.cast::<u8>();
        let pointer = NonNull::new(raw).ok_or(AllocationError::Failed)?;
        // SAFETY: malloc returned unique storage for at least len bytes, aligned for u8.
        unsafe { pointer.as_ptr().write_bytes(0, len) };
        Ok(Self { pointer, len })
    }

    pub fn as_slice(&self) -> &[u8] {
        // SAFETY: the initialized allocation remains owned by self for this borrow.
        unsafe { std::slice::from_raw_parts(self.pointer.as_ptr(), self.len) }
    }

    pub fn as_mut_slice(&mut self) -> &mut [u8] {
        // SAFETY: exclusive access to self gives exclusive access to its owned bytes.
        unsafe { std::slice::from_raw_parts_mut(self.pointer.as_ptr(), self.len) }
    }

    pub fn into_raw(self) -> (*mut u8, usize) {
        let result = (self.pointer.as_ptr(), self.len);
        std::mem::forget(self); // transfer cleanup responsibility to the recipient
        result
    }
}

impl Drop for ForeignBuffer {
    fn drop(&mut self) {
        // SAFETY: this is the original live malloc pointer, uniquely owned by self.
        unsafe { free(self.pointer.as_ptr().cast::<c_void>()) };
    }
}
```

Safe callers can borrow the bytes or transfer ownership out, but cannot construct a second owner from a pointer. After into_raw, the recipient must eventually use the matching C free; Rust must not recreate a Box from that allocation. Forgetting the wrapper leaks storage rather than enabling a double free. No manual Send/Sync implementation is provided: a foreign resource's transfer and shared-access contract must be established separately.

A foreign API retaining pointers needs a longer-lived owner. For callbacks, a registration handle must keep the state at a stable address, prevent forbidden concurrent access, and unregister before releasing it. If unregistration can fail or callbacks remain in flight, Drop alone is not a sufficient “everything stopped” claim. Completion must establish that C can no longer call the pointer; leaking state can be safer than freeing it while callbacks remain possible.

This is different from a call that borrows bytes only until it returns. Match the wrapper's lifetime to the actual foreign contract instead of making every pointer static or assuming a function-name convention implies ownership.

## Sharing Raw Pointers Across Threads

Raw pointers are neither `Send` nor `Sync`, so a struct holding one is not either. Implementing the traits by hand is a promise about the foreign object's thread-safety contract.

```rust
use std::ffi::c_void;
use std::ptr::NonNull;

/// Handle to a C object that the library documents as movable between threads but usable from only
/// one thread at a time.
pub struct Handle {
    raw: NonNull<c_void>,
}

// SAFETY: the library allows moving the object between threads, and exclusive use is enforced by
// Rust ownership (`&mut self` for every operation). `Sync` is deliberately not implemented, because
// concurrent shared access is not permitted by the library.
unsafe impl Send for Handle {}

impl Handle {
    pub fn with_raw<R>(&mut self, f: impl FnOnce(*mut c_void) -> R) -> R {
        f(self.raw.as_ptr())
    }
}
```

Send permits transferring ownership between threads, including destruction on the receiving thread. Sync permits sharing references between threads. Rc is neither Send nor Sync; Cell<T> and RefCell<T> are not Sync but can be Send when T is Send. A foreign handle also needs the foreign API's transfer, shared-access, and thread-affinity guarantees. A Mutex serializes access but cannot make a thread-affine handle transferable.

## PhantomData

`PhantomData<T>` tells the compiler about ownership, variance, and auto traits for data a raw pointer points at. Common marker forms have the following effects:

| Marker | Variance in `T` | `Send`/`Sync` | Drop check |
|---|---|---|---|
| `PhantomData<T>` | covariant | inherited from `T` | "owns `T`": `T` must outlive the container |
| `PhantomData<&'a T>` | covariant | `Send + Sync` when `T: Sync` | borrowed |
| `PhantomData<&'a mut T>` | invariant | inherited | borrowed |
| `PhantomData<*const T>` | covariant | `!Send + !Sync` | not owned |
| `PhantomData<*mut T>` | invariant | `!Send + !Sync` | not owned |
| `PhantomData<fn(T)>` | contravariant | `Send + Sync` | not owned |
| `PhantomData<fn() -> T>` | covariant | `Send + Sync` | not owned |
| `PhantomData<fn(T) -> T>` | invariant | `Send + Sync` | not owned |

A container that owns `T` through a raw pointer (`struct MyVec<T> { ptr: NonNull<T>, .. }`) adds `PhantomData<T>` so dropping it is understood to drop `T`s; a borrowed view adds `PhantomData<&'a T>` so the borrow checker ties it to the source's lifetime.

## Verification with Miri and Lints

- `rustup +nightly component add miri` then `cargo +nightly miri test` interprets the tests and reports out-of-bounds access, use-after-free, uninitialized reads, alignment violations, aliasing-model violations (Stacked or Tree Borrows), data races, and leaks. It cannot run FFI or most platform APIs, is slow, and does not prove the absence of undefined behavior; it is still the single most effective check for `unsafe` code.
- Run the debug build: since 1.86 it panics on null-pointer reads, writes, and reborrows, and overflow checks catch arithmetic mistakes in index computations.
- Clippy correctness lints (deny by default) for this area: `not_unsafe_ptr_arg_deref`, `uninit_vec`, `mem_replace_with_uninit`, `unsound_collection_transmute`, `zst_offset`, `size_of_in_element_count`, `transmuting_null`, `wrong_transmute`, `cast_slice_different_sizes`. Opt-in hygiene: `undocumented_unsafe_blocks`, `multiple_unsafe_ops_per_block`, `mem_forget`, `as_conversions` (restriction), `cast_ptr_alignment`, `ptr_as_ptr`, `borrow_as_ptr` (pedantic).
- Sanitizers (`-Z sanitizer=address`, `thread`) on nightly complement Miri for code that calls into C.
- A `// SAFETY:` explanation connects the operation to its invariants and the relevant validity requirements. Complex contracts can require more than one sentence; documentation and execution tools establish different kinds of evidence.

## Common Mistakes

- Treating `unsafe` as "trust me" instead of "here is the proof": blocks without a `// SAFETY:` comment, or comments that restate the code.
- A safe `pub fn` that dereferences a raw-pointer argument.
- `mem::zeroed()` or `MaybeUninit::uninit().assume_init()` for types with invalid bit patterns.
- `transmute` between slices or between `repr(Rust)` structs; `&T` to `&mut T`.
- A Rust `enum` in an FFI signature where C may pass unknown values.
- `Box::from_raw` on memory C allocated, or `free()` on memory Rust allocated.
- Letting a panic escape a callback.
- `unsafe impl Send`/`Sync` written to silence the compiler rather than from the library's documented threading contract.
- Holding `&mut` to data also reachable through a raw pointer that C still uses (aliasing violation).
- Skipping Miri because "it does not support FFI"; run it on the pure-Rust parts.

## Availability by Version

| Version | Change |
|---|---|
| 1.77 | C string literals `c"..."` |
| 1.81 | Panics abort at `extern "C"` boundaries; `core::hint::assert_unchecked` |
| 1.82 | `&raw const`/`&raw mut`; `unsafe extern` blocks with `safe` items; `#[unsafe(no_mangle)]` and friends; `Box::new_uninit` |
| 1.84 | Strict provenance APIs (`addr`, `with_addr`, `map_addr`, `expose_provenance`, `with_exposed_provenance`, `without_provenance`) |
| 1.85 | Edition 2024: `unsafe extern` and `unsafe(...)` attributes mandatory; `unsafe_op_in_unsafe_fn` warns; `static_mut_refs` denies |
| 1.86 | Debug-build null-pointer checks; safe `#[target_feature]` functions |
| 1.87 | Most `std::arch` intrinsics safe to call with the feature enabled |
| 1.88 | `#[unsafe(naked)]` functions with `naked_asm!` |
| 1.89 | `dangerous_implicit_autorefs` deny; `i128`/`u128` FFI-safe |
| 1.91 | `dangling_pointers_from_locals`, `integer_to_ptr_transmutes` lints; C-variadic declarations |
| 1.92 | `Box::new_zeroed`, `Rc::new_zeroed`, `Arc::new_zeroed` |
| 1.93 | `<[MaybeUninit<T>]>::assume_init_ref`, `assume_init_mut`, `assume_init_drop`, `write_copy_of_slice`; `Vec::into_raw_parts` |
| 1.98 | Moving a `ManuallyDrop<Box<T>>` after dropping its contents is documented as sound |

Per-release details live in [the versions index](../versions/index.md).

## Practical Boundaries

A safe abstraction must preserve its invariants for every input and interaction available to safe callers. An unsafe API instead documents the additional obligations callers must uphold. SAFETY comments explain how those obligations justify particular operations; their adequacy depends on the argument, not a one-sentence limit.

Initialization requires a valid value of the actual type. Raw-pointer construction does not establish alignment, readable extent, aliasing, or ownership; creating a reference imposes stronger validity requirements. Foreign interfaces add ABI, allocation/deallocation, callback lifetime, and thread-affinity contracts.

A panic strategy must match the ABI and build configuration. catch_unwind handles unwinding Rust panics, not arbitrary foreign failures or aborting panics. Miri, sanitizers, and target execution expose different classes of mistakes and leave different gaps; a successful run is not a general proof of soundness.
