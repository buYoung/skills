# Source grounding

Use this reference when the document makes factual claims that depend on supplied material, a codebase, data, or external sources.

## Evidence hierarchy

1. User-provided authoritative material
2. The current target document and its cited sources
3. Repository implementation and history for repository facts
4. Primary external documentation or standards when external verification is warranted
5. Explicitly labeled inference

Do not promote inference into fact. If sources disagree, surface the conflict and identify which source controls the current document.

## Claim handling

- Separate observed facts from interpretation and recommendation.
- Cite claims close to the supporting evidence when citations are requested or required.
- Preserve exact quotations and logs.
- State the verification date when freshness matters.
- Use an explicit missing-input marker instead of inventing a decision.
- When a source omits a unit, denominator, population, or time basis, preserve that ambiguity everywhere the claim appears. Any calculation that supplies the missing dimension must be conditional at first use; a later assumptions section does not repair an earlier factual overstatement.

## Research scope

Research only what affects the document's correctness. Avoid generic best-practice material that is disconnected from the actual audience, system, or decision. For technical questions, prefer primary specifications and official documentation.

## Final check

Confirm that each material factual claim is supported, clearly inferred, or explicitly unresolved. State any source or environment that could not be checked.
