# Tokens

## Contract

Tokens are the named interface between foundations and consuming components. They must express the approved direction and preserve semantic meaning across contexts. The supplied brief does not provide token values, names, themes, or deprecation policy, so no numeric or literal token values are established here.

## Required token layers

1. **Source tokens:** raw values, once approved, for the underlying visual properties.
2. **Semantic aliases:** roles such as primary action, supporting text, focus indication, surface, border, and status, once their source values are approved.
3. **Component bindings:** component-facing references to semantic roles; components should not bind directly to raw values.

## Unresolved decisions

The system still needs an authoritative decision for token naming, values, supported modes, contrast targets, typography scale, spacing scale, sizing, and motion durations. The owner must record those decisions here before implementation treats tokens as stable. Until then, consuming documents should use semantic roles in prose rather than inventing token identifiers.

## Verification

Review token mappings in the simple settings screen and dense data table. Confirm that changing a semantic role does not introduce competing emphasis, reduce readable hierarchy, or remove visible focus and state distinction.

