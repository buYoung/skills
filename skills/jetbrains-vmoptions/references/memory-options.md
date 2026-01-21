# Memory Options Reference

Memory-related VM options for JetBrains IDEs.

## Table of Contents

1. [Heap Memory](#heap-memory)
2. [Code Cache](#code-cache)
3. [Metaspace](#metaspace)
4. [Reference Processing](#reference-processing)
5. [Memory Pre-touch](#memory-pre-touch)
6. [Large Pages](#large-pages)
7. [NUMA Support](#numa-support)
8. [Container Environment](#container-environment)

---

## Heap Memory

Behavior: Controls Java heap size boundaries; larger heaps reduce GC frequency but increase memory footprint.
When it helps: Large projects, heavy indexing, or frequent analysis workloads.

### Core Flags

| Flag | Description | Typical |
|------|-------------|-------------|
| `-Xms<size>` | Initial heap size | 2g |
| `-Xmx<size>` | Maximum heap size | 4g-8g |
| `-XX:MinHeapSize=<size>` | Minimum heap size | 0 (ergonomic) |
| `-XX:InitialHeapSize=<size>` | Initial heap size (alternative) | - |
| `-XX:MaxHeapSize=<size>` | Maximum heap size (alternative) | - |
| `-XX:SoftMaxHeapSize=<size>` | Soft limit for max heap | - |

Usage Notes:
- `-Xms<size>`: Higher values reduce ramp-up GC but increase startup memory footprint.
- `-Xmx<size>`: Upper bound for heap growth; set based on available RAM and project size.
- `-XX:MinHeapSize=<size>`: Controls minimum committed heap in ergonomic mode.
- `-XX:InitialHeapSize=<size>` / `-XX:MaxHeapSize=<size>`: Alternative forms of `-Xms`/`-Xmx`.
- `-XX:SoftMaxHeapSize=<size>`: Limits growth under normal pressure while allowing bursts.

### Heap Size Ranges by RAM

| RAM | Typical -Xmx | Use Case |
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

Behavior: Stores compiled methods; larger cache reduces deoptimization and recompilation.
When it helps: Large codebases, heavy refactoring, and long IDE sessions.

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:ReservedCodeCacheSize=<size>` | base = platform default (C1: 32M, C2: 48M); if TieredCompilation and flag default -> min(2G, base * 5); if JVMCI native lib disabled -> max(64M, value) | Maximum code cache size |
| `-XX:InitialCodeCacheSize=<size>` | 2496K | Initial code cache size |
| `-XX:CodeCacheExpansionSize=<size>` | 64K | Expansion increment |

Usage Notes:
- `-XX:ReservedCodeCacheSize=<size>`: Increase when seeing code cache full or frequent deoptimizations.
- `-XX:InitialCodeCacheSize=<size>`: Helps reduce early expansions during startup bursts.
- `-XX:CodeCacheExpansionSize=<size>`: Larger increments reduce expansion frequency at the cost of memory jumps.

### Typical Values

| Project Size | ReservedCodeCacheSize |
|--------------|----------------------|
| Small | 256m |
| Medium | 512m |
| Large | 1g |

### Example Configuration

```
-XX:ReservedCodeCacheSize=512m
-XX:+UseCodeCacheFlushing
```

---

## Metaspace

Class metadata storage (replaced PermGen in JDK 8+).

Behavior: Holds class metadata; limits guard against runaway class loading.
When it helps: Projects with many modules/plugins or heavy code generation.

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:MetaspaceSize=<size>` | LP64: 21M; 32-bit: 16M | Initial metaspace size |
| `-XX:MaxMetaspaceSize=<size>` | unlimited | Maximum metaspace size |
| `-XX:CompressedClassSpaceSize=<size>` | 1G | Compressed class space |

Usage Notes:
- `-XX:MetaspaceSize=<size>`: Higher values reduce early metadata GCs.
- `-XX:MaxMetaspaceSize=<size>`: Cap when runaway class loading is suspected.
- `-XX:CompressedClassSpaceSize=<size>`: Adjust when class space pressure is high.

### Example Values

```
-XX:MetaspaceSize=512m
-XX:MaxMetaspaceSize=1g
```

---

## Reference Processing

Soft/Weak reference handling.

Behavior: Controls how aggressively soft references are cleared under memory pressure.
When it helps: Balancing memory footprint vs cache hit rate.

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:SoftRefLRUPolicyMSPerMB=<ms>` | 1000 | Soft reference retention (ms per MB of free heap) |
| `-XX:+ParallelRefProcEnabled` | false | Parallel reference processing |

Usage Notes:
- `-XX:SoftRefLRUPolicyMSPerMB=<ms>`: Lower values free caches sooner under memory pressure.
- `-XX:+ParallelRefProcEnabled`: Helps when reference processing time dominates pauses.

### Example Configuration

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

Behavior: Touches memory pages at startup to reduce runtime page faults.
When it helps: Large heaps where consistent latency is more important than startup time.

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:+AlwaysPreTouch` | false | Pre-touch all committed pages |
| `-XX:+AlwaysPreTouchStacks` | false | Pre-touch thread stacks |

Usage Notes:
- `-XX:+AlwaysPreTouch`: Reduces runtime page faults on large heaps.
- `-XX:+AlwaysPreTouchStacks`: Stabilizes thread stack latency for many threads.

### Behavior / Trade-offs

| Setting | Startup Time | Runtime Performance |
|---------|--------------|---------------------|
| Off (default) | Faster | Variable latency |
| On | Slower | More predictable |

### Behavior / When it helps

- Large heap sizes (8GB+)
- Latency-sensitive workflows
- Systems with sufficient RAM

```
-XX:+AlwaysPreTouch
```

---

## Large Pages

Using large pages reduces TLB misses.

Behavior: Uses large pages to reduce TLB misses and improve memory throughput.
When it helps: Very large heaps on OSes with huge page support enabled.

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:+UseLargePages` | false | Enable large page memory |
| `-XX:LargePageSizeInBytes=<size>` | 0 | Large page size (0 = OS default) |
| `-XX:+UseLargePagesIndividualAllocation` | false | Allocate large pages individually |

Usage Notes:
- `-XX:+UseLargePages`: Helps when OS huge pages are configured and heaps are large.
- `-XX:LargePageSizeInBytes=<size>`: Overrides OS default huge page size.
- `-XX:+UseLargePagesIndividualAllocation`: Useful when full reservation fails.

### Platform Requirements

| OS | Requirement |
|----|-------------|
| Linux | `vm.nr_hugepages` kernel parameter |
| Windows | "Lock pages in memory" privilege |
| macOS | Not supported |

### Example Configuration

```
-XX:+UseLargePages
-XX:LargePageSizeInBytes=2m
```

---

## NUMA Support

Non-Uniform Memory Access optimization.

Behavior: Improves allocation locality on multi-socket systems.
When it helps: Multi-socket machines with large heaps and memory-intensive workloads.

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:+UseNUMA` | false | Enable NUMA-aware allocation |
| `-XX:+UseNUMAInterleaving` | false | Interleave memory across NUMA nodes |
| `-XX:NUMAInterleaveGranularity=<size>` | 2m | Interleaving granularity (Windows) |

Usage Notes:
- `-XX:+UseNUMA`: Helps on multi-socket systems with large heaps.
- `-XX:+UseNUMAInterleaving`: Balances memory across NUMA nodes to avoid hotspots.
- `-XX:NUMAInterleaveGranularity=<size>`: Controls interleaving chunk size.

### Behavior / When it helps

- Multi-socket server systems
- Large heap sizes (16GB+)
- Memory-intensive workloads

### Example Configuration

```
-XX:+UseNUMA
-XX:+UseNUMAInterleaving
```

---

## Container Environment

Memory options for container/cloud environments.

Behavior: Binds heap sizing to detected container limits and CPU count.
When it helps: Running IDEs inside containers or constrained VMs.

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:MaxRAMPercentage=<percent>` | 25.0 | Max heap as percentage of available RAM |
| `-XX:MinRAMPercentage=<percent>` | 50.0 | Min heap percentage for small memory systems |
| `-XX:InitialRAMPercentage=<percent>` | 1.5625 | Initial heap as percentage of RAM |
| `-XX:ActiveProcessorCount=<n>` | -1 | Override detected CPU count (-1 = auto) |

Usage Notes:
- `-XX:MaxRAMPercentage=<percent>`: Caps heap size inside containers with limited memory.
- `-XX:MinRAMPercentage=<percent>`: Avoids tiny heaps on small containers.
- `-XX:InitialRAMPercentage=<percent>`: Speeds warmup by setting a larger initial heap.
- `-XX:ActiveProcessorCount=<n>`: Stabilizes thread heuristics in constrained CPU environments.

### Container Configuration Example

```
-XX:MaxRAMPercentage=75.0
-XX:InitialRAMPercentage=50.0
-XX:+UseContainerSupport
```

### Deprecated Flags (Use Percentage Instead)

| Deprecated | Replacement |
|------------|-------------|
| `-XX:MaxRAMFraction` | `-XX:MaxRAMPercentage` |
| `-XX:MinRAMFraction` | `-XX:MinRAMPercentage` |
| `-XX:InitialRAMFraction` | `-XX:InitialRAMPercentage` |

Usage Notes:
- Fraction-based flags map to percentage-based flags for modern JVMs.

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
