# GC Options Reference

Detailed garbage collector flags for JetBrains IDE VM options.

## Table of Contents

1. [IDE Version Compatibility](#ide-version-compatibility)
2. [GC Selection by IDE Version](#gc-selection-by-ide-version)
3. [Generational ZGC (JDK 21+)](#generational-zgc-jdk-21)
4. [ZGC Common Flags](#zgc-common-flags)
5. [G1GC Flags](#g1gc-flags)
6. [Shenandoah Flags](#shenandoah-flags)
7. [Parallel GC Flags](#parallel-gc-flags)

---

## IDE Version Compatibility

Support range and default GC behavior by IDE version.

| Version Range | JDK | Support Status |
|---------------|-----|----------------|
| 243+ | 21 | Supported |
| 222-242 | 17 | Supported |
| < 222 | - | Not supported |

---

## GC Selection by IDE Version

GC selection and behavior summary (why/when) by version range.

| Version Range | Default GC | Flags | Behavior / When it helps |
|---------------|------------|-------|---------------------------|
| 243+ | Generational ZGC | `-XX:+UseZGC -XX:+ZGenerational` | Low-pause, large heaps, latency-sensitive IDE workloads |
| 222-242 | G1GC | `-XX:+UseG1GC` | Balanced throughput/latency for mixed workloads |

### For Version 243+ (JDK 21)

| GC | Flags | Behavior / When it helps |
|----|-------|---------------------------|
| Generational ZGC | `-XX:+UseZGC -XX:+ZGenerational` | Low latency with young/old separation; effective with large heaps |
| ZGC (Legacy) | `-XX:+UseZGC` | Low latency with simpler tuning surface |
| G1GC | `-XX:+UseG1GC` | Balanced throughput/latency for mixed workloads |
| Shenandoah | `-XX:+UseShenandoahGC` | Very low pause times with concurrent compaction |
| Parallel GC | `-XX:+UseParallelGC` | Throughput-oriented, stop-the-world pauses |
| Serial GC | `-XX:+UseSerialGC` | Single-threaded, small heaps or constrained cores |

### For Version 222-242 (JDK 17)

| GC | Flags | Behavior / When it helps |
|----|-------|---------------------------|
| G1GC | `-XX:+UseG1GC` | Balanced throughput/latency for mixed workloads |
| ZGC | `-XX:+UseZGC` | Low latency (non-generational) |
| Shenandoah | `-XX:+UseShenandoahGC` | Very low pause times with concurrent compaction |
| Parallel GC | `-XX:+UseParallelGC` | Throughput-oriented, stop-the-world pauses |
| Serial GC | `-XX:+UseSerialGC` | Single-threaded, small heaps or constrained cores |

---

## Generational ZGC (JDK 21+)

Available in version 243+. Generational mode is available on JDK 21.

Behavior: Concurrent low-pause GC with young/old separation; reduces pause impact as heaps grow.
When it helps: Large heaps, latency-sensitive IDE workloads, frequent allocation spikes.

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
| `-XX:+ZCollectionIntervalOnly` | false | Use only timers for GC heuristics |
| `-XX:ZStatisticsInterval` | 10 | Statistics print interval (seconds) |

### Example Configuration

```
-XX:+UseZGC
-XX:+ZGenerational
-XX:ZAllocationSpikeTolerance=2.0
-XX:ZCollectionIntervalMajor=300
-XX:+ZProactive
```

---

## ZGC Common Flags

Common ZGC flags (Generational/Non-generational).

Behavior: Adjusts ZGC heuristics around allocation spikes, fragmentation, and memory uncommit.
When it helps: Tail latency tuning, memory footprint control, and allocation spike smoothing.

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:ZAllocationSpikeTolerance` | 2.0 | Allocation spike tolerance factor |
| `-XX:ZFragmentationLimit` | ZGC default: 5.0; XGC default: 25.0 | Maximum heap fragmentation (%) |
| `-XX:ZMarkStackSpaceLimit` | 8G | Mark stack space limit |
| `-XX:ZCollectionInterval` | 0 | Force GC interval (seconds) |
| `-XX:+ZProactive` | true | Proactive GC cycles |
| `-XX:+ZUncommit` | true | Uncommit unused memory |
| `-XX:ZUncommitDelay` | 300 | Uncommit delay (seconds) |

---

## G1GC Flags

Default GC for versions 222-242. Also available in 243+.

Behavior: Region-based GC balancing throughput and pause times using concurrent marking.
When it helps: Mixed workloads with moderate latency sensitivity and predictable throughput needs.

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
| `-XX:G1MixedGCLiveThresholdPercent` | 85 | Max live bytes for mixed GC region (%) |
| `-XX:G1ConcMarkStepDurationMillis` | 10.0 | Concurrent marking step duration (ms) |
| `-XX:G1EagerReclaimRemSetThreshold` | 0 | RSet threshold for humongous eager reclaim |

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

### Example Configuration

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

Behavior: Concurrent compaction with very low pauses; may trade throughput for latency.
When it helps: Latency-sensitive workflows where pause time dominates.

### Activation

```
-XX:+UseShenandoahGC
```

### Core Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-XX:ShenandoahGCMode` | satb | GC mode (satb, iu, passive) |
| `-XX:ShenandoahGCHeuristics` | adaptive | Heuristics mode |
| `-XX:ShenandoahMinFreeThreshold` | 10 | Min free threshold (%) |
| `-XX:ShenandoahAllocationThreshold` | 0 | Allocation threshold (%) |
| `-XX:ShenandoahGuaranteedGCInterval` | 300000 | Guaranteed GC interval (ms) |
| `-XX:ShenandoahEvacReserve` | 5 | Evacuation reserve space (%) |
| `-XX:+ShenandoahPacing` | true | Pace allocations to give GC time |
| `-XX:ShenandoahPacingMaxDelay` | 10 | Max pacing delay (ms) |
| `-XX:+ShenandoahUncommit` | true | Uncommit unused memory |
| `-XX:ShenandoahUncommitDelay` | 300000 | Uncommit delay (ms) |

### GC Modes

| Mode | Description |
|------|-------------|
| `satb` | Snapshot-at-the-beginning (default, 3-pass mark-evac-update) |
| `iu` | Incremental-update (3-pass mark-evac-update) |
| `passive` | Stop-the-world only (degenerated or full GC) |

### Heuristics Modes

| Mode | Description |
|------|-------------|
| `adaptive` | Adapts to application behavior (default) |
| `static` | Fixed triggering thresholds |
| `compact` | Aggressive space compaction |
| `aggressive` | Continuous concurrent GC |

### Example Configuration

```
-XX:+UseShenandoahGC
-XX:ShenandoahGCMode=satb
-XX:ShenandoahGCHeuristics=adaptive
-XX:ShenandoahGuaranteedGCInterval=300000
-XX:+ShenandoahPacing
```

---

## Parallel GC Flags

Maximum throughput GC.

Behavior: Stop-the-world parallel collector optimized for throughput.
When it helps: Batch-like workloads where throughput matters more than pause times.

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

### Example Configuration

```
-XX:+UseParallelGC
-XX:ParallelGCThreads=4
-XX:+UseAdaptiveSizePolicy
-XX:GCTimeRatio=19
```
