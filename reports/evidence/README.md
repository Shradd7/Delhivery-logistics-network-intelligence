# Evidence Pack

This folder contains lightweight validation exports for the Delhivery Logistics
Network Intelligence project.

Large local artifacts such as the raw CSV and pickle checkpoints are excluded
from GitHub because of size limits and reproducibility concerns. These CSVs are
small enough to track and make the main README, dashboard, and resume claims
auditable without requiring a reviewer to load 50-200 MB model checkpoints.

## Files

| File | Purpose |
|---|---|
| `canonical_model_validation.csv` | Single source of truth for OSRM, RF, graph RF, and CV metrics |
| `graph_validation_tests.csv` | Wilcoxon signed-rank test on paired validation-trip absolute errors |
| `leakage_safe_graph_validation.csv` | Train-split-first graph validation check to defend graph features against leakage concerns |
| `segment_error_analysis.csv` | Error breakdown by route type, risk bucket, delay bucket, source hub, time band, and trip complexity |
| `hub_simulator_assumptions.csv` | Observed, derived, and assumed inputs used by the hub intervention simulator |
| `impact_claim_reconciliation.csv` | Canonical vs scenario/supporting impact claims so INR numbers are not overclaimed |

## How To Regenerate

Run this from the project root after the local pickle artifacts exist:

```powershell
.\delhivery_env\Scripts\python.exe -B scripts\build_evidence_pack.py
```

The generated tables are intentionally compact. They support portfolio review,
resume defensibility, and dashboard fallback evidence; they do not replace the
full notebooks.
