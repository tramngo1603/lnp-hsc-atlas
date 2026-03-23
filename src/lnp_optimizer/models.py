"""Baseline ML models for HSC efficacy classification.

Trains XGBoost, LightGBM, and MLP classifiers with paper-level
GroupKFold cross-validation on the HSC feature matrix.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import GroupKFold
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

_META_COLS = [
    "source", "paper", "formulation_id", "experiment_id",
    "assay_category", "composition_confidence",
]
_LABEL_MAP = {0: "low", 1: "medium", 2: "high"}

# Features to always drop (zero-variance or irrelevant)
# NOTE: IL molecular descriptors REMOVED from drop list as of session 13
# (PPZ-A10 + 5A2-SC8 + ALC-0315 now cover 133/135 rows = 99%)
_DROP_COLS = [
    "species_nhp",
]


# ---------------------------------------------------------------------------
# Data preparation
# ---------------------------------------------------------------------------


def load_feature_matrix(
    path: Path,
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Load feature matrix, separating features, target, groups.

    Args:
        path: Path to feature matrix parquet.

    Returns:
        (X features, y target, paper groups).
    """
    df = pd.read_parquet(path)
    feat_cols = [
        c for c in df.columns
        if c not in _META_COLS
        and c != "target"
        and c not in _DROP_COLS
    ]
    X = df[feat_cols]
    y = df["target"].values
    groups = df["paper"].values
    return X, y, groups


# ---------------------------------------------------------------------------
# Model builders
# ---------------------------------------------------------------------------


def _build_xgb(n_classes: int) -> Any:
    """Build XGBoost classifier."""
    from xgboost import XGBClassifier

    return XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        min_child_weight=3,
        tree_method="hist",
        eval_metric="mlogloss",
        num_class=n_classes,
        use_label_encoder=False,
        verbosity=0,
        random_state=42,
    )


def _build_lgbm() -> Any:
    """Build LightGBM classifier."""
    from lightgbm import LGBMClassifier

    return LGBMClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        min_child_samples=5,
        class_weight="balanced",
        verbose=-1,
        random_state=42,
    )


def _build_mlp() -> tuple[Any, StandardScaler]:
    """Build MLP classifier with scaler."""
    clf = MLPClassifier(
        hidden_layer_sizes=(64, 32),
        activation="relu",
        solver="adam",
        max_iter=500,
        early_stopping=True,
        validation_fraction=0.15,
        random_state=42,
    )
    return clf, StandardScaler()


# ---------------------------------------------------------------------------
# MLP preprocessing
# ---------------------------------------------------------------------------


def _prepare_mlp_features(
    X_train: pd.DataFrame, X_test: pd.DataFrame
) -> tuple[np.ndarray, np.ndarray, StandardScaler]:
    """Impute NaN + scale for MLP.

    Adds binary _missing indicators for columns with >10% NaN.
    """
    scaler = StandardScaler()
    X_tr = X_train.copy()
    X_te = X_test.copy()

    # Add missingness indicators
    for col in X_tr.columns:
        miss_rate = X_tr[col].isna().mean()
        if miss_rate > 0.1:
            X_tr[f"{col}_missing"] = X_tr[col].isna().astype(int)
            X_te[f"{col}_missing"] = X_te[col].isna().astype(int)

    # Impute with median
    medians = X_tr.median()
    X_tr = X_tr.fillna(medians)
    X_te = X_te.fillna(medians)

    X_tr_scaled = scaler.fit_transform(X_tr)
    X_te_scaled = scaler.transform(X_te)
    return X_tr_scaled, X_te_scaled, scaler


# ---------------------------------------------------------------------------
# Sample weights for XGBoost
# ---------------------------------------------------------------------------


def _class_weights(y: np.ndarray) -> np.ndarray:
    """Compute inverse-frequency sample weights."""
    classes, counts = np.unique(y, return_counts=True)
    weight_map = {c: len(y) / (len(classes) * n) for c, n in zip(classes, counts, strict=True)}
    return np.array([weight_map[yi] for yi in y])


# ---------------------------------------------------------------------------
# CV evaluation
# ---------------------------------------------------------------------------


def evaluate_cv(
    X: pd.DataFrame,
    y: np.ndarray,
    groups: np.ndarray,
    model_name: str = "xgboost",
) -> dict[str, Any]:
    """Run leave-one-paper-out CV for a model.

    Args:
        X: Feature matrix.
        y: Target array.
        groups: Paper group labels.
        model_name: One of "xgboost", "lightgbm", "mlp".

    Returns:
        Dict with per-fold and aggregate metrics.
    """
    n_groups = len(set(groups))
    gkf = GroupKFold(n_splits=n_groups)
    fold_results: list[dict[str, Any]] = []

    for fold_i, (train_idx, test_idx) in enumerate(gkf.split(X, y, groups)):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        test_paper = set(groups[test_idx])

        y_pred = _train_and_predict(
            model_name, X_train, y_train, X_test
        )

        metrics = _compute_metrics(y_test, y_pred, fold_i, test_paper)
        fold_results.append(metrics)
        logger.info(
            "Fold %d (held-out %s): bal_acc=%.3f",
            fold_i, test_paper, metrics["balanced_accuracy"],
        )

    return _aggregate_results(model_name, fold_results)


