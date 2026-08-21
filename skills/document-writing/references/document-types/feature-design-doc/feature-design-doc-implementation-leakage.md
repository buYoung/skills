# FDD implementation leakage

An FDD defines design decisions, not implementation actions. Remove or relocate details that tell a coder what files or tasks to execute without changing the reader's understanding of the product design.

## Leakage indicators

- File, module, class, or function names used as implementation instructions
- PR, ticket, or commit sequencing
- Step-by-step engineering actions
- Code-agent commands
- Acceptance checklists that function as a test plan
- Migration or rollout task ordering
- Implementation-only state machines
- Release phasing that does not change the product surface

## Decision test

Ask whether removing the detail would still leave the product behavior and rationale understandable.

- If yes, remove it from the FDD.
- If no because the detail is a public or material design contract, keep only the contract-level detail.
- If the detail helps navigation after implementation, place it in the non-normative Appendix Code Map and pair it with verified-against metadata.

## Allowed design detail

Implementation-adjacent detail may remain when it is itself part of the externally meaningful contract, platform constraint, interoperability requirement, or security boundary. Explain why it is design-significant.

## Normalization output

When removing leakage during normalization, report what moved and the downstream artifact where it belongs. Do not silently discard potentially useful implementation information.
