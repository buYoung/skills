# Error Handling

## Contents

- [Values, Propagation, and Error Information](#values-propagation-and-error-information)
- [Design the Failure Boundary](#design-the-failure-boundary)
- [Option, Result, or Panic](#option-result-or-panic)
- [Anatomy of a Library Error Type](#anatomy-of-a-library-error-type)
- [The Same Type with thiserror](#the-same-type-with-thiserror)
- [Propagation with ? and From](#propagation-with--and-from)
- [Application Errors with anyhow](#application-errors-with-anyhow)
- [Box dyn Error for Dynamic Boundaries](#box-dyn-error-for-dynamic-boundaries)
- [Exit Codes and main](#exit-codes-and-main)
- [Public Error Types and Stability](#public-error-types-and-stability)
- [An Opaque Error with Stable Recovery Information](#an-opaque-error-with-stable-recovery-information)
- [Matching io::Error](#matching-ioerror)
- [Errors Across Iterators](#errors-across-iterators)
- [Combinators](#combinators)
- [Panics: When and How](#panics-when-and-how)
- [Panic Strategy and Boundaries](#panic-strategy-and-boundaries)
- [Reporting Error Chains](#reporting-error-chains)
- [Documenting Errors and Panics](#documenting-errors-and-panics)
- [Lint Policy](#lint-policy)
- [Common Mistakes](#common-mistakes)
- [Availability by Version](#availability-by-version)
- [Practical Boundaries](#practical-boundaries)

Examples use stable APIs unless marked otherwise; see [compatibility](../../SKILL.md#compatibility). Blocks marked `deps` use `thiserror` 2 or `anyhow` 1. Public-API stability continues in [API and crate design](api-and-crate-design.md); panics across `extern "C"` in [unsafe and FFI](unsafe-and-ffi.md).

## Values, Propagation, and Error Information

`Result<T, E>` represents success or failure as a value; it does not require `E` to implement `Error`. Pattern matching handles the variants. In a Result-returning function, `?` returns early on `Err`, applying an available `From` conversion; it does not log, retry, or choose a recovery policy.

`Display` supplies a human-readable message, while `Error::source` exposes a cause for reporting. A concrete enum or struct can carry information callers need for recovery. Erasing its type at a reporting boundary can simplify composition, but callers should not have to parse Display text to discover failure kinds.

Start with the manual [error type](#anatomy-of-a-library-error-type) to understand the contract, then compare [thiserror](#the-same-type-with-thiserror) for deriving the same implementations. [Application reporting](#application-errors-with-anyhow) addresses a different need: adding context after the layer that makes recovery decisions. Panic behavior belongs to the separate [unwind/abort boundary](#panic-strategy-and-boundaries).

## Design the Failure Boundary

Choose the information callers need before choosing an error crate. Recovery can be necessary inside an application, while a library can intentionally expose an opaque error representation.

| Caller need | Starting choice | Change when |
|---|---|---|
| One small, stable failure vocabulary | Concrete std/core error type implemented by hand | Repetitive Display/source conversions justify thiserror |
| Programmatic recovery by kind | Typed variants or an opaque error with stable accessors | Avoid exposing implementation-specific distinctions callers should not depend on |
| Human-facing context at an application boundary | anyhow or a suitable std-only reporting wrapper | Keep domain errors typed until recovery decisions are finished |
| Heterogeneous dynamic errors | `Box<dyn Error>` with the required bounds | A documented typed contract would make callers' recovery more reliable |
| Embedded/no heap | Small structured error, optionally core::error::Error on 1.81+ | Add allocation/reporting only if the environment and requirements permit it |

thiserror generates ordinary Error/Display implementations; it does not replace std's error model or require applications to use a different type architecture. An opaque public struct can hide a private enum and expose only a stable kind or selected accessors. Use non_exhaustive where future expansion is intended, not on every type automatically.

Attach actionable context at abstraction boundaries and preserve the source chain. Translate internal errors into public protocol/status codes at the relevant adapter; do not expose secrets or raw internal diagnostics as user-facing responses. Log at the layer deciding how the failure is handled rather than at every propagation step.

## Option, Result, or Panic

| Situation | Use | Reason |
|---|---|---|
| Absence is a normal outcome and needs no explanation (`find`, `first`, `get`) | `Option<T>` | Callers handle "nothing" without an error value |
| The operation can fail for reasons a caller may want to act on | `Result<T, E>` | Failure is part of the signature; "whether or not a function can produce an error is encoded in the function's type signature" |
| A precondition inside the program is violated (bug) | `panic!`, `assert!`, `unreachable!` | Not recoverable by callers; the program is already in a state the author did not anticipate |
| Input from outside the program is invalid | `Result` from a validating constructor | Invalid input is expected, not a bug |
| A library needs to report failure to any caller | Concrete error type implementing `std::error::Error` | Callers can match, log, and wrap it |
| An application boundary reports failure to a human | `anyhow::Error` or a std-only reporting wrapper | Preserve typed errors earlier where recovery depends on their kind |

A function returning `Option` where the caller needs to know why (not found versus permission denied) has thrown away information; a function returning `Result<T, ()>` has done the same.

## Anatomy of a Library Error Type

An error enum is useful when callers need distinct failure kinds. Use structured context, Display for humans, and source for causes. The example uses non_exhaustive to permit new variants; an opaque struct is another valid public design. Everything below is standard library only.

```rust
use std::fmt;
use std::io;
use std::num::ParseIntError;

#[derive(Debug)]
#[non_exhaustive]
pub enum ConfigError {
    Io { path: String, source: io::Error },
    Parse { line: usize, source: ParseIntError },
    MissingKey { key: &'static str },
}

impl fmt::Display for ConfigError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ConfigError::Io { path, .. } => write!(f, "cannot read config file `{path}`"),
            ConfigError::Parse { line, .. } => write!(f, "invalid number on line {line}"),
            ConfigError::MissingKey { key } => write!(f, "missing required key `{key}`"),
        }
    }
}

impl std::error::Error for ConfigError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            ConfigError::Io { source, .. } => Some(source),
            ConfigError::Parse { source, .. } => Some(source),
            ConfigError::MissingKey { .. } => None,
        }
    }
}

pub fn load_port(path: &str) -> Result<u16, ConfigError> {
    let text = std::fs::read_to_string(path)
        .map_err(|source| ConfigError::Io { path: path.to_owned(), source })?;
    let (line_number, line) = text
        .lines()
        .enumerate()
        .find_map(|(index, line)| line.strip_prefix("port=").map(|value| (index + 1, value)))
        .ok_or(ConfigError::MissingKey { key: "port" })?;
    line.trim()
        .parse::<u16>()
        .map_err(|source| ConfigError::Parse { line: line_number, source })
}
```

Design rules that this shape follows:

- `Display` describes the failure at this level without repeating the cause; the cause is reachable through `source()`, so a report can print the whole chain without duplicates.
- Fields hold what a caller needs to react (`path`, `line`, `key`), not preformatted strings.
- The type is `Send + Sync + 'static` because every field is; this keeps it usable across threads and inside `Box<dyn Error + Send + Sync>`.
- `description()` and `cause()` are deprecated; implement only `Display` and `source()`.

## The Same Type with thiserror

`thiserror` generates the `Display` and `Error` impls from attributes and is the common choice for library error types; it adds no runtime cost and no public dependency on `thiserror` types.

```rust,deps
use std::io;
use std::num::ParseIntError;
use thiserror::Error;

#[derive(Debug, Error)]
#[non_exhaustive]
pub enum ConfigError {
    #[error("cannot read config file `{path}`")]
    Io {
        path: String,
        #[source]
        source: io::Error,
    },
    #[error("invalid number on line {line}")]
    Parse {
        line: usize,
        #[source]
        source: ParseIntError,
    },
    #[error("missing required key `{key}`")]
    MissingKey { key: &'static str },
    /// `#[from]` implements `From<AddrParseError>` so `?` converts automatically.
    #[error("invalid listen address")]
    Address(#[from] std::net::AddrParseError),
}
```

`#[source]` marks the cause; a field literally named `source` is picked up automatically. `#[from]` implies `#[source]` and generates a `From` impl, which fits when the conversion has one domain meaning and needs no call-site context; otherwise use `map_err` to attach context, as `Io` and `Parse` do above. `#[error(transparent)]` forwards `Display` and `source` to a single inner error for pass-through wrappers.

## Propagation with ? and From

`?` returns early with `Err(From::from(e))`. Implementing `From<Inner> for Outer` makes `?` convert; doing so for every inner error is convenient but loses which operation failed when the same inner type appears in several places. Attach context at the call site when the inner type is ambiguous.

```rust
use std::fmt;

#[derive(Debug)]
pub enum ImportError {
    ReadManifest(std::io::Error),
    ReadPayload(std::io::Error),
    Decode { offset: usize },
}

impl fmt::Display for ImportError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ImportError::ReadManifest(_) => f.write_str("cannot read manifest"),
            ImportError::ReadPayload(_) => f.write_str("cannot read payload"),
            ImportError::Decode { offset } => write!(f, "malformed payload at byte {offset}"),
        }
    }
}

impl std::error::Error for ImportError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            ImportError::ReadManifest(e) | ImportError::ReadPayload(e) => Some(e),
            ImportError::Decode { .. } => None,
        }
    }
}

fn import(dir: &std::path::Path) -> Result<usize, ImportError> {
    // The same io::Error type arises twice; map_err records which read failed.
    let manifest = std::fs::read(dir.join("manifest")).map_err(ImportError::ReadManifest)?;
    let payload = std::fs::read(dir.join("payload")).map_err(ImportError::ReadPayload)?;
    if payload.first() != Some(&0x7f) {
        return Err(ImportError::Decode { offset: 0 });
    }
    Ok(manifest.len() + payload.len())
}
```

`?` also works on `Option` inside functions returning `Option`, and converts `Option` to `Result` with `ok_or`/`ok_or_else` first when the function returns `Result`.

## Application Errors with anyhow

At a reporting boundary, applications often add context and print rather than match on every lower-level variant. Keep errors typed where the application still needs recovery decisions. `anyhow::Error` wraps any `std::error::Error + Send + Sync + 'static`, carries a context chain, and prints it with `{:#}` on one line or `{:?}` with a backtrace when `RUST_BACKTRACE` is set. It is "generally not a good choice for the public API of a library, but is widely used in applications."

```rust,deps
use anyhow::{bail, ensure, Context, Result};

fn read_port(path: &str) -> Result<u16> {
    let text = std::fs::read_to_string(path).with_context(|| format!("reading config `{path}`"))?;
    let port: u16 = text.trim().parse().context("`port` must be an integer in 0..=65535")?;
    ensure!(port >= 1024, "port {port} is privileged; use 1024 or above");
    if port == 8080 {
        bail!("port 8080 is reserved for the health endpoint");
    }
    Ok(port)
}

fn main() -> Result<()> {
    let port = read_port("app.conf")?;
    println!("listening on {port}");
    Ok(())
}
```

`with_context` takes a closure so the message is built only on failure. `downcast_ref::<T>()` recovers a concrete error when one code path does need to react. A library that uses `anyhow` internally still exposes its own error type at the public boundary.

## Box dyn Error for Dynamic Boundaries

`Box<dyn std::error::Error + Send + Sync>` needs no external crate and accepts compatible concrete errors and string messages through conversions used by `?`. Downcasting can recover a known concrete error. It does not expose a closed failure vocabulary or guarantee a stable recovery contract; use it deliberately at dynamic/reporting boundaries. A public library whose callers need reliable recovery should expose documented variants or accessors instead.

```rust
type BoxError = Box<dyn std::error::Error + Send + Sync + 'static>;

fn parse_pair(input: &str) -> Result<(u32, u32), BoxError> {
    let (a, b) = input.split_once(',').ok_or("expected `a,b`")?; // &str converts into BoxError
    Ok((a.trim().parse()?, b.trim().parse()?))
}
```

## Exit Codes and main

`main` may return `Result<(), E>` for any `E: Debug`; on `Err` the runtime prints the `Debug` form and exits with code 1. For messages meant for users, print the `Display` form yourself and choose the code.

```rust
use std::process::ExitCode;

fn run() -> Result<(), String> {
    Err("disk full".to_owned())
}

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(message) => {
            eprintln!("error: {message}");
            ExitCode::from(2)
        }
    }
}
```

`std::process::exit` skips destructors and buffered output; return from `main` instead so `Drop` runs.

## Public Error Types and Stability

- Use non_exhaustive for public enums intended to grow; a deliberately closed vocabulary or an opaque struct can be a better contract.
- Promise Send + Sync + static where consumers need those bounds for task transfer or reporting wrappers. Borrowed or thread-local errors can be appropriate internally; preserve any bounds already promised publicly.
- Implement `Debug`, `Display`, and `Error`; consider `Clone` and `PartialEq` only when the fields allow it (`io::Error` is neither).
- Keep the size of `E` in check on hot paths; the layout of `Result<T, E>` depends on both variants, alignment, and discriminant/niche optimization, not simply the size of E alone. Box a rarely used large payload. Clippy `result_large_err` (perf) warns above 128 bytes by default.
- Exposing a third-party error type makes it part of the public dependency contract. Use a wrapper or opaque representation when that coupling is unnecessary; intentional public dependencies can be appropriate.

```rust
#[derive(Debug)]
pub struct QueueError {
    pub attempts: u32,
}

impl std::fmt::Display for QueueError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "queue unavailable after {} attempts", self.attempts)
    }
}

impl std::error::Error for QueueError {}

#[cfg(test)]
mod tests {
    fn assert_error_bounds<T: std::error::Error + Send + Sync + 'static>() {}

    #[test]
    fn queue_error_is_send_sync_static() {
        assert_error_bounds::<super::QueueError>();
    }
}
```

## An Opaque Error with Stable Recovery Information

A public struct can hide implementation variants while exposing a small recovery vocabulary. This avoids forcing callers to depend on the exact parser or I/O error representation. The source chain remains available for diagnostics.

```rust
use std::{fmt, io, num::{NonZeroUsize, ParseIntError}, path::Path};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[non_exhaustive]
pub enum LoadKind { Missing, Invalid, Temporary, Other }

#[derive(Debug)]
pub struct LoadError(Repr);
#[derive(Debug)]
enum Repr { Io(io::Error), Number(ParseIntError), Zero }

impl LoadError {
    pub fn kind(&self) -> LoadKind {
        match &self.0 {
            Repr::Io(error) => match error.kind() {
                io::ErrorKind::NotFound => LoadKind::Missing,
                io::ErrorKind::TimedOut | io::ErrorKind::WouldBlock
                    | io::ErrorKind::Interrupted => LoadKind::Temporary,
                _ => LoadKind::Other,
            },
            Repr::Number(_) | Repr::Zero => LoadKind::Invalid,
        }
    }
}
impl fmt::Display for LoadError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(match &self.0 {
            Repr::Io(_) => "cannot read limit",
            Repr::Number(_) => "limit is not an unsigned integer",
            Repr::Zero => "limit must be nonzero",
        })
    }
}
impl std::error::Error for LoadError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match &self.0 {
            Repr::Io(error) => Some(error),
            Repr::Number(error) => Some(error),
            Repr::Zero => None,
        }
    }
}

pub fn load_limit(path: &Path) -> Result<NonZeroUsize, LoadError> {
    let text = std::fs::read_to_string(path).map_err(|e| LoadError(Repr::Io(e)))?;
    let value = text.trim().parse::<usize>().map_err(|e| LoadError(Repr::Number(e)))?;
    NonZeroUsize::new(value).ok_or(LoadError(Repr::Zero))
}

pub fn limit_or_default(path: &Path, default: NonZeroUsize) -> Result<NonZeroUsize, LoadError> {
    match load_limit(path) {
        Err(error) if error.kind() == LoadKind::Missing => Ok(default),
        other => other,
    }
}
```

The application can default a missing optional file without treating malformed configuration or permission failures as absence. A Temporary classification is information for a retry policy, not permission to retry indefinitely: deadline, attempt budget, backoff, cancellation, and whether an operation is safe to repeat still belong to the operation's owner. This example performs a read; a write may have already produced side effects before its error.

At the final CLI/logging boundary, add operation context and print the cause chain once. Erasing the concrete type there with anyhow or Box<dyn Error> can simplify reporting. Erasing it before limit_or_default would make the intended recovery contract harder to express. Avoid copying low-level error messages into public protocol responses when they contain paths or sensitive data.

The stable public contract is kind(), Display, source(), and promised trait bounds. A future implementation can change its private parser representation while preserving that contract. An enum is simpler when callers legitimately need the complete variant structure; an opaque wrapper is useful when implementation details should remain private.

## Matching io::Error

`io::Error` carries an `ErrorKind`; match on kinds instead of comparing `raw_os_error` codes, which differ per platform. Rust 1.83 added many specific kinds.

```rust
use std::io::{self, ErrorKind};

fn explain_write_failure(error: &io::Error) -> &'static str {
    match error.kind() {
        ErrorKind::StorageFull => "the disk is full",               // 1.83
        ErrorKind::ReadOnlyFilesystem => "the filesystem is read-only", // 1.83
        ErrorKind::PermissionDenied => "permission denied",
        ErrorKind::Interrupted => "interrupted; retry the write",
        ErrorKind::NotFound => "the target directory does not exist",
        _ => "write failed",
    }
}

```

An ErrorKind alone is not an application retry policy. Check the failed operation, partial progress, idempotency, deadline, and attempt budget. WouldBlock normally requires readiness handling, not a busy retry loop; a timeout does not prove that a remote side effect failed.

`io::Error::new(kind, payload)` wraps a custom error with a kind; `io::Error::other(payload)` is the shorthand for `ErrorKind::Other`. `error.get_ref()` and `into_inner()` recover the payload.

## Errors Across Iterators

Collecting an iterator of `Result`s into `Result<Vec<_>, _>` stops at the first error; collecting into a pair of vectors keeps every outcome.

```rust
use std::num::ParseIntError;

fn parse_all(inputs: &[&str]) -> Result<Vec<u32>, ParseIntError> {
    inputs.iter().map(|s| s.parse::<u32>()).collect()
}

fn parse_partitioned(inputs: &[&str]) -> (Vec<u32>, Vec<(usize, ParseIntError)>) {
    let mut values = Vec::new();
    let mut errors = Vec::new();
    for (index, input) in inputs.iter().enumerate() {
        match input.parse::<u32>() {
            Ok(value) => values.push(value),
            Err(error) => errors.push((index, error)),
        }
    }
    (values, errors)
}

fn sum_checked(inputs: &[u32]) -> Option<u32> {
    inputs.iter().try_fold(0u32, |acc, &x| acc.checked_add(x))
}
```

`Option<Vec<T>>` collects the same way from an iterator of `Option<T>`. `try_fold` and `try_for_each` short-circuit with `Result` or `Option` without allocating.

## Combinators

| Method | Since | Use |
|---|---|---|
| `map_err(f)` | 1.0 | Convert the error type or add context |
| `ok_or(e)`, `ok_or_else(f)` | 1.0 | `Option` to `Result`; prefer `ok_or_else` when building `e` costs |
| `and_then(f)` | 1.0 | Chain a fallible step |
| `unwrap_or(v)`, `unwrap_or_else(f)`, `unwrap_or_default()` | 1.0 / 1.16 | Fallback value; lazy variant for expensive fallbacks |
| `map_or(v, f)`, `map_or_else(g, f)` | 1.0 | Transform or fall back in one call |
| `is_some_and(p)`, `is_ok_and(p)` | 1.70 | Test the contained value without matching |
| `is_none_or(p)` | 1.82 | `None` or the value satisfies `p` |
| `inspect(f)`, `inspect_err(f)` | 1.76 | Log without consuming |
| `transpose()` | 1.33 | `Option<Result<T, E>>` to `Result<Option<T>, E>` and back |
| `Option::flatten()` | 1.40 | `Option<Option<T>>` to `Option<T>` |
| `Result::flatten()` | 1.89 | `Result<Result<T, E>, E>` to `Result<T, E>` |
| `?` | 1.13 | Early return with `From` conversion |

```rust
use std::collections::HashMap;

fn port_from_env(env: &HashMap<String, String>) -> Result<u16, String> {
    env.get("PORT")
        .ok_or_else(|| "PORT is not set".to_owned())
        .and_then(|raw| raw.parse::<u16>().map_err(|e| format!("PORT is not a number: {e}")))
        .inspect_err(|e| eprintln!("config warning: {e}"))
}

fn timeout_ms(env: &HashMap<String, String>) -> u64 {
    env.get("TIMEOUT_MS")
        .and_then(|raw| raw.parse().ok())
        .unwrap_or(30_000)
}
```

Prefer `?` with early returns once a chain exceeds two or three combinators; readability wins over cleverness. `Option::ok_or(expensive())` evaluates the argument even on `Some`; use `ok_or_else`.

## Panics: When and How

Panic for bugs: a violated invariant, an impossible state, an index the code just proved in range. Do not panic for input validation, I/O failure, or anything the caller could reasonably handle.

- `expect("...")` with a message that states the invariant ("config validated at startup"), not the failure ("failed to unwrap").
- `assert!`/`assert_eq!` for cheap checks that guard soundness or correctness; `debug_assert!` for expensive checks that only need to run in debug builds.
- `unreachable!("...")` for match arms the type system cannot rule out but the logic does.
- `todo!()` and `unimplemented!()` never ship; Clippy `todo` and `unimplemented` (restriction) can enforce this per crate.
- Library code avoids `unwrap()` on values that depend on inputs; `unwrap()` on a value that a previous line established is acceptable with a comment, or better, restructure so the value is proven by the type.

```rust
fn median(sorted: &[u32]) -> u32 {
    assert!(!sorted.is_empty(), "median of an empty slice is undefined");
    debug_assert!(sorted.is_sorted(), "caller must pass a sorted slice"); // is_sorted: 1.82
    sorted[sorted.len() / 2]
}
```

Since 1.81 the standard sorts may panic when an `Ord` implementation is not a total order, which turns silently wrong orderings into visible bugs.

## Panic Strategy and Boundaries

| Setting or boundary | Effect |
|---|---|
| `panic = "unwind"` (default) | Destructors run while unwinding; `catch_unwind` works; a panicking thread returns `Err(payload)` from `JoinHandle::join` |
| `panic = "abort"` | Smaller binary, no unwinding; `catch_unwind` cannot catch; any panic ends the process; tests and benches ignore the setting |
| Panic reaching `extern "C"` | The process aborts (1.81+); use `catch_unwind` inside the function or declare `extern "C-unwind"` when both sides support unwinding |
| Panic inside `Drop` during unwinding | Abort |
| Panic while holding a `Mutex` | The mutex is poisoned; other threads see `Err(PoisonError)` |

```rust
use std::panic::{catch_unwind, AssertUnwindSafe};
use std::sync::{Mutex, PoisonError};
use std::thread;

fn worker_result() -> Result<u32, String> {
    let handle = thread::spawn(|| -> u32 { 41 + 1 });
    handle.join().map_err(|payload| {
        payload
            .downcast_ref::<&str>()
            .map(|s| s.to_string())
            .or_else(|| payload.downcast_ref::<String>().cloned())
            .unwrap_or_else(|| "worker panicked".to_owned())
    })
}

fn read_counter(counter: &Mutex<u64>) -> u64 {
    // A poisoned lock means another thread panicked while holding it. A plain counter is still
    // meaningful, so recover; for multi-step invariants, propagate the error instead.
    *counter.lock().unwrap_or_else(PoisonError::into_inner)
}

fn checksum(bytes: &[u8]) -> u32 {
    bytes.iter().map(|&b| u32::from(b)).sum()
}

/// Computes a checksum, returning -1 for null pointers and -2 for an unwinding panic.
///
/// # Safety
/// If both pointers are non-null, `ptr` must identify `len` initialized readable
/// bytes within one allocation, with `len <= isize::MAX`. The input must remain
/// valid and unmodified during this call. Even for zero length, it must be a
/// properly aligned, non-null pointer suitable for an empty slice.
/// `out` must be aligned and valid for writing one u32, must not overlap the input,
/// and must permit exclusive access for the duration of the call.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn checksum_bytes(ptr: *const u8, len: usize, out: *mut u32) -> i32 {
    if ptr.is_null() || out.is_null() {
        return -1;
    }
    // SAFETY: the caller guarantees a valid, initialized, immutable input range.
    let bytes = unsafe { std::slice::from_raw_parts(ptr, len) };
    match catch_unwind(AssertUnwindSafe(|| checksum(bytes))) {
        Ok(sum) => {
            // SAFETY: the caller guarantees aligned, exclusive writable output storage.
            unsafe { out.write(sum) };
            0
        }
        Err(_) => -2,
    }
}
```

The unsafe signature makes the caller's obligations explicit to Rust callers too; C callers must uphold the same contract. Null checks cannot validate an arbitrary non-null pointer. `catch_unwind` handles unwinding panics, not undefined behavior or `panic = "abort"`.

Set a panic hook (`std::panic::set_hook`) in binaries that need structured crash logs; since 1.81 the hook receives `PanicHookInfo`, and 1.91 adds `payload_as_str()`.

## Reporting Error Chains

Print the chain from the outermost error to the root cause; each level says one thing.

```rust
fn report(error: &dyn std::error::Error) -> String {
    let mut text = error.to_string();
    let mut source = error.source();
    while let Some(cause) = source {
        text.push_str(": ");
        text.push_str(&cause.to_string());
        source = cause.source();
    }
    text
}
```

With `anyhow`, `{:#}` prints the same shape. Log an error once, at the level that handles it; logging at every level of propagation produces duplicate lines with less context each.

## Documenting Errors and Panics

Public functions document their failure modes in `# Errors` and `# Panics` sections; Clippy `missing_errors_doc` and `missing_panics_doc` (pedantic) check for them.

````rust
/// Parses a TCP port.
///
/// # Errors
///
/// Returns [`std::num::ParseIntError`] when `text` is not a decimal integer in `0..=65535`.
///
/// # Examples
///
/// ```
/// # fn main() -> Result<(), std::num::ParseIntError> {
/// assert_eq!(parse_port("8080")?, 8080);
/// # Ok(())
/// # }
/// # fn parse_port(text: &str) -> Result<u16, std::num::ParseIntError> { text.trim().parse() }
/// ```
pub fn parse_port(text: &str) -> Result<u16, std::num::ParseIntError> {
    text.trim().parse()
}
````

Doc examples use `?`, not `unwrap()`, so copied code keeps propagating errors.

## Lint Policy

| Lint | Group | Default | Use |
|---|---|---|---|
| `unwrap_used`, `expect_used` | restriction | allow | Enable per crate where panics are forbidden (services, libraries); allow in tests |
| `unwrap_in_result` | restriction | allow | Functions returning `Result` should propagate, not unwrap |
| `panicking_unwrap` | correctness | deny | `unwrap` on a value known to be `None`/`Err` |
| `indexing_slicing`, `arithmetic_side_effects` | restriction | allow | Panic-free arithmetic and indexing in critical paths |
| `result_large_err` | perf | warn | Large `E` slows every `Ok` path |
| `missing_errors_doc`, `missing_panics_doc` | pedantic | allow | Public API documentation |
| `todo`, `unimplemented`, `dbg_macro`, `print_stdout` | restriction | allow | Keep debugging aids out of release code |
| `unused_must_use` | rustc | warn | `Result` and `#[must_use]` values must be handled; `let _ = f();` is a decision, comment it |

## Common Mistakes

- Erasing errors before recovery decisions, or expecting downcasts to supply an undocumented stable public contract.
- A single `From<io::Error>` impl on an error type that reads several files, so every failure says "I/O error" without saying which file.
- Error messages that end with a colon and the inner error's message, then printing the chain too, which duplicates text.
- `unwrap()` in a request handler on a value derived from user input.
- Swallowing errors with `let _ = ...` or `.ok()` to satisfy `unused_must_use` without deciding that ignoring is correct.
- Using `panic = "abort"` and still expecting `catch_unwind` or `join()` error recovery to work.
- Logging the same error at every layer.
- Comparing `raw_os_error()` codes instead of `ErrorKind`.

## Availability by Version

| Version | Addition |
|---|---|
| 1.81 | `core::error::Error` for `no_std`; `PanicHookInfo`; panics abort at `extern "C"`; sorts may panic on invalid `Ord` |
| 1.82 | `Option::is_none_or`; unreachable arms for uninhabited error types may be omitted (`let Ok(x) = infallible;`) |
| 1.83 | New `io::ErrorKind` variants (`StorageFull`, `ReadOnlyFilesystem`, `IsADirectory`, `NotADirectory`, `DirectoryNotEmpty`, others) |
| 1.89 | `Result::flatten` |
| 1.91 | `PanicHookInfo::payload_as_str`; panic messages include the thread ID |
| 1.92 | `unused_must_use` no longer fires on `Result<(), Uninhabited>` |

Per-release details live in [the versions index](../versions/index.md).

## Practical Boundaries

Keep the information needed for recovery until the responsible layer has acted on it. An enum, opaque error struct, or erased reporting wrapper can each be appropriate at a different boundary. Add context where an abstraction contributes useful information and preserve causes rather than logging the same propagation repeatedly.

Expected input and capacity failures usually belong in Result. An expect can express an established invariant, but it should not stand in for validation of an external condition. Error propagation, task/thread failure, panic unwinding, process abort, and foreign calls have different behavior; an application's failure policy must account for the boundaries it actually crosses.
