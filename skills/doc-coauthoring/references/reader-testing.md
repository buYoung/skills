# Stage 3: Reader Testing

Test the document with a fresh Claude instance that has no context from the authoring conversation. This catches blind spots — things that make sense to the authors but confuse others.

## Testing Approach Selection

| Environment | Approach |
|-------------|----------|
| Claude Code (sub-agents available) | Automated: spawn fresh sub-agents for testing |
| Claude.ai / Claude app (no sub-agents) | Manual: guide the user to test in a new conversation |

---

## Automated Approach (Sub-agents Available)

### Step 1: Predict Reader Questions

Generate 5-10 questions that readers would realistically ask when discovering this document. Focus on questions that test comprehension, not just retrieval.

### Step 2: Test with Sub-Agent

For each question, invoke a sub-agent with only the document content and the question — no context from the authoring conversation.

Summarize what Reader Claude got right and wrong for each question.

### Step 3: Additional Checks

Invoke a sub-agent to check for:
- Ambiguous statements that could be interpreted multiple ways
- Assumptions the document makes without stating
- Internal contradictions or inconsistencies

Summarize any issues found.

### Step 4: Report and Fix

If issues are found, report them with specifics. Fix the gaps by looping back to refinement for the affected sections.

---

## Manual Approach (No Sub-agents)

### Step 1: Predict Reader Questions

Ask what questions people might ask when discovering this document — what would they type into Claude.ai?

Generate 5-10 realistic reader questions.

### Step 2: Setup Testing

Provide these instructions to the user:

1. Open a fresh Claude conversation
2. Paste or share the document content (if using a shared doc platform with connectors enabled, provide the link)
3. Ask Reader Claude the generated questions

For each question, instruct Reader Claude to provide:
- The answer
- Whether anything was ambiguous or unclear
- What knowledge or context the document assumes readers already have

Check if Reader Claude gives correct answers or misinterprets anything.

### Step 3: Additional Checks

Also ask Reader Claude:
- "What in this doc might be ambiguous or unclear to readers?"
- "What knowledge or context does this doc assume readers already have?"
- "Are there any internal contradictions or inconsistencies?"

### Step 4: Iterate Based on Results

Ask the user what Reader Claude got wrong or struggled with. Fix those gaps by looping back to refinement for the affected sections.

---

## Exit Condition

Reader Claude consistently answers questions correctly and does not surface new gaps or ambiguities. The document is ready for human readers.

---

# Final Review

When Reader Testing passes:

1. Recommend a final read-through by the user — they own this document and are responsible for its quality
2. Suggest double-checking facts, links, and technical details
3. Ask them to verify the document achieves the impact they originally intended

If the user wants one more review, provide it. Otherwise, announce completion with these tips:

- **Conversation link:** Consider linking this conversation in an appendix so readers can see how the document was developed
- **Appendices:** Use appendices to provide depth without bloating the main document
- **Living document:** Update the document as feedback arrives from real readers
