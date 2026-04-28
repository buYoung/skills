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

Pick the **lowest branch you have actually tested**. Most platform APIs this skill covers
(coroutine suspending APIs, light-service `CoroutineScope` injection, Kotlin UI DSL v2
reach, `DocumentationTarget`) are stable from `241` upward; the unified `intellijIdea(...)`
Gradle helper is `253`+, so a plugin staying on the legacy
`intellijIdeaCommunity(...)`/`intellijIdeaUltimate(...)` helpers can still target `241`
without issue.

`untilBuild` should be open (provider `{ null }` in 2.x or omit the attribute). A narrow
`untilBuild` flags every fresh EAP as incompatible until you republish. Only narrow it when
you know an upcoming change will break you.
