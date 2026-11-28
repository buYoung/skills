# Compile Times

## Contents

- [Compile Times](#compile-times)
- [Availability by Version](#availability-by-version)

Examples use stable APIs unless marked otherwise; see [compatibility](../../SKILL.md#compatibility). Runtime costs are in [performance optimization](performance-optimization.md); the build cost of splitting crates is in [modules and crate boundaries](modules-and-crate-boundaries.md#build-and-runtime-costs).

## Compile Times

- `cargo build --timings` renders a chart of crate compilation; crates on the critical path that block others are the ones to split or slim.
- `cargo llvm-lines` (crate) lists which functions generate the most LLVM IR; generic functions instantiated many times dominate. Move the non-generic body into an inner function:

```rust
use std::path::Path;

pub fn read_config(path: impl AsRef<Path>) -> std::io::Result<String> {
    // The generic shell is tiny and instantiated per caller type; the body compiles once.
    fn inner(path: &Path) -> std::io::Result<String> {
        std::fs::read_to_string(path)
    }
    inner(path.as_ref())
}
```

- Replace heavily instantiated generic helpers (`Option::map` with distinct closure types in a macro) with `match` where a macro expands thousands of times; `cargo expand` shows the generated code and `-Zmacro-stats` (nightly) counts it.
- Profile settings that cut compile time (`debug = false` or `"line-tables-only"` in dev, `codegen-units`, faster linkers, `build.build-dir`) are in [build configuration](build-configuration.md#faster-development-builds).
- `cargo check` for the edit loop; a full build only when running.

## Availability by Version

| Version | Addition |
|---|---|
| 1.90 | `lld` default linker on `x86_64-unknown-linux-gnu` (faster links) |

Per-release details live in [the versions index](../versions/index.md).
