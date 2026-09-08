# Approved product UI contract
The product council approved “clear consequences before action; quiet shared surfaces” for Harbor. Validation record R7 passed a dense comparison view and an empty-state action view. This record establishes the direction, not a full runtime audit.

The supported public component is ActionButton, exported by the supplied action-button.ts. Its supported tone values are primary and quiet. Its label is required. Primary is used for the next committed action; quiet for a reversible secondary action. Both retain the same text-label convention. The implementation's internal padding constant is not a public option.

The supplied tokens.json owns action.background = #2457C5. ActionButton's primary tone consumes action.background. No disabled, loading, size, or danger API is approved by this source. The legacy-example.md is retained as historical evidence and is not supported usage.

ActionButton is an ordinary TypeScript function returning a data object with label, background, and padding fields. It has no React or JSX rendering contract. Use a direct call with label and tone, then let a separately supported consumer handle the returned data. No renderer is supplied in this fixture.
