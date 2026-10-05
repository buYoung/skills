# Authoring software project documentation

## Establish the real project and reader

Identify the requested package or project unit, reader role, document operation, paths, and applicable release or working-tree state. In a monorepo, distinguish repository-wide navigation, the installable package, and the consumer's working directory. Repository visitors, installed-product users, integrators, and contributors may need different entry paths. Use the requested audience; do not make a plugin user's first task build the plugin from source unless that is the actual distribution path.

Treat these as independent facts, not mutually exclusive project categories:

- Product form: plugin, library, CLI, application, or a combination.
- Execution or installation context: host application, language runtime, operating system, service, and required permissions.
- Distribution: registry, marketplace, binary release, source checkout, hosted access, or supported alternatives.
- Project operation: open-source contribution, private development, support channels, and maintenance status, where established.

An open-source plugin can need both host-specific installation and contribution links. A library can also expose a CLI. Include only the dimensions that change this reader's decisions or actions.

## Ground instructions in available evidence

Read the existing targets and relevant source material before drafting. Inspect the smallest useful set of manifests, command or API implementations, configuration schemas, packaging and release settings, licenses, and existing documentation. Verify external host or distribution rules from the provider's official documentation when they affect the instructions.

For material claims, keep a working association between the documented fact and its source or verification limit; this is not a required extra artifact. Check, as applicable:

| Claim | Evidence to inspect |
| --- | --- |
| Install identifier, artifact, channel, or hosted entry | Package or plugin manifest, publication/release configuration, supplied release, actual distribution page |
| Runtime or host compatibility | Declared requirements and supported compatibility evidence; a build target alone does not prove a tested minimum |
| Commands, imports, options, defaults, and configuration | Implemented entry points, parser/schema, exported API, current authoritative docs |
| Expected output and state changes | Implementation, supplied examples or fixtures, or an actual permitted run |
| License, help, contribution, and project links | Existing license and project-owned files or authoritative destinations |

Keep consumer installation separate from developer setup, and released behavior separate from unreleased source. When sources disagree, establish which state the requested document describes and retain material differences. Do not silently select a version, support policy, license, URL, default, menu label, or output to complete a familiar template. A public repository alone does not establish its license or contribution process.

A package's registry identifier, CLI executable, and library import can differ; verify each identifier used in an example. A local manifest alone does not establish that the package is published. For configuration claims, inspect the relevant definitions and consumers rather than assuming precedence, persistence, or reload behavior.

Use source-confirmed instructions without claiming they were executed. Run examples only when the available environment and permission scope support it; authoring does not itself authorize external installation, account changes, or destructive operations. If a material prerequisite or command remains unknown, ask when it blocks a usable path; otherwise state the local limit or omit the unsupported optional claim. Do not report a blocked first-use or requested task path as working. Explain legitimate reader-supplied placeholders, and distinguish them from missing author evidence.

## Draft for the selected profile

Use conventional Markdown headings, short paragraphs, lists, and language-tagged code fences. Explain required substitutions before examples. State execution location, environment, and inputs when they affect behavior. Separate copyable input from output and unexplained shell prompts. Show a supported observable result; distinguish exact output from an illustrative description. Keep relevant side effects and limits beside the affected task.

Apply the profile as a menu of reader needs, not a template to fill. Use tables only for genuinely comparable options or variants. Badges, screenshots, logos, a manual contents list, FAQs, and ornamental callouts are optional and need a reader benefit and real targets. Do not add empty sections or manufacture material to supply them.

When both documents exist, check the same package identity, prerequisites, install channel, command/API, defaults, example inputs, and success criterion across the README's short path and usage detail. Keep necessary qualifications locally visible and link to the deeper owner. If only one file is writable, fix that file within scope and report a remaining inconsistency in the other instead of silently editing it.

For focused updates, inspect affected examples and links; preserve unrelated content, exact text, and established section anchors where possible. For normalization, report material moves without changing supported behavior. Review the draft against [software-project-review.md](software-project-review.md) before delivery.
