# SSR-104: profile hydration and request contamination

This is an existing Node SSR integration on React 18.3.1. Keep `renderPage({ requestId, loadProfile })`, `Profile({ store, renderedAt })`, and `createProfileStore(initialProfile)` with `subscribe`, `getSnapshot`, `getServerSnapshot`, `replace`, and `increment`. No consumer relies on the module singleton. The host serves the fixed `/assets/client.js` entry from an existing build; build/host changes are outside this incident.

Reports show one request's name in another user's HTML during overlapping loads, repeated external-store snapshot warnings, server/client IDs and timestamps differing, and hydration recovering by replacing server content. A visitor with cached profile data sees their server profile flash to another value. Live updates before a delayed subtree hydrates also change what its server snapshot returns. Typing a note and then incrementing visits loses the note.

Repair server rendering and hydration without removing SSR, suppressing warnings, disabling interactivity, or changing React versions. Capture request data once, preserve it through bootstrap and the first client render, isolate concurrent users, and keep later client store updates and the note input working. Cached browser profile data must not override the request profile. Preserve the initial timestamp across hydration. Arbitrary profile names can contain `</script>`; transfer data safely.

Source fixes are authorized. Do not install dependencies. Write REPORT.md separating source/store checks from real React hydration, streaming, and host/browser checks that were not run. Streaming is not required for this synchronous preloaded tree; explain the existing renderer's limitation.
