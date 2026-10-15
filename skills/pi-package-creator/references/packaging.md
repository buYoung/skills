# Package layout, discovery, and dependencies

Read this for every package. It covers the directory layout, the `pi` manifest, how Pi discovers each resource type, how users' settings filters interact with the manifest, and where dependencies belong. The rules describe the Pi revision recorded in [evidence](evidence.md). [`assets/starter/`](../assets/starter/README.md) is the complete four-resource example.

## Choose a distribution shape

```text
pi-workspace-kit/
├── package.json
├── README.md
├── extensions/
│   └── index.ts
├── lib/
│   └── workspace.ts
├── skills/
│   └── acme-orient/
│       ├── SKILL.md
│       └── references/output.md
├── prompts/
│   └── acme-focus.md
└── themes/
    └── acme-midnight.json
```

- Every resource type is optional. A skill-only package needs its skill tree, not an extension wrapper.
- Add a manifest when you need explicit discovery or the delivery source requires one. A local directory can work without `package.json` through conventional discovery; npm distribution requires a valid npm package.
- Include `version` for npm. Pi identifies a package by name, not version, but compares the installed copy's version with the configured spec. Without a version, every resolution reinstalls the package.
- `type: module`, a `files` allowlist, package-prefixed names, and exact third-party dependency versions are recommended authoring defaults, not Pi schema requirements. Choose a real publishing name, license, and repository metadata before publishing.

### Declare extension entry points explicitly

Declare extensions through `pi.extensions` or an `extensions/` directory. When a local directory has no `pi` manifest and no conventional resource directory, Pi falls back to loading the directory itself as one extension through its root `index.ts` or `index.js`. Only a local string entry uses that fallback. npm and git installs of the same files, and object entries such as those `pi config` writes, load nothing and report no diagnostic.

## Manifest contract

`package.json.pi` has four runtime fields: `extensions`, `skills`, `prompts`, and `themes`. Pi accepts a field only when its value is an array of strings.

| Input | Pi's behavior |
|---|---|
| No `pi`, or `pi` is `null`, an array, or a string | No manifest; conventional discovery applies |
| `"pi": {}` | Manifest present but empty; a string entry loads no resources |
| `"extensions": "./index.ts"` | Field silently discarded |
| `"extensions": ["./index.ts", 42]` | Entire field silently discarded |
| Valid array of paths | Pi discovers those resources |
| Broken `package.json` | Manifest reading falls back; a later extension-package inspection can throw and prevent startup |

Manifest paths are relative to the package root. Pi does not reject `..` paths that escape the root, but write portable paths that stay inside the package. Missing paths disappear silently, so verify every path in the packed artifact.

- Exact file entries do not get the same suffix filtering that directory traversal applies. Prefer `.ts`/`.js` extension entries for predictable behavior.
- Exact directory entries run that resource type's directory collector.
- Entries containing `*` or `?` expand with Node's `globSync`.
- Glob discovery excludes path components that start with a dot. List a hidden or symlinked resource root directly when traversal cannot reach it.
- Entries beginning with `!`, `+`, or `-` filter discovered candidates; they do not add source roots.
- `pi.image`, `pi.video`, and npm `keywords: ["pi-package"]` are gallery metadata. They are not local loading requirements and do not guarantee a gallery listing.

## Discovery rules

### Extensions

For each scanned directory, Pi tries entry points in this order and stops at the first success:

1. A nonempty `pi.extensions` list in that directory's own `package.json` that resolves to existing paths. This lookup uses **literal paths**, not glob or exclusion syntax.
2. `index.ts`, then `index.js`.

A directory entry found this way hides sibling files. Without one, Pi collects:

1. Direct `.ts` and `.js` files.
2. Child directories, one level deep, that have their own package or index entry.

Pi does not search deeper. `.mjs`, `.cts`, and `.tsx` files are not discovered automatically. `types.d.ts` and `example.test.ts` match the `.ts` suffix and can become broken extension candidates.

Use explicit top-level manifest file entries, or a single `extensions/index.ts` that imports helpers from `lib/`. Do not assume that `extensions/index.ts` and `extensions/other.ts` both load automatically.

### Other resources

| Resource | Discovery in a package directory |
|---|---|
| Skills | At a directory with `SKILL.md`, take that file and stop descending. Otherwise take root `.md` files and recurse for child `SKILL.md` files. |
| Prompts | Recurse for `.md` files; the command name is the basename, without parent directories. |
| Themes | Recurse for `.json` files; the public name comes from the JSON `name`. |

### Excluded files

- Traversal normally skips dot entries and `node_modules`.
- Pi reads the ignore files `.gitignore`, `.ignore`, and `.fdignore` inside the traversal root and its descendants. The package-root `.gitignore` does not filter a scan rooted in `extensions/`.
- Keep drafts outside discovered roots, or exclude them explicitly.

Realpath deduplication removes repeated paths. It does not stop different files from registering the same public name.

## Manifest versus user filters

The manifest describes the author's resources. Entries in `settings.json` `packages` select resources from an installed package. A settings entry is either a **string entry** such as `"npm:@example/pi-workspace-kit@0.1.0"` or an **object entry** with a `source` and optional per-type filters:

```json
{
  "packages": [
    {
      "source": "npm:@example/pi-workspace-kit@0.1.0",
      "extensions": ["extensions/index.ts"],
      "skills": [],
      "prompts": ["prompts/acme-focus.md"]
    }
  ]
}
```

The two forms do not treat the manifest the same way:

| Manifest field | String entry | Object entry, user field omitted | Object entry, nonempty user filter |
|---|---|---|---|
| Nonempty paths | Manifest | Manifest | Manifest candidates, then user filter |
| Omitted | None, when a manifest exists | Conventional directory | Conventional directory |
| `[]` | None | None | Conventional directory |

