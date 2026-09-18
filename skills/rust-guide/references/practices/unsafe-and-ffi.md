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
- [Sharing Raw Pointers Across Threads](#sharing-raw-pointers-across-threads)
- [PhantomData](#phantomdata)
- [Verification with Miri and Lints](#verification-with-miri-and-lints)
- [Common Mistakes](#common-mistakes)
- [Availability by Version](#availability-by-version)
- [Review Checklist](#review-checklist)

Examples compile on stable Rust 1.84 or later with edition 2024 unless a version is stated (edition 2024 requires `unsafe extern`, `#[unsafe(no_mangle)]`, and `unsafe {}` inside `unsafe fn`). Lock and atomic semantics are in [concurrency](concurrency.md); the edition migration steps for `unsafe` code are in [Rust 1.85 and edition 2024](../versions/1.85.md).

## What unsafe Unlocks

The Rustonomicon lists exactly five operations that need `unsafe`:

1. Dereference raw pointers.
2. Call `unsafe` functions, including C functions, compiler intrinsics, and the raw allocator.
3. Implement `unsafe` traits (`Send`, `Sync`, `GlobalAlloc`, and others).
4. Access or modify mutable statics.
5. Access fields of unions.

Everything else, including integer overflow, leaks, and deadlocks, is safe Rust. The keyword marks where the compiler stops checking and the author takes over; the author's job is to keep the program free of the behaviors listed next.

## Undefined Behavior

The Reference's list of undefined behavior; any of these anywhere in the program invalidates all guarantees, even in code that never runs the offending line:

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

The Reference lists behaviors the compiler does not consider unsafe: deadlocks, leaks of memory and other resources, exiting without running destructors, exposing randomized base addresses through pointer leaks, integer overflow (a panic in debug builds, two's-complement wrapping in release), and logic errors such as violating a `Hash`/`Eq` contract or mutating a key stored in a `BTreeMap`. They are still bugs, but `unsafe` code may not rely on their absence for soundness; for example, a guard type cannot assume its `Drop` will run because `mem::forget` is safe.

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

The Rustonomicon: "the only bullet-proof way to limit the scope of unsafe code is at the module boundary with privacy." Keep the fields that carry an invariant private, keep the `unsafe` in the smallest module that can uphold the invariant, and expose a safe API. Everything outside that module can then be trusted without reading it.

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

The invariant is stated once on the struct, every `unsafe` block refers to it, and no public method can break it. Since 1.93, `<[MaybeUninit<T>]>::assume_init_ref` and `assume_init_drop` express the slice operations directly. The Rust Design Patterns book phrases the same rule as "Contain unsafety in small modules": `String` is a `Vec<u8>` with a UTF-8 invariant enforced by exactly this technique.

## Uninitialized Memory

Never create an integer, reference, or `bool` from uninitialized bytes, even to overwrite it. Safe tools cover most needs:

| Need | Safe tool |
|---|---|
| Zero-filled buffer | `vec![0u8; n]`, `[0u8; N]`, `Box::new_zeroed` (1.92) for large allocations |
| Buffer filled by a reader | `Vec::with_capacity(n)` plus `Read::read_to_end`, or `resize(n, 0)` then `read_exact` |
| Array built element by element | `std::array::from_fn(|i| ...)` |
| Partially initialized storage | `MaybeUninit<T>` with `write`, then `assume_init*` under a documented invariant, as in `FixedVec` above |
| Spare capacity of a `Vec` | `spare_capacity_mut()` returns `&mut [MaybeUninit<T>]`; `set_len` afterwards is `unsafe` and requires every element written |

`mem::zeroed::<T>()` is only valid when all-zero bytes are a valid `T` (integers, floats, raw pointers, `Option<Box<T>>`); zeroed references, `NonNull`, `bool`-carrying enums with no zero variant, and `char`-free types are undefined behavior at the moment they are produced. `mem::uninitialized` is deprecated and unsound for almost every type.

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

The Rustonomicon's transmute rules: the types must have the same size; the result must be a valid value (transmuting `3u8` to `bool` is undefined behavior); `&T` to `&mut T` is "always Undefined Behavior"; a transmuted reference without an explicit lifetime gets an unbounded one; compound types need identical layout, which the default `repr(Rust)` does not guarantee even between two identical-looking structs. The `bytemuck` and `zerocopy` crates provide checked casts for plain-old-data types and are the ecosystem answer to most byte-reinterpretation needs. Clippy `missing_transmute_annotations` (suspicious) asks for explicit type arguments so inference cannot pick a surprising type.

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

For single-threaded embedded targets without atomics, `Cell`/`RefCell` inside a `static` with a `Sync` wrapper, or the platform's critical-section primitive, replaces `static mut`.

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
    // `safe`: sound to call with any argument, so callers need no unsafe block.
    safe fn abs(value: c_int) -> c_int;
}

fn c_length(text: &str) -> Result<usize, std::ffi::NulError> {
    let owned = CString::new(text)?; // interior NUL bytes are rejected here
    // SAFETY: `owned` is a valid NUL-terminated string that lives until after the call returns.
    Ok(unsafe { strlen(owned.as_ptr()) })
}

fn string_from_c(ptr: *const c_char) -> Option<String> {
    if ptr.is_null() {
        return None;
    }
    // SAFETY: the caller guarantees `ptr` points to a NUL-terminated string that stays valid and
    // unmodified for the duration of this call.
    let text = unsafe { CStr::from_ptr(ptr) };
    Some(text.to_string_lossy().into_owned())
}

fn magnitude(value: c_int) -> c_int {
    abs(value)
}
```

- Use `core::ffi`/`std::ffi` integer aliases (`c_int`, `c_long`, `c_char`, `c_void`) so widths follow the platform; `i128`/`u128` are C-compatible with `__int128` since 1.89.
- `#[repr(C)]` on every struct that crosses the boundary; the default representation may reorder fields.
- C strings: `CString` to hand text to C, `CStr` to read it; `c"literal"` (1.77) for compile-time C string constants. A `String` is not NUL-terminated and a `&str` may contain interior NULs.
- `Option<extern "C" fn(...)>` and `Option<&T>` are guaranteed to have the same layout as a nullable pointer, so they model nullable function pointers and pointers without extra flags.
- Since 1.87, most `std::arch` intrinsics without pointer arguments are safe when the target feature is enabled; keep `unsafe` only where the compiler still requires it (`unused_unsafe` warns otherwise).
- Link attributes: `#[link(name = "foo")]` on the block; `#[unsafe(no_mangle)]`, `#[unsafe(export_name)]`, `#[unsafe(link_section)]` on exported items (edition 2024 requires the `unsafe(...)` wrapper).

## FFI: Callbacks and Panics

A panic that reaches an `extern "C"` function aborts the process (1.81 and later); it never unwinds into C. Callbacks convert panics to error codes with `catch_unwind`, and use `extern "C-unwind"` only when both sides are built to unwind through each other.

```rust
use std::ffi::c_void;
use std::panic::{catch_unwind, AssertUnwindSafe};

type ValueCallback = unsafe extern "C" fn(user_data: *mut c_void, value: i32) -> i32;

struct Accumulator {
    total: i64,
}

unsafe extern "C" fn on_value(user_data: *mut c_void, value: i32) -> i32 {
    // SAFETY: `register` passed a pointer to a live `Accumulator`, and the C library promises
    // to call back only while that object is registered and never from two threads at once.
    let accumulator = unsafe { &mut *user_data.cast::<Accumulator>() };
    match catch_unwind(AssertUnwindSafe(|| {
        accumulator.total += i64::from(value);
    })) {
        Ok(()) => 0,
        Err(_) => -1, // a panic becomes an error code instead of unwinding into C
    }
}

fn register(accumulator: &mut Accumulator) -> (ValueCallback, *mut c_void) {
    (on_value, std::ptr::from_mut(accumulator).cast::<c_void>())
}
```

- Unregister callbacks in `Drop` of the owning Rust object so C never calls into freed memory.
- A callback that must call back into an object behind `&mut` needs exclusive access guaranteed by the C library's threading contract; otherwise use a `Mutex` inside the object.
- `catch_unwind` needs `UnwindSafe`; `AssertUnwindSafe` asserts it for closures that capture `&mut`, which is fine when a panic leaves the state in a shape the code tolerates.

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

The Rustonomicon's obligations: `Send` requires no unsynchronized shared mutable state and cleanup that is valid on another thread; `Sync` requires either no interior mutability or all mutation behind exclusive access. `Rc`, `Cell`, and `RefCell` inside the type make both impls unsound. When in doubt, wrap the handle in a `Mutex` and implement nothing.

## PhantomData

`PhantomData<T>` tells the compiler about ownership, variance, and auto traits for data a raw pointer points at. From the Rustonomicon's table:

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
- For every `unsafe` block, review the `// SAFETY:` claim against the undefined-behavior list above; a claim that cannot be stated in one sentence usually hides a missing invariant.

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

## Review Checklist

- Each `unsafe` block has a one-sentence `// SAFETY:` claim tied to an invariant stated on the type or function.
- Every `pub unsafe fn` has a `# Safety` section; every safe function is sound for all arguments.
- Invariants live behind private fields in one module; the public API cannot break them.
- No value is created from uninitialized or zeroed bytes unless every bit pattern is valid for its type.
- No reference to misaligned or uninitialized memory exists, even transiently; `&raw` is used for packed fields.
- `transmute` appears only with equal sizes, valid values, and matching layouts, and never between reference types with different pointees.
- FFI signatures were checked against the C header; ownership of every pointer crossing the boundary is documented.
- Callbacks cannot unwind into C; `catch_unwind` converts panics to error codes.
- `unsafe impl Send`/`Sync` cite the foreign library's threading contract.
- Miri ran on the pure-Rust `unsafe` code; the debug build ran the tests.
