# Gradle Project Setup

## Contents

- Project shape (IntelliJ Platform Gradle Plugin 2.x)
  - Targeting older IDE branches (2024.1 — 2025.2)
  - Custom language plugin helpers
  - 1.x → 2.x migration cheatsheet
  - Multi-module pattern
  - Sandbox IDE


Read this when you are setting up a new plugin project, configuring the IntelliJ Platform Gradle Plugin, choosing a target IDE, running a sandbox IDE, or migrating build scripts from the legacy Gradle plugin.

## Project shape (IntelliJ Platform Gradle Plugin 2.x)

Use **IntelliJ Platform Gradle Plugin 2.x** (`org.jetbrains.intellij.platform`) for any new project. The 1.x plugin (`org.jetbrains.intellij`) is obsolete and no longer under active development; 2024.2+ targets require 2.x. Tutorials older than ~2024 commonly target 1.x, and its config shape differs.

Before copying a build file, record three values: the exact IDE distribution to compile against, the lowest branch in `sinceBuild` that has actually been verified, and the exact IntelliJ Platform Gradle Plugin version. This reference uses IntelliJ IDEA `2026.3` as its current target, retains separate guidance for `2024.1`, and shows Gradle plugin `2.20.1` (the release documented by the [Gradle Plugin Portal](https://plugins.gradle.org/plugin/org.jetbrains.intellij.platform/2.20.1)). Re-check those values when creating a real project; a marketing version alone is not evidence that a particular API or product module exists.

The [documented 2.20.1 setup requirements](https://plugins.jetbrains.com/docs/intellij/tools-intellij-platform-gradle-plugin.html#requirements) include Gradle 9.0+ and Java 17+ for the build tooling. The selected IDE can impose a higher Java requirement, such as Java 25 for 2026.2 and 2026.3; keep the Gradle runtime, compiler toolchain, plugin bytecode target, and sandbox runtime compatible with their respective requirements.

Minimum `build.gradle.kts` (current shape, targeting 2026.3):

```kotlin
plugins {
  id("org.jetbrains.intellij.platform") version "2.20.1"
  kotlin("jvm") version "..."
}

repositories {
  mavenCentral()
  intellijPlatform { defaultRepositories() }
}

dependencies {
  intellijPlatform {
    // Unified IDE helper for 2025.3+; this example is pinned to the 2026.3 installer.
    // The default is the OS-specific installer. Use the configure block only when you
    // deliberately need the multi-OS archive instead.
    intellijIdea("2026.3")
    bundledPlugin("com.intellij.java")        // bundled plugins your code touches
    zipSigner()                                // for signPlugin / publishPlugin
    // pluginVerifier() and javaCompiler() are auto-applied — do not call them.
  }
}

intellijPlatform {
  pluginConfiguration {
    name = "My Plugin"
    version = "1.0.0"                      // <version>; defaults to project.version
    ideaVersion {
      sinceBuild = "263"                   // this example targets 2026.3
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

The `2026.2+` platform, including 2026.3, requires Java 25. Configure the Gradle JVM and the project toolchain accordingly before compiling this example. The `sinceBuild` value is a claim about the plugin's tested minimum, not a synonym for the version used to compile it; choose the lowest branch you have actually verified.

`buildPlugin` still produces an archive when the descriptor has no `<version>` or `<description>`, but `verifyPlugin` rejects that archive as an invalid plugin. Set the version here or as `project.version`, and keep a `<description>` in `plugin.xml` or `pluginConfiguration`.

The platform bundles the Kotlin standard library. Add `kotlin.stdlib.default.dependency=false` to `gradle.properties` unless the plugin must ship its own stdlib; without the property, `verifyPluginProjectConfiguration` reports a stdlib dependency conflict (see [Kotlin Standard Library](https://plugins.jetbrains.com/docs/intellij/using-kotlin.html#kotlin-standard-library)).

In its default `enable` mode, the Kotlin compiler adds a bridge override to the plugin class for each interface method it inherits with a default body. When that member is `@ApiStatus.Internal`, as `InlineCompletionProvider.isEditorTypeSupported` is in 2026.3, `verifyPlugin` reports an internal API override and invocation that the source never wrote. The `no-compatibility` mode skips these bridges ([Kotlin compiler options](https://kotlinlang.org/docs/compiler-reference.html)):

```kotlin
kotlin {
  jvmToolchain(25)
  compilerOptions {
    jvmDefault = org.jetbrains.kotlin.gradle.dsl.JvmDefaultMode.NO_COMPATIBILITY
  }
}
```

Useful tasks: `runIde`, `buildPlugin`, `signPlugin`, `publishPlugin`, `verifyPlugin`, `prepareSandbox`, `runIdeForUiTests`. (The verifier task was renamed from `runPluginVerifier` to `verifyPlugin` in 2.x.)

When raising an existing build from 2.18.x, check these changes from the [plugin changelog](https://github.com/JetBrains/intellij-platform-gradle-plugin/blob/main/CHANGELOG.md) and [release notes](https://github.com/JetBrains/intellij-platform-gradle-plugin/releases):

- 2.19.0 removed the deprecated `setupDependencies` task. Delete references to it, including "After Sync" Gradle triggers.
- 2.19.0 excludes Kotlin stdlib and Kotlin Coroutines from sandbox runtime classpaths by default, and defaults `kotlin.stdlib.default.dependency` to `false` for projects that apply the IntelliJ Platform settings plugin, unless the project sets it explicitly.
- 2.19.0 runs Plugin Verifier against each verified IDE's bundled JetBrains Runtime and decides `verifyPlugin` failures from the verifier report files, also when `teamCityOutputFormat` is enabled.
- 2.19.0 restored the `NOT_DYNAMIC` failure level, which never failed the build from 2.10.0 through 2.18.1. A build whose `failureLevel` contains `NOT_DYNAMIC`, including `FailureLevel.ALL`, can start failing after the upgrade. 2.19.0 also rejected combining `NOT_DYNAMIC` with `teamCityOutputFormat`; 2.20.0 lifted that restriction.
- 2.20.0 removed the `org.jetbrains.intellij.platform.testIdeBundledPluginsClasspathEnabled` property. All bundled plugins are now on the `test` and `testIde` classpath; exclude specific ones with `org.jetbrains.intellij.platform.testIdeBundledPluginsClasspathExcludes`.
- 2.20.1 returns Gradle's public `TaskDependency` from `intellijPlatformTesting` parameters. Build logic compiled against the previous return type must be recompiled.

`useInstaller` is a dependency-helper option, not a product selector. It defaults to `true` and resolves the OS-specific installer (including its bundled JetBrains Runtime). Set it in the helper's configuration block only when you intentionally need a multi-OS archive, and then add the required `jetbrainsRuntime()` dependency because that archive does not contain the runtime:

```kotlin
intellijIdea("2026.3") {
  useInstaller = false
}
```

### Targeting older IDE branches (2024.1 — 2025.2)

The unified `intellijIdea("...")` helper is the current form for 2025.3 and newer. For plugins targeting a pre-2025.3 product line, use the legacy product-specific helpers; they remain available for those versions:

```kotlin
dependencies {
  intellijPlatform {
    intellijIdeaCommunity("2024.1")      // or intellijIdeaUltimate(...)
    bundledPlugin("com.intellij.java")
    zipSigner()
  }
}
```

The platform version also changes runtime requirements and some threading behavior. Keep the older branch's Java and API conditions with that branch when maintaining a multi-version plugin; do not infer compatibility from the dependency helper syntax alone.

For a plugin that supports `2024.1`, pair the legacy dependency example above with a Java 17-compatible bytecode target and verify `sinceBuild = "241"` separately. Select the Gradle runtime independently from the plugin bytecode target; it must also satisfy the chosen Gradle and IntelliJ Platform Gradle Plugin versions.

### Custom language plugin helpers

When the plugin uses a JFlex lexer or a Grammar-Kit BNF (see `07_language_pipeline.md` and `examples/simple_language_plugin/`), apply the dedicated Grammar-Kit sub-plugin. It provides both `generateLexer` and `generateParser`. Grammar-Kit and JFlex are build tools, not runtime plugin dependencies. The sub-plugin supplies their versions; use the `grammarKit(...)` and `jflex(...)` dependency helpers only to override them:

```kotlin
plugins {
  id("org.jetbrains.intellij.platform") version "2.20.1"
  id("org.jetbrains.intellij.platform.grammarkit") version "2.20.1"
}

dependencies {
  intellijPlatform {
    intellijIdea("2026.3")
  }
}

tasks {
  generateLexer {
    sourceFile = file("src/main/grammar/Simple.flex")
  }
  generateParser {
    sourceFile = file("src/main/grammar/Simple.bnf")
  }
}

sourceSets {
  main {
    java {
      srcDir(tasks.generateLexer)
      srcDir(tasks.generateParser)
    }
  }
}
```

Each task needs its `sourceFile`. Passing the task to `srcDir()` adds its generated output to the main source set and makes compilation depend on generation, as in the [Grammar-Kit recipe](https://plugins.jetbrains.com/docs/intellij/tools-intellij-platform-gradle-plugin-recipes.html#generate-a-lexer-and-parser-with-grammar-kit). The plugin version must be kept in lockstep with the main IntelliJ Platform Gradle Plugin. `composeUI()` is unrelated to language generation and should be added only when the plugin actually embeds the corresponding UI technology.

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

`runIde` launches a sandbox IDE with **isolated** settings, plugins, and caches. Settings you change in the sandbox do not affect your daily IDE. `autoReload = true` asks the running IDE to reload a newly prepared version of a dynamic plugin; it does not trigger compilation or rebuild the plugin. Run the relevant compile/build task first, then let the reload happen. Reload still requires every contributed extension and service to satisfy dynamic-plugin constraints (see `11_distribution_dynamic_plugins_classloaders.md`).

### Source and API evidence

For this reference, the IntelliJ Community `idea/2026.3` source snapshot is pinned to [commit `c91871ae2864649d952825cff72569e3db0e7ac6`](https://github.com/JetBrains/intellij-community/tree/c91871ae2864649d952825cff72569e3db0e7ac6). The Gradle configuration follows the [official 2.x plugin documentation](https://plugins.jetbrains.com/docs/intellij/tools-intellij-platform-gradle-plugin.html) and its [dependency helper contract](https://plugins.jetbrains.com/docs/intellij/tools-intellij-platform-gradle-plugin-dependencies-extension.html). The [Grammar-Kit sub-plugin contract](https://plugins.jetbrains.com/docs/intellij/tools-intellij-platform-gradle-plugin-plugins.html#grammar-kit) provides the lexer/parser tasks; do not apply this 2.20.1 shape blindly to older 2.x releases. Source inspection is evidence for the selected IDE version only: a language-level `public` declaration is not sufficient if the declaration or extension point is marked internal, or intended only for platform implementation. Deprecation is a separate compatibility signal: prefer its documented public replacement, preserving older branches where needed.
