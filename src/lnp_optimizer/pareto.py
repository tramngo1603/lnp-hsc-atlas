"""Multi-objective Pareto optimization: BM delivery vs liver de-targeting.

Jointly optimizes HSC delivery (maximize) and liver avoidance (maximize)
using dual GP classifiers on paired biodistribution data.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.gaussian_process.kernels import Matern
from sklearn.preprocessing import StandardScaler

from lnp_optimizer.bayesian_opt import (
    GP_FEATURES,
    enumerate_candidates,
)

logger = logging.getLogger(__name__)

# Published formulations for comparison
_PUBLISHED: list[dict[str, str | float]] = [
    {"name": "Breda CD117/LNP", "bm": 55.0, "liver": 76.0,
     "strategy": "antibody_conjugated"},
    {"name": "Kim LNP67 (0.5 mg/kg)", "bm": 20.9, "liver": 20.1,
     "strategy": "intrinsic_tropism"},
    {"name": "Kim LNP95", "bm": 4.4, "liver": 14.7,
     "strategy": "intrinsic_tropism"},
    {"name": "Kim LNP108", "bm": 8.8, "liver": 1.6,
     "strategy": "intrinsic_tropism"},
    {"name": "Kim LP01 (control)", "bm": 5.0, "liver": 42.4,
     "strategy": "none"},
]

# Thresholds for binary targets
BM_HIGH_THRESHOLD = 5.0  # >5% BM delivery = "high" (median of data)
LIVER_LOW_THRESHOLD = 5.0  # <5% liver delivery = "low"


# ---------------------------------------------------------------------------
# Paired dataset
# ---------------------------------------------------------------------------


def build_paired_dataset(
    hsc_parquet: Path,
    feature_parquet: Path,
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Build dataset with paired BM + liver delivery data.

    Args:
        hsc_parquet: Path to hsc_curated.parquet.
        feature_parquet: Path to hsc_features.parquet.

    Returns:
        Tuple of (features, bm_values, liver_values).
    """
    hsc = pd.read_parquet(hsc_parquet)
    feats = pd.read_parquet(feature_parquet)

    # Find rows in feature matrix that have paired data
    labeled = hsc[hsc["hsc_efficacy_class"].isin(
        ["high", "medium", "low"]
    )].reset_index(drop=True)
    paired_mask = (
        labeled["bone_marrow_percent"].notna()
        & labeled["liver_percent"].notna()
    )
    paired_idx = paired_mask[paired_mask].index

    paired_feats = feats.iloc[paired_idx].reset_index(drop=True)
    bm = labeled.loc[paired_idx, "bone_marrow_percent"].values.astype(float)
    liver = labeled.loc[paired_idx, "liver_percent"].values.astype(float)

    # Normalize Kim screen values to 0-100
    sources = labeled.loc[paired_idx, "source"].values
    for i in range(len(bm)):
        if sources[i] == "kim_2024_screen":
            bm[i] = bm[i] / 48.0 * 100
            liver[i] = liver[i] / 8.0 * 100

    logger.info("Paired dataset: %d records", len(paired_feats))
    return paired_feats, bm, liver


# ---------------------------------------------------------------------------
# Dual GP models
# ---------------------------------------------------------------------------


def fit_dual_gps(
    feats: pd.DataFrame,
    bm: np.ndarray,
    liver: np.ndarray,
    features: list[str] | None = None,
) -> tuple[Any, Any, StandardScaler, list[str]]:
    """Fit two GP classifiers: P(high BM) and P(low liver).

    Args:
        feats: Feature matrix for paired records.
        bm: BM delivery values (0-100).
        liver: Liver delivery values (0-100).
        features: Feature columns to use.

    Returns:
        Tuple of (gp_bm, gp_liver, scaler, feature_names).
    """
    if features is None:
        features = [f for f in GP_FEATURES if f in feats.columns]

    X = feats[features].fillna(feats[features].median()).values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    bm_binary = (bm > BM_HIGH_THRESHOLD).astype(int)
    liver_binary = (liver < LIVER_LOW_THRESHOLD).astype(int)

    kernel = Matern(nu=2.5, length_scale_bounds=(1e-2, 1e4))

    gp_bm = GaussianProcessClassifier(
        kernel=kernel, n_restarts_optimizer=3, random_state=42,
    )
    gp_bm.fit(X_scaled, bm_binary)

    gp_liver = GaussianProcessClassifier(
        kernel=kernel, n_restarts_optimizer=3, random_state=42,
    )
    gp_liver.fit(X_scaled, liver_binary)

    logger.info(
        "Dual GPs: BM high=%d/%d, liver low=%d/%d",
        bm_binary.sum(), len(bm_binary),
        liver_binary.sum(), len(liver_binary),
    )
    return gp_bm, gp_liver, scaler, features


