---
name: layered-module-structure
description: Use only when the user explicitly invokes this skill.
---

# Layered Module Structure

Organize a codebase as modules in three layers whose dependencies point one way. Every shared definition has one owner, every module has one public surface, resources are stored with the module that owns them, and the source tree holds only what ships. Use the same rules to design a new project, audit an existing one, restructure it, or decide where new code belongs.

The skill names no language and holds no per-language instructions. The rules describe outcomes, not file names: one toolchain reaches an outcome with an entry file that re-exports, and others reach it with visibility modifiers, build targets, or a public header directory. Apply each rule through the mechanism the project's own toolchain provides, and never copy a file convention into a language that has a different one. The mechanism changes a rule's form, never whether it applies: where a toolchain offers only a convention for something another toolchain checks at compile time, the rule still holds and rule V2 covers the gap.

**Terms.** A *module* is the smallest unit that declares its dependencies to the build system: a package, assembly, library, or build target. In a project built as one unit, the directories that divide the code by purpose play that role; a directory that only groups them into a layer is a container, not a module. Where build targets or packages select their own source files, a file belongs to the one that includes it, not to the directory it sits in; a file that sits inside another module's directory still reaches that module only through its public surface (E3). A *unit* is a module or any directory of source files inside one. An *execution unit* is anything that starts on its own: an app, CLI, service, worker, helper process, or editor tool. A *Composition Root* is the one place in an execution unit where the concrete lower modules are constructed and connected.

## 1. Settle the task

The description of this skill says nothing about the task, so read it from the invoking request: the action, the target, and whether files may change.

| The user asks to | Task | Files change |
|---|---|---|
| Set up, scaffold, or design a project or module | Design | Only when asked to create them |
| Check, review, or audit; or names no action and code exists | Audit | No |
| Apply, restructure, migrate, or fix the structure | Restructure | Yes |
| Add something, or asks where it belongs | Place | As the request requires |

- **Target.** The path the request names, otherwise the whole repository. For a request limited to one part, judge that part but include the modules it references in the layer map, because a layer has meaning only relative to the modules around it.
- **No action named.** With code present, run an Audit. With no code, the task is Design from whatever the request describes; if it describes nothing, ask what is to be built.
- **Several tasks in one request,** such as "audit and fix": run them in that order and give one report for the last, with the earlier results inside it.
- **Inferred task.** Name it in the first line of the answer so the user can redirect.

