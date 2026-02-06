# Data Format Selection Guide

Provides criteria for selecting data formats within system prompts and accuracy comparison data for each format.

## Table of Contents

- [Format Accuracy: Flat Data](#format-accuracy-flat-data)
- [Format Accuracy: Nested Data](#format-accuracy-nested-data)
- [Format Selection Decision Matrix](#format-selection-decision-matrix)
- [Use Case Recommendations](#use-case-recommendations)

## Format Accuracy: Flat Data

LLM accuracy comparison by format for 1D (flat) key-value data:

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

- **Highest Accuracy**: Markdown-KV (60.7%) — The explicit structure of key-value pairs is effective for LLM attention
- **Best Token Efficiency**: CSV (19,524 tokens) — However, accuracy is low at 44.3%
- **Accuracy-Efficiency Balance**: INI (55.7%, 48,100 tokens) or Markdown-KV (60.7%, 52,104 tokens)
- **High Token Cost of XML/HTML**: Tag-based formats consume 75,000+ tokens with marginal accuracy benefits
- **Limitations of Natural Language**: Unstructured format ranks in the lower-middle tier at 49.6% — structured formats are recommended for data delivery

## Format Accuracy: Nested Data

LLM accuracy comparison by format for nested structure data:

| Rank | Format | Accuracy | 95% CI | Tokens | Data Size |
|------|--------|----------|--------|--------|-----------|
| 1 | YAML | 62.1% | 59.1% – 65.1% | 42,477 | 142.6 KB |
| 2 | Markdown | 54.3% | 51.2% – 57.4% | 38,357 | 114.6 KB |
| 3 | JSON | 50.3% | 47.2% – 53.4% | 57,933 | 201.6 KB |
| 4 | XML | 44.4% | 41.3% – 47.5% | 68,804 | 241.1 KB |

### Key Insights: Nested Data

- **YAML Best Performance**: 62.1% accuracy + 42,477 tokens — Best in both accuracy and efficiency for nested structures
- **Markdown Efficiency**: Least token consumption at 38,357 tokens, with 54.3% accuracy
- **JSON Limitations**: 50.3% accuracy at 57,933 tokens — Inefficient except for programming integration
- **XML Inefficiency**: Lowest accuracy (44.4%) + highest tokens (68,804) — Not recommended for nested data

## Format Selection Decision Matrix

Guide for format selection based on data characteristics:

```yaml
- data_structure: Flat key-value
  primary: Markdown-KV
  alternative: INI
  avoid: CSV, Pipe-Delimited
- data_structure: Nested/hierarchical
  primary: YAML
  alternative: Markdown
  avoid: XML
- data_structure: Tabular (rows × columns)
  primary: Markdown-Table
  alternative: YAML
  avoid: CSV (Low accuracy)
- data_structure: List/array
  primary: YAML
  alternative: JSON
  avoid: Natural-Language
- data_structure: API integration required
  primary: JSON
  alternative: YAML
  avoid: Markdown
- data_structure: Legacy system integration
  primary: XML
  alternative: JSON
  avoid: "-"
```

## Use Case Recommendations

Format selection guide for system prompt design:

```yaml
- use_case: Reference data in system prompt
  format: Markdown-KV or YAML
  rationale: High accuracy + reasonable token efficiency
- use_case: Intermediate data transfer (multi-prompt)
  format: YAML
  rationale: Highest accuracy for nested data (62.1%)
- use_case: API integration output
  format: JSON
  rationale: Compatibility for programmatic parsing
- use_case: Large-volume data input (token limit)
  format: Markdown-Table or CSV
  rationale: Token efficiency as top priority
- use_case: Final output for human reading
  format: Markdown or Plain Text
  rationale: Readability
- use_case: Schema definition
  format: JSON Schema
  rationale: Standardized structure definition
```

### Considerations for Format Selection

```yaml
- factor: Accuracy Priority
  high: YAML (nested), Markdown-KV (flat)
  low: CSV, Pipe-Delimited
- factor: Token Efficiency Priority
  high: CSV, Markdown-Table
  low: XML, HTML
- factor: Accuracy-Efficiency Balance
  high: YAML, INI, Markdown-KV
  low: JSON (Inefficient), XML (Inefficient)
- factor: Programmatic Compatibility
  high: JSON, YAML
  low: Markdown-KV, INI
- factor: LLM Training Data Friendly
  high: Markdown, YAML, JSON
  low: TOML, INI, Pipe-Delimited
```

## Source

The accuracy comparison data and selection criteria in this guide are based on the analysis from [Improving Agents - The Best Data Formats for LLMs](https://www.improvingagents.com).
