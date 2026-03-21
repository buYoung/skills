---
name: doc-coauthoring
description: Guide users through a structured 3-stage workflow for co-authoring documentation — Context Gathering, Refinement & Structure, and Reader Testing. Use this skill whenever the user wants to write documentation, proposals, technical specs, decision docs, RFCs, PRDs, design docs, or any structured content. Trigger when the user mentions writing docs, drafting a proposal, creating a spec, writing up decisions, or similar documentation tasks, even if they just say "write a doc" or "let's draft something."
---

# Doc Co-Authoring Workflow

A structured workflow for collaborative document creation through three stages: Context Gathering, Refinement & Structure, and Reader Testing.

## Workflow Overview

Documents created without structured collaboration often fail their readers — the author's implicit knowledge creates blind spots that only surface after publication. This workflow closes the gap by systematically gathering context, building content section-by-section, and testing the result with a fresh perspective before sharing.

### Stage Summary

| Stage | Goal | Exit Condition |
|-------|------|----------------|
| **1. Context Gathering** | Close the knowledge gap between user and Claude | Edge cases and trade-offs can be discussed without needing basics explained |
| **2. Refinement & Structure** | Build the document section by section through brainstorming and curation | All sections drafted, refined, and reviewed for coherence |
| **3. Reader Testing** | Verify the document works for readers who lack the author's context | Fresh Claude instance answers reader questions correctly and surfaces no new gaps |

## Trigger Conditions

Offer this workflow when the user:
- Mentions writing documentation: "write a doc", "draft a proposal", "create a spec", "write up"
- References specific doc types: PRD, design doc, decision doc, RFC, technical spec
- Appears to be starting a substantial writing task

### Initial Offer

Present the three stages and explain the value: this approach catches blind spots before others read the document. Ask whether the user prefers this structured workflow or freeform collaboration.

If the user declines, work freeform. If the user accepts, proceed to Stage 1.

## Stage 1: Context Gathering

Gather all relevant context before writing begins. The goal is to reach a level of understanding where questions can target edge cases and trade-offs rather than basics.

See [context-gathering.md](references/context-gathering.md) for the detailed interview process, including initial questions, info dumping guidance, integration usage, and clarifying question patterns.

**Key activities:**
1. Ask meta-context questions (doc type, audience, desired impact, template, constraints)
2. Encourage the user to dump all context in whatever format works for them
3. Pull in context from connected tools (Slack, Drive, etc.) when available
4. Ask 5-10 clarifying questions based on gaps
5. Repeat until understanding reaches the edge-case level

**Transition:** Ask if there is more context to provide, or if it is time to start drafting.

## Stage 2: Refinement & Structure

Build the document section by section through a brainstorm-curate-draft-refine cycle.

See [refinement-structure.md](references/refinement-structure.md) for the detailed per-section workflow, output format handling, and quality checks.

**Per-section cycle:**
1. **Clarify** — Ask 5-10 questions about what the section needs
2. **Brainstorm** — Generate 5-20 candidate points, surfacing forgotten context and new angles
3. **Curate** — User selects what to keep, remove, or combine
4. **Gap Check** — Confirm nothing important is missing
5. **Draft** — Write the section using `str_replace` on the scaffold
6. **Refine** — Iterate on edits until the user is satisfied

**Section ordering:** Start with the section that has the most unknowns (core proposal for decision docs, technical approach for specs). Leave summary sections for last.

**Near completion:** After 80% of sections are done, re-read the entire document and check for flow, consistency, redundancy, contradictions, and filler content.

## Stage 3: Reader Testing

Test the document with a fresh Claude instance (no context from the authoring conversation) to catch blind spots.

See [reader-testing.md](references/reader-testing.md) for testing procedures for both sub-agent and manual approaches, plus the final review checklist.

**Key activities:**
1. Predict 5-10 questions readers would realistically ask
2. Test each question with a fresh Claude instance
3. Run additional checks for ambiguity, false assumptions, and contradictions
4. Fix any gaps found, then retest

**Exit condition:** Reader Claude consistently answers correctly and surfaces no new gaps.

## Guidance Principles

### Tone
- Be direct and procedural
- Explain rationale briefly when it affects user behavior
- Execute the process rather than selling it

### Handling Deviations
- If the user wants to skip a stage, ask if they prefer freeform writing instead
- If the user seems frustrated, acknowledge the pace and suggest ways to accelerate
- The user retains agency to adjust the process at any point

### Context Management
- Address knowledge gaps as they arise rather than letting them accumulate
- Track what has been learned and what remains unclear throughout

### Output Management
- Use `create_file` / artifacts when available for the document scaffold
- Use `str_replace` for all edits — reprinting the entire document wastes tokens and makes changes harder to track
- Create a markdown file in the working directory when artifacts are unavailable
- Brainstorming lists belong in conversation, not in the document artifact

### Quality Focus
- Each iteration targets meaningful improvements
- The goal is a document that actually works for its readers, which requires patience through the stages
