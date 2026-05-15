# Verification Criteria (six axes for the sub-agent)

The sub-agent reviews the main response only along these six axes. Each axis defines what it *catches* and what it *does not catch* — to stop the verifier's subjective preferences from expanding scope.

## 1. Coverage (does the response satisfy the request?)
- **Catch**: Items explicitly required by the user's input that the response omits.
- **Do not catch**: "Nice-to-have" items the user did not request — that is scope creep.

## 2. Factual correctness
- **Catch**: Assertions in the response that contradict the user's input or widely known facts.
- **Do not catch**: Domain claims the sub-agent cannot directly verify — those go under `unverified_assertions` instead.

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

## Deliberately excluded

### "Practical sufficiency"
- **Why excluded**: If the verifier imposes its own sense of "a more useful answer," scope creep is guaranteed. If a need is not present in the user's explicit input, it is not an issue.
- If anyone wants to reintroduce this axis, they must first define which user-input cue triggers it. Without that cue, verifier subjectivity drives an infinite loop.

### "Style / tone improvements"
- **Why excluded**: Not measurable. If the user explicitly requested a tone, that is caught by axis 1 (Coverage).

### "Performance / efficiency"
- **Why excluded**: For code responses, a separate code-review skill handles this. Self-review targets answer completeness, not optimization.
