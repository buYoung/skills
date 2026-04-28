# Gradle Project Setup

## Contents

- Project shape (IntelliJ Platform Gradle Plugin 2.x)
  - Targeting older IDE branches (2024.1 — 2025.2)
  - Custom language plugin helpers
  - 1.x → 2.x migration cheatsheet
  - Multi-module pattern
  - Sandbox IDE


Read this when you are setting up a new plugin project, configuring the IntelliJ Platform
Gradle Plugin, choosing a target IDE, running a sandbox IDE, or migrating build scripts from
the legacy Gradle plugin.

## Project shape (IntelliJ Platform Gradle Plugin 2.x)

Use **IntelliJ Platform Gradle Plugin 2.x** (`org.jetbrains.intellij.platform`) for any new
project. The 1.x plugin (`org.jetbrains.intellij`) is in maintenance mode; tutorials older
than ~2024 commonly target it and its config shape differs.

Minimum `build.gradle.kts` (current shape, targeting 2026.1):

```kotlin
plugins {
  id("org.jetbrains.intellij.platform") version "2.x.x"
  kotlin("jvm") version "..."
}

repositories {
  mavenCentral()
  intellijPlatform { defaultRepositories() }
}

dependencies {
  intellijPlatform {
    // Unified IDE helper since 2025.3 — works for both Community and Ultimate.
    // Pass `useInstaller = false` (or `IntelliJPlatformType.IntellijIdeaCommunity`)
    // for a specific edition; the default resolves the appropriate one.
    intellijIdea("2026.1")
    bundledPlugin("com.intellij.java")        // bundled plugins your code touches
    zipSigner()                                // for signPlugin / publishPlugin
    // pluginVerifier() and javaCompiler() are auto-applied — do not call them.
    // instrumentationTools() is deprecated and a no-op; remove any leftover calls.
  }
}

intellijPlatform {
  pluginConfiguration {
    name = "My Plugin"
    ideaVersion {
      sinceBuild = "261"                   // 2026.1
      untilBuild = provider { null }       // open until you have a known break
    }
  }
  buildSearchableOptions = false           // enable in CI release only — slow
  autoReload = true                        // dynamic reload in sandbox
}
```

Useful tasks: `runIde`, `buildPlugin`, `signPlugin`, `publishPlugin`, `verifyPlugin`,
`prepareSandbox`, `runIdeForUiTests`. (The verifier task was renamed from
`runPluginVerifier` to `verifyPlugin` in 2.x.)

### Targeting older IDE branches (2024.1 — 2025.2)

The unified `intellijIdea("...")` helper is **2025.3 and newer only**. For plugins whose
`sinceBuild` is below 253, use the legacy product-specific helpers — they remain available
indefinitely:

```kotlin
dependencies {
  intellijPlatform {
    intellijIdeaCommunity("2024.1")      // or intellijIdeaUltimate(...), clion(...), goland(...), pycharm(...)
    bundledPlugin("com.intellij.java")
    zipSigner()
  }
}
```

The skill's other Kotlin/coroutine/UI guidance still applies — only the dependency
declaration syntax changes.

### Custom language plugin helpers

When the plugin uses a JFlex lexer or a Grammar-Kit BNF (see `07_language_pipeline.md` and
`examples/simple_language_plugin/`), add the generators alongside the platform dependency:

```kotlin
dependencies {
  intellijPlatform {
    intellijIdea("2026.1")
    grammarKit()                  // pulls Grammar-Kit; latest by default, override with grammarKit("2025.1")
    jflex()                       // pulls the JFlex generator; same override pattern
  }
}
```

These wire the `generateLexer` / `generateParser` Gradle tasks against the correct
versions for the target platform. `composeUI()` is the analogous helper if your plugin
embeds Jetbrains Compose UI (rare; mostly relevant for newer Compose-based panels).

### 1.x → 2.x migration cheatsheet

| Topic | 1.x | 2.x |
|---|---|---|
| Plugin id | `org.jetbrains.intellij` | `org.jetbrains.intellij.platform` |
| IDE selection | `intellij { version = "..." ; type = "IC" }` | `dependencies { intellijPlatform { intellijIdea("...") } }` (2025.3+) or `intellijIdeaCommunity("...")` (legacy) |
| Bundled plugin | `intellij { plugins = ["java"] }` | `bundledPlugin("com.intellij.java")` |
| External plugin | `intellij { plugins = ["org.foo:1.0"] }` | `plugin("org.foo", "1.0")` |
| Verifier | `runPluginVerifier { ideVersions = [...] }` | Auto-applied; configure overrides via `intellijPlatform { pluginVerification { ides { recommended() } } }` if needed |
| Instrumentation | bundled in 1.x | Auto-applied; `instrumentationTools()` is deprecated and a no-op |
| Java compiler | implicit | Auto-applied; calling `javaCompiler()` is unnecessary |

### Multi-module pattern

For larger plugins, isolate platform-dependent code:

```
my-plugin/
  core/                # plain Kotlin/Java, easy to unit-test
  intellij-plugin/     # depends on `core`, applies the platform Gradle plugin
  build.gradle.kts
```

Only `intellij-plugin/` applies `org.jetbrains.intellij.platform`.

### Sandbox IDE

`runIde` launches a sandbox IDE under `build/idea-sandbox/` with **isolated** settings, plugins,
and caches. Settings you change in the sandbox do not affect your daily IDE. With
`autoReload = true`, code edits trigger plugin recompilation and dynamic reload — provided
the plugin meets dynamic-plugin constraints (see `11_distribution_deployment_checklist.md`).
