# Common Options Reference

Performance-focused VM options commonly used in JetBrains IDEs.

## Table of Contents

1. [Compiler Options](#compiler-options)
2. [String Optimization](#string-optimization)
3. [Diagnostics](#diagnostics)
4. [Tiered Compilation](#tiered-compilation)
5. [Thread Options](#thread-options)
6. [Example Configurations](#example-configurations)
7. [Example Output (Markdown)](#example-output-markdown)

---

## Compiler Options

JIT compiler-related options.

Behavior: Controls compilation concurrency and thresholds.
When it helps: Balancing startup responsiveness vs peak throughput.

### Core Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:CICompilerCount=<n>` | LP64 ergo (default when CICompilerCountPerCPU=true): max(log2(n) * log2(max(log2(n), 1)) * 3 / 2, 2), capped by code cache buffers; 32-bit default: 3 | Number of compiler threads |
| `-XX:CompileThreshold=<n>` | 10000 | Invocations before compilation |
| `-XX:+BackgroundCompilation` | true | Compile in background |
| `-XX:+UseCompilerSafepoints` | true | Use safepoints in compiled code |

Notes: `n` is `os::active_processor_count()` and `log2` is integer log2.

Usage Notes:
- `-XX:CICompilerCount`: Helps when compilation queues grow or CPU contention affects UI responsiveness.
- `-XX:CompileThreshold`: Lower values front-load compilation for faster warmup; higher values favor interpreted execution.
- `-XX:+BackgroundCompilation`: Reduces foreground stalls by compiling off the main path.
- `-XX:+UseCompilerSafepoints`: Improves safepoint responsiveness during long-running compiled code.

### Example Configuration

```
-XX:CICompilerCount=2
```

Typical scaling by CPU cores:
- 4 cores: `CICompilerCount=2`
- 8+ cores: `CICompilerCount=3-4`

---

## String Optimization

String processing optimizations.

Behavior: Reduces duplicate String storage and optimizes concatenation.
When it helps: Large projects with heavy String churn or memory pressure.

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:+UseStringDeduplication` | false | Deduplicate String objects (G1GC, ZGC) |
| `-XX:+OptimizeStringConcat` | true | Optimize string concatenation |
| `-XX:+CompactStrings` | true | Use compact strings (Latin-1) |

Usage Notes:
- `-XX:+UseStringDeduplication`: Helps when many duplicate Strings inflate heap usage (G1GC/ZGC only).
- `-XX:+OptimizeStringConcat`: Reduces temporary allocations in heavy concatenation paths.
- `-XX:+CompactStrings`: Saves memory when most Strings are Latin-1.

### Example Configuration

```
-XX:+UseStringDeduplication
-XX:+OptimizeStringConcat
-XX:+CompactStrings
```

**Note**: `UseStringDeduplication` requires G1GC or ZGC.

---

## Diagnostics

Diagnostics and debugging options.

Behavior: Emits logs and dumps to help analyze crashes and GC behavior.
When it helps: Investigating OOMs, GC pauses, or JVM crashes.

### Heap Dump

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:+HeapDumpOnOutOfMemoryError` | false | Dump heap on OOM |
| `-XX:HeapDumpPath=<path>` | working dir | Heap dump location |

Usage Notes:
- `-XX:+HeapDumpOnOutOfMemoryError`: Captures heap state for post-mortem analysis.
- `-XX:HeapDumpPath=<path>`: Use a writable location with sufficient disk space.

### GC Logging (JDK 9+ Unified Logging)

| Flag | Description |
|------|-------------|
| `-Xlog:gc` | Basic GC logging |
| `-Xlog:gc*` | Detailed GC logging |
| `-Xlog:gc*:file=gc.log` | Log to file |
| `-Xlog:gc*:file=gc.log:time,uptime` | With timestamps |
| `-Xlog:gc*:file=gc.log:time,uptime:filecount=5,filesize=10m` | Rotating logs |

Usage Notes:
- `-Xlog:gc`: Basic GC health signal during tuning.
- `-Xlog:gc*`: Adds detailed event fields for deeper analysis.
- `-Xlog:gc*:file=gc.log`: Redirects logs to a file for later review.
- `-Xlog:gc*:file=gc.log:time,uptime`: Adds time context for correlating with UI pauses.
- `-Xlog:gc*:file=gc.log:time,uptime:filecount=5,filesize=10m`: Limits disk usage with rotation.

### GC Logging Patterns

| Pattern | Description |
|---------|-------------|
| `-Xlog:gc` | GC events only |
| `-Xlog:gc+heap=debug` | GC + heap details |
| `-Xlog:gc+phases=debug` | GC phase timings |
| `-Xlog:gc*=debug:file=gc.log` | All GC debug info to file |
| `-Xlog:gc+age=trace` | Object age distribution |

Usage Notes:
- `-Xlog:gc`: Lightweight overview when looking for long pauses.
- `-Xlog:gc+heap=debug`: Helps diagnose heap sizing and promotion behavior.
- `-Xlog:gc+phases=debug`: Breaks down phase timings to spot bottlenecks.
- `-Xlog:gc*=debug:file=gc.log`: Captures full detail for offline analysis.
- `-Xlog:gc+age=trace`: Useful when tuning tenuring behavior.

### System.gc() Behavior

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:+ExplicitGCInvokesConcurrent` | false | System.gc() triggers concurrent GC |
| `-XX:+DisableExplicitGC` | false | Ignore System.gc() calls |

Usage Notes:
- `-XX:+ExplicitGCInvokesConcurrent`: Reduces stop-the-world impact of explicit GCs.
- `-XX:+DisableExplicitGC`: Helps when libraries trigger costly explicit GCs.

### Error Handling

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:ErrorFile=<path>` | `hs_err_pid%p.log` in current working directory (unless ErrorFileToStdout/ErrorFileToStderr) | Error log location |
| `-XX:+ShowMessageBoxOnError` | false | Show dialog on crash |

Usage Notes:
- `-XX:ErrorFile=<path>`: Redirects crash logs to a known location for collection.
- `-XX:+ShowMessageBoxOnError`: Useful for interactive debugging on desktop setups.

### Example Configuration

```
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=${user.home}/jetbrains_heap_dump.hprof
```

---

## Tiered Compilation

Tiered compilation settings.

Behavior: Trades startup speed for peak performance via tiered JIT levels.
When it helps: Choosing faster startup vs sustained throughput.

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:+TieredCompilation` | true | Enable tiered compilation |
| `-XX:TieredStopAtLevel=<n>` | 4 | Max compilation level (1-4) |

Usage Notes:
- `-XX:+TieredCompilation`: Balances startup and peak performance with multi-level JIT.
- `-XX:TieredStopAtLevel=<n>`: Lower levels favor faster startup; level 4 maximizes optimization.

### Compilation Levels

| Level | Description |
|-------|-------------|
| 0 | Interpreter |
| 1 | C1 without profiling |
| 2 | C1 with limited profiling |
| 3 | C1 with full profiling |
| 4 | C2 (full optimization) |

### Example: Fast Startup (less optimization)

```
-XX:TieredStopAtLevel=1
```

### Example: Full Optimization (default behavior)

```
-XX:+TieredCompilation
-XX:TieredStopAtLevel=4
```

---

## Thread Options

Thread-related options.

Behavior: Controls thread stack size and GC thread counts.
When it helps: Deep recursion, constrained memory, or GC thread tuning.

### Stack Size

| Flag | Default | Description |
|------|---------|-------------|
| `-Xss<size>` | Platform constant in `globals_<os>_<arch>.hpp` (KB); 0 means OS default (e.g., linux_x86_64=1024, bsd_x86_64=1024, linux_aarch64=2040, windows_*=0) | Thread stack size |
| `-XX:ThreadStackSize=<size>` | Platform constant in `globals_<os>_<arch>.hpp` (KB); 0 means OS default (e.g., linux_x86_64=1024, bsd_x86_64=1024, linux_aarch64=2040, windows_*=0) | Thread stack size (KB) |

Usage Notes:
- `-Xss<size>` / `-XX:ThreadStackSize=<size>`: Increase for deep recursion; reduce for many threads under memory pressure.

### Typical Values

| Use Case | Stack Size |
|----------|------------|
| Default | 1m |
| Deep recursion | 2m |
| Memory-constrained | 512k |

### Thread Pool

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:ParallelGCThreads=<n>` | auto | Parallel GC thread count |
| `-XX:ConcGCThreads=<n>` | auto | Concurrent GC thread count |

Usage Notes:
- `-XX:ParallelGCThreads=<n>`: Tune when GC phases over- or under-utilize CPU.
- `-XX:ConcGCThreads=<n>`: Adjust when concurrent phases impact UI responsiveness.

---

## Example Configurations

### Example: Standard IDE Setup

```
# Compiler
-XX:CICompilerCount=2

# String Optimization
-XX:+UseStringDeduplication
-XX:+OptimizeStringConcat
-XX:+CompactStrings

# Diagnostics
-XX:+HeapDumpOnOutOfMemoryError

# Tiered Compilation
-XX:+TieredCompilation
```

### Example: Performance-Focused

```
# Compiler
-XX:CICompilerCount=4

# String Optimization
-XX:+UseStringDeduplication
-XX:+OptimizeStringConcat
-XX:+CompactStrings

# Aggressive Compilation
-XX:+TieredCompilation
-XX:CompileThreshold=5000

# Pre-touch for predictable performance
-XX:+AlwaysPreTouch

# Diagnostics
-XX:+HeapDumpOnOutOfMemoryError
```

### Example: Minimal/Fast Startup

```
# Reduced compiler threads
-XX:CICompilerCount=1

# Stop at C1 level
-XX:TieredStopAtLevel=1

# Smaller stack
-Xss512k
```

---

## Example Output (Markdown)

Behavior: Outputs a Markdown snippet that includes `.vmoptions` lines in a code block.
When it helps: Sharing a ready-to-use baseline without generating files.

### Version 243+ with Generational ZGC (4GB)

```
# JetBrains IDE VM Options
# Generated for version 243+ (JDK 21)

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

# Miscellaneous
-XX:+HeapDumpOnOutOfMemoryError
-XX:CICompilerCount=2
```

### Version 242 with G1GC (6GB)

```
# JetBrains IDE VM Options
# Generated for version 222-242 (JDK 17)

# Memory
-Xms2g
-Xmx6g

# Garbage Collector: G1GC
-XX:+UseG1GC
-XX:MaxGCPauseMillis=200

# Performance
-XX:ReservedCodeCacheSize=512m
-XX:+UseStringDeduplication
-XX:SoftRefLRUPolicyMSPerMB=50

# Miscellaneous
-XX:+HeapDumpOnOutOfMemoryError
-XX:CICompilerCount=2
```
