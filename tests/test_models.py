"""Tests for baseline ML models and evaluation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from lnp_optimizer.models import (
    _class_weights,
    _compute_metrics,
    evaluate_cv,
    formulation_token,
    load_feature_matrix,
    make_validation_splits,
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

    def test_excludes_marked_label_boundary_rows(self, tmp_path: Path) -> None:
        path = _make_feature_parquet(tmp_path)
        df = pd.read_parquet(path)
        df["label_boundary_case"] = 0
        df.loc[[2, 9], "label_boundary_case"] = 1
        df.to_parquet(path, index=False)

        X, y, groups = load_feature_matrix(path)

        assert len(X) == len(y) == len(groups) == 10
        assert "label_boundary_case" not in X.columns

    def test_can_return_formulation_groups(self, tmp_path: Path) -> None:
        path = _make_feature_parquet(tmp_path)
        _, _, groups = load_feature_matrix(path, group_by="formulation")
        assert len(groups) == 12
        assert groups[0] == "breda::f0"


class TestFormulationGrouping:
    """Tests for formulation-token normalization and split isolation."""

    def test_xu_lead_cargo_and_library_aliases_share_token(self) -> None:
        aliases = [
            "LNP-028-ABE8e-PCSK9 (Library A lead)",
            "LNP-028-ABE8e-HBG (ABE8e + sgRNA-25)",
            "LNP-028-ABE8e/sgRNA-PCSK9",
        ]
        assert {
            formulation_token("xu_2026", formulation) for formulation in aliases
        } == {"xu-2026::lnp-028"}
        assert formulation_token("xu_2026", "LNP-168-Cre-miR-122T") == (
            "xu-2026::lnp-168"
        )

    def test_no_formulation_token_crosses_grouped_partitions(self) -> None:
        y = np.tile(np.array([0, 1, 2]), 10)
        groups = np.repeat([f"paper::lnp-{i:03d}" for i in range(10)], 3)
        splits = make_validation_splits(
            y,
            groups,
            strategy="formulation_grouped",
            n_splits=5,
        )

        assert len(splits) == 5
        for train_idx, held_out_idx in splits:
            train_formulations = set(groups[train_idx])
            held_out_formulations = set(groups[held_out_idx])
            assert train_formulations.isdisjoint(held_out_formulations)


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
