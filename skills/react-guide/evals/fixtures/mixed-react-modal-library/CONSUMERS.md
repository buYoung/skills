# Published consumer matrix

## catalog-storybook

- React and React DOM: 18.3.1
- Imports: default `Modal`, named `ModalProvider`
- Passes a ref used to measure the rendered `HTMLDivElement`

## account-console

- React and React DOM: 19.2.0
- Imports: named `Modal`, `ModalProvider`, `useModalController`
- Recreates `onClose` during unrelated form renders

Both consumers compile against `src/index.d.ts`. A breaking export, ref, provider, or prop change is outside this release.
