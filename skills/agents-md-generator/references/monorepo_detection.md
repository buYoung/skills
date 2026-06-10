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
- **`.moon/workspace.yml`**: moonrepo
- **`package.json`** with a top-level `workspaces` field (matched as a JSON key, not a substring): npm/Yarn workspaces

### JVM Ecosystem (Gradle / Maven)

- **`settings.gradle.kts`** or **`settings.gradle`** declaring **2+ included projects** or any `includeBuild(`: Gradle multi-project / composite build. Comments are ignored; a single `include ':app'` (the standard single-app Android layout) is **not** a monorepo
- **Root `pom.xml`** with `<modules>` section: Maven multi-module project

### Go

- **`go.work`**: Go workspaces (Go 1.18+)

### Rust

- **`Cargo.toml`** with a `[workspace]` table that declares `members`: Cargo workspaces. An empty `[workspace]` table (the idiom for detaching a crate from a parent workspace) is **not** a monorepo

### Python

- **`pyproject.toml`** with `[tool.hatch.envs]`: Hatch workspaces
- **`pyproject.toml`** with `[tool.uv.workspace]`: uv workspaces
- **`pyproject.toml`** with `[tool.rye.workspace]`: Rye workspaces
- Multiple `pyproject.toml` or `setup.py` under a shared root with a top-level orchestration config

### Build Systems (Language-Agnostic)

- **`WORKSPACE`** or **`WORKSPACE.bazel`** or **`MODULE.bazel`**: Bazel
- **`.buckconfig`**: Buck2
- **`pants.toml`** or **`pants.ini`**: Pants

## Workspace Package Discovery

After identifying a monorepo, discover packages from the relevant configuration:

### JavaScript / TypeScript

- **`pnpm-workspace.yaml`**: `packages` field
- **`package.json`**: `workspaces` field
- **`lerna.json`**: `packages` field
- **`nx.json`**: `projects` field or scan directories
- **`.moon/workspace.yml`**: `projects` field (glob list, object map, or array)

### JVM (Gradle / Maven)

- **`settings.gradle.kts`** / **`settings.gradle`**: Parse `include()` / `includeBuild()` declarations
- **`pom.xml`**: Parse `<modules>` entries

### Go

- **`go.work`**: Parse `use` directives

### Rust

- **`Cargo.toml`**: Parse `[workspace] members` field

### Python

- **`pyproject.toml`**: Parse `members` globs under `[tool.uv.workspace]` / `[tool.rye.workspace]`; for Hatch, scan directories containing their own `pyproject.toml`

### Build Systems

- **Bazel**: Scan directories containing `BUILD` or `BUILD.bazel` files
- **Buck2**: Scan directories containing `BUCK` files
- **Pants**: Scan directories containing `BUILD` files

## Fallback Discovery

If no configuration explicitly lists packages, scan these common directory patterns:

- `packages/*/`
- `apps/*/`
- `libs/*/`
- `modules/*/`
- `services/*/`
