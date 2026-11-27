# Monorepo Detection Specification

Defines the method for identifying if the current repository is a monorepo.

## Detection Logic

A repository is considered a monorepo if **any** of the following marker files or configurations exist in the root directory.

**Provisional result**: marker detection alone is not conclusive. After discovering packages (see [Workspace Package Discovery](#workspace-package-discovery)), if fewer than 2 packages exist, treat the repository as a single document regardless of markers — a marker can be present in single-package layouts (e.g., a single-app Gradle build, or a `[workspace]` table used to detach a crate).

### JavaScript / TypeScript Ecosystem

- **`pnpm-workspace.yaml`**: pnpm workspaces
- **`lerna.json`**: Lerna
- **`nx.json`**: Nx
- **`turbo.json`**: Turborepo
- **`rush.json`**: Rush
- **`.moon/workspace.*`**: moonrepo. moon v2 accepts `.yml`, `.yaml`, `.json`, `.jsonc`, `.toml`, `.hcl`, and `.pkl`; moon v1 read only `.yml` and `.pkl`
- **`package.json`** with a top-level `workspaces` field (matched as a JSON key, not a substring): npm/Yarn workspaces

### JVM Ecosystem (Gradle / Maven)

- **`settings.gradle.kts`** or **`settings.gradle`** declaring **2+ included projects** or any `includeBuild(`: Gradle multi-project / composite build. Comments are ignored; a single `include ':app'` (the standard single-app Android layout) is **not** a monorepo
- **Root `pom.xml`** with a `<modules>` or `<subprojects>` section outside XML comments: Maven multi-module project. POM model 4.1.0 (Maven 4) introduces `<subprojects>` and deprecates `<modules>`, which remains the Maven 3 form. Maven 4 can also discover subprojects without either section, from direct subdirectories that contain `pom.xml` when the parent has `pom` packaging; the detector does not report that case, so inspect such a parent POM explicitly

For Gradle, count distinct literal project paths across complete `include(...)` declarations, including multiline argument lists and trailing commas, as well as Groovy's unparenthesized `include '…', '…'` form. Treat `app` and `:app` as the same path. Ignore comments and declaration examples inside quoted strings; repeated paths and commas alone do not add projects. `includeBuild(...)` and Groovy's unparenthesized equivalent remain provisional composite-build markers. This is static detection: interpolated strings and computed include arguments are not evaluated, and dynamic declarations may require explicit inspection. A true CLI result still leads to package discovery; only two or more confirmed packages select the hierarchical document workflow.

### Go

- **`go.work`**: Go workspaces (Go 1.18+)

### Rust

- **`Cargo.toml`** with a `[workspace]` table that declares `members`: Cargo workspaces. An empty `[workspace]` table (the idiom for detaching a crate from a parent workspace) is **not** a monorepo

### Python

- **`pyproject.toml`** with `workspace.members` under a `[tool.hatch.envs.<env>]` table, or **`hatch.toml`** with the same key under `[envs.<env>]`: Hatch workspaces (Hatch 1.16+). Workspaces are configured per environment; an environment table without `workspace.members` is ordinary environment configuration, not a monorepo marker
- **`pyproject.toml`** with `[tool.uv.workspace]`: uv workspaces
- **`pyproject.toml`** with `[tool.rye.workspace]`: Rye workspaces. Rye is no longer developed, but existing repositories may still use this table
- Multiple `pyproject.toml` or `setup.py` under a shared root with a top-level orchestration config

TOML matching is line-level static detection, like the Gradle check. It reads table headers, dotted keys, and Hatch's `workspace = { members = … }` inline form, and skips comments and multiline strings. Other TOML spellings are not evaluated.

### Build Systems (Language-Agnostic)

- **`MODULE.bazel`** or **`REPO.bazel`**: Bazel repository boundary markers. Legacy **`WORKSPACE`** or **`WORKSPACE.bazel`** files are still detected; Bazel 8 disables WORKSPACE support by default and Bazel 9 removes it. A boundary marker is also present in single-project Bazel repositories, so package discovery decides
- **`.buckconfig`**: Buck2
- **`pants.toml`**: Pants. Legacy **`pants.ini`** is still detected; current Pants no longer reads `pants.ini`, and its configuration is TOML (`pants.toml`)

## Workspace Package Discovery

After identifying a monorepo, discover packages from the relevant configuration:

### JavaScript / TypeScript

- **`pnpm-workspace.yaml`**: `packages` field
- **`package.json`**: `workspaces` field
- **`lerna.json`**: `packages` field
- **`nx.json`**: `projects` field or scan directories
- **`.moon/workspace.*`**: `projects` field — a map of project names to paths, a list of globs, or an object with `globs`, `sources`, and `globFormat`. A glob that matches a file (for example `crates/*/Cargo.toml`) makes the file's parent directory a project; before moon v2.5, only moon configuration files could be matched this way

### JVM (Gradle / Maven)

- **`settings.gradle.kts`** / **`settings.gradle`**: Parse `include()` / `includeBuild()` declarations
- **`pom.xml`**: Parse `<modules>` or `<subprojects>` entries

### Go

- **`go.work`**: Parse `use` directives

### Rust

- **`Cargo.toml`**: Parse `[workspace] members` field

### Python

- **`pyproject.toml`**: Parse `members` globs under `[tool.uv.workspace]` / `[tool.rye.workspace]`. Rye's `members` is optional; without it, inspect the subdirectories that contain their own `pyproject.toml`
- **Hatch (`pyproject.toml` or `hatch.toml`)**: Parse each environment's `workspace.members` entries (paths or globs, as strings or `{path, features}` objects) and apply `workspace.exclude`; different environments may list different members

### Build Systems

- **Bazel**: Scan directories containing `BUILD` or `BUILD.bazel` files
- **Buck2**: Scan directories containing build files — `BUCK` by default, or the name configured in the `.buckconfig` `[buildfile]` section (some projects use `TARGETS`)
- **Pants**: Scan directories containing `BUILD` files

## Fallback Discovery

If no configuration explicitly lists packages, scan these common directory patterns:

- `packages/*/`
- `apps/*/`
- `libs/*/`
- `modules/*/`
- `services/*/`
