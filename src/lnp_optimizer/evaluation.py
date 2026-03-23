"""SHAP interpretability and SAR recovery analysis.

Computes SHAP values for tree models and checks whether learned
feature importances match known structure-activity relationships
from the HSC-LNP literature.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# SHAP computation
# ---------------------------------------------------------------------------


def compute_shap_values(
    model_name: str,
    X: pd.DataFrame,
    y: np.ndarray,
    output_dir: Path | None = None,
) -> tuple[np.ndarray, list[str]]:
    """Train on full data and compute SHAP values.

    Args:
        model_name: "xgboost" or "lightgbm".
        X: Feature matrix.
        y: Target array.
        output_dir: Optional directory to save SHAP values.

    Returns:
        (shap_values array, feature_names list).
    """
    import shap

    model = _train_full(model_name, X, y)
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    # Handle multiclass SHAP: list of 2D or single 3D array
    if isinstance(shap_values, list):
        shap_abs = np.mean(
            [np.abs(sv) for sv in shap_values], axis=0
        )
    elif shap_values.ndim == 3:
        # (n_samples, n_features, n_classes) → average across classes
        shap_abs = np.mean(np.abs(shap_values), axis=2)
    else:
        shap_abs = np.abs(shap_values)

    feat_names = list(X.columns)

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        shap_df = pd.DataFrame(shap_abs, columns=feat_names)
        shap_df.to_parquet(output_dir / "shap_values.parquet", index=False)
        logger.info("Saved SHAP values to %s", output_dir)

    return shap_abs, feat_names


def _train_full(
    model_name: str, X: pd.DataFrame, y: np.ndarray
) -> Any:
    """Train model on full dataset for SHAP analysis."""
    from lnp_optimizer.models import _build_lgbm, _build_xgb, _class_weights

    if model_name == "xgboost":
        model = _build_xgb(n_classes=3)
        sw = _class_weights(y)
        model.fit(X, y, sample_weight=sw)
    else:
        model = _build_lgbm()
        model.fit(X, y)
    return model


# ---------------------------------------------------------------------------
# Feature importance report
# ---------------------------------------------------------------------------


def print_top_features(
    shap_abs: np.ndarray,
    feature_names: list[str],
    n: int = 10,
) -> None:
    """Print top features by mean absolute SHAP value.

    Args:
        shap_abs: Absolute SHAP values (n_samples × n_features).
        feature_names: Feature names.
        n: Number of top features to show.
    """
    mean_shap = np.mean(shap_abs, axis=0)
    ranking = np.argsort(mean_shap)[::-1]

    print(f"\n{'='*50}")
    print(f"Top {n} Features by Mean |SHAP|")
    print(f"{'='*50}")
    print(f"{'Rank':<6} {'Feature':<30} {'Mean |SHAP|':>12}")
    print("-" * 50)
    for i in range(min(n, len(ranking))):
        idx = ranking[i]
        print(
            f"{i+1:<6} {feature_names[idx]:<30} "
            f"{mean_shap[idx]:>12.4f}"
        )


# ---------------------------------------------------------------------------
# SAR recovery check (Validation Layer 4)
# ---------------------------------------------------------------------------

# Known SARs from CLAUDE.md
_KNOWN_SARS = [
    {
        "name": "DOTAP drives BM delivery",
        "feature": "helper_is_cationic",
        "expected": "high importance",
    },
    {
        "name": "PEG chain C18 > C14 for HSC",
        "feature": "peg_chain_numeric",
        "expected": "high importance, positive direction",
    },
    {
        "name": "Targeting strategy matters",
        "feature": "targeting_encoded",
        "expected": "high importance",
    },
    {
        "name": "Dose is critical",
        "feature": "dose_mg_per_kg",
        "expected": "high importance",
    },
    {
        "name": "Low IL% better for BM",
        "feature": "ionizable_mol_pct",
        "expected": "important, lower values → higher efficacy",
    },
]


def check_sar_recovery(
    shap_abs: np.ndarray,
    feature_names: list[str],
) -> list[dict[str, str]]:
    """Check whether SHAP recovers known SARs.

    Args:
        shap_abs: Absolute SHAP values.
        feature_names: Feature names.

    Returns:
        List of SAR check results.
    """
    mean_shap = np.mean(shap_abs, axis=0)
    feat_to_shap = dict(zip(feature_names, mean_shap, strict=True))

    # Rank features
    sorted_feats = sorted(
        feat_to_shap.items(), key=lambda x: x[1], reverse=True
    )
    rank_map = {f: i + 1 for i, (f, _) in enumerate(sorted_feats)}
    n_feats = len(feature_names)
    top_third = n_feats // 3

    results: list[dict[str, str]] = []
    for sar in _KNOWN_SARS:
        feat = sar["feature"]
        if feat not in feat_to_shap:
            results.append({
                "sar": sar["name"],
                "verdict": "MISSING",
                "detail": f"Feature '{feat}' not in matrix",
            })
            continue

        rank = rank_map[feat]
        importance = feat_to_shap[feat]
        verdict = "AGREES" if rank <= top_third else "INCONCLUSIVE"

        results.append({
            "sar": sar["name"],
            "verdict": verdict,
            "detail": f"rank={rank}/{n_feats}, |SHAP|={importance:.4f}",
        })

    return results


def print_sar_report(results: list[dict[str, str]]) -> None:
    """Print SAR recovery report.

    Args:
        results: Output from check_sar_recovery.
    """
    print(f"\n{'='*60}")
    print("SAR Recovery Check (Validation Layer 4)")
    print(f"{'='*60}")
    for r in results:
        icon = {"AGREES": "✓", "INCONCLUSIVE": "?", "MISSING": "✗"}
        print(
            f"  {icon.get(r['verdict'], '?')} {r['sar']}: "
            f"{r['verdict']} — {r['detail']}"
        )
