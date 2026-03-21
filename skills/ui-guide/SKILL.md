---
name: ui-guide
description: "Generate, update, and maintain UI style guide documents from actual codebase analysis. Scans project files (Tailwind config, CSS/SCSS, design tokens, component code) to extract real color palettes, typography scales, spacing systems, component patterns, and layout approaches — then produces a structured Markdown style guide for developers. Use PROACTIVELY when: user asks to create a style guide, document UI conventions, audit current styles, update an existing style guide, or wants UI/UX recommendations for their project. Triggers on: 'style guide', 'UI guide', 'UI 가이드', '스타일 가이드', 'document styles', 'UI conventions', 'design documentation', '스타일 문서', 'UI 문서화'. Also triggers on Korean phrases like '스타일 가이드 만들어줘', '업데이트해줘', 'UI 추천해줘'."
argument-hint: "[create|update|recommend] [options]"
license: MIT
metadata:
  author: claudekit
  version: "1.0.0"
---

# UI Guide — Codebase Style Guide Generator

Analyze your project's actual UI implementation and produce a living Markdown style guide that developers can reference daily. Supports creating new guides, updating existing ones, and recommending improvements.

## Modes

| Mode | Trigger | Output |
|------|---------|--------|
| **Create** | `create`, `생성`, `만들어줘` | New `docs/ui-style-guide.md` |
| **Update** | `update`, `업데이트`, `갱신` | Updated existing guide |
| **Recommend** | `recommend`, `추천`, `개선` | Conversation (no file) |

If no mode keyword is detected, infer from context:
- Existing guide file found + user mentions changes → **Update**
- No guide file exists → **Create**
- User asks "better", "recommend", "추천", "개선" → **Recommend**

## Workflow

### Step 1: Discover Project Stack

Identify the tech stack by checking for these files (in order):

```
tailwind.config.{js,ts,mjs,cjs}  → Tailwind CSS
postcss.config.*                   → PostCSS
next.config.*                      → Next.js
vite.config.*                      → Vite
nuxt.config.*                      → Nuxt
svelte.config.*                    → SvelteKit
package.json                       → dependencies → React/Vue/Svelte/etc.
*.xcodeproj / Package.swift        → SwiftUI
pubspec.yaml                       → Flutter
```

Record: framework, CSS approach (Tailwind/CSS Modules/styled-components/vanilla), component library (shadcn/ui, MUI, Ant Design, etc.).

### Step 2: Scan Style Sources

Scan the codebase for style definitions. Read the reference for the full scanning procedure:

| Source Type | Reference |
|-------------|-----------|
| Full scan procedure | [`references/scan-procedure.md`](references/scan-procedure.md) |
| Output template | [`references/guide-template.md`](references/guide-template.md) |

**Quick summary of what to scan:**

1. **Colors** — Tailwind theme colors, CSS custom properties (`--color-*`, `--*`), SCSS variables, design tokens
2. **Typography** — Font families, size scale, weight usage, line heights, Google Fonts imports
3. **Spacing** — Tailwind spacing scale overrides, consistent padding/margin patterns, gap usage
4. **Components** — Reusable component files, their props/variants, naming conventions
5. **Layout** — Grid/flex patterns, breakpoints, container widths, responsive approach
6. **Icons** — Icon library used (Lucide, Heroicons, custom SVGs), size conventions
7. **Dark Mode** — Strategy (class-based, media query, CSS variables), token switching
8. **Accessibility** — ARIA patterns, focus styles, color contrast approach, reduced motion

### Step 3: Generate or Update

**Create mode:**
1. Run the full scan (Step 2)
2. Build the guide using `references/guide-template.md` as the structure
3. Fill each section with actual values extracted from the codebase
4. Add recommendation notes where patterns deviate from best practices
5. Write to `docs/ui-style-guide.md` (or user-specified path)

**Update mode:**
1. Read the existing guide file
2. Run the scan again
3. Diff: identify new tokens/components, removed ones, and changed values
4. Update the guide in-place, adding a "Last Updated" timestamp
5. Summarize changes to the user

**Recommend mode** (no file output):
1. Run a lightweight scan (colors, typography, key patterns only)
2. Identify potential improvements:
   - Inconsistent spacing or color usage
   - Missing dark mode support
   - Accessibility gaps (contrast, focus states)
   - Unused or redundant style definitions
   - Better alternatives from industry standards
3. Present findings conversationally with specific, actionable suggestions
4. For each recommendation, explain **why** it matters and show a before/after code example

### Step 4: Best Practice Cross-Reference (Optional)

When the ui-ux-pro-max skill is available in the project, enhance recommendations by querying its search engine:

```bash
# Find relevant UX guidelines
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "accessibility contrast" --domain ux

# Get style recommendations
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "minimalism" --domain style

# Check color palette best practices
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "saas dashboard" --domain color
```

This step enriches the guide with industry best practices but is not required — the skill works independently without ui-ux-pro-max.

## Output Location

Default: `docs/ui-style-guide.md`

If the user specifies a different path, use that instead. Common alternatives:
- `STYLE_GUIDE.md` (project root)
- `docs/design/style-guide.md`
- `.github/STYLE_GUIDE.md`

## Important Notes

- Extract **actual values** from the codebase — never invent or assume colors, fonts, or spacing that don't exist in the code.
- When values are ambiguous (e.g., inline styles mixed with Tailwind), document both and flag the inconsistency.
- Keep the guide developer-focused: include copy-pasteable code snippets, not abstract design theory.
- The guide should be a **living document** — encourage the user to run update mode after major UI changes.
- For Recommend mode, be thorough and conversational. Explain trade-offs. Show code examples. Don't generate a file unless explicitly asked.
