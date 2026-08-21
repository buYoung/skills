# Authoring a reference or specification

## Required context

Identify the authority for the contract, supported version, audience vocabulary, completeness boundary, and compatibility promises.

## Drafting sequence

1. Define scope and version.
2. Inventory all contract items within scope and mark each item as supplied, verified, or unspecified.
3. Choose one repeated field scheme for comparable items.
4. Define terms and normative language.
5. Populate exact values and constraints from authoritative sources.
6. Add examples for ambiguous or high-risk items.
7. Add exceptions beside the affected contract.
8. Check every cross-reference and identifier.

## Precision rules

- Use "must", "should", and "may" consistently when normative strength matters.
- Distinguish absent, empty, null, defaulted, unsupported, and invalid states.
- Include units in numeric values and names.
- Do not infer defaults or compatibility from examples.
- Mark unknown or implementation-dependent behavior explicitly.
- Do not fill an unspecified transport location, method exclusion, identifier version, serialization rule, retention start, or expiry behavior from convention alone.
- When behavior depends on a state combination, inventory every supplied branch in one decision table. Add unsupplied branches only as explicitly unknown boundaries.

## Avoid

- Narrative sections that bury lookup keys
- Multiple names for the same field or state
- Tables with large prose blocks in every cell
- Examples that contradict the stated contract
