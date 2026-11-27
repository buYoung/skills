# Restructuring an existing project

A restructure moves many files and edits build configuration. It stays safe when each step is small, verified, and changes structure only. Before the first move, use the [toolchain mapping](../SKILL.md#2-map-the-rules-to-the-toolchain) to find out what a move breaks in this toolchain.

## Before the first move

1. **Record the baseline.** Run the project's existing build and test commands and note the result. If they fail before any change, say so: later failures cannot then be attributed to a step, and the user should decide whether to proceed. If the project cannot be built or tested in this environment, say that before the first move as well; each step is then verified only by reading the manifests and the import graph, and the report lists it under **Not verified**.
2. **Check the working tree.** Uncommitted work mixed with hundreds of moves is hard to separate. If the tree is not clean, report it and continue only on files the uncommitted work does not touch, or ask.
3. **Finish the audit.** The current layer map, the findings, and the target layer map come first. Moves made before the target is settled get repeated.
4. **Settle the user's decisions** that the plan depends on, listed in [Decisions that belong to the user](../SKILL.md#5-decisions-that-belong-to-the-user). An answer covers what was asked: an exception accepted for one edge, directory, or dependency does not extend to others of the same kind, which stay findings until the user is asked about them.

## Order of steps

Take the steps in this order by default. Earlier steps lower the risk of later ones, and each can be verified alone. Skip a step with no findings. When a later finding has to be resolved before an earlier step can be applied or can pass, move only that finding directly ahead of the step it blocks, and give the reason in **Migration steps** or **Steps applied**.

1. **Clean tree (C1–C3).** Add ignore entries and move scratch files to the ignored scratch location. Removing tracked artifacts from the index needs approval. Doing this first keeps generated files out of every later diff.
2. **Create the Layer 0 modules.** Add empty core modules to the build with their public surface in place. Nothing depends on them yet, so the build is unaffected. If shipped code sits outside every build unit, bring it into one here: code that belongs to no module belongs to no layer. Leave files that nothing builds or loads where they are, and ask the user whether to include or remove them.
3. **Move shared definitions down (S).** Move one cluster of related definitions at a time into Layer 0, delete the duplicates, and point every consumer at the single definition. Bindings and configuration schema move down whatever the number of consumers (S1). Copies that differ only in form are unified. Copies that differ in value or shape are not: choosing one changes behavior for the other side, so leave both in place, report the difference, and let the user choose. Replacing a hand-written copy in another language with a generated one (S3) adds a build step and needs approval.
4. **Remove upward edges and cycles (L1, L2, L3).** Pick the technique that fits:
   - The lower module needs a *definition* from above: move the definition down.
   - The lower module needs to *call* something above: define a contract in Layer 0, implement it above, and pass the implementation in at the Composition Root.
   - The lower module *notifies* something above: define an event or observer contract in Layer 0; the upper module subscribes.
   - Two modules reference each other throughout: they are one module. Merge them, or extract the part both need into a lower module.
   - One module mixes layers: split it along the layer line.
5. **Separate execution units (L1, L4, S4).** Give each unit its own Layer 2 module. Move construction, wiring, and the reading of environment, files, and flags out of lower modules into each Composition Root, and pass the values down as arguments. Remove references a unit does not use, splitting lower modules where a unit needs only part of one. Keep the number and lifetime of the objects as they were: where each worker or request built its own client, pass a factory so each still gets its own. Sharing one instance where there were several changes behavior and needs the user's answer.
6. **Encapsulate (E).** Work upward from Layer 0, one module at a time, and inside each module from the innermost directories outward: add the public surface, reduce visibility of everything else, and redirect deep imports to the surface. Bottom-up order means consumers are fixed against a surface that is already final.
7. **Bring resources, tests, and packaging home (R, V1, C4).** Move each resource into its owning module, switch access to the module-relative mechanism, and update packaging so the resource still ships. Add or update the publish allowlist of any module packaged by file list (C4), and check it again after step 8 if a split changes the listed paths. Move tests and fixtures beside the module they exercise, and remove references from shipped code to tests or test-support modules.
8. **Split crowded files (F).** Last, because earlier steps often move or shrink these files.
9. **Add enforcement (V2).** With approval. Adding it last means it starts from a passing state and guards what was just achieved. Confirm the new check with the negative test described under Design in SKILL.md; without it, list the enforcement under **Not verified**.

## Each step

1. State what moves and which rule it resolves.
2. Move with the version control system's move command, and keep the move free of content edits beyond what it requires. Git records no renames and recognizes one afterward only when the content is still similar, so a file moved and rewritten at once loses its history. Where the toolchain keeps a file's identity outside the file, in sidecar metadata or a project index, move those together with the file or move through the tool.
3. Update everything that names the old location (see the next section).
4. Build, run the tests, and read the dependency graph again to confirm the edge is gone.
5. If the step cannot be made to pass, undo that step only, leaving earlier steps and the user's own changes in place, and report what blocked it. Do not stack further steps on a failing one.

Keep steps separable so each can be reviewed or reverted alone, and keep a list of each step's moves for the report. Commit only when the user asks for commits.

## What breaks silently

Moves change names that compilers do not check. After each move, search the repository for the old path and old qualified name as plain text.

- Build and packaging: manifests, workspace member lists, include and exclude lists, bundler configuration, container build files, install rules.
- CI and repository settings: path filters, cache keys, code-owner files, coverage and lint configuration.
- Strings that name code: reflection, dependency-injection registration by name, dynamic imports, plugin identifiers, serialized type or namespace names, routes, log categories.
- Assets and resources: resource paths, embedded resource names (often derived from the folder path), editor asset identifiers and their metadata files.
- Generated code: generator input and output paths.
- Documentation and scripts that link to source paths.

## Compatibility

- **Published libraries.** A move usually changes the import path or type location that outside consumers use. Keep a compatibility re-export or type forward at the old location and mark it deprecated, or get approval for a breaking change.
- **Temporary shims inside the repository.** When a definition has many consumers, a re-export at the old location can keep one step small. Remove it before finishing. Any shim still present at the end goes into the report as unfinished work.
- **Namespaces and package names.** Moving a file between modules often changes its namespace or package path. Change what the move requires and nothing more.
- **Persisted data.** If a type's qualified name is stored in files, databases, or messages, moving the type changes how that data is read. Find out before moving, and keep the stored name stable.

## When to stop

Stop and report instead of continuing when the baseline does not build and the user has not said to proceed, when a step fails after one honest attempt to fix it, when ownership of a definition or resource is unclear, or when the only way forward is one of the user's decisions. Steps that do not depend on the open question can still be applied first.
