# Typst Creator Revision — 2026-11-27

This revision documents the 0.15 folding of `par.first-line-indent`. The compatibility index already named the boundary but routed only to the 0.13 reference. The supported range remains stable Typst 0.13.0–0.15.1; the GitHub latest release was still v0.15.1 (2026-07-17, not a prerelease) when checked on 2026-11-27.

## Changes

- `references/versions/0.15.md` lists the folding under Behavior Changes, with the single-dictionary form for source shared with 0.13 or 0.14.
- `references/versions/index.md` routes the first-line indentation row to both the 0.13 and 0.15 references.
- `references/styling.md` notes the 0.15 behavior in the `par` parameter table.
- `evals/fixtures/typst-0.15.typ` asserts that `amount` and `all` set in two scoped rules fold into one value. The assertion is scoped to a content block, so the fixture's other output is unchanged.

## Sources

- [0.15.0 changelog](https://typst.app/docs/changelog/0.15.0/), Model: "The `par.first-line-indent` property will now _fold_, meaning that partial dictionaries across different set rules or `par` calls are combined".
- `crates/typst-library/src/model/par.rs` at tag `v0.15.0` marks `first_line_indent` with `#[fold]` and implements `Fold for FirstLineIndent`; the same field at `v0.14.2` has no `#[fold]`.

## Verification

- `python3 -m unittest discover -s scripts -p 'test_*.py'`: 11 tests passed.
- `python3 scripts/validate_version_support.py --compiler 0.15.1=<typst>` with the local `typst 0.15.1`: 11 checks passed (version check and 10 fixtures), no warnings. The other six releases were not installed and were not checked in this revision; the fixture's 0.15.0 behavior rests on the tagged source above.
- With typst 0.15.1, the previous and revised `typst-0.15.typ` rendered to byte-identical single-page PNGs at 72 ppi.
- Follow-up on 2026-11-27 with the official macOS arm64 release archives of 0.13.0, 0.13.1, 0.14.0, 0.14.1, 0.14.2, 0.15.0, and 0.15.1: `validate_version_support.py --require-all` passed all 65 checks with no warnings and no unchecked releases. The fold assertion block alone compiles with 0.15.0 and 0.15.1 and fails with 0.14.2 (`dictionary does not contain key "amount"`).
