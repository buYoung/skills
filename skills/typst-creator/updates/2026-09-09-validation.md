# Typst Creator Validation — 2026-09-09

This revision corrects API descriptions, adds inherited-feature routing and practical document guidance, and expands executable compatibility checks. The supported range remains stable Typst 0.13.0–0.15.1.

## Environment

Verification ran on macOS arm64 with Python 3.14.6, official Typst macOS arm64 release archives, Poppler, ImageMagick, and available system fonts. The Python tools target Python 3.9+ syntax/APIs; older Python runtimes were not executed. No compiler replaced the system installation.

| Release | Executable version evidence |
|---|---|
| 0.13.0 | `typst 0.13.0 (8dce676d)` |
| 0.13.1 | `typst 0.13.1 (8ace67d9)` |
| 0.14.0 | `typst 0.14.0 (dd1e6e94)` |
| 0.14.1 | `typst 0.14.1 (eb2027e5)` |
| 0.14.2 | `typst 0.14.2 (b33de9de)` |
| 0.15.0 | `typst 0.15.0 (3ae52774)` |
| 0.15.1 | `typst 0.15.1 (9dfd3a08)` |

Archives came from the [official release repository](https://github.com/typst/typst/releases), using each release's `typst-aarch64-apple-darwin.tar.xz` asset. Download URLs, archive SHA-256 values and executable paths were recorded in the temporary run manifest. Computed hashes identify the downloaded artifacts; they are not an independent signature verification.

## Executable and Output Checks

| Check | Result |
|---|---|
| Validator regression suite | 11 tests passed |
| Full `--require-all` fixture matrix | 65 checks passed: 7 exact version checks and 58 PDF compilations; no failures or warnings |
| Reference code blocks | 506 compilations passed: 483 independent-snippet checks and 23 checks with bundled assets; no failures or warnings |
| HTML | Basic semantic export passed on all 7 releases; experimental warnings retained |
| Bundle | Two linked HTML files produced on 0.15.0 and 0.15.1; experimental warnings retained |
| Local Markdown links and whitespace | No broken package-local file links; `git diff --check` passed |

The output checks confirmed these properties on every supported compiler:

- Long report: 4 A5 pages, all 60 observations in order, repeated headers on all 3 table pages, page numbers 1/4 through 4/4, footnote, bibliography, numbered references and PDF destinations.
- Presentation: exactly 3 numbered 16:9 pages, with overview/method/results and no initial blank page.
- API regression document: landscape A4 and numbered heading/table/figure references.
- On 0.15.0 and 0.15.1, each trim edge was inset by 3mm from the bleed area and the inclusive sequence contained 1, 2, 3.
- Resource fixtures propagated caller-loaded bytes through imports to a computed value of 84; 0.15 path fixtures preserved caller origin through a helper in another directory and decoded 42.

The representative PDFs were rendered. Their contact sheets were byte-identical across the seven releases, and the shared rendering was visually inspected for clipping, overlaps, continuation headers, numbering and figure placement. Korean text in the behavioral paper outputs was also visually inspected. These observations concern these fixtures, not arbitrary document rendering equivalence or PDF/UA conformance.

See the [fixture instructions](../evals/fixtures/README.md) for reproducible commands and expected output. Reference snippets needing assets use the bundled directory; stdin checks set the project root to the fixture directory so their relative resources resolve correctly.

## Behavioral Comparison

Independent agents used the original skill snapshot and the revised skill with the same prompts, assets and executables. Source files, compiled PDFs, handoffs and available renders were checked; exact compilers independently recompiled the generated sources. The compiler-unavailable scenario was not compiled, as its prompt forbids execution.

| Evaluation | Revised skill | Original skill | Interpretation |
|---|---:|---:|---|
| Initial run: 10 completed matching pairs | 32/36 expectations | 34/36 expectations | The draft omitted explicit reference reporting in some handoffs; both configurations omitted a rendering-equivalence caveat in range work |
| Targeted follow-up: cases 1, 2, 3 and 6 | 15/15 expectations | 12/15 expectations | The explicit handoff contract restored reference provenance and range verification limits |

The initial original-skill print proof inserted `#divider` as a function value, which printed the word `divider` while compiling successfully. This was counted as a functional failure, illustrating why compile-only checks are insufficient. The initial draft's reporting regression was corrected rather than discarded from the record.

The full initial run produced 21 of 22 requested artifacts sets. Original-skill environment-detection case 4 was blocked twice by automatic approval review, which classified its temporary output writes as outside the user's request. No source, PDF or handoff was generated for that run. It is recorded as an infrastructure limitation, excluded from paired statistics, and has not been represented as a skill failure or a successful verification. The revised-skill case 4 detected and compiled with the supplied 0.14.2 executable, but its initial handoff omitted reference filenames; the generalized reporting fix was assessed in the targeted follow-up.

There was one run per prompt/configuration. The follow-up covered the affected reporting cases, not a fresh run of every behavioral prompt. Full executor transcripts, elapsed durations and token counts were not provided by the agent API, so no timing/token comparison or statistical reliability claim is made. The standalone review reports retain both iterations and their individual expectations.

## Limits

This verifies the supplied examples and selected generation behaviors on macOS arm64. It does not certify all APIs, operating systems, installed fonts, third-party packages, accessibility standards or future Typst releases. Presentation-package APIs were routed to their versioned documentation rather than installing or claiming compatibility for untested package releases.
