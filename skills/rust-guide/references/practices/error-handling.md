# Error Handling

## Contents

- [Option, Result, or Panic](#option-result-or-panic)
- [Anatomy of a Library Error Type](#anatomy-of-a-library-error-type)
- [The Same Type with thiserror](#the-same-type-with-thiserror)
- [Propagation with ? and From](#propagation-with--and-from)
- [Application Errors with anyhow](#application-errors-with-anyhow)
- [Box dyn Error for Prototypes](#box-dyn-error-for-prototypes)
- [Exit Codes and main](#exit-codes-and-main)
- [Public Error Types and Stability](#public-error-types-and-stability)
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
- [Review Checklist](#review-checklist)

Examples compile on stable Rust 1.80 or later with edition 2024 unless a version is stated. Blocks marked `deps` use `thiserror` 2 or `anyhow` 1. Public-API stability continues in [API and crate design](api-and-crate-design.md); panics across `extern "C"` in [unsafe and FFI](unsafe-and-ffi.md).

## Option, Result, or Panic

| Situation | Use | Reason |
|---|---|---|
| Absence is a normal outcome and needs no explanation (`find`, `first`, `get`) | `Option<T>` | Callers handle "nothing" without an error value |
| The operation can fail for reasons a caller may want to act on | `Result<T, E>` | Failure is part of the signature; "whether or not a function can produce an error is encoded in the function's type signature" |
| A precondition inside the program is violated (bug) | `panic!`, `assert!`, `unreachable!` | Not recoverable by callers; the program is already in a state the author did not anticipate |
| Input from outside the program is invalid | `Result` from a validating constructor | Invalid input is expected, not a bug |
| A library needs to report failure to any caller | Concrete error type implementing `std::error::Error` | Callers can match, log, and wrap it |
| A binary needs to report failure to a human | `anyhow::Error` or `Box<dyn Error>` with context | Nobody matches on it; the message matters |

A function returning `Option` where the caller needs to know why (not found versus permission denied) has thrown away information; a function returning `Result<T, ()>` has done the same.

## Anatomy of a Library Error Type

A library error is an `enum` with one variant per failure kind, structured fields for what the caller needs, `Display` for humans, `Error::source` for the cause chain, and `#[non_exhaustive]` so variants can be added later. Everything below is standard library only.

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
    let line = text
        .lines()
        .find_map(|l| l.strip_prefix("port="))
        .ok_or(ConfigError::MissingKey { key: "port" })?;
    line.trim()
        .parse::<u16>()
        .map_err(|source| ConfigError::Parse { line: 1, source })
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

`#[source]` marks the cause; a field literally named `source` is picked up automatically. `#[from]` implies `#[source]` and generates a `From` impl, which is right only when the wrapped error can come from exactly one place in this type; otherwise use `map_err` to attach context, as `Io` and `Parse` do above. `#[error(transparent)]` forwards `Display` and `source` to a single inner error for pass-through wrappers.

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

Binaries rarely match on error variants; they add context and print. `anyhow::Error` wraps any `std::error::Error + Send + Sync + 'static`, carries a context chain, and prints it with `{:#}` on one line or `{:?}` with a backtrace when `RUST_BACKTRACE` is set. It is "generally not a good choice for the public API of a library, but is widely used in applications."

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

## Box dyn Error for Prototypes

`Box<dyn std::error::Error + Send + Sync>` needs no crate and accepts any error, `&str`, or `String` through `?`. It fits prototypes, examples, and tests; it gives callers no way to distinguish failures, so it does not belong in a library's public API.

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

- Mark public error enums `#[non_exhaustive]` when introducing them; adding a variant is then a minor change.
- Keep error types `Send + Sync + 'static` so they cross threads and wrap into `Box<dyn Error + Send + Sync>`. A static assertion in tests prevents a field change from silently losing the guarantee.
- Implement `Debug`, `Display`, and `Error`; consider `Clone` and `PartialEq` only when the fields allow it (`io::Error` is neither).
- Keep the size of `E` in check on hot paths; `Result<T, E>` is as large as the larger of `T` and `E`. Box a rarely used large payload. Clippy `result_large_err` (perf) warns above 128 bytes by default.
- Never expose a third-party error type in a public API unless that crate is already a public dependency; wrap it or box it.

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

fn is_retryable(error: &io::Error) -> bool {
    matches!(
        error.kind(),
        ErrorKind::Interrupted | ErrorKind::WouldBlock | ErrorKind::TimedOut
    )
}
```

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

/// Called from C: no panic may cross this boundary.
#[unsafe(no_mangle)]
pub extern "C" fn checksum_bytes(ptr: *const u8, len: usize, out: *mut u32) -> i32 {
    if ptr.is_null() || out.is_null() {
        return -1;
    }
    // SAFETY: the C caller guarantees `ptr` points to `len` readable bytes and `out` is writable
    // for the duration of this call.
    let bytes = unsafe { std::slice::from_raw_parts(ptr, len) };
    match catch_unwind(AssertUnwindSafe(|| checksum(bytes))) {
        Ok(sum) => {
            // SAFETY: `out` is non-null and writable per the contract above.
            unsafe { out.write(sum) };
            0
        }
        Err(_) => -2,
    }
}
```

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

Public functions document their failure modes in `# Errors` and `# Panics` sections (API Guidelines C-FAILURE); Clippy `missing_errors_doc` and `missing_panics_doc` (pedantic) check for them.

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

Doc examples use `?`, not `unwrap()` (C-QUESTION-MARK), so copied code keeps propagating errors.

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

- Returning `Box<dyn Error>` from a library because it is convenient; callers cannot react to distinct failures.
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

## Review Checklist

- `Option` is used only where absence needs no explanation; everything else returns `Result`.
- Library error types are enums with structured fields, `Display`, `source()`, `#[non_exhaustive]`, and `Send + Sync + 'static`.
- `From` impls exist only where the conversion is unambiguous; otherwise `map_err` adds context.
- No `unwrap`/`expect` on input-derived values in library or service code; every remaining `expect` states its invariant.
- Panic strategy, FFI boundaries, and thread joins agree with how panics are expected to surface.
- Public functions document `# Errors` and `# Panics`; doc examples use `?`.
- Errors are logged once with the full chain, at the layer that handles them.
