# Unit Economics

Core financial metrics for evaluating business viability at the unit level.

## Key Metrics

### Customer Lifetime Value (LTV)

| Formula | Description |
|---------|-------------|
| `LTV = ARPU × Gross Margin × Customer Lifespan` | Revenue-based calculation |
| `LTV = (ARPU × Gross Margin) / Churn Rate` | Churn-based calculation |

| Component | Definition |
|-----------|------------|
| ARPU | Average Revenue Per User (monthly/annual) |
| Gross Margin | (Revenue - COGS) / Revenue |
| Customer Lifespan | Average months/years customer remains active |
| Churn Rate | % of customers lost per period |

### Customer Acquisition Cost (CAC)

| Formula | Description |
|---------|-------------|
| `CAC = Total Sales & Marketing Spend / New Customers Acquired` | Blended CAC |
| `CAC = Channel Spend / Channel Conversions` | Channel-specific CAC |

| Cost Component | Examples |
|----------------|----------|
| Marketing | Ads, content, events, PR |
| Sales | Salaries, commissions, tools |
| Onboarding | Implementation, training |

### LTV:CAC Ratio

| Ratio | Interpretation |
|-------|----------------|
| < 1:1 | Losing money on each customer |
| 1:1 - 3:1 | Unsustainable, needs optimization |
| 3:1 - 5:1 | Healthy, sustainable growth |
| > 5:1 | Under-investing in growth |

### Contribution Margin

| Formula | Description |
|---------|-------------|
| `CM = Revenue - Variable Costs` | Absolute contribution |
| `CM % = (Revenue - Variable Costs) / Revenue × 100` | Percentage margin |

| Variable Cost Types | Examples |
|---------------------|----------|
| Direct Materials | COGS, raw materials |
| Direct Labor | Per-unit production labor |
| Transaction Costs | Payment processing, shipping |

### Payback Period

| Formula | Description |
|---------|-------------|
| `Payback Period = CAC / (ARPU × Gross Margin)` | Months to recover CAC |

| Payback | Interpretation |
|---------|----------------|
| < 6 months | Excellent, rapid capital efficiency |
| 6-12 months | Good, typical for SaaS |
| 12-18 months | Acceptable, monitor closely |
| > 18 months | High risk, requires strong retention |

## Benchmark Thresholds

| Metric | Poor | Acceptable | Good | Excellent |
|--------|------|------------|------|-----------|
| LTV:CAC | < 1 | 1-3 | 3-5 | > 5 |
| Payback Period | > 18mo | 12-18mo | 6-12mo | < 6mo |
| Gross Margin | < 40% | 40-60% | 60-80% | > 80% |
| CM % | < 20% | 20-40% | 40-60% | > 60% |

## Data Collection via Web Search

Use web search to benchmark unit economics:

| Search Query Examples | Target Data |
|-----------------------|-------------|
| "[industry] average CAC benchmark" | CAC baseline |
| "[industry] customer lifetime value" | LTV comparison |
| "[industry] SaaS gross margin benchmark" | Margin targets |
| "[business model] churn rate average" | Retention benchmarks |

## Output Format

```
LTV: $X,XXX
CAC: $XXX
LTV:CAC Ratio: X.X:1
Contribution Margin: XX%
Payback Period: X months
```
