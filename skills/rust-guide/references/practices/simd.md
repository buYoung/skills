# SIMD

## Contents

- [Lanes, Operations, and Data Layout](#lanes-operations-and-data-layout)
- [Decide Whether Vectorization Addresses the Bottleneck](#decide-whether-vectorization-addresses-the-bottleneck)
- [Make Scalar Semantics Explicit](#make-scalar-semantics-explicit)
- [Automatic Vectorization](#automatic-vectorization)
- [A Safe API Around Architecture-Specific Kernels](#a-safe-api-around-architecture-specific-kernels)
- [Target Features and Dispatch](#target-features-and-dispatch)
- [Search, Masks, and Reductions](#search-masks-and-reductions)
- [Correctness at the Vector Boundary](#correctness-at-the-vector-boundary)
- [Inspecting Generated Code and Measuring](#inspecting-generated-code-and-measuring)

## Lanes, Operations, and Data Layout

SIMD applies an operation to multiple lanes of a vector value. A 128-bit vector can hold four u32 lanes or sixteen u8 lanes; a 256-bit vector can hold eight u32 lanes. Lane count follows both vector width and element type. An instruction's name or register width alone does not describe its arithmetic semantics or throughput.

For element-wise addition, the work is load a group of left elements, load a group of right elements, add corresponding lanes, then store the group of results. A reduction such as a sum also combines lanes into one result. A search compares lanes and interprets a mask. Those extra steps matter when estimating whether SIMD helps.

```text
left:       [a0 a1 a2 a3] [a4 a5 a6 a7] [a8]
right:      [b0 b1 b2 b3] [b4 b5 b6 b7] [b8]
four lanes: [a0+b0 ...  ] [a4+b4 ...  ] scalar tail
```

Contiguous data makes full-width loads straightforward. In an array of `Point { x, y, z }`, the x values are separated by the other fields; separate x/y/z arrays make field-wise operations contiguous. Converting to that layout has a cost and can hurt operations that need whole points. Padding, gather operations, and shuffles are alternatives with their own costs. Choose a layout from actual access patterns rather than making every record a set of separate arrays.

SIMD runs within a core. Rayon-style parallelism divides work across execution threads and may use SIMD within each chunk. Thread scheduling and vector operations solve different problems; combining them can saturate memory bandwidth before all cores or lanes become useful.

## Decide Whether Vectorization Addresses the Bottleneck

| Work shape | Useful starting point | Reason to change course |
|---|---|---|
| Tiny input, pointer chasing, irregular control flow | Clear scalar code | Setup, gather, or dispatch costs can exceed the useful work |
| Contiguous independent transformations | A vectorizable scalar loop | Inspect generated code before writing intrinsics |
| A supported common operation, such as byte search | An optimized implementation such as memchr | Reuse its dispatch and boundary handling when its semantics fit |
| A hot kernel whose generated code is inadequate | A small explicit intrinsic implementation | Extra unsafe code and target variants need a meaningful benefit |
| Many independent large chunks | SIMD within a bounded compute pool | Bandwidth, pool contention, and chunk overhead limit scaling |

`core::arch` exposes target-specific intrinsics; availability and stability are per API. `core::simd` uses the nightly `portable_simd` feature. Portable source syntax still needs compatible code generation and deployment features. Keep a stable implementation when the project requires stable Rust.

## Make Scalar Semantics Explicit

The following operation adds equal-length u32 slices with wrapping arithmetic. The output is caller-owned and cannot safely overlap either input while being mutably borrowed. Length mismatches are returned before any output is changed.

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct LengthMismatch;

pub fn add_scalar(
    left: &[u32], right: &[u32], output: &mut [u32],
) -> Result<(), LengthMismatch> {
    if left.len() != right.len() || left.len() != output.len() {
        return Err(LengthMismatch);
    }
    for ((dst, &a), &b) in output.iter_mut().zip(left).zip(right) {
        *dst = a.wrapping_add(b);
    }
    Ok(())
}
```

This is a semantic reference, not necessarily machine code with one scalar instruction per element: an optimizing compiler can vectorize it. Wrapping addition is deliberate; checked or saturating addition would need corresponding lane operations and failure handling. A SIMD implementation cannot silently replace one policy with another.

## Automatic Vectorization

LLVM can vectorize loop iterations or combine independent scalar operations. Legal transformations and a cost model both matter. A loop can be legal to vectorize but remain scalar because setup, tails, or target costs outweigh the benefit.

| Pattern | Effect on optimization | Practical adjustment |
|---|---|---|
| Independent elements with contiguous loads/stores | Exposes regular work | Keep a simple kernel and explicit length/ownership contracts |
| `out[i]` depends on `out[i - 1]` | Iterations are dependent | Change the algorithm only if an equivalent parallel formulation exists |
| Data-dependent branches | May become masks or remain branches | Compare a branchless formulation without changing overflow or exceptional behavior |
| Dynamic calls in each iteration | Can hide the operation from the optimizer | A concrete generic kernel or moving dispatch outside the loop may help |
| Floating-point accumulation | Reordering can change results | Choose required numerical semantics before changing reduction order |
| Many unrelated operations and large temporaries | Can increase register pressure | Separate passes only when their extra memory traffic is justified |

Iterator syntax does not guarantee SIMD, and index syntax does not prevent it. Equal-length slices and borrowing can make relevant facts visible, but the emitted result depends on optimization, inlining, alias analysis, and the target. Avoid changing a clear iterator into unsafe pointer arithmetic without inspecting what the compiler already produces.

## A Safe API Around Architecture-Specific Kernels

This independent example contains a scalar fallback, AVX2 and AArch64 NEON kernels, and the public dispatch function. It uses std for runtime feature detection. Each vector loop proves that a full load/store stays in bounds and handles remaining elements with scalar operations.

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct LengthMismatch;

pub fn add_into(
    left: &[u32], right: &[u32], output: &mut [u32],
) -> Result<(), LengthMismatch> {
    if left.len() != right.len() || left.len() != output.len() {
        return Err(LengthMismatch);
    }
    #[cfg(target_arch = "x86_64")]
    if std::is_x86_feature_detected!("avx2") {
        // SAFETY: AVX2 was detected; lengths agree and slices provide valid storage.
        unsafe { add_avx2(left, right, output) };
        return Ok(());
    }
    #[cfg(target_arch = "aarch64")]
    if std::arch::is_aarch64_feature_detected!("neon") {
        // SAFETY: NEON was detected; lengths agree and slices provide valid storage.
        unsafe { add_neon(left, right, output) };
        return Ok(());
    }
    add_tail(left, right, output);
    Ok(())
}

fn add_tail(left: &[u32], right: &[u32], output: &mut [u32]) {
    for ((dst, &a), &b) in output.iter_mut().zip(left).zip(right) {
        *dst = a.wrapping_add(b);
    }
}

#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2")]
unsafe fn add_avx2(left: &[u32], right: &[u32], output: &mut [u32]) {
    use core::arch::x86_64::{__m256i, _mm256_add_epi32, _mm256_loadu_si256, _mm256_storeu_si256};
    let end = left.len() / 8 * 8;
    let mut index = 0;
    while index < end {
        // SAFETY: index..index+8 is inside all slices. Unaligned intrinsics do not
        // require 32-byte alignment. The mutable output does not alias the inputs.
        unsafe {
            let a = _mm256_loadu_si256(left.as_ptr().add(index).cast::<__m256i>());
            let b = _mm256_loadu_si256(right.as_ptr().add(index).cast::<__m256i>());
            let sum = _mm256_add_epi32(a, b);
            _mm256_storeu_si256(output.as_mut_ptr().add(index).cast::<__m256i>(), sum);
        }
        index += 8;
    }
    add_tail(&left[end..], &right[end..], &mut output[end..]);
}

#[cfg(target_arch = "aarch64")]
#[target_feature(enable = "neon")]
unsafe fn add_neon(left: &[u32], right: &[u32], output: &mut [u32]) {
    use core::arch::aarch64::{vaddq_u32, vld1q_u32, vst1q_u32};
    let end = left.len() / 4 * 4;
    let mut index = 0;
    while index < end {
        // SAFETY: index..index+4 is inside all slices, which are aligned for u32;
        // these loads/stores need no stronger alignment. Output is exclusive.
        unsafe {
            let a = vld1q_u32(left.as_ptr().add(index));
            let b = vld1q_u32(right.as_ptr().add(index));
            vst1q_u32(output.as_mut_ptr().add(index), vaddq_u32(a, b));
        }
        index += 4;
    }
    add_tail(&left[end..], &right[end..], &mut output[end..]);
}
```

The integer lane additions discard carry beyond 32 bits, matching wrapping_add. The kernels are private because their CPU and length preconditions are established at the public boundary. Empty slices perform no loads. Inputs shorter than a vector use only the tail. Using `len / lanes * lanes` avoids an overflowing `index + lanes` bound calculation.

An unaligned load still reads the entire vector width; it does not permit crossing an allocation boundary. A u32 subslice may lack vector alignment but remains aligned for u32, which these kernels require. Reinterpreting arbitrary bytes as u32 slices would introduce a separate alignment and validity problem.

## Target Features and Dispatch

| Mechanism | What it establishes | What it does not establish |
|---|---|---|
| `#[cfg(target_arch = "x86_64")]` | Which architecture's code is compiled | Whether that CPU supports AVX2 |
| `#[cfg(target_feature = "avx2")]` | A compilation-wide feature assumption | A runtime check on the deployment machine |
| `#[target_feature(enable = "avx2")]` | The feature set used for one function | That every caller runs on a compatible CPU |
| `is_x86_feature_detected!("avx2")` | Runtime support on x86/x86_64 | Availability of that macro on another architecture |
| `-C target-cpu=native` | Code generation for the build machine | Compatibility with a broader distribution baseline |

The example keeps the whole program at its portable target baseline and enables extra instructions only in selected functions. Enabling AVX2 globally may introduce AVX2 elsewhere, including code intended as fallback. A fallback function cannot repair an incompatible build baseline.

For a fixed deployment, known target guarantees can replace runtime detection. In no_std code, use supported core intrinsics with a justified build-time feature baseline or a platform-specific detection contract; std's runtime macros are not automatically available. A microcontroller being ARM does not imply NEON support.

Wasm compatibility is checked at module instantiation. A module containing unsupported SIMD instructions can be rejected even if its optimized function would never run. A baseline module and a SIMD-enabled module may therefore need to be built separately and selected before instantiation. See [Wasm feature compatibility](webassembly.md#simd-and-feature-compatibility).

## Search, Masks, and Reductions

Element-wise mapping is only one useful SIMD shape:

- **Search/filter:** compare lanes, turn matching lanes into a mask, and locate or count set lanes. After processing full vectors, search the tail normally. Mask layout and conversion operations are API-specific; an all-bits-set lane is not a scalar Rust bool. An existing byte-search implementation can avoid maintaining this logic yourself.
- **Reduction:** accumulate partial results in lanes, combine those lanes, then process the tail. Use more than one accumulator only when shorter dependency chains justify extra registers and final reduction work. Integer width and overflow policy remain part of the result contract.
- **Rearrangement:** shuffles and interleaving can place data into useful lanes, but conversion work can erase the gain. Evaluate the entire load/rearrange/compute/store sequence.

Wrapping integer sums can be regrouped while preserving modular arithmetic. Floating-point sums generally cannot: different grouping and fused multiply-add can change rounding. Define exact reproducibility or an acceptable numerical tolerance before adopting a reordered kernel. NaNs, signed zero, infinities, and subnormal behavior need attention when relevant to the operation.

## Correctness at the Vector Boundary

Compare the public function with the scalar reference on empty input, lengths immediately below/at/above each lane width, larger non-multiples, and values near u32::MAX. An offset subslice exercises valid storage without assuming vector alignment. Length-error cases should establish the promised output behavior.

Exercise fallback separately from the optimized path. A run on NEON hardware does not validate AVX2 execution, and a target compilation does not exercise its instructions. Keep feature detection outside any forced-kernel correctness check; an unsupported kernel must not be called just to increase coverage.

For a masked intrinsic, establish exactly which addresses it may access. Masking a result after loading does not make an out-of-bounds load valid. For floating-point kernels, compare the agreed numerical contract rather than assuming bit equality or choosing a tolerance after seeing failures.

## Inspecting Generated Code and Measuring

For a library package containing the example:

```sh
cargo rustc --release --lib -- --emit=asm
```

Assembly files are emitted under the target's release artifacts, normally `target/release/deps/`. Locate the kernel and its callers: vector registers and packed operations show the generated strategy, while scalar cleanup should remain for tails. Inlining or dead-code elimination can remove a standalone symbol; an optimized caller may contain the relevant code. Explicit intrinsics express operations but are still subject to optimization.

Compare the scalar-source function, the automatically vectorized build, and the dispatched intrinsic implementation under the same target/profile. The scalar-source baseline may already use SIMD. Calling it “scalar” in a timing table would be misleading without inspecting the generated code.

Vary input size, distribution, warm/cold data, and alignment. Include dispatch and conversion costs when they occur in the real call. For very small calls, setup and tails can dominate; for large arrays, load/store bandwidth can dominate. A one-time dispatch cache is useful only if repeated feature checks matter to the workload and its extra interface complexity is justified.

Use the [measurement patterns](performance.md#benchmarking) for repeated runs and optimizer-resistant inputs. Report throughput or latency together with the deployment CPU and code size. A wider instruction set is a mechanism to evaluate, not a performance result.
