# Error Types

## Contents

- [Values, Propagation, and Error Information](#values-propagation-and-error-information)
- [Design the Failure Boundary](#design-the-failure-boundary)
- [Option, Result, or Panic](#option-result-or-panic)
- [Anatomy of a Library Error Type](#anatomy-of-a-library-error-type)
- [The Same Type with thiserror](#the-same-type-with-thiserror)
- [Public Error Types and Stability](#public-error-types-and-stability)
- [An Opaque Error with Stable Recovery Information](#an-opaque-error-with-stable-recovery-information)
- [Documenting Errors and Panics](#documenting-errors-and-panics)
- [Lint Policy](#lint-policy)
- [Common Mistakes](#common-mistakes)
- [Availability by Version](#availability-by-version)
- [Practical Boundaries](#practical-boundaries)

Examples use stable APIs unless marked otherwise; see [compatibility](../../SKILL.md#compatibility). Blocks marked `deps` use `thiserror` 2. Conversions, context, and reporting continue in [error propagation and reporting](error-propagation-and-reporting.md); panic behavior in [panics](panics.md); public-API stability in [crate compatibility](crate-compatibility.md).

## Values, Propagation, and Error Information

`Result<T, E>` represents success or failure as a value; it does not require `E` to implement `Error`. Pattern matching handles the variants. In a Result-returning function, `?` returns early on `Err`, applying an available `From` conversion; it does not log, retry, or choose a recovery policy.

`Display` supplies a human-readable message, while `Error::source` exposes a cause for reporting. A concrete enum or struct can carry information callers need for recovery. Erasing its type at a reporting boundary can simplify composition, but callers should not have to parse Display text to discover failure kinds.

Start with the manual [error type](#anatomy-of-a-library-error-type) to understand the contract, then compare [thiserror](#the-same-type-with-thiserror) for deriving the same implementations. [Application reporting](error-propagation-and-reporting.md#application-errors-with-anyhow) addresses a different need: adding context after the layer that makes recovery decisions. Panic behavior belongs to the separate [unwind/abort boundary](panics.md#panic-strategy-and-boundaries).

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
| `result_large_err` | perf | warn | Large `E` slows every `Ok` path |
| `missing_errors_doc`, `missing_panics_doc` | pedantic | allow | Public API documentation |

## Common Mistakes

- Error messages that end with a colon and the inner error's message, then printing the chain too, which duplicates text.

## Availability by Version

| Version | Addition |
|---|---|
| 1.81 | `core::error::Error` for `no_std` |
| 1.82 | Unreachable arms for uninhabited error types may be omitted (`let Ok(x) = infallible;`) |
| 1.100 | `Result<T, !>` can be written directly; `Infallible` is an alias of `!` |

Per-release details live in [the versions index](../versions/index.md).

## Practical Boundaries

Keep the information needed for recovery until the responsible layer has acted on it. An enum, opaque error struct, or erased reporting wrapper can each be appropriate at a different boundary.
