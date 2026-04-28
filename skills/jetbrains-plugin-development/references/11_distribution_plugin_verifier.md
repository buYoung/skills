# Plugin Verifier

## Plugin Verifier

The `verifyPlugin` Gradle task simulates running your plugin against a list of IDE
versions and reports incompatible API usage, missing classes, accessor changes, and some
dynamic-plugin issues. The task is auto-applied by the IntelliJ Platform Gradle Plugin
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

Run it in CI. It is the only practical way to catch "works in my dev IDE, breaks on the
user's IDE branch" before users find it.

`verifyPlugin` issues you should treat as blocking:

- Missing classes / methods (you used a class removed in a target branch).
- Use of `@ApiStatus.Internal` from outside the platform.
- Static field reachability of plugin classes from the platform classloader (potential
  unload leaks).

`@ApiStatus.Experimental` warnings are informational; track them so a future API rename
doesn't surprise you.
