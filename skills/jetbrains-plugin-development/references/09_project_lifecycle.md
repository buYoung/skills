# Project Lifecycle

## Project lifecycle hooks

| Hook | Use |
|---|---|
| `ProjectActivity` (`<postStartupActivity>`) | Run code after project open, as a suspending function. Use it for new code |
| `StartupActivity` / `StartupActivity.DumbAware` (`<postStartupActivity>`) | Obsolete in favor of `ProjectActivity`. Keep only for existing Java implementations, which cannot implement a suspending function |
| `ProjectManagerListener` | open/close events |
| `ModuleListener` | module add/remove |
| `ModuleRootListener` | content roots changed |

`ProjectActivity` example:

```kotlin
class MyStartup : ProjectActivity {
  override suspend fun execute(project: Project) {
    // ... runs after project open, on a coroutine, off EDT
  }
}
```

```xml
<postStartupActivity implementation="com.example.MyStartup"/>
```

`StartupActivity.Background` (`<backgroundPostStartupActivity>`) is deprecated; replace it
with a `ProjectActivity`. Early application-startup hooks are not available to plugins:
2026.3 removed the internal `ApplicationLoadListener` and points to `ProjectActivity` instead.

Status checked at `idea/2026.3`, commit `c91871ae2864649d952825cff72569e3db0e7ac6`:
[`StartupActivity.kt`](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/core-api/src/com/intellij/openapi/startup/StartupActivity.kt)
and the EP declarations in
[`intellij.platform.core.xml`](https://github.com/JetBrains/intellij-community/blob/c91871ae2864649d952825cff72569e3db0e7ac6/platform/core-api/resources/intellij.platform.core.xml).
See also [Plugin Components: Project Open](https://plugins.jetbrains.com/docs/intellij/plugin-components.html#project-open)
and the [2026 API changes](https://plugins.jetbrains.com/docs/intellij/api-changes-list-2026.html).
