# Reviewing software project documentation

Use the selected README or usage profile and the shared [four reader outcomes](../../shared/human-readable-writing.md#reader-outcomes). Apply checks to the requested scope; a focused correction does not require a whole-document rewrite. Review and fact-check produce findings, not edits.

## Check the actual reader path

- **Relevant:** Is the project unit, audience, and supported context clear? Does the document answer its profile's questions without unnecessary contributor, architecture, or promotional detail?
- **Findable:** Can a README reader find installation and first use? Can a usage reader enter at a task or lookup section and find the governing condition? Do real links reach the intended owners?
- **Understandable:** Are commands, substitutions, execution locations, roles, and terms clear? Do descriptions preserve defaults, version applicability, and uncertainty?
- **Usable:** Is a representative documented path complete from its stated starting conditions to a meaningful observable result? Are side effects and limits beside the affected action?

Trace the path against available implementation, manifest, packaging, release, configuration, and license evidence. Check repository-relative paths and relevant anchors. Verify material external instructions or links with primary sources when needed; distinguish inaccessible destinations from confirmed broken links.

For a README and usage pair, compare package identifiers, versions, prerequisites, install paths, commands or imports, defaults, inputs, and success criteria. Summaries may be shorter but must preserve conditions. If a companion file is outside the requested write scope, report any mismatch there without changing it.

## Findings that matter

- A plugin is documented as a standalone app, or source build instructions replace the published consumer path.
- Open-source contribution is treated as an alternative to plugin, library, or CLI behavior rather than an independent concern.
- A claimed runtime minimum, installation channel, license, default, menu action, output, or URL has no applicable evidence.
- The quick start reaches only installation or help output while promising an actual project result.
- A task depends on unstated prior setup, omits a necessary substitution, or gives unsupported repeat/recovery instructions.
- A qualification exists only in distant usage detail while the README makes an unconditional claim.
- Generated option lists bury practical tasks, or conceptual discussion obscures the next action.
- Decorative elements, empty headings, broken links, or repeated catalogs impede the profile's purpose.

Report the affected passage, reader consequence, and supporting source or missing evidence. For fact-check, prioritize factual defects over unrelated style preferences. For authoring, resolve supported defects in writable files and preserve the original exact material outside the requested change.

## State the verification limit

Distinguish source inspection, link checks, author walkthrough, observed execution, and reader/model evaluation. An example inferred from implementation is not an executed example; passing a structural package validator is not proof of software behavior or reader success. Report unverified environments and unresolved material gaps.
