"""Transfer learning from external LNP datasets to HSC prediction.

Pretrains on LNPDB/LANCE/AGILE (24K rows) to learn general LNP
formulation physics, then fine-tunes on HSC data (135 rows).
Two approaches: (1) pretrain + continue training, (2) stacked
generalization (external predictions as features).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score

from lnp_optimizer.features import (
    build_formulation_features,
    build_molecular_features,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Feature alignment
# ---------------------------------------------------------------------------

# Features shared between external and HSC datasets
SHARED_FEATURES = [
    "ionizable_mol_pct", "helper_mol_pct", "cholesterol_mol_pct",
    "peg_mol_pct", "il_to_helper_ratio", "il_to_chol_ratio",
    "chol_to_helper_ratio", "helper_is_cationic",
]

# Molecular descriptor features (prefix il_)
MOL_FEATURES = [
    "il_molecular_weight", "il_logp", "il_tpsa", "il_hbd", "il_hba",
    "il_rotatable_bonds", "il_num_rings", "il_heavy_atom_count",
]


def prepare_external_data(
    unified_parquet: Path,
    expt_filter: str = "luminescence",
) -> tuple[pd.DataFrame, pd.Series]:
    """Load and featurize external data for pretraining.

    Args:
        unified_parquet: Path to unified training_data.parquet.
        expt_filter: Substring to filter expt_unit (luminescence).

    Returns:
        Tuple of (feature_df, target_series).
    """
    raw = pd.read_parquet(unified_parquet)

    # Filter to relevant experiment type
    mask = raw["expt_unit"].str.contains(expt_filter, case=False, na=False)
    filtered = raw[mask].copy().reset_index(drop=True)
    logger.info("External data: %d/%d rows after filter '%s'", len(filtered), len(raw), expt_filter)

    # Build features
    form_feats = build_formulation_features(filtered)
    mol_feats = build_molecular_features(filtered, include_fp=False)
    feats = pd.concat([form_feats, mol_feats], axis=1)

    # Target: experiment_value (continuous)
    target = pd.to_numeric(filtered.get("experiment_value"), errors="coerce")

    # Drop rows with no target or no features
    valid = target.notna() & feats[SHARED_FEATURES[:4]].notna().any(axis=1)
    feats = feats[valid].reset_index(drop=True)
    target = target[valid].reset_index(drop=True)

    return feats, target


def align_features(
    ext_feats: pd.DataFrame,
    hsc_feats: pd.DataFrame,
) -> list[str]:
    """Find feature columns shared between external and HSC data.

    Args:
        ext_feats: Feature DataFrame from external data.
        hsc_feats: Feature DataFrame from HSC data.

    Returns:
        List of shared feature column names.
    """
    shared = sorted(set(ext_feats.columns) & set(hsc_feats.columns))
    # Exclude metadata and target
    exclude = {"source", "paper", "formulation_id", "experiment_id",
               "target", "composition_confidence", "assay_category"}
    return [c for c in shared if c not in exclude]


# ---------------------------------------------------------------------------
# Transfer approach 1: Pretrain + continue training
# ---------------------------------------------------------------------------


def transfer_continue_training(
    ext_feats: pd.DataFrame,
    ext_target: pd.Series,  # type: ignore[type-arg]
    hsc_feats: pd.DataFrame,
    hsc_target: np.ndarray,
    shared_cols: list[str],
    train_idx: np.ndarray,
    test_idx: np.ndarray,
) -> dict[str, Any]:
    """Pretrain on external, continue training on HSC.

    Args:
        ext_feats: External feature matrix.
        ext_target: External regression target.
        hsc_feats: HSC feature matrix (all columns).
        hsc_target: HSC classification target (0/1/2).
        shared_cols: Columns shared between external and HSC.
        train_idx: HSC training indices.
        test_idx: HSC test indices.

    Returns:
        Dict with predictions and metrics.
    """
    import xgboost as xgb

    # Phase 1: Pretrain on external data (regression)
    ext_X = ext_feats[shared_cols].fillna(0).values
    ext_y = ext_target.fillna(0).values

    pretrain = xgb.XGBRegressor(
        n_estimators=100, max_depth=4, learning_rate=0.1,
        subsample=0.8, colsample_bytree=0.8, random_state=42,
    )
    pretrain.fit(ext_X, ext_y)
    logger.info("Pretrained on %d external rows", len(ext_X))

    # Phase 2: Generate external predictions as feature
    hsc_shared = hsc_feats[shared_cols].fillna(0).values
    ext_preds = pretrain.predict(hsc_shared)

    # Phase 3: Train HSC classifier with augmented features
    hsc_all_cols = [c for c in hsc_feats.columns if c not in {
        "source", "paper", "formulation_id", "experiment_id",
        "target", "composition_confidence", "assay_category",
    }]
    hsc_X = hsc_feats[hsc_all_cols].fillna(0).values
    hsc_X_aug = np.column_stack([hsc_X, ext_preds])

    X_train = hsc_X_aug[train_idx]
    X_test = hsc_X_aug[test_idx]
    y_train = hsc_target[train_idx]
    y_test = hsc_target[test_idx]

    clf = xgb.XGBClassifier(
        n_estimators=100, max_depth=3, learning_rate=0.1,
        num_class=3, objective="multi:softmax",
        random_state=42, eval_metric="mlogloss",
    )
    clf.fit(X_train, y_train)
    preds = clf.predict(X_test)
    acc = balanced_accuracy_score(y_test, preds)

    return {"y_test": y_test, "y_pred": preds, "bal_acc": acc}


# ---------------------------------------------------------------------------
# Transfer approach 2: Stacked generalization
# ---------------------------------------------------------------------------


def transfer_stacked(
    ext_feats: pd.DataFrame,
    ext_target: pd.Series,  # type: ignore[type-arg]
    hsc_feats: pd.DataFrame,
    hsc_target: np.ndarray,
    shared_cols: list[str],
    train_idx: np.ndarray,
    test_idx: np.ndarray,
) -> dict[str, Any]:
    """Stacked generalization: external predictions as feature.

    Args:
        ext_feats: External feature matrix.
        ext_target: External regression target.
        hsc_feats: HSC feature matrix.
        hsc_target: HSC classification target.
        shared_cols: Shared feature columns.
        train_idx: HSC training indices.
        test_idx: HSC test indices.

    Returns:
        Dict with predictions and metrics.
    """
    from lightgbm import LGBMClassifier, LGBMRegressor

    # Train external regressor
    ext_X = ext_feats[shared_cols].fillna(0).values
    ext_y = ext_target.fillna(0).values

    ext_model = LGBMRegressor(
        n_estimators=100, max_depth=4, learning_rate=0.1,
        subsample=0.8, colsample_bytree=0.8, random_state=42,
        verbose=-1,
    )
    ext_model.fit(ext_X, ext_y)

    # Add external prediction as feature
    hsc_shared = hsc_feats[shared_cols].fillna(0).values
    ext_preds = ext_model.predict(hsc_shared)

    hsc_all_cols = _feature_cols(hsc_feats)
    hsc_X = hsc_feats[hsc_all_cols].fillna(0).values
    hsc_X_aug = np.column_stack([hsc_X, ext_preds])

    X_train = hsc_X_aug[train_idx]
    X_test = hsc_X_aug[test_idx]
    y_train = hsc_target[train_idx]
    y_test = hsc_target[test_idx]

    clf = LGBMClassifier(
        n_estimators=100, max_depth=3, learning_rate=0.1,
        num_class=3, objective="multiclass", random_state=42,
        verbose=-1,
    )
    clf.fit(X_train, y_train)
    preds = clf.predict(X_test)
    acc = balanced_accuracy_score(y_test, preds)

    return {"y_test": y_test, "y_pred": preds, "bal_acc": acc}


def _feature_cols(df: pd.DataFrame) -> list[str]:
    """Get feature columns (exclude metadata)."""
    exclude = {"source", "paper", "formulation_id", "experiment_id",
               "target", "composition_confidence", "assay_category"}
    return [c for c in df.columns if c not in exclude]


# ---------------------------------------------------------------------------
# Learning curve (Validation Layer 7)
# ---------------------------------------------------------------------------


def learning_curve(
    ext_feats: pd.DataFrame,
    ext_target: pd.Series,  # type: ignore[type-arg]
    hsc_feats: pd.DataFrame,
    hsc_target: np.ndarray,
    shared_cols: list[str],
    train_idx: np.ndarray,
    test_idx: np.ndarray,
    n_values: list[int] | None = None,
    n_repeats: int = 5,
) -> pd.DataFrame:
    """Generate learning curve: accuracy vs N_hsc.

    Args:
        ext_feats: External features.
        ext_target: External target.
        hsc_feats: HSC features.
        hsc_target: HSC classification target.
        shared_cols: Shared feature columns.
        train_idx: HSC training indices.
        test_idx: HSC test indices.
        n_values: List of training set sizes to evaluate.
        n_repeats: Number of random subsamples per N.

    Returns:
        DataFrame with columns [n, hsc_only_acc, transfer_acc].
    """
    import xgboost as xgb

    if n_values is None:
        max_n = len(train_idx)
        n_values = [n for n in [10, 20, 30, 50, 80, max_n] if n <= max_n]

    rng = np.random.RandomState(42)
    results: list[dict[str, Any]] = []

    # Precompute external model predictions
    ext_X = ext_feats[shared_cols].fillna(0).values
    ext_y = ext_target.fillna(0).values
    ext_model = xgb.XGBRegressor(
        n_estimators=100, max_depth=4, learning_rate=0.1,
        random_state=42,
    )
    ext_model.fit(ext_X, ext_y)

    hsc_shared = hsc_feats[shared_cols].fillna(0).values
    ext_preds = ext_model.predict(hsc_shared)

    hsc_all_cols = _feature_cols(hsc_feats)
    hsc_X = hsc_feats[hsc_all_cols].fillna(0).values
    hsc_X_aug = np.column_stack([hsc_X, ext_preds])

    y_test = hsc_target[test_idx]
    X_test_base = hsc_X[test_idx]
    X_test_aug = hsc_X_aug[test_idx]

    for n in n_values:
        for _ in range(n_repeats):
            sub = rng.choice(train_idx, size=min(n, len(train_idx)), replace=False)
            base_acc = _train_eval_xgb(hsc_X[sub], hsc_target[sub], X_test_base, y_test)
            aug_acc = _train_eval_xgb(hsc_X_aug[sub], hsc_target[sub], X_test_aug, y_test)
            results.append({"n": n, "hsc_only_acc": base_acc, "transfer_acc": aug_acc})

    return pd.DataFrame(results)


def _train_eval_xgb(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
) -> float:
    """Train XGBoost and return balanced accuracy."""
    import xgboost as xgb

    clf = xgb.XGBClassifier(
        n_estimators=50, max_depth=3, learning_rate=0.1,
        num_class=3, objective="multi:softmax",
        random_state=42, eval_metric="mlogloss",
    )
    clf.fit(X_train, y_train)
    preds = clf.predict(X_test)
    return float(balanced_accuracy_score(y_test, preds))


# ---------------------------------------------------------------------------
# Run all transfer experiments
# ---------------------------------------------------------------------------


def run_transfer_experiments(
    hsc_parquet: Path,
    unified_parquet: Path,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Run all transfer learning experiments.

    Args:
        hsc_parquet: Path to HSC feature matrix parquet.
        unified_parquet: Path to unified external data parquet.
        output_dir: Optional directory for results.

    Returns:
        Dict with all results.
    """
    from lnp_optimizer.feature_matrix import get_paper_groupkfold_splits

    # Load HSC data
    hsc_df = pd.read_parquet(hsc_parquet)
    hsc_target = hsc_df["target"].values
    splits = get_paper_groupkfold_splits(hsc_df, n_splits=3)

    # Load external data
    ext_feats, ext_target = prepare_external_data(unified_parquet)
    shared_cols = align_features(ext_feats, hsc_df)
    logger.info("Shared features: %d — %s", len(shared_cols), shared_cols)

    # Run per-fold
    results = _run_per_fold(
        ext_feats, ext_target, hsc_df, hsc_target, shared_cols, splits
    )

    # Learning curve on largest fold
    train_idx, test_idx = max(splits, key=lambda s: len(s[0]))
    lc = learning_curve(
        ext_feats, ext_target, hsc_df, hsc_target,
        shared_cols, train_idx, test_idx,
    )

    results["learning_curve"] = lc.groupby("n").mean().to_dict()

    if output_dir:
        _save_results(results, lc, output_dir)

    return results


