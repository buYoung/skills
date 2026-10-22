# Skills, prompt templates, and themes

Read the section for each static resource the package provides. These resources work directly; static content needs no executable extension wrapper. Include their supporting files in the distribution.

## Contents

- [Rules for all three resource types](#rules-for-all-three-resource-types)
- [Skills](#skills)
- [Prompt templates](#prompt-templates)
- [Themes](#themes)

## Rules for all three resource types

- **Name collisions:** the first discovered name wins, and Pi skips a later resource with the same name and reports a `collision` diagnostic. Project and personal resources, from settings entries or automatic discovery, come before installed package resources, so a user's skill, prompt, or theme with the same name hides the package's. A temporary `-e` package comes earlier still. Package-prefixed names avoid depending on this order.
- **Frontmatter position:** in a skill or prompt template, put the opening `---` on the file's first line. Pi strips a byte-order mark, but anything else before that line, even a blank line, means the file has no frontmatter. A skill without frontmatter has no description and is skipped.
- **Excluded files:** traversal skips dot-prefixed entries and `node_modules`, and applies `.gitignore`, `.ignore`, and `.fdignore` files found inside the scanned root and its descendants. A resource under a hidden or ignored directory is not discovered, and the package-root `.gitignore` does not filter a scan rooted in a resource directory such as `skills/`.

## Skills

Prefer one directory per skill:

```text
skills/acme-orient/
├── SKILL.md
└── references/output.md
```

```markdown
---
name: acme-orient
description: Map a workspace's entry points and development commands. Use when first exploring an unfamiliar project or preparing to change it.
---

# Workspace orientation

Read `references/output.md` for the output shape.

1. Identify the workspace root, package manifests, and application entry points.
2. Trace the files related to the user's intended change.
3. Describe the relevant directories, commands, and unresolved questions.

Resolve supporting file paths relative to this skill directory.
```

### Frontmatter fields

- **`name`:** keep it equal to the directory name for portability. Use lowercase ASCII letters, digits, and single hyphens, up to 64 characters, without a leading or trailing hyphen and without `--`. Quote a name that looks like a number so YAML keeps it a string. A missing, non-string, or empty name falls back to the parent directory name, so root-level `.md` files can all become `skills` and collide.
- **`description`:** a nonempty string of at most 1024 UTF-16 code units that explains both what the skill does and when to use it. Quote the YAML value when the text contains characters such as `: `.
- **`disable-model-invocation`:** the boolean `true` hides the skill from the model's automatic-selection list; the quoted string `"true"` does not. Manual `/skill:acme-orient` invocation still expands the skill.

```yaml
disable-model-invocation: true
```

Pi reads only `name`, `description`, and `disable-model-invocation`. Other metadata can help other runtimes, but `allowed-tools` is **not a Pi permission boundary**.

### What Pi enforces

| Condition | Pi's loader result |
|---|---|
| Unreadable `SKILL.md` or malformed YAML | Warning; skill skipped |
| Missing, blank, or non-string description | Warning; skill skipped |
| Invalid name characters, length, or hyphens | Warning; skill still loaded |
| Description over 1024 | Warning; skill still loaded |
| Name differs from directory | Loaded; equality is not checked |
| Same name at another path | Earlier entry wins; later entry skipped with a `collision` diagnostic |

Produce compliant names and lengths even where Pi only warns. Pi can silently ignore generic root `.md` candidates that lack valid frontmatter, which is another reason to use explicit `SKILL.md` directories.

### How the model finds and runs a skill

- The model first sees the names, descriptions, and paths, then reads the body of a skill it selects. Pi advertises this list only when `read` or `bash` capability is available, so do not promise automatic discovery in a tool set with neither.
- `/skill:acme-orient additional context` inserts the body, its base directory, and the supplied arguments. Put a normal space after the name; the parser does not treat a tab or newline there as a space.
- `enableSkillCommands: false` affects interactive autocomplete, not manually typed `/skill:` expansion.

### Discovery and supporting files

A directory that contains `SKILL.md` ends the descent, so put sibling skills beside one another, not inside another skill. You can organize supporting files as `references/`, `scripts/`, or `assets/`. Relative references must still resolve after packing and extraction.

Write a precise activation description, a finite workflow, the expected output, and explicit routing to large supporting references. Put detailed procedures in the skill body, not in the description metadata.

## Prompt templates

### Choose a command name

`prompts/acme-focus.md` becomes `/acme-focus`. Parent directories do not namespace commands, so two nested `review.md` files collide. Use distinct basenames without whitespace.

Interactive mode handles its own built-in commands before the whole [input processing pipeline](#input-processing-order), including extension commands and skill expansion, without a collision diagnostic. A prompt with one of these names never runs there when invoked without arguments:

`settings`, `scoped-models`, `model`, `thinking`, `export`, `import`, `share`, `bug`, `copy`, `name`, `session`, `changelog`, `hotkeys`, `fork`, `clone`, `tree`, `trust`, `login`, `logout`, `new`, `compact`, `reload`, `debug`, `resume`, `quit`

`bug`, `compact`, `export`, `import`, `login`, `model`, `name`, and `thinking` are intercepted with arguments too. Choose prompt names outside this list.

### Example and expansion

```markdown
---
description: Investigate a selected workspace area with a specific focus
argument-hint: "[target] [focus] [additional context...]"
---

Investigate ${1:-the current workspace}.
Focus on ${2:-entry points and execution flow}.
Additional context: ${@:3}
```

At the reference commit,

```text
/acme-focus "src/api.ts" "" concurrency
```

expands to:

```text
Investigate src/api.ts.
Focus on entry points and execution flow.
Additional context: concurrency
```

Empty quoted arguments are preserved in `v1.3.0` and `v1.4.0`. The older `v1.2.0` release drops them; check the actual target when supporting that release.

### Frontmatter

- Frontmatter is optional. When `description` is absent, not a string, or an empty string, Pi uses the first nonempty body line, truncated to 60 characters plus an ellipsis when needed. Pi keeps a whitespace-only description instead of replacing it, so do not use one.
- `argument-hint` is display metadata; `<required>` does not enforce that an argument is present. Describe what happens when input is missing, or use defaults.
- Quote values that begin with `[` or `{` or contain `: `. Unquoted, `argument-hint: [focus]` parses as a YAML list and is silently dropped, and `argument-hint: [target] [focus]` or `description: Review: API` is a YAML error that makes Pi skip the whole prompt with a warning.

### Complete substitution grammar

| Syntax | Meaning |
|---|---|
| `$1`, `$2`, `$10` | One-based positional argument; a missing one becomes empty |
| `$@`, `$ARGUMENTS` | All parsed arguments joined with spaces |
| `${1:-default}` | Default if that argument is missing or empty |
| `${@:-default}`, `${ARGUMENTS:-default}` | Default if the joined argument string is empty |
| `${@:2}` | Arguments from position 2 through the end |
| `${@:2:3}` | Up to three arguments starting at position 2 |
| `${@:0}` | Same starting position as 1 |
| `${@:1:0}` | Empty string |
| `$0` | Empty string |
| `${1}`, `${-1:-x}`, `${ARGUMENTS:2}` | Unsupported; remain literal |

Substitution makes one pass over the original template:

- Inserted text is not expanded again.
- No escape produces a literal `$1`, `$@`, or `$ARGUMENTS`; code fences and backslashes do not protect them.
- A default ends at the first `}`, so do not nest syntax or put `}` inside a default.
- `$1suffix` and `$ARGUMENTS_suffix` still substitute their prefixes.

### Argument parsing

- Single and double quotes group whitespace. Adjacent quoted and unquoted fragments join: `a"b c"d` is one argument, `ab cd`.
- An unmatched quote consumes the rest of the input instead of raising an error.
- There is no backslash escaping, environment expansion, glob expansion, or command substitution: `a\ b` yields `a\` and `b`.
- `$@` does not preserve argument boundaries the way a shell does. Two empty arguments join into a space, so an all-arguments default does not apply to that pair.

A template produces text. Never treat substitution as shell-safe quoting: if the expanded task runs a command, build the process arguments separately instead of interpolating untrusted text into a shell string.

### Input processing order

Pi processes input in this order: extension command → `input` event → skill expansion → prompt-template expansion. An extension command can therefore shadow a prompt with the same name. Expanded output is not run again as another slash command.

### Discovery depth

Package prompt directories are searched recursively. Automatic personal and project prompt directories, and CLI `--prompt-template <dir>`, read only the files directly inside them.

## Themes

The full [starter theme](../assets/starter/themes/acme-midnight.json) contains all 56 supported color tokens. Copy and recolor it; you do not need to find an upstream theme.

### JSON contract

The required top-level keys are `name` and `colors`. The only optional keys are `$schema`, `appearance`, `vars`, and `export`. Any other key is rejected, including `author` or `version` at the top level and custom token names under `colors`; put metadata outside the theme and custom color names in `vars`.

- **`name`:** a nonempty string without `/`. Use a package-specific name and a matching `<name>.json` filename.
- **Reserved names:** do not use `system`, `dark`, or `light`. The JSON schema accepts them, but the built-in themes come first in the theme list and `system` always resolves to the generated built-in theme, so a package theme with one of these names cannot be selected. The bundled theme checker rejects these names.
- **`appearance`:** `"light"` or `"dark"`; set it explicitly.
- **`$schema`:** optional string metadata. Omit it for an entirely local authoring flow; the bundled theme checker already contains the complete contract.
- **`vars`:** reusable color names. Color references resolve here, not to other `colors` slots.
- **`export`:** optional `pageBg`, `cardBg`, and `infoBg` colors for HTML export.

### Required 51 color tokens

```text
accent border borderAccent borderMuted success error warning muted dim
text thinkingText selectedBg
userMessageBg userMessageText customMessageBg customMessageText customMessageLabel
toolPendingBg toolSuccessBg toolErrorBg toolTitle toolOutput
mdHeading mdLink mdLinkUrl mdCode mdCodeBlock mdCodeBlockBorder
mdQuote mdQuoteBorder mdHr mdListBullet
toolDiffAdded toolDiffRemoved toolDiffContext
syntaxComment syntaxKeyword syntaxFunction syntaxVariable syntaxString
syntaxNumber syntaxType syntaxOperator syntaxPunctuation
thinkingOff thinkingMinimal thinkingLow thinkingMedium thinkingHigh thinkingXhigh
bashMode
```

### Optional tokens

| Optional token | Fallback |
|---|---|
| `scrollbarTrack` | `muted` |
| `scrollbarThumb` | `text` |
| `searchMatchBg` | `selectedBg` |
| `searchMatchText` | `text` |
| `thinkingMax` | `thinkingXhigh` |

### Color values

```json
{
  "vars": {
    "accent": "#60a5fa",
    "shortHex": "#0af",
    "perceptual": "oklch(62% 0.1 200)",
    "hslAlternative": "okhsl(250 60% 55%)",
    "palette": 117,
    "terminalDefault": "",
    "alias": "accent"
  }
}
```

This snippet illustrates the value forms; it is not a complete theme.

- Palette indices are integers from 0 to 255.
- An empty string uses the terminal's default foreground or background, as appropriate for the token.
- CSS names such as `"red"` and `rgb(...)` are not color literals here; Pi treats them as variable references.
- The JSON schema does not fully check strings, so also validate actual color resolution.
- Keep every variable reference defined and acyclic. Runtime resolution visits only the variables that colors use, so a bad unused variable can pass load validation.
- Export colors resolve separately and can fall back after an error instead of invalidating the whole theme.

### Discovery

Package `themes/` directories and directory entries in settings are searched recursively for `.json` files. Automatic personal and project theme directories, and CLI `--theme <dir>`, read only the files directly inside them. Every `.json` file in a recursively searched package theme directory loads as a theme, so a non-theme JSON file there produces a diagnostic; keep other JSON outside it.

### Verification and reload

Select the theme in the CLI and inspect theme diagnostics. A missing active theme can fall back to `system`, so a working screen does not prove that the requested theme loaded. Inspect normal text, selected text, code, diffs, errors, and tool backgrounds, on both truecolor and limited-color terminals when the package supports them.

The CLI installs strict schema validation, but SDK loading may skip it. The bundled [package validator](../scripts/validate-package.mjs) therefore checks, without fetching a schema, every required token, allowed key, color syntax, variable reference, and cycle. It also catches bad unused variables, export colors that Pi may defer or tolerate, and reserved built-in theme names. [Validation](validation.md) has the commands and visual checks.

Pi can watch the active personal theme file automatically. Package and project themes need `/reload` after editing, so do not advertise automatic hot reload for every package resource.
