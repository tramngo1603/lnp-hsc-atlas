"""Tests for baseline ML models and evaluation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from lnp_optimizer.models import (
    _class_weights,
    _compute_metrics,
    evaluate_cv,
    load_feature_matrix,
)


def _make_feature_parquet(tmp_path: Path, n: int = 12) -> Path:
    """Create a minimal feature matrix parquet for testing."""
    rng = np.random.RandomState(42)
    df = pd.DataFrame({
        "source": ["hsc"] * n,
        "paper": (["breda"] * 4 + ["shi"] * 4 + ["kim"] * 4)[:n],
        "formulation_id": [f"F{i}" for i in range(n)],
        "experiment_id": [f"E{i}" for i in range(n)],
        "assay_category": ["editing"] * n,
        "composition_confidence": ["HIGH"] * n,
        "ionizable_mol_pct": rng.uniform(30, 55, n),
        "helper_mol_pct": rng.uniform(5, 20, n),
        "cholesterol_mol_pct": rng.uniform(30, 50, n),
        "peg_mol_pct": rng.uniform(1, 5, n),
        "il_to_helper_ratio": rng.uniform(2, 6, n),
        "il_to_chol_ratio": rng.uniform(0.5, 2, n),
        "chol_to_helper_ratio": rng.uniform(2, 5, n),
        "peg_chain_numeric": rng.choice([14.0, 16.0, 18.0], n),
        "dose_mg_per_kg": rng.uniform(0.1, 2.0, n),
        "targeting_encoded": rng.choice([0, 1, 2], n),
        "helper_is_cationic": rng.choice([0, 1], n),
        "species_mouse": [1] * n,
        "species_human": [0] * n,
        "assay_editing": [1] * n,
        "target": rng.choice([0, 1, 2], n),
    })
    path = tmp_path / "features.parquet"
    df.to_parquet(path, index=False)
    return path


class TestLoadFeatureMatrix:
    """Tests for feature matrix loading."""

    def test_load(self, tmp_path: Path) -> None:
        path = _make_feature_parquet(tmp_path)
        X, y, groups = load_feature_matrix(path)
        assert len(X) == 12
        assert "target" not in X.columns
        assert "paper" not in X.columns
        assert len(y) == 12
        assert len(groups) == 12

    def test_drops_meta(self, tmp_path: Path) -> None:
        path = _make_feature_parquet(tmp_path)
        X, _, _ = load_feature_matrix(path)
        assert "source" not in X.columns
        assert "formulation_id" not in X.columns


class TestClassWeights:
    """Tests for inverse-frequency class weights."""

    def test_balanced(self) -> None:
        y = np.array([0, 0, 1, 1, 2, 2])
        w = _class_weights(y)
        assert len(w) == 6
        assert np.allclose(w[0], w[2])  # same class frequency

    def test_imbalanced(self) -> None:
        y = np.array([0, 0, 0, 0, 1, 2])
        w = _class_weights(y)
        assert w[4] > w[0]  # minority class gets higher weight


class TestMetrics:
    """Tests for metric computation."""

    def test_compute_metrics(self) -> None:
        y_true = np.array([0, 1, 2, 0, 1])
        y_pred = np.array([0, 1, 2, 0, 2])
        result = _compute_metrics(y_true, y_pred, 0, {"test"})
        assert "balanced_accuracy" in result
        assert "macro_f1" in result
        assert "confusion_matrix" in result
        assert result["balanced_accuracy"] > 0


class TestEvaluateCV:
    """Tests for CV evaluation."""

    def test_runs_xgboost(self, tmp_path: Path) -> None:
        path = _make_feature_parquet(tmp_path)
        X, y, groups = load_feature_matrix(path)
        result = evaluate_cv(X, y, groups, "xgboost")
        assert result["model"] == "xgboost"
        assert result["n_folds"] == 3
        assert "balanced_accuracy_mean" in result

    def test_runs_lightgbm(self, tmp_path: Path) -> None:
        path = _make_feature_parquet(tmp_path)
        X, y, groups = load_feature_matrix(path)
        result = evaluate_cv(X, y, groups, "lightgbm")
        assert result["n_folds"] == 3

    def test_runs_mlp(self, tmp_path: Path) -> None:
        path = _make_feature_parquet(tmp_path)
        X, y, groups = load_feature_matrix(path)
        result = evaluate_cv(X, y, groups, "mlp")
        assert result["n_folds"] == 3


class TestSHAP:
    """Tests for SHAP computation."""

    def test_shap_runs(self, tmp_path: Path) -> None:
        from lnp_optimizer.evaluation import compute_shap_values

        path = _make_feature_parquet(tmp_path)
        X, y, _ = load_feature_matrix(path)
        shap_abs, feat_names = compute_shap_values(
            "lightgbm", X, y, output_dir=tmp_path
        )
        assert shap_abs.shape == (len(X), len(feat_names))
        assert (tmp_path / "shap_values.parquet").exists()

    def test_sar_check(self, tmp_path: Path) -> None:
        from lnp_optimizer.evaluation import check_sar_recovery

        path = _make_feature_parquet(tmp_path)
        X, y, _ = load_feature_matrix(path)
        # Fake SHAP values
        shap_abs = np.random.rand(len(X), len(X.columns))
        results = check_sar_recovery(shap_abs, list(X.columns))
        assert len(results) > 0
        assert all("verdict" in r for r in results)
