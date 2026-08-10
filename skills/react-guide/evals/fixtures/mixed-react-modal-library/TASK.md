# Release blocker: @acme/modal 4.7

The package is shared by the consumers in `CONSUMERS.md`. After a refactor, the React 18 Storybook crashes in the provider path, its imperative measurement ref never receives the dialog node, and its default import no longer resolves. Both consumer generations report that recreating an inline close callback repeatedly removes and adds the global Escape listener while the dialog stays open. Closing also leaves keyboard focus on `body`.

The fix must retain the published peer range, export names, default import, prop names, dialog semantics, and declaration/runtime agreement. An Escape press must invoke current caller behavior without lifecycle churn caused only by function identity. Focus should return to the element that opened the dialog when that element still belongs to the document.

Do not raise the supported React floor, add dependencies, or redesign the controller API. `REPORT.md` must explain which failures were compatibility defects versus Effect/focus ownership defects and state which runtime/type checks were and were not performed.
