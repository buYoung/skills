# Dependencies and Platform Versions

### `<depends>` — modules and other plugins

You must depend on at least `com.intellij.modules.platform`. Common module dependencies:

| Module | Provides |
|---|---|
| `com.intellij.modules.platform` | Core platform |
| `com.intellij.modules.lang` | Language API support |
| `com.intellij.modules.vcs` | VCS API |
| `com.intellij.modules.xml` | XML support |
| `com.intellij.modules.xdebugger` | Debugger API |
| `com.intellij.modules.python` / `.ruby` / `.go` / `.cidr.lang` / etc. | Language-specific APIs |
| `com.intellij.java` | Java PSI / JDK / etc. (bundled plugin id) |
| `org.jetbrains.kotlin` | Kotlin plugin id |

For optional integration with another plugin, use `<depends optional="true" config-file="x.xml">`. The contents of `x.xml` (sibling of `plugin.xml`) load only when the dependency is present. This is how a single plugin can expose Python features only on PyCharm or contribute Spring support only when the Spring plugin is installed.

```xml
<depends optional="true" config-file="python-support.xml">com.intellij.modules.python</depends>
```

You can also use `<incompatible-with>` to declare a hard exclusion against another module.

### Modules and plugins split out in 2026.3

The [2026.3 incompatible changes](https://plugins.jetbrains.com/docs/intellij/api-changes-list-2026.html) move several APIs out of the core plugin. The notes say this should not affect binary compatibility, but a plugin that uses these APIs needs an explicit dependency in `build.gradle.kts`:

| API area | Gradle dependency | Note |
|---|---|---|
| Debugger, External System, remote servers, `webide.impl` | `bundledModule("intellij.platform.debugger")`, `bundledModule("intellij.platform.externalSystem")`, `bundledModule("intellij.platform.remoteServers")`, `bundledModule("intellij.platform.webide.impl")` | Separate modules with their own classloaders |
| Version Control | `bundledPlugin("com.intellij.platform.vcs")` | A dependency on the `com.intellij.modules.vcs` alias is sufficient |
| XML and HTML | `bundledPlugin("com.intellij.xml")` | A dependency on the `com.intellij.modules.xml` alias is sufficient |
| Tasks and Contexts | `bundledPlugin("com.intellij.platform.tasks")` | Not the `com.intellij.tasks` (Issue Trackers) plugin |
| Problems View | `bundledPlugin("com.intellij.problemsView")` | |

JNA is no longer visible through the core classloader either. A plugin that uses `com.sun.jna.*` or `com.intellij.jna.JnaLoader` without shipping its own JNA declares `<dependencies><module name="intellij.libraries.jna"/></dependencies>` in `plugin.xml` and `bundledModule("intellij.libraries.jna")` in Gradle; otherwise it fails at runtime with `NoClassDefFoundError`. The same notes recommend the Java 25 Foreign Function and Memory API as the replacement.

### Picking `sinceBuild` / `untilBuild`

`sinceBuild` is the lowest IDE branch your plugin works on. Branch-to-version mapping:

| Branch | Year |
|---|---|
| 211–213 | 2021.1 / .2 / .3 |
| 221–223 | 2022.1 / .2 / .3 |
| 231–233 | 2023.1 / .2 / .3 |
| 241–243 | 2024.1 / .2 / .3 |
| 251–253 | 2025.1 / .2 / .3 |
| 261 | 2026.1 |
| 262 | 2026.2 |
| 263 | 2026.3 |

Pick the **lowest branch you have actually tested**. This skill uses IntelliJ IDEA `2026.3` (branch `263`) as its current source baseline while retaining `2024.1` (`241`) as the minimum guidance version. Suspending read actions (`readAction`, `smartReadAction`) and service `CoroutineScope` injection are available from `241`. Suspending write actions and dispatchers changed later (`edtWriteAction` in 2025.1, `Dispatchers.UI` in 2025.3, background `writeAction` in 2026.2), so check `04_threading_coroutines_2024.md` before using them on an older minimum. The unified `intellijIdea(...)` Gradle helper is `253`+, so a plugin staying on the legacy `intellijIdeaCommunity(...)`/`intellijIdeaUltimate(...)` helpers can still target `241` without issue. Verify every API used by a plugin against the exact target IDE and its resolved bundled plugins; the branch number alone does not establish public API status.

`untilBuild` should be open (provider `{ null }` in 2.x or omit the attribute). A narrow `untilBuild` flags every fresh EAP as incompatible until you republish. Only narrow it when you know an upcoming change will break you.

### Public API and version evidence

The source baseline for the current examples is the IntelliJ Community [`idea/2026.3` commit `c91871ae2864649d952825cff72569e3db0e7ac6`](https://github.com/JetBrains/intellij-community/tree/c91871ae2864649d952825cff72569e3db0e7ac6). Before adding a dependency or extension point, inspect its declaration and descriptor in that source or the corresponding SDK artifact. A type that is merely language-level `public` is not automatically usable by external plugins: reject `@ApiStatus.Internal`, `@IntellijInternalApi`, internal extension points, and implementation-only classes. Treat `@ApiStatus.Experimental` separately; use it only when the API is explicitly external and there is no stable public alternative, and record the first supported IDE version and its instability.
