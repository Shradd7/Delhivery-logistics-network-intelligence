# Causal Experiment Design: Hub Delay Reduction Pilot

## Business Question

Does a targeted delay-reduction intervention at high-risk hubs reduce ETA error
and SLA breach rate compared with similar untreated hubs?

## Treatment

Operational intervention at selected bottleneck hubs, such as staffing changes,
dispatch process changes, loading/unloading process fixes, or schedule
rebalancing.

## Unit Of Randomization

Hub-corridor pairs are the preferred unit because delays propagate through
specific corridors rather than only at the hub level.

## Primary Metrics

| Metric | Why It Matters |
|---|---|
| SLA severe breach rate | Direct operational reliability metric |
| ETA absolute error | Measures prediction and planning quality |
| Median delay ratio | Robust to extreme route outliers |
| Revenue recovered | Business value of intervention |

## Experiment Design

1. Select high-risk hubs using bottleneck score, trip volume, and delay ratio.
2. Match each treated hub-corridor pair to similar untreated pairs using:
   - route type
   - baseline delay ratio
   - trip volume
   - source/destination state
   - corridor distance bucket
3. Randomly assign eligible matched pairs into treatment and control groups.
4. Run the intervention for a fixed window, such as 4 weeks.
5. Compare pre/post changes between treatment and control.

## Difference-In-Differences Setup

```text
effect =
  (post_treatment_metric - pre_treatment_metric)
  -
  (post_control_metric - pre_control_metric)
```

This helps separate the intervention effect from seasonality, demand spikes,
network-wide disruptions, or weather effects.

## Key Assumptions

- Parallel trends: treatment and control corridors should have similar trends
  before intervention.
- No spillover: treatment hubs should not materially affect control corridors.
- Stable measurement: SLA and ETA definitions should not change mid-experiment.
- Sufficient volume: very low-volume corridors should be excluded or pooled.

## Guardrail Metrics

- Average actual transit time should not worsen.
- Severe delay should not shift to downstream corridors.
- Intervention cost should not exceed recovered value.
- Customer promise time should not be relaxed to make metrics look better.

## Implementation Note

Risk ranking is predictive analytics. Proving that an intervention caused
improvement requires treatment/control comparison, pre/post measurement, and
guardrails against spillover and seasonality.
