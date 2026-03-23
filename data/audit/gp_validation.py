"""AUDIT 5: GP classification model validation.

Tests whether the Gaussian Process classifier used for gap scoring
is reliable. Four adversarial checks:
  1. Base rate — is the GP better than class-frequency baseline?
  2. Stability — does the GP give similar scores across random seeds?
  3. Known formulation — does the GP correctly score known formulations?
  4. Leave-one-out calibration — predicted vs actual for each training point.

Exploration script — no tests needed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.gaussian_process.kernels import Matern
from sklearn.preprocessing import StandardScaler

_ROOT = Path(__file__).resolve().parent.parent.parent
_FEATURES_PATH = _ROOT / "data" / "features" / "hsc_features.parquet"
_GAP_SCORES_PATH = _ROOT / "data" / "models" / "gap_scores.json"

# Inline gap formulation features (from score_gaps.py)
_GAP_FORMULATIONS: list[dict[str, Any]] = [
    {
        "name": "Gap #1: CD117/2B8 + DOTAP + C18-PEG",
        "ionizable_mol_pct": 35, "helper_mol_pct": 15,
        "cholesterol_mol_pct": 47.5, "peg_chain_numeric": 18,
        "hl_dotap": 1, "helper_is_cationic": 1,
        "receptor_cd117": 1, "dose_mg_per_kg": 0.3,
    },
    {
        "name": "Gap #2: LNP67 + C18-PEG swap",
        "ionizable_mol_pct": 35, "helper_mol_pct": 15,
        "cholesterol_mol_pct": 47.5, "peg_chain_numeric": 18,
        "hl_dotap": 1, "helper_is_cationic": 1,
        "receptor_cd117": 0, "dose_mg_per_kg": 1.0,
    },
    {
        "name": "Gap #3: Breda + C16GalCer",
        "ionizable_mol_pct": 50, "helper_mol_pct": 10,
        "cholesterol_mol_pct": 38.5, "peg_chain_numeric": 14,
        "hl_dotap": 0, "helper_is_cationic": 0,
        "receptor_cd117": 1, "dose_mg_per_kg": 0.25,
    },
    {
        "name": "Gap #5: Low-dose Ab + high-dose untargeted",
        "ionizable_mol_pct": 42, "helper_mol_pct": 12,
        "cholesterol_mol_pct": 43, "peg_chain_numeric": 14,
        "hl_dotap": 1, "helper_is_cationic": 1,
        "receptor_cd117": 1, "dose_mg_per_kg": 1.0,
    },
]

GP_FEATURES = [
    "ionizable_mol_pct", "receptor_cd117", "dose_mg_per_kg",
    "hl_dotap", "helper_mol_pct", "cholesterol_mol_pct",
    "peg_chain_numeric", "helper_is_cationic",
]


def _load_data() -> tuple[pd.DataFrame, np.ndarray]:
    """Load features and build binary target."""
    feats = pd.read_parquet(_FEATURES_PATH)
    binary: np.ndarray = (feats["target"] == 2).astype(int).values
    return feats, binary


def _get_X(feats: pd.DataFrame) -> np.ndarray:
    """Extract GP feature matrix."""
    gp_cols = [f for f in GP_FEATURES if f in feats.columns]
    result: np.ndarray = (
        feats[gp_cols].fillna(feats[gp_cols].median()).values
    )
    return result


def _test_base_rate(
    feats: pd.DataFrame, binary: np.ndarray,
) -> None:
    """Test 1: Base rate check.

    A useless model predicts the majority class. P(high) from GP
    should differ meaningfully from the base rate.
    """
    print("\n" + "=" * 70)
    print("TEST 1: BASE RATE CHECK")
    print("=" * 70)

    base_rate = float(binary.mean())
    print(f"  Base rate (fraction high): {base_rate:.3f}")
    print(f"  High: {binary.sum()}, Not-high: {len(binary) - binary.sum()}")

    # Fit GP and get training predictions
    X = _get_X(feats)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kernel = Matern(nu=2.5, length_scale_bounds=(1e-2, 1e4))
    gpc = GaussianProcessClassifier(
        kernel=kernel, n_restarts_optimizer=5, random_state=42,
    )
    gpc.fit(X_scaled, binary)

    train_proba = gpc.predict_proba(X_scaled)
    p_high_train = (
        train_proba[:, 1] if train_proba.shape[1] == 2
        else train_proba[:, 0]
    )

    print("\n  Training P(high) distribution:")
    print(f"    Mean: {p_high_train.mean():.3f}")
    print(f"    Std:  {p_high_train.std():.3f}")
    print(f"    Min:  {p_high_train.min():.3f}")
    print(f"    Max:  {p_high_train.max():.3f}")

    # Check gap scores
    with open(_GAP_SCORES_PATH) as f:
        gap_data = json.load(f)

    gap_scores = [g["p_high"] for g in gap_data["gap_formulations"]]
    print("\n  Gap formulation P(high) scores:")
    for g in gap_data["gap_formulations"]:
        diff = g["p_high"] - base_rate
        print(
            f"    {g['name'][:40]:40s}: "
            f"P={g['p_high']:.3f} "
            f"(base_rate + {diff:+.3f})"
        )

    all_close = all(
        abs(s - base_rate) < 0.1 for s in gap_scores
    )
    if all_close:
        print("\n  FLAG: All gap scores within 0.1 of base rate!")
        print("  The GP may not be discriminating effectively.")
    else:
        print(
            "\n  OK: Gap scores vary from base rate "
            "(GP is discriminating)."
        )


def _test_stability(feats: pd.DataFrame, binary: np.ndarray) -> None:
    """Test 2: Stability check across random seeds."""
    print("\n" + "=" * 70)
    print("TEST 2: STABILITY ACROSS RANDOM SEEDS")
    print("=" * 70)

    X = _get_X(feats)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Use gap formulation features from gap_scores.json
    with open(_GAP_SCORES_PATH) as f:
        gap_data = json.load(f)

    seeds = [0, 7, 42, 123, 999]
    all_scores: dict[str, list[float]] = {}
    for gap_info in gap_data["gap_formulations"]:
        all_scores[gap_info["name"]] = []

    for seed in seeds:
        kernel = Matern(nu=2.5, length_scale_bounds=(1e-2, 1e4))
        gpc = GaussianProcessClassifier(
            kernel=kernel, n_restarts_optimizer=5,
            random_state=seed,
        )
        gpc.fit(X_scaled, binary)

        gp_cols = [f for f in GP_FEATURES if f in feats.columns]
        for gap_dict, gap_info in zip(
            _GAP_FORMULATIONS,
            gap_data["gap_formulations"],
            strict=True,
        ):
            gap_vec = np.array(
                [[float(gap_dict.get(c, 0)) for c in gp_cols]],
            )
            gap_scaled = scaler.transform(gap_vec)
            proba = gpc.predict_proba(gap_scaled)
            p = float(
                proba[0, 1] if proba.shape[1] == 2
                else proba[0, 0]
            )
            all_scores[gap_info["name"]].append(p)

    print(f"  Seeds tested: {seeds}")
    hdr = f"{'Gap':35s} {'Mean':>7s} {'Std':>7s} {'Range':>12s}"
    print(hdr)
    print("-" * len(hdr))

    max_range = 0.0
    for name, scores in all_scores.items():
        arr = np.array(scores)
        score_range = float(arr.max() - arr.min())
        max_range = max(max_range, score_range)
        print(
            f"{name[:35]:35s} {arr.mean():7.3f} {arr.std():7.3f} "
            f"[{arr.min():.3f}-{arr.max():.3f}]"
        )

    if max_range > 0.15:
        print(
            f"\n  FLAG: Max range across seeds = {max_range:.3f}"
        )
        print(
            "  GP scores are UNSTABLE — sensitive to "
            "optimization seed."
        )
    else:
        print(
            f"\n  OK: Max range = {max_range:.3f} "
            "(stable across seeds)."
        )


def _test_known_formulations(
    feats: pd.DataFrame, binary: np.ndarray,
) -> None:
    """Test 3: Does the GP correctly score KNOWN formulations?

    Take known high-efficacy formulations from training data,
    predict them with the GP, and check calibration.
    """
    print("\n" + "=" * 70)
    print("TEST 3: KNOWN FORMULATION CHECK")
    print("=" * 70)

    X = _get_X(feats)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kernel = Matern(nu=2.5, length_scale_bounds=(1e-2, 1e4))
    gpc = GaussianProcessClassifier(
        kernel=kernel, n_restarts_optimizer=5, random_state=42,
    )
    gpc.fit(X_scaled, binary)

    train_proba = gpc.predict_proba(X_scaled)
    p_high = (
        train_proba[:, 1] if train_proba.shape[1] == 2
        else train_proba[:, 0]
    )

    # Check known high-efficacy formulations
    print("\n  Known HIGH-efficacy formulations (target=2):")
    high_mask = binary == 1
    high_indices = np.where(high_mask)[0]
    high_p = p_high[high_indices]

    for idx in high_indices[:10]:
        row = feats.iloc[idx]
        fm = row.get("formulation_id", "?")
        paper = row.get("paper", "?")
        print(f"    {fm} ({paper}): P(high)={p_high[idx]:.3f}")

    high_correct = (high_p > 0.5).sum()
    print(
        f"\n  Of {len(high_indices)} known HIGH formulations, "
        f"{high_correct} ({high_correct/max(len(high_indices),1)*100:.0f}%) "
        f"have P(high) > 0.5"
    )

    # Check known LOW-efficacy formulations
    print("\n  Known LOW-efficacy formulations (target=0):")
    low_mask = binary == 0
    low_indices = np.where(low_mask)[0]
    low_p = p_high[low_indices]

    for idx in low_indices[:5]:
        row = feats.iloc[idx]
        fm = row.get("formulation_id", "?")
        paper = row.get("paper", "?")
        print(f"    {fm} ({paper}): P(high)={p_high[idx]:.3f}")

    low_correct = (low_p < 0.5).sum()
    print(
        f"\n  Of {len(low_indices)} known LOW/MEDIUM formulations, "
        f"{low_correct} "
        f"({low_correct/max(len(low_indices),1)*100:.0f}%) "
        f"have P(high) < 0.5"
    )

    total_correct = int(high_correct) + int(low_correct)
    total = len(binary)
    print(
        f"\n  Overall training accuracy: "
        f"{total_correct}/{total} "
        f"({total_correct/max(total,1)*100:.0f}%)"
    )

    if total_correct / max(total, 1) > 0.95:
        print(
            "  FLAG: Training accuracy >95% — possible overfitting."
        )
        print(
            "  LOO check below will reveal true generalization."
        )


def _test_loo_calibration(
    feats: pd.DataFrame, binary: np.ndarray,
) -> None:
    """Test 4: Leave-one-out calibration.

    For each training point, train without it and predict.
    Check calibration: are P(high) predictions reliable?
    """
    print("\n" + "=" * 70)
    print("TEST 4: LEAVE-ONE-OUT CALIBRATION")
    print("=" * 70)

    X = _get_X(feats)
    n = len(X)
    print(f"  Running LOO for {n} data points...")

    loo_preds = np.zeros(n)
    for i in range(n):
        X_train = np.delete(X, i, axis=0)
        y_train = np.delete(binary, i)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_train)
        X_test = scaler.transform(X[i : i + 1])

        kernel = Matern(nu=2.5, length_scale_bounds=(1e-2, 1e4))
        gpc = GaussianProcessClassifier(
            kernel=kernel, n_restarts_optimizer=3,
            random_state=42,
        )
        gpc.fit(X_scaled, y_train)

        proba = gpc.predict_proba(X_test)
        loo_preds[i] = float(
            proba[0, 1] if proba.shape[1] == 2
            else proba[0, 0]
        )

    # Calibration analysis
    pred_classes = (loo_preds > 0.5).astype(int)
    accuracy = float((pred_classes == binary).mean())
    print(f"\n  LOO accuracy: {accuracy:.3f}")

    # Confusion matrix
    tp = int(((pred_classes == 1) & (binary == 1)).sum())
    fp = int(((pred_classes == 1) & (binary == 0)).sum())
    tn = int(((pred_classes == 0) & (binary == 0)).sum())
    fn = int(((pred_classes == 0) & (binary == 1)).sum())

    print("\n  Confusion matrix:")
    print(f"    TP={tp}, FP={fp}")
    print(f"    FN={fn}, TN={tn}")

    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    print(f"    Precision: {precision:.3f}")
    print(f"    Recall:    {recall:.3f}")

    # Calibration bins
    print("\n  Calibration bins:")
    bins = [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]
    for lo, hi in bins:
        mask = (loo_preds >= lo) & (loo_preds < hi)
        if mask.sum() == 0:
            continue
        actual_rate = float(binary[mask].mean())
        predicted_mid = (lo + hi) / 2
        n_in_bin = int(mask.sum())
        print(
            f"    P(high) in [{lo:.1f}, {hi:.1f}): "
            f"n={n_in_bin}, actual rate={actual_rate:.3f} "
            f"(expected ~{predicted_mid:.1f})"
        )

    # Brier score
    brier = float(np.mean((loo_preds - binary) ** 2))
    base_brier = float(np.mean((binary.mean() - binary) ** 2))
    print(f"\n  Brier score: {brier:.4f}")
    print(f"  Baseline Brier (always predict base rate): {base_brier:.4f}")
    if brier < base_brier:
        print("  OK: GP is better than baseline")
    else:
        print("  FLAG: GP is WORSE than baseline — model adds no value!")

    # Show worst LOO predictions
    print("\n  Worst LOO predictions (largest errors):")
    errors = np.abs(loo_preds - binary)
    worst_idx = np.argsort(errors)[-5:][::-1]
    for idx in worst_idx:
        row = feats.iloc[idx]
        fm = row.get("formulation_id", "?")
        paper = row.get("paper", "?")
        actual = "HIGH" if binary[idx] == 1 else "not-HIGH"
        print(
            f"    {fm} ({paper}): "
            f"P(high)={loo_preds[idx]:.3f}, actual={actual}"
        )


def main() -> None:
    """Run GP validation audit."""
    print("=" * 70)
    print("AUDIT 5: GP CLASSIFICATION MODEL VALIDATION")
    print("=" * 70)

    feats, binary = _load_data()
    print(
        f"  Feature matrix: {feats.shape[0]} rows x "
        f"{feats.shape[1]} cols"
    )
    print(
        f"  Binary target: {binary.sum()} high / "
        f"{len(binary)} total"
    )

    _test_base_rate(feats, binary)
    _test_stability(feats, binary)
    _test_known_formulations(feats, binary)
    _test_loo_calibration(feats, binary)


if __name__ == "__main__":
    main()
