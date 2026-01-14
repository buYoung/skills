# Step 1: Input Analysis & Clarification Loop

Parse user input and validate required information. Loop until sufficient.

## Required Information Checklist

| Item | Check | Question if Missing |
|------|-------|---------------------|
| Purpose | What problem does this skill solve? | "What task should this skill automate or support?" |
| Domain | Target technology/framework specified? | "What language/framework/tool is this for?" |
| Trigger | When should the skill activate? | "In what situations should this skill be invoked?" |
| Input/Output | Clear inputs and expected outputs? | "What input does it receive and what output does it produce?" |
| Resources | Need scripts/references/assets? | "Are there scripts to execute or reference docs needed?" |

## Loop Logic

1. Parse input → extract purpose, domain, trigger, I/O, resources
2. Check each required item
3. If any missing → generate clarification questions → wait for response → repeat
4. If all sufficient → proceed to Step 2
