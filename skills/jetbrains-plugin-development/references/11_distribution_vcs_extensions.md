# VCS Extensions

## VCS plugin extensions

The VCS API is large. Common extension points for
plugins integrating with a VCS not yet supported:

- `AbstractVcs` — main VCS implementation entry.
- `ChangeProvider` — feeds Local Changes view.
- `VcsDirtyScopeManager` — drives "what to recompute".
- `ContentRevision` / `FilePath` / `VcsRevisionNumber` — content addressing.
- `VcsRoot` / `VcsRootChecker` — discovery.
- Show diff/merge requests through public `DiffManager` methods, including `showMerge`;
  use `createRequestPanel` for an embedded diff panel. Do not subclass or call
  `MergeRequestProcessor`: it is `@ApiStatus.Internal` in the pinned 2026.2.2 source.

For plugins layered on top of an existing VCS (e.g., adding a Git workflow on top of the Git
plugin), usually you extend the Git plugin's EPs via `<depends optional config-file>` rather
than implementing a new `AbstractVcs`.

Check each chosen VCS EP and member against its target-version declaration and metadata;
an existing Git implementation is behavioral evidence, not permission to reuse its internals.

Pinned evidence: [DiffManager](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/diff-api/src/com/intellij/diff/DiffManager.java)
exposes the public display/panel methods;
[MergeRequestProcessor](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/diff-impl/src/com/intellij/diff/merge/MergeRequestProcessor.java)
is internal. Verify the selected public method on the minimum supported branch too.

The VCS implementation route is backed by public
[`AbstractVcs`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/vcs-api/src/com/intellij/openapi/vcs/AbstractVcs.java)
and its `StartedActivated` base, plus public
[`ChangeProvider`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/vcs-api/src/com/intellij/openapi/vcs/changes/ChangeProvider.java).
The `vcs` and `vcsRootChecker` declarations in
[`VcsExtensionPoints.xml`](https://github.com/JetBrains/intellij-community/blob/1c7e601c0423e544917046c23763b15d0282e2a3/platform/vcs-impl/resources/META-INF/VcsExtensionPoints.xml)
are dynamic and not marked internal. This does not authorize all members of `AbstractVcs`:
its internal `getCustomConvertor` and `filterUniqueRoots` must not be used.
