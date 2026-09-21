# WebAssembly

## Contents

- [Host Capabilities and Linear Memory](#host-capabilities-and-linear-memory)
- [Start with the Host and ABI](#start-with-the-host-and-abi)
- [A Portable Kernel and a Browser Boundary](#a-portable-kernel-and-a-browser-boundary)
- [Memory and JS Views](#memory-and-js-views)
- [Async, Workers, and Threads](#async-workers-and-threads)
- [A WASI Boundary](#a-wasi-boundary)
- [SIMD and Feature Compatibility](#simd-and-feature-compatibility)
- [Size, Startup, and Throughput](#size-startup-and-throughput)

## Host Capabilities and Linear Memory

A Wasm module executes inside a host that supplies imports and capabilities. A target triple selects an ABI and supported environment; it does not supply arbitrary browser or OS services. Rust allocations live in linear memory, while JS objects belong to the host. Bindings connect them through copies, conversions, views, or handles.

A useful cost model is host preparation + boundary conversion + Rust computation + result conversion + rendering/I/O. A fast kernel can lose overall if it crosses the boundary once per pixel or rebuilds large objects repeatedly. Batch meaningful units such as a frame, but bound retained data and queue length so batching does not become excessive latency or memory use.

## Start with the Host and ABI

| Deployment | Integration | Constraints |
|---|---|---|
| Browser/JS host | wasm32-unknown-unknown and wasm-bindgen where bindings are needed | JS APIs, event loop, glue generation, worker and shared-memory policy |
| WASIp1 host | wasm32-wasip1 core module | Host-provided WASI imports, preopened resources and runtime configuration |
| WASIp2 host | wasm32-wasip2 component | Component interfaces and host support; not a browser core module |
| Freestanding engine | A target and feature baseline matching the engine | Explicit imports, memory, allocator, and supported instructions |

Wasm is not synonymous with browser execution or no_std. wasm32-unknown-unknown has partial std support but ordinary std filesystem calls fail and std thread spawning is unavailable. WASI adds capabilities through the host, not unrestricted access to the host machine.

## A Portable Kernel and a Browser Boundary

The example transforms RGB channels with saturating addition while preserving alpha. The kernel receives an exclusive slice, allocates nothing, and rejects incomplete RGBA pixels before mutation.

`src/kernel.rs`:

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct InvalidPixels;

pub fn brighten_pixels(rgba: &mut [u8], delta: u8) -> Result<(), InvalidPixels> {
    if rgba.len() % 4 != 0 {
        return Err(InvalidPixels);
    }
    for pixel in rgba.chunks_exact_mut(4) {
        for channel in &mut pixel[..3] {
            *channel = channel.saturating_add(delta);
        }
    }
    Ok(())
}
```

The binding owns its incoming boxed bytes. Numeric boxed-slice bindings copy between JS and Wasm; returning the box produces an independent JS typed array. This makes disposal straightforward and gives a baseline against which a retained-memory interface can be compared.

`Cargo.toml`:

```toml
[package]
name = "rgba-demo"
version = "0.1.0"
edition = "2024"

[lib]
crate-type = ["cdylib", "rlib"]

[dependencies]
wasm-bindgen = "0.2"
```

`src/lib.rs`:

```rust,deps
use wasm_bindgen::prelude::*;
mod kernel;

// Illustrative application limit, not a universal Wasm limit.
const MAX_FRAME_BYTES: usize = 16 * 1024 * 1024;

#[wasm_bindgen]
pub fn brighten_rgba(mut rgba: Box<[u8]>, delta: u8) -> Result<Box<[u8]>, JsValue> {
    if rgba.len() > MAX_FRAME_BYTES {
        return Err(JsValue::from_str("frame exceeds byte limit"));
    }
    kernel::brighten_pixels(&mut rgba, delta)
        .map_err(|_| JsValue::from_str("RGBA input length must be a multiple of four"))?;
    Ok(rgba)
}
```

With the browser target installed and a wasm-bindgen CLI matching the resolved wasm-bindgen crate version:

```sh
cargo build --release --target wasm32-unknown-unknown --lib
wasm-bindgen --target web --out-dir pkg target/wasm32-unknown-unknown/release/rgba_demo.wasm
```

Serve the generated files through an HTTP server. A module script can use them as follows:

```javascript
import init, { brighten_rgba } from "./pkg/rgba_demo.js";
await init();
const input = new Uint8Array([250, 10, 20, 255, 0, 1, 2, 128]);
const output = brighten_rgba(input, 10);
// output: [255, 20, 30, 255, 10, 11, 12, 128]; input remains independently owned.
console.log(output);
```

Argument conversion occurs before the Rust function body. A Rust-side limit prevents excess computation but does not prevent an oversized JS argument from first being copied by the glue. Validate size before the call too when controlling memory pressure. A checked limit also does not guarantee an allocation will succeed.

Returning Result maps expected input failures to a JS-visible error. Keep normal validation out of panic paths; a trap is not a recoverable domain-error interface. Validate JS numeric domains too: converting a JS number to a Rust integer is not a substitute for checking that a count or delta is an integer in the intended range. String conversion, structured-object conversion, and serialization add different costs. Do not infer zero-copy from the presence of a typed array or assume a serde bridge always beats JSON.

## Memory and JS Views

For repeated operations on one frame, keeping storage in Rust can avoid copying it for every call. Append this class to `src/lib.rs`; it reuses the kernel and limit above:

```rust,deps
#[wasm_bindgen]
pub struct Frame {
    pixels: Vec<u8>,
}

#[wasm_bindgen]
impl Frame {
    #[wasm_bindgen(constructor)]
    pub fn new(pixel_count: usize) -> Result<Frame, JsValue> {
        let bytes = pixel_count.checked_mul(4)
            .filter(|&bytes| bytes <= MAX_FRAME_BYTES)
            .ok_or_else(|| JsValue::from_str("frame exceeds byte limit"))?;
        Ok(Frame { pixels: vec![0; bytes] })
    }

    pub fn data_ptr(&mut self) -> *mut u8 { self.pixels.as_mut_ptr() }
    pub fn byte_len(&self) -> usize { self.pixels.len() }

    pub fn brighten(&mut self, delta: u8) {
        kernel::brighten_pixels(&mut self.pixels, delta)
            .expect("Frame storage contains complete RGBA pixels");
    }
}
```

The host now participates in the memory contract. This is a controlled-host interface: Rust cannot enforce the lifetime or mutation rules of a raw JS view. The class keeps the Vec length fixed, and brighten does not allocate or call JS. It therefore keeps its own allocation stable during the operation. Other allocations in the module can still grow linear memory.

```javascript
import init, { Frame } from "./pkg/rgba_demo.js";
const wasm = await init();
const frame = new Frame(2);
const view = () => new Uint8Array(
  wasm.memory.buffer, frame.data_ptr(), frame.byte_len()
);
try {
  view().set([250, 10, 20, 255, 0, 1, 2, 128]);
  frame.brighten(10);
  const result = view().slice(); // independent JS ownership before disposal
  console.log(result);
} finally {
  frame.free();
}
```

data_ptr uses mutable access because the host writes through the returned pointer; a pointer obtained only for shared reading does not grant that permission. Use the view only while the Frame is alive, never mutate it concurrently with Rust access, and reacquire it after a Rust operation or a call that may grow memory. For ordinary memory, growth detaches the old ArrayBuffer; shared-memory views do not expand to cover newly grown memory. Calling free invalidates all views regardless of whether memory grew.

The generated free method releases the Rust object, not necessarily linear-memory pages back to the host. A retained object also retains its allocation. Automatic JS garbage collection is not a precise release schedule for Rust resources; explicit disposal is useful for predictable workloads.

The example copies once into persistent storage and copies the final result out. Between those points, multiple Rust operations can share the same allocation. That trade-off becomes useful when there are enough repeated operations to offset interface complexity. The simple boxed-slice boundary is preferable when callers cannot uphold the view protocol. An exported raw pointer is not a general-purpose safe interface for arbitrary consumers.

## Async, Workers, and Threads

Awaiting a Promise coordinates waiting on the host event loop; it does not move a long Rust loop off the main thread. Break work into bounded pieces that actually yield, or execute the computation in a worker. A microtask-only loop can still starve rendering, so the host scheduling mechanism matters.

A worker can use its own Wasm instance and exchange transferable buffers without shared memory. For the boxed-slice function above, a complete worker module can be:

```javascript
// worker.js
import init, { brighten_rgba } from "./pkg/rgba_demo.js";
const ready = init().then(
  () => ({ ok: true }),
  error => ({ ok: false, error })
);
self.onmessage = async ({ data: { id, buffer, delta } }) => {
  try {
    const state = await ready;
    if (!state.ok) throw state.error;
    const result = brighten_rgba(new Uint8Array(buffer), delta);
    self.postMessage({ id, buffer: result.buffer }, [result.buffer]);
  } catch (error) {
    self.postMessage({ id, error: String(error) });
  }
};
```

A main-thread client with one admitted request at a time:

```javascript
const worker = new Worker(new URL("./worker.js", import.meta.url), { type: "module" });
let pending;
let isWorkerFailed = false;
let nextId = 0;
worker.onmessage = ({ data }) => {
  if (!pending || pending.id !== data.id) return;
  const current = pending;
  pending = undefined;
  if (data.error !== undefined) current.reject(new Error(data.error));
  else current.resolve(new Uint8Array(data.buffer));
};
worker.onerror = (event) => {
  isWorkerFailed = true;
  pending?.reject(new Error(event.message));
  pending = undefined;
};
function processFrame(input, delta) {
  if (isWorkerFailed) return Promise.reject(new Error("worker unavailable"));
  if (pending) return Promise.reject(new Error("worker busy"));
  if (!(input instanceof Uint8Array) || input.byteLength > 16 * 1024 * 1024 || input.byteLength % 4 !== 0) {
    return Promise.reject(new Error("invalid frame size"));
  }
  if (!Number.isInteger(delta) || delta < 0 || delta > 255) {
    return Promise.reject(new Error("invalid brightness delta"));
  }
  const owned = input.slice(); // own exactly this view's bytes before transfer
  return new Promise((resolve, reject) => {
    const id = nextId++;
    pending = { id, resolve, reject };
    try {
      worker.postMessage({ id, buffer: owned.buffer, delta }, [owned.buffer]);
    } catch (error) {
      pending = undefined;
      reject(error);
    }
  });
}
```

The worker installs its handler while initialization is pending, waits for that initialization per request, and reports initialization failures through the same response protocol. The single-request admission bound is enforced by this client; other producers would need the same coordination.

Transferring detaches the sender's buffer. The explicit slice above preserves the caller's input and avoids transferring unrelated bytes from a larger backing buffer. If the caller deliberately relinquishes an entire owned buffer, that copy can be removed. Transfer between worker and main thread does not remove the separate JS/Wasm binding copies.

Termination and restart need a policy for rejecting a pending request. A timeout that only rejects a Promise does not stop the worker's computation; freeing the admission slot at that point can silently create an unbounded queue. Retain the slot until completion or terminate/recreate the worker according to the application's loss/retry policy.

Shared-memory threading is a different design. It needs compatible Wasm/engine features, browser isolation and deployment headers, a worker/executor integration, and synchronized access. A native Rayon call does not create a browser thread pool by itself. A worker-message design does not inherit all shared-memory prerequisites.

## A WASI Boundary

The same kernel can operate on stdin/stdout in a WASIp1 binary. `src/bin/filter.rs` includes the portable source directly so it has no JS binding dependency in its code:

```rust
#[path = "../kernel.rs"]
mod kernel;
use std::io::{self, Read, Write};

fn main() -> io::Result<()> {
    const MAX_BYTES: usize = 16 * 1024 * 1024;
    let mut input = Vec::new();
    io::stdin().take((MAX_BYTES + 1) as u64).read_to_end(&mut input)?;
    if input.len() > MAX_BYTES {
        return Err(io::Error::new(io::ErrorKind::InvalidInput, "frame too large"));
    }
    kernel::brighten_pixels(&mut input, 10)
        .map_err(|_| io::Error::new(io::ErrorKind::InvalidInput, "incomplete pixel"))?;
    io::stdout().write_all(&input)
}
```

```sh
cargo build --release --target wasm32-wasip1 --bin filter
```

Execute the resulting module in a WASIp1 host configured to supply stdin/stdout. Filesystem paths need host-provided directories/capabilities; a local-looking path inside the module does not establish access. WASIp2 components use a different interface model, so changing only the target string is not a browser-binding or host-interface migration strategy.

## SIMD and Feature Compatibility

Wasm engines validate the module's required instructions before the optimized path runs. For a baseline that may lack simd128, build a baseline module and a SIMD module separately and choose before instantiation. Hiding a SIMD function behind an ordinary runtime branch inside one module does not give a universally compatible fallback.

Track instruction features together with memory/threading requirements and imports. A module can compile successfully yet fail to instantiate in its deployment engine. Use the [SIMD patterns](simd.md) for kernel semantics and boundary handling; its native CPU dispatch example has a different compatibility boundary.

## Size, Startup, and Throughput

Measure Wasm plus JS glue transfer size, compile/instantiate time, first call, steady-state processing, main-thread responsiveness, and peak/retained memory separately. For the frame example, compare per-pixel calls, one boxed-slice call per frame, and several operations on a retained Frame. Count all copies and conversions rather than timing only brighten_pixels.

Unused exported bindings and dependency features can affect code size. Compare optimization levels and LTO individually: opt-level="z" disables loop vectorization and may lose throughput without producing the smallest module. Cold startup and warmed steady state can favor different choices.

Native kernel tests exercise arithmetic and input handling. Browser execution exercises glue, disposal, workers, memory growth, and engine features. WASI execution exercises its host imports and capabilities. None of those results automatically substitutes for the others.
