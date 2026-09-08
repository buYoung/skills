# Plugin Verifier

## Plugin Verifier

The `verifyPlugin` Gradle task performs static binary compatibility analysis against IDE
artifacts. It reports incompatible API usage, missing classes, accessor changes, and
supported descriptor checks; it does not launch the IDE or execute the feature.
The task is provided by the IntelliJ Platform Gradle Plugin
2.x — you only configure it when overriding the default IDE set. (Older guides refer to
this task as `runPluginVerifier`; that is the 1.x name and the 2.x equivalent is
`verifyPlugin`.)

```kotlin
intellijPlatform {
  pluginVerification {                          // block was named `pluginVerifier` in early 2.x previews
    ides {
      recommended()                             // IDE versions matching sinceBuild..untilBuild
      create(IntelliJPlatformType.IntellijIdeaCommunity, "2024.1")  // explicit version
      local(file("/path/to/installed/ide"))    // verify against a local IDE install
    }
  }
}
```

The explicit `2024.1` entry above illustrates an older minimum target, not the source
baseline. Select the actual minimum and current target IDE products/builds; do not assume
`recommended()` alone covers every declared support boundary. Run it in CI alongside
separate sandbox feature and dynamic lifecycle checks.

`verifyPlugin` issues you should treat as blocking:

- Missing classes / methods (you used a class removed in a target branch).
- Use of `@ApiStatus.Internal` or `@IntellijInternalApi`, internal EPs, and other violations
  of the package's external-public-API boundary, regardless of task failure thresholds.

Inspect the generated report, including API-status findings, rather than relying only on
the task exit code: configured failure levels affect which reports fail a build.
An `Experimental` finding is not permission to use an API. Confirm external availability,
record the target versions and instability, and prefer a stable public alternative.

Runtime object retention, stale listeners, cancellation, feature correctness, and actual
classloader unloading require sandbox observation and, when needed, heap analysis. A
successful static check does not establish any of these properties. Record commands,
IDE builds, and observed results; mark checks that were not run explicitly.

Sources: [compatibility verification](https://plugins.jetbrains.com/docs/intellij/verifying-plugin-compatibility.html),
[Plugin Verifier](https://github.com/JetBrains/intellij-plugin-verifier),
and [dynamic plugins](https://plugins.jetbrains.com/docs/intellij/dynamic-plugins.html).
