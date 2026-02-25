# Monorepo Detection Specification

Defines the method for identifying if the current repository is a monorepo.

## Detection Logic

A repository is considered a monorepo if **any** of the following marker files or configurations exist in the root directory:

### JavaScript / TypeScript Ecosystem

- **`pnpm-workspace.yaml`**: pnpm workspaces
- **`lerna.json`**: Lerna
- **`nx.json`**: Nx
- **`turbo.json`**: Turborepo
- **`rush.json`**: Rush
- **`package.json`** with `workspaces` field: npm/Yarn workspaces

### JVM Ecosystem (Gradle / Maven)

- **`settings.gradle.kts`** or **`settings.gradle`** containing `include(` or `includeBuild(`: Gradle multi-project / composite build
- **Root `pom.xml`** with `<modules>` section: Maven multi-module project

### Go

- **`go.work`**: Go workspaces (Go 1.18+)

### Rust

- **`Cargo.toml`** with `[workspace]` section: Cargo workspaces

### Python

- **`pyproject.toml`** with `[tool.hatch.envs]` or workspace config: Hatch workspaces
- Multiple `pyproject.toml` or `setup.py` under a shared root with a top-level orchestration config

### Build Systems (Language-Agnostic)

- **`WORKSPACE`** or **`WORKSPACE.bazel`** or **`MODULE.bazel`**: Bazel
- **`pants.toml`** or **`pants.ini`**: Pants

## Workspace Package Discovery

After identifying a monorepo, discover packages from the relevant configuration:

### JavaScript / TypeScript

- **`pnpm-workspace.yaml`**: `packages` field
- **`package.json`**: `workspaces` field
- **`lerna.json`**: `packages` field
- **`nx.json`**: `projects` field or scan directories

### JVM (Gradle / Maven)

- **`settings.gradle.kts`** / **`settings.gradle`**: Parse `include()` / `includeBuild()` declarations
- **`pom.xml`**: Parse `<modules>` entries

### Go

- **`go.work`**: Parse `use` directives

### Rust

- **`Cargo.toml`**: Parse `[workspace] members` field

### Build Systems

- **Bazel**: Scan directories containing `BUILD` or `BUILD.bazel` files
- **Pants**: Scan directories containing `BUILD` files

## Fallback Discovery

If no configuration explicitly lists packages, scan these common directory patterns:

- `packages/*/`
- `apps/*/`
- `libs/*/`
- `modules/*/`
- `services/*/`