def _run_per_fold(
    ext_feats: pd.DataFrame,
    ext_target: pd.Series,  # type: ignore[type-arg]
    hsc_df: pd.DataFrame,
    hsc_target: np.ndarray,
    shared_cols: list[str],
    splits: list[tuple[np.ndarray, np.ndarray]],
) -> dict[str, Any]:
    """Run transfer experiments across CV folds."""
    cont_accs: list[float] = []
    stack_accs: list[float] = []

    for fold, (train_idx, test_idx) in enumerate(splits):
        held_out = set(hsc_df.iloc[test_idx]["paper"].unique())
        logger.info("Fold %d: held out %s", fold, held_out)

        cont = transfer_continue_training(
            ext_feats, ext_target, hsc_df, hsc_target,
            shared_cols, train_idx, test_idx,
        )
        cont_accs.append(cont["bal_acc"])

        stack = transfer_stacked(
            ext_feats, ext_target, hsc_df, hsc_target,
            shared_cols, train_idx, test_idx,
        )
        stack_accs.append(stack["bal_acc"])

        logger.info(
            "  Continue: %.3f, Stacked: %.3f",
            cont["bal_acc"], stack["bal_acc"],
        )

    return {
        "continue_training": {
            "per_fold": cont_accs,
            "mean": float(np.mean(cont_accs)),
        },
        "stacked": {
            "per_fold": stack_accs,
            "mean": float(np.mean(stack_accs)),
        },
    }