def _train_and_predict(
    model_name: str,
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    X_test: pd.DataFrame,
) -> np.ndarray:
    """Train model and return predictions."""
    if model_name == "xgboost":
        model = _build_xgb(n_classes=3)
        sw = _class_weights(y_train)
        model.fit(X_train, y_train, sample_weight=sw)
        return model.predict(X_test)  # type: ignore[no-any-return]

    if model_name == "lightgbm":
        model = _build_lgbm()
        model.fit(X_train, y_train)
        return model.predict(X_test)  # type: ignore[no-any-return]

    # MLP
    clf, _ = _build_mlp()
    X_tr_s, X_te_s, _ = _prepare_mlp_features(X_train, X_test)
    clf.fit(X_tr_s, y_train)
    return clf.predict(X_te_s)  # type: ignore[no-any-return]


def _compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    fold_i: int,
    test_paper: set[str],
) -> dict[str, Any]:
    """Compute classification metrics for one fold."""
    labels = [0, 1, 2]
    return {
        "fold": fold_i,
        "test_paper": list(test_paper),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(
            y_true, y_pred, average="macro", zero_division=0, labels=labels
        )),
        "confusion_matrix": confusion_matrix(
            y_true, y_pred, labels=labels
        ).tolist(),
        "classification_report": classification_report(
            y_true, y_pred, labels=labels,
            target_names=["low", "medium", "high"],
            zero_division=0, output_dict=True,
        ),
    }


def _aggregate_results(
    model_name: str, folds: list[dict[str, Any]]
) -> dict[str, Any]:
    """Aggregate fold results into summary."""
    bal_accs = [f["balanced_accuracy"] for f in folds]
    f1s = [f["macro_f1"] for f in folds]
    return {
        "model": model_name,
        "n_folds": len(folds),
        "balanced_accuracy_mean": float(np.mean(bal_accs)),
        "balanced_accuracy_std": float(np.std(bal_accs)),
        "macro_f1_mean": float(np.mean(f1s)),
        "macro_f1_std": float(np.std(f1s)),
        "folds": folds,
    }


# ---------------------------------------------------------------------------
# Run all baselines
# ---------------------------------------------------------------------------


def run_all_baselines(
    feature_path: Path,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Train and evaluate all 3 baseline models.

    Args:
        feature_path: Path to hsc_features.parquet.
        output_dir: Optional directory to save results.

    Returns:
        Dict of model_name → results.
    """
    X, y, groups = load_feature_matrix(feature_path)
    logger.info("Loaded %d rows × %d features", len(X), len(X.columns))

    all_results: dict[str, Any] = {}
    for name in ["xgboost", "lightgbm", "mlp"]:
        logger.info("Training %s...", name)
        results = evaluate_cv(X, y, groups, model_name=name)
        all_results[name] = results

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / "cv_results.json"
        out_path.write_text(json.dumps(all_results, indent=2))
        logger.info("Saved CV results to %s", out_path)

    return all_results


def print_comparison(results: dict[str, Any]) -> None:
    """Print model comparison table."""
    print(f"\n{'='*75}")
    print("Baseline Model Comparison (leave-one-paper-out CV)")
    print(f"{'='*75}")
    header = f"{'Model':<12} {'Bal.Acc':>8} {'Macro F1':>9}"
    header += f" {'High P/R':>10} {'Med P/R':>10} {'Low P/R':>10}"
    print(header)
    print("-" * 75)

    for name, res in results.items():
        ba = f"{res['balanced_accuracy_mean']:.3f}"
        f1 = f"{res['macro_f1_mean']:.3f}"

        # Aggregate per-class from folds
        pr_strs = []
        for cls in ["high", "medium", "low"]:
            ps = [f["classification_report"][cls]["precision"] for f in res["folds"]]
            rs = [f["classification_report"][cls]["recall"] for f in res["folds"]]
            pr_strs.append(f"{np.mean(ps):.2f}/{np.mean(rs):.2f}")

        print(f"{name:<12} {ba:>8} {f1:>9} {pr_strs[0]:>10} {pr_strs[1]:>10} {pr_strs[2]:>10}")

    # Per-fold detail
    print(f"\n{'Per-fold results:'}")
    for name, res in results.items():
        print(f"\n  {name}:")
        for fold in res["folds"]:
            papers = ", ".join(fold["test_paper"])
            print(
                f"    Fold {fold['fold']} (held-out {papers}): "
                f"bal_acc={fold['balanced_accuracy']:.3f} "
                f"f1={fold['macro_f1']:.3f}"
            )
