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
| `ExternalSystemProjectAware` / `Tracker` | "this build file changed; re-import" |

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
