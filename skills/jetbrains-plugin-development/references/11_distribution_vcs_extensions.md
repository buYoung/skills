# VCS Extensions

## VCS plugin extensions

The VCS API is large. Common extension points for
plugins integrating with a VCS not yet supported:

- `AbstractVcs` — main VCS implementation entry.
- `ChangeProvider` — feeds Local Changes view.
- `VcsDirtyScopeManager` — drives "what to recompute".
- `ContentRevision` / `FilePath` / `VcsRevisionNumber` — content addressing.
- `VcsRoot` / `VcsRootChecker` — discovery.
- Diff / merge tools: `DiffViewer`, `MergeRequestProcessor`.

For plugins layered on top of an existing VCS (e.g., adding a Git workflow on top of the Git
plugin), usually you extend the Git plugin's EPs via `<depends optional config-file>` rather
than implementing a new `AbstractVcs`.
