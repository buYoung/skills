# Common Options Reference

JetBrains IDE에서 자주 사용되는 성능 관련 VM 옵션.

## Table of Contents

1. [Compiler Options](#compiler-options)
2. [String Optimization](#string-optimization)
3. [Diagnostics](#diagnostics)
4. [Tiered Compilation](#tiered-compilation)
5. [Thread Options](#thread-options)

---

## Compiler Options

JIT 컴파일러 관련 옵션.

### Core Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:CICompilerCount=<n>` | varies | Number of compiler threads |
| `-XX:CompileThreshold=<n>` | 10000 | Invocations before compilation |
| `-XX:+BackgroundCompilation` | true | Compile in background |
| `-XX:+UseCompilerSafepoints` | true | Use safepoints in compiled code |

### IDE Recommended

```
-XX:CICompilerCount=2
```

Adjust based on CPU cores:
- 4 cores: `CICompilerCount=2`
- 8+ cores: `CICompilerCount=3-4`

---

## String Optimization

문자열 처리 최적화.

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:+UseStringDeduplication` | false | Deduplicate String objects (G1GC, ZGC) |
| `-XX:+OptimizeStringConcat` | true | Optimize string concatenation |
| `-XX:+CompactStrings` | true | Use compact strings (Latin-1) |

### IDE Configuration

```
-XX:+UseStringDeduplication
-XX:+OptimizeStringConcat
-XX:+CompactStrings
```

**Note**: `UseStringDeduplication` requires G1GC or ZGC.

---

## Diagnostics

문제 진단 및 디버깅 옵션.

### Heap Dump

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:+HeapDumpOnOutOfMemoryError` | false | Dump heap on OOM |
| `-XX:HeapDumpPath=<path>` | working dir | Heap dump location |

### GC Logging

| Flag | Description |
|------|-------------|
| `-Xlog:gc*` | Basic GC logging (JDK 9+) |
| `-Xlog:gc*:file=gc.log` | Log to file |
| `-Xlog:gc*:file=gc.log:time,uptime` | With timestamps |

### Error Handling

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:ErrorFile=<path>` | varies | Error log location |
| `-XX:+ShowMessageBoxOnError` | false | Show dialog on crash |

### IDE Recommended

```
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=${user.home}/jetbrains_heap_dump.hprof
```

---

## Tiered Compilation

단계별 컴파일 설정.

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:+TieredCompilation` | true | Enable tiered compilation |
| `-XX:TieredStopAtLevel=<n>` | 4 | Max compilation level (1-4) |

### Compilation Levels

| Level | Description |
|-------|-------------|
| 0 | Interpreter |
| 1 | C1 without profiling |
| 2 | C1 with limited profiling |
| 3 | C1 with full profiling |
| 4 | C2 (full optimization) |

### Fast Startup (Trade-off: Less optimization)

```
-XX:TieredStopAtLevel=1
```

### Maximum Performance (Default)

```
-XX:+TieredCompilation
-XX:TieredStopAtLevel=4
```

---

## Thread Options

스레드 관련 옵션.

### Stack Size

| Flag | Default | Description |
|------|---------|-------------|
| `-Xss<size>` | varies | Thread stack size |
| `-XX:ThreadStackSize=<size>` | varies | Thread stack size (KB) |

### Recommended Values

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

---

## Complete Common Configuration

### Standard IDE Setup

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

### Performance-Focused

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

### Minimal/Fast Startup

```
# Reduced compiler threads
-XX:CICompilerCount=1

# Stop at C1 level
-XX:TieredStopAtLevel=1

# Smaller stack
-Xss512k
```