A request to restructure authorizes the moves, but not the choices listed in [Decisions that belong to the user](#5-decisions-that-belong-to-the-user).

## 2. Map the rules to the toolchain

Before judging anything, work out how this project's toolchain expresses each rule. Answer the questions below from the project's build manifests and the toolchain's own documentation, whatever the language or engine is. In Design, Audit, and Restructure, put every answer in the report's toolchain-mapping table together with its source (the manifest line, the command output, or the documentation it came from), so the user can correct it; a question that does not apply keeps its row and says why. In Place, state only the answers the placement depends on, with their sources. Check an answer by reading the manifest or running the command whenever that is possible; `unconfirmed` marks only what could not be checked.

| Question | What the answer decides |
|---|---|
| What is the smallest unit that declares its dependencies to the build system? | What a module is, and where layers can be enforced. If the whole project is one such unit, layers are directories held by an import rule |
| Does the toolchain reject dependency cycles, and at which level: build unit, package, or file? | What L2 has to check by hand or by a tool |
| What hides an implementation: access modifiers, an export list, a naming convention, a module descriptor? Does it work for a directory, and is a sub-directory a visibility scope of its own? | The form of E2, where E1 is held only by convention, and whether a split under F1 can share private state |
| Is there an entry file that re-exports? If not, what defines what consumers can see? Does moving code into a sub-directory change its qualified name, and can a re-export keep the old one? | The form of E1, and whether F1 splits into a sub-directory or sibling files |
| How does a module bundle files with itself and find them without depending on the working directory? | The form of R1 |
| How are low-level bindings declared, and can the other side of a language boundary be generated from one definition? | The form of S1 and S3 |
| Where does an executable start, and can each executable declare its own dependencies? | The Composition Root, and what L4 needs |
| Which directories receive build output, caches, and downloaded dependencies? Which generated files must stay tracked? | The entries for C1 and C3 |
| Which files or directories does the toolchain or a framework require at a fixed path? | What stays in place and is kept thin |
| Which command prints the real dependency graph, which boundaries does the project already enforce (a lint rule, an architecture test, a build check), and which tool can fail the build on a forbidden import? | The evidence for an audit, and what V2 already holds or could hold |

An answer of "the toolchain has no mechanism" does not remove a rule. The rule is then kept by convention, checked by hand or by a tool, and reported as unenforced (V2). Do not fill the gap by imitating another language's file convention.

When a finding or a move depends on how the toolchain behaves, confirm it against the version the project uses rather than from memory. A tool the project does not already have is a proposal, not a requirement.

These traps recur across toolchains. Check each one while answering:

- **Declared dependencies understate the real ones.** References can flow transitively, and shared install or include roots let code import what its manifest never declared. Compare the declarations with the actual imports.
- **Cycle checks cover one level only.** A toolchain that rejects cycles between build units usually allows them between the directories or files inside one.
- **A directory is not always a visibility boundary.** Where only the module hides things, the directory-level surface is a convention; say so in the report. E1 says how an audit reports the directories that lack one.
- **A sub-directory can be its own visibility scope.** Moving code into one then forces members that were private to be exposed across the new boundary. Hide the new unit with the toolchain's internal-visibility mechanism; where none works at the level of a directory, F1 gives the form of the split.
- **A directory can be part of a name.** Where the directory path sets the qualified name of what it holds and no entry module can re-export the contents under the old name, moving a file into a sub-directory renames its contents for every consumer, including the ones that name them in strings (see F1).
- **One entry file can join what the toolchain keeps apart.** Where the toolchain builds or loads the files of one directory into separate contexts, such as the server and client bundles of one feature, an entry module that re-exports all of them drags each context's code into the others. Such a directory gets one surface per context (E1), and one that already has them meets the rule. A different caller is not a different context.
- **Executables declared in one manifest share its dependency list.** L4 needs a separate declaration per execution unit. The exception is a toolchain that itself builds each unit from what that unit imports, such as a framework that makes a server and a client bundle from one package; judge L4 there on what each built unit contains.
- **Build flags and conditional compilation can hide an edge.** An optional integration switched on inside a lower module is still a dependency of that module. Give it its own Layer 1 module.
- **Entry modules have a cost.** One that re-exports widely or runs code when loaded slows builds and startup. Re-export only the names consumers use and keep it free of side effects.
- **A file's identity can live outside the file.** Where the toolchain keeps sidecar metadata or project index files, move them together with the file or move through the tool.
- **References can live in data.** Serialized assets, declaration files that name code as strings, registration by name, and reflection hold edges the import graph does not show. Search for them before calling a module or a reference unused, and before proposing to move, rename, or conditionally exclude code.

A repository with several toolchains, such as a native core under a managed or web front end, gets one mapping per toolchain and one layer map:

- A module in one language may sit below a module in another.
- Every boundary between languages or processes (FFI, IPC, HTTP, generated bindings) is a contract. Its definition belongs to Layer 0 on the side that owns it, and the other side is generated (S3).
- Each build system sees only its own edges. Cross-language edges appear only in binding and schema files, so list them in the layer map by hand: which side calls which native function, which service consumes which schema.

## 3. Rules

Each rule has an ID so findings can cite it.

The encapsulation and decomposition rules (E, F) judge shipped code: what is built into an execution unit or published. Tests, test support, examples, design-time previews, benchmarks, and experiments are not given entry modules or split by role unless the user asks. The other rules still reach them: where they live (V1, C2), what they may reference and what may reference them (L2, V1), and that they stay out of the shipped artifact (L4, C4).

### Layers

- **L1 — Three layers.** Every module belongs to exactly one.

  | Layer | Holds | May reference |
  |---|---|---|
  | 0 Core | Shared types, constants, error types, contracts (interfaces, message and protocol definitions), configuration schema, raw low-level bindings (FFI, native, OS declarations) | Other Layer 0 modules only, without cycles. By default nothing outside the language's standard library |
  | 1 Services | Domain services and platform integrations: storage, network, OS, engine or UI framework, device drivers | Layer 0. Another Layer 1 module only under L3 |
  | 2 Apps | One module per execution unit. Each is a Composition Root: it builds the concrete Layer 1 pieces, reads configuration values, wires everything together, and starts | Layers 1 and 0 |

  Layer 0 defines; it does not act. It performs no I/O of its own and makes no product decisions, which is what lets everything else depend on it safely. Everything above inherits whatever Layer 0 depends on, so an external dependency there is an exception that the user accepts, and one to accept only where a definition cannot be written without it: the native library a binding declares, a serialization or schema library the definitions are expressed in, an engine base type. A dependency used for behavior is an L1 finding whatever its reason. The others that nobody has accepted are reported together as one L1 finding, whose Fix names both ways out: writing the definitions without the dependency, or acceptance recorded with its reason. **Decisions needed** lists them one by one, and an accepted one goes into the layer map with its reason.

  Construction happens only at the top. Modules below Layer 2 receive what they need from other modules as arguments; they do not construct another module's implementation, look one up in a registry the project builds for itself (a singleton, a static instance), or add themselves to any global registry, the project's own or an external one, when loaded. Wiring hidden in a lower module is a dependency the Composition Root cannot see or replace.

  Where a framework owns construction through its own container or service registry, the wiring belongs with the Composition Root: in a registration function the root calls, in a declaration file the framework reads, or in a passive marker on a type or function, one that runs no project code at load and leaves the root able to replace or leave out what it marks. A lower module then receives its dependencies at the injection points the framework offers; taking them from the container in the middle of its code is a hidden lookup. The one exception is a component the framework itself instantiates without offering an injection point; code the Composition Root can construct takes its dependencies as arguments. Either way each dependency is a reference to the module that owns it, judged under L2 and L3. Layer 0 requests nothing from a container.

  Layer 2 holds no domain logic. Logic that a second execution unit could need belongs in Layer 1, because Layer 2 modules cannot share it (L3).

- **L2 — One direction.** A module references only lower layers. There is no upward reference and no cycle, at any granularity the language allows one. Developer tools (scripts and generators that are not shipped) sit outside the layers, so no shipped module references them. An upward edge means the lower module can no longer be built, tested, or reused alone, and a change above ripples back down.

- **L3 — Same-layer references keep the direction.** Layer 2 modules never reference each other: a unit that links another unit links everything that unit wires, which defeats L4. They communicate through contracts defined in Layer 0. Layer 1 modules are independent by default: when a domain service needs a platform capability, the contract lives in Layer 0, the platform module implements it, and the Composition Root passes the implementation in, so the domain builds and tests without the platform. Every direct Layer 1 → Layer 1 reference goes into the same-layer references table, whoever writes the report; in an audit that is the auditor, from what the code shows. A reference to a pure library is recorded and needs nothing more. Any other direct reference departs from that default and stands only as an exception the user has accepted. Three kinds break the direction itself and are reported one finding each: a reference that closes a cycle (L2), one that runs from a platform integration to a domain service, and one that runs from a pure library to anything but Layer 0 or another pure library. The remaining direct references that nobody has accepted are reported together as one L3 finding, whose Fix names both ways out: a Layer 0 contract, or acceptance recorded with its reason. **Decisions needed** then lists them one by one, because accepting one does not accept the rest.

  A platform integration talks to something outside the program; a domain service holds the product's rules. A Layer 1 module that does neither, such as a library of pure algorithms or data structures, is a pure library.

- **L4 — Execution units reference the minimum.** Each unit that runs separately, or with a different privilege or role, is its own Layer 2 module with its own Composition Root, and references only the lower modules it uses. Examples: client and server, UI and background worker, elevated helper and normal app, editor tooling and runtime, host and separately loaded plugin. When a unit needs part of a lower module, split that module instead of linking all of it. Whatever a privileged unit links becomes part of its attack surface, its binary, and its startup.

### Single source of truth

- **S1 — Shared definitions exist once, in Layer 0.** A type, constant, or name (event name, key, error code, route) that two modules both need, where neither may reference the other, is defined in Layer 0 and imported by both: typically two Layer 1 modules, two execution units, or the two sides of a contract. What belongs to one module's API, such as the types it takes and returns, stays in that module, and the modules allowed to reference it import it from there; that is still one definition. Raw low-level bindings and the configuration schema are defined there however many modules use them: a binding is the project's one statement of a foreign interface, and a schema is shared by construction between the Composition Root that fills it and the module that consumes it (S4). No copies, parallel declarations, or repeated literals, including a value kept both in a build manifest and in source: two copies drift, and the mismatch surfaces at run time.
- **S2 — Layer 0 stays small.** A type, constant, or name moves there only under S1 or when it crosses a process or language boundary; one that a single module uses, or that is part of one module's API, stays with that module. Group Layer 0 by topic (contracts, config, bindings) rather than one `common` or `utils` bag, and split it into separate modules when consumers need different subsets, so L4 remains possible.
- **S3 — Across languages or processes, generate.** One side holds the authoritative definition (a schema, an IDL, or one language's types), and a build step generates the other side. Generated files are never edited by hand; they are produced during the build, or committed together with a check that fails when they are stale.
- **S4 — Schema below, values above.** The configuration schema is the shape, defaults, and validation of every setting that comes from outside the program; it lives in Layer 0. A module's ordinary constructor parameters are its API, not configuration schema. Values from environment, files, flags, or remote sources are read at the Composition Root and passed down as arguments. Lower layers do not read the environment or global state. A configuration object the Composition Root loaded and hands down is passed-down configuration when the receiving module reads only its own section of it, into the Layer 0 schema type; reading another section, the process environment, a fixed path, or a global directly is not. Secrets do not live in source.

### Resources

- **R1 — Resources live with their owner.** Templates, schemas, queries, shaders, locale files, icons, fixtures, and default configuration files are stored inside the module that uses them, and reached through a module-relative mechanism: embedding, resolution relative to the module, or the build system's packaging. No path that climbs out of the module, no absolute path, no dependence on the working directory. The module then moves, packages, and tests as one piece.
- **R2 — A shared resource still has one owner.** That owner exposes the content or an accessor through its public surface, not a path.

### Encapsulation

- **E1 — One public surface per unit.** Every module, and every directory of source files inside it at any depth, exposes its API in one place: an entry module that declares the implementation files privately and re-exports chosen names, or the toolchain's equivalent where the language has no entry file. Implementation files hold the logic; the entry module only assembles, and it reaches sub-directories through their entry modules. Every entry on a surface resolves to something that exists. A directory whose files the toolchain builds or loads into separate contexts has one surface per context (section 2), and each consumer imports only the surface of its own context; that never stands in for the module split L4 requires, or for giving an optional integration its own module. Two kinds of directory have nothing to assemble: one that holds only other units and is never imported as a whole (`services/`, `apps/`), and one that holds no code (resources, fixtures, build output). Files a framework loads by location (routes, migrations, engine special folders) follow that framework's convention; project code still does not import them directly.

  Where the toolchain hides nothing below the module boundary, a directory's surface is a convention that only an import rule can hold (V2). New code still gets the surface form the language has for a directory; where the language has none, none is invented (section 2). In an existing project, the directories that lack a surface are reported together as one E1 finding, not one each. Its Fix names the ways out this toolchain has: the language's surface form together with a rule that holds it, a module boundary of their own that the build can hold, or direct imports inside the module accepted as an exception. **Decisions needed** asks which.
- **E2 — Private by default.** Whatever is not deliberately exported is hidden with the strongest mechanism the language offers. Export named items, not everything.
- **E3 — No reaching inside.** Consumers import a unit only through its public surface, never an implementation file or a directory nested inside it. Inside a unit, sibling files import each other directly rather than through their own entry module, which would create a cycle.
- **E4 — One form everywhere.** Choose one convention per language (entry-file style, re-export style) and apply it at every level of the tree, so a reader learns it once. No directory is exempt for being small, deep, or internal. Where the form has a real cost, contain the cost rather than drop the form; dropping it for some directory is a deviation the user decides. A per-context surface under E1 and a sibling-file split under F1 are forms the toolchain mapping gives, not deviations.

### Decomposition

- **F1 — Split a crowded file by role.** When one file gathers several responsibilities (event handlers, drivers, styles, commands, routes, state), split it by role in the form the toolchain mapping gives. The default is a sub-directory of the same name holding one file per role and an entry module that assembles them (E1); consumers keep the same import path wherever the language resolves a file and a directory alike, and where it does not, update them in the same step. Where the mapping shows that a sub-directory would change the qualified names of its contents with no re-export able to keep them, or would force shared private state open with no internal visibility at directory level (section 2), split into sibling files in the same directory instead, behind that directory's surface, and say so in the report.
- **F2 — Split on signals, not on length.** Signals: unrelated reasons to change, sections separated by banner comments, registration tables mixed with implementations, repeated merge conflicts, needing search to move around. Length alone is not a signal, and a file with one role is not split: a directory holding one file and an entry module is noise.
- **F3 — Group by feature or role, not by kind.** No project-wide `utils/`, `helpers/`, `types/`, or `misc/` buckets: a bucket has no owner, so it grows until everything depends on it. A helper belongs to its user; once two modules need it, the `utils` row of [Where things go](#where-things-go) says where it moves.

### Clean tree

- **C1 — Outputs stay out.** Build outputs, caches, and downloaded dependencies are written outside the source tree or ignored by version control (`.gitignore` or its equivalent).
- **C2 — Scratch stays out.** Temporary analysis, experiments, one-off scripts, logs, dumps, and profiles go to one ignored scratch location or outside the repository. An experiment worth keeping moves out of scratch and becomes an example; once its code ships, it is a real module and every rule applies.
- **C3 — Ignoring is not untracking.** A file already tracked stays tracked after an ignore rule is added; it must also be removed from the index (in Git, `git rm --cached`), which the user approves. Keep tracking what the build needs to be reproducible: lockfiles and metadata the toolchain requires.
- **C4 — Packages ship an allowlist.** Where a module is published or packaged by file list, its configuration names the files to include rather than relying on what happens to be present.

### Tests and enforcement

- **V1 — Tests stay with their module.** Tests live inside the module they test or in a test module beside it. They are its companion: same layer, free to reference it, referencing nothing above that layer, and referenced by no shipped module. They exercise it through its public surface or the language's sanctioned test access. Shared test helpers form a test-support module that shipped modules never reference. Fixtures are resources (R1).
- **V2 — Enforce boundaries mechanically.** A boundary kept only by habit erodes. Prefer boundaries the build system enforces, which means separate modules; where layers are directories inside one build unit, an import rule in lint or CI is the only thing holding them. Enforcement supports the rules and does not replace them: where none is installed, the rules still apply, the import graph is checked by reading it, and the report names the boundary as unenforced.

### Where things go

| Item | Location |
|---|---|
| Type or constant that belongs to one module, including the types of its API | That module; exported only if its consumers need it |
| Type, constant, or name that two modules both need, where neither may reference the other | Layer 0 (S1) |
| Capability a domain service needs from the platform | Contract in Layer 0, implementation in a Layer 1 platform module, wiring in Layer 2 |
| Cross-cutting capability: logging, clock, ID generation, metrics | Contract in Layer 0, implementation in Layer 1, selection and configuration in Layer 2. Where the standard library already provides the contract, use it instead of writing one |
| Variants of one capability per OS, device, or vendor | One Layer 1 platform module per variant behind the same Layer 0 contract; the Composition Root selects |
| Raw FFI or native declarations, even with one consumer | A Layer 0 bindings module, separate from the pure definitions so consumers that need no native code do not link it. A thin safe wrapper that adds no policy may sit beside it; behavior built on it is Layer 1 |
| Message, IPC, or HTTP contract between execution units | Layer 0, generated for the other side (S3) |
| Configuration structure and defaults; reading environment, files, and flags | Layer 0; Layer 2, which passes values down (S4) |
| Database schema, migrations, queries | The Layer 1 storage module that owns them (R1) |
| Reusable UI components and their styles | A Layer 1 UI module, styles beside the component |
| App shell: window or routing setup, dependency wiring, startup | Layer 2 |
| Plugin contract; discovery and loading | Layer 0; the host's Layer 2 module |
| Plugin compiled into the app; plugin built and loaded as its own artifact | Layer 1, registered by the Composition Root; its own Layer 2 module that references the contract and never the host |
| A file or directory whose location the framework or toolchain fixes (file-system routes, engine special folders, platform manifests) | Where the toolchain requires it. Keep it thin, assign it to the module it serves, and move the logic it would hold into a module |
| A `utils` module with mixed content | Split it: each helper to its only user; shared helpers that only serve Layer 0 definitions to the Layer 0 topic module that holds those definitions; a standalone library of pure algorithms or data structures, or any shared helper that needs an external dependency, to a Layer 1 pure library (L3) |
| Generated code | Written to the build directory, or committed inside the module that exposes it with a staleness check (S3) |
| Tests, fixtures, test helpers | With the module under test; shared helpers in a test-support module (V1) |
| Developer scripts and code generators | A tools directory outside the layers; shipped code never references it |
| Vendored or third-party source | Its own directory, exempt from these rules, referenced like any external dependency |

## 4. Work through the task

### Every task

1. Derive the toolchain mapping (section 2).
2. For existing code, take inventory from evidence rather than folder names: modules and their declared dependencies from the manifests, execution units from the build targets, real import edges from the toolchain, and what each Layer 0 module depends on outside the project. Prefer tools the project already has; otherwise read manifests and import statements. When a graph command would write into a tree that must not change, run it in a copy outside the tree. Two build systems that describe the same sources declare one set of modules; a difference between the two descriptions goes under **Other observations**. Record vendored, third-party, and generated code (under **Scope** in an Audit). Vendored and third-party code stays out of the judgment; generated code is judged only on how it is produced and tracked (S3, C1, C3). Leave out files this session's own tooling created as well; output that the project's own build writes unignored into the tree is different, and is C1 evidence. A source file that no build target, package, entry point, or data-held reference (section 2) includes belongs to no module: note it (under **Other observations** in an Audit), and do not use it as evidence of an edge. If the repository already holds a layer map or a list of accepted exceptions, read it: a recorded exception is not a finding, and a difference between that record and the code is.
3. Draft the layer map by assigning every module to a layer. A module that builds an execution unit or wires others is Layer 2. A module that holds only definitions is Layer 0. The rest are Layer 1. Assign a module by what it holds, not by what it references today: a definitions module with an upward reference or an external dependency is still Layer 0, and that reference is the finding (L2, L1). Developer tools, shared test-support modules, examples, benchmarks, and design-time previews sit outside the layers; mark them `outside`. A module that only extends an editor or design tool for one module is that module's companion, as its tests are: it shares the module's row, references nothing above the module's layer, and never ships with it (L4). A module that fits two layers is an L1 finding: it needs splitting. A facade that only re-exports other modules takes the layer of the highest module it re-exports. A directory that holds only the declarations of what another module implements, such as public headers or interface files, is that module's surface and not a module of its own. A project that ships only libraries has no Layer 2; do not invent an app.

### Design

Propose the layer map and a directory tree. For each module, state its public surface, where its resources live, and what it references. Add the ignore entries, and propose the enforcement mechanism (V2).

The tree has this shape. The names are placeholders: use the names the project's toolchain and community expect, and keep the shape. Where a directory name becomes part of an import path or namespace, a generic name such as `core` or `services` appears in every import and can collide with names the ecosystem already uses, so name those directories for what they hold.

```text
<root>/
  core/        Layer 0   separate modules for contracts, config, and bindings when their consumers differ
  services/    Layer 1   one module per domain service or platform integration
  apps/        Layer 2   one module per execution unit
  tools/                 developer scripts and generators; shipped code never references them
```

Build output and scratch work sit outside this tree or under ignored directories.

Scale the mechanism to the project, never the rules. A small project with one execution unit can keep the three layers as top-level directories in a single build unit, held by an import rule; the directories inside each layer are its modules, and every rule still applies to them, L3 included. Use separate modules once there is more than one execution unit, a difference in privilege, or a part reused elsewhere: L4 needs each unit to declare its own references, and separate modules are what lets the toolchain enforce the boundary.

When asked to create files, create the smallest skeleton that builds: manifests, entry modules, ignore file. Add no placeholder logic. Then build it once and read the dependency graph back from the toolchain; if the toolchain is not available, say the skeleton is unverified. An enforcement check counts as working only after it has rejected a real forbidden reference: add an import of an existing name across a forbidden boundary in a file the build includes, confirm that the build or the rule rejects it for that reason and not for a syntax or missing-name error, then remove it and confirm a clean pass. Work in a copy outside the source tree when the tree must stay untouched. A skeleton with no imports passes every check, so without this negative check report the enforcement as unverified.

### Audit

Check every rule and report each violation with evidence: the manifest line, import statement, or path that shows it. The toolchain mapping names the commands; this is what to collect.

| Rule | Evidence |
|---|---|
| L1 | Modules that mix layers; domain logic in a Layer 2 module; below Layer 2, construction of another module's implementation, registration at load, and registry or container lookups; external dependencies of Layer 0 modules |
| L2 | Each module's declared dependencies and actual imports against its layer, including edges the manifests do not declare and edges held in data or across languages; upward references; cycles between modules, between the directories inside one, and between files where the language allows them; shipped modules that reference developer tools |
| L3 | Layer 2 → Layer 2 references; every direct Layer 1 → Layer 1 reference, for the same-layer references table |
| L4 | Everything each execution unit links or bundles, transitively, against what its own code and its data-held references use; execution units that share one dependency declaration |
| S1 | The same type, constant, or literal (key, event name, error code, route) declared in more than one module; the same value kept in a build manifest and in source; bindings or configuration schema outside Layer 0 |
| S2 | Layer 0 items that only one module uses, other than bindings, configuration schema, contracts that cross a process or language boundary, and what a published module offers outside the repository; a mixed `common` or `utils` bag inside Layer 0 |
| S3 | A hand-written mirror of another language's or process's definition; generated files edited by hand, or committed without a staleness check |
| S4 | Below Layer 2: reads of the process environment, flags, fixed configuration paths, remote configuration, or global state; reading another module's section of a handed-down configuration object, or reading into a type that is not the Layer 0 schema; secrets in source |
| E1–E4 | In shipped code: source directories without a surface, entry modules that hold logic, and surface entries that point at nothing (E1); wildcard re-exports, and items on a unit's surface that no code or data-held reference outside the unit uses, other than what a published module offers outside the repository (E2); imports that name a file or nested directory inside another unit (E3); more than one surface form within one language (E4) |
| R1, R2 | Path strings that climb out of the module, are absolute, or depend on the working directory, and resources stored outside their owner (R1); a shared resource handed out as a path (R2) |
| F1–F3 | In shipped code: files that show the F2 signals (F1, F2); project-wide kind buckets such as `utils` (F3) |
| C1–C4 | Outputs, caches, or downloaded dependencies that are neither ignored nor outside the tree (C1); scratch files in the tree (C2); tracked files that the ignore rules match, in Git `git ls-files -ci --exclude-standard` (C3); a module packaged by file list without an allowlist (C4) |
| V1, V2 | Tests that live away from their module, reference above its layer, or go around its public surface without sanctioned test access; shipped code that references tests or a test-support module (V1); which boundaries the build or a lint rule holds, and which nothing holds (V2) |

Run every check in the table as a search over the whole target, not a reading of sampled files, and list each check that was not run under **Not checked**. Take every line number from line-numbered search or file output, and every count from complete command output in this session; leave out a number that cannot be reproduced that way.

Sort findings by rule ID in this order, whatever order they were found in: L1, L2, L3, L4, S, E, R, F, C, V. A finding that cites two rules is placed by whichever comes earlier in this order. The order runs from what constrains everything else to what constrains least. When a violation fits two rules, cite the more specific one: a cycle or an upward edge is L2 whichever layers it joins; a mixed bag is S2 inside Layer 0 and F3 elsewhere; a shipped reference to tests or test support is V1.

Do not report a rule as broken when the toolchain satisfies it in a different form, and do not report style preferences. A real defect that no rule covers goes under **Other observations**, not under a borrowed rule ID.

Check each Fix against the toolchain mapping before writing it: which mechanism of this toolchain carries it out, what would have to become more visible, which data-held references and path-based wiring it breaks, and whether it adds an edge or brings an external dependency into Layer 0. State the mechanism in the Fix, together with whichever of the others apply, and say so when the mechanism is unconfirmed.

An audit changes no files; it closes with the target structure and the migration steps that reach it, in the step order of [references/restructuring.md](references/restructuring.md), so the user can ask for a Restructure. The target keeps the project's existing layout wherever that layout already carries the layers, and moves a directory only when a rule requires it.

### Restructure

Read [references/restructuring.md](references/restructuring.md) first. In short: audit, plan ordered steps that each leave the build and tests passing, then apply one step at a time. Change structure only. A restructure that also changes behavior, renames things beyond what a move requires, or cleans up opportunistically cannot be verified by "it still works the same."

### Place

Decide with the table in [Where things go](#where-things-go). Name every execution unit the new code runs in and, when there is more than one, the contract between them: a definition two units share is declared once, in Layer 0. Then follow the conventions the project already uses for that layer, as far as they satisfy the rules. Where an existing convention breaks one, such as a kind-named bucket or a directory that mixes layers, do not extend it silently: give the location the rules require and the location the convention would give, name the rule that separates them, and use the first unless the user chooses the second. New code follows every rule from the start: exposed through its unit's public surface, its resources beside it, no new upward edge. If the right place requires a structural change, such as a shared type that must move down, say so and make that change part of the work.

## 5. Decisions that belong to the user

Proceed without asking on everything else. In Design and Audit, list these under **Decisions needed** and continue on a stated assumption. In Restructure and Place, do not carry out the affected step until the user has answered; steps that do not depend on the open question can still go ahead.

- A layer assignment that is ambiguous and would reverse the direction of a dependency.
- An external dependency in a Layer 0 module (L1).
- Which copy wins when duplicates of a shared definition differ in value or shape. Unifying them changes behavior for one side.
- Changing the public API or import paths of a library published outside the repository.
- Deleting files whose content is not preserved elsewhere, or removing tracked files from version control.
- Adding tools, dependencies, or CI steps, including enforcement (V2) and generators (S3).
- Splitting or merging modules in a way that changes what gets deployed or released.
- Keeping a deviation, including a direct Layer 1 → Layer 1 reference (L3) and direct imports inside a module where a directory's surface would be convention only (E1): when a rule cannot be met without disproportionate cost, present the cost and let the user decide, then record the exception in the layer map or, for a same-layer reference, in that table. Until the user accepts it, a deviation is a finding. An acceptance covers what was asked: accepting one edge, directory, or dependency does not extend to others of the same kind.

## 6. Report

Use the template for the task from [references/report-templates.md](references/report-templates.md). Design, Audit, and Restructure reports include the full layer map, because it is the one artifact that makes the structure checkable later; a Place answer includes only the rows it adds or changes.

Write the layer map into the repository only when the user asks for a written record; otherwise the manifests and enforcement configuration are the record. Accepted exceptions are the one thing those cannot hold. When the map carries one, say that it exists only in the report and offer to keep it where the next audit will find it: an allow entry with its reason in the enforcement configuration, or a short structure document.
