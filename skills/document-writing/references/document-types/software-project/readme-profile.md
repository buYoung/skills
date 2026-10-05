# README writing profile

## Reader journey

A README is the project's entry document. Its opening should let the intended reader identify the project, understand its main benefit, and recognize whether it fits their situation. The practical path then leads from applicable requirements through installation or access to one successful first use.

Prefer a familiar Markdown structure and direct description over promotional claims or a product-specific decorative layout. Adapt the content to the real package and audience while keeping common entry questions easy to find.

## Compose only applicable sections

The usual order is orientation, requirements, installation or access, quick start, then deeper documentation and project links. Existing effective sections and user-supplied structure may already serve this journey.

- **Purpose and fit:** project name, what it does, intended users or use case, and a material limit when necessary to judge applicability. A compact capability list can help; unsupported comparisons and slogans cannot establish fit.
- **Requirements:** supported runtime or host, versions, permissions, or other prerequisites needed for the chosen path. Put consequential compatibility limits before installation.
- **Installation or access:** a verified consumer path. Name the actual package, marketplace entry, binary, or service; distinguish supported alternatives by the condition that selects each. Keep development builds secondary unless they are the consumer path.
- **Quick start:** the smallest representative use that produces a useful result after installation. Include the actual invocation or UI action, minimal required input, and supported evidence of success. A help screen alone is usually not the product outcome.
- **Further use and help:** specific links to existing usage, configuration, API, examples, or troubleshooting owners. Keep enough local context that the first-use path is complete; do not offload a required step behind an unexplained link.
- **Project participation and terms:** link existing support, maintainer, contribution, security, or license material when relevant and verified. Open-source participation can coexist with any product form; it is not a reason to replace end-user onboarding with a contributor setup guide.

Use these as composition choices. Do not require every heading, a fixed number of features, badges, screenshots, or a template placeholder for an inapplicable topic. A hosted tool may need an access link rather than an installation command. A small package may combine requirements and installation in a few paragraphs.

## Adapt the first-use path

Combine the relevant project traits without changing the common Markdown style:

- For a plugin, show its supported host, installation and activation context, and the first useful invocation inside that host.
- For a library, show the consumer package identity, public import, necessary initialization, minimal call, and supported return or side effect.
- For a CLI, show the actual executable, required input and working directory, and the first goal-oriented invocation and result.
- For an application or hosted service, show the actual access, setup, and first meaningful user action.
- Open-source operation can add verified license and contribution links alongside any of these paths. It does not replace the end-user path with contributor setup.

## Depth and handoff

Keep one clear representative path near the start. Explain materially different supported paths where the reader must choose; avoid copying an entire command catalog, configuration reference, development handbook, or conceptual essay into the README. Link existing detailed documents with descriptive text and repository-relative paths when appropriate.

If a detail document does not exist and was not requested, do not invent a link or create it. Include essential first-use detail locally and report any out-of-scope documentation gap separately. Preserve accurate links and stable anchors when editing an existing README.

## Completion question

Can a reader with the stated prerequisites judge fit, follow the documented distribution path, and recognize a meaningful first result without guessing a missing name, step, or condition? Assess this from the actual text and evidence; a successful prose walkthrough is not proof that the software was executed.
