# Data Format Selection Guide

Criteria for selecting the format of data placed inside a system prompt.

## How to Read the Numbers Below

The accuracy figures in this guide come from two **small-model retrieval benchmarks** (see
[Source](#source)). They are useful as a starting prior, **not** as a universal law:

- The flat-data numbers were measured on a **single** model (GPT-4.1-nano).
- The nested-data ranking **flips across models** (e.g. JSON beats YAML on Llama 3.2 3B).
- Both tested only simple field-retrieval over large, single-domain datasets.

> The optimal format is model- and task-dependent. Treat the recommendation as a **default to
> confirm with your own eval** (see [evaluation.md](evaluation.md)), not as a fixed truth.

> **If a user demands "the single most accurate / best format," do not name one.** No format is
> universally or objectively most accurate — the ranking flips across models (the nested-data
> table below shows JSON beating YAML on one model). The correct response is to pick the
> **shape-based default** (Markdown-KV for flat, YAML for nested, Markdown-Table for tabular), say
> plainly that it is a *starting default that depends on the target model and task*, and recommend
> confirming it with the user's own eval. Never cite a benchmark number as proof that one format is
> "the most accurate" / "the highest-accuracy" / "the top-ranked" format in general — a scoped
> percentage does not license a universal superlative.
>
> - ✅ "For flat reference data I'll default to Markdown-KV — a solid starting point, but the best
>   format is model- and task-dependent, so confirm it against your own eval."
> - ❌ "Markdown-KV is the most accurate format (60.7%), so use it."

**Practical default**: in the absence of a task-specific eval, use **Markdown-KV for flat data**
and **YAML for nested data**. These rank at or near the top across the tested models and remain
token-efficient. This default is also a common practitioner heuristic — Markdown-KV / YAML tend
to be recognized more reliably than tag-heavy or delimiter-only formats on current models —
though that is hands-on experience, not something the benchmarks above establish.

> These rankings concern **data embedded for the model to read**. They say nothing about XML
> tags used to *delimit prompt sections* (`<task>`, `<examples>`, `<user_input>`) — a standard,
> low-token practice for Claude-family models that remains recommended regardless of the
> tag-heavy data-format costs in the tables below.

## Format Accuracy: Flat Data (single model — GPT-4.1-nano)

LLM accuracy by format for 1D (flat) key-value retrieval over a large tabular dataset:

| Rank | Format | Accuracy | 95% CI | Tokens |
|------|--------|----------|--------|--------|
| 1 | Markdown-KV | 60.7% | 57.6% – 63.7% | 52,104 |
| 2 | XML | 56.0% | 52.9% – 59.0% | 76,114 |
| 3 | INI | 55.7% | 52.6% – 58.8% | 48,100 |
| 4 | YAML | 54.7% | 51.6% – 57.8% | 55,395 |
| 5 | HTML | 53.6% | 50.5% – 56.7% | 75,204 |
| 6 | JSON | 52.3% | 49.2% – 55.4% | 66,396 |
| 7 | Markdown-Table | 51.9% | 48.8% – 55.0% | 25,140 |
| 8 | Natural-Language | 49.6% | 46.5% – 52.7% | 43,411 |
| 9 | TOML | 47.5% | 44.4% – 50.6% | 21,518 |
| 10 | JSONL | 45.0% | 41.9% – 48.1% | 54,407 |
| 11 | CSV | 44.3% | 41.2% – 47.4% | 19,524 |
| 12 | Pipe-Delimited | 41.1% | 38.1% – 44.2% | 43,098 |

### Key Insights: Flat Data

- **Highest score in this single-model test**: Markdown-KV (60.7%) — explicit `key: value`
  structure is easy to attend to. This is one model's retrieval result, not a general ranking of
  "the most accurate format."
- **Best token efficiency**: CSV (19,524 tokens), but accuracy is low (44.3%).
- **Balance**: Markdown-KV (60.7%, 52,104 tokens) or INI (55.7%, 48,100 tokens).
- **Tag-heavy cost**: XML/HTML consume 75,000+ tokens for marginal accuracy benefit.
- **Caveat**: single-model result — re-confirm before treating any one format as best for your
  model.

## Format Accuracy: Nested Data (ranking flips across models)

LLM accuracy by format for nested-structure retrieval, measured on **three** small models. Note
that the best format is **not** the same for every model:

| Format | GPT-5 Nano | Llama 3.2 3B Instruct | Gemini 2.5 Flash Lite |
|--------|-----------|-----------------------|-----------------------|
| YAML     | **62.1%** | 49.1% | **51.9%** |
| Markdown | 54.3% | 48.0% | 48.2% |
| JSON     | 50.3% | **52.7%** | 43.1% |
| XML      | 44.4% | 50.7% | 33.8% |

(Bold = best format for that model.)

### Key Insights: Nested Data

- **YAML scored highest on 2 of the 3 tested models** (GPT-5 Nano, Gemini 2.5 Flash Lite) and is a
  reasonable default for nested data — on those models, not as a universal ranking.
- **But JSON wins on Llama 3.2 3B** — so "YAML is always best / avoid JSON" is **false** as a
  universal claim. The right format depends on the target model.
- **Markdown** is consistently mid-pack and token-cheap; a fine readability-leaning choice.
- **Verify on your actual target model** before locking a format in.

## Format Selection Decision Matrix

Defaults by data shape — confirm against your model with an eval:

```yaml
- data_structure: Flat key-value
  default: Markdown-KV
  alternative: INI / YAML
  note: Single-model evidence; CSV/Pipe-Delimited rank lowest on accuracy
- data_structure: Nested/hierarchical
  default: YAML
  alternative: JSON (notably stronger on some models, e.g. Llama)
  note: Best format flips across models — verify
- data_structure: Tabular (rows × columns)
  default: Markdown-Table
  alternative: Markdown-KV / YAML
  note: CSV/Pipe-Delimited rank lowest on accuracy; Markdown-Table buys materially higher
    accuracy for ~29% more tokens than CSV
- data_structure: API integration required
  default: JSON
  alternative: YAML
  note: Prefer API-level Structured Outputs / strict schema over prompt-only JSON requests
- data_structure: Legacy system integration
  default: XML
  alternative: JSON
  note: "-"
```

## Use Case Recommendations

```yaml
- use_case: Reference data in a system prompt
  format: Markdown-KV (flat) or YAML (nested)
  rationale: High accuracy + reasonable token efficiency on tested models
- use_case: Intermediate data transfer (multi-prompt) read by the NEXT PROMPT as in-context text
  format: YAML
  rationale: Top-ranked for nested-data reading on most tested models; verify per model. If an
    orchestrator parses stage outputs programmatically, prefer JSON + Structured Outputs
    instead — see multi_prompt_architecture.md (Inter-Prompt Data Contract)
- use_case: API integration output
  format: JSON (with Structured Outputs / strict function calling)
  rationale: Reliable programmatic parsing
- use_case: Large-volume data input (token limit)
  format: Markdown-Table or CSV
  rationale: Token efficiency over accuracy
- use_case: Final output for human reading
  format: Markdown or Plain Text
  rationale: Readability
- use_case: Schema definition
  format: JSON Schema
  rationale: Standardized structure definition
```

## Source

Accuracy data is from two benchmarks by Improving Agents. Both test **small models only** and
**simple field-retrieval** tasks, and both explicitly caution that other models may prefer other
formats:

- Flat data — single model (GPT-4.1-nano), 1,000 synthetic tabular records:
  <https://www.improvingagents.com/blog/best-input-data-format-for-llms/>
- Nested data — three models (GPT-5 Nano, Llama 3.2 3B Instruct, Gemini 2.5 Flash Lite),
  Terraform configs: <https://www.improvingagents.com/blog/best-nested-data-format/>

Larger/newer models (Claude, GPT-4-class, Gemini Pro, etc.) were not tested. Always confirm the
format choice for your own model and task with an eval — see [evaluation.md](evaluation.md).
