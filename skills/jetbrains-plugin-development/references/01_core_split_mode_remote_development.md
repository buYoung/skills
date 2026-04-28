# Split Mode and Remote Development

Read this when a plugin must work well in JetBrains Remote Development, Code With Me-like
split architecture, frontend/backend module separation, or remote-development latency.

## Mental model

Split Mode runs the IDE frontend and backend as separate processes. The frontend renders UI
and handles latency-sensitive interactions. The backend owns the project model, indexing,
analysis, execution, and heavy work. In a monolithic IDE, both sides run in one process, so a
split plugin should still work locally.

Do not assume plugin code always runs near the project files or always has local UI access.
Place code according to the API it needs.

## Module placement

A split plugin normally has shared, frontend, and backend modules. Shared code defines
serializable contracts. Frontend code renders UI and calls backend services. Backend code
performs project, PSI, indexing, execution, and file-system work. Communication goes through
the platform RPC model and serializable data.

The platform determines loadability from module dependencies such as frontend and backend
platform modules. Missing dependencies can cause only part of a plugin to load.

## Gradle and sandbox

Split Mode requires IntelliJ Platform Gradle Plugin 2.x. Use the current official property
names for the target branch; the split-mode configuration has changed across 2.x releases.
The modern docs use `pluginInstallationTarget` for choosing backend, frontend, or both.

Use generated Split Mode run configurations or split-mode testing tasks to run frontend and
backend processes locally. Emulate latency before calling the feature remote-ready.

## Feature routing

Many language features can remain backend-oriented: inspections, annotators, quick fixes,
intentions, completion contributors, references, run configurations, Find Usages, and inlays.
UI-heavy or typing-sensitive features need extra care because backend-rendered UI can feel
slow through the frontend.

## Diagnostics checklist

1. Identify whether each class needs project/index state, UI rendering, or shared RPC data.
2. Confirm content module dependencies make the module load on the intended side.
3. Confirm all RPC data is serializable and does not carry PSI, VFS, Swing, or service
   objects across the boundary.
4. Run the sandbox in Split Mode, not only normal `runIde`.
5. Emulate latency and check typing, popups, dialogs, and tool windows.

## Official docs

- https://plugins.jetbrains.com/docs/intellij/split-mode-for-remote-development.html
- https://plugins.jetbrains.com/docs/intellij/configuring-split-mode.html
- https://plugins.jetbrains.com/docs/intellij/plugin-management-in-split-mode.html
- https://plugins.jetbrains.com/docs/intellij/remote-procedure-calls.html