def _save_results(
    results: dict[str, Any],
    lc: pd.DataFrame,
    output_dir: Path,
) -> None:
    """Save results to JSON and parquet."""
    import json

    output_dir.mkdir(parents=True, exist_ok=True)
    # Save learning curve
    lc.to_parquet(output_dir / "learning_curve.parquet", index=False)
    # Save summary (convert numpy types)
    summary = {
        k: v for k, v in results.items() if k != "learning_curve"
    }
    with (output_dir / "transfer_results.json").open("w") as f:
        json.dump(summary, f, indent=2, default=str)
    logger.info("Saved transfer results to %s", output_dir)


def print_comparison(
    results: dict[str, Any],
    baseline_xgb: float = 0.479,
    baseline_lgbm: float = 0.467,
) -> None:
    """Print transfer learning comparison table.

    Args:
        results: Output from run_transfer_experiments.
        baseline_xgb: Baseline XGBoost balanced accuracy.
        baseline_lgbm: Baseline LightGBM balanced accuracy.
    """
    print(f"\n{'='*65}")
    print("Transfer Learning Comparison")
    print(f"{'='*65}")
    print(f"{'Approach':<35} {'Bal.Acc':>8} {'vs XGB':>8} {'vs LGBM':>8}")
    print("-" * 65)
    print(f"{'HSC-only XGBoost (baseline)':<35} {baseline_xgb:>8.3f} {'—':>8} {'—':>8}")
    print(f"{'HSC-only LightGBM (baseline)':<35} {baseline_lgbm:>8.3f} {'—':>8} {'—':>8}")

    cont = results.get("continue_training", {}).get("mean", 0)
    stack = results.get("stacked", {}).get("mean", 0)

    diff_xgb_c = cont - baseline_xgb
    diff_xgb_s = stack - baseline_xgb
    print(f"{'Transfer (pretrain+continue)':<35} {cont:>8.3f} {diff_xgb_c:>+8.3f} {'':>8}")
    print(f"{'Transfer (stacked)':<35} {stack:>8.3f} {diff_xgb_s:>+8.3f} {'':>8}")

    # Learning curve summary
    lc = results.get("learning_curve", {})
    if lc:
        print(f"\n{'Learning Curve (mean over repeats)':}")
        hsc_acc = lc.get("hsc_only_acc", {})
        tf_acc = lc.get("transfer_acc", {})
        print(f"{'N':>6} {'HSC-only':>10} {'Transfer':>10} {'Delta':>8}")
        for n in sorted(hsc_acc.keys(), key=lambda x: int(x)):
            h = hsc_acc[n]
            t = tf_acc[n]
            print(f"{n:>6} {h:>10.3f} {t:>10.3f} {t-h:>+8.3f}")
