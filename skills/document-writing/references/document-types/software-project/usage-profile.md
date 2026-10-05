# Usage writing profile

## Reader journey

A usage document serves readers who need to do a particular job with the project. They may enter directly at a task heading rather than read from the top. Make task selection, relevant setup, detailed actions, configuration, results, and limitations easy to find without requiring the author's context.

State the covered package or product, reader, and supported environment when needed. Link the established installation entry if it exists; retain local prerequisites that materially control a task. Do not assume every reader has completed the README's example.

## Organize around real work

Choose headings from supported reader goals, such as exporting a report or embedding a parser, rather than making every implementation class or flag a task. Order tasks by reader needs and dependencies. A task index or contents list helps only when the document's size warrants it.

For each substantial task, provide the applicable parts of this contract:

1. Goal and applicability: what the reader achieves and which environment or mode supports it.
2. Starting conditions: prerequisites, inputs, permissions, and execution location.
3. Actions: exact supported commands, API calls, configuration changes, or UI labels in dependency order.
4. Result: output or observable state, including where a created artifact appears and what success means.
5. Conditions and limits: relevant defaults, side effects, unsupported cases, and documented recovery or next step.

Combine trivial parts naturally rather than forcing five labels onto every task. Keep a materially different environment's instructions distinct; do not place mutually exclusive steps in one copyable command block.

Use complete, supported examples when they resolve a common task. Identify input fixtures or substitutions, explain the result, and label illustrative output. Avoid toy snippets that omit essential initialization or silently rely on a previous task's state.

## Separate lookup from procedure

Place detailed configuration or option lookup in a clearly labeled section or link its existing owner. For covered options, include supported syntax, types, defaults, allowed values, precedence, and relevant interactions when those affect use. Do not invent any field to complete a table, or duplicate an exhaustive generated API reference unnecessarily.

Keep short explanations beside the task when they support an immediate choice. Link deeper conceptual material when available; the distinction does not require separate files or a full documentation site.

Include common local failures and documented remedies where they help a task. If branching diagnosis and incident recovery become the document's primary purpose, route that requested artifact to a troubleshooting runbook. Do not expand ordinary usage authoring into an unrequested runbook.

## Completion question

Can a reader find their covered task, identify its starting conditions, execute the documented actions, and interpret its result and relevant limits? If a README exists, its quick-start example must remain a valid short instance of the same behavior. Reading a companion document to check this does not authorize changing it.
