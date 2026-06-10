---
#### Task Info
- Working agent : claude code (fable 5)
- Verification/analysis agents : 3 sub-agents — documentation quality evaluation, script execution verification, adversarial review (each in an independent context)
- Task type : Skill hardening (patch included — `changes.patch`)
- Review method : the adversarial agent built real fixtures and executed the scripts; only failure paths proven by execution were adopted
- Design decision : the "externally-authored AGENTS.md with unnumbered headings" scenario was confirmed as an intended scope limit, not a defect — the guard "never modify an AGENTS.md this skill did not generate" is now codified

---

### Proven Failure Paths and Resolutions

| Severity | Finding | Resolution |
|---|---|---|
| Major | Updating an externally-authored (unnumbered headings) AGENTS.md marks all 5 standard sections missing, producing a duplicated document | New skill-ownership guard: zero standard-heading matches → do not modify, report; full regeneration only on explicit request (`SKILL.md` Step 5, `update_strategy.md` > Skill-Generated Files Only) |
| Major | Document type transition (single ↔ monorepo) forces full regeneration that silently drops custom sections | Forced regeneration must carry custom sections over verbatim and obtain user confirmation before overwriting |
| Major | Monorepo false positives: empty `[workspace]` (crate-detach idiom), single-app Android `include ':app'`, commented-out `include`, `"keywords": ["workspaces"]` | `detect_monorepo.py` made precise (JSON parsing, comment stripping, `members` required, 2+ includes) + new provisional rule: fewer than 2 discovered packages → single repo |
| Major | Budget contradiction: whole-file length check vs byte-for-byte custom preservation cannot both hold | `character_limit` scope codified as "preamble + standard sections"; custom sections excluded and never trimmed |
| Minor | `## ` lines inside code fences mistaken for section headings → silent document corruption | Fence (``` / ~~~) state tracking added to `parse_sections.py` |
| Minor | Both scripts expose tracebacks on non-UTF-8 files | `parse_sections.py`: clean error + exit 2; `detect_monorepo.py`: `errors="replace"` |
| Minor | LOC explosion in git-less directories from counting node_modules (measured 1 → 120,001) | `node_modules`/`vendor`/`dist` excludes added to `loc_to_limit.py` and the measurement command |
| Minor | Mandatory type-check command vs build-command anti-pattern verification conflict | Anti-pattern exception codified: the discovered type-check command in Working Agreements is verification guidance |
| Minor | User additions inside standard sections silently deleted | New verification item: report wording removed from managed sections before overwriting |
| Minor | uv/rye markers missing from `monorepo_detection.md` (out of sync with script and SKILL.md) | uv/rye markers and a Python package-discovery entry added; all three sources synchronized |
| Minor | Personal machine absolute path hardcoded in `update_strategy.md` | Anonymized (`<project-root>/AGENTS.md`) |
| Info | Trigger over-expansion ("Use when setting up a new repository") | Description narrowed to AGENTS.md; CLAUDE.md/README declared out of scope |
| Info | Monorepo All mode skipped Step 1, omitting per-package Generate/Update decision | Per-package Step 1 decision (and ownership check) now explicit |
| Info | "Largest section" note in `loc_measurement.md` contradicts actual allocation (25% < 35%) | Note corrected |
| Info | Stale updates/README index + unmet mandatory-patch rule | Index fully refreshed; patches made optional |
| Info | Explicit language requests ignored ("English only" had no exception) | Exception added: follow an explicitly requested document language |
| Info | `--from-stdin` silently misparses thousands separators (`50,000` → 50) | Separator-tolerant regex + clean error when the Total row is missing |

### Regression Verification

- `detect_monorepo.py`: all 7 false-positive fixtures (keywords-only, empty workspace, comments, single include, etc.) return false; all 8 true-positive fixtures (npm array/object, cargo members, gradle multi/first-line/composite, latin-1, uv) return true.
- `parse_sections.py`: fenced `##` ignored, unclosed fence handled, latin-1 yields a clean error; existing standard/custom/missing behavior unchanged.
- `loc_to_limit.py`: git-less node_modules directory normalized to LOC 1; boundary values (10000/10001/1000001) unchanged; real-repo run normal.

### Defenses Confirmed (no change needed)

Reordered standard sections preserved, duplicate headings (first occurrence only), preamble/HTML comment preservation, tiny-repo limit (ceiling, not floor), code-less monorepo root — all already defended by the existing design.
