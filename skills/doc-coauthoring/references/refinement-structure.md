# Stage 2: Refinement & Structure

Build the document section by section through brainstorming, curation, and iterative refinement.

## Setting Up the Structure

### When the user knows the sections they need

Ask which section to start with. Suggest starting with whichever section has the most unknowns — the core proposal for decision docs, the technical approach for specs. Summary sections work best when written last because they synthesize content from other sections.

### When the user does not know what sections they need

Based on the document type and any provided template, suggest 3-5 appropriate sections. Ask if the structure works or needs adjustment.

### Creating the Scaffold

Once the structure is agreed upon:

**With artifact access:** Use `create_file` to create an artifact with all section headers and `[To be written]` placeholder text. Provide the scaffold link.

**Without artifact access:** Create a markdown file in the working directory (e.g., `decision-doc.md`, `technical-spec.md`). Confirm the filename.

## Per-Section Workflow

### Step 1: Clarify

Announce work on the section. Ask 5-10 clarifying questions about what the section needs, based on the gathered context and the section's purpose.

Inform the user they can answer in shorthand or indicate what is important to cover.

### Step 2: Brainstorm

Generate 5-20 candidate points for the section, scaling with complexity. Look for:
- Context the user shared earlier that might be relevant here
- Angles or considerations not yet mentioned

Present as a numbered list. Offer to brainstorm more if the user wants additional options.

### Step 3: Curate

Ask the user to indicate what to keep, remove, or combine. Request brief justifications — these reveal priorities that inform future sections.

**Example response formats:**
- "Keep 1,4,7,9"
- "Remove 3 (duplicates 1)"
- "Remove 6 (audience already knows this)"
- "Combine 11 and 12"

If the user gives freeform feedback instead of numbered selections (e.g., "looks good" or "I like most of it but..."), extract their preferences and proceed.

### Step 4: Gap Check

Based on the user's selections, ask if anything important is missing for the section.

### Step 5: Draft

Use `str_replace` to replace the placeholder text with the drafted content.

**With artifact access:** Provide a link to the artifact after drafting.

**Without artifact access:** Confirm the section has been drafted in the file.

Ask the user to read through and indicate what to change.

**First section only — include this note:**
> Instead of editing the doc directly, indicate what to change here in chat. This helps me learn your style for future sections. For example: "Remove the X bullet — already covered by Y" or "Make the third paragraph more concise."

Directing feedback through conversation rather than direct edits helps calibrate tone and priorities for subsequent sections.

### Step 6: Iterate

As the user provides feedback:
- Apply edits with `str_replace` (reprinting the whole document wastes tokens and obscures what changed)
- With artifact access: provide the link after each edit
- Without artifact access: confirm edits are complete
- If the user edits the document directly and asks to read it: note the changes they made and apply those preferences to future sections

Continue iterating until the user is satisfied with the section.

### Quality Check

After 3 consecutive iterations with no substantial changes, ask if anything can be removed without losing important information. Concision improves readability.

When the section is done, confirm completion and ask if ready to proceed to the next section.

## Repeat for All Sections

Apply the same per-section workflow to each remaining section.

## Near-Completion Review

When 80% or more of sections are complete, re-read the entire document and check for:
- Flow and consistency across sections
- Redundancy or contradictions between sections
- Generic filler content ("slop") that doesn't carry weight
- Whether every sentence adds value

Provide feedback based on this review.

## Final Assembly

When all sections are drafted and refined, review the complete document one more time for overall coherence, flow, and completeness. Provide any final suggestions.

Ask if ready to move to Reader Testing, or if further refinement is needed.
