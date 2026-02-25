---
#### Task Information
- Work agent: junie (gemini 3.0 flash)
- Verification/Analysis agent: junie (opus 4.6)
- GitHub Repository: https://github.com/buYoung/intellij-jsoninja
- Tag Name: agents-test-base
- Note: Running the requirements from this tag will produce the same results.

#### Requirements
- Ensure template syntax (`{{.value}}`) is preserved and included in formatting results when formatting JSON.
- Example: `{ "test": {{.value}} }` should remain `{ "test": {{.value}} }` after formatting.

---

### 1. Detailed Review of `no-agents-test.patch`

#### Implementation Method
- **Regex**: `("([^"\\]|\\.)*")|(\{\{.*?\}\}|\$\{.*?\}|<%.*?%>)` — Handles string literals and three types of template syntax (`{{...}}`, `${...}`, `<%...%>`) in a single pass.
- **Placeholder**: `"__JSONINJA_TEMPLATE_${counter++}__"` (including quotes).
- **Substitution/Restoration**: `prepareJsonForFormatting()` / `restoreTemplates()`.
- **Variable Rename**: `var formatState = formatState` → `var currentFormatState = formatState` (removes parameter shadowing).

#### Pros
- **Supports various template syntaxes** like `${...}`, `<%...%>` (high extensibility).
- Matches string literal groups first in the regex to **naturally preserve templates inside strings**.
- Resolves parameter shadowing issue (`currentFormatState`).
- Well-documented with KDoc comments.

#### Cons
- **Directly modifies existing test file (`JsonFormatterServiceTest.kt`)** — includes massive unnecessary changes like whitespace cleanup (trailing spaces) + `assertEquals` format changes.
- Tests added to the existing file, so **template-related tests are not isolated**.
- Uses `DOT_MATCHES_ALL` option — matches even when there are newlines inside `{{...}}`, but it's unclear if this was intentional.
- `combinedTemplateRegex` declared as a class field, inconsistent with the constant pattern in `companion object`.

#### Test Coverage
- `testFormatJsonWithTemplate`: Basic value template, multiple templates, key template, templates inside strings, uglify mode.
- `testIsValidJsonWithTemplate`: Validity check.
- Coverage is good, but **no negative cases (broken templates)** are tested.

---

### 2. Detailed Review of `agents-v1-test.patch`

#### Implementation Method
- **Regex**: `\{\{.*?\}\}` (matches only `{{...}}`).
- **Two-step Substitution**:
    1. Replace all `{{...}}` with `__JNJ_TPL_N__`.
    2. Wrap only placeholders outside quotes with `"__JNJ_TPL_Q_N__"` (using lookahead/lookbehind).
- **Restoration**: Decides whether to remove quotes based on the presence of `_TPL_Q_`.

#### Pros
- **Explicit logic** separating template processing inside vs. outside strings into two stages.
- `sortedByDescending { it.length }` replaces longer placeholders first to prevent partial matching.
- Fast-exit: `if (!json.contains("{{"))` check.
- Isolated in a separate test file (`JsonTemplateFormatTest.kt`).

#### Cons
- **Unnecessarily complex two-step substitution** — inefficient in both performance and readability as it performs global replacement first, then creates `Regex` again for each to check.
- `(?<!["'])placeholder(?!["'])` lookbehind pattern **may not accurately distinguish templates deep inside strings** (e.g., issues could occur in positions not immediately preceded by `"` like `"url": "http://{{host}}/api"`).
- **No support for other template syntaxes** like `${...}`, `<%...%>`.
- `isValidJson()` changes the original behavior by reassigning the `trimedJson` variable after calling `replaceTemplates`.
- `var formatState = formatState` parameter shadowing remains in `formatJson`.

#### Test Coverage
- Go template, multiple templates, templates inside quotes, templates with spaces, mixed templates.
- Relatively diverse, but **no uglify mode testing** and no negative cases.

---

### 3. Detailed Review of `agents-v2-test.patch`

#### Implementation Method
- **Regex**: `("(?:\\.|[^\\"])*")|(\{\{.*?\}\})` — Matches string literals and `{{...}}` in a single pass.
- **Placeholder**: `"__JSONINJA_TEMPLATE_${counter++}__"` (including quotes).
- **Substitution/Restoration**: `replaceTemplates()` / `restoreTemplates()` — simple and intuitive.

#### Pros
- **Most concise and clean implementation** — core logic is about 30 lines.
- Matches string literals first in the regex to **accurately preserve templates inside strings in a single pass** (same principle as no-agents but more concise).
- **Isolated in a separate test file (`JsonFormatterTemplateTest.kt`)** — adheres to the Separation of Concerns principle.
- Minimal changes to existing code — includes only whitespace cleanup, no unnecessary changes.
- Preserves `var formatState = formatState` in `formatJson` to **maintain compatibility with existing API/behavior**.
- **Includes negative tests** (verifies broken template `{{.value}` in `testIsValidJsonWithTemplate`).
- Includes nested template tests (`{{.value { "foo": "bar" } }}`).

#### Cons
- No support for other template syntaxes like `${...}`, `<%...%>` (but meets YAGNI principle as the requirement is only `{{...}}`).
- No fast-exit optimization (no pre-check for `{{` inclusion — negligible difference).
- Missing KDoc comments (only Korean inline comments present).

#### Test Coverage
- Basic formatting, key templates, mixed (inside + outside strings), nested templates, validity verification (positive + **negative**).
- **Most balanced test configuration**.

---

### Comparison Table

| Item | no-agents | agents-v1 | agents-v2 |
|------|-----------|-----------|-----------|
| **Code Conciseness** | Medium | Low (complex 2-step sub) | **High** |
| **Accuracy** | High | Medium (unstable lookbehind) | **High** |
| **Code Change Scope** | Broad (whitespace+refactor) | Medium | **Minimal** |
| **Test Isolation** | ✗ (Added to existing file) | ✓ | **✓** |
| **Negative Tests** | ✗ | ✗ | **✓** |
| **Extensibility** (`${...}`, etc.) | ✓ | ✗ | ✗ |
| **Parameter Shadowing Fix** | ✓ | ✗ | ✗ |
| **Lines Changed** | ~384 lines | ~243 lines | **~193 lines** |

---

### Final Recommendation: `agents-v2-test.patch`

#### Reasons for Recommendation

1. **Principle of Minimal Changes**: Best aligns with the "Minimal changes; preserve public APIs" principle specified in AGENTS.md. Adds core functionality while barely touching the existing code structure.

2. **Regex Strategy Accuracy**: The `("(?:\\.|[^\\"])*")|(\{\{.*?\}\})` pattern accurately distinguishes between the inside and outside of string literals in a single pass. It is much more stable than agents-v1's 2-step lookahead/lookbehind approach and sufficient without no-agents' `DOT_MATCHES_ALL` option.

3. **YAGNI Principle**: Since the requirement is only the `{{...}}` syntax, supporting `${...}` or `<%...%>` (no-agents) is over-engineering. Groups can be added to the regex later if needed.

4. **Test Quality**: Provides the best edge case coverage as the only one including **negative cases** (broken template) and **nested template** tests.

5. **Code Readability**: Intent is clear with about 30 lines of core logic, without the need for complex delimiter logic like `_TPL_Q_` in agents-v1.

#### Suggested Improvements
- Add KDoc comments to `replaceTemplates`/`restoreTemplates`.
- Add uglify mode tests.
- Add `if (!json.contains("{{"))` fast-exit (optional).
