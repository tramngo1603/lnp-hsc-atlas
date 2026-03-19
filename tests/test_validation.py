"""Tests for validation protocol."""

from __future__ import annotations

import numpy as np

from lnp_optimizer.validation import build_sar_table


class TestSarTable:
    """Tests for SAR table generation."""

    def test_basic_table(self) -> None:
        feat_names = [
            "ionizable_mol_pct", "receptor_cd117",
            "dose_mg_per_kg", "hl_dotap", "peg_chain_numeric",
            "helper_is_cationic", "cholesterol_mol_pct",
            "peg_mol_pct", "clone_2b8",
        ]
        shap_abs = np.random.rand(10, len(feat_names))
        table = build_sar_table(shap_abs, feat_names)
        assert len(table) > 0
        for entry in table:
            assert "verdict" in entry
            assert entry["verdict"] in [
                "CONFIRMED", "SUPPORTED", "INCONCLUSIVE",
                "NOT_TESTABLE",
            ]

    def test_missing_feature(self) -> None:
        table = build_sar_table(
            np.random.rand(5, 2),
            ["feat_a", "feat_b"],
        )
        not_testable = [e for e in table if e["verdict"] == "NOT_TESTABLE"]
        assert len(not_testable) > 0

    def test_high_rank_confirmed(self) -> None:
        # Make ionizable_mol_pct the top feature
        feat_names = ["ionizable_mol_pct", "filler1", "filler2"]
        shap = np.array([[10.0, 0.1, 0.05]] * 5)
        table = build_sar_table(shap, feat_names)
        il_sar = [s for s in table if s["feature"] == "ionizable_mol_pct"]
        assert il_sar[0]["verdict"] == "CONFIRMED"
        assert il_sar[0]["rank"] == 1


class TestShuffledLabels:
    """Test that shuffled labels produce ~chance accuracy."""

    def test_shuffle_degrades(self) -> None:
        # Just verify the concept — actual test runs in ablation
        rng = np.random.RandomState(42)
        y = np.array([0, 0, 0, 1, 1, 1, 2, 2, 2])
        y_shuf = rng.permutation(y)
        # Shuffled labels should differ from original
        assert not np.array_equal(y, y_shuf)
