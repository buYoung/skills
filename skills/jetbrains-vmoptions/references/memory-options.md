# Memory Options Reference

JetBrains IDE 메모리 관련 VM 옵션.

## Table of Contents

1. [Heap Memory](#heap-memory)
2. [Code Cache](#code-cache)
3. [Metaspace](#metaspace)
4. [Reference Processing](#reference-processing)
5. [Memory Pre-touch](#memory-pre-touch)

---

## Heap Memory

### Core Flags

| Flag | Description | Recommended |
|------|-------------|-------------|
| `-Xms<size>` | Initial heap size | 2g |
| `-Xmx<size>` | Maximum heap size | 4g-8g |
| `-XX:MinHeapSize=<size>` | Minimum heap size | 0 (ergonomic) |
| `-XX:InitialHeapSize=<size>` | Initial heap size (alternative) | - |
| `-XX:MaxHeapSize=<size>` | Maximum heap size (alternative) | - |
| `-XX:SoftMaxHeapSize=<size>` | Soft limit for max heap | - |

### Heap Size Guidelines

| RAM | Recommended -Xmx | Use Case |
|-----|------------------|----------|
| 8GB | 2g-4g | Light development |
| 16GB | 4g-6g | Standard development |
| 32GB+ | 6g-8g | Large projects, monorepos |

### Size Notation

| Suffix | Meaning | Example |
|--------|---------|---------|
| `k` / `K` | Kilobytes | `512k` |
| `m` / `M` | Megabytes | `512m` |
| `g` / `G` | Gigabytes | `4g` |

---

## Code Cache

JIT compiled code storage.

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:ReservedCodeCacheSize=<size>` | varies | Maximum code cache size |
| `-XX:InitialCodeCacheSize=<size>` | 2496K | Initial code cache size |
| `-XX:CodeCacheExpansionSize=<size>` | 64K | Expansion increment |

### Recommended Values

| Project Size | ReservedCodeCacheSize |
|--------------|----------------------|
| Small | 256m |
| Medium | 512m |
| Large | 1g |

### IDE Configuration

```
-XX:ReservedCodeCacheSize=512m
-XX:+UseCodeCacheFlushing
```

---

## Metaspace

Class metadata storage (replaced PermGen in JDK 8+).

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:MetaspaceSize=<size>` | varies | Initial metaspace size |
| `-XX:MaxMetaspaceSize=<size>` | unlimited | Maximum metaspace size |
| `-XX:CompressedClassSpaceSize=<size>` | 1G | Compressed class space |

### Recommended Values

```
-XX:MetaspaceSize=512m
-XX:MaxMetaspaceSize=1g
```

---

## Reference Processing

Soft/Weak reference handling.

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:SoftRefLRUPolicyMSPerMB=<ms>` | 1000 | Soft reference retention (ms per MB of free heap) |
| `-XX:+ParallelRefProcEnabled` | false | Parallel reference processing |

### IDE Configuration

Lower values = more aggressive soft reference clearing = reduced memory usage.

```
# Aggressive (less memory, more GC)
-XX:SoftRefLRUPolicyMSPerMB=50

# Conservative (more memory, less GC)
-XX:SoftRefLRUPolicyMSPerMB=250
```

---

## Memory Pre-touch

Commit pages at startup for more predictable performance.

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:+AlwaysPreTouch` | false | Pre-touch all committed pages |
| `-XX:+AlwaysPreTouchStacks` | false | Pre-touch thread stacks |

### Trade-offs

| Setting | Startup Time | Runtime Performance |
|---------|--------------|---------------------|
| Off (default) | Faster | Variable latency |
| On | Slower | More predictable |

### When to Enable

- Large heap sizes (8GB+)
- Latency-sensitive workflows
- Systems with sufficient RAM

```
-XX:+AlwaysPreTouch
```

---

## Complete Memory Configuration Examples

### Standard (4GB Heap)

```
-Xms2g
-Xmx4g
-XX:ReservedCodeCacheSize=512m
-XX:SoftRefLRUPolicyMSPerMB=50
```

### Large Project (8GB Heap)

```
-Xms4g
-Xmx8g
-XX:ReservedCodeCacheSize=1g
-XX:MetaspaceSize=512m
-XX:MaxMetaspaceSize=1g
-XX:SoftRefLRUPolicyMSPerMB=50
-XX:+AlwaysPreTouch
```

### Memory-Constrained (2GB Heap)

```
-Xms1g
-Xmx2g
-XX:ReservedCodeCacheSize=256m
-XX:SoftRefLRUPolicyMSPerMB=25
```
