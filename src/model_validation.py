"""Model validation summaries for presentation and deployment fallback."""

import pandas as pd


MODEL_VALIDATION = pd.DataFrame(
    [
        ["OSRM baseline", 161.50, None, None, "Routing estimate baseline"],
        ["Random Forest", 30.95, 74.57, 0.9816, "Segment and trip features"],
        ["Graph-enhanced RF", 29.85, 73.13, 0.9823, "Adds centrality and Node2Vec"],
        ["Cross-validation", 28.81, None, None, "Mean MAE +/- 0.48 min"],
    ],
    columns=["model", "mae_min", "rmse_min", "r2", "notes"],
)

FEATURE_IMPORTANCE = pd.DataFrame(
    [
        ["log_osrm_distance", 0.5484],
        ["log_osrm_time", 0.2353],
        ["total_segments", 0.1073],
        ["log_total_distance", 0.0467],
        ["bottleneck_x_segments", 0.0145],
        ["mean_speed_efficiency", 0.0084],
        ["pct_severe_segments", 0.0071],
        ["distance_per_segment", 0.0043],
        ["severe_x_segments", 0.0030],
        ["osrm_time_per_segment", 0.0028],
    ],
    columns=["feature", "importance"],
)

ERROR_BY_SEGMENT = pd.DataFrame(
    [
        ["Short local routes", "Higher sensitivity to loading/unloading and hub dwell time"],
        ["Multi-segment trips", "Compounding segment delays make prediction harder"],
        ["High-risk FTL corridors", "SLA severe rates require monitoring beyond average MAE"],
        ["Bottleneck hub routes", "Central hubs can amplify downstream ETA errors"],
    ],
    columns=["segment", "validation_note"],
)

VALIDATION_NOTES = [
    "Modeling is evaluated at trip level after segment cleaning and aggregation.",
    "Train/test split should be performed after aggregation to avoid leakage across segment rows from the same trip.",
    "Graph features are generated from historical network structure and should be recomputed on the training window in production.",
    "Cross-validation MAE is reported as 28.81 +/- 0.48 minutes to show stability beyond one split.",
    "Operational validation should monitor MAE by route type, risk category, state pair, and delay bucket.",
]


def get_model_results(artifacts: dict) -> pd.DataFrame:
    """Use phase 4 results when available, otherwise return a static summary."""
    phase4 = artifacts.get("Phase 4 results")
    if isinstance(phase4, dict) and isinstance(phase4.get("results_df"), pd.DataFrame):
        results = phase4["results_df"].copy()
        rename_map = {"name": "model", "mae": "mae_min", "rmse": "rmse_min"}
        return results.rename(columns=rename_map)
    return MODEL_VALIDATION.copy()


def get_feature_importance(artifacts: dict, top_n: int = 10) -> pd.DataFrame:
    """Extract feature importance from the saved graph model if available."""
    phase4 = artifacts.get("Phase 4 results")
    if isinstance(phase4, dict):
        model = phase4.get("best_rf")
        names = phase4.get("feat_names_e") or phase4.get("feat_names_d")
        importances = getattr(model, "feature_importances_", None)
        if names and importances is not None and len(names) == len(importances):
            rows = sorted(zip(names, importances), key=lambda row: row[1], reverse=True)[:top_n]
            return pd.DataFrame(rows, columns=["feature", "importance"])
    return FEATURE_IMPORTANCE.head(top_n).copy()

