# Workspaces and Monorepos

## Contents

- [Shared Build Context and Independent Packages](#shared-build-context-and-independent-packages)
- [Decide What Must Be Managed Together](#decide-what-must-be-managed-together)
- [Root and Member Responsibilities](#root-and-member-responsibilities)
- [Connect Features to Source Code](#connect-features-to-source-code)
- [Feature Unification and Portability](#feature-unification-and-portability)
- [Dependency Graph and Releases](#dependency-graph-and-releases)
- [Build and Validation Scope](#build-and-validation-scope)
- [Coordinated and Independent Releases](#coordinated-and-independent-releases)

## Shared Build Context and Independent Packages

A workspace coordinates Cargo packages: members share the root lockfile and output directory, and profiles/patches are read from the root. Inherited package fields and dependencies are opt-in. Members still expose separate crate APIs and can have different targets, features, and release versions. Shared configuration reduces repetition but does not enforce identical capabilities.

## Decide What Must Be Managed Together

Use one workspace for related packages benefiting from shared resolution and coordinated changes. Separate workspaces can fit independently built toolchains, incompatible build assumptions, or unrelated products. Different binary targets alone do not require separate workspaces.

| Decision | Starting choice | Change when |
|---|---|---|
| Repository structure | One workspace for related Rust packages | Toolchain or release isolation is required |
| Root manifest | Virtual workspace if no package is primary | A root application is the natural default |
| Versioning | Share versions for lockstep releases | Libraries evolve independently |
| Dependencies | Centralize deliberately shared requirements | A member has a justified different requirement |
| Features | Additive capabilities, minimal foundational defaults | A capability is essential to the package |
| Commands | Explicit `-p` / `--workspace` for repeatability | Interactive work can use `default-members` |

## Root and Member Responsibilities

```toml
# Root Cargo.toml: illustrative layout, not a universal template.
[workspace]
members = ["crates/engine", "apps/cli"]
default-members = ["apps/cli"]
resolver = "3"

[workspace.package]
edition = "2024"
rust-version = "1.85"
license = "MIT"

[workspace.dependencies]
engine = { path = "crates/engine", version = "0.1.0", default-features = false }

[profile.release]
debug = "line-tables-only"
```

```toml
# crates/engine/Cargo.toml
[package]
name = "engine"
version = "0.1.0"
edition.workspace = true
rust-version.workspace = true
license.workspace = true

[features]
default = ["std"]
std = ["alloc"]
alloc = []
```

```toml
# apps/cli/Cargo.toml
[package]
name = "engine-cli"
version = "0.1.0"
edition.workspace = true
rust-version.workspace = true
license.workspace = true
publish = false

[dependencies]
engine = { workspace = true, features = ["std"] }
```

Resolver 3 needs Cargo 1.84+; edition 2024 needs Rust 1.85+. Virtual workspaces need an explicit resolver because they have no package edition from which to infer it. A member's `rust-version` neither installs a compiler nor guarantees every resolved dependency is compatible.

Share lint policy only where intended; members opt in with `[lints] workspace = true`. Firmware, FFI adapters, and applications need not have identical capabilities or release versions.

## Connect Features to Source Code

Feature names in Cargo.toml do not make a crate no_std by themselves. For the engine manifest above, `crates/engine/src/lib.rs` can expose a core operation, an allocating operation, and a host-only adapter:

```rust
#![cfg_attr(not(feature = "std"), no_std)]
#[cfg(feature = "alloc")]
extern crate alloc;

pub fn checksum(bytes: &[u8]) -> u32 {
    bytes.iter().fold(0_u32, |sum, &byte| sum.wrapping_add(u32::from(byte)))
}

#[cfg(feature = "alloc")]
pub fn checksums(chunks: &[&[u8]]) -> alloc::vec::Vec<u32> {
    chunks.iter().map(|chunk| checksum(chunk)).collect()
}

#[cfg(feature = "std")]
pub fn checksum_file(path: impl AsRef<std::path::Path>) -> std::io::Result<u32> {
    std::fs::read(path).map(|bytes| checksum(&bytes))
}
```

The CLI member requesting std can call checksum_file. A firmware member can request no features and call checksum on its own buffer. An allocator-capable consumer can enable alloc without enabling filesystem access. The std feature enables alloc in this manifest because it is an intended API superset, not because Cargo implicitly creates that relationship.

`apps/cli/src/main.rs`:

```rust
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let path = std::env::args_os().nth(1).ok_or("usage: engine-cli FILE")?;
    println!("{}", engine::checksum_file(path)?);
    Ok(())
}
```

The feature matrix now has observable API differences:

| Build of engine | Available example API | Facilities needed |
|---|---|---|
| No default features | checksum | core |
| alloc only | checksum, checksums | core plus an allocator in the final program |
| std | All three functions | hosted std support |

```sh
cargo check -p engine --no-default-features
cargo check -p engine --no-default-features --features alloc
cargo check -p engine --features std
cargo check -p engine-cli
```

A bare-metal target check adds a distinct constraint; for example, with that target installed, `cargo check -p engine --no-default-features --target thumbv7em-none-eabi` catches accidental dependencies on unavailable std facilities. A host feature check alone does not establish that target contract.

## Feature Unification and Portability

Building packages together can unify features requested for their dependencies. This can hide a member's missing feature declaration or enable std for a core intended to support no_std. Resolver 2/3 separate some target/build/dev contexts, not every member's features.

For example, suppose an `engine` enables an optional serialization dependency only through a `serialization` feature. A CLI enables that feature while another member uses serialization APIs without requesting it. A combined build can expose those APIs through feature unification; the second member built alone can fail. Each consumer therefore declares the capabilities it uses, and a portable package's supported feature/target combinations are meaningful independently of the host application's build.

- Disable defaults at the shared declaration when consumers must opt out. A local `default-features = false` cannot undo defaults enabled elsewhere.
- Workspace dependency entries cannot be optional; a member can inherit one as optional.
- Check the affected package alone with its promised features/target as well as in relevant workspace combinations. Host `--all-features` does not establish firmware or Wasm compatibility.
- `--all-features` is not a universal matrix for platform-specific or documented mutually exclusive configurations. Verify supported combinations.
- Use `cargo tree -e features` and `cargo tree -d` to inspect unexpected features and duplicate versions. Shared declarations do not force one transitive version.

Resolver 3's MSRV fallback prefers compatible dependencies but can choose incompatible ones when requirements leave no compatible solution. An actual MSRV build remains necessary.

### When a Combined Build Hides a Missing Feature

Add `apps/file-tool` as a workspace member. Its source calls engine::checksum_file, but the following dependency declaration does not request std:

```toml
# apps/file-tool/Cargo.toml: intentionally incomplete for its source usage.
[package]
name = "file-tool"
version = "0.1.0"
edition = "2024"

[dependencies]
engine = { workspace = true }
```

```rust
// apps/file-tool/src/main.rs
fn main() -> std::io::Result<()> {
    println!("{}", engine::checksum_file("input.dat")?);
    Ok(())
}
```

The CLI member enables engine/std when both consumers are selected together. The file-tool can therefore compile in that invocation and fail in isolation:

```sh
cargo check --workspace
cargo check -p file-tool
cargo tree --workspace -e features -i engine
cargo tree -p file-tool -e features
```

The isolated error points to a function configured out behind std. The inverse workspace tree shows which consumer enables that feature; the file-tool tree lacks that request. The repair is for file-tool to declare `engine = { workspace = true, features = ["std"] }`. Changing resolver or enabling all features globally would hide the consumer's missing contract.

For actual monorepo checks, select packages by the task and include their affected consumers. Default-members controls implicit selection, not dependency independence. A root profile, lockfile, or shared feature change can affect many members even when only one source package changed.

## Dependency Graph and Releases

Use [module and crate boundaries](modules-and-crate-boundaries.md) to keep core logic independent of adapters. Splitting every layer into a package can multiply public contracts without reducing coupling.

Choose lockstep or independent versioning deliberately. A dependency type exposed publicly can create compatibility obligations even when the local workspace compiles. Keep internal-only packages unpublished where appropriate.

A `path` dependency selects development code; a version alongside it supplies the registry requirement when publishing. Validate package contents and dependency availability before release. A local sibling directory is not a publishing strategy.

Commit the workspace lockfile for reproducible development/CI. Library consumers resolve using published requirements, not the publisher's workspace lockfile. Reproducibility and compatibility with newly resolved dependencies are distinct checks.

## Build and Validation Scope

Choose checks from the affected dependency graph, including reverse dependencies and target adapters. Root manifest, lockfile, feature, and build-script changes may need broader checks than isolated implementation changes.

For build-time work, distinguish clean/incremental compilation, proc macros, build scripts, linking, and generated generic code. One workspace does not mean one invocation can correctly build every native, firmware, and Wasm target.

Report which packages, targets, features, and toolchains were checked. Reuse project tooling where suitable; the examples explain Cargo choices rather than prescribing additional monorepo tooling.

## Coordinated and Independent Releases

For lockstep packages, `[workspace.package] version = "..."` and `version.workspace = true` express one release version, but each registry dependency requirement still needs to accept the published version. For independent packages, keep member versions separate and update consumers whose requirements or public contracts change. Sharing a workspace does not select a release policy automatically.

A path plus version dependency uses the path during local development and the registry requirement for publication. This allows coordinated local work while still making the published package resolvable outside the monorepo. An unpublished internal package cannot satisfy another package's registry dependency merely by being a workspace member.

Before a release, inspect the packaged files and the dependency versions consumers will resolve. Root workspace success can depend on local sibling code, local patches, or unified features that a downstream build will not have. Publishing order follows the dependency graph; a workspace publish operation coordinates packages but does not decide whether an API or behavior change is compatible.

For mixed Rust and non-Rust repositories, Cargo owns the Rust dependency/build graph. Repository-wide task tools can coordinate it with other builds without replacing Cargo's feature and package semantics. Use cargo metadata when automation needs package IDs, target types, and dependency edges instead of inferring the graph from directory names.
