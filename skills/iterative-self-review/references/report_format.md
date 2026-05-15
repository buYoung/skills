# Sub-agent Report Format

The sub-agent must emit exactly this YAML. No free prose, no preamble.

## Schema

```yaml
verdict: clean | issues_found
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
    note: <one sentence on why it cannot be verified from the two inputs>
final_recommendation: revise | accept
```

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
- An external fact (API behavior, library version, dataset content) that the sub-agent cannot verify from the two inputs alone.
- Example: Response asserts "Library X v2 supports Y" with no basis in the input.
- Main-agent handling: verify directly or rewrite as a hedge. **Never ask the user** — this is the main agent's job.

### `minor_default`
- A reasonable default for something the user did not specify; alternative values would not change the response's direction.
- Example: variable names, log format, sample-code identifiers.
- Main-agent handling: state the assumption, leave as is.

## `affects_direction` semantics

- `true` — if the assertion is wrong, the response's core conclusion or direction changes.
- `false` — even if wrong, the response's overall shape holds.

## Verdict semantics

- `clean` + `issues=[]` + `missing=[]` → candidate for the Clean pass trigger (see `termination_triggers.md`).
- `issues_found` → routing step engages.
- `final_recommendation` is advisory only. The main agent decides independently per its routing rules.
