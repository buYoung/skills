# Content Quality and Information Retention

Use this reference during repository analysis, drafting, compression, and final verification. Its purpose is to retain the facts that change how a contributor safely edits the repository. More names or a longer document do not by themselves make a better guide.

## Select Decision-Relevant Facts

For each meaningful behavior boundary or cross-cutting flow, identify the applicable facts below and verify them against current source or a current documented contract:

- **Change entry point**: where the contributor should start, including the shared owner rather than only one caller.
- **Behavior choices**: settings, modes, or supported alternatives that change execution, and how those choices reach the final consumer.
- **Conditions and recovery**: the trigger, guard, exception, fallback, and observable outcome; avoid converting a conditional fallback into a universal guarantee.
- **State and resource lifecycle**: initialization, migration, switching, cancellation, stale-result rejection, cleanup, and the owner responsible for them.
- **Compatibility and external effects**: legacy data, public contracts, persistence, registrations, notifications, and other side effects the change must preserve.
- **Verification surface**: a concrete existing test area, consumer, or manual surface that exercises the stated behavior.

Keep the identifiers needed to find or distinguish these facts. Name a small set of behavior-changing alternatives rather than replacing them with a count such as "three engines" or "multiple modes". For a large registry, identify the authoritative registry and selection contract instead of copying its entire inventory. Do not collect every function, dependency, or directory name.

Describe complete relationships: an entry point without its safety condition, or a fallback without its trigger, is incomplete. Trace representative callers through shared layers to the consumer before treating the relationship as verified. Recurrence helps identify a pattern, but a single critical entry point still deserves coverage.

Prioritize even a one-off boundary when it installs a global hook, may overwrite persisted state, recovers from external I/O failures, owns native/foreign resources, or propagates a setting/event to multiple consumers. The impact of a missed condition matters more than how many files repeat it.

## Check Coverage Before Selecting Behaviors

Build a compact coverage table in the temporary working record before using history to prioritize work or drafting prose. Seed Generate mode from the repository's documented capabilities and authoritative public surfaces: registrations/manifests, exported APIs, routes, commands/actions, major UI tabs, and lifecycle/service registrations as applicable. Confirm their current owners in source; README text alone does not prove implementation.

In Update mode, also give every old managed Stable boundary, Active route, and core behavior a coverage row, then add newly exposed surfaces. Do not silently lose an old row because its heading was removed or its historical classification changed. Group duplicate rows only when their current relationship is the same and record the grouping.

Each row records the exposed surface or old item, current owner/consumer evidence, why it affects safe contribution, and a `selected` or evidence-based `excluded` disposition. This table catches omissions; it is not a feature inventory to copy into the output. A registered lifecycle hook or live state/compatibility guard is not low-value merely because it is used once or has no recent commit. An empty history window, lack of recurrence, space pressure, or preference for other features alone cannot exclude such a live contract.

## Finish Tracing the Selected Behavior

For each selected important boundary, follow the entry point through its direct behavior-defining helpers until the relevant decisions and effects are visible. Stopping at a wrapper named "normalize", "restore", "migrate", or "recover" does not establish its contract. Read the implementing helper as well as its caller. This is bounded tracing of selected behaviors, not an instruction to enumerate every branch in the repository.

Also inspect the caller's continuation after the helper returns: publication, multi-consumer notifications, cleanup, or UI application may be owned there rather than by the shared helper. A setter or transformation returning successfully is not necessarily the end of the user-visible flow.

Resolve the applicable relationships before drafting:

- For a setting, input form, or mode, identify the actual supported alternatives and the consumer dispatch, including rejected or unsupported cases that change safe use.
- For a guard, inspect both the applied path and the bypass/delegation path. State which objects or consumers are affected and which retain their original behavior.
- For recovery, inspect the caught failure, extra eligibility conditions, attempted alternatives, and the final result when recovery is exhausted. Keep separate recovery mechanisms separate.
- For reused state or caches, find where the container is created and cleared to establish whether reuse lasts for a call, component, project, or process.
- For lifecycle ownership, inspect installation/allocation and every release, disposal, or restoration path, including error-owned resources and any identity/ownership condition that protects someone else's later replacement.
- For migration or switching, inspect both the source and destination, the conditions that prevent overwriting existing values, and the actual recipients of any resulting notifications.

Treat non-applicable fields as such rather than inventing behavior. If a necessary relation is still unknown, trace the relevant helper or mark the limitation; do not fill it with a generic statement that suggests it was verified.

Give each selected row a trace status of `open` until the applicable relationships have concrete source evidence. For a multi-stage pipeline, identify which direct helper actually implements each stage's supported inputs, branching, state reuse, recovery, and output effects; listing "parse → normalize → generate → validate" is not a closed trace. Evidence must identify the actual file and implementing symbol or line window, not just a directory or a group such as "the services". Mark the row `closed` only after the applicable choices, conditions, lifetimes, failure results, ownership, and recipients are accounted for. Unknown is not the same as non-applicable.

## Build a Working Fact Record

Keep a compact working record while analyzing and save it to a temporary scratch file before drafting so the final review can inspect the actual record rather than rely on recollection. It is an internal drafting aid, not a new section in the generated `AGENTS.md`, a mandatory user questionnaire, or a permanent repository artifact. Do not put it in the target repository. In explicit evaluations it may be retained with run evidence.

For each important behavior, record its owner/entry point and consumer; applicable choices, trigger/guard and bypass path; scope/lifetime; recovery/cleanup/compatibility effects and notification recipients; current evidence locations; and proposed output section. Group these related fields into one concise row or bullet, omitting inapplicable fields. A short source condition excerpt can disambiguate a claim, but do not transcribe entire files. "Has a cache", "restores the handler", or "migrates settings" alone is an incomplete record when source defines a narrower lifetime or precondition.

