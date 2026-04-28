# Workspace Model

## Workspace Model — modern entity-based API

The Workspace Model (`platform/backend/workspace/src/WorkspaceModel.kt`) is the new
representation underlying `Module`/`ContentEntry`/`OrderEntry`. Use it for:

- async modifications under Write Action,
- subscribing to entity-level change events (`Flow<VersionedStorageChange>`),
- contributing custom workspace entities (e.g., a non-module project structure piece).

Core types:

| Type | Role |
|---|---|
| `ImmutableEntityStorage` | A read-only snapshot of the project structure |
| `MutableEntityStorage` | A staging area for changes |
| `WorkspaceEntity` | Base for entities (`ModuleEntity`, `ContentRootEntity`, `SourceRootEntity`, `LibraryEntity`, custom subclasses) |
| `WorkspaceModel.currentSnapshot` | Cheap read access |
| `WorkspaceModel.update(description, updater)` (suspend) | Atomic mutation |

Reading:

```kotlin
val storage = WorkspaceModel.getInstance(project).currentSnapshot
storage.entities(ModuleEntity::class.java).forEach { m ->
  m.contentRoots.forEach { cr -> /* cr.url */ }
}
```

Updating (suspend variant):

```kotlin
WorkspaceModel.getInstance(project).update("Add module") { storage ->
  storage.addEntity(ModuleEntity(name = "new", entitySource = ..., dependencies = listOf(...)))
}
```

Annotations on entity definitions: `@Default`, `@Child`, `@Abstract` shape the
serialization and parent-child semantics.

`SymbolicEntityId` and `ExternalMappingKey` let you track external-system associations
(e.g., mapping Gradle module ids back to `ModuleEntity`s).

The classic `ModuleManager`/`ModuleRootManager` APIs still work and are backed by the
Workspace Model under the hood. New code that does heavy structure mutations should target
the Workspace Model directly; small reads can stay on the classic API.
