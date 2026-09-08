# Memory Options

Tune memory from observed pressure in the IDE process. Total system RAM or project size alone does not determine a safe heap value.

## Read the effective state first

Collect the active command line and initialized flags:

```
jcmd <pid> VM.command_line
jcmd <pid> VM.flags -all
jcmd <pid> GC.heap_info
jcmd <pid> Compiler.codecache
jcmd <pid> VM.metaspace basic
```

When native memory is part of the question, `VM.native_memory` is useful only if Native Memory Tracking was enabled when the JVM started. Enabling it changes the measurement setup and must be identical in A and B.

Classify each reported value as a source declaration, runtime-selected value, or IDE bundle/custom value. Values such as heap size, code cache, and thread stacks can be adjusted by runtime ergonomics or product launch options; do not quote a source initializer as the final process value.

When explaining a declaration, link the file from the exact source revision that matches the user's runtime. The [JBR 25.0.4 `globals.hpp` at inspected revision `4af5e119...`](https://github.com/JetBrains/JetBrainsRuntime/blob/4af5e1194b7f34a396bd56f25eef17624eb60400/src/hotspot/share/runtime/globals.hpp) is an evidence example only; do not reuse its declarations for a different JBR build.

## Heap sizing

Relevant options include `-Xmx`, `-Xms`, and their long-form equivalents. Keep one semantic definition for each boundary.

### Increase `-Xmx` only with evidence

Evidence may include:

- an IDE low-memory warning or Java heap OOM;
- repeatedly high post-GC occupancy with little free headroom;
- frequent collection caused by capacity pressure;
- a workload that demonstrably needs more live heap.

Before increasing it, confirm that the IDE process is the constrained process and the operating system has memory headroom. A larger heap can reduce collection frequency, but it increases committed/resident memory potential, can increase memory pressure or swapping, and may lengthen some collection work. It does not fix a memory leak or excessive allocation rate.

Choose the candidate from the measured live set and available system memory, then compare it. Do not use fixed `4g`, `8g`, or RAM-percentage tables as universal recommendations.

### Treat `-Xms` separately

Preserve the IDE's existing `-Xms` unless startup allocation behavior provides a reason to change it. Setting `-Xms` equal to a large `-Xmx` can reserve or commit more memory early and worsen startup or system pressure. It is not a general performance optimization.

### Avoid duplicate heap forms

Normalize duplicates such as:

```
-Xmx<size-a>
-XX:MaxHeapSize=<size-b-in-bytes>
```

Do not emit both. Use `VM.command_line` and `VM.flags -all` to explain which value became effective, then keep the conventional project/product form already in use.

## Code cache

`-XX:ReservedCodeCacheSize=<size>` is relevant when `Compiler.codecache` or IDE diagnostics show the code cache approaching exhaustion, code cache flushing, or compilation being disabled. A larger cache consumes additional address space/native memory and does not improve performance when the cache has adequate headroom.

Do not recommend `256m`, `512m`, or `1g` solely from project size. Preserve the IDE-bundled value unless observed occupancy supports a change. Verify the final size and usage after restart.

## Metaspace and compressed class space

Inspect `VM.metaspace basic` and OOM/error evidence before changing:

- `-XX:MetaspaceSize` is a collection threshold input, not a simple amount of preallocated class memory.
- `-XX:MaxMetaspaceSize` imposes a cap. Adding an arbitrary cap can create `OutOfMemoryError: Metaspace` without reducing the underlying class-loader or plugin growth.
- `-XX:CompressedClassSpaceSize` is relevant only to measured compressed-class-space pressure and supported configurations.

Do not add fixed metaspace limits as a generic large-project configuration. Investigate class-loader/plugin growth when usage keeps increasing.

## Soft references and reference processing

`-XX:SoftRefLRUPolicyMSPerMB=<ms>` changes how long soft references tend to survive relative to free heap. Lower values can release cache contents earlier but increase recomputation, allocation, disk access, and GC churn. Do not prescribe an aggressive value without evidence that soft-reference retention is causing pressure.

`-XX:+ParallelRefProcEnabled` is useful only when reference-processing phases materially contribute to measured pauses and the exact collector/runtime supports the behavior. Verify whether it is already enabled ergonomically.

## Pre-touch, large pages, and NUMA

These are platform and workload options, not routine IDE tuning:

| Option area | Consider only when | Cost or risk |
|---|---|---|
| `-XX:+AlwaysPreTouch` | Runtime page faults are measured and predictable warm-state latency matters | Slower startup and earlier physical-memory commitment, especially with large `-Xms` |
| Large pages | The OS is explicitly configured, the exact JBR supports them, and measurement shows a benefit | Startup/allocation failure modes, locked/reserved memory, operational setup |
| NUMA controls | A multi-socket system shows locality problems | Can worsen placement; behavior is collector and platform dependent |

Do not recommend large pages on macOS. On Linux and Windows, confirm OS setup and actual activation, not just option acceptance.

## Memory diagnostics

For heap OOM analysis, a bounded recommendation can include:

```
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=<existing-writable-directory>
```

Warn that heap dumps may contain source code, credentials, paths, and user data, and can require substantial disk space. A heap dump is diagnostic evidence, not a performance optimization.

JetBrains provides an IDE action for changing maximum heap and warns when post-GC free heap is very low. Prefer the product action when only `-Xmx` needs adjustment, and still confirm the effective value after restart:

- [JetBrains: Increase the memory heap of the IDE](https://www.jetbrains.com/help/idea/increasing-memory-heap.html)
- [JetBrains: Advanced configuration and custom VM options](https://www.jetbrains.com/help/idea/tuning-the-ide.html)

## Recommendation format

For every memory change, state:

1. the measured condition;
2. the existing effective value and its origin;
3. the candidate value or removal;
4. expected benefit and memory/startup/GC cost;
5. the post-restart command that confirms propagation;
6. the rollback line;
7. the metric used in the A/B procedure from [performance-validation.md](performance-validation.md).
