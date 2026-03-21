# Stage 1: Context Gathering

Close the gap between what the user knows and what Claude knows. The richer the shared context, the smarter the guidance in later stages.

## Initial Questions

Ask these meta-context questions first:

1. What type of document is this? (technical spec, decision doc, proposal, etc.)
2. Who is the primary audience?
3. What is the desired impact when someone reads this?
4. Is there a template or specific format to follow?
5. Any other constraints or context to know?

Inform the user they can answer in shorthand or dump information in whatever format works best.

### Template Handling

- If the user mentions a template or doc type, ask if they have a template document to share
- If a link to a shared document is provided, use the appropriate integration to fetch it
- If a file is provided, read it directly

### Existing Document Handling

If the user mentions editing an existing shared document:
1. Use the appropriate integration to read the current state
2. Check for images without alt-text
3. If images exist without alt-text, explain the accessibility gap: when others use Claude to understand the doc, Claude cannot see images without alt-text. Offer to generate descriptive alt-text if the user pastes each image into chat.

## Info Dumping

Encourage the user to dump all context they have. Useful categories to request:

- Background on the project or problem
- Related team discussions or shared documents
- Why alternative solutions are not being used
- Organizational context (team dynamics, past incidents, politics)
- Timeline pressures or constraints
- Technical architecture or dependencies
- Stakeholder concerns

Advise the user not to worry about organizing the information — raw context is fine. Offer multiple input methods:
- Stream-of-consciousness info dump
- Pointers to team channels or threads
- Links to shared documents

### Integration Awareness

**If integrations are available** (Slack, Teams, Google Drive, SharePoint, or other MCP servers): mention that these can pull context directly.

**If no integrations are detected** (Claude.ai or Claude app): suggest enabling connectors in Claude settings to allow pulling context from messaging apps and document storage.

## Clarifying Questions

Trigger clarifying questions when the user signals their initial dump is complete, or after substantial context has been provided.

Generate 5-10 numbered questions based on gaps in the context. Focus on:
- Ambiguities in the provided information
- Missing perspectives (stakeholders, users, opponents)
- Unstated assumptions
- Scope boundaries
- Success criteria

Inform the user they can answer in shorthand (e.g., "1: yes, 2: see #channel, 3: no because backwards compat"), link to more docs, point to channels, or continue dumping context.

### During Context Gathering

- **Team channels / shared documents mentioned:** If integrations are available, inform the user that the content will be read, then use the integration. If not available, explain the limitation and suggest enabling connectors or pasting content directly.
- **Unknown entities or projects mentioned:** Ask if connected tools should be searched to learn more. Wait for confirmation before searching.
- **Track progress:** Maintain awareness of what has been learned and what remains unclear.

## Exit Condition

Context gathering is sufficient when questions demonstrate understanding — when the conversation can address edge cases and trade-offs without needing basics explained.

## Transition

Ask if there is any more context to provide, or if it is time to move on to drafting the document. If the user wants to add more, let them. When ready, proceed to Stage 2.
