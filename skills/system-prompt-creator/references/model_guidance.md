# Model and Provider Guidance

Read this reference only when the request names a model/provider or requires a provider-specific
capability. Read the common procedure and the applicable section, not every provider's docs.
The general prompt structure remains model-neutral.

## Adaptation Procedure

1. Recover the exact requested model, provider, interface, and required capabilities from the
   conversation. Do not replace a named model with a newer or preferred one.
2. Check current official documentation for that target before specifying model-specific
   prompt conventions, message roles, API fields, tools, or output settings.
3. Verify only what is needed: system-instruction placement, runtime message/input placement,
   supported structured-output/schema features, tool interfaces, and required controls.
4. Keep the user-facing task and output contract intact. Explain any necessary adaptation and
   cite the exact official page, target scope, and date checked.
5. If official guidance cannot be accessed or does not establish support, identify the
   unverified detail. A model-neutral draft may still be delivered when it remains useful;
   do not label an unknown integration compatible or invent exact API settings.

Record applied adaptations as:

| Target/interface | Required capability | Official source and checked date | Applied change | Unverified limit |
|---|---|---|---|---|
| Exact requested target | What the task needs | Page supporting the claim | Prompt placement or setting | What was not established |

Do not prescribe universal sampling values or claim deterministic output from a temperature
setting. Record actual settings only when available and supported. A documentation check is
not a runtime test.

## OpenAI

Official sources checked 2026-09-08:

- [Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs):
  scope is supported OpenAI models and schemas. Responses uses `text.format`; Chat Completions
  uses `response_format`. Confirm support for the exact model/API before giving configuration.
  JSON mode addresses JSON validity; Structured Outputs adds schema adherence. Prompt-only
  schema text enables neither feature. Even schema-conforming output may contain wrong facts
  or labels. Handle refusals and incomplete responses separately from a successful parsed result.
- [Responses API reference](https://developers.openai.com/api/reference/cli/resources/responses/methods/create):
  `instructions` carries system/developer instructions and `input` carries runtime input.
  With `previous_response_id`, previous instructions are not automatically carried forward;
  account for that when the requested integration relies on persistent rules.

Use these as entry points, not a compatibility list for every OpenAI model. Keep API setup in
the application note rather than implying schema text inside the prompt configures the client.
Grade semantic correctness independently of schema adherence.

## Anthropic Claude

Official source checked 2026-09-08:
[Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices).
Its general guidance recommends descriptive XML tags to separate instructions, context,
examples, and inputs in complex prompts. The Messages example places fixed instructions in
the top-level `system` field and runtime requests in `messages`.

Use tags when helpful to the requested Claude prompt; this is sectioning guidance, not a
universal serialization ranking. Verify the exact model's current instructions for any
thinking controls, structured outputs, or other required features rather than transferring
OpenAI parameter names or applying a model-specific recommendation to every Claude model.

## Other Providers or Local Models

Find the requested provider's official prompt/API documentation or the exact local model's
official model card and chat-template documentation. Check system-role support and input
serialization before promising direct applicability. Reuse the general requirements and
evaluation workflow; do not extrapolate one provider's parameters or benchmark scores to another.

## Evaluation Boundary

Current-agent simulation can provide observed examples under this session's conditions. It
does not verify the target API's role hierarchy, target-model performance, schema constraints,
or host orchestration. Preserve that limit in both application guidance and result records;
follow [evaluation.md](evaluation.md) for approval and comparison.
