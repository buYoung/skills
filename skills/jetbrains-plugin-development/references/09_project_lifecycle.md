# Project Lifecycle

## Project lifecycle hooks

| Hook | Use |
|---|---|
| `StartupActivity.DumbAware` (`<postStartupActivity>`) | Run code after project open, in dumb-friendly form |
| `ProjectActivity` (`<postStartupActivity>` for new entries) | Coroutine equivalent |
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
