---
name: ux-design-guide
description: Reviews existing UI for UX guideline violations and generates implementation guidance based on 99+ rules across Navigation, Layout, Accessibility, Forms, Performance, Typography, and more. Supports Web, Mobile, and Desktop GUI platforms. Use when the user requests a UX review, UX audit, UI accessibility check, or implementation guidance for user experience best practices.
---

# UX Design Guide

Comprehensive UX review and implementation guidance system based on 99+ validated guidelines across 8 domains.

## Core Capabilities

### Review Mode (Audit Existing UI)

Analyzes existing UI code or screenshots against the full guideline set to identify violations and improvement opportunities.

- Scan codebase for UX anti-patterns
- Map violations to specific guidelines with severity
- Provide actionable fix recommendations with code examples
- Prioritize findings by severity and user impact

### Guide Mode (Advise on New UI)

Provides proactive implementation guidance when building new UI components or features.

- Recommend best practices for the target platform
- Provide code examples following guidelines
- Flag potential UX pitfalls before they occur
- Suggest appropriate patterns for the use case

## Severity Levels

| Level | Criteria | Action |
|-------|----------|--------|
| **High** | Blocks usability, causes accessibility failures, or breaks core interactions (e.g., missing focus states, no touch targets, color contrast violations) | Must fix before release |
| **Medium** | Degrades experience but has workarounds (e.g., missing hover states, suboptimal animation timing, no inline validation) | Should fix in current cycle |
| **Low** | Polish and best-practice improvements (e.g., easing functions, date formatting, breadcrumbs on shallow sites) | Fix when convenient |

## Platform Coverage

| Platform | Scope |
|----------|-------|
| **Web** | Desktop browsers, responsive web, PWA |
| **Mobile** | iOS, Android native and hybrid apps |
| **Desktop** | Electron, Tauri, native desktop GUI |
| **VisionOS** | Spatial UI, gaze interaction |
| **All** | Cross-platform universal guidelines |

## Domain Knowledge

| Domain | Guidelines | Reference |
|--------|-----------|-----------|
| Navigation & Motion | 14 | [navigation-motion.md](references/navigation-motion.md) |
| Layout & Responsive | 15 | [layout-responsive.md](references/layout-responsive.md) |
| Interaction & Touch | 14 | [interaction-touch.md](references/interaction-touch.md) |
| Accessibility | 11 | [accessibility.md](references/accessibility.md) |
| Forms | 10 | [forms.md](references/forms.md) |
| Performance | 8 | [performance.md](references/performance.md) |
| Visual & Feedback | 16 | [visual-feedback.md](references/visual-feedback.md) |
| Emerging Patterns | 12 | [emerging-patterns.md](references/emerging-patterns.md) |

## Input Contract

| Field | Required | Description |
|-------|----------|-------------|
| **Target** | Yes | UI code, component, page, or screenshot to review/guide |
| **Mode** | No | `review` (audit existing) or `guide` (advise new). Default: inferred from context |
| **Platform** | No | Web, Mobile, Desktop, VisionOS, or All. Default: inferred from code |
| **Focus areas** | No | Specific domains to prioritize (e.g., accessibility, forms, performance) |
| **Scope** | No | Full audit or targeted check. Default: full |

## Review Output Format

```
## UX Review: {Target}

### Summary
- **Platform**: {detected platform}
- **Total findings**: {count}
- **High**: {count} | **Medium**: {count} | **Low**: {count}

### Findings

#### [{Severity}] {Issue Name}
- **Domain**: {category}
- **Guideline**: {rule reference}
- **Location**: {file:line or component}
- **Problem**: {what is wrong and why it matters}
- **Fix**: {specific recommendation}
- **Code Before**: `{current code}`
- **Code After**: `{fixed code}`

### Priority Roadmap
1. {High severity items first}
2. {Medium severity items}
3. {Low severity items}
```

## Guide Output Format

```
## UX Guide: {Feature/Component}

### Platform: {target platform}
### Applicable Guidelines

#### {Domain}: {Guideline Name}
- **Severity**: {level}
- **Recommendation**: {what to implement}
- **Example**: `{code example}`
- **Avoid**: `{anti-pattern}`

### Implementation Checklist
- [ ] {guideline-based check}
- [ ] {guideline-based check}
```

## Workflow

```
1. Identify Target    → Determine what UI to review or guide
2. Detect Platform    → Infer platform from code/context
3. Select Guidelines  → Filter applicable rules by platform and focus
4. Analyze/Advise     → Review mode: find violations | Guide mode: recommend patterns
5. Classify Severity  → Rate each finding as High/Medium/Low
6. Generate Output    → Produce structured report with code examples
```
