# Software project documentation

## Purpose and boundary

Help the intended reader decide whether a software project fits, reach a working first use, and find the detail needed for later tasks. This type covers a project or package's user-facing entry and usage surface, including plugins, libraries, command-line tools, and applications.

Select by the artifact's role and actual package, not its filename alone. A `usage.md` that only lists API fields may be a reference or specification; a `README.md` that indexes a design system belongs to that document set. A guide about writing READMEs remains an action guide. Do not replace FDD, design-system, policy, or runbook contracts because their files use these names.

## Select a writing profile

| Profile | Reader outcome | Load |
| --- | --- | --- |
| README | Understand what this project is, judge applicability, install or access it, and succeed with one representative first use | [readme-profile.md](readme-profile.md) |
| Usage | Locate and complete a specific task, configure behavior, interpret results, and understand relevant limits | [usage-profile.md](usage-profile.md) |

Choose one profile per requested deliverable. A README can contain a short usage example without becoming two documents; a usage guide can include the local explanation and reference needed to complete its tasks. Distinguish those sections by purpose instead of blending a long conceptual discussion into steps.

If a requested single file genuinely serves both entry and detailed-use roles, retain one software project document contract and load both profiles for the relevant sections. Do not split it into unrequested files.

Use the requested or established path and casing. `usage.md` is a writing profile, not a mandatory filename or destination. Do not create a companion file, contribution guide, license file, generated API reference, or documentation site unless requested. Existing related documents may be read to check links and consistency without gaining write permission.

Resolve a destination in this order: the user's path, the existing target's location, then the actual project or package root with `README.md` or `usage.md` for the selected profile. Use an established documentation directory when the supplied context identifies it as the destination. A repository-wide introduction and a package README in a monorepo may have different owners and installation scopes.

## Load next

- For create, rewrite, update, or normalize: read the selected profile and [software-project-authoring.md](software-project-authoring.md).
- For review or fact-check: read the selected profile and [software-project-review.md](software-project-review.md). Inspect and report; do not apply fixes or create files.
- Read the shared [source-grounding.md](../../shared/source-grounding.md) for project facts. Before completing authoring, read [software-project-review.md](software-project-review.md) and use its relevant checks within the authorized scope. Shared plain-language and existing-edit references retain their roles; this type adds project-specific criteria rather than replacing them.

## Basis and interpretation

[GitHub's README guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes) describes README as a common first encounter with a project, covering purpose, usefulness, getting started, help, and maintainers. It recommends keeping longer documentation elsewhere and using relative links for repository files.

[Diátaxis](https://diataxis.fr/start-here/) distinguishes learning, task completion, exact lookup, and explanation. This skill applies that distinction within software documentation: a README offers a bounded entry journey; usage sections separate task directions from option lookup and background. Neither source requires this skill's two profiles, a universal section list, or a file named `usage.md`.
