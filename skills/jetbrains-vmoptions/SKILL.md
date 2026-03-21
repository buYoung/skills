---
name: jetbrains-vmoptions
description: >
  Provides JetBrains IDE VM options knowledge for version-specific GC selection and memory/performance tuning
  (JDK 17/21, IDE 222+). Use this skill whenever the user mentions JetBrains IDE performance, vmoptions,
  .vmoptions files, IntelliJ/WebStorm/PyCharm/GoLand/Rider/CLion/PhpStorm/RubyMine/DataGrip tuning,
  IDE freezes or lag, heap size configuration, GC tuning for IDEs, or wants to optimize their JetBrains
  IDE startup or runtime performance — even if they don't explicitly mention "vmoptions".
---

# JetBrains IDE VM Options

Generate `.vmoptions` configurations for JetBrains IDEs. Output as Markdown code blocks (one option per line, `#` comments). Do not generate files directly.

## Workflow

### 1. Identify IDE version (blocking)

Read [prerequisite-check.md](references/prerequisite-check.md) for validation logic. IDE version determines the JDK (17 vs 21), which controls which GC collectors and flags are available. Never skip this step — wrong version means wrong recommendations.

### 2. Understand the user's goal

Match the user's problem to a tuning strategy:

| User says | Primary goal | Start with |
|-----------|-------------|------------|
| "freezes", "hangs", "lag", "UI stutter" | Low GC pause times | [gc-options.md](references/gc-options.md) → ZGC/Shenandoah |
| "slow indexing", "build is slow" | Throughput | [gc-options.md](references/gc-options.md) → G1GC/Parallel |
| "out of memory", "OOM", "large project" | Memory capacity | [memory-options.md](references/memory-options.md) → heap sizing |
| "startup is slow" | Fast startup | [common-options.md](references/common-options.md) → tiered compilation |
| "general tuning", "optimize" | Balanced | All references as needed |

### 3. Compose options from references

Read only the relevant reference files. Each reference includes flag descriptions, defaults, usage notes, and example configurations.

| File | Content | Read when |
|------|---------|-----------|
| [prerequisite-check.md](references/prerequisite-check.md) | IDE version validation, JDK mapping | Always (step 1) |
| [gc-options.md](references/gc-options.md) | GC selection and tuning flags | GC-related goals |
| [memory-options.md](references/memory-options.md) | Heap, code cache, metaspace, large pages | Memory-related goals |
| [common-options.md](references/common-options.md) | Compiler, strings, diagnostics, threads | Performance/startup goals |

### 4. Self-review before presenting

- Verify every flag is compatible with the user's JDK version
- Remove flags that conflict with each other (e.g., two different GC activations)
- Remove flags the user didn't ask about and doesn't need — lean configs are better
- Include a brief comment explaining each section's purpose

### 5. Present with context

Show the final `.vmoptions` block with:
- A header comment noting the IDE version and JDK
- Grouped sections (Memory, GC, Performance, Diagnostics)
- A short explanation of each non-obvious choice

## Scope

- **Supported**: IDE versions 222+ (JDK 17) and 243+ (JDK 21)
- **GC collectors**: Generational ZGC, ZGC, G1GC, Shenandoah, Parallel, Serial
- **Tuning areas**: Memory, code cache, metaspace, GC, compiler, strings, diagnostics
- **Not in scope**: OS-level tuning, plugin configuration, IDE settings (non-JVM), or IDE versions below 222

## Output Example

```
# JetBrains IDE VM Options
# IntelliJ IDEA 2024.3 (version 243, JDK 21)

# Memory
-Xms2g
-Xmx4g

# Garbage Collector: Generational ZGC
-XX:+UseZGC
-XX:+ZGenerational

# Performance
-XX:ReservedCodeCacheSize=512m
-XX:+UseStringDeduplication
-XX:SoftRefLRUPolicyMSPerMB=50

# Diagnostics
-XX:+HeapDumpOnOutOfMemoryError
-XX:CICompilerCount=2
```
