# PMF Indicators

Product-Market Fit measurement criteria and validation signals.

## PMF Definition

Product-Market Fit exists when a product satisfies strong market demand, evidenced by organic growth, high retention, and customer advocacy.

## Quantitative Indicators

### Retention Metrics

| Metric | Formula | PMF Threshold |
|--------|---------|---------------|
| Day 1 Retention | Users active Day 1 / Total signups | > 40% |
| Day 7 Retention | Users active Day 7 / Total signups | > 20% |
| Day 30 Retention | Users active Day 30 / Total signups | > 10% |
| Monthly Churn | Customers lost / Starting customers | < 5% (B2B), < 7% (B2C) |

### Engagement Metrics

| Metric | Formula | PMF Signal |
|--------|---------|------------|
| DAU/MAU | Daily Active / Monthly Active | > 20% (good), > 50% (excellent) |
| Session Frequency | Sessions per user per week | Increasing trend |
| Time in Product | Average session duration | Consistent or growing |
| Feature Adoption | % users using core features | > 60% |

### Growth Metrics

| Metric | Formula | PMF Signal |
|--------|---------|------------|
| Organic Growth % | Non-paid signups / Total signups | > 50% |
| Viral Coefficient | Invites sent × Conversion rate | > 1.0 |
| NPS | Promoters % - Detractors % | > 40 |
| Referral Rate | Referred customers / Total customers | > 25% |

### Revenue Metrics

| Metric | Formula | PMF Signal |
|--------|---------|------------|
| Revenue Retention | Current MRR from cohort / Original MRR | > 100% (expansion) |
| Expansion Revenue | Upsell + Cross-sell revenue | Positive trend |
| Willingness to Pay | Customers accepting price increase | Low churn on increase |

## Sean Ellis Test

| Survey Question | PMF Threshold |
|-----------------|---------------|
| "How would you feel if you could no longer use [product]?" | |
| Very disappointed | > 40% |
| Somewhat disappointed | Combined > 70% |
| Not disappointed | < 30% |

## PMF Stage Assessment

| Stage | Characteristics |
|-------|-----------------|
| Pre-PMF | High churn, low organic growth, inconsistent revenue |
| Approaching PMF | Improving retention, emerging patterns, some organic growth |
| PMF Achieved | Strong retention, organic growth > paid, clear ICP |
| Post-PMF Scale | Predictable unit economics, repeatable acquisition |

## Output Format

```
PMF Stage: Pre-PMF / Approaching / Achieved / Scale
Sean Ellis Score: XX% very disappointed
Retention Signal: Weak / Moderate / Strong
Growth Signal: Weak / Moderate / Strong
Overall PMF Confidence: Low / Medium / High
```

## Validation Methods for Early Stage

| Method | Application |
|--------|-------------|
| Customer Interviews | Qualitative demand signal |
| Landing Page Test | Interest validation via signups |
| Smoke Test | Pre-product demand measurement |
| Concierge MVP | Manual service delivery test |
| Waitlist Size | Demand proxy before launch |
