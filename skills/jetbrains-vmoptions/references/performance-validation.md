# Before/After Performance Validation

Use this procedure to verify both option application and workload impact. JVM startup success proves neither.

## 1. Define one hypothesis

Write a falsifiable statement before changing options:

> Changing [one tuning purpose] from A to B should improve [primary metric] during [repeatable IDE operation] without unacceptable regression in [guardrail metrics].

Examples of one tuning purpose include increasing an insufficient heap ceiling or comparing the existing collector with one candidate collector. Do not combine heap, collector, compiler, and thread changes in the same comparison.

## 2. Capture configuration A

Record:

- IDE product and full build;
- actual boot runtime vendor/version/build/path;
- bundled or custom runtime status;
- OS, architecture, machine, power mode, and relevant system load;
- project revision, project settings, enabled plugins, and remote/local topology;
- complete active custom options and their source;
- IDE process PID, effective command line, and initialized flags.

```
jcmd <pid> VM.version
jcmd <pid> VM.command_line
jcmd <pid> VM.flags -all
```

Save enough information to restore A exactly. If the current source file or process cannot be confirmed, do not claim a controlled comparison.

## 3. Prepare candidate B

- Change only the lines needed for the stated tuning purpose.
- Remove a conflicting or duplicate option instead of appending another semantic copy.
- Preserve IDE-required options and unrelated user properties.
- Preflight version-sensitive flags with the exact runtime binary where possible.
- Define the rollback before restarting.

After restarting B, run the same `VM.version`, `VM.command_line`, and `VM.flags -all` checks. Confirm the requested value and collector are active and look for ignored, obsolete, disabled, or overridden options. Repeat the same confirmation when returning to A.

`VM.command_line` prints the launch command, while `VM.flags -all` prints the current values of all flags supported by that VM. See the [Oracle JDK 25 `jcmd` reference](https://docs.oracle.com/en/java/javase/25/docs/specs/man/jcmd.html). For JBR 17 or 21, check the matching runtime's command help because availability can differ.

## 4. Keep test conditions comparable

Hold these constant unless they are the variable being studied:

- IDE and JBR build;
- project revision and project settings;
- plugin set;
- machine, operating system, display/remote topology, and background load;
- power source and power/performance mode;
- profiler, GC log, and JFR collection configuration;
- cache state appropriate to the scenario.

Perform an untimed preparation run for each condition. Then measure A and B in alternating order to reduce drift. Collect at least three measured repetitions per condition and report the median plus a spread such as min–max or interquartile range. More repetitions are appropriate when variability is high.

Do not mix cold startup with warmed editing measurements. Measure full indexing separately from ready-state work and recreate the same initial cache/index state for every full-index run. Cache invalidation can remove indices and Local History; do not perform it without the user's explicit intent and a recoverable setup.

## 5. Choose evidence for the symptom

| Target | Collection method | Compare |
|---|---|---|
| Option recognition and application | Same-runtime preflight plus IDE-process `VM.command_line` and `VM.flags -all` | Requested option, effective value, selected collector, warnings or inactive flags |
| GC and memory | Same GC log and JFR settings in A and B | Pause duration/count, allocation rate, post-GC occupancy, heap trend, concurrent GC CPU |
| Slow editing or UI stalls | IDE CPU profiling while replaying the same action | Operation duration, hot CPU paths, blocked/waiting time, correlation with GC/safepoints |
| Startup | Product slow-startup profiler if available plus consistent timestamps | Launch-to-ready time, CPU work, I/O, and memory use |
| Indexing | Product indexing profiler or a reproducible performance script | Time to completion, CPU bottlenecks, cache condition |
| Whole-process resources | OS process monitoring | CPU time/utilization, resident/real memory, system memory pressure, swapping |

For GC evidence, use one identical bounded collection setup in A and B. Depending on the exact runtime and product, that may be a startup logging option such as:

```
-Xlog:gc*,safepoint:file=<condition-specific-path>:time,uptime,level,tags:filecount=5,filesize=20m
```

or a JFR recording started after the IDE reaches the same test state:

```
jcmd <pid> JFR.start name=vmoptions-comparison settings=profile duration=<duration> filename=<condition-specific-path>
```

Confirm command support with `jcmd <pid> help`. Use the same JFR settings and duration for A and B, keep output paths separate, and account for profiler/recording overhead. Profiles and recordings can contain sensitive code, paths, and activity data.

Use JetBrains' profiler and performance scripts only after confirming that the action/plugin exists for the user's product, edition, and version:

- [JetBrains: Reporting performance problems](https://intellij-support.jetbrains.com/hc/en-us/articles/207241235-Reporting-performance-problems)
- [JetBrains: Performance testing plugin and scripts](https://intellij-support.jetbrains.com/hc/en-us/articles/207241225-Performance-testing-plugin)

## 6. Record results

Use a compact table and keep raw evidence paths separate:

| Condition | Effective change confirmed? | Run 1 | Run 2 | Run 3 | Median | Spread | Guardrail observations |
|---|---:|---:|---:|---:|---:|---:|---|
| A | Yes/No | | | | | | |
| B | Yes/No | | | | | | |

Also record failures, restarts, profiler errors, cache mismatches, thermal throttling, and background load. Excluding a run requires an explicit reason applied consistently to both conditions.

If effective flags differ from the intended A/B definitions, discard that run rather than attributing its result to the candidate option.

## 7. Decide and roll back

Adopt B only when:

1. its options are confirmed active in the IDE process;
2. the primary metric improves repeatedly beyond ordinary run-to-run variation;
3. CPU, resident memory, startup, responsiveness, and other guardrails do not regress beyond the user's accepted cost; and
4. the result is attributable to the single tested tuning purpose.

If the difference remains within the observed spread, report no demonstrated improvement. If B fails to start, increases instability, or regresses a guardrail unacceptably, restore A immediately. Keep diagnostic logging or profiling options only when their ongoing value justifies their overhead and disk use.

## Verification limits

- An option accepted by `<runtime>/bin/java ... -version` is only recognized by that binary.
- An option shown in the launch command may still be overridden, obsolete, or inactive; check initialized flags and logs.
- An active option is not evidence of a performance benefit; compare workload metrics.
- Results from one machine, project, IDE/JBR build, or plugin set do not guarantee results elsewhere.
