# Verification Criteria (six axes for the sub-agent)

The sub-agent reviews the main response only along these six axes. Each axis defines what it *catches* and what it *does not catch* — to stop the verifier's subjective preferences from expanding scope.

## 1. Coverage (does the response satisfy the request?)
- **Catch**: Items explicitly required by the user's input that the response omits.
- **Do not catch**: "Nice-to-have" items the user did not request — that is scope creep.

## 2. Factual correctness
- **Catch**: Assertions in the response that contradict the user's input, widely known facts, **or what the sub-agent can confirm with read-only tools** (Read, Glob, Grep; WebFetch only for URLs the response itself cites).
- **Tool-use expectation**: For any claim about a file, symbol, identifier, command, or cited URL, the sub-agent must actually inspect the artifact before classifying. Failure to inspect when inspection is possible is a process error.
- **Reporting**: Inspection-manifest enforcement (every inspected/attempted artifact appears in `artifact_inspections`; clean verdict invalid without complete manifest) is defined canonically in `report_format.md`.
- **Do not catch as `issues`**: Claims that even read-only inspection cannot resolve — runtime behavior, private API responses, secret values, network/external-system state, future-tense statements. These go under `unverified_assertions`.
- **Wrapper vs. underlying reality**: Reading a cited wrapper (doc/index/README) does not satisfy verification of the claims the wrapper makes about its subject. Full rules — including enumerated-assertion handling and absolute-path scope — live canonically in `sub_agent_prompt_template.md`.

## 3. Internal consistency
- **Catch**: Assertions, numbers, or conclusions within the response that contradict each other.
- **Do not catch**: Re-statements of the same fact in different wording. Surface vocabulary differences are not contradictions.

## 4. Reasoning validity
- **Catch**: Missing steps, faulty generalizations, or hidden premises between premises and conclusions.
- **Do not catch**: A preference for a "more elegant" reasoning style. Style preferences are not issues.

## 5. Constraints and edge cases
- **Catch**: Boundary conditions implied by the user's input or by the response itself that go unhandled.
- **Do not catch**: Edge cases the verifier invents without any cue in the user's input. Inventing edge cases is scope creep.

## 6. Evidence for assertions
- **Catch**: The response states something as fact without support in either the response or the user's input.
- Main-agent handling: hedge the wording or verify directly. **Note**: user-input ambiguity is a separate channel (`user_input_ambiguity`), not this axis.

---

## Verification duty for cited artifacts

When the response specifically names file paths, symbol names, identifiers, commands/scripts, or quoted URLs, the sub-agent must inspect them with read-only tools before classifying. The detailed rules (wrapper-vs-reality, enumerated-assertion handling, absolute-path scope, `unverifiable_fact` boundary) are defined canonically in `sub_agent_prompt_template.md` — the sub-agent reads that prompt and executes against it.

After inspection: matches reality → no report item; contradicts reality → `issues`; real but behavior unconfirmable without runtime/external context → `unverified_assertions` with `unverifiable_fact`.

### Allowed dependency tracing (claim-linkage scope)

Following imports, callers/callees, type definitions, or files referenced from a cited file is allowed and encouraged **as far as the trace remains tied to a specific claim in the response**. Scope is bounded by claim-linkage, not by file count.

### Scope-creep boundary

Stop tracing the moment "which claim in the response does this verify?" has no clear answer. The sub-agent must not:

- Surface new requirements the response does not address.
- Suggest refactors or improvements outside the response's scope.
- Hunt for defects in regions the response does not touch.

---

## Deliberately excluded

### "Practical sufficiency"
- **Why excluded**: If the verifier imposes its own sense of "a more useful answer," scope creep is guaranteed. If a need is not present in the user's explicit input, it is not an issue.
- If anyone wants to reintroduce this axis, they must first define which user-input cue triggers it. Without that cue, verifier subjectivity drives an infinite loop.

### "Style / tone improvements"
- **Why excluded**: Not measurable. If the user explicitly requested a tone, that is caught by axis 1 (Coverage).

### "Performance / efficiency"
- **Why excluded**: For code responses, a separate code-review skill handles this. Self-review targets answer completeness, not optimization.
