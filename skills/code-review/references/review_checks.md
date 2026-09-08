# Practical Review Checks

Select only checks relevant to the changed behavior and follow evidence through the selected version. These are investigation prompts, not mandatory report sections.

| Change surface | Questions and evidence to inspect |
|---|---|
| Boundaries and defaults | What happens at zero, empty, absent, null, negative, maximum, and just-outside values? Are units, rounding, overflow, timezone, and default precedence preserved through the final consumer? |
| Authorization and trust | Is the authenticated identity authorized for the specific object/action/tenant? Can an alternate entrypoint bypass the check? Are untrusted values validated at the actual trust boundary? |
| State transitions | Which states permit the operation? Can failure leave a partially updated record/cache/UI? Do transactions and recovery preserve the intended invariant? |
| Concurrency | What interleaving makes reads stale or duplicates writes? Inspect locks, uniqueness, atomic operations, task lifetime, and cancellation propagation; do not assert a race without a reachable interleaving. |
| Resource lifetime | On success, error, timeout, and cancellation, who releases files, connections, locks, listeners, timers, and subscriptions? Can cleanup override the original failure or leak work? |
| Retry and duplicate delivery | Which failures are retried, with what bounds/backoff? Can a successful side effect be repeated after a lost response? Does idempotency survive concurrent requests and restarts? |
| Data and API compatibility | Can old readers consume new writers and vice versa during rollout? Check adapters, defaults, strict decoders, enum handling, migrations, serialization, public exports, and intended deprecation rules. |
| Performance and capacity | What is the input-size or request-rate dependent cost? Inspect repeated I/O, query fan-out, allocation, unbounded queues, and cache invalidation. Ground impact in a reachable workload, not unsupported speed claims. |
| Tests | Do assertions observe the required value and its effect at the final consumer? Can mocks hide dropped options or errors? Are promises awaited and relevant failure/boundary paths asserted? Report unexecuted checks honestly. |
| Maintainability | Does current duplication encode one policy in multiple places? Does complexity obscure an existing invariant? Does coupling force coordinated unrelated edits? Explain a bounded improvement and its immediate benefit. |
| Build and deployment | Do runtime/dependency versions support the API? Do generated artifacts match their source and actual shipped behavior? Do lock changes alter resolved dependencies, integrity, platform support, or installation beyond the manifest? |

For any concern, reconstruct the trigger and expected/actual path, seek existing defenses and intentional compatibility, then compare the base before reporting. An interesting risk is not automatically a defect.

The emphasis on surrounding context, complexity, and the validity of tests is informed by [Google's code review guidance](https://google.github.io/eng-practices/review/reviewer/looking-for.html).
