# Report templates

Use the template for the task. Keep the headings and their order; omit a section only when it has nothing to say, except **Layer map**, which every Design, Audit, and Restructure report includes. When one request covers several tasks, use the last task's template; in a Restructure report, each finding of the audit appears either in **Steps applied**, under the step that resolved it, or under **Remaining findings**. Write in the user's language. Module names, paths, commands, and rule IDs stay as they are.

## Shared tables

**Toolchain mapping**

```markdown
| Question | <toolchain> | Source |
|---|---|---|
| Module unit | | |
| Cycle check, and at which level | | |
| What hides an implementation; directory visibility and sub-directory scope | | |
| Entry file, or what defines the surface; whether a sub-directory changes qualified names | | |
| Resource access | | |
| Bindings, and generation across a language boundary | | |
| Executable entry; dependencies per executable | | |
| Output, cache, and dependency directories; tracked generated files | | |
| Fixed-path files and directories | | |
| Graph command; enforcement already present, and available | | |
```

Keep all ten rows, in one table per toolchain. **Source** is the manifest line, command, or document the answer came from. Write `unconfirmed` only for an answer that could not be checked against the repository or the toolchain, and `n/a` with the reason for a question that does not apply.

**Layer map**

```markdown
| Module | Path | Layer | References | Public surface | Notes |
|---|---|---|---|---|---|
| core | core/ | 0 | — | <entry module or equivalent> | external: none |
| billing | services/billing/ | 1 | core | <entry module or equivalent> | |
| storage | services/storage/ | 1 | core | <entry module or equivalent> | owns migrations/ |
| desktop | apps/desktop/ | 2 | billing, storage, core | — (executable) | Composition Root: <entry point> |
```

The rows show the shape; use the project's own module names and paths, and name the public surface the way the toolchain mapping defines it. **References** lists project modules only. **Layer** holds one number; for a module that mixes layers, write the layers it mixes (`1+2`) and raise the L1 finding; for developer tools, shared test-support modules, examples, benchmarks, and design-time previews, write `outside`. A companion module (tests, or editor-only tooling for one module) shares the row of the module it accompanies.

**Notes** carries, each with its reason: each cross-language edge that no build system declares, each boundary that nothing enforces mechanically, and each deviation the user accepted, other than a same-layer reference, which the next table holds. A deviation the user has not accepted is a finding, not a note. Every external dependency of a Layer 0 module is named there either way: with its reason once accepted, with its finding number until then, and as `proposed` in a Design, where **Decisions needed** lists it.

**Same-layer references**

```markdown
| From | To | What it uses | Status |
|---|---|---|---|
| billing | money-math | <names used> | recorded (pure library) |
| billing | storage | <names used; what billing cannot build or test without it> | finding <n> |
| reports | billing | <names used> | accepted: <reason on record> |
```

One row for each direct Layer 1 → Layer 1 reference. **Status** is `recorded` for a reference to a pure library; `accepted` only when the user was asked about that reference and accepted it, or the repository already records the exception; `proposed` in a Design, with the reference listed under **Decisions needed**; and `finding <n>` for every other row, under L2 when the reference closes a cycle and L3 otherwise. In an Audit, keep this section when there are no such references and write `None`.

**Execution units**

```markdown
| Unit | Role and privilege | Composition Root | References | Unneeded references |
|---|---|---|---|---|
```

## Design

```markdown
# Structure design: <project>

## Toolchain mapping

## Layer map

## Same-layer references

## Execution units

## Directory tree
<Tree with a layer label on each module.>

## Layer 0 contents
<Shared definitions and which module holds them; cross-language contracts and how the other side is generated.>

## Resources
<Which module owns which resources and how they are reached.>

## Ignore and packaging
<Ignore entries; scratch location; publish allowlist.>

## Enforcement
<What the toolchain enforces already; what is proposed in addition.>

## Decisions needed
<Each with the assumption the design makes until the user answers.>
```

## Audit

```markdown
# Structure audit: <project>

## Scope
<Toolchains found, modules examined, vendored, third-party, and generated code set aside, and how the dependency graph was obtained.>

## Toolchain mapping

## Layer map (current)

## Same-layer references

## Execution units

## Findings
<Sorted by rule ID: L1, L2, L3, L4, S, E, R, F, C, V. Number them after sorting. Every finding carries all four fields.>

### <n>. <Rule ID> — <short title>
- **Where:** <path, path:line taken from line-numbered output, or manifest entry>
- **Evidence:** <the import, reference, duplicate, or path, quoted>
- **Effect:** <what this makes harder or unsafe>
- **Fix:** <the structural change that resolves it, the toolchain mechanism that carries it out, and whatever it breaks, widens, or adds>

## Other observations
<Real defects that no rule covers. No rule ID.>

## Target structure
<Target layer map and tree, showing only what changes.>

## Migration steps
<Steps in the default order of restructuring.md, with the reason for any step taken out of that order; each names the findings it resolves.>

## Decisions needed
<The user's decisions the target structure depends on, each with the assumption made here.>

## Not checked
<Areas, modules, or rules not examined, and why.>
```

When a rule has no finding, do not list it. When there are no findings at all, say so under **Findings** and still give the layer map.

## Restructure

```markdown
# Restructure: <project>

## Status
<Done, partly done, or stopped; one sentence on what remains. The baseline build and test result before the first step.>

## Steps applied
| Step | What moved | Rules resolved | Verification |
|---|---|---|---|
<Verification names the command and its result.>

## Toolchain mapping

## Layer map (after)

## Same-layer references

## Remaining findings
<Findings not resolved, temporary shims still present, exceptions recorded.>

## Decisions needed

## Not verified
<What could not be built, tested, or checked, and why.>
```

## Place

Answer briefly: the location, the rule or table row that decides it, the execution units the code runs in and any contract between them, the toolchain-mapping answers the placement depends on with their sources, and any structural change it requires. Where an existing convention conflicts with a rule, give the convention's location and the rule that separates the two. Include the layer-map row of every module the placement adds or changes, and no others.
