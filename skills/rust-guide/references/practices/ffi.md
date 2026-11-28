# FFI

## Contents

- [FFI: Declaring and Calling C](#ffi-declaring-and-calling-c)
- [FFI: Callbacks and Panics](#ffi-callbacks-and-panics)
- [FFI: Types and Ownership Across the Boundary](#ffi-types-and-ownership-across-the-boundary)
- [Own a Foreign Allocation with a Rust Handle](#own-a-foreign-allocation-with-a-rust-handle)
- [Sharing Raw Pointers Across Threads](#sharing-raw-pointers-across-threads)
- [Common Mistakes](#common-mistakes)
- [Availability by Version](#availability-by-version)
- [Practical Boundaries](#practical-boundaries)

Edition-2024 examples require Rust 1.85 or later, subject to any newer API version stated beside an example. That edition requires `unsafe extern` blocks and unsafe attributes such as `#[unsafe(no_mangle)]`. Omitting explicit `unsafe {}` around unsafe operations in an unsafe function triggers the default-warning `unsafe_op_in_unsafe_fn` lint; a deny setting makes it an error. Explicit blocks separate the caller's safety contract from the implementation's unsafe operations. Safety contracts, raw-pointer validity, and verification tools are in [unsafe Rust](unsafe-rust.md); migration details are in [Rust 1.85 and edition 2024](../versions/1.85.md).

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

Ownership crosses the boundary explicitly: a `Box::into_raw` handed to C is leaked until C returns it to a Rust function that calls `Box::from_raw`. Two allocators must never free each other's memory. Since 1.91 C-variadic functions can be declared for `sysv64`, `win64`, `efiapi`, and `aapcs`; since 1.99 they can also be defined in Rust with the `"C"` and `"C-unwind"` ABIs, reading arguments through `core::ffi::VaList`.

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

## Common Mistakes

- A Rust `enum` in an FFI signature where C may pass unknown values.
- `Box::from_raw` on memory C allocated, or `free()` on memory Rust allocated.
- Letting a panic escape a callback.
- `unsafe impl Send`/`Sync` written to silence the compiler rather than from the library's documented threading contract.
- Holding `&mut` to data also reachable through a raw pointer that C still uses (aliasing violation).

## Availability by Version

| Version | Change |
|---|---|
| 1.77 | C string literals `c"..."` |
| 1.81 | Panics abort at `extern "C"` boundaries |
| 1.82 | `unsafe extern` blocks with `safe` items; `#[unsafe(no_mangle)]` and friends |
| 1.85 | Edition 2024: `unsafe extern` and `unsafe(...)` attributes mandatory |
| 1.89 | `i128`/`u128` FFI-safe |
| 1.91 | C-variadic declarations |
| 1.99 | C-variadic function definitions; 1.99.1 fixes x86_64 FFI `bool` returns |

Per-release details live in [the versions index](../versions/index.md).

## Practical Boundaries

Foreign interfaces add ABI, allocation/deallocation, callback lifetime, and thread-affinity contracts. A panic strategy must match the ABI and build configuration. catch_unwind handles unwinding Rust panics, not arbitrary foreign failures or aborting panics.
