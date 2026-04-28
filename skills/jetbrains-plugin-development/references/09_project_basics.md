# Project Basics

Read this when plugin code needs the current `Project`, must distinguish a real project
from the default project, or needs project open/close basics. Use
`09_project_modules_roots_file_index.md`, `09_project_libraries_sdks_facets.md`, `09_project_workspace_model.md`, and
`09_project_view.md` for project-structure details.

## `Project`

The top-level container.

```kotlin
val project: Project? = e.project                    // from action context
@Service(Service.Level.PROJECT)
class MyService(private val project: Project)        // injected
psiElement.project; editor.project                   // from PSI / editor
// VirtualFile has no inherent project — resolve via ProjectFileIndex (below)
```

Common methods:

```kotlin
project.name
project.basePath          // String? — root path; null on default project
project.projectFile       // .ipr or .idea/misc.xml
project.workspaceFile     // .iws or .idea/workspace.xml
project.isOpen / project.isDisposed
project.getService(...)
project.messageBus
```

`ProjectManager.getInstance()`:

```kotlin
val pm = ProjectManager.getInstance()
pm.openProjects                       // Array<Project>
pm.defaultProject                     // template / settings store, NOT a real project
pm.addProjectManagerListener(listener, parentDisposable)
```

`defaultProject` is the IDE-wide template; do not use it as a substitute for a real open
project. Many APIs reject it.

Project open/close events come from `ProjectManagerListener` (declarative listener
preferred — see `02_runtime_services.md`).
