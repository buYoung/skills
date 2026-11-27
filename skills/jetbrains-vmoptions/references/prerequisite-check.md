# Runtime and Baseline Check

Use this check before making any version-sensitive JetBrains IDE VM option recommendation.

## Required baseline

Collect or explicitly mark unknown:

| Field | Preferred evidence | Why it matters |
|---|---|---|
| IDE product and full build | **Help | About** | Identifies the product instance, not the runtime by itself |
| Boot runtime vendor, version, and build | **Help | About** plus `jcmd <pid> VM.version` when available | Controls flag availability and behavior |
| Runtime home/path | `jcmd <pid> VM.system_properties` or IDE logs/About | Distinguishes bundled from overridden runtime |
| Bundled or custom runtime | Runtime path plus boot-runtime override state | A custom runtime need not match the IDE release |
| OS and architecture | About/system properties | Some defaults and features are platform-specific |
| Effective launch options | `jcmd <pid> VM.command_line` | Shows what started the target process |
| Effective flags | `jcmd <pid> VM.flags -all` | Shows initialized values and flag origins |
| Existing custom options | **Help | Edit Custom VM Options** or confirmed override file | Required to produce a safe delta or full file |
| Affected process | Process list, profile, or PID | IDE options do not tune Gradle, test, or build JVMs |
| Reproducible symptom and evidence | Profile, thread dump, GC log, JFR, OOM, or timing | Determines whether any VM change is justified |

System RAM and CPU count are supporting context, not sufficient reasons to force heap or thread values.

## Runtime identification order

1. Start with **Help | About** and record the complete runtime line, IDE build, OS, and architecture.
2. Identify the actual IDE process PID. In remote development, identify the backend process; the local client is a different process boundary.
3. If the matching JBR/JDK provides `jcmd`, use that tool against the IDE PID:

```
jcmd <pid> VM.version
jcmd <pid> VM.command_line
jcmd <pid> VM.flags -all
jcmd <pid> VM.system_properties
```

4. Record the runtime path and determine whether it is inside the IDE installation/bundle or points to a custom location. Check the product's boot-runtime selector and configuration only as supporting evidence; the running process is authoritative.
5. Read the active custom options through **Help | Edit Custom VM Options**. Also check whether a product-specific VM-options environment variable or Toolbox configuration overrides that file.

If `jcmd` is unavailable or attach is denied, do not fabricate the missing values. Use About, the IDE log, and the active options file, and label effective flags as unverified.

## Do not confuse these runtimes

| Runtime/process | Controlled by IDE `.vmoptions`? | Where to investigate instead |
|---|---:|---|
| Local IDE frontend process | Yes, for that IDE instance | IDE custom VM options |
| Remote IDE backend | Only its backend options | Remote host/backend configuration |
| Project SDK/JDK | No | Project Structure / SDK settings |
| Gradle daemon | No | Gradle JVM and `org.gradle.jvmargs` |
| Maven importer/build JVM | Not necessarily | Maven runner/importer JDK and options |
| Run/debug or test JVM | No | Run/debug configuration |
| Kotlin daemon or other child process | No | Owning tool's process configuration |

JetBrains documents that the IDE boot runtime and the application/project runtime are separate. Do not use `java -version` from an arbitrary terminal as proof of the IDE runtime.

## Version decision

After identifying the actual runtime:

- **JBR 17, 21, or 25:** continue, but verify the exact build because included collectors and obsolete flags can differ.
- **Non-JBR runtime:** use its vendor's matching documentation and source; do not label JBR behavior as applicable.
- **Other or unknown major:** restrict the response to collection and runtime-independent diagnostics. Do not map it to the nearest supported version.

An IDE build-to-JBR table can help locate likely artifacts, but it is never the deciding input because users can select a custom boot runtime.

## Candidate option preflight

Where safe and available, test recognition with the exact runtime binary before editing the IDE configuration:

```
<runtime-home>/bin/java <candidate-options> -version
```

Then check the option names and defaults exposed by that binary:

```
<runtime-home>/bin/java -XX:+PrintFlagsFinal -version
```

This only confirms that the standalone runtime accepts or exposes an option. The restarted IDE process still must be checked with `VM.command_line` and `VM.flags -all`, and performance must be measured separately.

## Security mitigation options

On 2026-11-24 JetBrains published the Java4Shell advisory (CVE-2026-114938). The HotSpot Base64 decoding intrinsic can write out of bounds on x86-64 CPUs with AVX-512 VBMI when it decodes attacker-controlled Base64; ARM64, including Apple Silicon, is not affected. IDEs bundling JBR 17 (17.0.6 and later), 21, or 25 are affected until updated.

- Updated IDE releases add `-XX:-UseBASE64Intrinsics` to their default VM options. The first mitigated version differs by product and release line; take it from the advisory's table instead of inferring it. Before updating, JetBrains' workaround is the same line added through **Help | Edit Custom VM Options**, followed by a restart.
- Treat the option as part of the baseline until the advisory states that the confirmed IDE build bundles a JBR with the upstream fix; JetBrains plans to remove the default option at that point and to update the advisory when the runtime builds are available. Until then, keep it wherever it is present in a delta, comparison condition, or rollback, even though it can make Base64 decoding slower. After an update a manual copy is redundant but harmless. Check the advisory before stating whether a given build ships the option or still needs it.
- The default need not appear in the installation's `.vmoptions` file; IntelliJ IDEA 2026.3.0.1 for macOS aarch64 supplies it through `Contents/Resources/product-info.json`. Confirm the value on the target process with `jcmd <pid> VM.flags`. A standalone `java -XX:+PrintFlagsFinal -version` shows the runtime's own value, not the IDE's launch options.
- Do not suggest `-XX:UseAVX=2`, even where other advisories propose it. JetBrains warns that it prevents JBR 25 from starting on ARM64.
- The IDE update covers the IDE process and remote development backends, which receive the same defaults. Project JDKs, Gradle and Maven daemons, tests, and run configurations need the vendor's fixed JDK or the same option in their own configuration.

## Evidence record

For every version-sensitive claim, retain this shape in the answer or working notes:

| Claim | Runtime/build | Evidence type | Revision/source | Verified on target process? |
|---|---|---|---|---|
| Example: selected collector | JBR 25.0.4 build … | Runtime-selected value | `VM.flags -all` capture | Yes |
| Example: ergonomic selection code | JBR 25.0.4 source | Source declaration | commit and file URL | No; source only |
| Example: bundled `-Xmx` | IDE build … | IDE bundle value | active/default options file | Confirm after restart |

## Sources

- [JetBrains: Change the boot Java runtime of the IDE](https://www.jetbrains.com/help/idea/switching-boot-jdk.html)
- [JetBrains: Advanced configuration and VM-options precedence](https://www.jetbrains.com/help/idea/tuning-the-ide.html)
- [JetBrains Runtime repository and release/build matrix](https://github.com/JetBrains/JetBrainsRuntime)
- [Oracle JDK 25 `jcmd` command reference](https://docs.oracle.com/en/java/javase/25/docs/specs/man/jcmd.html)
- [JetBrains: Java4Shell vulnerability advisory](https://blog.jetbrains.com/security/2026/11/java4shell-vulnerability/)
