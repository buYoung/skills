# Error Propagation and Reporting

## Contents

- [Propagation with ? and From](#propagation-with--and-from)
- [Application Errors with anyhow](#application-errors-with-anyhow)
- [Box dyn Error for Dynamic Boundaries](#box-dyn-error-for-dynamic-boundaries)
- [Exit Codes and main](#exit-codes-and-main)
- [Matching io::Error](#matching-ioerror)
- [Errors Across Iterators](#errors-across-iterators)
- [Combinators](#combinators)
- [Reporting Error Chains](#reporting-error-chains)
- [Lint Policy](#lint-policy)
- [Common Mistakes](#common-mistakes)
- [Availability by Version](#availability-by-version)
- [Practical Boundaries](#practical-boundaries)

Examples use stable APIs unless marked otherwise; see [compatibility](../../SKILL.md#compatibility). Blocks marked `deps` use `anyhow` 1. The error model and type design are in [error types](error-types.md); panic behavior in [panics](panics.md).

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

## Lint Policy

| Lint | Group | Default | Use |
|---|---|---|---|
| `unwrap_in_result` | restriction | allow | Functions returning `Result` should propagate, not unwrap |
| `unused_must_use` | rustc | warn | `Result` and `#[must_use]` values must be handled; `let _ = f();` is a decision, comment it |

## Common Mistakes

- Erasing errors before recovery decisions, or expecting downcasts to supply an undocumented stable public contract.
- A single `From<io::Error>` impl on an error type that reads several files, so every failure says "I/O error" without saying which file.
- Swallowing errors with `let _ = ...` or `.ok()` to satisfy `unused_must_use` without deciding that ignoring is correct.
- Logging the same error at every layer.
- Comparing `raw_os_error()` codes instead of `ErrorKind`.

## Availability by Version

| Version | Addition |
|---|---|
| 1.82 | `Option::is_none_or` |
| 1.83 | New `io::ErrorKind` variants (`StorageFull`, `ReadOnlyFilesystem`, `IsADirectory`, `NotADirectory`, `DirectoryNotEmpty`, others) |
| 1.89 | `Result::flatten` |
| 1.92 | `unused_must_use` no longer fires on `Result<(), Uninhabited>` |

Per-release details live in [the versions index](../versions/index.md).

## Practical Boundaries

Add context where an abstraction contributes useful information and preserve causes rather than logging the same propagation repeatedly.
