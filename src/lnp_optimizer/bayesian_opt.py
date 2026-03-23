"""Bayesian optimization for LNP formulation recommendation.

Uses a Gaussian Process surrogate to recommend untested formulations
ranked by Expected Improvement, with calibrated uncertainty estimates.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

# Core GP features (from SHAP analysis)
GP_FEATURES = [
    "ionizable_mol_pct", "receptor_cd117", "dose_mg_per_kg",
    "hl_dotap", "helper_mol_pct", "cholesterol_mol_pct",
    "peg_chain_numeric", "helper_is_cationic",
]

# Formulation sanity constraints (from CLAUDE.md)
_CONSTRAINTS = {
    "ionizable_mol_pct": (30, 60),
    "helper_mol_pct": (5, 25),
    "cholesterol_mol_pct": (20, 50),
    "peg_mol_pct": (0.5, 5),
}


# ---------------------------------------------------------------------------
# Continuous target construction
# ---------------------------------------------------------------------------


def build_numeric_target(
    hsc_parquet: Path,
    feature_parquet: Path,
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Build targets from HSC data with real numeric values.

    Returns features for all 110 labeled rows, a continuous target
    (NaN where no numeric value), and a binary target (high=1).

    Args:
        hsc_parquet: Path to hsc_curated.parquet.
        feature_parquet: Path to hsc_features.parquet.

    Returns:
        Tuple of (feature_df, continuous_target, binary_target).
    """
    hsc = pd.read_parquet(hsc_parquet)
    feats = pd.read_parquet(feature_parquet)

    labeled = hsc[hsc["hsc_efficacy_class"].isin(["high", "medium", "low"])].copy()
    labeled = labeled.reset_index(drop=True)

    # Continuous: only real numeric values (no class midpoints)
    continuous = np.full(len(labeled), np.nan)
    for i, row in labeled.iterrows():
        val = row.get("hsc_transfection_percent")
        if pd.notna(val):
            continuous[int(i)] = float(val)  # type: ignore[arg-type]

    # Binary: high=1, not-high=0 (uses all rows)
    binary = (labeled["hsc_efficacy_class"] == "high").astype(int).values

    return feats, continuous, binary


# ---------------------------------------------------------------------------
# GP model
# ---------------------------------------------------------------------------


def fit_gp(
    feats: pd.DataFrame,
    target: np.ndarray,
    features: list[str] | None = None,
) -> tuple[GaussianProcessRegressor, StandardScaler, list[str]]:
    """Fit a Gaussian Process regressor on HSC data.

    Args:
        feats: Feature matrix DataFrame.
        target: Continuous target array.
        features: Feature columns to use (default: GP_FEATURES).

    Returns:
        Tuple of (fitted GP, fitted scaler, feature names used).
    """
    if features is None:
        features = [f for f in GP_FEATURES if f in feats.columns]

    X = feats[features].fillna(feats[features].median()).values
    y = target.copy()

    # Drop NaN targets
    valid = ~np.isnan(y)
    X = X[valid]
    y = y[valid]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kernel = Matern(nu=2.5) + WhiteKernel(noise_level=0.1)
    gp = GaussianProcessRegressor(
        kernel=kernel, n_restarts_optimizer=5,
        alpha=1e-6, random_state=42,
    )
    gp.fit(X_scaled, y)
    logger.info("GP fitted on %d points, %d features", len(X), len(features))

    return gp, scaler, features


def fit_gp_classifier(
    feats: pd.DataFrame,
    target: np.ndarray,
    features: list[str] | None = None,
) -> tuple[Any, StandardScaler, list[str]]:
    """Fit a GP classifier for P(high | features).

    Args:
        feats: Feature matrix DataFrame.
        target: Binary target (1=high, 0=not-high).
        features: Feature columns to use.

    Returns:
        Tuple of (fitted GPC, fitted scaler, feature names).
    """
    from sklearn.gaussian_process import GaussianProcessClassifier

    if features is None:
        features = [f for f in GP_FEATURES if f in feats.columns]

    X = feats[features].fillna(feats[features].median()).values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kernel = Matern(nu=2.5, length_scale_bounds=(1e-2, 1e4))
    gpc = GaussianProcessClassifier(
        kernel=kernel, n_restarts_optimizer=5, random_state=42,
    )
    gpc.fit(X_scaled, target)
    logger.info("GPC fitted on %d points, %d features", len(X), len(features))

    return gpc, scaler, features


# ---------------------------------------------------------------------------
# Acquisition functions
# ---------------------------------------------------------------------------


