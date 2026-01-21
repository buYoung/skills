# GC Options Reference

Detailed garbage collector flags for JetBrains IDE VM options.

## Table of Contents

1. [Generational ZGC (JDK 21+)](#generational-zgc-jdk-21)
2. [ZGC Common Flags](#zgc-common-flags)
3. [G1GC Flags](#g1gc-flags)
4. [Shenandoah Flags](#shenandoah-flags)
5. [Parallel GC Flags](#parallel-gc-flags)

---

## Generational ZGC (JDK 21+)

Version 243 이상에서 사용 가능. JDK 21의 기본 권장 GC.

### Activation

```
-XX:+UseZGC
-XX:+ZGenerational
```

### Tuning Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:ZYoungCompactionLimit` | 25.0 | Maximum allowed garbage in young pages (%) |
| `-XX:ZCollectionIntervalMinor` | -1 | Force Minor GC interval (seconds), -1 = disabled |
| `-XX:ZCollectionIntervalMajor` | -1 | Force Major GC interval (seconds), -1 = disabled |
| `-XX:ZAllocationSpikeTolerance` | 2.0 | Allocation spike tolerance factor |
| `-XX:ZFragmentationLimit` | 5.0 | Maximum allowed heap fragmentation (%) |
| `-XX:ZMarkStackSpaceLimit` | 8G | Maximum bytes for mark stacks |
| `-XX:ZUncommitDelay` | 300 | Uncommit unused memory delay (seconds) |
| `-XX:ZTenuringThreshold` | -1 | Tenuring threshold, -1 = dynamic |

### Diagnostic Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:ZYoungGCThreads` | 0 | Young generation GC threads (0 = auto) |
| `-XX:ZOldGCThreads` | 0 | Old generation GC threads (0 = auto) |
| `-XX:+ZProactive` | true | Enable proactive GC cycles |
| `-XX:+ZUncommit` | true | Uncommit unused memory |

### IDE Recommended Configuration

```
-XX:+UseZGC
-XX:+ZGenerational
-XX:ZAllocationSpikeTolerance=2.0
-XX:ZCollectionIntervalMajor=300
-XX:+ZProactive
```

---

## ZGC Common Flags

ZGC 공통 플래그 (Generational/Non-generational).

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:ZAllocationSpikeTolerance` | 2.0 | Allocation spike tolerance factor |
| `-XX:ZFragmentationLimit` | varies | Maximum heap fragmentation (%) |
| `-XX:ZMarkStackSpaceLimit` | 8G | Mark stack space limit |
| `-XX:ZCollectionInterval` | 0 | Force GC interval (seconds) |
| `-XX:+ZProactive` | true | Proactive GC cycles |
| `-XX:+ZUncommit` | true | Uncommit unused memory |
| `-XX:ZUncommitDelay` | 300 | Uncommit delay (seconds) |

---

## G1GC Flags

Version 222-242 기본 GC. Version 243+에서도 사용 가능.

### Activation

```
-XX:+UseG1GC
```

### Core Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:MaxGCPauseMillis` | max_uintx-1 | Target max GC pause time (ms) |
| `-XX:G1HeapRegionSize` | 0 | Region size (0 = auto, 1MB-32MB) |
| `-XX:G1ReservePercent` | 10 | Reserve heap percentage |
| `-XX:G1NewSizePercent` | 5 | Min young gen size (%) |
| `-XX:G1MaxNewSizePercent` | 60 | Max young gen size (%) |
| `-XX:G1MixedGCCountTarget` | 8 | Target mixed GC count after marking |
| `-XX:G1HeapWastePercent` | 5 | Allowed uncollected space (%) |
| `-XX:InitiatingHeapOccupancyPercent` | 45 | IHOP for concurrent marking |

### Concurrency Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:G1ConcRefinementThreads` | 0 | Refinement threads (0 = auto) |
| `-XX:ConcGCThreads` | 0 | Concurrent GC threads (0 = auto) |
| `-XX:ParallelGCThreads` | 0 | Parallel GC threads (0 = auto) |
| `-XX:+G1UseAdaptiveIHOP` | true | Adaptive IHOP |

### Periodic GC

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:G1PeriodicGCInterval` | 0 | Periodic GC interval (ms), 0 = disabled |
| `-XX:+G1PeriodicGCInvokesConcurrent` | true | Use concurrent GC for periodic |
| `-XX:G1PeriodicGCSystemLoadThreshold` | 0.0 | System load threshold |

### IDE Recommended Configuration

```
-XX:+UseG1GC
-XX:MaxGCPauseMillis=200
-XX:+UseStringDeduplication
-XX:G1ReservePercent=15
-XX:InitiatingHeapOccupancyPercent=35
```

---

## Shenandoah Flags

Ultra-low pause time GC.

### Activation

```
-XX:+UseShenandoahGC
```

### Core Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:ShenandoahGCHeuristics` | adaptive | Heuristics mode |
| `-XX:ShenandoahMinFreeThreshold` | 10 | Min free threshold (%) |
| `-XX:ShenandoahAllocationThreshold` | 0 | Allocation threshold |
| `-XX:ShenandoahGuaranteedGCInterval` | 300000 | Guaranteed GC interval (ms) |

### Heuristics Modes

| Mode | Description |
|------|-------------|
| `adaptive` | Adapts to application behavior (default) |
| `static` | Fixed triggering thresholds |
| `compact` | Aggressive space compaction |
| `aggressive` | Continuous concurrent GC |

### IDE Recommended Configuration

```
-XX:+UseShenandoahGC
-XX:ShenandoahGCHeuristics=adaptive
-XX:ShenandoahGuaranteedGCInterval=300000
```

---

## Parallel GC Flags

Maximum throughput GC.

### Activation

```
-XX:+UseParallelGC
```

### Core Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:ParallelGCThreads` | 0 | Parallel GC threads (0 = auto) |
| `-XX:+UseAdaptiveSizePolicy` | true | Adaptive sizing |
| `-XX:GCTimeRatio` | 99 | App time to GC time ratio |
| `-XX:MaxGCPauseMillis` | max | Target max pause time |
| `-XX:YoungGenerationSizeIncrement` | 20 | Young gen size increment (%) |

### IDE Recommended Configuration

```
-XX:+UseParallelGC
-XX:ParallelGCThreads=4
-XX:+UseAdaptiveSizePolicy
-XX:GCTimeRatio=19
```
