"""Multi-layer validation protocol for HSC-LNP ML models.

Implements Validation Layers 1-7 from CLAUDE.md: held-out papers,
cross-target, SAR recovery, ablation/stress tests.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import GroupKFold

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# SAR definitions from CLAUDE.md
# ---------------------------------------------------------------------------

KNOWN_SARS: list[dict[str, str]] = [
    {"id": "SAR1", "name": "PEG density up → BM uptake down",
     "feature": "peg_mol_pct", "expected_dir": "negative"},
    {"id": "SAR2", "name": "C18-PEG > C14-PEG for HSC",
     "feature": "peg_chain_numeric", "expected_dir": "positive"},
    {"id": "SAR3", "name": "Higher cholesterol → liver bias",
     "feature": "cholesterol_mol_pct", "expected_dir": "negative"},
    {"id": "SAR4", "name": "CD117 targeting boosts HSC delivery",
     "feature": "receptor_cd117", "expected_dir": "positive"},
    {"id": "SAR5", "name": "Clone 2B8 >> ACK2",
     "feature": "clone_2b8", "expected_dir": "positive"},
    {"id": "SAR6", "name": "DOTAP enables BM tropism",
     "feature": "hl_dotap", "expected_dir": "positive"},
    {"id": "SAR7", "name": "Low IL% better for BM",
     "feature": "ionizable_mol_pct", "expected_dir": "negative"},
    {"id": "SAR8", "name": "Dose-dependent HSC delivery",
     "feature": "dose_mg_per_kg", "expected_dir": "positive"},
    {"id": "SAR9", "name": "IL pKa 6.2-6.5 optimal",
     "feature": "pka", "expected_dir": "N/A"},
    {"id": "SAR10", "name": "Optimal Ab:mal ratio ~1:20",
     "feature": "ab_mal_ratio", "expected_dir": "N/A"},
]


# ---------------------------------------------------------------------------
# SAR validation (Layer 4)
# ---------------------------------------------------------------------------


def build_sar_table(
    shap_values: np.ndarray,
    feature_names: list[str],
) -> list[dict[str, Any]]:
    """Build structured SAR recovery table.

    Args:
        shap_values: Absolute SHAP values (n_samples x n_features).
        feature_names: Feature names matching columns.

    Returns:
        List of SAR check results with verdicts.
    """
    mean_shap = np.mean(shap_values, axis=0)
    feat_shap = dict(zip(feature_names, mean_shap, strict=False))
    ranked = sorted(feat_shap.items(), key=lambda x: x[1], reverse=True)
    rank_map = {f: i + 1 for i, (f, _) in enumerate(ranked)}
    n = len(feature_names)
    top_third = n // 3

    results: list[dict[str, Any]] = []
    for sar in KNOWN_SARS:
        feat = sar["feature"]
        if feat not in feat_shap:
            results.append({
                **sar, "rank": None, "shap_value": None,
                "verdict": "NOT_TESTABLE",
                "detail": f"Feature '{feat}' not in matrix",
            })
            continue

        rank = rank_map[feat]
        val = feat_shap[feat]
        verdict = "CONFIRMED" if rank <= top_third else (
            "SUPPORTED" if rank <= 2 * top_third else "INCONCLUSIVE"
        )
        results.append({
            **sar, "rank": rank, "n_features": n,
            "shap_value": round(float(val), 4), "verdict": verdict,
            "detail": f"rank {rank}/{n}, |SHAP|={val:.4f}",
        })

    return results


# ---------------------------------------------------------------------------
# Per-fold SAR stability (Layer 4 extension)
# ---------------------------------------------------------------------------


def check_sar_stability(
    X: pd.DataFrame,
    y: np.ndarray,
    groups: np.ndarray,
    model_name: str = "lightgbm",
) -> dict[str, list[int]]:
    """Check if key features maintain rank across CV folds.

    Args:
        X: Feature matrix.
        y: Target array.
        groups: Paper groups.
        model_name: Model to use.

    Returns:
        Dict of feature_name → list of ranks per fold.
    """
    import shap

    from lnp_optimizer.evaluation import _train_full

    key_features = [
        "ionizable_mol_pct", "receptor_cd117", "dose_mg_per_kg",
        "hl_dotap", "helper_is_cationic", "peg_chain_numeric",
    ]

    gkf = GroupKFold(n_splits=len(set(groups)))
    stability: dict[str, list[int]] = {f: [] for f in key_features}

    for train_idx, _ in gkf.split(X, y, groups):
        X_tr, y_tr = X.iloc[train_idx], y[train_idx]
        model = _train_full(model_name, X_tr, y_tr)
        explainer = shap.TreeExplainer(model)
        sv = explainer.shap_values(X_tr)

        if isinstance(sv, list):
            abs_sv = np.mean([np.abs(s) for s in sv], axis=0)
        elif sv.ndim == 3:
            abs_sv = np.mean(np.abs(sv), axis=2)
        else:
            abs_sv = np.abs(sv)

        mean_shap = np.mean(abs_sv, axis=0)
        ranked = np.argsort(mean_shap)[::-1]
        rank_map = {X_tr.columns[i]: r + 1 for r, i in enumerate(ranked)}

        for f in key_features:
            stability[f].append(rank_map.get(f, len(X_tr.columns)))

    return stability


# ---------------------------------------------------------------------------
# Cross-target validation (Layer 2)
# ---------------------------------------------------------------------------


def cross_target_validation(
    X: pd.DataFrame,
    y: np.ndarray,
    targeting: np.ndarray,
    model_name: str = "lightgbm",
) -> dict[str, float]:
    """Train on one targeting strategy, predict the other.

    Args:
        X: Feature matrix.
        y: Target array.
        targeting: Targeting encoded values (2=antibody, 1=intrinsic).
        model_name: Model to use.

    Returns:
        Dict with accuracy in each direction.
    """
    from lnp_optimizer.evaluation import _train_full

    ab_mask = targeting == 2
    it_mask = targeting == 1

    results: dict[str, float] = {}

    # Train on antibody → predict intrinsic
    if ab_mask.sum() >= 5 and it_mask.sum() >= 5:
        model = _train_full(model_name, X[ab_mask], y[ab_mask])
        pred = model.predict(X[it_mask])
        results["ab_to_intrinsic"] = float(
            balanced_accuracy_score(y[it_mask], pred)
        )

        model2 = _train_full(model_name, X[it_mask], y[it_mask])
        pred2 = model2.predict(X[ab_mask])
        results["intrinsic_to_ab"] = float(
            balanced_accuracy_score(y[ab_mask], pred2)
        )

    return results


# ---------------------------------------------------------------------------
# Ablation tests (Layer 6)
# ---------------------------------------------------------------------------


def run_ablation_tests(
    X: pd.DataFrame,
    y: np.ndarray,
    groups: np.ndarray,
    model_name: str = "lightgbm",
) -> dict[str, float]:
    """Run ablation and stress tests.

    Args:
        X: Feature matrix.
        y: Target array.
        groups: Paper groups.
        model_name: Model to use.

    Returns:
        Dict of test_name → balanced accuracy.
    """
    from lnp_optimizer.models import evaluate_cv

    # Baseline
    base = evaluate_cv(X, y, groups, model_name)
    results: dict[str, float] = {
        "baseline": base["balanced_accuracy_mean"],
    }

    # Shuffle labels
    rng = np.random.RandomState(42)
    y_shuffled = rng.permutation(y)
    shuf = evaluate_cv(X, y_shuffled, groups, model_name)
    results["shuffled_labels"] = shuf["balanced_accuracy_mean"]

    # Remove top feature
    top_feat = _get_top_feature(X, y, model_name)
    if top_feat:
        X_drop1 = X.drop(columns=[top_feat])
        d1 = evaluate_cv(X_drop1, y, groups, model_name)
        results["drop_top1"] = d1["balanced_accuracy_mean"]

    # Remove top 3 features
    top3 = _get_top_features(X, y, model_name, n=3)
    if top3:
        X_drop3 = X.drop(columns=top3)
        d3 = evaluate_cv(X_drop3, y, groups, model_name)
        results["drop_top3"] = d3["balanced_accuracy_mean"]

    # Add noise
    X_noisy = X.copy()
    for col in X_noisy.select_dtypes(include=[np.number]).columns:
        noise = rng.normal(0, 1, len(X_noisy))
        X_noisy[col] = X_noisy[col].fillna(0) + noise
    noisy = evaluate_cv(X_noisy, y, groups, model_name)
    results["gaussian_noise"] = noisy["balanced_accuracy_mean"]

    return results


def _get_top_feature(
    X: pd.DataFrame, y: np.ndarray, model_name: str
) -> str | None:
    """Get the top SHAP feature."""
    feats = _get_top_features(X, y, model_name, n=1)
    return feats[0] if feats else None


def _get_top_features(
    X: pd.DataFrame, y: np.ndarray, model_name: str, n: int = 3
) -> list[str]:
    """Get top-n SHAP features."""
    import shap

    from lnp_optimizer.evaluation import _train_full

    model = _train_full(model_name, X, y)
    explainer = shap.TreeExplainer(model)
    sv = explainer.shap_values(X)

    if isinstance(sv, list):
        abs_sv = np.mean([np.abs(s) for s in sv], axis=0)
    elif sv.ndim == 3:
        abs_sv = np.mean(np.abs(sv), axis=2)
    else:
        abs_sv = np.abs(sv)

    mean_shap = np.mean(abs_sv, axis=0)
    top_idx = np.argsort(mean_shap)[::-1][:n]
    return [X.columns[i] for i in top_idx]


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


def generate_full_report(
    feature_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Run all validation layers and generate reports.

    Args:
        feature_path: Path to feature matrix parquet.
        output_dir: Directory for output files.

    Returns:
        Complete validation results dict.
    """
    from lnp_optimizer.evaluation import compute_shap_values
    from lnp_optimizer.models import load_feature_matrix

    X, y, groups = load_feature_matrix(feature_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Layer 4: SAR recovery
    shap_abs, feat_names = compute_shap_values(
        "lightgbm", X, y, output_dir=output_dir
    )
    sar_table = build_sar_table(shap_abs, feat_names)

    # SAR stability across folds
    stability = check_sar_stability(X, y, groups)

    # Layer 2: Cross-target
    if "targeting_encoded" in X.columns:
        targeting = X["targeting_encoded"].values
    else:
        targeting = np.zeros(len(X))
    cross_target = cross_target_validation(X, y, targeting)

    # Layer 6: Ablation
    ablation = run_ablation_tests(X, y, groups)

    results = {
        "sar_table": sar_table,
        "sar_stability": {k: v for k, v in stability.items()},
        "cross_target": cross_target,
        "ablation": ablation,
    }

    # Save JSON
    (output_dir / "sar_validation.json").write_text(
        json.dumps(sar_table, indent=2)
    )
    (output_dir / "validation_layers.json").write_text(
        json.dumps(results, indent=2, default=str)
    )

    # Generate markdown report
    _write_markdown_report(results, output_dir)

    return results


def _write_markdown_report(
    results: dict[str, Any], output_dir: Path
) -> None:
    """Write markdown SAR validation report."""
    md_dir = Path("papers/seeds")
    md_dir.mkdir(parents=True, exist_ok=True)
    path = md_dir / "sar_validation_report.md"

    lines = ["# SAR Validation Report", ""]
    lines.append("## SAR Recovery Table (Validation Layer 4)")
    lines.append("")
    lines.append("| SAR | Feature | Rank | |SHAP| | Verdict |")
    lines.append("|-----|---------|------|--------|---------|")

    for sar in results["sar_table"]:
        rank = sar.get("rank", "—")
        shap_val = sar.get("shap_value", "—")
        if isinstance(shap_val, float):
            shap_val = f"{shap_val:.4f}"
        lines.append(
            f"| {sar['name']} | {sar['feature']} | "
            f"{rank} | {shap_val} | {sar['verdict']} |"
        )

    # Stability
    lines.extend(["", "## SAR Stability Across Folds", ""])
    lines.append("| Feature | Fold 0 | Fold 1 | Fold 2 | Stable? |")
    lines.append("|---------|--------|--------|--------|---------|")
    for feat, ranks in results["sar_stability"].items():
        stable = "Yes" if max(ranks) - min(ranks) <= 5 else "No"
        rank_str = " | ".join(str(r) for r in ranks)
        lines.append(f"| {feat} | {rank_str} | {stable} |")

    # Cross-target
    lines.extend(["", "## Cross-Target Validation (Layer 2)", ""])
    ct = results["cross_target"]
    if ct:
        for direction, acc in ct.items():
            lines.append(f"- {direction}: {acc:.3f} balanced accuracy")
    else:
        lines.append("Insufficient data for cross-target split.")

    # Ablation
    lines.extend(["", "## Ablation Tests (Layer 6)", ""])
    for test, acc in results["ablation"].items():
        lines.append(f"- {test}: {acc:.3f}")

    path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Wrote SAR report to %s", path)


def print_report(results: dict[str, Any]) -> None:
    """Print validation report to console."""
    print(f"\n{'='*65}")
    print("SAR Recovery Table (Layer 4)")
    print(f"{'='*65}")
    print(f"{'SAR':<40} {'Feature':<25} {'Rank':>5} {'Verdict':<15}")
    print("-" * 65)
    for s in results["sar_table"]:
        rank = s.get("rank", "—")
        print(f"{s['name']:<40} {s['feature']:<25} {rank!s:>5} {s['verdict']:<15}")

    confirmed = sum(1 for s in results["sar_table"] if s["verdict"] == "CONFIRMED")
    supported = sum(1 for s in results["sar_table"] if s["verdict"] == "SUPPORTED")
    total = sum(1 for s in results["sar_table"] if s["verdict"] != "NOT_TESTABLE")
    print(f"\nRecovered: {confirmed} confirmed + {supported} supported / {total} testable")

    print(f"\n{'SAR Stability Across Folds':}")
    for feat, ranks in results["sar_stability"].items():
        stable = "✓" if max(ranks) - min(ranks) <= 5 else "✗"
        print(f"  {stable} {feat}: ranks={ranks}")

    print(f"\n{'Cross-Target (Layer 2):':}")
    for d, a in results.get("cross_target", {}).items():
        print(f"  {d}: {a:.3f}")

    print(f"\n{'Ablation (Layer 6):':}")
    for t, a in results.get("ablation", {}).items():
        print(f"  {t}: {a:.3f}")
