# Prerequisite Check Guide

This document defines the **mandatory input validation logic** before generating any vmoptions.

## Required Input

| Field | Required | Why |
|-------|----------|-----|
| **IDE version** | ✅ BLOCKING | Determines JDK version (17 vs 21), available GC options, and compatible flags |

## Optional Input

| Field | Why |
|-------|-----|
| **System RAM** | Heap size (`-Xmx`) recommendation |
| **CPU cores** | GC thread count (`-XX:ParallelGCThreads`, `-XX:ConcGCThreads`) tuning |
| **OS** | Platform-specific optimizations (e.g., large pages support) |
| **Primary goal** | Filter relevant options (latency vs throughput vs memory) |
| **GC preference** | Skip GC selection if user already decided |

### IDE Version Format Examples

- `IntelliJ IDEA 2024.1` → version 241.x → JDK 21
- `WebStorm 2023.3` → version 233.x → JDK 17
- `PyCharm 243.21565` → version 243.x → JDK 21

### Version to JDK Mapping

| IDE Version Range | Build Number | JDK |
|-------------------|--------------|-----|
| 2022.2 – 2024.2   | 222 – 242    | 17  |
| 2024.3+           | 243+         | 21  |

## Prompt Templates

### When IDE version is missing

```
I need your JetBrains IDE version to provide accurate vmoptions.

Please tell me:
- **IDE name and version** (e.g., IntelliJ IDEA 2024.1, WebStorm 2023.3)

This is required because different IDE versions use different JDK versions (17 vs 21), which affects available GC options and compatible flags.
```

### After collecting IDE version

```
Got it. [IDE version] uses JDK [17/21].

For better recommendations, you can also share:
- **System info** — RAM size, CPU cores, OS (macOS/Windows/Linux)
- **Primary goal** — e.g., reduce freezes, faster indexing, large project support
- **GC preference** — G1GC, ZGC, Generational ZGC, Shenandoah

Or I can use sensible defaults. What would you like?
```

## Validation Rules

1. **Never assume IDE version** — Always ask if not explicitly provided
2. **Never generate vmoptions without IDE version** — This is a blocking requirement
3. **Accept partial version info** — If user says "latest IntelliJ", ask for specific version number
4. **Version number is sufficient** — "243.21565" alone is enough to determine JDK version
