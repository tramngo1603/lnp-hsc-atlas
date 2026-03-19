"""Tests for transfer learning pipeline."""

from __future__ import annotations

import numpy as np
import pandas as pd

from lnp_optimizer.transfer import (
    SHARED_FEATURES,
    align_features,
    learning_curve,
    transfer_continue_training,
    transfer_stacked,
)


def _make_ext_df(n: int = 100) -> tuple[pd.DataFrame, pd.Series]:
    """Create fixture external feature data."""
    rng = np.random.RandomState(42)
    data: dict[str, object] = {}
    for col in SHARED_FEATURES:
        data[col] = rng.uniform(0, 50, n).tolist()
    return pd.DataFrame(data), pd.Series(rng.uniform(-1, 5, n))


def _make_hsc_df(n: int = 30) -> tuple[pd.DataFrame, np.ndarray]:
    """Create fixture HSC feature data."""
    rng = np.random.RandomState(42)
    data: dict[str, object] = {
        "source": ["hsc"] * n,
        "paper": (["breda"] * 10 + ["shi"] * 10 + ["kim"] * 10)[:n],
        "formulation_id": [f"F{i}" for i in range(n)],
        "experiment_id": [f"E{i}" for i in range(n)],
        "assay_category": ["editing"] * n,
        "composition_confidence": ["HIGH"] * n,
        "target": rng.choice([0, 1, 2], n).tolist(),
    }
    for col in SHARED_FEATURES:
        data[col] = rng.uniform(0, 50, n).tolist()
    # Add HSC-specific features
    data["targeting_encoded"] = rng.choice([0, 1, 2], n).tolist()
    data["dose_mg_per_kg"] = rng.uniform(0.1, 2.0, n).tolist()
    data["peg_chain_numeric"] = rng.choice([14, 16, 18], n).tolist()
    df = pd.DataFrame(data)
    target = df["target"].values.astype(int)
    return df, target


class TestAlignFeatures:
    """Tests for feature alignment."""

    def test_finds_shared_columns(self) -> None:
        ext, _ = _make_ext_df()
        hsc, _ = _make_hsc_df()
        shared = align_features(ext, hsc)
        assert len(shared) > 0
        for col in shared:
            assert col in ext.columns
            assert col in hsc.columns

    def test_excludes_metadata(self) -> None:
        ext, _ = _make_ext_df()
        hsc, _ = _make_hsc_df()
        shared = align_features(ext, hsc)
        assert "source" not in shared
        assert "paper" not in shared
        assert "target" not in shared


class TestTransferContinue:
    """Tests for pretrain + continue training."""

    def test_runs(self) -> None:
        ext_feats, ext_target = _make_ext_df(200)
        hsc_feats, hsc_target = _make_hsc_df(30)
        shared = align_features(ext_feats, hsc_feats)
        train = np.arange(20)
        test = np.arange(20, 30)
        result = transfer_continue_training(
            ext_feats, ext_target, hsc_feats, hsc_target,
            shared, train, test,
        )
        assert "bal_acc" in result
        assert 0 <= result["bal_acc"] <= 1
        assert len(result["y_pred"]) == 10


class TestTransferStacked:
    """Tests for stacked generalization."""

    def test_runs(self) -> None:
        ext_feats, ext_target = _make_ext_df(200)
        hsc_feats, hsc_target = _make_hsc_df(30)
        shared = align_features(ext_feats, hsc_feats)
        train = np.arange(20)
        test = np.arange(20, 30)
        result = transfer_stacked(
            ext_feats, ext_target, hsc_feats, hsc_target,
            shared, train, test,
        )
        assert "bal_acc" in result
        assert 0 <= result["bal_acc"] <= 1


class TestLearningCurve:
    """Tests for learning curve generation."""

    def test_curve_shape(self) -> None:
        ext_feats, ext_target = _make_ext_df(200)
        hsc_feats, hsc_target = _make_hsc_df(30)
        shared = align_features(ext_feats, hsc_feats)
        train = np.arange(20)
        test = np.arange(20, 30)
        lc = learning_curve(
            ext_feats, ext_target, hsc_feats, hsc_target,
            shared, train, test,
            n_values=[10, 20], n_repeats=2,
        )
        assert "n" in lc.columns
        assert "hsc_only_acc" in lc.columns
        assert "transfer_acc" in lc.columns
        assert len(lc) == 4  # 2 n_values × 2 repeats

    def test_all_n_values_present(self) -> None:
        ext_feats, ext_target = _make_ext_df(200)
        hsc_feats, hsc_target = _make_hsc_df(30)
        shared = align_features(ext_feats, hsc_feats)
        train = np.arange(20)
        test = np.arange(20, 30)
        lc = learning_curve(
            ext_feats, ext_target, hsc_feats, hsc_target,
            shared, train, test,
            n_values=[10, 15, 20], n_repeats=1,
        )
        assert set(lc["n"]) == {10, 15, 20}
