"""Measure the lift from graph features for the LightGBM + XGBoost ensemble.

The comparison is deliberately paired: baseline and graph-enhanced models use
the same train/validation/test row indices. The blend weight is selected on
the validation rows and the final numbers are reported only on the untouched
test rows.

Run from the repository root:
    python scripts/phase5_graph_ensemble.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from train_boosting_ensemble import (
    RANDOM_STATE,
    build_matrix,
    choose_blend_weight,
    load_pickle,
    metric_row,
)


def model_params():
    return {
        "lgb": dict(
            objective="regression_l1", n_estimators=700, learning_rate=0.035,
            num_leaves=31, min_child_samples=35, subsample=0.85,
            colsample_bytree=0.85, reg_alpha=0.05, reg_lambda=0.5,
            random_state=RANDOM_STATE, n_jobs=-1, verbosity=-1,
        ),
        "xgb": dict(
            objective="reg:absoluteerror", n_estimators=700, learning_rate=0.035,
            max_depth=6, min_child_weight=5, subsample=0.85,
            colsample_bytree=0.85, reg_alpha=0.05, reg_lambda=1.0,
            random_state=RANDOM_STATE, n_jobs=-1, tree_method="hist",
        ),
    }


def train_ensemble(X, y, fit_idx, val_idx, test_idx, label, lgb, xgb):
    params = model_params()
    lgb_val_model = lgb.LGBMRegressor(**params["lgb"])
    xgb_val_model = xgb.XGBRegressor(**params["xgb"])
    lgb_val_model.fit(X.iloc[fit_idx], y[fit_idx], eval_set=[(X.iloc[val_idx], y[val_idx])], callbacks=[lgb.early_stopping(60, verbose=False)])
    xgb_val_model.fit(X.iloc[fit_idx], y[fit_idx], eval_set=[(X.iloc[val_idx], y[val_idx])], verbose=False)
    weight, _ = choose_blend_weight(
        y[val_idx], lgb_val_model.predict(X.iloc[val_idx]), xgb_val_model.predict(X.iloc[val_idx])
    )

    lgb_final = lgb.LGBMRegressor(**{**params["lgb"], "n_estimators": getattr(lgb_val_model, "best_iteration_", 700) or 700})
    xgb_final = xgb.XGBRegressor(**params["xgb"])
    lgb_final.fit(X.iloc[fit_idx.tolist() + val_idx.tolist()], y[np.r_[fit_idx, val_idx]])
    xgb_final.fit(X.iloc[fit_idx.tolist() + val_idx.tolist()], y[np.r_[fit_idx, val_idx]], verbose=False)
    lgb_pred = lgb_final.predict(X.iloc[test_idx])
    xgb_pred = xgb_final.predict(X.iloc[test_idx])
    ensemble_pred = weight * lgb_pred + (1 - weight) * xgb_pred
    result = metric_row(label, y[test_idx], ensemble_pred)
    result["blend_weight_lightgbm"] = weight
    return result, ensemble_pred, lgb_final, xgb_final


def main():
    try:
        import lightgbm as lgb
        import xgboost as xgb
    except ImportError as exc:
        raise SystemExit("Install dependencies first: python -m pip install -r requirements-analysis.txt") from exc

    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts" / "phase5_graph_ensemble"
    output.mkdir(parents=True, exist_ok=True)
    phase3 = load_pickle(root / "artifacts" / "phase3_checkpoint.pkl")
    phase4 = load_pickle(root / "artifacts" / "phase4_results.pkl")

    graph_X, y, graph_names, route_type = build_matrix(phase3, phase4)
    baseline_names = list(phase3["baseline_features"])
    baseline_trip = phase3["trip_agg"]
    baseline_X = baseline_trip[baseline_names].replace([np.inf, -np.inf], np.nan).fillna(0.0).reset_index(drop=True)
    baseline_y = pd.to_numeric(baseline_trip["total_actual_time"], errors="coerce").to_numpy(dtype=float)
    if len(baseline_X) != len(graph_X) or not np.allclose(baseline_y, y):
        raise ValueError("Phase 3 and phase 4 checkpoints do not contain the same trip row order.")

    indices = np.arange(len(y))
    fit_val, test_idx = train_test_split(indices, test_size=0.20, random_state=RANDOM_STATE, stratify=route_type)
    fit_idx, val_idx = train_test_split(fit_val, test_size=0.20, random_state=RANDOM_STATE, stratify=route_type[fit_val])

    baseline_result, baseline_pred, _, _ = train_ensemble(baseline_X, y, fit_idx, val_idx, test_idx, "Boosting ensemble — baseline features", lgb, xgb)
    graph_result, graph_pred, lgb_final, xgb_final = train_ensemble(graph_X, y, fit_idx, val_idx, test_idx, "Boosting ensemble — baseline + graph features", lgb, xgb)
    metrics = pd.DataFrame([baseline_result, graph_result])
    metrics["mae_lift_vs_baseline_min"] = metrics.iloc[0]["mae_min"] - metrics["mae_min"]
    metrics["within_15_lift_pct_points"] = (metrics["within_15_pct"] - metrics.iloc[0]["within_15_pct"]) * 100
    metrics.to_csv(output / "metrics.csv", index=False)

    lgb_gain = lgb_final.booster_.feature_importance(importance_type="gain")
    xgb_gain = xgb_final.feature_importances_
    w = graph_result["blend_weight_lightgbm"]
    importance = pd.DataFrame({"feature": graph_names, "lightgbm_gain": lgb_gain, "xgboost_gain": xgb_gain})
    importance["ensemble_gain"] = w * importance["lightgbm_gain"] + (1 - w) * importance["xgboost_gain"]
    importance = importance.sort_values("ensemble_gain", ascending=False)
    importance.to_csv(output / "graph_model_feature_importance.csv", index=False)
    graph_mask = importance["feature"].isin(set(phase4["graph_features"]))
    graph_share = float(importance.loc[graph_mask, "ensemble_gain"].sum() / max(importance["ensemble_gain"].sum(), 1e-12))

    fig, axes = plt.subplots(1, 3, figsize=(17, 5))
    axes[0].bar(["Baseline", "+ Graph"], metrics["mae_min"], color=["#9b51e0", "#2f80ed"])
    axes[0].set_ylabel("MAE (minutes)")
    axes[0].set_title("Graph feature lift")
    for i, value in enumerate(metrics["mae_min"]):
        axes[0].text(i, value + 0.2, f"{value:.2f}", ha="center")
    top = importance.head(15).sort_values("ensemble_gain")
    axes[1].barh(top["feature"], top["ensemble_gain"], color="#2f80ed")
    axes[1].set_title("Top graph-model features")
    axes[1].set_xlabel("Tree gain")
    axes[2].scatter(y[test_idx], baseline_pred, s=10, alpha=0.25, label="Baseline", color="#9b51e0")
    axes[2].scatter(y[test_idx], graph_pred, s=10, alpha=0.25, label="+ Graph", color="#2f80ed")
    limit = max(y[test_idx].max(), graph_pred.max())
    axes[2].plot([0, limit], [0, limit], "--", color="black")
    axes[2].set_xlabel("Actual time (minutes)")
    axes[2].set_ylabel("Predicted time (minutes)")
    axes[2].set_title("Paired holdout predictions")
    axes[2].legend()
    fig.tight_layout()
    fig.savefig(output / "graph_feature_lift.png", dpi=160)
    plt.close(fig)

    (output / "summary.json").write_text(json.dumps({
        "graph_gain_share": graph_share,
        "mae_lift_min": float(metrics.iloc[1]["mae_lift_vs_baseline_min"]),
        "within_15_lift_percentage_points": float(metrics.iloc[1]["within_15_lift_pct_points"]),
        "same_test_indices": True,
        "metrics": metrics.to_dict(orient="records"),
    }, indent=2), encoding="utf-8")
    print(metrics.to_string(index=False))
    print(f"\nGraph feature share of tree gain: {graph_share:.1%}")
    print(f"Saved phase-5 outputs to: {output}")


if __name__ == "__main__":
    main()
