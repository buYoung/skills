# Modules and Crate Boundaries

## Contents

- [Namespaces, Compilation, and Packaging](#namespaces-compilation-and-packaging)
- [Choose the Boundary for a Reason](#choose-the-boundary-for-a-reason)
- [Dependency Direction and Ownership](#dependency-direction-and-ownership)
- [Visibility and the Public Facade](#visibility-and-the-public-facade)
- [Example: CLI, Service, and Wasm](#example-cli-service-and-wasm)
- [From One Package to a Shared Core](#from-one-package-to-a-shared-core)
- [Build and Runtime Costs](#build-and-runtime-costs)

## Namespaces, Compilation, and Packaging

A module is a namespace/privacy boundary; a crate is a compilation unit; a Cargo package can provide one library and multiple binary targets; a workspace manages packages together. A repository may contain multiple workspaces. File layout supports navigation, but moving a file alone does not create a new ownership or dependency boundary.

These boundaries serve different purposes. A private module can hide a representation while keeping package dependencies shared. A separate crate exposes an API to its consumers and can have its own dependency, feature, and target requirements. A workspace coordinates those packages without making their private items visible to each other. See [visibility](#visibility-and-the-public-facade) and [workspaces](workspaces-and-monorepos.md).

## Choose the Boundary for a Reason

Group code that changes together and protects the same invariants. Split where ownership, dependency direction, target support, or public contracts differ. Line counts are navigation signals, not architectural thresholds.

| Need | Starting boundary | Cost |
|---|---|---|
| Name one operation or isolate calculation from I/O | Function/type in the current module | Excessive indirection can hide cohesive code |
| Organize a feature and hide implementation | Module with a small visible surface | No independent dependencies or release policy |
| Share a core across applications/targets | Library crate, often in its own package | Public API, features, dependencies, compatibility |
| Multiple entry points over one implementation | Library and binary targets in one package | Separate packages only if their policies differ |
| Isolate no_std, Wasm, native I/O, or proc macros | Separate crate/package when useful | More build configuration and type boundaries |
| Manage related packages together | Workspace | Shared dependency resolution and features |

## Dependency Direction and Ownership

Reusable calculations should depend on the data and abstractions they need, not incidentally on a CLI parser, request framework, or board startup code. Adapters can depend on the core and translate host types at the boundary. Making that dependency direction explicit explains where a useful split belongs.

Introduce a trait for meaningful substitution or to isolate a volatile/target-specific dependency. A trait for every function adds bounds and maintenance without automatically adding flexibility; a concrete type or closure may suffice.

Avoid a catch-all `common` crate collecting unrelated helpers. Extract a shared type only when its meaning and compatibility policy are shared. Similar-looking types with different invariants can belong in separate modules.

Normal package dependencies should be acyclic. If a split creates a cycle, reconsider ownership, extract a narrow contract, or invert the dependency at integration. Do not hide a production cycle behind development dependencies.

## Visibility and the Public Facade

Keep implementation private; use `pub(super)` or `pub(crate)` for internal contracts and `pub` for external consumers. Re-export selected items when callers should not depend on the directory layout.

```rust
mod parser {
    #[derive(Debug, PartialEq)]
    pub struct Port(u16);

    impl Port {
        pub fn get(&self) -> u16 { self.0 }
    }

    pub fn parse_port(text: &str) -> Result<Port, core::num::ParseIntError> {
        text.trim().parse().map(Port)
    }
}

pub use parser::{parse_port, Port};
```

Splitting into another crate changes `pub(crate)` access: consumers now require a deliberate public API. Check error types, trait implementations, Send/Sync guarantees, and dependency types crossing that surface, not just imports.

## Example: CLI, Service, and Wasm

A parser or compute engine shared by these consumers is a portable-library candidate. Keep filesystem access, request extraction, and JS conversion in the integrations that own them. Pass slices or domain values where this keeps the core portable.

For a small single-purpose CLI, modules may be enough. Extract a package when a real second consumer, target/dependency constraint, or release boundary gives it a job. Conversely, isolate unsafe FFI or a no_std core when its contract needs it, without waiting for a file-length threshold.

## From One Package to a Shared Core

A small CLI can expose reusable logic through its package's library target before introducing another package. Keep one invariant with the operations that establish it. This example accepts a configured, nonzero listening port; port zero is intentionally outside this application's contract.

```text
port-app/
  Cargo.toml
  src/lib.rs       public facade
  src/port.rs      parsing and the nonzero-port invariant
  src/main.rs      arguments, messages, exit status
```

`src/lib.rs`:

```rust
mod port;
pub use port::{Port, PortError};
```

`src/port.rs`:

```rust
use core::{fmt, num::NonZeroU16};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Port(NonZeroU16);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct PortError;

impl Port {
    pub fn parse(text: &str) -> Result<Self, PortError> {
        text.trim().parse::<u16>().ok()
            .and_then(NonZeroU16::new).map(Self).ok_or(PortError)
    }
    pub fn get(self) -> u16 { self.0.get() }
}

impl fmt::Display for PortError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("expected a port from 1 through 65535")
    }
}
impl core::error::Error for PortError {}
```

`src/main.rs`, for a package named port-app:

```rust
use port_app::Port;
use std::process::ExitCode;

fn main() -> ExitCode {
    let Some(text) = std::env::args().nth(1) else {
        eprintln!("usage: port-app PORT");
        return ExitCode::FAILURE;
    };
    match Port::parse(&text) {
        Ok(port) => { println!("configured port: {}", port.get()); ExitCode::SUCCESS }
        Err(error) => { eprintln!("{error}"); ExitCode::FAILURE }
    }
}
```

The binary imports its package's library instead of declaring a second mod port. That gives one type identity and one implementation. The private field prevents callers from bypassing construction, and the public facade keeps consumers independent of the file layout. No trait is needed to test a pure parsing operation.

When a real second consumer or target boundary appears, move that library into a package such as port-core and leave argument/HTTP/JS conversion in its consumers:

```text
crates/port-core/src/{lib.rs,port.rs}
apps/port-cli/                 depends on port-core
apps/port-service/             depends on port-core
bindings/port-wasm/            depends on port-core
```

The public types and behavior need not change when storage moves to the new package; imports and manifests do. The core can use no_std because its implementation uses core facilities. A service translates PortError into a response; a JS binding translates it into its host error representation. Those adapters own transport policy rather than adding HTTP or JS types to PortError.

A trait becomes useful when the core needs a replaceable capability, such as reading a clock or storing records. Put the smallest needed contract near that consumer and implement it in adapters. If the core can accept an already-read value or a closure, that may avoid an unnecessary service abstraction. A trait that merely repeats every method of an implementation preserves coupling while adding another layer.

Crate extraction changes privacy: pub(crate) no longer reaches a sibling package. Avoid fixing every import error by making all internals public. Decide which operations form a supported contract and keep helper types behind the facade. Public dependency types, auto traits, and feature-dependent methods can become compatibility obligations even if the new directory tree looks cleaner.

## Build and Runtime Costs

Independent crates can compile in parallel, while long dependency chains serialize work and tiny crates add overhead. Generic code can be instantiated in consumers; inlining depends on compiler decisions, attributes, and LTO. A crate boundary does not universally prevent inlining without LTO.

Use build timings to evaluate a split motivated by build speed, distinguishing clean and incremental builds. Do not add inline attributes everywhere to compensate for an assumed cost.

Explain what the boundary owns, what it removes from consumers, and what API it introduces. Check that it does not accidentally add copies, boxing, locks, or a runtime requirement. Moving lines alone is not evidence of improved design.
