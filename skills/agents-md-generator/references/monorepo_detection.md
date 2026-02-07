# Monorepo Detection Specification

Defines the method for identifying if the current repository is a monorepo.

## Detection Logic

A repository is considered a monorepo if **any** of the following files exist in the root directory:

- **`pnpm-workspace.yaml`**: pnpm workspaces
- **`lerna.json`**: Lerna
- **`nx.json`**: Nx
- **`turbo.json`**: Turborepo
- **`rush.json`**: Rush

## Workspace Package Discovery

After identifying a monorepo, discover packages from these configuration files:

- **`pnpm-workspace.yaml`**: `packages`
- **`package.json`**: `workspaces`
- **`lerna.json`**: `packages`
- **`nx.json`**: Check `projects` or scan directories

## Fallback Discovery

If no configuration explicitly lists packages, scan these common directory patterns:

- `packages/*/package.json`
- `apps/*/package.json`
- `libs/*/package.json`
