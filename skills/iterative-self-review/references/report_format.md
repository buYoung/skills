# Sub-agent Report Format

The sub-agent must emit exactly this YAML. No free prose, no preamble.

## Schema

```yaml
verdict: clean | issues_found
artifact_inspections:
  - artifact: <file path, directory path, symbol, identifier, command, script, or URL>
    status: inspected | missing | access_denied | not_applicable
    method: read | glob | grep | serena | webfetch | none
    claim_checked: "<direct quote or short label of the claim this inspection checked>"
issues:
  - id: i1
    criterion: coverage | factual | consistency | reasoning | constraints | evidence
    severity: blocker | major | minor
    description: <one sentence>
    evidence: "<direct quote from the response or the user's input>"
missing:
  - id: m1
    description: <something the user asked for that the response does not address>
    evidence: "<direct quote from the user's input>"
unverified_assertions:
  - id: u1
    quote: "<direct quote of the assertion from the response>"
    source_of_uncertainty: user_input_ambiguity | unverifiable_fact | minor_default
    affects_direction: true | false
    note: <one sentence on why it cannot be verified with the allowed read-only inspection>
```

## Inspection manifest enforcement

- `artifact_inspections` is required.
- Use `artifact_inspections: []` only when neither the user input nor the current response cites inspectable artifacts.
- Every cited file, directory, symbol, identifier, command, script, or URL must have an inspection record.
- If a cited directory or package is the subject of the response, include the directory manifest inspection and the child files inspected to verify claims about that subject.
- `status: inspected` is allowed only for artifacts actually read or searched during the current review.
- A report with `verdict: clean` is invalid when inspectable artifacts are cited but `artifact_inspections` is empty or incomplete.
- The main agent must re-call the sub-agent when required inspection records are missing; do not treat the report as a clean pass.

## Evidence enforcement

- `issues[*]` and `missing[*]` must include `evidence`.
- `evidence` must be a **direct quote** — paraphrase and summary are forbidden.
- Items without valid evidence are **downgraded** by the main agent:
  - `blocker` → `minor`
  - `major` → auxiliary signal only (not accepted on its own)
  - `minor` → ignored

## `unverified_assertions` three-way classification

When the sub-agent cannot verify an assertion, classify the cause as one of:

### `user_input_ambiguity`
- The user's input is ambiguous; the response committed to one interpretation, but other interpretations are equally reasonable.
- Example: User said "add tests." Response added unit tests only. The input did not specify unit vs. integration.
- Main-agent handling: if `affects_direction=true`, ask the user.

### `unverifiable_fact`
- An external fact that **even read-only inspection cannot resolve**: runtime behavior, private API/secret values, external-system responses, network state, future-tense statements, third-party service behavior.
- Example: Response asserts "Library X v2 supports Y at runtime" with no basis in the input and no way to confirm without executing code.
- **Not eligible** for this bucket: claims about files, symbols, identifiers, scripts, or quoted URLs that live in the working environment. The sub-agent must read those directly; if they contradict the response, file as `issues`; if they match, omit from the report.
- **Read access genuinely failed** (file does not exist at the cited path, permission denied) qualifies as `unverifiable_fact`. Simply being outside the current working directory does **not** qualify — absolute paths are readable; cite the access error as the reason in `note` if and only if a real read attempt failed.
- Main-agent handling: verify directly with tools or rewrite as a hedge. **Never ask the user** — this is the main agent's job. The Step 5.5 routing-completion gate requires every `unverifiable_fact` + `affects_direction=true` item to be marked resolved (verified-and-reflected, or hedged) before any Positive termination trigger can fire.

### `minor_default`
- A reasonable default for something the user did not specify; alternative values would not change the response's direction.
- Example: variable names, log format, sample-code identifiers.
- Main-agent handling: state the assumption, leave as is.

## `affects_direction` semantics

- `true` — if the assertion is wrong, the response's core conclusion or direction changes.
- `false` — even if wrong, the response's overall shape holds.

## Verdict semantics

- `clean` + `issues=[]` + `missing=[]` + complete `artifact_inspections` → candidate for the Clean pass trigger (see `termination_triggers.md`).
- `issues_found` → routing step engages.
- The main agent decides termination independently per `routing_rules.md` and `termination_triggers.md`; the sub-agent reports only — it does not recommend a loop action.
