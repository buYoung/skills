---
name: jetbrains-vmoptions
description: Provides JetBrains IDE VM options knowledge for version-specific GC selection and memory/performance tuning (JDK 17/21, IDE 222+). Use this when composing `.vmoptions` as Markdown output for IDE tuning without platform-specific flags.
---

# JetBrains IDE VM Options Capabilities

Provides reference knowledge to compose `.vmoptions` sets for JetBrains IDEs.
Output format: Markdown with code blocks containing `.vmoptions` lines (no file generation).

## Scope

- IDE version ranges: 222-242 (JDK 17), 243+ (JDK 21)
- Cross-platform JVM options only (`.vmoptions`, one option per line, `#` comments)
- GC selection/tuning: Generational ZGC, ZGC, G1GC, Shenandoah, Parallel, Serial
- Memory/Code cache/Metaspace/Reference processing flags
- Compiler/runtime performance options commonly used for IDE tuning

## Reference Documents

| File | Content |
|------|---------|
| [gc-options.md](references/gc-options.md) | Detailed GC flags and tuning parameters |
| [memory-options.md](references/memory-options.md) | Memory management options |
| [common-options.md](references/common-options.md) | Commonly used performance flags |
