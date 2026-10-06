# Software project documentation

Use this type for a software project's entry document or normal usage manual. A standalone API contract, isolated task guide, incident runbook, or design-system index keeps its own document type even when named `README.md` or `usage.md`.

## Select the profile and destination

| Profile | Primary reader outcome | Composition owner |
| --- | --- | --- |
| README | Judge project fit, obtain the software, and reach a first useful result | [readme-profile.md](readme-profile.md) |
| Usage | Find a task, perform it from its starting conditions, and interpret the result | [usage-profile.md](usage-profile.md) |

Select a primary profile by purpose, not filename. A short example in a README does not make it a second deliverable. For a requested single-file manual that genuinely combines both roles, load both profiles for their respective sections and keep one document contract.

The main skill owns operation permissions and collision rules. Produce only requested deliverables; inspecting an existing companion does not add it to the writable scope. Resolve paths from the user's destination, then the existing target, then `README.md` or `usage.md` at the actual project or package root. Use an established documentation directory when the inputs identify it as the destination; preserve existing casing.

## Load the relevant instructions

- Create, rewrite, update, or normalize: read [software-project-authoring.md](software-project-authoring.md), then the selected profile. Follow the main skill's shared writing, grounding, and existing-edit references.
- Review or fact-check: read the selected profile and [software-project-review.md](software-project-review.md). The review reference points to the common evidence and consistency contracts; report findings within the requested operation.
- Before completing authoring, apply the review reference to the affected reader path. A focused change does not require rebuilding unrelated sections.
