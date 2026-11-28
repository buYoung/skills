# Reference Split and Wording Corrections (2026-11-28)

## Scope

Corrected four statements, added two crates to the library catalog, and split eight practice references into twenty, so the package now has 29 practice references. The skill description, release coverage (1.80 through 1.100.0), and evaluation cases are unchanged. This record is maintenance material outside the runtime reference graph.

## Wording Corrections

| Location | Before | After | Reason |
|---|---|---|---|
| `concurrency.md`, Choosing a Model | "Threads per connection do not scale" | "Each waiting operation would otherwise hold a thread and its stack; a few blocking operations can stay on threads" | The absolute form contradicted the conditional comparison in `library-selection.md` |
| `concurrency.md`, Threads | "Threads spawned with `spawn` are detached from their creator" | A spawned thread runs independently of its creator, and dropping its `JoinHandle` detaches it | [JoinHandle](https://doc.rust-lang.org/std/thread/struct.JoinHandle.html) detaches the thread when the handle is dropped; the Async Boundary section already said so |
| `performance-optimization.md`, Logging and Assertions | "Logging that is disabled must cost nothing" | "Disabled logging should cost no more than its level check" | The level comparison remains after gating message construction |
| `concurrency.md`, introduction | "Blocks marked `ignore` need an async runtime crate." | Removed | The file has no `ignore` block |

## Adoption Audit: Checked Byte Casts

Method and floor as in `2026-09-21-guideline-redesign.md`, queried 2026-11-28. The byte-reinterpretation section already named both crates as the ecosystem answer without a catalog entry or audit.

| Package | Repository stars | Recent downloads | Decision |
|---|---:|---:|---|
| [bytemuck](https://crates.io/crates/bytemuck) | [1089](https://github.com/Lokathor/bytemuck) | 157526236 | Eligible for a relevant topic |
| [zerocopy](https://crates.io/crates/zerocopy) | [2656](https://github.com/google/zerocopy) | 362135368 | Eligible for a relevant topic |

Neither repository was archived when queried. Latest stable versions were bytemuck 1.25.2 and zerocopy 0.8.66. Both are listed under Topic-Specific Candidates in `library-selection.md`. bytemuck is close to the star floor; recheck it with the next audit.

## Split Criteria

A reference file is the unit loaded for one question, so a file should hold what one kind of question needs and nothing that question never uses. Length is not a criterion: it neither starts nor blocks a split, and every practice reference is reviewed.

Split a group of sections into its own file when all three hold:

1. **Distinct question.** Users ask about the group in words that differ from the rest of the file, so it can have its own routing row whose signal does not overlap another row.
2. **Complete on its own.** The group carries the explanation its question needs: how the mechanism works, when the pattern applies, its pitfalls, and an example.
3. **Independent.** The group shares no example code or types with the rest, has no positional reference such as "the example above", and reads without definitions that only the rest provides.

Keep sections in one file when any one holds:

4. **Shared example.** The sections continue one example or scenario.
5. **Candidates of one question.** One question compares the sections as alternatives or scans them as candidates, such as the primitives for shared state or the changes that can lower a runtime cost.
6. **Not asked on its own.** The group only follows up another group.

When a split separates a decision table from sections it selects among, the file that keeps the table links to the files that received those sections.

Evidence used for each decision: code identifiers shared between sections, positional references, internal links, decision tables, routing signals in `SKILL.md`, and the 18 evaluation prompts.

## File Mapping

| Previous file | New file | Question it answers |
|---|---|---|
| `ownership-and-type-design.md` | `ownership-and-borrowing.md` | Who owns, borrows, clones, or shares a value, and who may mutate it |
| | `raii-and-drop.md` | When and in what order cleanup runs, and how to write a guard |
| | `type-design.md` | How a type keeps its invariants and stays extensible |
| | `traits-and-dispatch.md` | Enum, generic, or trait object, and which traits allow it |
| `error-handling.md` | `error-types.md` | Which failure information a function exposes and in what type |
| | `error-propagation-and-reporting.md` | How errors are converted, given context, matched, and printed |
| | `panics.md` | When to panic and what unwinding or abort does at a boundary |
| `performance.md` | `performance-measurement.md` | How to benchmark, profile, and interpret a result |
| | `performance-optimization.md` | Which change lowers a measured runtime cost |
| | `compile-times.md` | Why a build is slow and which code structure causes it |
| `unsafe-and-ffi.md` | `unsafe-rust.md` | Which obligations an unsafe operation carries and how to keep them |
| | `ffi.md` | How to declare, call, and own things across a C boundary |
| `api-and-crate-design.md` | `api-design.md` | How the public surface is named, converted, and documented |
| | `crate-compatibility.md` | Whether a change breaks users: SemVer, features, MSRV, dependencies |
| `lints-and-diagnostics.md` | `compiler-diagnostics.md` | What a borrow, lifetime, or Send error is asking for |
| | `lints.md` | Which lints to enable and how to configure them |
| `concurrency.md` | `concurrency.md` | How threads move or share work: threads, channels, Send and Sync, pools |
| | `synchronization.md` | Which primitive protects shared state: locks, lazy initialization, atomics |
| `collections.md` | `collections.md` | Which container fits and how its operations behave |
| | `graphs-and-trees.md` | How to represent nodes with parent or cyclic links |

Sources recorded per document in `2026-09-18-sources-and-verification.md` and `2026-09-21-reference-sources.md` apply to the new files that received the corresponding sections. Clippy group placements now appear in `lints.md`, `performance-optimization.md`, `synchronization.md`, `unsafe-rust.md`, `error-types.md`, `error-propagation-and-reporting.md`, `panics.md`, `api-design.md`, `ownership-and-borrowing.md`, and `raii-and-drop.md`.

## Decisions Under the Criteria

Groups split although they are short, because conditions 1 through 3 hold and none of 4 through 6 does:

- **Compile times.** A slow-build question never uses the runtime sections, and a runtime question never uses this one. `SKILL.md` already names build time as a separate cost.
- **Graphs and trees.** The arena-with-indices pattern is not a row of the collection selection table, and no collection operation section refers to it. The shared-ownership section links to it as the alternative to `Rc` with `Weak`.
- **RAII and drop order.** Cleanup timing is not one of the alternatives in the borrow, own, or share decision, and both sections bring their own examples.
- **Panics.** Unwinding, abort, and boundary behavior are asked about separately from error type design.

References and groups kept whole, with the deciding condition:

| Reference or group | Condition | Evidence |
|---|---|---|
| `async-and-parallel-execution.md` | 3 | The supervisor and CPU-pool examples combine admission limits, blocking work, and cancellation; the cancellation sections rely on the future, task, and handle definitions in the opening section; evaluation prompt 8 needs both parts |
| `webassembly.md`, `simd.md`, `modules-and-crate-boundaries.md`, `workspaces-and-monorepos.md` | 4 | Each carries one example through its sections (pixel kernel, slice addition from scalar reference to dispatched kernels, port parser, engine workspace) |
| `memory-and-allocation.md` | 5 | The storage table compares reuse, pools, arenas, and allocators; evaluation prompt 13 spans them |
| `build-configuration.md` | 5 | Settings are compared against each other per objective; the recipes refer to the CI section |
| `embedded-and-no-std.md` | 5 | The target and execution tables select among the patterns; evaluation prompt 11 spans them |
| `library-selection.md` | 5 | One admission policy and its catalog |
| `collections.md` after the split | 5 | Operation sections are read after the selection table, and several cover sequences and maps together |
| Runtime changes in `performance-optimization.md` | 5, 1 | One cost question scans them; allocation and parallelism overlap the signals of other routing rows |
| Primitives in `synchronization.md` | 5 | They are the alternatives of the model table in `concurrency.md` |
| Sections of `unsafe-rust.md` | 5, 3 | The opening section enumerates the unsafe operations that the later sections cover; one section refers to the `FixedVec` example of another |
| Features and no_std support in `crate-compatibility.md` | 5 | The SemVer table classifies feature and no_std changes |
| Patterns in `type-design.md` | 5 | They are alternatives for controlling construction, validity, and extension |

## Item-Level Division

- Common Mistakes, Availability by Version, and Practical Boundaries were divided item by item among the new files. Body sections moved verbatim.
- The Lint Policy table of `error-handling.md` was divided by row: two rows each to `error-types.md` and `error-propagation-and-reporting.md`, four to `panics.md`.
- Availability rows that listed several additions were divided by addition. A row prefix such as "Edition 2024:" is repeated where both halves need it.
- One availability item was divided in two: "edition 2024 capture and drop-order rules" became "edition 2024 capture rules" in `traits-and-dispatch.md` and "Edition 2024 drop-order rules" in `raii-and-drop.md`.
- One sentence appears in two files: "Sealed traits and non_exhaustive types address specific extension policies rather than being mandatory on every public type." (`type-design.md` and `traits-and-dispatch.md`).
- One connective changed: "Queues and task limits also bound different resources" lost "also" because the preceding sentence moved to `synchronization.md`.
- The edition-2024 introductory paragraph of `unsafe-and-ffi.md` is kept in both `unsafe-rust.md` and `ffi.md`.
- Link text changed in seven places where it named a file that no longer holds the target: "ownership and type design" (2), "error handling" (2), "unsafe and FFI" (1), "collections" (1, now "graphs and trees"), and the one-time initialization pointer from interior mutability, which now targets `synchronization.md#one-time-and-lazy-initialization`.
- Each new file has a new introductory paragraph that points to its sibling files.
- The routing table in `SKILL.md` grew from 22 to 33 rows so that every new file has a direct row.

## Verification

Performed locally with rustc 1.99.1 (aarch64-apple-darwin).

- Section conservation was checked by script against the pre-split files: every body section appears in exactly one new file with identical lines apart from the seven link-text changes; every Common Mistakes bullet, Lint Policy row, and Availability addition appears exactly once, except the availability item divided in two; every Practical Boundaries sentence is present, with the one duplicate and the one connective change listed above.
- 504 package-local Markdown links and anchors resolve, including `updates/` and `evals/`. All 29 practice references are linked from `SKILL.md`.
- The 103 fenced `rust` blocks were compiled one by one as libraries with edition 2024 and `--emit=metadata` before and after the split. 97 compiled both times; the same six parts of multi-file examples fail standalone, all in references that were not split.

## Limits

No evaluation case was executed, so this record does not show that the split or the corrections change answer quality. Whether a question is "asked on its own" is a judgment supported by the listed evidence, not a measurement. Blocks tagged `rust,deps`, `compile_fail`, or `ignore` were not rebuilt. rustc 1.100.0 was not used for this revision.
