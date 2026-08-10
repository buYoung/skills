# PERF-944: one price tick stalls the grid

`profile.json` was captured from the production profiling build with a fixed 10,000-row dataset. Updating the server price for one row causes all row components to render and the commit takes 184 ms. Adding memoization in an abandoned branch did not solve the invalidation source and broke a draft input comparator.

Desired observable behavior:

- Reordering, inserting, or removing IDs updates the grid structure.
- Replacing a row value updates that rendered row without invalidating unrelated rows.
- An in-progress row-local draft survives a server price replacement for the same row.
- `Grid({ store })`, the exported `GridRow`, and every public store method retain their contracts.

Find the ownership error from the supplied code and fix the narrowest responsible layer. Do not introduce deep serialization/equality, mutate rows in place, add dependencies, or edit build-owned configuration. `REPORT.md` must cite the supplied measurement, explain the invalidation chain, state the expected render scope, and avoid presenting an unrecorded post-fix duration as measured.
