# Project Model Diagnostics

## Common mistakes

- Treating `ProjectManager.getInstance().defaultProject` as a real project. Use the open
  projects list.
- Storing `Project` references on application-level state. They become invalid on close.
- Editing `ModuleRootManager` outside a Write Action. Throws.
- Not calling `model.commit()` (or not calling `model.dispose()` on failure). Leaks the
  modifiable snapshot.
- Iterating `ProjectFileIndex.iterateContent` from the EDT for huge projects. Move to a
  background thread inside a Read Action.
- Ignoring `isExcluded` and traversing into excluded directories.
- Not implementing `DumbAware` on a `StartupActivity` that doesn't need indexes — it then
  blocks until indexing finishes.

## Related references

- `09_project_lifecycle.md` — `ProjectManagerListener`, `ModuleListener`, and `ModuleRootListener`.
- `09_project_modules_roots_file_index.md` — `ProjectFileIndex` and module root APIs.
- `10_execution_external_system_integration.md` — Gradle/Maven-style project imports.