# ---------------------------------------------------------------------------
# Pareto frontier
# ---------------------------------------------------------------------------


def compute_pareto_frontier(
    p_bm: np.ndarray,
    p_liver: np.ndarray,
) -> np.ndarray:
    """Find Pareto-optimal indices (maximize both objectives).

    Args:
        p_bm: P(high BM delivery) for each candidate.
        p_liver: P(low liver delivery) for each candidate.

    Returns:
        Boolean array marking Pareto-optimal candidates.
    """
    n = len(p_bm)
    is_pareto = np.ones(n, dtype=bool)

    for i in range(n):
        if not is_pareto[i]:
            continue
        for j in range(n):
            if i == j or not is_pareto[j]:
                continue
            # j dominates i if j is >= on both and > on at least one
            dominates = (
                p_bm[j] >= p_bm[i] and p_liver[j] >= p_liver[i]
                and (p_bm[j] > p_bm[i] or p_liver[j] > p_liver[i])
            )
            if dominates:
                is_pareto[i] = False
                break

    return is_pareto


def scalarized_score(
    p_bm: np.ndarray,
    p_liver: np.ndarray,
    w_bm: float = 0.5,
    w_liver: float = 0.5,
) -> np.ndarray:
    """Compute weighted scalarized objective.

    Args:
        p_bm: P(high BM delivery).
        p_liver: P(low liver delivery).
        w_bm: Weight for BM objective.
        w_liver: Weight for liver objective.

    Returns:
        Scalarized score for each candidate.
    """
    return w_bm * p_bm + w_liver * p_liver


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def run_pareto_optimization(
    hsc_parquet: Path,
    feature_parquet: Path,
    output_dir: Path | None = None,
    top_n: int = 10,
) -> dict[str, Any]:
    """Run multi-objective Pareto optimization pipeline.

    Args:
        hsc_parquet: Path to hsc_curated.parquet.
        feature_parquet: Path to hsc_features.parquet.
        output_dir: Optional output directory.
        top_n: Number of top recommendations.

    Returns:
        Dict with Pareto frontier, scores, comparisons.
    """
    feats, bm, liver = build_paired_dataset(hsc_parquet, feature_parquet)
    gp_bm, gp_liver, scaler, feat_names = fit_dual_gps(feats, bm, liver)

    # Score candidates
    all_feats = pd.read_parquet(feature_parquet)
    candidates = enumerate_candidates(all_feats, feat_names)
    X_cand = scaler.transform(candidates[feat_names].fillna(0).values)

    p_bm = _get_p_class1(gp_bm, X_cand)
    p_liver = _get_p_class1(gp_liver, X_cand)

    candidates["p_high_bm"] = p_bm
    candidates["p_low_liver"] = p_liver
    candidates["combined_score"] = scalarized_score(p_bm, p_liver)

    # Pareto frontier
    is_pareto = compute_pareto_frontier(p_bm, p_liver)
    candidates["is_pareto"] = is_pareto

    # Top by combined score
    top = candidates.nlargest(top_n, "combined_score").reset_index(drop=True)
    pareto_df = candidates[candidates["is_pareto"]].reset_index(drop=True)

    # Published comparison
    published = _score_published(gp_bm, gp_liver, scaler, feat_names, feats)

    results = {
        "n_paired": len(feats),
        "n_candidates": len(candidates),
        "n_pareto": int(is_pareto.sum()),
        "top_recommendations": top.to_dict(orient="records"),
        "published_comparison": published,
        "bm_threshold": BM_HIGH_THRESHOLD,
        "liver_threshold": LIVER_LOW_THRESHOLD,
    }

    if output_dir:
        _save_pareto(results, top, pareto_df, feats, bm, liver, output_dir)

    return results


def _get_p_class1(gpc: Any, X: np.ndarray) -> np.ndarray:
    """Get P(class=1) from a GPC."""
    proba = gpc.predict_proba(X)
    return proba[:, 1] if proba.shape[1] == 2 else proba[:, 0]  # type: ignore[no-any-return]


