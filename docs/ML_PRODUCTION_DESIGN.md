# ML Production Design: ETA And Network Risk System

## Objective

Convert the Delhivery logistics analysis into a repeatable production system
that scores ETA risk, corridor risk, and hub intervention priority on a schedule.

## Batch Scoring Flow

```text
Raw shipment events
-> data validation
-> trip aggregation
-> feature generation
-> graph feature refresh
-> ETA model scoring
-> corridor risk scoring
-> hub intervention ranking
-> dashboard / alert tables
```

## Retraining Strategy

| Area | Plan |
|---|---|
| Cadence | Retrain weekly or monthly depending on volume and drift |
| Training window | Rolling 8-12 week window |
| Validation | Hold out most recent trips as temporal validation |
| Promotion | Deploy only if MAE, bias, and SLA-risk precision improve |
| Rollback | Keep previous model artifact and feature schema |

## Drift Monitoring

Track these features and metrics over time:

- OSRM time
- OSRM distance
- actual time
- delay ratio
- route type mix
- trip volume by corridor
- severe SLA breach rate
- ETA MAE by route type and state pair

## Data Quality Checks

- Missing source or destination center
- Negative or zero distance/time
- Duplicate trip UUIDs
- Unusually high delay ratios
- Route type values outside expected set
- Sudden volume drops for key hubs

## Model Monitoring

| Metric | Alert Condition |
|---|---|
| ETA MAE | Increases by more than 15% vs trailing baseline |
| Prediction bias | Systematic over/under prediction by route type |
| Within-15-min accuracy | Drops below threshold |
| Corridor risk precision | Top-ranked corridors stop producing SLA breaches |
| Feature drift | PSI or distribution shift exceeds threshold |

## Production Tables

```text
fact_trip_segments
fact_trip_aggregates
dim_facility
dim_corridor
model_eta_predictions
corridor_risk_scores
hub_intervention_scores
model_monitoring_daily
```

## Implementation Note

The model is only one component of the production system. A complete rollout
also needs data validation, feature refresh, graph rebuilds, monitoring,
retraining policy, model rollback, and operations-facing alerting.
