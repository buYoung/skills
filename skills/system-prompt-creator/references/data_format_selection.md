# Data Format Selection Guide

Select a representation for the actual reader and contract. Preserve a user-required format
unless it conflicts with another requirement. Do not claim a universally most accurate format;
use task-specific evidence and explain a practical starting choice briefly.

## Selection Order

1. Honor a required API, parser, storage, or user-facing format.
2. Identify whether the data is input for a model to read, output for code to parse, or a human
   deliverable. These are different decisions.
3. In the absence of a fixed contract or task-specific evidence, use these readability defaults.
4. If format quality needs measurement, prepare comparable cases and follow the approval gate
   in [evaluation.md](evaluation.md) before simulating them.

| Use | Starting choice | Reason and alternatives |
|---|---|---|
| Flat reference fields | Markdown key-value | Visible field names; JSON/YAML also fit |
| Nested reference data | YAML | Readable hierarchy; preserve JSON when integration requires it |
| Rows and columns | Markdown table | Easy scanning; CSV may suit a constrained input budget |
| Programmatic stage output | Existing schema/format, commonly JSON | Parseability and compatibility take priority |
| Human prose output | Markdown or plain text | Match the audience and requested structure |

These are design defaults, not experimentally established winners for every model. Do not
override requested JSON because a reading benchmark preferred YAML. A schema described in a
prompt does not enable API schema constraints, and valid structure is separate from correct
content. See [model_guidance.md](model_guidance.md) when a target is named.

Data serialization is also distinct from prompt-section delimiters. An experiment using XML
for a large dataset does not measure the value of a few tags around instructions or sources.

## Evidence: Flat Data

Source: Improving Agents, [Which Table Format Do LLMs Understand Best?](https://www.improvingagents.com/blog/best-input-data-format-for-llms/)
Published 2025-09-30; checked 2026-09-08. Scope: GPT-4.1-nano; 1,000 synthetic employee records
with eight attributes, 1,000 retrieval questions, 11 formats. Token counts refer to that dataset.

| Format | Reported accuracy | Tokens |
|---|---|---|
| Markdown-KV | 60.7% | 52,104 |
| XML | 56.0% | 76,114 |
| INI | 55.7% | 48,100 |
| YAML | 54.7% | 55,395 |
| HTML | 53.6% | 75,204 |
| JSON | 52.3% | 66,396 |
| Markdown-Table | 51.9% | 25,140 |
| Natural-Language | 49.6% | 43,411 |
| JSONL | 45.0% | 54,407 |
| CSV | 44.3% | 19,524 |
| Pipe-Delimited | 41.1% | 43,098 |

The source reports no TOML result; the previously included TOML numbers were unsupported and
have been removed. Confidence intervals are available in the source. This single-model,
large-context retrieval experiment does not establish a universal format ranking.

## Evidence: Nested Data

Source: Improving Agents, [Which Nested Data Format Do LLMs Understand Best?](https://www.improvingagents.com/blog/best-nested-data-format/)
Published 2025-10-14; checked 2026-09-08. Scope: synthetic Terraform-like configurations with
six to seven nesting levels; 1,000 retrieval questions per model/format; substring-based grading.
Data volumes were calibrated per model to stress performance, so columns are not a controlled
cross-model comparison.

| Format | GPT-5 Nano | Llama 3.2 3B Instruct | Gemini 2.5 Flash Lite |
|---|---|---|---|
| YAML | 62.1% | 49.1% | 51.9% |
| Markdown | 54.3% | 48.0% | 48.2% |
| JSON | 50.3% | 52.7% | 43.1% |
| XML | 44.4% | 50.7% | 33.8% |

YAML had the highest reported score on two models. JSON's lead on Llama was not statistically
significant according to the source. These results concern reading nested data in that setting,
not generation reliability, all task types, or untested models.

## Applying Evidence

Keep the source, tested model, task/data scale, grading method when known, and checked date
alongside any reported result. Recheck the original source before updating figures; remove or
mark unsupported claims instead of filling gaps. Treat explanations of why a format worked as
hypotheses unless the experiment established them.

When recommending a format for a new task, distinguish the selected default from the scoped
experimental observation. Evaluate semantic answer accuracy as well as token use or parsing
when those dimensions matter to the user's request. A current-agent simulation cannot establish
which format performs best on the named target provider.
