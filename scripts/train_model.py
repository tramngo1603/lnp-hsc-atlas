"""Train LightGBM via LOPOCV and compute SHAP values.

Outputs:
  - data/models/lgbm_model.pkl
  - data/models/shap_values.csv
  - data/models/lopocv_results.json
"""

from __future__ import annotations

import json
import logging
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from lnp_optimizer.models import load_feature_matrix, evaluate_cv  # noqa: E402
from lnp_optimizer.evaluation import compute_shap_values  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(message)s")

_ROOT = Path(__file__).resolve().parent.parent
_FEAT_PATH = _ROOT / "data" / "features" / "hsc_features.parquet"
_MODELS_DIR = _ROOT / "data" / "models"

_KNOWN_SARS = {"ionizable_mol_pct", "receptor_cd117", "dose_mg_per_kg",
               "hl_dotap", "helper_mol_pct"}
_NEW_FINDINGS = {"chol_to_helper_ratio", "cholesterol_mol_pct", "il_molecular_weight"}

_EXTRA_DROP = ["metric_type", "covalent_lipid_mol_pct"]


def main() -> int:
    """Train model and generate artifacts."""
    print("=" * 60)
    print("Training LightGBM (LOPOCV)")
    print("=" * 60)

    X, y, groups = load_feature_matrix(_FEAT_PATH)
    drop = [c for c in _EXTRA_DROP if c in X.columns]
    X = X.drop(columns=drop)

    print(f"Features: {X.shape[1]}, Rows: {X.shape[0]}")
    print(f"Papers: {dict(pd.Series(groups).value_counts())}")
    print(f"Target: {dict(pd.Series(y).value_counts())}")

    # LOPOCV
    cv = evaluate_cv(X, y, groups, model_name="lightgbm")
    ba = cv["balanced_accuracy_mean"]
    ba_std = cv["balanced_accuracy_std"]

    print(f"\nBalanced accuracy: {ba:.4f} ± {ba_std:.4f}")
    for fold in cv.get("folds", []):
        print(f"  Fold {fold['fold']}: BA={fold['balanced_accuracy']:.3f}"
              f" (test: {fold.get('test_paper', '?')})")

    # Save LOPOCV results
    lopocv_path = _MODELS_DIR / "lopocv_results.json"
    results = {
        "model": "lightgbm",
        "balanced_accuracy_mean": round(ba, 4),
        "balanced_accuracy_std": round(ba_std, 4),
        "n_rows": X.shape[0],
        "n_features": X.shape[1],
        "n_papers": len(set(groups)),
        "folds": cv.get("folds", []),
    }
    with open(lopocv_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved: {lopocv_path}")

    # Train full model
    print("\nTraining full model for SHAP...")
    from lightgbm import LGBMClassifier
    model = LGBMClassifier(
        n_estimators=100, max_depth=4, learning_rate=0.1,
        min_child_samples=5, class_weight="balanced",
        verbose=-1, random_state=42,
    )
    model.fit(X, y)

    model_path = _MODELS_DIR / "lgbm_model.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    print(f"Saved: {model_path}")

    # SHAP
    print("\nComputing SHAP values...")
    shap_abs, feat_names = compute_shap_values("lightgbm", X, y)
    mean_shap = shap_abs.mean(axis=0)
    ranked = sorted(zip(feat_names, mean_shap, strict=True), key=lambda x: -x[1])

    shap_rows = []
    for rank, (feat, val) in enumerate(ranked, 1):
        if feat in _KNOWN_SARS:
            ftype = "known"
        elif feat in _NEW_FINDINGS:
            ftype = "new"
        else:
            ftype = "other"
        shap_rows.append({"rank": rank, "feature": feat,
                          "mean_abs_shap": round(float(val), 4), "type": ftype})

    shap_df = pd.DataFrame(shap_rows)
    shap_path = _MODELS_DIR / "shap_values.csv"
    shap_df.to_csv(shap_path, index=False)
    print(f"Saved: {shap_path}")

    # Also save raw SHAP matrix
    pd.DataFrame(shap_abs, columns=feat_names).to_parquet(
        _MODELS_DIR / "shap_values.parquet", index=False)

    print("\nTop 10 SHAP features:")
    for row in shap_rows[:10]:
        marker = " ← SAR" if row["type"] == "known" else (
            " ← NEW" if row["type"] == "new" else "")
        print(f"  {row['rank']:2d}. {row['feature']:30s} {row['mean_abs_shap']:.4f}{marker}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
