# Delhivery Logistics Network Intelligence

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red)
![Machine Learning](https://img.shields.io/badge/ML-Random%20Forest-green)
![NetworkX](https://img.shields.io/badge/Graph-NetworkX-purple)
![Status](https://img.shields.io/badge/Status-Deployed-success)

A logistics intelligence dashboard that combines **ETA prediction**, **network
science**, **corridor risk ranking**, **delay propagation analysis**, and
**hub-level intervention simulation** to identify where Delhivery-style
operations should act first.

Live dashboard:

https://delhivery-logistics-network-intelligence-9fai7petrfsyvrbxs26fx.streamlit.app/

---

## Problem Statement

Logistics networks often lose time and money because delays are not isolated.
A late hub can affect downstream corridors, SLA performance, customer
experience, and revenue recovery.

This project answers:

> Which hubs and corridors should be prioritized to reduce ETA error, SLA breaches, and operational delays?

---

## Solution Overview

The project turns shipment segment data into a decision system:

1. Clean shipment segment records.
2. Aggregate segment-level activity into trip-level modeling data.
3. Build ETA prediction baselines and Random Forest models.
4. Create a facility-corridor graph using NetworkX.
5. Add graph features such as centrality, bottleneck score, and embeddings.
6. Rank risky corridors using delay, SLA, volume, and graph signals.
7. Simulate hub interventions to estimate SLA and revenue impact.
8. Present results in a deployed Streamlit dashboard.

---

## Key Results

| Metric | Value |
|---|---:|
| Raw shipment segments | 144,867 |
| Cleaned shipment segments | 141,661 |
| Unique trips | 14,804 |
| Facilities / Nodes | 1,657 |
| Corridors / Edges | 2,781 |
| Chronic corridors | 92 |
| OSRM Baseline MAE | 161.5 min |
| Random Forest MAE | 30.95 min |
| Graph-Enhanced RF MAE | 29.85 min |
| Cross-Validation MAE | 28.81 +/- 0.48 min |

---

## Business Impact

The project does not stop at ETA prediction. It converts model and network
signals into an intervention plan for hubs and corridors.

The rupee values below are calculated from the available project dataset and
should be interpreted as sample-window estimates. In a production environment,
the same framework can be scaled across more facilities, more corridors,
longer time windows, and live shipment volume.

| Business Question | Result |
|---|---:|
| Estimated revenue at risk from severe delays | INR 21.17 lakh |
| Potential recovery from targeted interventions | INR 3.96 lakh |
| Illustrative annualized recovery opportunity | INR 47.52 lakh |
| Best single hub by recovered value | IND421302AAG |
| Estimated recovery from best hub intervention | INR 4.54 lakh |
| SLA breaches avoided at best hub | 3,029 |

### Recommended Actions

- Run a 30% delay-reduction pilot on the highest ROI bottleneck hubs.
- Prioritize hubs with high trip volume, bottleneck score, and recoverable value.
- Review critical FTL corridors where severe SLA breach rates approach 100%.
- Track recovered SLA breaches and recovered revenue weekly after intervention.
- Recalculate impact at full network scale using current volume and SLA assumptions.

### Business Assumptions

- Revenue impact is a sample-window estimate, not a full Delhivery P&L claim.
- Annualized recovery assumes the observed recoverable value represents one comparable operating month.
- Production ROI should include intervention cost, shipment volume, SLA penalty rules, and revenue per delayed shipment.
- Hub recommendations should be treated as pilot priorities before permanent capacity investments.

### Top Hub Intervention Examples

| Hub | Delay Reduction | Trips | Affected Corridors | ETA Improvement | SLA Breaches Avoided | Revenue Recovered |
|---|---:|---:|---:|---:|---:|---:|
| IND421302AAG | 30% | 1,281 | 29 | 10.15 min | 3,029 | INR 4.54 lakh |
| IND000000ACB | 30% | 1,848 | 49 | 10.37 min | 2,897 | INR 4.35 lakh |
| IND562132AAA | 30% | 1,366 | 36 | 9.04 min | 1,771 | INR 2.66 lakh |
| IND400072AAJ | 30% | 53 | 1 | 32.40 min | 1,240 | INR 1.86 lakh |
| IND501359AAE | 30% | 660 | 27 | 9.37 min | 981 | INR 1.47 lakh |

---

## Dashboard Preview

The Streamlit dashboard includes executive KPIs, business impact, ETA model
performance, network bottlenecks, corridor risk ranking, delay propagation, and
hub intervention simulation.

Interactive dashboard controls include:

- Hub and intervention scenario filters for business impact.
- Route type, risk category, state, and minimum-trip filters for corridor risk.
- Hub comparison controls for the intervention simulator.
- Validation tables for model performance, feature importance, and error review.

![ETA model performance](assets/plots/phase4_graph_advantage.png)

![Network bottleneck analysis](assets/plots/network_bottleneck.png)

![Corridor risk ranking](assets/plots/corridor_risk_ranking.png)

![Hub intervention simulator](assets/plots/hub_intervention_simulator.png)

---

## Project Structure

```text
.
+-- app.py
+-- requirements.txt
+-- Dockerfile
+-- README.md
+-- .streamlit/
|   +-- config.toml
+-- src/
|   +-- artifacts.py
|   +-- impact.py
|   +-- model_validation.py
+-- docs/
|   +-- CAUSAL_EXPERIMENT_DESIGN.md
|   +-- ML_PRODUCTION_DESIGN.md
|   +-- STATISTICAL_ANALYSIS_PLAN.md
+-- sql/
|   +-- delhivery_analytics_queries.sql
+-- assets/
|   +-- plots/
+-- artifacts/
|   +-- delhivery_graph.edgelist
+-- notebooks/
|   +-- phase1.ipynb
|   +-- phase2.ipynb
|   +-- phase3.ipynb
|   +-- phase4.ipynb
|   +-- phase5.ipynb
|   +-- Delay_propogation_analysis.ipynb
|   +-- corridor_risk_ranking.ipynb
|   +-- Hub_Intervention_sim.ipynb
```

Large raw data and pickle checkpoints are intentionally excluded from GitHub.
The deployed dashboard runs from static plots and fallback summary tables.

---

## Interview Extensions

These additions make the project stronger for DS, MLE, product analytics, and
quantitative analytics interviews.

| Interview Area | Artifact |
|---|---|
| Causal inference / A/B testing | `docs/CAUSAL_EXPERIMENT_DESIGN.md` |
| ML system design / production retraining | `docs/ML_PRODUCTION_DESIGN.md` |
| Statistics / hypothesis testing / Bayesian reasoning | `docs/STATISTICAL_ANALYSIS_PLAN.md` |
| SQL product analytics | `sql/delhivery_analytics_queries.sql` |

These files are design and analysis extensions. They do not require rerunning
the notebooks or retraining the model.

---

## Methodology

### Phase 1 - Data Cleaning

Cleaned raw shipment segment records and removed inconsistent observations.

### Phase 2 - Delay Analysis

Analyzed delay patterns by route type, time window, corridor, and facility.

Key findings:

- OSRM underestimates ETA by 69% at median.
- Carting delays are higher than FTL delays.
- 3 AM-4 AM trips show the highest delay.

### Phase 3 - Baseline ETA Model

Built a Random Forest ETA model and compared it with the OSRM baseline.

| Model | MAE |
|---|---:|
| OSRM Baseline | 161.5 min |
| Random Forest | 30.95 min |

### Phase 4 - Graph-Enhanced ETA Model

Constructed a logistics graph using facilities as nodes and shipment corridors
as edges.

Graph features used:

- Betweenness centrality
- Bottleneck scores
- Node2Vec embeddings
- Source/destination network features

Result:

- Graph RF MAE: 29.85 min
- Graph features improved MAE by 1.09 minutes.

### Phase 5 - Business Impact Simulation

Created intervention analysis covering:

- Revenue at risk
- FTL vs Carting comparison
- Bottleneck hub prioritization
- Chronic corridor analysis
- SLA breaches avoided
- Revenue recovered

---

## Model Validation

Validation was designed to make the project credible beyond a single model
score.

- Modeling is evaluated at trip level after segment cleaning and aggregation.
- Train/test splitting should happen after aggregation to avoid leakage from multiple segments of the same trip.
- Cross-validation MAE is reported as 28.81 +/- 0.48 minutes.
- Feature importance confirms that distance, OSRM time, segment count, and bottleneck features drive predictions.
- Error should be monitored by route type, risk category, state pair, and delay bucket in production.

---

## Deployment Fallback

The original analysis uses large local pickle checkpoints. Some exceed
GitHub's 100 MB file limit, so they are not tracked.

For deployment, the dashboard uses:

- Static PNG plots from `assets/plots/`.
- Lightweight graph output from `artifacts/delhivery_graph.edgelist`.
- Fallback summary tables embedded in `src/impact.py` and `src/model_validation.py`.

If local pickle artifacts are available, the dashboard loads them. If they are
missing, the dashboard still runs with fallback tables and static visuals.

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Shradd7/Delhivery-logistics-network-intelligence.git
cd Delhivery-logistics-network-intelligence
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the dashboard

```bash
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

### 4. Run with Docker

```bash
docker build -t delhivery-dashboard .
docker run -p 8501:8501 delhivery-dashboard
```

---

## Tech Stack

| Category | Tools |
|---|---|
| Dashboard | Streamlit |
| Data Processing | Pandas |
| Machine Learning | Random Forest, Scikit-learn |
| Graph Analytics | NetworkX, Node2Vec-style embeddings |
| Visualization | Matplotlib/Seaborn outputs, Streamlit charts |
| Deployment | Streamlit Community Cloud, Docker |
| Repository Structure | Python `src/` helpers + notebooks |

---

## Production Roadmap

### 1. Daily Network Scoring

- Score every active hub and corridor daily using latest shipment data.
- Recompute delay ratio, SLA breach rate, trip volume, and bottleneck score.
- Store daily scores in a warehouse table for trend monitoring.

### 2. SLA Alerting

- Trigger alerts for corridors crossing risk-score or severe-breach thresholds.
- Send hub-level summaries to operations teams before peak dispatch windows.
- Separate alerts by route type so FTL and Carting teams get relevant actions.

### 3. Model Monitoring

- Track ETA MAE, bias, and within-15-minute accuracy by route type and state pair.
- Monitor drift in OSRM time, distance, trip volume, and delay ratio.
- Flag hubs where prediction error rises faster than the network average.

### 4. Retraining Cadence

- Retrain the ETA model weekly or monthly.
- Rebuild graph features from a training-window-only network snapshot.
- Compare the new model against the current production model before release.

### 5. Intervention Measurement

- Run hub intervention pilots with clear pre/post measurement windows.
- Track SLA breaches avoided, ETA improvement, revenue recovered, and intervention cost.
- Promote interventions only when recovered value exceeds operational cost.

---

## Conclusion

This project shows how logistics analytics can move beyond ETA prediction into
actionable network intelligence. The graph-enhanced model improves ETA accuracy,
while corridor risk ranking and hub intervention simulation translate model
outputs into operational priorities.

The deployed dashboard makes the analysis easy to explore for business,
operations, and analytics stakeholders.

---

## Future Work

- Add live data refresh from a warehouse or scheduled CSV export.
- Add downloadable action lists for operations managers.
- Add intervention cost modeling for stronger ROI estimates.
- Add state/region-level product analytics views.
- Add automated retraining and model monitoring.

---

## Author

**Shradd7** - [GitHub](https://github.com/Shradd7)
