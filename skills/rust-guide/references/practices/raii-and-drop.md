# RAII and Drop

## Contents

- [RAII Guards and Drop](#raii-guards-and-drop)
- [Drop Order Rules](#drop-order-rules)
- [Common Mistakes](#common-mistakes)
- [Availability by Version](#availability-by-version)
- [Practical Boundaries](#practical-boundaries)

Examples use stable APIs unless marked otherwise; see [compatibility](../../SKILL.md#compatibility). How ownership decides when a value is destroyed is in [ownership and borrowing](ownership-and-borrowing.md#ownership-borrowing-and-resource-lifetimes); lock guards in [synchronization](synchronization.md).

## RAII Guards and Drop

Tie cleanup to a value's lifetime with `Drop` so callers cannot forget it. `Drop::drop` cannot return an error and cannot `.await`; when cleanup can fail or must be asynchronous, provide an explicit consuming method and keep `Drop` as the fallback.

```rust
use std::io::{self, Write};

#[must_use = "a Transaction that is dropped without commit() rolls back"]
pub struct Transaction<W: Write> {
    writer: W,
    committed: bool,
}

impl<W: Write> Transaction<W> {
    pub fn begin(mut writer: W) -> io::Result<Self> {
        writeln!(writer, "BEGIN")?;
        Ok(Self { writer, committed: false })
    }

    pub fn write(&mut self, statement: &str) -> io::Result<()> {
        writeln!(self.writer, "{statement}")
    }

    /// Fallible cleanup goes through an explicit method; errors reach the caller.
    pub fn commit(mut self) -> io::Result<()> {
        writeln!(self.writer, "COMMIT")?;
        self.committed = true;
        Ok(())
    }
}

impl<W: Write> Drop for Transaction<W> {
    fn drop(&mut self) {
        if !self.committed {
            // Drop cannot report failure. Log it or ignore it; never panic here, because a panic
            // during unwinding aborts the process.
            let _ = writeln!(self.writer, "ROLLBACK");
        }
    }
}
```

Drop cannot return an error. Provide an explicit fallible completion operation when callers need a result, and avoid unexpected blocking during destruction. `#[must_use]` on the guard type makes `Transaction::begin(w)?;` without a binding a warning. `mem::forget` and `ManuallyDrop` skip `Drop` without unsafety, so a guard cannot guarantee that cleanup runs; leaking is safe, it is just a bug.

## Drop Order Rules

- Local variables drop in reverse declaration order at the end of their block.
- Struct fields drop in declaration order; tuple elements in order; the active enum variant's fields in declaration order.
- Variables bound in one pattern drop in reverse order of declaration within the pattern.
- Temporaries drop at the end of the enclosing statement, except that edition 2024 drops `if let` scrutinee temporaries before the `else` branch and block tail-expression temporaries before the block's locals.
- `let _ = value;` drops immediately because `_` does not bind; `let _guard = value;` keeps it alive to the end of the scope.

```rust
struct Guard(&'static str);

impl Drop for Guard {
    fn drop(&mut self) {
        println!("drop {}", self.0);
    }
}

fn main() {
    let _first = Guard("first"); // dropped last
    let _second = Guard("second"); // dropped before `first`
    let _ = Guard("temporary"); // dropped right here
    println!("end of main");
}
// Output: drop temporary, end of main, drop second, drop first
```

Lock guards, spans, and timers depend on these rules; Clippy `let_underscore_lock` (correctness, deny) catches `let _ = mutex.lock()`.

## Common Mistakes

- Panicking in `Drop`; a panic while unwinding aborts the process.

## Availability by Version

| Version | Addition |
|---|---|
| 1.85 | Edition 2024 drop-order rules |
| 1.100 | `mem::DropGuard` |

Per-release details live in [the versions index](../versions/index.md).

## Practical Boundaries

Resource guards deserve deliberate scopes; fallible cleanup needs an explicit result-returning operation because Drop cannot return an error.
