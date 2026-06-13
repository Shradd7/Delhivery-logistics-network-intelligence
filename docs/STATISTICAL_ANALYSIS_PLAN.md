# Statistical Analysis Plan

## Objective

Add explicit statistical reasoning to the logistics project so model findings
can be tested, compared, and communicated with uncertainty.

## Hypothesis Tests

| Question | Test |
|---|---|
| Do FTL and Carting have different delay ratios? | Mann-Whitney U test or t-test after distribution check |
| Are severe SLA breaches independent of route type? | Chi-square test |
| Did intervention reduce breach rate? | Two-proportion z-test or difference-in-differences |
| Did ETA error improve after graph features? | Paired test on same validation trips |
| Are high-risk corridors statistically different from normal corridors? | Bootstrap confidence intervals |

## Confidence Intervals

Use confidence intervals for:

- mean ETA error
- median delay ratio
- severe SLA breach rate
- revenue recovered
- treatment effect in intervention pilots

## Bayesian Extension

A Bayesian view can estimate the probability that a hub is truly high risk:

```text
posterior risk =
  prior hub risk
  updated by observed SLA breaches, trip volume, and delay ratio
```

This is useful for low-volume hubs where raw breach rate can be noisy.

## Example Bayesian Use Case

If a corridor has 2 severe breaches out of 2 trips, the raw breach rate is 100%.
But with low volume, a Bayesian prior prevents overreacting to tiny samples.

## Implementation Note

The statistical layer separates prediction quality from decision confidence:

- ML predicts ETA and ranks risk.
- Statistics tests whether differences are significant.
- Causal inference estimates whether interventions caused improvement.
- Bayesian reasoning handles uncertainty when sample sizes are small.