def expected_improvement(
    X: np.ndarray,
    gp: GaussianProcessRegressor,
    y_best: float,
    xi: float = 0.01,
) -> np.ndarray:
    """Compute Expected Improvement acquisition function.

    Args:
        X: Candidate points (already scaled).
        gp: Fitted GP model.
        y_best: Best observed value.
        xi: Exploration-exploitation tradeoff (small = exploit).

    Returns:
        EI values for each candidate.
    """
    mu, sigma = gp.predict(X, return_std=True)
    sigma = np.maximum(sigma, 1e-8)
    z = (mu - y_best - xi) / sigma
    ei = (mu - y_best - xi) * norm.cdf(z) + sigma * norm.pdf(z)
    return np.maximum(ei, 0)  # type: ignore[no-any-return]


def upper_confidence_bound(
    X: np.ndarray,
    gp: GaussianProcessRegressor,
    kappa: float = 2.0,
) -> np.ndarray:
    """Compute Upper Confidence Bound acquisition function.

    Args:
        X: Candidate points (already scaled).
        gp: Fitted GP model.
        kappa: Exploration parameter (higher = more exploration).

    Returns:
        UCB values for each candidate.
    """
    mu, sigma = gp.predict(X, return_std=True)
    return mu + kappa * sigma  # type: ignore[no-any-return]