Under normal autoload, a **user** field `[]` disables the whole resource type. Do not confuse it with a **manifest** field `[]` or with an empty array in delta mode.

So when you use a manifest:

1. Declare actual paths for every provided type.
2. Prefer `[]` to document unused types. Omitting a type is valid when its conventional directory cannot expose unintended resources.
3. Do not leave an unused conventional directory with candidate files. A filter can expose its files even when the manifest field is `[]`.

The same principle applies to npm `files`: exclude examples and development fixtures that discovery would pick up in a released package.

### Pattern precedence under normal autoload

Patterns apply in phases, not left to right:

1. Ordinary paths and globs include matching candidates. Without any ordinary include pattern, all candidates start included.
2. `!glob` excludes matches.
3. `+path` includes one exact path.
4. `-path` excludes one exact path; this phase wins.

Ordinary patterns can match the package-relative path, the basename, or the absolute path. Skill patterns can also match the skill's parent directory. `+` and `-` are exact path operations, not globs. A list containing only `+path` does **not** narrow the selection to that path.

Manifest filtering runs first. When a nonempty manifest supplies the candidates, a user `+path` cannot bring back an item that the manifest excluded.

### Delta mode: `autoload: false`

An entry with `autoload: false` uses a different, sequential algorithm:

- It changes only explicit matches and does not enable anything by itself.
- Ordinary and `+` patterns enable; `!` and `-` patterns disable.
- The **last matching pattern wins**. For example, `["-extensions/index.ts", "+extensions/index.ts"]` enables that entry.
- An empty array or an omitted field changes nothing.

A project entry in this form modifies the personal package selection instead of replacing it, so untouched selections stay as they were. `autoload` belongs in settings entries, not in package manifests.

`pi config` changes how settings are written. A personal toggle can turn a string entry into an object entry, which stays an object after you re-enable the resource. Project overrides can use `autoload: false` deltas. Verify the resulting enabled resources, not whether the settings text returns to its original form.

## Dependencies and module identity

Only host packages that the code imports need `"*"` peer declarations:

```json
{
  "peerDependencies": {
    "@earendil-works/pi-coding-agent": "*",
    "typebox": "*"
  },
  "dependencies": {
    "ms": "2.1.3"
  }
}
```

The `ms` dependency only illustrates the shape; do not add it unless the code uses it. The host packages are `@earendil-works/pi-ai`, `@earendil-works/pi-agent-core`, `@earendil-works/pi-coding-agent`, `@earendil-works/pi-tui`, and `typebox`.

| Dependency kind | Place | Reason |
|---|---|---|
| Imported Pi host API | `peerDependencies` with `"*"` | Pi supplies and maps its runtime |
| Third-party runtime library | `dependencies` | Must exist in production installs |
| Compiler, typings, development tools | `devDependencies` | Not needed at runtime |
| Host API copy for local type checking | `devDependencies`, optionally | Pin it to the target API; do not bundle it |

Keep host packages out of runtime `dependencies` and out of a compiled extension bundle. When physical copies exist, native ESM imports can bypass Pi's module mapping and produce duplicate classes and registries. Pi reports this configuration as a warning, not as a universal startup rejection. The warning also recognizes the legacy `@mariozechner/*` host names and `@sinclair/typebox`.

Import only package roots and the public subpaths that the target version supports. At this revision, Pi maps selected entry points, including `@earendil-works/pi-ai/compat`, `@earendil-works/pi-ai/oauth`, `@earendil-works/pi-ai/providers/all`, `typebox/compile`, and `typebox/value`. A mapped root does not make arbitrary subpaths such as `@earendil-works/pi-ai/dist/...` available.

Do not rely on another installed package's undeclared dependencies or on shared module globals. npm installs share a scope's `node_modules` tree, but that is not a contract for sharing singletons. Use `pi.events` to communicate between extensions.

## Installation behavior

- **Peers:** Pi's managed installs turn off automatic peer resolution, so a third-party library declared only as a peer may be missing.
- **Development dependencies:** git installs use production dependencies (`npm --omit=dev --legacy-peer-deps`, or the equivalent pnpm or Bun options). A `prepare` build that needs a development-only compiler is therefore unreliable.
- **Lifecycle scripts:** Pi passes `--ignore-scripts` only when it updates Pi itself, never for package installs. npm and git sources can run the install scripts of the package and of its dependencies. Git sources run the package manager's install inside the cloned package root, so root-only scripts such as npm's `prepare` can also run there.
- **Local sources:** Pi neither installs nor copies them. Install their external dependencies yourself.

So prefer one of these:

- Ship `.ts` that Pi can load directly, including its local imports.
- Build before publication and ship runnable output plus its assets.

Do not require install-time setup when the package can ship ready to load. Document any script behavior you cannot avoid.

## Reusing another Pi package

Installing a dependency does not load that dependency's Pi resources. To re-export its resources deliberately:

1. Declare the other package as a runtime dependency.
2. Bundle it into the published tarball, for example through npm `bundleDependencies`.
3. Name its resource directories under `node_modules` explicitly in `pi`.
4. Inspect the tarball to prove those paths exist.

```json
{
  "dependencies": { "pi-shared-resources": "1.0.0" },
  "bundleDependencies": ["pi-shared-resources"],
  "pi": {
    "extensions": [],
    "skills": ["./node_modules/pi-shared-resources/skills"],
    "prompts": [],
    "themes": []
  }
}
```

This composition pattern is optional, and it is not a reason to bundle Pi's host APIs. Keep the dependency's license and public names explicit.
