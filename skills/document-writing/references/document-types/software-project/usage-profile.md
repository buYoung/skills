# Usage writing profile

Organize a usage document around jobs the reader performs. Readers may enter at a task heading without reading the README, so each task must expose its own starting context. Apply the [common authoring contract](software-project-authoring.md) for project facts and examples; this profile owns task selection, detail and lookup organization.

## Build the task map

Derive coverage from the user's request and supported public workflows. Put the normal task first, then meaningful variations that change input, configuration, integration or output. Group by reader goals rather than internal classes or individual flags. Preserve requested coverage; do not replace a broad manual with one easy example or add unrelated tasks to a focused update.

For each substantial task, connect:

1. The goal and when the task applies.
2. Starting state, required input, setup and execution location.
3. Actions in dependency order, using the actual command, API or host interface.
4. The result, its location or return handling, and the condition that distinguishes success.
5. Material variations, limits, side effects and documented local failure handling.

Combine trivial elements naturally instead of repeating five subheadings. Use one complete normal example, then show the meaningful change for a variant with enough local context to interpret it. Do not present mutually exclusive environment paths in one copyable block.

## Explain configuration as behavior

Keep lookup information separate from the task sequence. For settings in scope, explain the exact name, accepted value and unit, default, affected behavior, and supported interactions. Describe precedence or reload/persistence only when established; distinguish a sample value from a default or requirement. Comparable fields can use a compact table, while interactions usually need prose or an example.

Connect a setting to the task it changes. A list of keys is insufficient when the reader cannot tell where to set one or when it takes effect. If an exhaustive reference already owns the definitions, keep task-relevant interpretation here and link to it rather than maintaining a second catalog.

## Keep the task path readable

Link the existing installation owner while retaining additional task-local requirements. Place a common failure at the step it affects when that helps the reader choose a supported correction. If branching diagnosis becomes the primary artifact, apply the runbook boundary defined in the overview. Keep deeper explanation and developer procedures outside the normal task sequence unless they are required for this reader's goal.
