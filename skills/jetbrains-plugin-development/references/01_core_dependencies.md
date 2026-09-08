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

For optional integration with another plugin, use `<depends optional="true" config-file="x.xml">`.
The contents of `x.xml` (sibling of `plugin.xml`) load only when the dependency is present.
This is how a single plugin can expose Python features only on PyCharm or contribute Spring
support only when the Spring plugin is installed.

```xml
<depends optional="true" config-file="python-support.xml">com.intellij.modules.python</depends>
```

You can also use `<incompatible-with>` to declare a hard exclusion against another module.

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

Pick the **lowest branch you have actually tested**. This skill uses IntelliJ IDEA `2026.2.2`
(branch `262`) as its current source baseline while retaining `2024.1` (`241`) as the
minimum guidance version. Most platform APIs this skill covers
(coroutine suspending APIs, light-service `CoroutineScope` injection, Kotlin UI DSL v2
reach, `DocumentationTarget`) are stable from `241` upward; the unified `intellijIdea(...)`
Gradle helper is `253`+, so a plugin staying on the legacy
`intellijIdeaCommunity(...)`/`intellijIdeaUltimate(...)` helpers can still target `241`
without issue. Verify every API used by a plugin against the exact target IDE and its
resolved bundled plugins; the branch number alone does not establish public API status.

`untilBuild` should be open (provider `{ null }` in 2.x or omit the attribute). A narrow
`untilBuild` flags every fresh EAP as incompatible until you republish. Only narrow it when
you know an upcoming change will break you.

### Public API and version evidence

The source baseline for the current examples is the IntelliJ Community
[`idea/2026.2.2` commit `1c7e601c0423e544917046c23763b15d0282e2a3`](https://github.com/JetBrains/intellij-community/tree/1c7e601c0423e544917046c23763b15d0282e2a3).
Before adding a dependency or extension point, inspect its declaration and descriptor in
that source or the corresponding SDK artifact. A type that is merely language-level
`public` is not automatically usable by external plugins: reject `@ApiStatus.Internal`,
`@IntellijInternalApi`, internal extension points, and implementation-only classes. Treat
`@ApiStatus.Experimental` separately; use it only when the API is explicitly external and
there is no stable public alternative, and record the first supported IDE version and its
instability.
