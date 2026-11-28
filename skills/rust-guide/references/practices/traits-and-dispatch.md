# Traits and Dispatch

## Contents

- [Enum, Trait, Generic, or dyn](#enum-trait-generic-or-dyn)
- [Dyn Compatibility](#dyn-compatibility)
- [Sealed and Extension Traits](#sealed-and-extension-traits)
- [Async Functions in Traits](#async-functions-in-traits)
- [Availability by Version](#availability-by-version)
- [Practical Boundaries](#practical-boundaries)

Examples use stable APIs unless marked otherwise; see [compatibility](../../SKILL.md#compatibility). Invariants and extension policy for data types are in [type design](type-design.md); public-surface rules in [API design](api-design.md).

## Enum, Trait, Generic, or dyn

| Need | Choose | Why |
|---|---|---|
| Closed set of alternatives you control | `enum` | Exhaustive `match`, inline variant storage; payloads may themselves allocate |
| Behavior others may implement | `trait` | Open extension; the trait is the contract |
| One concrete type per call site, hot path | generic `T: Trait` or `impl Trait` | Monomorphized and inlinable; "for each unique type that substitutes a parameter a new version of that function is generated" |
| Heterogeneous collection or an erased interface | `dyn Trait` behind `Box`, `&`, `Rc`, `Arc` | Dynamic dispatch can reduce type-specific code generation; pointer choice determines ownership |
| Both open and restricted | sealed trait | Users can name and call it, cannot implement it |

```rust
// Closed set: an enum with data per variant.
enum Shape {
    Circle { radius: f64 },
    Rect { width: f64, height: f64 },
}

impl Shape {
    fn area(&self) -> f64 {
        match self {
            Shape::Circle { radius } => std::f64::consts::PI * radius * radius,
            Shape::Rect { width, height } => width * height,
        }
    }
}

// Open set: a trait others can implement.
trait Area {
    fn area(&self) -> f64;
}

impl Area for Shape {
    fn area(&self) -> f64 {
        Shape::area(self)
    }
}

// Static dispatch: specialized for T; the optimizer can inline the calls.
fn total_area<T: Area>(items: &[T]) -> f64 {
    items.iter().map(Area::area).sum()
}

// Dynamic dispatch: one function, mixed concrete types, one vtable call per item.
fn total_area_dyn(items: &[Box<dyn Area>]) -> f64 {
    items.iter().map(|item| item.area()).sum()
}
```

Use an enum for a closed set, generics for compile-time substitution, and dyn Trait for runtime heterogeneity or a deliberately erased interface. A borrowed trait object need not allocate or require downcasting. Generic instantiations can improve optimization while increasing code size/build time; dynamic dispatch has indirection and can reduce duplication. Choose according to extension requirements and measured costs.

## Dyn Compatibility

A dyn-compatible trait cannot require Self: Sized or define associated constants. Its dispatchable methods need a supported receiver and cannot have type-generic parameters, opaque impl Trait/async returns, or use Self in other argument/return positions. Methods marked where Self: Sized are excluded from dynamic dispatch and can coexist with a dyn-compatible interface. Ordinary associated types are possible when specified on the trait object, such as dyn Iterator<Item = u8>; generic associated types prevent dyn compatibility.

```rust
trait Storage {
    fn get(&self, key: &str) -> Option<Vec<u8>>;
    fn put(&mut self, key: &str, value: Vec<u8>);

    /// Generic helper: excluded from the vtable so the trait stays dyn-compatible.
    fn get_as<T: From<Vec<u8>>>(&self, key: &str) -> Option<T>
    where
        Self: Sized,
    {
        self.get(key).map(T::from)
    }
}

fn read_all(stores: &[Box<dyn Storage>], key: &str) -> Vec<Vec<u8>> {
    stores.iter().filter_map(|s| s.get(key)).collect()
}
```

Since 1.86, `&dyn Sub` coerces to `&dyn Super` (trait upcasting), which removes the `fn as_super(&self) -> &dyn Super` boilerplate. Keep public traits dyn-compatible when trait objects are plausible for users; adding a generic method later without `where Self: Sized` is a breaking change for `dyn` users.

## Sealed and Extension Traits

A sealed trait is public but cannot be implemented outside the crate because it requires a private supertrait. Use it when downstream implementations would be unsound, unstable, or would prevent you from adding methods later.

```rust
mod sealed {
    pub trait Sealed {}
}

pub trait Backend: sealed::Sealed {
    fn name(&self) -> &'static str;
}

pub struct Postgres;
pub struct Sqlite;

impl sealed::Sealed for Postgres {}
impl sealed::Sealed for Sqlite {}

impl Backend for Postgres {
    fn name(&self) -> &'static str {
        "postgres"
    }
}

impl Backend for Sqlite {
    fn name(&self) -> &'static str {
        "sqlite"
    }
}
```

Compared with an enum, a sealed trait hides the list of implementors and monomorphizes per type; compared with an open trait, it keeps the right to add required methods in a minor release. An extension trait adds methods to a foreign type:

```rust
pub trait StrExt {
    fn is_blank(&self) -> bool;
}

impl StrExt for str {
    fn is_blank(&self) -> bool {
        self.trim().is_empty()
    }
}

fn check(input: &str) -> bool {
    input.is_blank()
}
```

Define an extension trait only when method syntax reads clearly better than a free function, and name it `<Type>Ext`; a later inherent method with the same name on the foreign type takes priority and silently changes behavior.

## Async Functions in Traits

An async trait method returns a future whose concrete state can depend on Self and borrowed inputs. Static dispatch can retain that concrete type. A dynamically dispatched interface needs a representable erased return type, commonly a pinned boxed future. The box erases and stores the future; pinning supplies an address-stability contract. Those are different purposes.

For a public interface whose futures must be Send, an explicit return-position impl Future bound makes that promise visible. This example also requires Sync for borrowed access to the source. The in-memory implementation clones its payload to produce independent output; a real I/O implementation would have its own waiting/error behavior.

```rust
use std::{future::Future, pin::Pin};

pub trait ByteSource: Sync {
    fn read(&self) -> impl Future<Output = Vec<u8>> + Send;
}

pub struct MemorySource(pub Vec<u8>);
impl ByteSource for MemorySource {
    fn read(&self) -> impl Future<Output = Vec<u8>> + Send {
        async { self.0.clone() }
    }
}

pub trait DynByteSource {
    fn read(&self) -> Pin<Box<dyn Future<Output = Vec<u8>> + Send + '_>>;
}

impl<S: ByteSource> DynByteSource for S {
    fn read(&self) -> Pin<Box<dyn Future<Output = Vec<u8>> + Send + '_>> {
        Box::pin(ByteSource::read(self))
    }
}

pub async fn read_static<S: ByteSource>(source: &S) -> Vec<u8> {
    ByteSource::read(source).await
}
pub async fn read_dynamic(source: &(dyn DynByteSource + Sync)) -> Vec<u8> {
    DynByteSource::read(source).await
}
```

The static interface does not require a box for its returned future; its body can still allocate output. The dynamic interface permits heterogeneous implementations through one erased API and boxes each returned future in this pattern. That future borrows source until it finishes, so boxing has not made it static. An independently spawned operation needs a suitable owner for the source as well as the required Send bounds.

A trait with an ordinary async fn or return-position impl Trait method is not automatically usable as dyn Trait. Use static dispatch when consumers know the type, and introduce an erased facade where runtime heterogeneity is needed. Choosing Send versus a thread-local future contract is a public API decision; do not add bounds just to silence one caller's diagnostic. See [task ownership](async-and-parallel-execution.md#borrowing-and-task-ownership) for the scheduling boundary.

## Availability by Version

| Version | Addition |
|---|---|
| 1.82 | `use<..>` precise capturing on `impl Trait` returns |
| 1.85 | Async closures and `AsyncFn` traits; edition 2024 capture rules |
| 1.86 | Trait upcasting `&dyn Sub` to `&dyn Super` |
| 1.87 | `use<..>` in trait definitions |
| 1.95 | `if let` guards in `match` |

Per-release details live in [the versions index](../versions/index.md).

## Practical Boundaries

Sealed traits and non_exhaustive types address specific extension policies rather than being mandatory on every public type.
