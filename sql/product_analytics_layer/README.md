# Delhivery Product Analytics SQL Layer

This folder adds a MySQL 8 analytics layer on top of the existing Python/ML
project. It is intentionally additive: it does not replace the notebooks,
artifacts, Streamlit app, or model code.

## Files

| File | Purpose |
|---|---|
| `delhivery_product_analytics_layer.sql` | MySQL 8 views and stakeholder queries for corridor, SLA, hub, impact, and North Star analytics |
| `README.md` | Product framing, phase mapping, assumptions, and run guidance |

## Verified Against Existing Project

I checked the local project files before writing this layer:

| Existing metric | Local evidence |
|---|---:|
| Raw shipment segments in `data/delivery_data.csv` | 144,867 |
| Unique trips in raw CSV | 14,817 raw / 14,804 cleaned per README |
| Raw source-destination corridors | 2,783 raw / 2,781 cleaned graph edges per README |
| Risk-ranked corridors in artifact after volume filtering | 1,946 |
| Chronic corridors in risk artifact | 92 |
| Critical-risk corridors in risk artifact | 98 |
| Best hub interventions recovery | INR 14.88 lakh |
| Best hub interventions SLA breaches avoided | 9,918 |

The SQL uses the same operating idea as the notebooks: delay ratio, SLA breach
rate, corridor volume, hub contribution, and INR impact.

## How To Run

The SQL assumes a MySQL table named `delivery_segments` with columns matching
`data/delivery_data.csv`.

Recommended flow from PowerShell:

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p -e "CREATE DATABASE IF NOT EXISTS delhivery;"
cmd /c '"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p delhivery < "D:\iit g\projects\delihivery\sql\product_analytics_layer\delhivery_product_analytics_layer.sql"'
```

If the CSV is not loaded yet, the SQL file includes a commented table shape and
`LOAD DATA LOCAL INFILE` example. Enable `LOCAL INFILE` in MySQL if needed.

## Product Story

The SQL output is organized as a PM narrative:

| Story step | SQL artifact | Product question answered |
|---|---|---|
| Problem | `v_product_metrics_north_star` | How reliable is the network overall? |
| Diagnosis | `v_corridor_delay_frequency_rank`, `v_corridor_week_over_week_delay_trend`, `v_hub_downstream_delay_diagnostic` | Where is reliability breaking: lanes, cohorts, hubs, or time periods? |
| Intervention | `v_top10_highest_risk_lanes_by_sla_breach`, `v_business_impact_summary_table` | Which lanes should operations fix first? |
| Impact | `v_top20_lane_recovery_summary`, final executive summary query | What INR recovery and SLA improvement should stakeholders expect? |

## Query Components

### 1. Corridor Performance Dashboard

Views:

- `v_corridor_delay_frequency_rank`
- `v_corridor_week_over_week_delay_trend`
- `v_top10_highest_risk_lanes_by_sla_breach`

Product thinking:

These queries turn model-style risk into an operating dashboard. The PM can ask:
which corridors repeatedly miss SLA, which are worsening week over week, and
which top 10 lanes deserve immediate weekly review.

Techniques used:

- CTEs for readable metric staging
- `DENSE_RANK()` for tied corridor prioritization
- `LAG()` for week-over-week trend movement

### 2. SLA Breach Cohort Analysis

Views:

- `v_sla_breach_cohort_analysis`
- `v_monthly_on_time_corridor_retention`

Product thinking:

Cohorts compress thousands of corridors into severity bands:
`low`, `medium`, `high`, and `critical`. This helps a PM explain whether the
business problem is broad and shallow or narrow and severe.

The retention view answers a stronger product question: are on-time corridors
staying healthy month over month, or are fixes decaying?

### 3. Hub-Level Diagnostic

Views:

- `v_hub_downstream_delay_diagnostic`
- `v_hub_efficiency_drop_alerts`

Product thinking:

Corridor delay is often a symptom. Hub diagnostics identify upstream facilities
that create downstream delay across multiple lanes. The efficiency-drop alert
acts like an operational monitoring trigger when a hub falls more than 10%
versus its previous weekly period.

### 4. Business Impact Summary Table

Views:

- `v_business_impact_summary_table`
- `v_top20_lane_recovery_summary`

Product thinking:

This is the PM prioritization layer. It converts lane-level SLA breaches into:

- total projected delay cost per lane
- expected recovery if fixed
- estimated effort
- impact-vs-effort score
- top 20 lane recovery opportunity

The default SLA penalty assumption is INR 150 per breach, matching the scale of
the existing hub intervention artifacts.

### 5. Product Metrics View

View:

- `v_product_metrics_north_star`

Final query:

- The last query in `delhivery_product_analytics_layer.sql`

Product thinking:

This creates a North Star metric frame:

- On-Time Delivery Rate
- Mean Delay per Corridor
- SLA Breach Rate
- Projected SLA Cost

The final query returns a stakeholder-ready readout:
Problem -> Diagnosis -> Intervention -> Impact.

## Which Project Phases SQL Replaces Or Complements

SQL does not replace the project. It operationalizes the analytical layer that
comes after the Python/ML work.

| Existing project phase | SQL role | Replace or complement? |
|---|---|---|
| Phase 1: Data cleaning | Can reproduce basic filters, validity checks, and clean feature views | Partially replaces simple tabular cleaning for analytics use cases |
| Phase 2: Delay analysis | Replaces many recurring EDA summaries with reusable dashboard views | Mostly replaces repeatable descriptive analysis |
| Phase 3: Baseline ETA model | Can monitor ETA error and SLA outcomes, but cannot train Random Forest models | Complements only |
| Phase 4: Graph-enhanced ETA model | Can consume graph/risk scores if exported to MySQL, but does not compute NetworkX/node embeddings | Complements only |
| Corridor risk ranking notebook | Can create a product-facing lane backlog using breach, delay, volume, and impact | Partially replaces analyst-facing ranking, complements graph-based scoring |
| Delay propagation analysis | Identifies hub downstream contribution, but does not model full network propagation | Complements only |
| Hub intervention simulation | Creates hub alerts and lane priorities, but does not simulate causal scenarios | Complements only |
| Phase 5: Business impact simulation | Operationalizes cost, recovery, and top-lane impact summaries | Partially replaces static business reporting; complements scenario simulation |
| Streamlit dashboard | Supplies SQL-ready datasets and stakeholder summary outputs | Complements and can feed BI tools |

Short version:

SQL replaces repeatable descriptive analytics and monitoring tables. It does not
replace ML prediction, graph feature engineering, causal validation, or
simulation. It makes those outputs easier for a PM, analyst, or operations team
to track every week.

## Assumptions

- `segment_actual_time > 2 * segment_osrm_time` is treated as an SLA breach.
- On-time departure is proxied as `segment_actual_time <= segment_osrm_time`
  because the raw dataset has segment timings rather than explicit hub departure
  promises.
- INR impact uses an assumed INR 150 per SLA breach.
- Top-lane recovery assumes 70% of observed breach cost is recoverable if the
  lane is fixed. Change this constant inside the SQL `params` CTEs if your
  business assumption changes.
