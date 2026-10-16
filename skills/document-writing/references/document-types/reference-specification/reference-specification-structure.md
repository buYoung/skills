# Reference or specification structure

## Default structure

1. Title, scope, and applicability, version, or effective date
2. Quick-reference contract or lookup sections
3. Terminology needed to interpret the contract
4. Examples and counterexamples
5. Errors, exceptions, and limits
6. Compatibility or change history
7. Authoritative sources

## Lookup design

Organize by the keys readers already know: endpoint, command, field, option, state, concept, or error code. Use tables only when every row shares meaningful columns.

When the reader needs an implementation-time lookup surface, make every user-requested contract item discoverable from a quick-reference table immediately after the title, scope, and applicability, so a reader who stops at the table already knows which version and cases it covers. For a large contract, use that table as an index linking to canonical detail sections instead of duplicating every rule in one oversized table. Put terminology before the table only when it cannot be interpreted without it.

For each contract item, include only applicable fields such as:

- Name
- Type or category
- Required or optional status
- Allowed values
- Default
- Meaning
- Constraints
- Example
- Failure behavior

## Navigation

Use predictable headings and stable vocabulary. Do not hide normative exceptions in prose far from the item they modify.
