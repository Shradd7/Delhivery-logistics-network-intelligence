"""Model validation summaries for presentation and deployment fallback."""

from pathlib import Path

import pandas as pd


MODEL_VALIDATION = pd.DataFrame(
    [
        ["OSRM baseline", 161.50, None, None, 5.50, None, None, None, "Routing estimate baseline"],
        [
            "Historical RF baseline",
            30.9461,
            74.5730,
            0.9816,
            77.6427,
            -0.7828,
            None,
            None,
            "Previous Random Forest model",
        ],
        [
            "LightGBM + XGBoost ensemble",
            29.4870,
            78.0489,
            0.9799,
            80.2769,
            -9.1013,
            None,
            None,
            "Baseline features; phase-5 paired holdout",
        ],
        [
            "Graph-enhanced LightGBM + XGBoost ensemble",
            28.0028,
            74.1050,
            0.9819,
            81.3576,
            -7.7652,
            None,
            None,
            "Baseline + graph centrality, corridor, and embedding features",
        ],
        ["RF Baseline (historical Set C)", 30.9461, 74.5730, 0.9816, 77.6427, -0.7828, None, None, "Previous model; retained for comparison"],
        [
            "RF + Graph Centrality (historical Set D)",
            30.2888,
            73.4359,
            0.9822,
            78.2506,
            -0.6466,
            None,
            None,
            "Adds trainable graph centrality features",
        ],
        [
            "RF + Centrality + Node2Vec Embeddings (historical Set E)",
            29.8117,
            73.1315,
            0.9823,
            78.1830,
            -1.0180,
            None,
            None,
            "Best graph model with centrality and embeddings",
        ],
        [
            "5-fold CV on best graph model",
            None,
            None,
            None,
            None,
            None,
            28.78,
            0.51,
            "Canonical notebook output from phase4.ipynb",
        ],
    ],
    columns=[
        "model",
        "mae_min",
        "rmse_min",
        "r2",
        "within_15_pct",
        "bias_min",
        "cv_mae_mean_min",
        "cv_mae_std_min",
        "notes",
    ],
)

GRAPH_VALIDATION_TESTS = pd.DataFrame(
    [
        [
            "Wilcoxon signed-rank test",
            "Boosting baseline vs graph-enhanced boosting ensemble",
            2961,
            2066088.0,
            0.006534,
            0.05,
            "Graph-enhanced boosting has lower paired holdout MAE on the same validation trips.",
            "paired phase-5 holdout predictions on the same route_type-stratified trip split",
        ]
    ],
    columns=[
        "test_name",
        "comparison",
        "sample_size",
        "statistic",
        "p_value",
        "alpha",
        "conclusion",
        "evidence_scope",
    ],
)

LEAKAGE_SAFE_GRAPH_VALIDATION = pd.DataFrame(
    [
        [
            "RF baseline retrained for leakage-safe comparison",
            31.145365,
            74.752369,
            0.981535,
            77.136103,
            -0.809,
            "Trip split first; no graph features.",
            None,
            None,
            None,
        ],
        [
            "Leakage-safe graph centrality RF",
            30.232576,
            72.711160,
            0.982530,
            78.183046,
            -1.130519,
            "Graph rebuilt from training trips only; validation hubs mapped to train-window graph features.",
            2089904.0,
            0.027257,
            0.912789,
        ],
    ],
    columns=[
        "model",
        "mae_min",
        "rmse_min",
        "r2",
        "within_15_pct",
        "bias_min",
        "notes",
        "wilcoxon_statistic_vs_retrained_baseline",
        "wilcoxon_p_value_vs_retrained_baseline",
        "mae_lift_min_vs_retrained_baseline",
    ],
)

