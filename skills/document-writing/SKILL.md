---
name: document-writing
description: Create, update, rewrite, review, fact-check, or normalize durable human-readable documents. Use for explanatory overviews, action guides, references or specifications, proposals, analysis reports, policies, troubleshooting runbooks, records or meeting notes, Feature Design Docs (FDDs), and Design System Documents for product UI or any digital storefront's visual assets, including the document portion of mixed document-and-production requests. Route by the requested artifact and load only its references. Do not use for implementation plans, task briefs, tickets, system or architecture design docs, source changes, pure UI or asset production, or short chat-only answers.
---

# Document Writing

Create documents that help a specific reader understand, act, decide, comply, recover, or reconstruct what happened. The skill routes first and writes second: a polished document built from the wrong document contract is still wrong.

## Scope

This skill supports ten target document types:

1. Explanatory overview
2. Action guide
3. Reference or specification
4. Proposal
5. Analysis report
6. Policy or rules
7. Troubleshooting runbook
8. Record or meeting notes
9. Feature Design Doc (FDD)
10. Design System Document

The document type describes the artifact being created or assessed. Words appearing only as the subject do not select a type. For example, "write a guide to authoring FDDs" targets a guide, while "write an FDD for saved filters" targets an FDD.

## Workflow

### 1. Identify the requested operation

Determine whether the user wants to create, update, rewrite, review, fact-check, or normalize a document. When an existing document is involved, inspect it before deciding how to proceed.

Review is an operation, not a proposal type. A request such as "review this policy" routes to the policy type with the review operation.

Review and fact-check are non-mutating unless the user separately requests an update. They may inspect and research, but must not create, rename, or edit document files. Create, update, rewrite, and normalize are mutating operations within the requested document scope.

### 2. Identify the target artifact

Use evidence in this order:

1. The artifact the user explicitly asks to create or change
2. Existing document metadata, path, title, and headings
3. The reader's primary outcome
4. The content shape implied by the request

If an explicit label conflicts with the requested outcome and the choice materially changes the structure, ask one concise clarification question. Put that question directly in the user-facing response and phrase it so the user can answer the single unresolved choice; a decision note inside an artifact is not a substitute for the question.

### 3. Select exactly one document type

| Type | Select when the primary reader outcome is | Do not select when | Start with |
| --- | --- | --- | --- |
| Explanatory overview | Understand a concept, context, or meaning from a readable narrative | The reader needs exact lookup, ordered action, or a design decision source | [explanation-overview.md](references/document-types/explanation/explanation-overview.md) |
| Action guide | Complete a known task from a normal starting state | The starting state is an incident or unknown failure | [guide-overview.md](references/document-types/guide/guide-overview.md) |
| Reference or specification | Look up exact definitions, fields, states, options, or contracts non-linearly | The reader needs a conceptual introduction or whole-feature design | [reference-specification-overview.md](references/document-types/reference-specification/reference-specification-overview.md) |
| Proposal | Choose, approve, fund, or commit to a future action | The document only reports findings or defines an approved feature's design | [proposal-overview.md](references/document-types/proposal/proposal-overview.md) |
| Analysis report | Understand evidence, findings, implications, and limitations | The primary value is chronology or an explicit approval request | [analysis-report-overview.md](references/document-types/analysis-report/analysis-report-overview.md) |
| Policy or rules | Follow durable obligations, permissions, prohibitions, and exceptions | The document is a one-time procedure or a single feature's full design source | [policy-rules-overview.md](references/document-types/policy-rules/policy-rules-overview.md) |
| Troubleshooting runbook | Diagnose and recover from an abnormal state | The reader is following a normal installation or usage path | [troubleshooting-runbook-overview.md](references/document-types/troubleshooting-runbook/troubleshooting-runbook-overview.md) |
| Record or meeting notes | Reconstruct past events, statements, agreements, and chronology | The document interprets evidence as a report or defines current product design | [record-minutes-overview.md](references/document-types/record-minutes/record-minutes-overview.md) |
| Feature Design Doc | Use one product feature's behavior, flows, policies, scope, and alternatives as a design decision source for implementation | The artifact is a feature introduction, guide, interface specification, performance report, or build-approval proposal | [feature-design-doc-overview.md](references/document-types/feature-design-doc/feature-design-doc-overview.md) |
| Design System Document | Use a durable source for product UI foundations, tokens, components, and patterns, or for any digital storefront's visual asset rules | The user wants UI code, a mockup, generated images or assets, or a system or architecture design | [design-system-overview.md](references/document-types/design-system/design-system-overview.md) |

### 4. Apply the Design System Document gate and select prebuilts per output set

Select Design System Document only when a requested artifact governs reusable visual or interaction decisions across product UI or any digital storefront's listing assets. A request whose only deliverable is UI, a mockup, images, video, or other produced assets is a production task, not this document type.

For each output set, choose exactly one prebuilt from semantic intent:

| Prebuilt ID | Select when the document governs | Default output root |
| --- | --- | --- |
| `default` | Product UI foundations, tokens, components, content, accessibility, and patterns | `docs/design-system` |
| `app-store-page` | A digital storefront listing's visual assets, using whatever asset vocabulary and media types its operator defines | `docs/design-system-visual-assets` |

The requested output path never changes a prebuilt. Resolve each root in this order: a user-specified directory for that set, the location of the existing document set being changed or reviewed, then the selected prebuilt's default output root. Read only the prebuilt reference for that output set.

