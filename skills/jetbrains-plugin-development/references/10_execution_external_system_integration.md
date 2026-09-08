# External System Integration

Most language ecosystems use external build tools (Gradle, Maven, Cargo). The IDE's
External System framework provides a generic plumbing for "import project structure from
build system X". Use this when your plugin imports project structure from an external
build or dependency tool.

## Gradle/Maven-style importers

### Core types

| Type | Role |
|---|---|
| `ExternalSystemManager<S, T, M, C, X>` | The integration entry point |
| `ProjectResolver` | Builds the project structure tree as `DataNode<ProjectData>` |
| `DataNode<T>` | Tree node carrying typed data (`ProjectData`, `ModuleData`, `LibraryData`, custom) |
| `Key<T>` | Discriminator for `DataNode` payloads |
| `ProjectDataService<E, I>` | Applies a `DataNode<E>` to the IDE project (creates modules, libs, etc.) |
| `ExternalSystemProjectAware` / `ExternalSystemProjectTracker` | Describe tracked files / register the descriptor and schedule re-import |

Implement `ExternalSystemProjectAware` for the integration's tracked settings. Obtain
[`ExternalSystemProjectTracker`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/external-system-api/src/com/intellij/openapi/externalSystem/autoimport/ExternalSystemProjectTracker.kt)
from the project and call it; the tracker is `@ApiStatus.NonExtendable` in `idea/2026.2.2`, so
plugins must not implement or subclass it.

### Skeleton

```kotlin
class MyExternalSystemManager : ExternalSystemManager<MySettings, MyListener, MySettings, MyLocalSettings, MyExecutionSettings> {
  override fun getSystemId(): ProjectSystemId = ProjectSystemId("MyBuildTool")
  override fun getProjectResolverClass(): Class<out ExternalSystemProjectResolver<MyExecutionSettings>> =
    MyProjectResolver::class.java
  override fun getTaskManagerClass(): Class<out ExternalSystemTaskManager<MyExecutionSettings>> =
    MyTaskManager::class.java
  // ... and a few more accessors
}
```

```xml
<externalSystemManager implementation="com.example.MyExternalSystemManager"/>
```

### Import flow

1. The user "Reload" or open imports a project.
2. `ProjectResolver.resolveProjectInfo` builds a `DataNode<ProjectData>` tree off-thread.
3. The platform walks the tree; for each `DataNode`, it finds matching `ProjectDataService`
   implementations and calls `importData` (Write Action) to materialize modules, libraries,
   etc.
4. `ExternalSystemProjectTracker` watches build files; when they change, it triggers
   re-import.

For most plugins, the right move is to extend Gradle (`org.jetbrains.plugins.gradle`) or
Maven (`org.jetbrains.idea.maven`) plugins via their EPs rather than building a brand-new
external system.
