"""Retrain XGBoost/LightGBM with Lian 2024 data and compare to baseline.

Runs LOPOCV (now 4 papers instead of 3), computes SHAP, checks SARs.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

from lnp_optimizer.evaluation import compute_shap_values
from lnp_optimizer.models import evaluate_cv, load_feature_matrix

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parent.parent.parent
_FEATURES_PATH = _ROOT / "data" / "features" / "hsc_features.parquet"
_MODELS_DIR = _ROOT / "data" / "models"

# Baseline results from session 7a (110 rows, 3 papers)
_BASELINE = {
    "xgboost": {"balanced_accuracy": 0.479, "n_rows": 110, "n_papers": 3},
    "lightgbm": {"balanced_accuracy": 0.467, "n_rows": 110, "n_papers": 3},
}

# Additional columns to drop (new columns that aren't features)
_EXTRA_DROP = ["metric_type", "covalent_lipid_mol_pct"]


def retrain() -> dict:
    """Retrain models and compare to baseline."""
    # Load updated matrix
    X, y, groups = load_feature_matrix(_FEATURES_PATH)

    # Drop new metadata/non-feature columns
    drop_cols = [c for c in _EXTRA_DROP if c in X.columns]
    X = X.drop(columns=drop_cols)

    n_papers = len(set(groups))
    print(f"Feature matrix: {X.shape[0]} rows × {X.shape[1]} features")
    print(f"Papers: {dict(pd.Series(groups).value_counts())}")
    print(f"Target: {dict(pd.Series(y).value_counts())}")
    print(f"LOPOCV folds: {n_papers}")
    print()

    results = {}

    for model_name in ["xgboost", "lightgbm"]:
        print(f"{'='*60}")
        print(f"Training {model_name.upper()}")
        print(f"{'='*60}")

        cv_result = evaluate_cv(X, y, groups, model_name=model_name)

        ba = cv_result["balanced_accuracy_mean"]
        ba_std = cv_result["balanced_accuracy_std"]
        baseline_ba = _BASELINE[model_name]["balanced_accuracy"]
        delta = ba - baseline_ba

        results[model_name] = {
            "balanced_accuracy_mean": ba,
            "balanced_accuracy_std": ba_std,
            "baseline": baseline_ba,
            "delta": delta,
            "n_rows": X.shape[0],
            "n_papers": n_papers,
        }

        print(f"\n  Balanced accuracy: {ba:.4f} ± {ba_std:.4f}")
        print(f"  Baseline (110 rows): {baseline_ba:.3f}")
        print(f"  Delta: {delta:+.4f} ({'improved' if delta > 0 else 'declined'})")

        # Per-fold details
        for fold in cv_result.get("folds", []):
            print(f"  Fold {fold['fold']}: BA={fold['balanced_accuracy']:.3f}"
                  f"  (test paper: {fold.get('test_paper', '?')})")
        print()

    # SHAP analysis with LightGBM
    print(f"{'='*60}")
    print("SHAP Analysis (LightGBM, full data)")
    print(f"{'='*60}")

    shap_abs, feat_names = compute_shap_values("lightgbm", X, y)
    mean_shap = shap_abs.mean(axis=0)
    shap_rank = sorted(zip(feat_names, mean_shap, strict=True), key=lambda x: -x[1])

    print("\nTop 15 features by mean |SHAP|:")
    for i, (name, val) in enumerate(shap_rank[:15], 1):
        marker = ""
        if name in ("ionizable_mol_pct", "receptor_cd117", "dose_mg_per_kg",
                     "hl_dotap", "helper_mol_pct"):
            marker = " ← known SAR"
        if name == "covalent_lipid_mol_pct":
            marker = " ← NEW (Lian)"
        print(f"  {i:2d}. {name:30s} {val:.4f}{marker}")

    # Save SHAP values
    shap_df = pd.DataFrame(shap_abs, columns=feat_names)
    shap_df.to_parquet(_MODELS_DIR / "shap_values.parquet", index=False)

    # Save updated CV results
    cv_path = _MODELS_DIR / "cv_results_with_lian.json"
    with open(cv_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved results to {cv_path}")

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    retrain()
