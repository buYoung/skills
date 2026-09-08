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

Before copying a build file, record three values: the exact IDE distribution to compile
against, the lowest branch in `sinceBuild` that has actually been verified, and the exact
IntelliJ Platform Gradle Plugin version. This reference uses IntelliJ IDEA `2026.2.2` as its
current target, retains separate guidance for `2024.1`, and shows
Gradle plugin `2.18.1` (the release documented by the [Gradle Plugin Portal](https://plugins.gradle.org/plugin/org.jetbrains.intellij.platform/2.18.1)).
Re-check those values when creating a real project; a marketing version alone is not evidence
that a particular API or product module exists.

The [documented 2.18.1 setup requirements](https://plugins.jetbrains.com/docs/intellij/tools-intellij-platform-gradle-plugin.html#requirements)
include Gradle 9.0+ and Java 17+ for the build tooling. The selected IDE can impose a higher
Java requirement, such as Java 25 for 2026.2; keep the Gradle runtime, compiler toolchain,
plugin bytecode target, and sandbox runtime compatible with their respective requirements.

Minimum `build.gradle.kts` (current shape, targeting 2026.2.2):

```kotlin
plugins {
  id("org.jetbrains.intellij.platform") version "2.18.1"
  kotlin("jvm") version "..."
}

repositories {
  mavenCentral()
  intellijPlatform { defaultRepositories() }
}

dependencies {
  intellijPlatform {
    // Unified IDE helper for 2025.3+; this example is pinned to the 2026.2.2 installer.
    // The default is the OS-specific installer. Use the configure block only when you
    // deliberately need the multi-OS archive instead.
    intellijIdea("2026.2.2")
    bundledPlugin("com.intellij.java")        // bundled plugins your code touches
    zipSigner()                                // for signPlugin / publishPlugin
    // pluginVerifier() and javaCompiler() are auto-applied — do not call them.
  }
}

intellijPlatform {
  pluginConfiguration {
    name = "My Plugin"
    ideaVersion {
      sinceBuild = "262"                   // this example targets 2026.2.2
      untilBuild = provider { null }       // open until you have a known break
    }
  }
  // Keep the default true for plugins that declare Configurable settings pages.
  // For a plugin with no Configurable extension, the task is skipped automatically;
  // disable it only as a local speed optimization when that warning is intentional.
  buildSearchableOptions = true
  // Reloads a newly built dynamic plugin; it does not compile source files.
  autoReload = true
}
```

The `2026.2+` platform requires Java 25. Configure the Gradle JVM and the project
toolchain accordingly before compiling this example. The `sinceBuild` value is a claim about
the plugin's tested minimum, not a synonym for the version used to compile it; choose the
lowest branch you have actually verified.

Useful tasks: `runIde`, `buildPlugin`, `signPlugin`, `publishPlugin`, `verifyPlugin`,
`prepareSandbox`, `runIdeForUiTests`. (The verifier task was renamed from
`runPluginVerifier` to `verifyPlugin` in 2.x.)

`useInstaller` is a dependency-helper option, not a product selector. It defaults to `true`
and resolves the OS-specific installer (including its bundled JetBrains Runtime). Set it in
the helper's configuration block only when you intentionally need a multi-OS archive, and
then add the required `jetbrainsRuntime()` dependency because that archive does not contain
the runtime:

```kotlin
intellijIdea("2026.2.2") {
  useInstaller = false
}
```

### Targeting older IDE branches (2024.1 — 2025.2)

The unified `intellijIdea("...")` helper is the current form for 2025.3 and newer. For
plugins targeting a pre-2025.3 product line, use the legacy product-specific helpers; they
remain available for those versions:

```kotlin
dependencies {
  intellijPlatform {
    intellijIdeaCommunity("2024.1")      // or intellijIdeaUltimate(...)
    bundledPlugin("com.intellij.java")
    zipSigner()
  }
}
```

The platform version also changes runtime requirements and some threading behavior. Keep the
older branch's Java and API conditions with that branch when maintaining a multi-version
plugin; do not infer compatibility from the dependency helper syntax alone.

For a plugin that supports `2024.1`, pair the legacy dependency example above with a
Java 17-compatible bytecode target and verify `sinceBuild = "241"` separately. Select the
Gradle runtime independently from the plugin bytecode target; it must also satisfy the
chosen Gradle and IntelliJ Platform Gradle Plugin versions.

### Custom language plugin helpers

When the plugin uses a JFlex lexer or a Grammar-Kit BNF (see `07_language_pipeline.md` and
`examples/simple_language_plugin/`), apply the dedicated Grammar-Kit sub-plugin. It provides
both `generateLexer` and `generateParser`; do not add the removed `jflex()` helper or treat
Grammar-Kit as a runtime plugin dependency:

```kotlin
plugins {
  id("org.jetbrains.intellij.platform") version "2.18.1"
  id("org.jetbrains.intellij.platform.grammarkit") version "2.18.1"
}

dependencies {
  intellijPlatform {
    intellijIdea("2026.2.2")
  }
}
```

These wire the `generateLexer` / `generateParser` Gradle tasks against the target platform.
The plugin version must be kept in lockstep with the main IntelliJ Platform Gradle Plugin.
`composeUI()` is unrelated to language generation and should be added only when the plugin
actually embeds the corresponding UI technology.

### 1.x → 2.x migration cheatsheet

| Topic | 1.x | 2.x |
|---|---|---|
| Plugin id | `org.jetbrains.intellij` | `org.jetbrains.intellij.platform` |
| IDE selection | `intellij { version = "..." ; type = "IC" }` | `dependencies { intellijPlatform { intellijIdea("...") } }` (2025.3+) or `intellijIdeaCommunity("...")` (legacy) |
| Bundled plugin | `intellij { plugins = ["java"] }` | `bundledPlugin("com.intellij.java")` |
| External plugin | `intellij { plugins = ["org.foo:1.0"] }` | `plugin("org.foo", "1.0")` |
| Verifier | `runPluginVerifier { ideVersions = [...] }` | Auto-applied; configure overrides via `intellijPlatform { pluginVerification { ides { recommended() } } }` if needed |
| Instrumentation | bundled in 1.x | Auto-applied; the removed `instrumentationTools()` helper must not be called |
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

`runIde` launches a sandbox IDE with **isolated** settings, plugins, and caches. Settings you
change in the sandbox do not affect your daily IDE. `autoReload = true` asks the running IDE
to reload a newly prepared version of a dynamic plugin; it does not trigger compilation or
rebuild the plugin. Run the relevant compile/build task first, then let the reload happen.
Reload still requires every contributed extension and service to satisfy dynamic-plugin
constraints (see `11_distribution_deployment_checklist.md`).

### Source and API evidence

For this reference, the IntelliJ Community `idea/2026.2.2` source snapshot is pinned to
[commit `1c7e601c0423e544917046c23763b15d0282e2a3`](https://github.com/JetBrains/intellij-community/tree/1c7e601c0423e544917046c23763b15d0282e2a3).
The Gradle configuration follows the [official 2.x plugin documentation](https://plugins.jetbrains.com/docs/intellij/tools-intellij-platform-gradle-plugin.html)
and its [dependency helper contract](https://plugins.jetbrains.com/docs/intellij/tools-intellij-platform-gradle-plugin-dependencies-extension.html).
The [Grammar-Kit sub-plugin contract](https://plugins.jetbrains.com/docs/intellij/tools-intellij-platform-gradle-plugin-plugins.html#grammar-kit)
provides the lexer/parser tasks; do not apply this 2.18.1 shape blindly to older 2.x releases.
Source inspection is evidence for the selected IDE version only: a language-level `public`
declaration is not sufficient if the declaration or extension point is marked internal,
or intended only for platform implementation. Deprecation is a separate compatibility
signal: prefer its documented public replacement, preserving older branches where needed.
