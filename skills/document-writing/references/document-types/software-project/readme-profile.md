# README writing profile

A README is the project's entry document. Lead with its identity, concrete purpose and suitable users, then give a coherent path to first use. Use familiar Markdown sections and the shared prose style; this profile supplies composition decisions rather than another style checklist.

## Choose coverage and order

| Reader question | Content to select |
| --- | --- |
| What does it do, and is it for me? | Brief purpose, principal use case, a useful capability list and material applicability limits |
| What do I need? | Requirements that determine whether the shown path works, placed before dependent installation or actions |
| How do I obtain it? | The user-facing installation/access route and selection conditions for meaningful alternatives |
| How do I get a useful result? | One representative quick start constructed with the common example contract |
| Where is the detail or help? | Direct destinations for tasks, configuration, reference and support |
| What are the project terms and participation paths? | Existing license, contribution and status information when relevant |

These are responsibilities, not mandatory titles or sections. Combine small sections; retain a useful existing layout. Badges, screenshots, contents lists and comparison tables are optional aids when they carry supported information or improve navigation.

## Select the first-use path

Prefer the documented default route for the intended reader. If supported routes have different prerequisites, label the choice before its commands instead of mixing them into one sequence. A repository-wide README may direct readers to separate packages; a package README must make that package's installation and first use clear.

Choose a small real outcome that demonstrates the stated value, such as processing one input or invoking one useful host action. Installation or `--help` alone does not demonstrate a promised processing feature. A temporary output or minimal sample is useful when it makes the result observable without unrelated setup. Apply the project-specific emphasis and evidence rules in the [common authoring contract](software-project-authoring.md).

## Decide what stays local

Keep every prerequisite needed for the shown first result in the short path. Move exhaustive options, advanced workflows, long conceptual explanations and contributor procedures to their existing owner, with specific links. If no detailed document exists and only README is requested, include the necessary entry detail locally.

Avoid repeating a full command or configuration catalog under features, quick start and usage. Reuse one representative example and explain where additional supported tasks live. Write connected prose for purpose and fit, numbered steps for a genuine sequence, and code blocks for actual input or supported output.
