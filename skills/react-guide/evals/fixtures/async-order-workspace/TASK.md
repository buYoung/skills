# Incident ORD-4821: order workspace corruption

The browser CSR screen is deployed from this fixture. Production telemetry and support reproduction provide the following sequence:

1. Select order A, then order B before A finishes. B appears first; A later replaces it.
2. A parent telemetry render recreates `onResolved` without changing `orderId`. Network traces show another request.
3. While an order is visible, type an internal note and trigger a refresh. The entire screen falls back to loading and the draft disappears.
4. A failed request leaves plain text with no announced status and no recovery control.
5. The audit panel occasionally loses its internal expansion state after otherwise unrelated workspace renders.

The public component contract is `OrderWorkspace({ orderId, onResolved })`. The request contract is `fetchOrder(orderId, { signal })`; existing callers rely on that shape. The resolved dependency versions and `OWNERSHIP.md` are authoritative.

Restore these observable behaviors without adding dependencies, weakening Hook checks, or changing public contracts. Avoid speculative build changes. `REPORT.md` must identify the independent root causes, edited ownership boundary, verification actually performed, and browser/runtime checks that remain.
