---
name: jetbrains-vmoptions
description: >
  Diagnose and tune JetBrains IDE VM options against the IDE's actual boot runtime, including bundled or custom
  JetBrains Runtime (JBR) 17, 21, and 25. Use whenever a user asks about JetBrains IDE performance, freezes,
  startup or indexing speed, memory pressure, garbage collection, heap sizing, `.vmoptions`, or IntelliJ IDEA,
  WebStorm, PyCharm, GoLand, Rider, CLion, PhpStorm, RubyMine, or DataGrip JVM tuning. Distinguish the IDE process
  from project JDK, Gradle, build, test, and remote-backend processes; propose evidence-based minimal changes,
  confirm effective flags after restart, and provide rollback and before/after measurement steps.
---

# JetBrains IDE VM Options

Analyze the running IDE first, then propose the smallest defensible `.vmoptions` delta. Do not create or edit the user's files. Treat a flag being accepted by a JVM as compatibility evidence, not as proof of a performance improvement.

## Workflow

### 1. Establish the runtime and baseline

Read [prerequisite-check.md](references/prerequisite-check.md). Identify the IDE product/build, actual boot runtime vendor/version/build/path, bundled-versus-custom status, OS, architecture, current effective command line and flags, current custom options, and the process showing the problem.

The IDE build number is context only. It does not prove which runtime is active. The project SDK/JDK is not the IDE boot runtime.

If the exact runtime is unavailable, give collection instructions and limit the answer to diagnostics or runtime-independent changes. Do not infer an unconfirmed JBR major from an IDE version.

### 2. Confirm the process boundary

Determine whether the symptom belongs to the local IDE process, a remote IDE backend, Gradle daemon, build process, test JVM, language server, terminal process, or another child process. IDE `.vmoptions` affect only the IDE process to which the file is applied.

Redirect out-of-scope process tuning to that process's own configuration. Never claim that an IDE heap or GC change fixes a Gradle or test JVM problem.

### 3. Diagnose before selecting an option

Classify the observed evidence rather than mapping a symptom directly to GC:

| Evidence | First investigation | Relevant reference |
|---|---|---|
| IDE freeze or UI stall | Thread dump or IDE CPU profile; correlate with GC/safepoint data | [common-options.md](references/common-options.md) |
| High CPU or slow editing | Repeatable IDE CPU profile | [performance-validation.md](references/performance-validation.md) |
| OOM, low-memory warning, or heap saturation | Heap trend, post-GC occupancy, allocation rate | [memory-options.md](references/memory-options.md) |
| Long or frequent GC pauses | GC log or JFR recorded on the IDE process | [gc-options.md](references/gc-options.md) |
| Slow startup or indexing | Separate startup/indexing profile under controlled cache conditions | [performance-validation.md](references/performance-validation.md) |

If evidence is missing, explain how to collect it. A freeze alone is not evidence that the collector is the cause.

### 4. Ground every version-sensitive claim

For each proposed option, record the exact runtime family and build it applies to and distinguish:

- **source declaration**: a value or availability declared by a specific JBR/OpenJDK source revision;
- **runtime-selected value**: the ergonomic or initialized value reported by the user's running JVM;
- **IDE bundle value**: an option supplied by the product's shipped or custom `.vmoptions` file.

Prefer the running IDE's `jcmd VM.command_line` and `VM.flags -all` output for effective values. Link source claims to the matching JBR version, revision, and file. Do not present a source initializer as the final value when runtime ergonomics can change it.

### 5. Propose a minimal delta

Read only the references relevant to the diagnosed cause:

| File | Use for |
|---|---|
| [gc-options.md](references/gc-options.md) | Collector compatibility, selection conflicts, measured GC latency |
| [memory-options.md](references/memory-options.md) | Heap, code cache, metaspace, references, native-memory trade-offs |
| [common-options.md](references/common-options.md) | Compiler, strings, threads, diagnostics, process boundaries |
| [performance-validation.md](references/performance-validation.md) | Application checks and controlled A/B comparison |

Default to an add/change/remove list against the confirmed current settings. Preserve unrelated IDE-supplied options and user properties. Remove duplicates by semantic key (for example, multiple `-Xmx` forms or collector selectors), and explain which effective value wins or conflicts.

Recommend one change purpose at a time. Do not use fixed large heaps, `-Xms = -Xmx`, lower compilation tiers, or forced compiler/GC thread counts as generic optimizations. State the observed condition that justifies them and their costs.

### 6. Include application, verification, and rollback

Tell the user to use the product's **Help | Edit Custom VM Options** action or the exact override source already confirmed. Do not advise editing the installation's default file.

After restart, verify the same IDE process with `jcmd <pid> VM.command_line` and `jcmd <pid> VM.flags -all`. Confirm the requested values, selected collector, and any ignored, obsolete, inactive, or overridden flags. JVM startup success alone is insufficient.

Give a rollback that restores the captured baseline or removes only the proposed delta. For performance claims, follow [performance-validation.md](references/performance-validation.md).

## Output contract

Unless the user explicitly requests a full file, return:

1. **Confirmed environment** — IDE, actual boot runtime/build/path, bundled or custom status, OS/architecture, target process, and unknowns.
2. **Evidence and diagnosis** — observations, likely cause, alternatives, and the provenance of version-sensitive facts.
3. **Proposed delta** — options to add, change, or remove, with reason, applicability, and trade-off. Say “no VM option change yet” when evidence does not support one.
4. **Apply and verify** — exact settings location, restart requirement, and effective-value checks.
5. **Rollback** — how to restore the captured baseline.
6. **Before/after comparison** — target metric and controlled A/B procedure, or a link to the relevant steps.

When a full configuration is requested, require the current effective/original options first, preserve required IDE options, annotate only the intended changes, and still provide the delta separately.

## Compatibility and evidence boundaries

- Cover JBR 17, 21, and 25 only after confirming the actual runtime major and build.
- Treat unconfirmed or other runtime versions as unknown; do not approximate them with the nearest supported version.
- Verify platform- and build-dependent flags against the exact runtime binary before recommending them.
- Distinguish option recognition, option activation, and measured improvement.
- Report when a collector or diagnostic facility is absent from a particular JBR build.
- State when only JBR 25.0.4 source/default inspection is available and other builds or performance outcomes remain unverified.

## Scope

This skill provides analysis, proposed text, verification commands, and measurement procedures for the JetBrains IDE process. It does not change IDE settings, run benchmarks, tune unrelated JVM processes, or guarantee performance gains.
