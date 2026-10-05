# Plain Language for Generated AGENTS.md

Use this reference before drafting and after final compression. It applies to prose that this skill generates or rebuilds, including `Working Agreements`. It does not authorize changes to preserved custom sections, the existing title or preamble, management markers, standard headings, section numbers, or document scope. Follow the existing update and character-budget contracts.

## Basis and Limits

ISO 24495-1:2023 describes plain language guidance for written documents, including technical writing and most written languages. The International Plain Language Federation, which initiated the standard, publicly summarizes four reader outcomes: relevance, findability, understanding, and use. Apply those outcomes together; simpler words alone do not make a useful guide.

The practices below adapt those public principles to contributor guides. They are not a reproduction of the full standard, a clause-by-clause conformity assessment, or a certification scheme. Do not describe generated documents as ISO-compliant or certified. Do not append an ISO notice or a plain-language checklist to the generated `AGENTS.md`.

Sources checked on 2026-10-06:

- [ISO 24495-1:2023 official catalogue and scope](https://www.iso.org/standard/78907.html)
- [International Plain Language Federation: the four principles and their language-neutral scope](https://www.iplfederation.org/iso-standard/)

## Write for the Contributor's Task

The primary reader is an AI agent making changes in this repository; a human maintainer also needs to review the guide. Assume software knowledge and source access, but do not assume familiarity with the project's private names, acronyms, or unwritten history. Use more specific audience information when the request supplies it. Use the request and confirmed repository scope to identify the reader's likely changes and needed decisions. Keep this context in the existing temporary working record; it is not a new questionnaire or output section.

For a monorepo root, focus on choosing the responsible package and shared contracts. For a package or single repository, focus on the entry point, implementation choice, protected behavior, and verification surface. Keep the existing section responsibilities and optional-section evidence gates.

| Reader outcome | Apply while drafting | Check after compression |
| --- | --- | --- |
| Relevant | Retain facts that affect the reader's change; state necessary choices, conditions, and consequences. Remove generic advice before protected contracts. | Can the reader distinguish the supported action from the cases where it does not apply? |
| Findable | Use the required section headings. Within each section, group related decisions and put the entry point or task in the bullet label or first actionable clause. Use descriptive link text and precise paths when a reference is needed. | Can the reader locate the owner, rule, exception, and verification surface without searching an unrelated section? |
| Understandable | Use direct verbs, explicit actors, familiar terms, and stable names. Explain necessary project-specific terms briefly at first use. | Are references such as "it", "this", and "the helper" unambiguous? Does the prose preserve the source's conditions? |
| Usable | State what to inspect, change, preserve, or verify, and the concrete surface that shows the result. Keep related conditions beside the action they qualify. | Can the reader identify the next action and its expected result from the guide? |

## Sentence and Bullet Practices

- Lead with the decision or action. Put a condition first when it determines whether the action applies: "When [condition], [owner] [action]." Keep exceptions adjacent to their rule.
- Prefer active sentences that name the responsible component: "`SettingsStore` writes defaults only when the key is absent." Passive wording is useful when the actor is irrelevant, but must not hide ownership.
- Keep one coherent task or relationship per bullet. Use separate sentences for the entry point, behavior, and verification when a single sentence becomes hard to follow. Split independent rules into separate bullets; retain the connection between a rule and its exception.
- Prefer verbs to abstract noun phrases: "validate the input" rather than "perform input validation". Remove filler such as "in order to", "it should be noted", and claims of robustness without a defined behavior.
- Keep paths, symbols, API names, configuration keys, values, units, and code examples exact. Plain language must not replace a necessary identifier with a vague substitute. Use the same term for the same concept throughout the document.
- Use technical terms when they help a software contributor act accurately. Briefly explain unfamiliar project-specific terms; do not expand every familiar term or replace a precise distinction with a misleading simplification.
- Separate observed behavior from contributor instructions. Describe what code currently does in declarative sentences; use direct imperatives for actions the contributor should take. Preserve the strength and scope of obligations, permissions, and prohibitions when rephrasing.
- Write in the output language required by the template or user. Adapt sentence structure to that language; do not impose an English word count, reading-grade target, fixed sentence length, or universal acronym rule.
- Make Markdown scannable with informative bullet labels and short related paragraphs. Use lists for parallel items or a meaningful sequence, without adding new standard sections or converting the guide into a commands catalogue.

## Examples of Wording

These examples illustrate style only. They are not repository facts to copy into output.

| Weak wording | Clearer wording |
| --- | --- |
| "The loader retries external failures only upon timeout qualification, with other failures propagated." | "The loader retries only timeout failures. It passes other failures to the caller." |
| "Upon a timeout, utilization of the cached response is permissible solely when its key matches the request; when no key matches, the timeout is propagated." | "On a timeout, you may use the cached response only if its key matches the request. If no key matches, propagate the timeout error." |
| "Restoration of the original handler upon disposal is conditional on continued identity equivalence between the currently registered handler and this component's wrapper." | "On disposal, restore the original handler only if the current handler is still this component's wrapper." |
| "Cache reuse is restricted to a single normalization call, with a new cache per call." | "The normalizer reuses cached documents within one call. Each call gets a new cache." |

Only use the clearer versions when current source confirms their owners, conditions, values, and verification surfaces. A more direct sentence that invents a retry count or narrows a contract is still wrong. Preserve permissions such as "may" and limiting conditions such as "only if"; a rewrite must not change them into unconditional instructions.

## Review the Finished Guide

After compression, read the assembled document alongside the existing fact record. Review each selected important contract from the contributor's perspective: find its owner or entry point, identify the applicable choice and exception, decide the next action, and locate the expected result or verification surface. Include applicable Working Agreements in this review. For a monorepo root, check package selection and shared contracts rather than inventing package-internal patterns. If any part requires guessing, revise the wording or reopen source tracing. Do not add a separate testing strategy or new verification commands to solve a prose problem.

Check all four reader outcomes and the information-retention checks in [content_quality.md](content_quality.md). Confirm that clearer wording preserves required facts, obligation strength, section identifiers, total budget, and every byte of protected content. Recheck length after the wording changes; brevity is not permission to remove a condition.

This is an editorial review, not evidence that real readers successfully used the guide. Use available reader feedback when supplied; otherwise report material unresolved clarity or evidence limits without inventing user testing or creating an additional approval gate.
