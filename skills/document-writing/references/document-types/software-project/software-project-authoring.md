# Authoring software project documentation

This reference owns project context, evidence, example construction, and README/usage consistency. The profiles own content selection and depth; the shared writing reference owns prose style.

## Establish the package context

Identify the project or installable package, target release or checkout, reader role and starting knowledge, available software or access, and execution location. In a monorepo, repository navigation, an individual package, and the consumer's working directory can differ. Choose the installation/access route supported for that reader; source builds are appropriate when required or when contributors are the audience.

Base prerequisites and inputs on what that reader receives through the selected route. A supplied artifact may be usable from its actual file location without a checkout; an installed package may omit repository samples. Distinguish checkout files, installed resources and reader-created input rather than assuming the writer's workspace is available to the reader.

Product form, host/runtime, distribution channel, and open-source operation are independent traits. Combine the applicable rows below; a CLI library or open-source plugin does not need another template.

| Established trait | README emphasis | Usage emphasis |
| --- | --- | --- |
| Plugin | Supported host, install/enable location, first invocation | Host state, exact actions, configuration location and activation/reload behavior |
| Library | Install identifier, public import, minimal integration | Initialization, input and return handling, useful integration scenarios |
| CLI | Obtain the executable, first goal-oriented command | Working directory, input/output, flags, exit and repeat-run behavior |
| Application or service | Actual access and first user action | User workflows, relevant setup, stored or exchanged data |
| Open-source operation | Existing license, support and contribution owners | Developer or extension workflows only when those readers are in scope |

Use only established behavior. A hosted application may require access rather than installation. A public repository does not establish a license or maintenance commitment.

## Ground evidence and examples

Use the shared [source-grounding.md](../../shared/source-grounding.md) hierarchy and inspect the relevant sources for the documented version:

| Fact | Useful source |
| --- | --- |
| Installable identity and distribution | Manifest, release/publication settings, supplied artifact or distribution evidence |
| Host/runtime compatibility | Declared constraints and support evidence; distinguish declarations from tested combinations |
| Executable/import/action names and accepted input | Public exports, command parser, registered actions and maintained examples |
| Configuration behavior | Definitions and consumers: default, precedence, scope and application timing |
| Result, limitation or side effect | Implementation, supplied observation, fixture or permitted execution |
| License and project destinations | Actual license and existing documentation or authoritative project destinations |

Registry name, executable name, and import name can differ. A local manifest does not prove publication; a source-checkout feature does not prove release availability. Resolve conflicting evidence for the target state rather than copying obsolete prose for consistency. Recover missing material facts or disclose the affected path as unresolved; omit unsupported optional claims.

Construct an example as one coherent path: starting environment and required setup, explained input, supported invocation, then observable result and relevant limits. Keep copyable input separate from output. Explain reader-supplied placeholders before use; they are different from missing author evidence. Include stable output only when supported, and identify variable fields or illustrative descriptions. Source inspection and an executed example are different evidence levels; run an example only within the task's environment and authorization.

Match invocation detail to the reader's established knowledge. Provide a short supported opening action when an unfamiliar host interface or execution context would otherwise prevent the intended reader from reaching the project action. Familiar developer conventions may remain implicit.

## Keep shared facts in one owner

When both README and usage exist, trace the short first-use path into its detailed task. Compare the same package/version, installation route, setup, invocation, defaults, result and limitations. Correct the requested artifact from controlling evidence; report a conflicting companion outside writable scope.

Keep detailed rules and option definitions at their established owner. Retain the conditions needed to interpret a summary locally, then link directly to the relevant task or setting. Link only to existing or requested-and-produced destinations; check relative paths, casing and affected anchors from the containing file.

When a link delegates a necessary part of first use or a task, inspect the destination's content for the same reader's starting conditions, action and observable result. A resolving link alone does not establish a complete path. Supply a missing connection in the requested artifact when evidence permits, or report the affected path as unresolved; inspection does not expand the linked document's writable scope.
