# Workspace Model

## Workspace Model — modern entity-based API

The Workspace Model is the representation underlying `Module`/`ContentEntry`/`OrderEntry`.
The `WorkspaceModel` interface and the storage/entity types below are in the stable API dumps
for IntelliJ Community `idea/2026.2.2` at commit
`1c7e601c0423e544917046c23763b15d0282e2a3`. Check the
[`WorkspaceModel` declaration](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/backend/workspace/src/WorkspaceModel.kt),
[`WorkspaceEntity` declaration](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/workspace/storage/src/com/intellij/platform/workspace/storage/WorkspaceEntity.kt),
and generated [JPS entity API](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/workspace/jps/gen/com/intellij/platform/workspace/jps/entities/ModuleEntityModifications.kt)
again when changing the minimum IDE version.

Use it for:

- suspending modifications started outside read and write locks,
- subscribing to entity-level change events (`Flow<VersionedStorageChange>`),
- contributing custom workspace entities (e.g., a non-module project structure piece).

Core types:

| Type | Role |
|---|---|
| `ImmutableEntityStorage` | A read-only snapshot of the project structure |
| `MutableEntityStorage` | A staging area for changes |
| `WorkspaceEntity` | Base for entities (`ModuleEntity`, `ContentRootEntity`, `SourceRootEntity`, `LibraryEntity`, custom subclasses) |
| `WorkspaceModel.currentSnapshot` | Cheap read access |
| `WorkspaceModel.update(description, updater)` (suspend) | Atomic asynchronous mutation; call outside locks |

Reading:

```kotlin
val storage = WorkspaceModel.getInstance(project).currentSnapshot
storage.entities(ModuleEntity::class.java).forEach { m ->
  m.contentRoots.forEach { cr -> /* cr.url */ }
}
```

For `WorkspaceModel.update`, keep the updater free of side effects because the platform may
invoke it more than once when concurrent changes race. Completion means the storage update was
applied; it does not guarantee that legacy bridges or `WorkspaceFileIndex` have caught up.
Creating JPS entities also requires a correct public `EntitySource` and complete relationships,
so do not paste placeholder constructors into production code.

Annotations on entity definitions: `@Default`, `@Child`, `@Abstract` shape the
serialization and parent-child semantics.

`SymbolicEntityId` and `ExternalMappingKey` let you track external-system associations
(e.g., mapping Gradle module ids back to `ModuleEntity`s).

The classic `ModuleManager`/`ModuleRootManager` APIs still work and are backed by the
Workspace Model under the hood. Prefer those higher-level public APIs when they cover the
operation. Use Workspace Model directly when entity-level reads, change flows, or an atomic
multi-entity update are required. Do not import `*.impl` types, generated entity implementation
classes, or entity properties annotated `@ApiStatus.Internal`.