def _score_published(
    gp_bm: Any,
    gp_liver: Any,
    scaler: StandardScaler,
    feat_names: list[str],
    feats: pd.DataFrame,
) -> list[dict[str, Any]]:
    """Score published formulations against the Pareto frontier."""
    results = []
    for pub in _PUBLISHED:
        results.append({
            "name": pub["name"],
            "actual_bm": pub["bm"],
            "actual_liver": pub["liver"],
            "bm_above_threshold": float(pub["bm"]) > BM_HIGH_THRESHOLD,
            "liver_below_threshold": float(pub["liver"]) < LIVER_LOW_THRESHOLD,
            "strategy": pub["strategy"],
        })
    return results


def _save_pareto(
    results: dict[str, Any],
    top: pd.DataFrame,
    pareto_df: pd.DataFrame,
    feats: pd.DataFrame,
    bm: np.ndarray,
    liver: np.ndarray,
    output_dir: Path,
) -> None:
    """Save Pareto results to files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    pareto_df.to_parquet(output_dir / "pareto_frontier.parquet", index=False)

    paired = feats.copy()
    paired["bm_delivery"] = bm
    paired["liver_delivery"] = liver
    paired.to_parquet(output_dir / "paired_delivery.parquet", index=False)

    summary = {
        "n_paired": results["n_paired"],
        "n_candidates": results["n_candidates"],
        "n_pareto": results["n_pareto"],
        "published_comparison": results["published_comparison"],
    }
    with (output_dir / "pareto_results.json").open("w") as f:
        json.dump(summary, f, indent=2, default=str)

    logger.info("Saved Pareto results to %s", output_dir)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def print_pareto_report(results: dict[str, Any]) -> None:
    """Print Pareto optimization report."""
    print(f"\n{'='*80}")
    print("Multi-Objective Optimization: BM Delivery vs Liver De-targeting")
    print(f"{'='*80}")
    print(f"Paired data points: {results['n_paired']}")
    print(f"Candidates evaluated: {results['n_candidates']}")
    print(f"Pareto-optimal: {results['n_pareto']}")

    _print_top_recs(results["top_recommendations"])
    _print_published(results["published_comparison"])


def _print_top_recs(top: list[dict[str, Any]]) -> None:
    """Print top recommendations table."""
    print(f"\n{'Top 10 by Combined Score':}")
    header = (
        f"{'Rank':>4} | {'IL%':>4} | {'HL%':>4} | {'Chol%':>5} "
        f"| {'PEG%':>4} | {'Chain':>5} | {'CD117':>5} "
        f"| {'DOTAP':>5} | {'P(BM)':>6} | {'P(!Liv)':>7} "
        f"| {'Score':>6} | {'Pareto':>6}"
    )
    print(header)
    print("-" * 80)

    for i, rec in enumerate(top[:10]):
        cd117 = "Yes" if rec.get("receptor_cd117") else "No"
        dotap = "Yes" if rec.get("hl_dotap") else "No"
        chain = f"C{int(rec.get('peg_chain_numeric', 14))}"
        pareto = "*" if rec.get("is_pareto") else ""
        print(
            f"{i + 1:>4} | {rec['ionizable_mol_pct']:>4.0f} | "
            f"{rec['helper_mol_pct']:>4.0f} | "
            f"{rec['cholesterol_mol_pct']:>5.1f} | "
            f"{rec['peg_mol_pct']:>4.1f} | {chain:>5} | "
            f"{cd117:>5} | {dotap:>5} | "
            f"{rec['p_high_bm']:>6.3f} | "
            f"{rec['p_low_liver']:>7.3f} | "
            f"{rec['combined_score']:>6.3f} | {pareto:>6}"
        )


def _print_published(published: list[dict[str, Any]]) -> None:
    """Print published formulation comparison."""
    print("\nPublished formulations:")
    print(f"  {'Name':<30} {'BM%':>6} {'Liver%':>7} {'BM>5%':>6} {'Liv<5%':>7}")
    print("  " + "-" * 60)
    for p in published:
        bm_ok = "Yes" if p["bm_above_threshold"] else "No"
        liver_ok = "Yes" if p["liver_below_threshold"] else "No"
        print(
            f"  {p['name']:<30} {p['actual_bm']:>6.1f} "
            f"{p['actual_liver']:>7.1f} {bm_ok:>6} {liver_ok:>7}"
        )
