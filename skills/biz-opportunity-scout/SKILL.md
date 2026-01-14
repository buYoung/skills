---
name: biz-opportunity-scout
description: Identify and validate profitable business opportunities by analyzing market size (TAM/SAM/SOM), unit economics, competitive landscape, and PMF indicators. Generates comprehensive HTML reports with opportunity scorecards.
---

# Biz Opportunity Scout

Capability to identify, analyze, and validate business opportunities through quantitative frameworks.

## Analysis Scope

| Scope Type | Description |
|------------|-------------|
| Idea Validation | Early-stage concept viability assessment |
| Idea Pivot/Extension | Existing idea modification or expansion |
| Business Expansion | Established business growth opportunity |

## Core Analysis Frameworks

| Framework | Reference | Purpose |
|-----------|-----------|---------|
| Market Sizing | [market_sizing.md](references/market_sizing.md) | TAM/SAM/SOM calculation methodology |
| Unit Economics | [unit_economics.md](references/unit_economics.md) | LTV, CAC, Contribution Margin, Payback Period |
| Competitive Analysis | [competitive_analysis.md](references/competitive_analysis.md) | Market positioning and competitor mapping |
| PMF Indicators | [pmf_indicators.md](references/pmf_indicators.md) | Product-Market Fit measurement criteria |

## Data Collection

| Method | Description |
|--------|-------------|
| External Research | Web search, industry reports, public data sources |
| User Input | Business-specific assumptions and known metrics |

## Output Specification

| Component | Description |
|-----------|-------------|
| Numeric Report | Quantitative analysis with calculated metrics |
| Investment Pitch | Key figures formatted for investor presentation |
| Go/No-Go Decision | Binary recommendation with supporting rationale |
| Opportunity Scorecard | Composite score/grade across all dimensions |

See [report_template.md](references/report_template.md) for HTML output structure and file naming conventions.

## Report File Naming

| Option | Pattern | Example |
|--------|---------|---------|
| Default | `report/scout-report_[service-name]_[date].html` | `report/scout-report_coffee-subscription_2024-01-14.html` |
| Custom | User-specified folder and filename | User input |
