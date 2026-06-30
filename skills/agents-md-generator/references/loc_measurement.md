# LOC Measurement Specification

Defines the method for measuring repository size and determining dynamic character limits for AGENTS.md.

## Measurement Command

```bash
tokei -e "*.json" -e "*.yaml" -e "*.yml" -e "*.md" -e "*.sh" -e "*.lock" -e "*.map" -e "*.svg" -e node_modules -e vendor -e dist .
```

**Priority**: This is the **first step** before generating AGENTS.md.

The explicit directory excludes (`node_modules`, `vendor`, `dist`) matter outside git repositories: `tokei` honors `.gitignore` only inside a git repo, so vendored dependencies and build output would otherwise inflate LOC in exported or unzipped directories.

## Tool Installation

If `tokei` is not installed:

```
tokei is not installed.
https://github.com/XAMPPRocky/tokei Please install it from here and try again.
```

## Character Limit by Repository Scale

```yaml
- scale: Small
  loc_range: "≤ 10,000"
  character_limit: 10,000
- scale: Small-Medium
  loc_range: "10,001 ~ 50,000"
  character_limit: 12,000
- scale: Medium
  loc_range: "50,001 ~ 100,000"
  character_limit: 15,000
- scale: Medium-Large
  loc_range: "100,001 ~ 500,000"
  character_limit: 20,000
- scale: Large
  loc_range: "500,001 ~ 1,000,000"
  character_limit: 30,000
- scale: Extra-Large
  loc_range: "> 1,000,000"
  character_limit: 50,000
```

## Workflow

1. Run `tokei` command to get total LOC
2. If tokei not installed → display installation guide and stop
3. Determine repository scale from LOC value
4. Apply corresponding character limit to AGENTS.md generation

## Section Budget Allocation

Distribute the total character limit across sections to prevent front-loading. These are recommended proportions — adjust slightly based on project characteristics.

**Budget scope in update mode**: the character limit covers the preamble plus the standard (managed) sections only. Custom user sections are excluded from the limit and must never be trimmed to satisfy it.

### Single Repo / Package Document (4-5 Sections)

`Ownership Map` is optional. Use its budget only when repository analysis finds concrete, stable ownership boundaries. If no such boundaries are detected, omit the section and do not pad other sections just to consume the unused budget.

```yaml
- section: "1. Overview"
  budget: "5%"
  note: "Keep brief; 1-2 sentences"
- section: "2. Ownership Map"
  budget: "25%"
  note: "Optional; current responsibility boundaries, not directory inventory"
- section: "3. Core Behaviors & Patterns"
  budget: "30%"
  note: "Cross-cutting patterns need detail to be actionable"
- section: "4. Conventions"
  budget: "25%"
  note: "Each convention should include rule + example"
- section: "5. Working Agreements"
  budget: "15%"
  note: "Fixed rules; relatively stable across projects"
```

### Monorepo Root Document (2-3 Sections)

For monorepo roots, include `Ownership Map` when package-level roles or shared cross-package contracts are evident from names plus manifests, public exports, README text, or dependency direction. If the root only exposes an uninformative package list, omit the section.

```yaml
- section: "1. Overview"
  budget: "10%"
- section: "2. Ownership Map"
  budget: "50%"
  note: "Optional; package-level responsibility boundaries and shared contracts"
- section: "3. Working Agreements"
  budget: "40%"
```

## tokei Output Interpretation

Use the **Total** lines value from tokei output:

```
===============================================================================
 Language            Files        Lines         Code     Comments       Blanks
===============================================================================
 TypeScript            150        45000        38000         3000         4000
 JavaScript             30         5000         4200          400          400
-------------------------------------------------------------------------------
 Total                 180        50000        42200         3400         4400
===============================================================================
```

In this example: Total Lines = 50,000 → Small-Medium → 12,000 chars limit