def classify_acquisition(
    X: np.ndarray,
    gpc: Any,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Score candidates using classification GP.

    Ranks by P(high) * entropy (exploration-exploitation balance).

    Args:
        X: Candidate points (already scaled).
        gpc: Fitted GaussianProcessClassifier.

    Returns:
        Tuple of (p_high, entropy, acquisition_score).
    """
    proba = gpc.predict_proba(X)
    # P(high) is the probability of class 1
    p_high = proba[:, 1] if proba.shape[1] == 2 else proba[:, 0]
    entropy = -np.sum(proba * np.log(proba + 1e-10), axis=1)
    score = p_high * (1 + entropy)
    return p_high, entropy, score


# ---------------------------------------------------------------------------
# Candidate enumeration
# ---------------------------------------------------------------------------


def enumerate_candidates(
    existing_feats: pd.DataFrame,
    features: list[str],
) -> pd.DataFrame:
    """Generate feasible candidate formulations on a grid.

    Applies composition constraints and removes candidates that
    match existing formulations.

    Args:
        existing_feats: Current feature matrix.
        features: Feature column names.

    Returns:
        DataFrame of candidate formulations.
    """
    grid = _build_grid()
    grid = _filter_constraints(grid)
    grid = _remove_existing(grid, existing_feats, features)
    return grid


def _build_grid() -> pd.DataFrame:
    """Build combinatorial grid of formulation parameters."""
    from itertools import product

    il_vals = [30, 35, 40, 45, 50]
    hl_vals = [10, 15, 20, 25]
    peg_vals = [1.5, 2.5, 5.0]
    peg_chain = [14, 18]
    cd117 = [0, 1]
    dotap = [0, 1]
    doses = [0.5, 1.0, 2.0]

    rows = []
    for il, hl, peg, chain, cd, dot, dose in product(
        il_vals, hl_vals, peg_vals, peg_chain, cd117, dotap, doses
    ):
        chol = 100 - il - hl - peg
        rows.append({
            "ionizable_mol_pct": float(il),
            "helper_mol_pct": float(hl),
            "cholesterol_mol_pct": chol,
            "peg_mol_pct": float(peg),
            "peg_chain_numeric": float(chain),
            "receptor_cd117": cd,
            "hl_dotap": dot,
            "helper_is_cationic": dot,
            "dose_mg_per_kg": float(dose),
        })
    return pd.DataFrame(rows)


def _filter_constraints(grid: pd.DataFrame) -> pd.DataFrame:
    """Filter candidates by formulation sanity constraints."""
    mask = pd.Series(True, index=grid.index)
    for col, (lo, hi) in _CONSTRAINTS.items():
        if col in grid.columns:
            mask &= (grid[col] >= lo) & (grid[col] <= hi)
    return grid[mask].reset_index(drop=True)


def _remove_existing(
    grid: pd.DataFrame,
    existing: pd.DataFrame,
    features: list[str],
) -> pd.DataFrame:
    """Remove candidates that match existing formulations."""
    key_cols = [c for c in features if c in grid.columns and c in existing.columns]
    if not key_cols:
        return grid

    # Build set of existing feature tuples for fast lookup
    existing_tuples = set()
    for _, row in existing[key_cols].dropna().round(1).iterrows():
        existing_tuples.add(tuple(row.values))

    mask = []
    for _, row in grid[key_cols].round(1).iterrows():
        mask.append(tuple(row.values) not in existing_tuples)

    return grid[mask].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Recommendation pipeline
# ---------------------------------------------------------------------------


def recommend_formulations(
    hsc_parquet: Path,
    feature_parquet: Path,
    output_dir: Path | None = None,
    top_n: int = 20,
) -> dict[str, Any]:
    """Run both regression GP and classification GP pipelines.

    Args:
        hsc_parquet: Path to hsc_curated.parquet.
        feature_parquet: Path to hsc_features.parquet.
        output_dir: Optional directory for results.
        top_n: Number of top recommendations.

    Returns:
        Dict with regression and classification results.
    """
    feats, cont_target, bin_target = build_numeric_target(
        hsc_parquet, feature_parquet
    )

    # --- Regression GP (numeric-only, ~43 rows) ---
    reg_results = _run_regression_gp(feats, cont_target, top_n)

    # --- Classification GP (all rows, binary) ---
    cls_results = _run_classification_gp(feats, bin_target, top_n)

    results = {"regression": reg_results, "classification": cls_results}

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        top_reg = pd.DataFrame(reg_results["top_recommendations"])
        top_cls = pd.DataFrame(cls_results["top_recommendations"])
        top_reg.to_parquet(output_dir / "recommendations_regression.parquet", index=False)
        top_cls.to_parquet(output_dir / "recommendations_classification.parquet", index=False)
        summary = {
            "regression_cal": reg_results["calibration"],
            "classification_n": cls_results["n_points"],
            "n_candidates": reg_results["n_candidates"],
        }
        with (output_dir / "bayesian_opt_results.json").open("w") as f:
            json.dump(summary, f, indent=2)

    return results


def _run_regression_gp(
    feats: pd.DataFrame,
    target: np.ndarray,
    top_n: int,
) -> dict[str, Any]:
    """Run regression GP on numeric-only data."""
    gp, scaler, feat_names = fit_gp(feats, target)
    candidates = enumerate_candidates(feats, feat_names)
    X_cand = scaler.transform(candidates[feat_names].fillna(0).values)

    y_best = float(np.nanmax(target))
    mu, sigma = gp.predict(X_cand, return_std=True)
    ei = expected_improvement(X_cand, gp, y_best)

    candidates["gp_mean"] = mu
    candidates["gp_std"] = sigma
    candidates["ei"] = ei

    top = candidates.nlargest(top_n, "ei").reset_index(drop=True)
    cal = _leave_one_out_calibration(feats, target, feat_names)

    return {
        "top_recommendations": top.to_dict(orient="records"),
        "calibration": cal,
        "n_candidates": len(candidates),
        "y_best": y_best,
        "n_numeric": int((~np.isnan(target)).sum()),
    }


def _run_classification_gp(
    feats: pd.DataFrame,
    target: np.ndarray,
    top_n: int,
) -> dict[str, Any]:
    """Run classification GP on all labeled data."""
    gpc, scaler, feat_names = fit_gp_classifier(feats, target)
    candidates = enumerate_candidates(feats, feat_names)
    X_cand = scaler.transform(candidates[feat_names].fillna(0).values)

    p_high, entropy, score = classify_acquisition(X_cand, gpc)
    candidates["p_high"] = p_high
    candidates["entropy"] = entropy
    candidates["score"] = score

    top = candidates.nlargest(top_n, "score").reset_index(drop=True)

    return {
        "top_recommendations": top.to_dict(orient="records"),
        "n_points": int(len(target)),
    }


def _leave_one_out_calibration(
    feats: pd.DataFrame,
    target: np.ndarray,
    feat_names: list[str],
) -> dict[str, float]:
    """Leave-one-out GP calibration check."""
    X_all = feats[feat_names].fillna(feats[feat_names].median()).values
    valid = ~np.isnan(target)
    X = X_all[valid]
    y = target[valid]
    n = len(y)

    in_95ci = 0
    residuals = []

    for i in range(n):
        X_train = np.delete(X, i, axis=0)
        y_train = np.delete(y, i, axis=0)
        X_test = X[i:i + 1]

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)

        kernel = Matern(nu=2.5) + WhiteKernel(noise_level=0.1)
        gp = GaussianProcessRegressor(
            kernel=kernel, n_restarts_optimizer=2, alpha=1e-6,
        )
        gp.fit(X_train_s, y_train)
        mu, sigma = gp.predict(X_test_s, return_std=True)

        if y[i] >= mu[0] - 1.96 * sigma[0] and y[i] <= mu[0] + 1.96 * sigma[0]:
            in_95ci += 1
        residuals.append(abs(y[i] - mu[0]))

    coverage = in_95ci / n if n > 0 else 0
    mae = float(np.mean(residuals)) if residuals else 0

    return {
        "n_points": n,
        "coverage_95ci": round(coverage, 3),
        "mae": round(mae, 2),
    }


def _save_results(
    results: dict[str, Any],
    top: pd.DataFrame,
    output_dir: Path,
) -> None:
    """Save recommendation results."""
    output_dir.mkdir(parents=True, exist_ok=True)
    top.to_parquet(output_dir / "recommendations.parquet", index=False)

    # Serialize summary (avoid numpy types)
    summary = {
        "calibration": results["calibration"],
        "n_candidates": results["n_candidates"],
        "y_best": results["y_best"],
    }
    with (output_dir / "bayesian_opt_results.json").open("w") as f:
        json.dump(summary, f, indent=2)
    logger.info("Saved recommendations to %s", output_dir)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def print_recommendations(results: dict[str, Any]) -> None:
    """Print formatted recommendation report for both GP models."""
    if "regression" in results:
        _print_regression(results["regression"])
        _print_classification(results["classification"])
        return
    # Legacy single-model format
    _print_regression(results)


def _print_regression(results: dict[str, Any]) -> None:
    """Print regression GP results."""
    top = results["top_recommendations"]
    cal = results.get("calibration", {})

    print(f"\n{'='*90}")
    print(f"Top {len(top)} Formulation Recommendations by Expected Improvement")
    print(f"{'='*90}")

    header = (
        f"{'Rank':>4} | {'IL%':>4} | {'HL%':>4} | {'Chol%':>5} "
        f"| {'PEG%':>4} | {'Chain':>5} | {'CD117':>5} "
        f"| {'DOTAP':>5} | {'Dose':>5} | {'Mean':>6} "
        f"| {'Std':>5} | {'EI':>6}"
    )
    print(header)
    print("-" * 90)

    for i, rec in enumerate(top):
        cd117 = "Yes" if rec["receptor_cd117"] else "No"
        dotap = "Yes" if rec["hl_dotap"] else "No"
        chain = f"C{int(rec['peg_chain_numeric'])}"
        print(
            f"{i + 1:>4} | {rec['ionizable_mol_pct']:>4.0f} | "
            f"{rec['helper_mol_pct']:>4.0f} | "
            f"{rec['cholesterol_mol_pct']:>5.1f} | "
            f"{rec['peg_mol_pct']:>4.1f} | {chain:>5} | "
            f"{cd117:>5} | {dotap:>5} | "
            f"{rec['dose_mg_per_kg']:>5.1f} | "
            f"{rec['gp_mean']:>6.1f} | "
            f"{rec['gp_std']:>5.1f} | {rec['ei']:>6.2f}"
        )

    print("\nGP Calibration (LOO):")
    print(f"  95% CI coverage: {cal['coverage_95ci']:.1%}")
    print(f"  MAE: {cal['mae']:.1f}")
    print(f"  N points: {cal['n_points']}")


def _print_classification(results: dict[str, Any]) -> None:
    """Print classification GP results."""
    top = results["top_recommendations"]

    print(f"\n{'='*80}")
    print(f"Top {len(top)} by Classification GP: P(high) × (1 + entropy)")
    print(f"{'='*80}")

    header = (
        f"{'Rank':>4} | {'IL%':>4} | {'HL%':>4} | {'Chol%':>5} "
        f"| {'PEG%':>4} | {'Chain':>5} | {'CD117':>5} "
        f"| {'DOTAP':>5} | {'Dose':>5} | {'P(high)':>7} "
        f"| {'Entropy':>7} | {'Score':>6}"
    )
    print(header)
    print("-" * 80)

    for i, rec in enumerate(top[:20]):
        cd117 = "Yes" if rec["receptor_cd117"] else "No"
        dotap = "Yes" if rec["hl_dotap"] else "No"
        chain = f"C{int(rec['peg_chain_numeric'])}"
        print(
            f"{i + 1:>4} | {rec['ionizable_mol_pct']:>4.0f} | "
            f"{rec['helper_mol_pct']:>4.0f} | "
            f"{rec['cholesterol_mol_pct']:>5.1f} | "
            f"{rec['peg_mol_pct']:>4.1f} | {chain:>5} | "
            f"{cd117:>5} | {dotap:>5} | "
            f"{rec['dose_mg_per_kg']:>5.1f} | "
            f"{rec['p_high']:>7.3f} | "
            f"{rec['entropy']:>7.3f} | {rec['score']:>6.3f}"
        )