If the user explicitly requests both product UI and storefront visual asset systems, split the request into two coordinated Design System Document output sets and apply `default` and `app-store-page` independently. Use their separate default roots unless the user supplies one directory for each; ask once before writing if one custom root does not establish the two destinations.

For `app-store-page`, first resolve the storefronts actually included in the requested deliverable. Excluded storefronts and names used only for comparison, examples, or background are not targets. For create, update, rewrite, or normalize, follow the storefront research workflow for each in-scope target, including its explicit web-unavailable fallback, and create or update one storefront document. When both web research and the storefront identity or official material are unavailable, create no partial document: state the capability limit, request the operator identity or official guide, and leave mutable requirements unverified. For review or fact-check, research as available and report findings without changing files.

When a request combines a document with actual UI, image, or video production, keep the document portion under this skill and route the production portion to the appropriate capability as a separate deliverable. Do not let either portion suppress or silently replace the other.

### 5. Apply the FDD gate

Select FDD only when all of these are true:

- The subject is one product feature.
- The artifact defines what the feature is and why, including material behavior, flow, policy, scope, or alternative decisions.
- Implementers or code agents should treat the artifact as the current design decision source.

The word "feature" or "FDD" appearing as background is not enough. If the artifact teaches how to write an FDD, route to a guide. If it lists an API contract for a feature, route to reference or specification.

### 6. Resolve generic boundary cases

When no explicit target type settles the choice, use the reader's final action:

- Learn or understand: explanatory overview
- Complete a normal task: action guide
- Retrieve an exact fact or contract: reference or specification
- Approve or choose: proposal
- Interpret evidence: analysis report
- Comply with durable rules: policy or rules
- Recover from failure: troubleshooting runbook
- Reconstruct the past: record or meeting notes
- Govern reusable product UI or digital storefront visual asset decisions: Design System Document

Recommendations do not automatically make a report a proposal. Steps do not automatically make a policy a guide. Choose the type that controls why the document exists.

### 7. Load references progressively

After routing:

1. Read only the selected type's overview reference.
2. Follow that overview's operation-specific links.
3. Do not load the whole type directory.
4. Do not load another type's references merely for inspiration.
5. If clear evidence shows the route is wrong, discard the previous type contract, return here, and route again.

For all substantial creation, rewrite, or review work, read [human-readable-writing.md](references/shared/human-readable-writing.md). Read [source-grounding.md](references/shared/source-grounding.md) only when factual claims require sources or verification. Read [existing-document-edits.md](references/shared/existing-document-edits.md) only when modifying or reviewing an existing document.

### 8. Gather context before drafting

Establish the audience, intended outcome, authoritative inputs, constraints, and output destination. Infer what is safely recoverable from supplied material or the repository. Ask only when an unresolved choice would materially change the document's scope, behavior, or tradeoffs.

Do not invent missing decisions or facts. Mark unresolved content explicitly when no live user can answer.

### 9. Draft and verify

Follow the selected references. Use their structure as a reader-centered default, not as filler. Generic document types may omit sections that do not help the reader. FDD follows its stricter profile and validator contract.

Before delivery, confirm:

- The opening states the purpose, conclusion, outcome, or request appropriate to the type.
- Headings expose the document's logic when scanned.
- Each paragraph has one main idea.
- Facts, interpretation, decisions, and recommendations are distinguishable.
- Examples and expected results are concrete where useful.
- No empty, duplicated, or ceremonial sections remain.
- The result still matches the selected document type.
- For a multi-file Design System Document, every substantive supplied decision is in the owning prebuilt file, every required owner is linked from `index.md`, and the actual changed paths match the files the completion will claim.
- No supplied or verified value has been replaced by convention, and no unsupported value, policy, platform behavior, or storefront requirement has been added.
- Any unresolved choice that requires the user is asked once as a direct question in the user-facing response, not left only as an internal decision note.

## File output and collision rules

- Resolve a type-specific output destination in this order: a user-specified path, the existing target's location, then the selected type or prebuilt's default location.
- A Design System Document prebuilt writes a multi-file set, so its root must be a directory. For a new set, ask once if the user provides a `.md` path instead of a directory. For an existing file inside a set, resolve and preserve its established set root.
- Inspect an existing target before writing.
- Update the established artifact only when the request is an update or the selected reference defines in-place lifecycle behavior.
- Do not silently overwrite a different document.
- Do not invent -v2, -final, or date-suffixed duplicates to avoid deciding what the canonical file is.
- Preserve existing platform, storefront, and custom files outside the requested change scope; "not requested" does not mean "delete" or "invalidate".
- If the user asks only for a draft in conversation, return complete Markdown without creating an unsolicited file.
- Follow type-specific location rules when the selected reference defines them; FDD is one such type.

## Preservation and safety

When editing, preserve fenced code blocks, paths, identifiers, exact logs, quotations, and user-owned custom sections unless the user explicitly asks to change them. Preserve caller options and established document contracts. Warn before any instruction that can destroy data or materially disrupt a system.

## Completion

Before reporting completion, compare the resolved output contract and promised paths with the actual final artifact tree. Fix missing owners, links, or files first; if they cannot be produced, report the work as incomplete instead of claiming completion. Report the selected document type, the artifact produced or reviewed, validation performed, and any limitation that remains unverified. Never claim an unrun check passed.
