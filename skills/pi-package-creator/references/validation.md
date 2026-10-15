# Package validation and behavioral testing

Use this procedure after creating a package, and again after changing its manifest, resources, dependencies, or extension behavior. The commands, expected results, test format, and checking code are all in this skill; no external schema, tutorial, test service, or documentation is needed.

**Prerequisites:**

- The package validator needs Node.js `>=22.19.0`; its runtime checks also need the installed target Pi.
- Creating an artifact needs npm, and extracting it needs `tar`.
- Tool tests use Pi's public faux provider and need no model account or API key.
- Install the package's ordinary runtime dependencies before running extensions that import them. The bundled scripts never download Pi or install dependencies automatically.

## Contents

1. [Select the checks](#1-select-the-checks)
2. [Run the package validator](#2-run-the-package-validator)
3. [Test tools without a live model](#3-test-tools-without-a-live-model)
4. [Exercise resources and lifecycle through Pi](#4-exercise-resources-and-lifecycle-through-pi)
5. [Check provider and MCP integrations](#5-check-provider-and-mcp-integrations)
6. [Verify the delivered form, then report](#6-verify-the-delivered-form-then-report)
7. [Give the user verification commands](#7-give-the-user-verification-commands)

## 1. Select the checks

Start from the package's purpose, intended resources, implemented features, and delivery source. Every resource type is optional: extensions-only, skills-only, prompts-only, themes-only, and mixed packages are all valid. An extension need not register tools; it can provide only commands, events, or UI.

Select the checks before running them:

| Package scope or feature | Applicable checks | Not required just because this guide covers it |
|---|---|---|
| Every package | Intended resource and file inventory, actual discovery and load, relevant diagnostics and selection boundaries | All four resource types |
| Extensions | Factory, import, and registration behavior, and the implemented handlers | A skill, prompt, theme, or tool |
| Registered tools | Argument and result contracts and meaningful success and error cases; cancellation for ongoing work; size limits for growing output | Running the example tool cases unchanged, or adding a tool only to test one |
| Commands, events, UI | Their actual invocation, event, or UI behavior | The tool runner when no tools exist |
| Skills | Frontmatter, discovery and invocation, supporting files actually referenced | Executable extension tests |
| Prompts | Discovery and the argument forms the prompt supports | Theme or extension tests |
| Themes | Theme JSON and colors, selection and rendering | Tool tests or provider access |
| Stateful or long-lived behavior | Restoration and cleanup across supported lifecycle transitions | Inventing persistence, watchers, or subprocesses for a stateless package |
| Provider or MCP integration | Its configured authentication, connection, call, error, and cancellation behavior | A live integration check for a package without such an integration |
| Local delivery | Actual load from the local directory and the applicable behavior | npm metadata, a gallery listing, or an npm tarball |
| npm delivery or a requested tarball | npm metadata, actual archive contents, checks on the extracted copy | Registry publication, unless requested |
| Git delivery | A clean checkout of the intended ref with production dependencies | An npm tarball when that is not the delivery format |

Record each result with one status:

- `not_applicable`: an absent optional resource or an unused feature. A package without a theme is complete without theme validation.
- `skipped`: an applicable check that could not run. A theme check blocked by a missing runtime remains unverified.
- `fail`: a violated contract or expectation. A package that promises a theme that cannot load has a failure.
- `warning`: a nonblocking recommendation.

### Write the inventory

The inventory states what the package must contain, so the validator can catch a resource that silently fails to load. Adapt [extensions-only-inventory.json](../assets/testing/extensions-only-inventory.json) for an extension package, or [starter-inventory.json](../assets/testing/starter-inventory.json) for the complete four-resource demonstration. Both are examples, not universal expected contents. The extensions-only example keeps the starter's extension and helper and asserts `skills: []`, `prompts: []`, and `themes: []`; rename its tools, commands, and flags, and use `[]` for capabilities your extension does not register.

Keep the inventory outside automatically discovered resource directories. Do not generate the expected values from the loader's result: an accidentally empty load would then validate itself.

The inventory has four optional groups:

| Group | Meaning |
|---|---|
| `resources` | Exact package-relative discovered file paths for `extensions`, `skills`, `prompts`, and `themes`; use `[]` for absent types |
| `names` | Exact public `tools`, `commands`, `flags`, `skills`, `prompts`, and `themes`; use `[]` where none are intended |
| `requiredFiles` | Every entry point, imported helper, resource, skill reference, and runtime asset that must be shipped |
| `forbiddenFiles` | Specific package-relative files that must not exist or be packed, such as a known credential file or a draft entry point |

- Each supplied key is an assertion. `[]` requires that the category has no resources or names; it does not ask you to add any.
- An omitted key or group is not checked, and it does not inherit the starter's contents.
- Resource paths name the resolved entry files, such as `skills/acme-orient/SKILL.md`, not their directories. Use `/` as the separator.
- In `requiredFiles`, list only files this package needs; unused starter files are not requirements.

Review imports and generated bundles yourself as well. Confirm that imported host packages have wildcard peers, public imports resolve, non-host runtime dependencies are declared under `dependencies`, no physical host copy is bundled, and helpers sit outside automatic extension scanning. The validator matches imports with regular expressions and does not claim to be a full TypeScript or bundler analysis.

## 2. Run the package validator

Set these absolute paths for the current task:

```bash
skill_dir="/absolute/path/to/pi-package-creator"
package_dir="/absolute/path/to/your-package"
inventory="/absolute/path/to/your-package-inventory.json"
check_dir="$(mktemp -d)"

node "$skill_dir/scripts/validate-package.mjs" "$package_dir" \
  --expect "$inventory" --runtime \
  --report "$check_dir/package-check.json"
```

- For npm delivery or a requested tarball, append `--pack`. Local and git packages do not need an npm artifact because of this example.
- A local package without `package.json` uses conventional discovery; the runtime inventory still verifies its intended resources.
- The validator looks for the installed `@earendil-works/pi-coding-agent` in the package's ancestor directories and in the npm and pnpm global roots. If it is installed elsewhere, append `--pi-root /absolute/path/to/node_modules/@earendil-works/pi-coding-agent`. That path must be an installed package with its executable public entry and dependencies, not an unbuilt source checkout.
- Each resource worker and subprocess has a 30-second limit by default; `--timeout-ms 60000` changes it.

### What the report covers

- Manifest fields that are present, path existence and containment, and wildcard host peers. Omitted resource types do not fail. npm name and version checks apply with `--pack`; a gallery keyword and `type: module` are nonblocking recommendations rather than universal Pi load requirements.
- Actual Pi resource loading, diagnostics, resolved file paths, and public names, compared with the inventory. A factory that throws, hangs, or imports an unavailable API fails the runtime check.
- Parity between string and object settings entries, disabling each provided resource type without changing the others, and wildcard filters that must not expose unintended conventional resources. Absence is valid; unexpected exposure is a different condition.
- Whether Pi loaded the package directory itself as an implicit extension. That root `index.ts` fallback works only for a local string entry, so npm and git installs and `pi config` object entries would load nothing. The check fails and names the fix.
- For provided themes, the complete bundled contract: 51 required and 5 optional tokens, supported properties, color syntax and ranges, and defined acyclic variables. Without themes, this check is `not_applicable`. The authoring check also rejects invalid unused variables and export colors that runtime loading may defer or tolerate, and the reserved names `system`, `dark`, and `light`.
- With `--pack`, a real npm archive: the packed file list, the extraction location, and byte equality of required files. The validator uses `npm pack --ignore-scripts` and never publishes. Run any necessary build yourself before packing.

### Read the result

| Exit code | Meaning |
|---|---|
| `0` | The requested and implemented checks passed |
| `1` | An assertion or runtime check failed |
| `2` | An input or infrastructure error occurred |

Read the `skipped`, `not_applicable`, and `warning` entries too; a recommendation warning does not fail the package. A run without `--runtime` is not a runtime pass, and a run without an inventory cannot establish the intended resource surface.

### Isolation limits

The workers use disposable settings and work directories and suppress unrelated automatic resources. The validator keeps temporary reports and artifacts for inspection. This isolates resource discovery, not filesystem or network access: extensions and explicitly configured setup commands still run code with the process's permissions, and loading a factory alone can run package code. A worker that exceeds its deadline is killed; that is a failed check, not evidence that the extension cleaned up.

## 3. Test tools without a live model

Use this section only when the package registers tools. For an extension with only commands or events, or for a static resource package, record tool testing as `not_applicable` and use the checks in [section 4](#4-exercise-resources-and-lifecycle-through-pi). Do not run the tool runner with the starter's tool names against an unrelated package.

Copy [starter-cases.json](../assets/testing/starter-cases.json), adapt it to the package's actual tools and meaningful input and error cases, and run:

```bash
node "$skill_dir/scripts/test-tools.mjs" "$package_dir" \
  "/absolute/path/to/your-tool-cases.json" \
  --report "$check_dir/tool-tests.json"
```

- The tool runner accepts the same `--pi-root` and `--timeout-ms` options. Its default deadline is 20 seconds per case.
- Save a `--report` file as durable evidence.
- Each case runs independently in a fresh process and workspace, which are removed afterward.
- After reporting its result, each case process emits `session_shutdown`, disposes the session, and must exit on its own. If it is still alive 2 seconds later, an extension left a timer, watcher, socket, or child process active. A passing case then fails with that message, and its other observations stay in the report. Release such handles in `session_shutdown`.

The tool runner uses the actually loaded extension, an in-memory session, and Pi's agent loop with scripted faux model responses. It exercises argument validation, tool hooks, result and error handling, nested execution, and execution events without requesting a provider response. A call that fails schema validation should fail before the tool does any work.

### Complete case format

The top-level JSON is `{ "cases": [...] }` or an array of cases.

| Field | Type and behavior |
|---|---|
| `name` | Required descriptive string |
| `tool` | Required registered tool name |
| `args` | Any JSON value; defaults to `{}` only when absent. Use invalid types to test schema rejection. |
| `files` | Optional object that maps safe workspace-relative paths to UTF-8 fixture contents |
| `setupCommands` | Optional array of `{ "command": "git", "args": ["init", "-q"] }`; the processes run in the workspace without a shell and must exit successfully |
| `flags` | Optional object of registered Pi flag values, using the types the package declares |
| `abortAfterMs` | Optional nonnegative integer; aborts the session this long after the target tool's execution-start event |
| `expect.isError` | Required boolean that asserts the actual tool result's error flag |
| `expect.textIncludes` | Optional string or array of substrings that the concatenated text content must include |
| `expect.textExcludes` | Optional string or array of forbidden substrings |
| `expect.details` | Optional recursive partial match against the structured result details; arrays must match in length and elements, and primitive values must match exactly |
| `expect.maxTextBytes` | Optional UTF-8 byte ceiling for the concatenated model-facing text |
| `expect.maxTextLines` | Optional line ceiling for the same text; empty text has zero lines, and otherwise the count comes from splitting on `\n` |
| `expect.fullOutputPathDetail` | Optional dot path within `details`, such as `fullOutputPath`. Requires an absolute path to a readable regular file inside the isolated test directory. The tool runner sets `TMPDIR` there, so the bundled helper stays inside this boundary. |
| `expect.fullOutputEqualsFile` | Optional workspace-relative fixture filename. Requires the complete-output file to match the fixture's bytes from before execution; use it with `fullOutputPathDetail` |
| `expect.aborted` | Optional boolean that requires an observed aborted execution |

String values support `{{cwd}}` for the actual workspace path and `{{name}}` for its directory basename. These let a test prove that a tool uses the current context instead of its extension directory. Fixtures and expected values are controlled test inputs.

### Test cancellation

`abortAfterMs` schedules cancellation after execution starts, so choose a fixture with enough ongoing work to observe it; a tool that returns immediately can finish before the timer fires. A canceled execution can end without a tool-result message, in which case the report records `isError: null`, not a successful result. That missing result can replace the error-flag assertion only when `expect.aborted: true` and cancellation was actually observed. If a result exists, its error flag must still match.

### Choose cases by implemented behavior

| Behavior | Input or fixture | Assert |
|---|---|---|
| Ordinary success | Representative valid input and the files it needs | `isError: false`, meaningful text, exact domain values in `details`, correct `cwd` |
| Input rejection | Wrong type, missing required value, out-of-range field | `isError: true`; no successful business result or unintended side effect |
| Operational failure | Missing file, non-repository cwd, controlled nonzero subprocess, failed local service | `isError: true`; an actionable diagnostic and no success-shaped result |
| Cancellation | An operation still running when `abortAfterMs` fires | Observed cancellation; no continuing subprocess, late write, or success message |
| Flag or configuration | The default and a changed supported flag | Display or behavior changes as intended; structured values stay valid |
| Oversized result | More than 2000 lines and more than 50 KiB; also one oversized Unicode line | Text is bounded and keeps a meaningful portion (for the single line, assert a known prefix with `textIncludes`); the truncation notice names a readable full-output path; the saved bytes equal the original |
| Repeated use or state | Two calls, or a restored session when the feature is stateful | No duplicated state, wrong cwd, leaked handles, or stale context |

Use only the rows that apply. An immediate in-memory lookup has no running subprocess to cancel, and a small fixed result needs no oversized-output fixture.

- The tool runner can cover the first six rows when they apply.
- Observe filesystem and process effects after cancellation separately. The child process exiting eventually cannot prove that the tool cleaned up a detached process of its own.
- Repeated use and restoration need a live-session check, because ordinary cases deliberately start fresh.

Examples:

- **Git tool:** a success case can use `files: { "marker.txt": "untracked\n" }`, `setupCommands: [{ "command": "git", "args": ["init", "-q"] }]`, and an expected `marker.txt` substring. A failure case omits the Git initialization.
- **Duration parser:** test a supported value with an exact numeric `details` assertion, and an invalid string with `isError: true`.
- **File-output tool:** create a large `expected.txt` fixture with the chosen case generator or the package's fixture setup, pass that filename as the tool argument, and assert:

```json
{
  "isError": false,
  "textIncludes": ["Output truncated.", "Full output:"],
  "maxTextBytes": 53248,
  "maxTextLines": 2003,
  "fullOutputPathDetail": "fullOutputPath",
  "fullOutputEqualsFile": "expected.txt"
}
```

The 52 KiB and 2003-line budgets allow the helper's 50 KiB and 2000-line body plus its short path notice. They are concrete examples, not permission for arbitrary overflow. Choose the actual budget deliberately, and test Unicode so that character counts cannot stand in for byte counts.

### What the tool runner does not test

The tool runner calls `session.agent.prompt`, not `session.prompt`. It does not test user input expansion, `before_agent_start`, `agent_settled`, normal model choice and authentication, commands, terminal rendering, RPC transport, live session replacement, or provider and MCP integration.

- It marks cases that need provider, virtual-model, or MCP registrations as `skipped`, and records unsupported lifecycle and authentication operations instead of accepting inert stubs.
- A factory can start connections before that classification happens, so the faux model is not a network sandbox.

The report status is `pass`, `fail`, or `incomplete`:

| Exit code | Meaning |
|---|---|
| `0` | Every case passed |
| `1` | Failed assertions, load or setup errors, or invalid inputs |
| `2` | At least one case was skipped and none failed |

Missing tool names, load errors, failed fixtures, exceeded deadlines, and unmet assertions all fail. Unsupported host exports or integration features produce an explicit incomplete result. Report target-runtime mismatches and run the separate integration checks; never count a skipped case as a success.

## 4. Exercise resources and lifecycle through Pi

Use the isolated CLI setup in [operations](operations.md). Select the rows for resources and features the package actually provides; the other rows are `not_applicable`.

| Feature | Action | Expected observation |
|---|---|---|
| Fresh startup | Launch `pi -e "$package_dir"` in the isolated environment | No load, flag, or tool conflict; every intended resource is present |
| Direct command | Run its slash command with ordinary, missing, and invalid arguments | Correct result or diagnostic; no unwanted model turn; only documented state changes |
| Prompt | Invoke it with omitted values, quoted spaces, `""`, and extra arguments | Expansion matches the substitution grammar in [resources](resources.md); allow for the documented post-tag difference in empty-argument handling |
| Skill | Invoke `/skill:<name>` and follow a relative supporting reference | Intended body, base directory, and arguments; the reference stays readable in the extracted artifact |
| Theme | Select its exact name in `/settings` | No fallback or diagnostic; inspect text, code, diff, selection, and tool and error backgrounds |
| Reload | Invoke the feature, run `/reload`, invoke it again | One registration, watch, or process; the updated resource; no use of the old context; the reloading handler returns immediately |
| Session state | Change state, then switch, fork, or resume the session as supported | State restored from the correct branch; no cache leaking from the old session |
| Mode guards | Run the feature in each advertised `tui`, `rpc`, `json`, or `print` mode | UI calls only where supported; a valid output protocol and correct `ctx.mode` behavior |
| Filters | Toggle a resource off and on in disposable `pi config` settings | Exactly that selection changes; unused conventional resources never appear |
| Project delta | Exercise the documented `autoload: false` selection changes | The last matching delta wins; untouched personal resources stay unchanged |

Prompt and skill actions normally request a model after expansion. Use a configured test model, or capture the expanded input through a deliberately controlled test integration. A resource-list check does not show that the model ran successfully; do not report it as successful model execution. The bundled grammar gives the expected expansion without external material.

For long-lived handles, record the active watchers and subprocesses before startup, after the first invocation, after reload, and after shutdown. Verify that the feature releases its own handles instead of relying on the test process being killed.

## 5. Check provider and MCP integrations

Apply these checks only when the package includes the feature. [Integrations](integrations.md) has the complete contracts; no other documentation is part of this workflow.

**Provider:** start with a local controlled HTTP endpoint or a dedicated test account for the service.

- Exercise a small streamed success, a server error, malformed data, cancellation mid-stream, and the optional-callback path with no callback supplied.
- Assert the request URL, headers, and body; the order of stream events; the final stop reason; usage and cost values where provided; and correct termination on error and abort.
- Check the exact authentication result shape and its expiry and refresh behavior separately.
- A successful resource load proves registration only, not authentication or streaming.

**MCP:** use a local fixture server that exposes a known tool and a delayed or failing tool.

- Check the connection, namespaced discovery, valid call arguments and results, remote error mapping, in-flight cancellation, disconnect and reconnect, and cleanup on reload and shutdown.
- If the package advertises both extension-wrapped and direct invocation, exercise both.
- A wrapper that calls nested MCP tools must declare `reachesTools` returning the `mcp__<server>` namespace or full tool names. Call it while the fixture server is still connecting, and confirm that the nested call waits instead of failing as an unknown tool.
- Test HTTP and stdio separately only if the package promises both transports.

Keep test-service addresses, credential setup, and fixture launch commands with the generated package. If the feature depends on a service decision the user has not made, ask for that specific value. When a test service or account is unavailable, finish all local checks and report the live integration as unverified; do not invent a success or substitute a load-only check.

## 6. Verify the delivered form, then report

Follow the delivery source:

- **Local:** the checked local directory is the deliverable; no archive or extraction step is needed.
- **npm or a tarball:** use the archive steps below, after running the validator with `--pack`.
- **Git:** repeat the procedure in a clean checkout of the intended ref with production dependencies.

For an archive, read `artifact.packageDir` from the validator report. It is the actual extracted package path; do not guess a tarball filename from a scoped package name.

If the package needs ordinary runtime dependencies, install them in that extracted directory with the chosen package manager. For a normal npm package that needs no installation scripts:

```bash
cd "/absolute/extracted/package"
npm install --omit=dev --ignore-scripts --legacy-peer-deps
```

This command can reach the registry. It deliberately omits development dependencies and host peers. If a native dependency needs installation scripts, use its specific required build or setup command and record that requirement; an installation that ignored scripts does not prove such a dependency works.

Repeat `validate-package.mjs` with `--runtime --expect` against the extracted directory. Then repeat the tool tests if the package has tools, and the applicable CLI checks. The starter, which has only host peers, needs no dependency installation; run the checks directly. When you deliver an artifact, a pass on the source tree does not replace a pass on the artifact.

Check update, pin migration, and removal in a disposable installation only when those operations are part of the delivered behavior. Installation, publication, and service-account changes have real effects of their own, and a local tarball check does not exercise them.

The final package report lists the Pi and Node versions, the commands and inputs, the source and artifact paths, the `pass`, `fail`, `skipped`, and `not_applicable` checks, and concrete remaining limits. Include failures you repaired and their final rerun result when that helps. Never report a missing environment, a static-only check, or an unexecuted manual step as a pass.

## 7. Give the user verification commands

End every package creation or update with verification commands, in both the final response and the package README. Choose them using [section 1](#1-select-the-checks), so that the user can verify this package's intended resources and behavior without adding optional resource types or reading another document. For each command, give its working directory and prerequisites, the expected success and failure observations, and any report path, and say whether you ran it or are providing it for the user to run.

- Use the user's shell and platform; the patterns below use a POSIX shell.
- In the final response, give the actual command for entering the delivered package directory. In the README, use package-relative paths so the instructions survive a move.
- Replace example names with the package's real names.
- A command you call ready to run must not contain `/absolute/path/to/...`, a nonexistent npm script, a temporary agent checkout, or an undisclosed skill-installation path.

### Native Pi CLI check

From the delivered package directory, provide version checks and an isolated launch:

```bash
node --version
pi --version
package_dir="$(pwd -P)"
verification_dir="$(mktemp -d)"
mkdir -p "$verification_dir/agent" "$verification_dir/work"
(
  cd "$verification_dir/work" || exit 1
  PI_CODING_AGENT_DIR="$verification_dir/agent" PI_OFFLINE=1 \
    pi --no-skills --no-prompt-templates --no-themes --no-context-files \
    -e "$package_dir"
)
```

Expected result: Pi starts with the intended package resources and no package load or conflict diagnostic. Explicit package resources still load despite the discovery-suppression flags. The command does not install the package into personal settings, and it isolates configuration, not the extension code's filesystem or network access.

After the shell block, list the exact actions to enter inside Pi, labeled separately as Pi input. A clean startup alone is not a behavioral pass.

- **Command extension:** its actual slash command and arguments, the expected output, `/reload`, and a repeat invocation when reload matters.
- **Prompts, skills, or themes:** only their actual invocation or selection steps.
- **Event-only extension:** the concrete action that triggers the handler, and the observable result.

For example, the unchanged starter's `/acme-info` should display `work` and the temporary workspace path, and the same command should still work after `/reload`. Adapt this example; do not give `/acme-info` for an unrelated package. Prompt, skill, and tool requests that call a live model need configured model access, which an isolated agent directory may lack. Separate those clearly from commands and model-free automated tests.

### Reproducible automated checks

Reuse the package's existing verification commands when they cover the intended checks. When handing off the bundled validators, put the needed files in a durable directory such as `verification/` inside the delivered project, outside automatically discovered resource roots. Keep the scripts' relative imports intact:

```text
verification/
├── scripts/
│   ├── validate-package.mjs
│   ├── test-tools.mjs             # only when tool tests apply
│   └── lib/
│       ├── runtime.mjs
│       └── theme.mjs
├── inventory.json                # adapted to this package
└── tool-cases.json                # only when tool tests apply
```

Copy the validator and its helpers from this skill's `scripts/`, and deliver the inventory and applicable cases you created while authoring. These files are checking utilities, not Pi extension entry points or SDK session code for the package's feature implementation. If the commands are promised to work from an npm artifact, add these files to its `files` allowlist and to the required-file inventory. Do not advertise a command whose scripts or fixtures the delivered artifact excludes.

From the package directory, run the structural and resource check:

```bash
package_dir="$(pwd -P)"
verification_reports="$(mktemp -d)"
node "$package_dir/verification/scripts/validate-package.mjs" "$package_dir" \
  --expect "$package_dir/verification/inventory.json" --runtime \
  --report "$verification_reports/package-check.json"
```

Expected result: exit `0` and a report with `status: "pass"` for the requested checks. Explain any `warning`, `skipped`, or `not_applicable` entries; they do not mean every possible behavior was tested. Give the report location as `$verification_reports/package-check.json`. Add a `--pi-root` argument only when the target installation needs it and you have identified its path.

If the package has tools covered by the tool runner, add this command, using the same shell variables:

```bash
node "$package_dir/verification/scripts/test-tools.mjs" "$package_dir" \
  "$package_dir/verification/tool-cases.json" \
  --report "$verification_reports/tool-tests.json"
```

Expected result: exit `0`, `status: "pass"`, and no failed or skipped cases. Exit `1` reports a failure, and exit `2` reports coverage this runner could not complete. For an extension with only commands or events, or for a static resource package, omit this command and its files.

For npm delivery or a requested tarball, add `--pack` to the validator command and give the applicable rerun on the extracted copy from [section 6](#6-verify-the-delivered-form-then-report). For local-only delivery, omit it. If the package needs dependencies, a build, or a test service, put their exact preparation commands before the checks, and state the network, model, or service requirements without embedding secrets.

Before handoff, confirm that every referenced file exists and that the commands match the delivered resource names, CLI options, and scripts. Run the feasible automated commands from the documented directory. List any interactive or service-dependent steps you did not run as unverified user checks, instead of implying that they already passed.
