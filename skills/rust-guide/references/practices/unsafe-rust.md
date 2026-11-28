# Unsafe Rust

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
- [PhantomData](#phantomdata)
- [Verification with Miri and Lints](#verification-with-miri-and-lints)
- [Common Mistakes](#common-mistakes)
- [Availability by Version](#availability-by-version)
- [Practical Boundaries](#practical-boundaries)

Edition-2024 examples require Rust 1.85 or later, subject to any newer API version stated beside an example. That edition requires `unsafe extern` blocks and unsafe attributes such as `#[unsafe(no_mangle)]`. Omitting explicit `unsafe {}` around unsafe operations in an unsafe function triggers the default-warning `unsafe_op_in_unsafe_fn` lint; a deny setting makes it an error. Explicit blocks separate the caller's safety contract from the implementation's unsafe operations. Foreign-function boundaries continue in [FFI](ffi.md); lock and atomic semantics are in [synchronization](synchronization.md); migration details are in [Rust 1.85 and edition 2024](../versions/1.85.md).

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
- Skipping Miri because "it does not support FFI"; run it on the pure-Rust parts.

## Availability by Version

| Version | Change |
|---|---|
| 1.81 | `core::hint::assert_unchecked` |
| 1.82 | `&raw const`/`&raw mut`; `Box::new_uninit` |
| 1.84 | Strict provenance APIs (`addr`, `with_addr`, `map_addr`, `expose_provenance`, `with_exposed_provenance`, `without_provenance`) |
| 1.85 | Edition 2024: `unsafe_op_in_unsafe_fn` warns; `static_mut_refs` denies |
| 1.86 | Debug-build null-pointer checks; safe `#[target_feature]` functions |
| 1.87 | Most `std::arch` intrinsics safe to call with the feature enabled |
| 1.88 | `#[unsafe(naked)]` functions with `naked_asm!` |
| 1.89 | `dangerous_implicit_autorefs` deny |
| 1.91 | `dangling_pointers_from_locals`, `integer_to_ptr_transmutes` lints |
| 1.92 | `Box::new_zeroed`, `Rc::new_zeroed`, `Arc::new_zeroed` |
| 1.93 | `<[MaybeUninit<T>]>::assume_init_ref`, `assume_init_mut`, `assume_init_drop`, `write_copy_of_slice`; `Vec::into_raw_parts` |
| 1.98 | Moving a `ManuallyDrop<Box<T>>` after dropping its contents is documented as sound |
| 1.99 | `Layout::for_value_raw`, `size_of_val_raw`, `align_of_val_raw`; `Box::into_non_null`, `from_non_null`; `Box::leak` documentation advises against later freeing leaked memory |
| 1.100 | `mem::conjure_zst`; `UnsafeCell::as_ref_unchecked`, `as_mut_unchecked`; `Allocator` with `Box::new_in` and `Vec::new_in` |

Per-release details live in [the versions index](../versions/index.md).

## Practical Boundaries

A safe abstraction must preserve its invariants for every input and interaction available to safe callers. An unsafe API instead documents the additional obligations callers must uphold. SAFETY comments explain how those obligations justify particular operations; their adequacy depends on the argument, not a one-sentence limit.

Initialization requires a valid value of the actual type. Raw-pointer construction does not establish alignment, readable extent, aliasing, or ownership; creating a reference imposes stronger validity requirements.

Miri, sanitizers, and target execution expose different classes of mistakes and leave different gaps; a successful run is not a general proof of soundness.
