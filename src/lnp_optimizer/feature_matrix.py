"""Feature matrix assembly, CV splits, and quality reporting.

Combines formulation + molecular features into a single matrix,
provides GroupKFold splits by paper, and prints feature quality report.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

from lnp_optimizer.features import (
    build_formulation_features,
    build_molecular_features,
)

logger = logging.getLogger(__name__)

_LABEL_COL = "hsc_efficacy_class"
_LABEL_MAP = {"high": 2, "medium": 1, "low": 0}
_META_COLS = [
    "source", "paper", "formulation_id", "experiment_id",
    "assay_category", "composition_confidence",
]


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------


def build_feature_matrix(
    hsc_parquet_path: Path,
    output_path: Path | None = None,
    include_fp: bool = False,
) -> pd.DataFrame:
    """Build ML-ready feature matrix from HSC dataset.

    Args:
        hsc_parquet_path: Path to hsc_curated.parquet.
        output_path: Optional path to save feature parquet.
        include_fp: Whether to include 2048-bit fingerprints.

    Returns:
        DataFrame with features + target + metadata.
    """
    raw = pd.read_parquet(hsc_parquet_path)
    logger.info("Loaded %d rows from %s", len(raw), hsc_parquet_path)

    # Drop rows without efficacy class
    labeled = raw[raw[_LABEL_COL].isin(_LABEL_MAP.keys())].copy()
    labeled = labeled.reset_index(drop=True)
    logger.info("%d rows with efficacy label", len(labeled))

    # Build feature groups
    form_feats = build_formulation_features(labeled)
    mol_feats = build_molecular_features(
        labeled, include_fp=include_fp
    )

    # Target
    target = labeled[_LABEL_COL].map(_LABEL_MAP).astype(int)

    # Metadata
    meta = pd.DataFrame(index=labeled.index)
    for c in _META_COLS:
        if c in labeled.columns:
            meta[c] = labeled[c]

    # Combine
    result = pd.concat(
        [meta, form_feats, mol_feats, target.rename("target")],
        axis=1,
    )

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result.to_parquet(output_path, index=False)
        logger.info("Saved feature matrix to %s", output_path)

    return result


# ---------------------------------------------------------------------------
# CV splits
# ---------------------------------------------------------------------------


def get_paper_groupkfold_splits(
    df: pd.DataFrame,
    n_splits: int = 3,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Generate GroupKFold splits using paper as group.

    Args:
        df: Feature matrix with 'paper' column.
        n_splits: Number of CV folds (default 3 = leave-one-paper-out).

    Returns:
        List of (train_indices, test_indices) tuples.
    """
    groups = df["paper"].values
    n_groups = len(set(groups))
    actual_splits = min(n_splits, n_groups)

    gkf = GroupKFold(n_splits=actual_splits)
    y = df.get("target", pd.Series(np.zeros(len(df))))

    return [
        (train_idx, test_idx)
        for train_idx, test_idx in gkf.split(df, y, groups)
    ]


# ---------------------------------------------------------------------------
# Quality report
# ---------------------------------------------------------------------------


def print_feature_report(df: pd.DataFrame) -> None:
    """Print feature matrix quality report.

    Args:
        df: Feature matrix from build_feature_matrix.
    """
    _report_shape(df)
    _report_target(df)
    _report_completeness(df)
    _report_flagged(df)


def _report_shape(df: pd.DataFrame) -> None:
    """Print matrix dimensions."""
    feat_cols = [
        c for c in df.columns if c not in _META_COLS and c != "target"
    ]
    print(f"\n{'='*60}")
    print(f"Feature Matrix: {len(df)} rows × {len(feat_cols)} features")
    print(f"{'='*60}")


def _report_target(df: pd.DataFrame) -> None:
    """Print target class distribution."""
    if "target" not in df.columns:
        return
    inv_map = {v: k for k, v in _LABEL_MAP.items()}
    counts = df["target"].value_counts().sort_index()
    print("\nTarget distribution:")
    for val, cnt in counts.items():
        label = inv_map.get(int(val), str(val))
        print(f"  {label}: {cnt}")


def _report_completeness(df: pd.DataFrame) -> None:
    """Print completeness per feature group."""
    feat_cols = [
        c for c in df.columns if c not in _META_COLS and c != "target"
    ]
    form_cols = [c for c in feat_cols if not c.startswith("il_") and not c.startswith("fp_")]
    mol_cols = [c for c in feat_cols if c.startswith("il_")]
    fp_cols = [c for c in feat_cols if c.startswith("fp_")]

    for name, cols in [
        ("Formulation", form_cols),
        ("Molecular", mol_cols),
        ("Fingerprint", fp_cols),
    ]:
        if not cols:
            continue
        nn = df[cols].notna().sum().sum()
        total = len(df) * len(cols)
        pct = nn / total * 100 if total else 0
        print(f"{name} features ({len(cols)}): {pct:.1f}% complete")


def _report_flagged(df: pd.DataFrame) -> None:
    """Flag features with >90% missing or zero variance."""
    feat_cols = [
        c for c in df.columns if c not in _META_COLS and c != "target"
    ]
    flagged = []
    for c in feat_cols:
        if c.startswith("fp_"):
            continue
        missing_pct = df[c].isna().sum() / len(df) * 100
        if missing_pct > 90:
            flagged.append((c, f"{missing_pct:.0f}% missing"))
            continue
        if df[c].nunique() <= 1:
            flagged.append((c, "zero variance"))

    if flagged:
        print(f"\nFlagged features ({len(flagged)}):")
        for name, reason in flagged:
            print(f"  {name}: {reason}")
