---
name: jetbrains-vmoptions
description: Generates JetBrains IDE VM options based on IDE version. Supports version-specific GC selection (Generational ZGC for 243+, G1GC for 222-242) and memory configuration. Requires IDE version input from user.
---

# JetBrains IDE VM Options Generator

This agent generates optimized VM options for JetBrains IDEs based on the IDE version and user preferences.

## Required User Input

Before generating VM options, the following information is collected:

| Input | Required | Description |
|-------|----------|-------------|
| IDE version | **Yes** | Format: `IDE version: XXX` (e.g., 243, 242, 233) |
| GC option | No | User-specified garbage collector preference |
| Memory allocation | No | Heap size in GB (recommended: 4-8 GB) |

**Version 222 미만은 지원하지 않습니다.**

## Version-Based GC Selection

| Version Range | JDK | Default GC | Flags |
|---------------|-----|------------|-------|
| 243+ | 21 | Generational ZGC | `-XX:+UseZGC -XX:+ZGenerational` |
| 222-242 | 17 | G1GC | `-XX:+UseG1GC` |

## Available GC Options

### For Version 243+ (JDK 21)

| GC | Flags | Use Case |
|----|-------|----------|
| Generational ZGC | `-XX:+UseZGC -XX:+ZGenerational` | Low latency, large heaps (default) |
| ZGC (Legacy) | `-XX:+UseZGC` | Low latency, simpler configuration |
| G1GC | `-XX:+UseG1GC` | Balanced throughput/latency |
| Shenandoah | `-XX:+UseShenandoahGC` | Ultra-low pause times |
| Parallel GC | `-XX:+UseParallelGC` | Maximum throughput |
| Serial GC | `-XX:+UseSerialGC` | Single-threaded, small heaps |

### For Version 222-242 (JDK 17)

| GC | Flags | Use Case |
|----|-------|----------|
| G1GC | `-XX:+UseG1GC` | Balanced throughput/latency (default) |
| ZGC | `-XX:+UseZGC` | Low latency (non-generational) |
| Shenandoah | `-XX:+UseShenandoahGC` | Ultra-low pause times |
| Parallel GC | `-XX:+UseParallelGC` | Maximum throughput |
| Serial GC | `-XX:+UseSerialGC` | Single-threaded, small heaps |

## Memory Configuration

| Option | Description | Recommended |
|--------|-------------|-------------|
| `-Xms` | Initial heap size | 2g |
| `-Xmx` | Maximum heap size | 4g-8g |
| `-XX:ReservedCodeCacheSize` | Code cache size | 512m |
| `-XX:SoftRefLRUPolicyMSPerMB` | Soft reference policy | 50 |

## Platform-Independent Options

This skill generates **cross-platform** VM options only. Platform-specific flags are excluded:
- No OS-specific memory mappings
- No platform-dependent rendering options
- No architecture-specific optimizations

## Output Format

Generated options are provided in `.vmoptions` file format:
- One option per line
- Comments start with `#`
- Ready for direct use in `idea64.vmoptions`, `webstorm64.vmoptions`, etc.

## Reference Documents

| File | Content |
|------|---------|
| [gc-options.md](references/gc-options.md) | Detailed GC flags and tuning parameters |
| [memory-options.md](references/memory-options.md) | Memory management options |
| [common-options.md](references/common-options.md) | Commonly used performance flags |

## Example Output

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
