# Common Options and Diagnostics

Use this reference to avoid unsupported generic tuning and to collect evidence from the correct process.

## Compiler options

The JVM normally derives compiler thread counts and tiered-compilation behavior from the runtime, CPU active processors, and code cache. Inspect the actual values and compiler/code-cache evidence before overriding them.

| Option | Consider only when | Trade-off |
|---|---|---|
| `-XX:CICompilerCount=<n>` | Compiler queues or profiling show JIT threads causing material CPU contention | Too few threads delay optimization and warmup; too many can compete with IDE work |
| `-XX:TieredStopAtLevel=<n>` | A controlled startup-only experiment has an explicit peak-throughput trade-off | Stopping below level 4 can improve early startup but permanently removes higher-tier optimization for that run |
| `-XX:CompileThreshold=<n>` | Compilation logs/profiles identify a threshold problem | Lowering it front-loads CPU and code-cache use; raising it delays optimized execution |

Do not present fixed `CICompilerCount` values by CPU size or `TieredStopAtLevel=1` as general IDE optimizations. Preserve the IDE/runtime defaults unless measurements justify the trade-off. Confirm that the flag is active on the exact JBR build, not merely recognized.

Useful observations include:

```
jcmd <pid> VM.flags -all
jcmd <pid> Compiler.queue
jcmd <pid> Compiler.codecache
```

Available diagnostic commands vary by runtime build; use `jcmd <pid> help` before depending on one.

When a compiler option explanation depends on a source declaration, link the exact matching runtime revision. The [JBR 25.0.4 `compiler_globals.hpp` at inspected revision `4af5e119...`](https://github.com/JetBrains/JetBrainsRuntime/blob/4af5e1194b7f34a396bd56f25eef17624eb60400/src/hotspot/share/compiler/compiler_globals.hpp) is an evidence example, not a default-value source for other JBR builds. Prefer the target process's initialized values for the recommendation.

## String options

Do not add options that already match the runtime default or IDE bundle. Duplicate declarations add noise and can hide the true source of a value.

- `-XX:+UseStringDeduplication` can trade GC/CPU work for lower retained duplicate-string memory. Confirm support and activity for the selected collector and show duplicate-string or heap evidence before recommending it.
- `-XX:+CompactStrings` and string-concatenation optimizations are runtime defaults in many builds. Verify with `VM.flags -all`; do not restate them as tuning without a measured reason.

Enabling a flag successfully is not proof that it is active for the selected collector or beneficial for the IDE workload.

## Thread and stack options

Leave GC, compiler, and worker thread counts ergonomic unless a profile shows CPU oversubscription or an explicit platform limit is being misdetected. Forced counts can become wrong after hardware, container, remote-host, or runtime changes.

Change `-Xss` only for a demonstrated stack overflow or measured native-memory constraint. A smaller stack raises `StackOverflowError` risk; a larger stack increases per-thread address-space/native-memory use. Platform and architecture affect defaults, so read the initialized value.

## Diagnostics matched to symptoms

| Symptom | Preferred evidence | Notes |
|---|---|---|
| IDE unresponsive | Thread dumps | Capture multiple dumps while hung when the UI cannot start a profiler |
| High CPU or slow editing | **Help | Diagnostic Tools | Start CPU Usage Profiling** | Reproduce the same operation several times |
| Suspected heap leak | IDE memory snapshot/heap dump | Snapshot contents can be sensitive |
| Suspected GC pauses | Unified GC/safepoint logging or JFR | Use the same collection settings in A and B |
| Slow startup | Product's slow-startup profiling action if present | Product/version availability must be checked |
| Slow indexing | Product's indexing profiler if present | Cache invalidation changes the test state and can remove Local History/indices |

JetBrains documents current profiling entry points and notes that profiler availability differs by product/edition/version:

- [JetBrains: Reporting performance problems](https://intellij-support.jetbrains.com/hc/en-us/articles/207241235-Reporting-performance-problems)
- [JetBrains: Performance testing plugin](https://intellij-support.jetbrains.com/hc/en-us/articles/207241225-Performance-testing-plugin)

### GC and safepoint logging

A temporary diagnostic candidate can use unified logging with rotation:

```
-Xlog:gc*,safepoint:file=<existing-writable-directory>/ide-gc.log:time,uptime,level,tags:filecount=5,filesize=20m
```

Validate the exact logging syntax with the target runtime before applying it. State disk usage, choose an existing writable location, use the same line in both comparison conditions, and remove it after data collection if ongoing logs are unnecessary.

### Java Flight Recorder

When `jcmd <pid> help` lists JFR commands, start and stop a bounded recording using identical settings for A and B. The exact syntax and available profiles depend on the runtime; obtain command help from the target process:

```
jcmd <pid> help JFR.start
jcmd <pid> help JFR.stop
```

The JDK documentation distinguishes lower-overhead `default.jfc` from more detailed, higher-overhead `profile.jfc`. Do not compare runs collected with different settings.

- [Oracle JDK 25 `jcmd` command reference](https://docs.oracle.com/en/java/javase/25/docs/specs/man/jcmd.html)

## Process boundaries

Before proposing any option, name the target PID and configuration owner:

- IDE custom VM options: local IDE process only;
- remote development: backend and frontend are distinct;
- Gradle: Gradle daemon/JVM settings;
- Maven: importer/runner settings;
- run/debug and tests: their run configuration/JDK;
- Kotlin daemon or language service: its own launcher/settings.

If the evidence comes from a non-IDE process, do not place the remedy in IDE `.vmoptions`.

## Apply and recover

Use **Help | Edit Custom VM Options** or the already-confirmed Toolbox/environment override. JetBrains advises against editing the installation's default file because updates replace it and editing a macOS application bundle can invalidate its signature.

Before editing, preserve the exact baseline text. After restart, confirm the active command line and flags. If startup fails, restore the baseline custom file or remove only the new lines from the confirmed override source.

- [JetBrains: Advanced configuration](https://www.jetbrains.com/help/idea/tuning-the-ide.html)
- [JetBrains: IDE directories and Special Files and Folders](https://www.jetbrains.com/help/idea/directories-used-by-the-ide-to-store-settings-caches-plugins-and-logs.html)
