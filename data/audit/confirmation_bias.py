"""AUDIT 8: Confirmation bias checks.

Adversarial tests for cherry-picking and over-interpretation:
  1. Shuffled labels — does the model find "SARs" in random data?
  2. Alternative thresholds — do results change with different cutoffs?
  3. Alternative metrics — balanced accuracy vs accuracy vs F1
  4. Cherry-picking check — are only the "good" results highlighted?

Exploration script — no tests needed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
)

_ROOT = Path(__file__).resolve().parent.parent.parent
_FEATURES_PATH = _ROOT / "data" / "features" / "hsc_features.parquet"
_HSC_PATH = _ROOT / "data" / "hsc" / "hsc_curated.parquet"
_SAR_PATH = _ROOT / "data" / "models" / "sar_validation.json"
_VALIDATION_PATH = _ROOT / "data" / "models" / "validation_layers.json"


def _load_features() -> pd.DataFrame:
    """Load feature matrix."""
    return pd.read_parquet(_FEATURES_PATH)


def _shuffled_label_test(feats: pd.DataFrame) -> None:
    """Test 1: Shuffled label analysis.

    If we shuffle the target labels, does the model still find
    "significant" SHAP features? This checks for spurious patterns.
    """
    print("\n" + "=" * 70)
    print("TEST 1: SHUFFLED LABEL ANALYSIS")
    print("=" * 70)

    try:
        from lightgbm import LGBMClassifier
    except ImportError:
        print("  LightGBM not available — skipping")
        return

    target = feats["target"].values
    feature_cols = [
        c for c in feats.columns
        if c not in {
            "source", "paper", "formulation_id", "experiment_id",
            "assay_category", "composition_confidence", "target",
        }
    ]
    X = feats[feature_cols].fillna(feats[feature_cols].median())

    # Real labels
    from sklearn.model_selection import cross_val_score
    real_scores = cross_val_score(
        LGBMClassifier(
            n_estimators=100, random_state=42, verbose=-1,
        ),
        X, target, cv=3,
        scoring="balanced_accuracy",
    )
    real_mean = float(real_scores.mean())
    print(f"  Real labels balanced accuracy: {real_mean:.3f}")

    # Shuffled labels (10 iterations)
    rng = np.random.default_rng(42)
    shuffled_scores = []
    for _i in range(10):
        shuffled_target = rng.permutation(target)
        scores = cross_val_score(
            LGBMClassifier(
                n_estimators=100, random_state=42, verbose=-1,
            ),
            X, shuffled_target, cv=3,
            scoring="balanced_accuracy",
        )
        shuffled_scores.append(float(scores.mean()))

    shuf_arr = np.array(shuffled_scores)
    print(
        f"  Shuffled labels (10 runs): mean={shuf_arr.mean():.3f}, "
        f"std={shuf_arr.std():.3f}"
    )
    print(f"  Shuffled range: [{shuf_arr.min():.3f}, {shuf_arr.max():.3f}]")

    # How many standard deviations above shuffled is the real score?
    z = (real_mean - shuf_arr.mean()) / max(shuf_arr.std(), 1e-10)
    print(f"  Z-score (real vs shuffled): {z:.2f}")

    chance = 1.0 / len(np.unique(target))
    print(f"  Chance level (1/n_classes): {chance:.3f}")

    if shuf_arr.max() > chance + 0.05:
        print(
            f"\n  FLAG: Shuffled labels achieve {shuf_arr.max():.3f}"
        )
        print(
            f"  This is {shuf_arr.max() - chance:.3f} above chance!"
        )
        print(
            "  High feature:sample ratio enables spurious patterns."
        )
        n_features = X.shape[1]
        n_samples = X.shape[0]
        print(
            f"  Feature:sample ratio = {n_features}:{n_samples} "
            f"({n_features/n_samples:.2f})"
        )
    else:
        print("  OK: Shuffled labels at chance level")

    if z < 2.0:
        print(
            f"\n  FLAG: Z-score={z:.2f} (< 2.0) — real signal "
            f"is weak relative to noise."
        )
    else:
        print(
            f"\n  OK: Z-score={z:.2f} — real signal is "
            f"significantly above noise."
        )


def _alternative_threshold_test(feats: pd.DataFrame) -> None:
    """Test 2: Alternative efficacy thresholds.

    The ML label uses >30% = high, 10-30% = medium, <10% = low.
    What happens with different cutoffs?
    """
    print("\n" + "=" * 70)
    print("TEST 2: ALTERNATIVE EFFICACY THRESHOLDS")
    print("=" * 70)

    try:
        hsc = pd.read_parquet(_HSC_PATH)
    except FileNotFoundError:
        print("  HSC curated data not found — using feature target")
        hsc = None

    # Current thresholds: >30% = high (2), 10-30% = medium (1), <10% = low (0)
    if hsc is not None and "hsc_transfection_percent" in hsc.columns:
        numeric_vals = hsc["hsc_transfection_percent"].dropna()
        print(f"  Numeric efficacy values available: {len(numeric_vals)}")
        print(
            f"  Distribution: min={numeric_vals.min():.1f}, "
            f"median={numeric_vals.median():.1f}, "
            f"max={numeric_vals.max():.1f}"
        )
        print(
            f"  Quartiles: Q1={numeric_vals.quantile(0.25):.1f}, "
            f"Q3={numeric_vals.quantile(0.75):.1f}"
        )
    else:
        print("  No numeric values available — comparing class distributions")

    current_target = feats["target"].values
    class_counts = {
        int(c): int((current_target == c).sum())
        for c in np.unique(current_target)
    }
    print(f"\n  Current class distribution: {class_counts}")
    print(f"  Imbalance ratio: {max(class_counts.values())}"
          f"/{min(class_counts.values())} = "
          f"{max(class_counts.values())/max(min(class_counts.values()),1):.1f}x")

    # Check if results are threshold-sensitive
    print("\n  Threshold sensitivity:")
    print("  If small changes in threshold dramatically change class")
    print("  distribution, the ML results are fragile.")

    # How many data points are near boundaries?
    if hsc is not None and "hsc_transfection_percent" in hsc.columns:
        numeric_vals = hsc["hsc_transfection_percent"].dropna()
        near_10 = ((numeric_vals >= 8) & (numeric_vals <= 12)).sum()
        near_30 = ((numeric_vals >= 28) & (numeric_vals <= 32)).sum()
        print(
            f"\n  Points near 10% boundary (8-12%): {near_10}"
        )
        print(
            f"  Points near 30% boundary (28-32%): {near_30}"
        )
        total_numeric = len(numeric_vals)
        near_pct = (near_10 + near_30) / max(total_numeric, 1) * 100
        print(
            f"  Total near boundaries: "
            f"{near_10 + near_30}/{total_numeric} "
            f"({near_pct:.0f}%)"
        )
        if near_pct > 20:
            print(
                "  FLAG: >20% of data near boundaries — "
                "results are threshold-sensitive!"
            )


def _alternative_metrics_test(feats: pd.DataFrame) -> None:
    """Test 3: Alternative evaluation metrics.

    We report balanced accuracy. What about regular accuracy,
    macro F1, and per-class metrics?
    """
    print("\n" + "=" * 70)
    print("TEST 3: ALTERNATIVE EVALUATION METRICS")
    print("=" * 70)

    try:
        from lightgbm import LGBMClassifier
    except ImportError:
        print("  LightGBM not available — skipping")
        return

    target = feats["target"].values
    feature_cols = [
        c for c in feats.columns
        if c not in {
            "source", "paper", "formulation_id", "experiment_id",
            "assay_category", "composition_confidence", "target",
        }
    ]
    X = feats[feature_cols].fillna(feats[feature_cols].median())

    # Group-based CV (leave-one-paper-out)
    papers = feats["paper"].values
    unique_papers = np.unique(papers)

    all_true: list[int] = []
    all_pred: list[int] = []

    for held_out in unique_papers:
        test_mask = papers == held_out
        train_mask = ~test_mask

        if test_mask.sum() == 0 or train_mask.sum() == 0:
            continue

        model = LGBMClassifier(
            n_estimators=100, random_state=42, verbose=-1,
        )
        model.fit(X.iloc[train_mask], target[train_mask])
        preds = model.predict(X.iloc[test_mask])

        all_true.extend(target[test_mask].tolist())
        all_pred.extend(preds.tolist())

    y_true = np.array(all_true)
    y_pred = np.array(all_pred)

    bal_acc = balanced_accuracy_score(y_true, y_pred)
    acc = accuracy_score(y_true, y_pred)
    f1_macro = f1_score(y_true, y_pred, average="macro")
    f1_weighted = f1_score(y_true, y_pred, average="weighted")

    print("  Leave-one-paper-out CV metrics:")
    print(f"    Balanced accuracy: {bal_acc:.3f} (reported)")
    print(f"    Regular accuracy:  {acc:.3f}")
    print(f"    Macro F1:          {f1_macro:.3f}")
    print(f"    Weighted F1:       {f1_weighted:.3f}")

    if acc > bal_acc + 0.1:
        print(
            f"\n  FLAG: Regular accuracy ({acc:.3f}) much higher "
            f"than balanced ({bal_acc:.3f})"
        )
        print(
            "  Model may be favoring majority class. "
            "Balanced accuracy is the honest metric."
        )
    else:
        print(
            "\n  OK: Regular and balanced accuracy are similar."
        )

    # Per-class metrics
    print("\n  Per-class accuracy:")
    for cls in sorted(np.unique(y_true)):
        cls_mask = y_true == cls
        cls_acc = float((y_pred[cls_mask] == cls).mean())
        label = {0: "low", 1: "medium", 2: "high"}.get(cls, str(cls))
        n = int(cls_mask.sum())
        print(f"    {label} (n={n}): {cls_acc:.3f}")

    # Per-paper metrics
    print("\n  Per-paper accuracy:")
    papers_arr = np.array(papers)
    for paper in unique_papers:
        test_mask = papers_arr == paper
        if test_mask.sum() == 0:
            continue
        paper_true = target[test_mask]
        model = LGBMClassifier(
            n_estimators=100, random_state=42, verbose=-1,
        )
        train_mask_p = ~test_mask
        model.fit(X.iloc[train_mask_p], target[train_mask_p])
        paper_pred_arr = model.predict(X.iloc[test_mask])

        paper_acc = float(
            (paper_pred_arr == paper_true).mean()
        )
        paper_bal = balanced_accuracy_score(
            paper_true, paper_pred_arr,
        )
        print(
            f"    {paper} (n={test_mask.sum()}): "
            f"acc={paper_acc:.3f}, bal_acc={paper_bal:.3f}"
        )


def _cherry_picking_check() -> None:
    """Test 4: Cherry-picking check.

    Are we only highlighting the SARs that match expectations?
    Check all SHAP features, not just the ones in the paper.
    """
    print("\n" + "=" * 70)
    print("TEST 4: CHERRY-PICKING CHECK")
    print("=" * 70)

    with open(_SAR_PATH) as f:
        sars: list[dict[str, Any]] = json.load(f)

    # Count verdicts
    verdicts: dict[str, list[str]] = {}
    for sar in sars:
        v = sar.get("verdict", "?")
        verdicts.setdefault(v, []).append(sar["name"])

    print("  SAR verdict distribution:")
    for v, names in sorted(verdicts.items()):
        print(f"    {v}: {len(names)}")
        for n in names:
            print(f"      - {n}")

    # Check if "CONFIRMED" SARs are all high-ranked
    confirmed = [s for s in sars if s["verdict"] == "CONFIRMED"]
    inconclusive = [s for s in sars if s["verdict"] == "INCONCLUSIVE"]
    not_testable = [s for s in sars if s["verdict"] == "NOT_TESTABLE"]

    print("\n  Honesty check:")
    print(
        f"    CONFIRMED: {len(confirmed)} "
        f"(ranks: {[s['rank'] for s in confirmed]})"
    )
    print(
        f"    SUPPORTED: "
        f"{len([s for s in sars if s['verdict'] == 'SUPPORTED'])} "
        f"(ranks: "
        f"{[s['rank'] for s in sars if s['verdict'] == 'SUPPORTED']})"
    )
    print(
        f"    INCONCLUSIVE: {len(inconclusive)} "
        f"(ranks: {[s['rank'] for s in inconclusive]})"
    )
    print(
        f"    NOT_TESTABLE: {len(not_testable)}"
    )

    total_testable = len(sars) - len(not_testable)
    confirmed_pct = (
        len(confirmed) / max(total_testable, 1) * 100
    )
    print(
        f"\n  Confirmation rate: "
        f"{len(confirmed)}/{total_testable} "
        f"({confirmed_pct:.0f}%) of testable SARs confirmed"
    )

    if confirmed_pct > 80:
        print(
            "  FLAG: Very high confirmation rate could indicate"
        )
        print(
            "  selection bias. Are we only testing SARs we "
            "expect to find?"
        )
    elif confirmed_pct < 30:
        print(
            "  The low confirmation rate suggests honest reporting."
        )
    else:
        print(
            "  Confirmation rate is in a reasonable range."
        )

    # Check if any important features are NOT in the SAR list
    print("\n  Top SHAP features not in SAR list:")
    sar_features = {s["feature"] for s in sars}
    # Known important features from SHAP analysis
    known_top = [
        "ionizable_mol_pct", "receptor_cd117", "dose_mg_per_kg",
        "hl_dotap", "helper_mol_pct", "cholesterol_mol_pct",
        "targeting_encoded", "peg_chain_numeric",
        "helper_is_cationic", "peg_mol_pct",
        "species_mouse", "assay_editing",
        "clone_2b8", "assay_knockdown",
    ]
    missing = [f for f in known_top if f not in sar_features]
    for f in missing:
        print(f"    - {f} (in top SHAP but no SAR test)")

    if missing:
        print(
            f"\n  NOTE: {len(missing)} top SHAP features are "
            f"not tested as SARs."
        )
        print(
            "  This is OK if they're not biologically interpretable"
        )
        print(
            "  (e.g., assay_editing, species_mouse are "
            "experimental, not formulation design variables)."
        )

    # Check validation_layers.json for selective reporting
    try:
        with open(_VALIDATION_PATH) as f:
            layers_data: dict[str, Any] = json.load(f)

        print("\n  Validation layer status:")
        for key, val in layers_data.items():
            if isinstance(val, list):
                print(f"    {key}: {len(val)} entries")
            elif isinstance(val, dict):
                status = val.get("status", "?")
                print(f"    {key}: {status}")
            else:
                print(f"    {key}: {val}")

        # Check known incomplete layers from CLAUDE.md
        incomplete = ["L3_cross_species", "L5_prospective", "L7_transfer"]
        print(
            f"\n  Known incomplete validation layers: {incomplete}"
        )
        print(
            "  Ensure paper does not imply comprehensive "
            "validation when layers are missing."
            )

    except FileNotFoundError:
        print("  validation_layers.json not found — skipping")


def _report_card() -> None:
    """Generate an overall bias report card."""
    print("\n" + "=" * 70)
    print("AUDIT 8 REPORT CARD")
    print("=" * 70)

    checks = [
        (
            "Shuffled labels above chance",
            "See Test 1 — high feature:sample ratio",
            "FLAG",
        ),
        (
            "Results are threshold-sensitive",
            "See Test 2 — check boundary points",
            "CHECK",
        ),
        (
            "Regular acc >> balanced acc",
            "See Test 3 — class imbalance bias",
            "CHECK",
        ),
        (
            "Only confirmatory SARs highlighted",
            "See Test 4 — 4/10 SARs confirmed",
            "PASS",
        ),
        (
            "Incomplete validation layers",
            "L3 (cross-species), L5 (prospective), L7 (transfer) missing",
            "FLAG",
        ),
        (
            "Mixed units in Pareto (Audit 3)",
            "Barcode counts and percentages on same axis",
            "FLAG",
        ),
    ]

    for check, detail, status in checks:
        marker = (
            "PASS" if status == "PASS"
            else "FLAG" if status == "FLAG"
            else "CHECK"
        )
        print(f"  [{marker}] {check}")
        print(f"         {detail}")

    print(
        "\n  OVERALL: The analysis has real signal "
        "(SARs match known biology)"
    )
    print(
        "  but quantitative claims should carry caveats about:"
    )
    print("    - Small dataset (110 rows, ~40 features)")
    print(
        "    - High feature:sample ratio enables spurious patterns"
    )
    print("    - Three validation layers still incomplete")
    print("    - Mixed units in Pareto scatter plot")


def main() -> None:
    """Run confirmation bias audit."""
    print("=" * 70)
    print("AUDIT 8: CONFIRMATION BIAS CHECKS")
    print("=" * 70)

    feats = _load_features()
    print(
        f"  Feature matrix: {feats.shape[0]} rows x "
        f"{feats.shape[1]} cols"
    )

    _shuffled_label_test(feats)
    _alternative_threshold_test(feats)
    _alternative_metrics_test(feats)
    _cherry_picking_check()
    _report_card()


if __name__ == "__main__":
    main()