SEGMENT_ERROR_ANALYSIS = pd.DataFrame(
    [
        [
            "route_type",
            "FTL",
            1181,
            52.068,
            23.901,
            121.902,
            4.101,
            "FTL trips carry the highest aggregate ETA error and should be monitored separately.",
        ],
        [
            "route_type",
            "Carting",
            1780,
            15.045,
            5.514,
            34.751,
            -1.027,
            "Carting trips are materially easier for the graph model to predict in this validation split.",
        ],
        [
            "delay_bucket",
            "extreme_delay",
            167,
            76.838,
            32.380,
            194.314,
            63.407,
            "Extreme-delay trips are the clearest failure pocket and are under-predicted.",
        ],
        [
            "corridor_risk_bucket",
            "Critical",
            365,
            42.318,
            13.129,
            91.006,
            3.941,
            "Critical-risk corridors need separate SLA monitoring beyond average network MAE.",
        ],
    ],
    columns=[
        "segment_group",
        "segment_value",
        "n_trips",
        "mae_min",
        "median_abs_error_min",
        "p90_abs_error_min",
        "bias_min",
        "actionable_readout",
    ],
)

EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "reports" / "evidence"

FEATURE_IMPORTANCE = pd.DataFrame(
    [
        ["log_osrm_time", 0.2200],
        ["log_osrm_distance", 0.1994],
        ["mean_speed_efficiency", 0.1030],
        ["pct_severe_segments", 0.0314],
        ["total_segments", 0.0225],
        ["osrm_speed", 0.0166],
        ["osrm_time_per_segment", 0.0117],
        ["severe_x_segments", 0.0115],
        ["distance_per_segment", 0.0092],
        ["bottleneck_x_segments", 0.0038],
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
    "The phase-5 paired holdout reduced ensemble MAE from 29.49 to 28.00 minutes after adding graph features.",
    "Operational validation should monitor MAE by route type, risk category, state pair, and delay bucket.",
]


def get_model_results(artifacts: dict) -> pd.DataFrame:
    """Return the current boosting summary, with historical RF rows retained."""
    phase5_metrics = EVIDENCE_DIR.parent.parent / "artifacts" / "phase5_graph_ensemble" / "metrics.csv"
    if phase5_metrics.exists():
        phase5 = pd.read_csv(phase5_metrics)
        rows = []
        for row in phase5.to_dict("records"):
            rows.append([
                row["model"], row["mae_min"], row["rmse_min"], row["r2"],
                row["within_15_pct"] * 100, row["bias_min"], None, None,
                "Phase-5 paired holdout comparison",
            ])
        return pd.DataFrame(rows, columns=MODEL_VALIDATION.columns)
    # Keep the dashboard aligned with the current phase-5 model even when the
    # generated local artifacts are not committed for deployment.
    return MODEL_VALIDATION.copy()


def get_feature_importance(artifacts: dict, top_n: int = 10) -> pd.DataFrame:
    """Extract phase-5 graph-ensemble importance when available."""
    phase5_importance = EVIDENCE_DIR.parent.parent / "artifacts" / "phase5_graph_ensemble" / "graph_model_feature_importance.csv"
    if phase5_importance.exists():
        phase5 = pd.read_csv(phase5_importance)
        return phase5[["feature", "ensemble_gain"]].rename(columns={"ensemble_gain": "importance"}).head(top_n)
    return FEATURE_IMPORTANCE.head(top_n).copy()


def read_evidence_csv(file_name: str, fallback: pd.DataFrame) -> pd.DataFrame:
    """Read a lightweight evidence CSV when present."""
    path = EVIDENCE_DIR / file_name
    if path.exists():
        return pd.read_csv(path)
    return fallback.copy()


def get_canonical_model_validation() -> pd.DataFrame:
    """Return the canonical model validation evidence table."""
    return read_evidence_csv("canonical_model_validation.csv", MODEL_VALIDATION)


def get_graph_validation_tests() -> pd.DataFrame:
    """Return paired graph validation test evidence."""
    return read_evidence_csv("graph_validation_tests.csv", GRAPH_VALIDATION_TESTS)


def get_leakage_safe_graph_validation() -> pd.DataFrame:
    """Return leakage-aware graph validation evidence."""
    return read_evidence_csv("leakage_safe_graph_validation.csv", LEAKAGE_SAFE_GRAPH_VALIDATION)


def get_segment_error_analysis() -> pd.DataFrame:
    """Return segment-wise model error analysis."""
    return read_evidence_csv("segment_error_analysis.csv", SEGMENT_ERROR_ANALYSIS)
