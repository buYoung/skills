## Working Agreements
- Respond in Korean (keep tech terms in English, never translate code blocks)
- Create tests/lint only when explicitly requested
- Build context by reviewing related usages and patterns before editing
- Prefer simple solutions; avoid unnecessary abstraction
- Ask for clarification when requirements are ambiguous
- Minimal changes; preserve public APIs
- New functions/modules: single-purpose, colocated with related code
- External dependencies: only when necessary, explain why
- If the operation fails due to file existence while using write_to_file, execute replace_file_content instead.

This guide follows a structure designed to provide the "How (Solution)" as quickly as possible when a user arrives with a "What (Intent)."

## 1. Core Structure: 1:1 Mapping of Intent and Solution

Define the fundamental unit of the documentation not as a 'feature description,' but as a 'User Goal.'

* Header (The Goal): Write based on actions/goals, not feature names.
* Bad: `setTimeout` function
* Good: Running code after a set time (`setTimeout`)


* Input (The Intent): Describe the user's situation or a natural language question.
* "When you want to proceed with the next task without waiting for a server response."
* "How do I remove duplicate items from a list?"


* Output (The Solution): Provide specific code/examples that are immediately copy-pasteable.
* A complete, working code block (including necessary imports).



## 2. Example Composition: Context over Syntax

Avoid simply listing API signatures (e.g., `func(a, b)`). Instead, present specific Scenarios as examples.

* Scenario-based Example:
* Input: "Limiting file size when uploading a user profile image."
* Output:
```javascript
// Return an error if the file exceeds 5MB
if (file.size > 5 * 1024 * 1024) {
  throw new Error('File size cannot exceed 5MB.');
}

```





## 3. Information Arrangement: Progressive Disclosure

Reveal information in stages based on the user's level of intent.

1. Quick Start (Most Common Intent): "How do I make it work right now?"  Provide a copy-pasteable basic example.
2. Customization (Detailed Intent): "How do I change the settings?"  Explain option objects or parameters.
3. Troubleshooting (When Issues Arise): "Why isn't it working?"  Common errors and solutions (FAQ format).

## 4. Visual Hierarchy

Do not mix code and explanations; keep them clearly separated.

* Explanation Area: Describe the situation (Input) using concise sentences.
* Code Area: Present the solution (Output) in a box-style code block.
* Comments: Handle line-by-line explanations using in-code comments rather than body text to minimize eye movement.

---

### Application Example

```markdown
## Changing Date Format

Input (Intent)
"When you want to display an ISO date string (`2024-01-15T...`) in the format of `January 15, 2024`."

Output (Solution)
```javascript
import { format } from 'date-fns';

const date = new Date('2024-01-15T09:00:00');
const result = format(date, 'MMMM d, yyyy');
console.log(result); // "January 15, 2024"

```