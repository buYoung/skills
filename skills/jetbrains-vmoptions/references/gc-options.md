# Garbage Collector Options

Use this reference only after identifying the exact IDE boot runtime and observing GC-related evidence. UI lag or a freeze by itself does not justify changing collectors.

## Evidence boundary

Keep three layers separate:

1. **Source declaration:** what a specific JBR/OpenJDK revision declares.
2. **Runtime-selected value:** what ergonomics and initialization selected for this process, shown by `VM.flags -all`.
3. **IDE bundle value:** what the IDE's default or custom options explicitly selected.

The available direct check of local JBR 25.0.4 reported G1 as its default collector. At inspected source revision `4af5e1194b7f34a396bd56f25eef17624eb60400`, `GCConfig::select_gc_ergonomically()` selects G1 on a server-class machine when no collector is already selected, and Serial on a non-server-class machine when available. The same source rejects multiple collectors. This checked result and source are not proof of the effective collector in another build or in an IDE whose bundled options override it.

- [JBR 25.0.4 inspected `gcConfig.cpp` revision](https://github.com/JetBrains/JetBrainsRuntime/blob/4af5e1194b7f34a396bd56f25eef17624eb60400/src/hotspot/share/gc/shared/gcConfig.cpp)
- [JetBrains Runtime release/build matrix](https://github.com/JetBrains/JetBrainsRuntime)

For JBR 17 and 21, link the exact release tag or commit matching the user's runtime before claiming a source default. When that mapping cannot be confirmed, report only the effective value from the user's process.

## Collector selection compatibility

The following table describes upstream generation-mode transitions. The collector still must be present in the exact JBR build and confirmed with the runtime binary.

| Runtime | ZGC selection | Generational-mode note |
|---|---|---|
| JBR 17 | `-XX:+UseZGC` | Non-generational ZGC; do not add `ZGenerational` |
| JBR 21 | `-XX:+UseZGC` plus `-XX:+ZGenerational` when deliberately testing generational ZGC | Generational ZGC was introduced in JDK 21; it was not yet the upstream default mode |
| JBR 25 | `-XX:+UseZGC` | Only generational ZGC remains; `ZGenerational` was made obsolete in JDK 24 and should not be recommended |

Relevant upstream design records:

- [JEP 439: Generational ZGC (JDK 21)](https://openjdk.org/jeps/439)
- [JEP 474: ZGC generational mode by default (JDK 23)](https://openjdk.org/jeps/474)
- [JEP 490: Remove the non-generational mode (JDK 24)](https://openjdk.org/jeps/490)

G1, Parallel, Serial, Shenandoah, or ZGC may be build-dependent. Confirm availability rather than assuming every JBR flavor includes every collector:

```
<runtime-home>/bin/java -XX:+PrintFlagsFinal -version
<runtime-home>/bin/java -XX:+UseG1GC -version
<runtime-home>/bin/java -XX:+UseParallelGC -version
<runtime-home>/bin/java -XX:+UseSerialGC -version
<runtime-home>/bin/java -XX:+UseShenandoahGC -version
<runtime-home>/bin/java -XX:+UseZGC -version
```

Run only the candidate relevant to the diagnosis. A successful `-version` preflight means the option is accepted, not that the IDE uses it or benefits from it.

## Selection rules

- Keep exactly one collector selection. Treat `UseG1GC`, `UseParallelGC`, `UseSerialGC`, `UseShenandoahGC`, and `UseZGC` as mutually exclusive.
- Inspect the active default/custom options before adding a collector. Removing one line can expose another selector or the runtime's ergonomic choice.
- Do not label Generational ZGC as the default collector merely because the runtime supports it.
- Prefer the existing collector unless GC/JFR evidence shows that collector pauses or throughput are a material part of the measured problem.
- A low-pause collector can consume more concurrent CPU or memory bandwidth and can worsen throughput or UI contention. Test it against a defined metric.
- Parallel GC is usually inappropriate for an interactive IDE when long stop-the-world pauses are the complaint, even if it improves batch throughput.
- Serial GC is generally relevant only to constrained/small environments or diagnostics, not as a broad performance recommendation.
- Shenandoah availability and behavior must be verified on the exact JBR build.

## Tuning individual GC flags

Avoid copying a catalog of internal flags into `.vmoptions`. Many defaults are ergonomic, initialized after parsing, or collector-specific. Recommend an individual flag only when all of the following are true:

1. The exact JBR build exposes and accepts it.
2. The selected collector makes it active.
3. A GC log or JFR event identifies the behavior the flag controls.
4. The expected benefit and cost are stated.
5. The A/B comparison changes only that tuning purpose.

Examples of required caveats:

| Option type | When it may be relevant | Required cost/limitation |
|---|---|---|
| `-XX:MaxGCPauseMillis=<ms>` with G1 | Measured pauses miss a latency target | It is a target, not a guarantee; tighter targets may increase GC CPU or reduce throughput |
| G1 reserve/IHOP controls | Logs show evacuation pressure or marking starts too late | Manual values can defeat adaptive behavior and become stale as the workload changes |
| GC thread counts | Profiles show collector threads contending with UI work | Lower counts can lengthen collection; higher counts can increase CPU contention |
| Periodic/proactive collection controls | Evidence shows idle cleanup or delayed cycles are the issue | More cycles can raise CPU use and allocation interference |

Do not present source initializer values as universal defaults. Confirm final values with:

```
jcmd <pid> VM.flags -all
```

## String deduplication

`-XX:+UseStringDeduplication` is not a general-purpose GC switch. Recommend it only after duplicate strings are shown to be a meaningful heap cost and the exact collector/runtime combination supports and activates it. Measure CPU overhead and retained-heap change. Remove duplicate occurrences and verify the effective flag after restart.

## GC evidence collection

Use the same logging or JFR configuration for baseline A and candidate B. A typical bounded rotating log is:

```
-Xlog:gc*,safepoint:file=<writable-path>/ide-gc.log:time,uptime,level,tags:filecount=5,filesize=20m
```

Confirm the path is writable and contains no sensitive location details before suggesting it. GC logs add overhead and disk use; retain them only for the measurement period when appropriate.

Compare pause duration and count, allocation/collection rate, post-GC occupancy, concurrent-cycle behavior, CPU usage, and user-visible task time. Correlation between a stall and a GC/safepoint event matters more than a collector name.

## Output example: delta, not a generic configuration

```
Remove:
-XX:+UseG1GC

Add for JBR 21 candidate B only:
-XX:+UseZGC
-XX:+ZGenerational
```

Accompany such a delta with the observed GC evidence, exact JBR build, compatibility preflight, effective-flag check, expected trade-off, rollback to the original selector, and the comparison procedure in [performance-validation.md](performance-validation.md).
