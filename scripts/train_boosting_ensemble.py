"""Train LightGBM + XGBoost on the existing graph-enhanced ETA features.

This script uses the feature matrices already produced by phase3/phase4.  It
keeps one untouched test split for reporting, selects the ensemble weight on a
validation split, and writes models, metrics, feature importance tables and
plots to artifacts/boosting_ensemble.

Run from the repository root:
    python scripts/train_boosting_ensemble.py
"""

from __future__ import annotations

import argparse
import json
import pickle
import warnings
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split


RANDOM_STATE = 42


class _IgnoredLegacyObject:
    """Placeholder for an optional legacy object that is not used for training."""

    def __setstate__(self, state):
        if isinstance(state, dict):
            self.__dict__.update(state)


class _CheckpointUnpickler(pickle.Unpickler):
    """Load phase-4 data without requiring the old gensim runtime."""

    def find_class(self, module, name):
        if module.startswith("gensim."):
            return _IgnoredLegacyObject
        return super().find_class(module, name)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase3", type=Path, default=Path("artifacts/phase3_checkpoint.pkl"))
    parser.add_argument("--phase4", type=Path, default=Path("artifacts/phase4_results.pkl"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/boosting_ensemble"))
    parser.add_argument("--permutation-repeats", type=int, default=5)
    return parser.parse_args()


def load_pickle(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {path}")
    try:
        with path.open("rb") as handle:
            value = pickle.load(handle)
    except ModuleNotFoundError as exc:
        # phase4_results.pkl also contains the original Word2Vec object. The
        # ensemble only needs its already-materialised embeddings dictionary.
        if not exc.name or not exc.name.startswith("gensim"):
            raise
        with path.open("rb") as handle:
            value = _CheckpointUnpickler(handle).load()
    if not isinstance(value, dict):
        raise TypeError(f"Expected a dictionary in {path}, got {type(value).__name__}")
    return value


def metric_row(name: str, y_true: np.ndarray, prediction: np.ndarray) -> dict:
    error = prediction - y_true
    return {
        "model": name,
        "mae_min": float(mean_absolute_error(y_true, prediction)),
        "rmse_min": float(np.sqrt(mean_squared_error(y_true, prediction))),
        "r2": float(r2_score(y_true, prediction)),
        "within_15_pct": float(np.mean(np.abs(error) / np.maximum(np.abs(y_true), 1e-8) < 0.15)),
        "bias_min": float(np.mean(error)),
    }


def build_matrix(phase3: dict, phase4: dict) -> tuple[pd.DataFrame, np.ndarray, list[str], np.ndarray]:
    """Return X, y, feature names and route types from the saved phase outputs."""
    trip_agg = phase4.get("trip_agg_p4", phase3.get("trip_agg"))
    baseline_features = phase3.get("baseline_features")
    graph_features = phase4.get("graph_features", [])
    embeddings = phase4.get("embeddings", {})
    feat_names_e = phase4.get("feat_names_e")

    if trip_agg is None or baseline_features is None:
        raise KeyError("The checkpoints need trip_agg and baseline_features from phase 3.")
    if not graph_features:
        raise KeyError("No graph_features found in phase4_results.pkl. Run phase4 first.")

    base_names = list(baseline_features)
    graph_names = list(graph_features)
    missing = [name for name in base_names + graph_names if name not in trip_agg.columns]
    if missing:
        raise KeyError(f"Missing saved feature columns: {missing[:10]}")

    X = trip_agg[base_names + graph_names].copy()
    names = base_names + graph_names

    # phase4 stores embeddings as a node -> vector mapping rather than columns.
    # Recreate them so the boosting models use the same Set E as the RF model.
    if embeddings:
        try:
            emb_dim = len(next(iter(embeddings.values())))
            src = np.vstack([
                np.asarray(embeddings.get(str(node), np.zeros(emb_dim)), dtype=float)
                for node in trip_agg["source_center"]
            ])
            dst = np.vstack([
                np.asarray(embeddings.get(str(node), np.zeros(emb_dim)), dtype=float)
                for node in trip_agg["destination_center"]
            ])
            emb_names = [f"src_emb_{i}" for i in range(emb_dim)] + [f"dst_emb_{i}" for i in range(emb_dim)]
            X = pd.concat([X.reset_index(drop=True), pd.DataFrame(np.c_[src, dst], columns=emb_names)], axis=1)
            names += emb_names
        except (KeyError, TypeError, ValueError):
            warnings.warn("Could not reconstruct saved embeddings; training on centrality features only.")

    # Keep feature names aligned with the saved checkpoint when possible.
    if feat_names_e and len(feat_names_e) == len(names):
        names = list(feat_names_e)
    X = X.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    y = pd.to_numeric(trip_agg["total_actual_time"], errors="coerce").to_numpy(dtype=float)
    route_type = trip_agg["route_type"].astype(str).to_numpy()
    valid = np.isfinite(y)
    return X.loc[valid].reset_index(drop=True), y[valid], names, route_type[valid]


def choose_blend_weight(y_val: np.ndarray, lgb_val: np.ndarray, xgb_val: np.ndarray) -> tuple[float, np.ndarray]:
    weights = np.linspace(0.0, 1.0, 21)
    scores = [mean_absolute_error(y_val, weight * lgb_val + (1 - weight) * xgb_val) for weight in weights]
    best = float(weights[int(np.argmin(scores))])
    return best, np.asarray(scores)


def save_feature_plot(importance: pd.DataFrame, output: Path) -> None:
    top = importance.head(20).sort_values("ensemble_gain")
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.barh(top["feature"], top["ensemble_gain"], color="#2f80ed")
    ax.set_title("Top feature importance — LightGBM + XGBoost")
    ax.set_xlabel("Normalised average gain")
    fig.tight_layout()
    fig.savefig(output / "feature_importance.png", dpi=160)
    plt.close(fig)


class BlendEstimator(RegressorMixin, BaseEstimator):
    """Small sklearn-compatible wrapper used by permutation_importance."""

    def __init__(self, lgb_model, xgb_model, lgb_weight: float):
        self.lgb_model = lgb_model
        self.xgb_model = xgb_model
        self.lgb_weight = lgb_weight

    def fit(self, X, y=None):
        return self

    def predict(self, X):
        return self.lgb_weight * self.lgb_model.predict(X) + (1 - self.lgb_weight) * self.xgb_model.predict(X)


def main() -> None:
    args = parse_args()
    try:
        import lightgbm as lgb
        import xgboost as xgb
    except ImportError as exc:
        raise SystemExit(
            "LightGBM and XGBoost are required. Install them with "
            "`python -m pip install -r requirements-analysis.txt` and rerun."
        ) from exc

    args.output.mkdir(parents=True, exist_ok=True)
    phase3 = load_pickle(args.phase3)
    phase4 = load_pickle(args.phase4)
    X, y, feature_names, route_type = build_matrix(phase3, phase4)

    X_train, X_test, y_train, y_test, rt_train, rt_test = train_test_split(
        X, y, route_type, test_size=0.20, random_state=RANDOM_STATE, stratify=route_type
    )
    X_fit, X_val, y_fit, y_val = train_test_split(
        X_train, y_train, test_size=0.20, random_state=RANDOM_STATE, stratify=rt_train
    )

    lgb_params = dict(
        objective="regression_l1", n_estimators=700, learning_rate=0.035,
        num_leaves=31, max_depth=-1, min_child_samples=35,
        subsample=0.85, colsample_bytree=0.85, reg_alpha=0.05,
        reg_lambda=0.5, random_state=RANDOM_STATE, n_jobs=-1, verbosity=-1,
    )
    xgb_params = dict(
        objective="reg:absoluteerror", n_estimators=700, learning_rate=0.035,
        max_depth=6, min_child_weight=5, subsample=0.85,
        colsample_bytree=0.85, reg_alpha=0.05, reg_lambda=1.0,
        random_state=RANDOM_STATE, n_jobs=-1, tree_method="hist",
    )

    lgb_model = lgb.LGBMRegressor(**lgb_params)
    xgb_model = xgb.XGBRegressor(**xgb_params)
    lgb_model.fit(X_fit, y_fit, eval_set=[(X_val, y_val)], callbacks=[lgb.early_stopping(60, verbose=False)])
    xgb_model.fit(X_fit, y_fit, eval_set=[(X_val, y_val)], verbose=False)

    lgb_val = lgb_model.predict(X_val)
    xgb_val = xgb_model.predict(X_val)
    blend_weight, blend_scores = choose_blend_weight(y_val, lgb_val, xgb_val)

    # Refit on all non-test rows after selecting the blend weight.
    lgb_final = lgb.LGBMRegressor(**{**lgb_params, "n_estimators": getattr(lgb_model, "best_iteration_", 700) or 700})
    xgb_final = xgb.XGBRegressor(**xgb_params)
    lgb_final.fit(X_train, y_train)
    xgb_final.fit(X_train, y_train, verbose=False)
    pred_lgb = lgb_final.predict(X_test)
    pred_xgb = xgb_final.predict(X_test)
    pred_ensemble = blend_weight * pred_lgb + (1.0 - blend_weight) * pred_xgb

    metric_rows = []
    saved_rf = phase3.get("best_rf")
    if saved_rf is not None:
        try:
            metric_rows.append(metric_row("Saved RF baseline", y_test, saved_rf.predict(X_test[phase3["baseline_features"]])))
        except (KeyError, ValueError, AttributeError):
            warnings.warn("Saved RF was present but could not be evaluated against the reconstructed test split.")
    metric_rows.extend([
        metric_row("LightGBM", y_test, pred_lgb),
        metric_row("XGBoost", y_test, pred_xgb),
        metric_row(f"Ensemble ({blend_weight:.2f} LightGBM / {1-blend_weight:.2f} XGBoost)", y_test, pred_ensemble),
    ])
    metrics = pd.DataFrame(metric_rows)
    metrics.to_csv(args.output / "metrics.csv", index=False)

    lgb_gain = lgb_final.booster_.feature_importance(importance_type="gain")
    xgb_gain = xgb_final.feature_importances_
    importance = pd.DataFrame({
        "feature": feature_names,
        "lightgbm_gain": lgb_gain / max(lgb_gain.sum(), 1e-12),
        "xgboost_gain": xgb_gain / max(xgb_gain.sum(), 1e-12),
    })
    importance["ensemble_gain"] = blend_weight * importance["lightgbm_gain"] + (1 - blend_weight) * importance["xgboost_gain"]
    importance = importance.sort_values("ensemble_gain", ascending=False)
    importance.to_csv(args.output / "feature_importance.csv", index=False)
    save_feature_plot(importance, args.output)

    # Permutation importance on the untouched test split gives a model-agnostic plot/table.
    perm = permutation_importance(
        BlendEstimator(lgb_final, xgb_final, blend_weight),
        X_test, y_test, scoring="neg_mean_absolute_error", n_repeats=args.permutation_repeats,
        random_state=RANDOM_STATE, n_jobs=1,
    )
    pd.DataFrame({"feature": feature_names, "permutation_mae_lift": perm.importances_mean}) \
        .sort_values("permutation_mae_lift", ascending=False) \
        .to_csv(args.output / "permutation_importance.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    colors = ["#9b51e0", "#6fcf97", "#f2994a", "#2f80ed"]
    axes[0].bar(metrics["model"], metrics["mae_min"], color=colors[:len(metrics)])
    axes[0].set_ylabel("MAE (minutes)")
    axes[0].set_title("Holdout model comparison")
    axes[0].tick_params(axis="x", rotation=20)
    axes[1].scatter(y_test, pred_ensemble, s=10, alpha=0.35, color="#2f80ed")
    limit = float(max(y_test.max(), pred_ensemble.max()))
    axes[1].plot([0, limit], [0, limit], "--", color="black")
    axes[1].set_xlabel("Actual time (minutes)")
    axes[1].set_ylabel("Predicted time (minutes)")
    axes[1].set_title("Ensemble predictions")
    fig.tight_layout()
    fig.savefig(args.output / "model_diagnostics.png", dpi=160)
    plt.close(fig)

    bundle = {
        "lightgbm": lgb_final, "xgboost": xgb_final,
        "blend_weight_lightgbm": blend_weight,
        "feature_names": feature_names,
        "metrics": metrics,
    }
    joblib.dump(bundle, args.output / "lightgbm_xgboost_ensemble.joblib")
    (args.output / "run_summary.json").write_text(json.dumps({
        "n_rows": int(len(X)), "n_features": int(X.shape[1]),
        "train_rows": int(len(X_train)), "test_rows": int(len(X_test)),
        "blend_weight_lightgbm": blend_weight,
        "metrics": metrics.to_dict(orient="records"),
    }, indent=2), encoding="utf-8")

    print(metrics.to_string(index=False))
    print(f"\nSelected validation blend: {blend_weight:.2f} LightGBM / {1-blend_weight:.2f} XGBoost")
    print(f"Top features:\n{importance.head(15).to_string(index=False)}")
    print(f"\nSaved outputs to: {args.output.resolve()}")


if __name__ == "__main__":
    main()