During final review, add the exact output sentence or bullet that conveys each row, or its correction/exclusion reason. Only `closed` rows may be marked Included, and only when the applicable decision-relevant fields are conveyed together, not merely when the owner's identifier occurs somewhere. Read the scratch record and the final document together; an incomplete record is not evidence that a missing condition was unimportant.

### Generate Mode

Build the record from current repository discovery. Check decision points, failure paths, and lifecycle owners as well as the happy path; there is no old document to supply missing clues. Verify that the facts discovered during analysis survive into the assembled output.

### Update Mode

Before rewriting, extract decision-relevant facts from the old analysis-derived managed sections into the working record. Treat them as inspection leads, never as proof that they are still correct. Also discover current facts that the old document omitted.

Reconfirm each retained relationship against current source or contracts. Classify its final disposition as:

| Disposition | Required basis |
| --- | --- |
| Included | Current evidence supports it and the assembled document conveys it, possibly in different wording or a more appropriate section |
| Corrected | Current evidence supersedes the old claim; the output describes the current behavior and does not leave the old contradictory claim in a managed section |
| Excluded with reason | The claim is obsolete, unsupported, duplicated elsewhere, outside the document's scope, or does not affect a contributor's decision |

Document-wide deduplication is valid: record the destination that still conveys the fact. An entry point that merely tells the reader to inspect source does not substitute for an omitted safety condition. If a fact is covered by an authoritative linked repository document, retain the concise condition and a precise route to that document rather than a generic "see docs" instruction.

The old wording need not survive; verified meaning and necessary identifiers should. Reanalysis can produce the same identifier or factual statement without being blind reuse of an old section. Rebuild `Working Agreements` from its canonical reference and confirmed repository-specific language/verification details; do not promote arbitrary old managed policy into a new standing rule. User-owned custom sections remain byte-for-byte preserved outside this semantic comparison.

History chooses where to investigate and whether a route belongs in `Active Change Routes`; it does not decide whether a live contract survives. If an active route no longer has a recent-history delta, preserve its currently verified safety conditions in the appropriate stable boundary or core behavior. Moving or removing a historical classification is not a reason to abbreviate a live migration, guard, or compatibility condition.

## Allocate and Compress Without Losing Meaning

The proportions in [loc_measurement.md](loc_measurement.md) are starting allocations, not independent ceilings. The hard limit is the combined preamble and managed sections. Move unused capacity to the sections with decision-relevant content, retaining the established section responsibilities. Do not move content to the wrong section or add filler merely to meet a ratio.

Draft the closed, high-impact contracts in Ownership Map/Core Behaviors first, keeping each fact in its appropriate section without repeating it across both. Only then spend the remaining space on repository-specific conventions. Naming, role suffixes, generic logging advice, and resource inventories are not a mandatory checklist and must not consume the space needed for verified conditions. This order applies to the first draft, not only to a final attempt to trim an overlong document.

Compress in this order:

1. Remove repetitions, including broad ownership details already covered by a parent stable boundary.
2. Shorten generic advice and inventories that do not distinguish this repository's work.
3. Combine related descriptions within the appropriate owner or flow without erasing their separate conditions.
4. Tighten sentence structure while retaining necessary entry points, alternatives, guards, recovery conditions, cleanup, and compatibility obligations.

Keep the decision-relevant fields of a behavior together during compression. Before shortening a protected condition, remove generic naming/role inventories, broad logging advice, and repeated resource or owner descriptions that do not change how work is done. The template's categories are discovery prompts, not a list of bullets to fill at the expense of verified contracts.

For example, "the loader retries" loses important meaning if retries occur only for one failure class. Preserve the triggering condition even if surrounding explanation is shortened. Do not replace specific APIs with vague terms such as "the helper" solely to fit an initial section allocation.

Keep fresh content evidence-based rather than padding to the total limit. If important verified facts still cannot fit after compression and reallocation, do not silently drop them or raise the total limit. Complete a reviewable candidate, report the excess and the facts that would be lost, and ask the user to choose a scope or limit change before writing.

## Verify the Assembled Document

Run this comparison after final compression, since information can disappear after the initial draft:

- Every documented/registered capability and old managed boundary, active route, or core flow from the coverage table has a current evidence-based disposition. No row disappeared during historical reclassification. Every selected row is `closed` before inclusion; unresolved behavior requires further source tracing or an explicit limitation rather than an unsupported summary.
- Every important verified fact has an included, corrected, or evidence-based excluded disposition. Space pressure alone is not a valid reason to exclude an important fact.
- Each included fact appears meaningfully in the final text, not just as an isolated identifier. Necessary choices and conditions are explicit; caller-to-consumer relationships have not become misleading summaries.
- Reverse-check every final claim about recovery, migration, restoration, reuse, guards, or resource ownership against its implementing helper: does the sentence retain the applicable trigger, non-applicable/delegation path, lifetime, result, and cleanup or recipient boundary? If the record also lacks these fields, reopen the helper instead of treating record/output agreement as success.
- Corrected facts reflect current code. Unverified old claims are not retained for apparent completeness, and new unsupported claims are not added to replace them.
- The document preserves section responsibilities, total character limit, management rules, and custom-section bytes. Exceeding an initial section allocation alone is not a failure.

An unexplained loss or distortion of an important fact fails verification even when headings, length, and freshness checks pass. Revise the candidate before writing. In the user-facing summary, report meaningful corrections and exclusions with their reasons; do not dump the entire working record or replace the existing dropped-managed-wording report required by update mode.
