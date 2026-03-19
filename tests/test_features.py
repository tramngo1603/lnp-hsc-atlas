"""Tests for feature engineering pipeline."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from lnp_optimizer.feature_matrix import (
    build_feature_matrix,
    get_paper_groupkfold_splits,
)
from lnp_optimizer.features import (
    _extract_peg_chain,
    _safe_ratio,
    build_formulation_features,
    build_molecular_features,
)

VALID_SMILES = "CCN(CC)CCNC(=O)CCCCCCCCC"


def _make_hsc_df(n: int = 6) -> pd.DataFrame:
    """Create a fixture HSC-like DataFrame."""
    return pd.DataFrame({
        "source": ["hsc_curated"] * n,
        "paper": ["breda"] * 2 + ["shi"] * 2 + ["kim"] * 2,
        "formulation_id": [f"F{i}" for i in range(n)],
        "experiment_id": [f"E{i}" for i in range(n)],
        "il_name": ["MC3"] * n,
        "il_smiles": [VALID_SMILES] * 3 + [""] * 3,
        "il_mol_percent": [50.0, 50.0, 35.0, 45.0, None, 35.0],
        "hl_name": ["DSPC", "DSPC", "DOTAP", "DSPC", "DDAB", "DOTAP"],
        "hl_mol_percent": [10.0, 10.0, 15.0, 10.0, None, 15.0],
        "chl_mol_percent": [38.5, 38.5, 47.5, 38.5, None, 47.5],
        "peg_mol_percent": [1.5, 1.5, 2.5, 1.5, None, 2.5],
        "peg_chain_length": ["C14", "C18", "C14", "", "C16", "C14"],
        "targeting_strategy": [
            "antibody_conjugated", "antibody_conjugated",
            "intrinsic_tropism", "none", "intrinsic_tropism", "none",
        ],
        "dose_mg_per_kg": [1.0, 0.5, 2.0, None, 1.0, 0.5],
        "animal_model": [
            "mouse C57BL/6", "mouse Ai14", "mouse C57BL/6",
            "human primary", "rhesus monkey", "mouse",
        ],
        "assay_category": [
            "editing", "editing", "protein_expression",
            "knockdown", "protein_expression", "barcode_delivery",
        ],
        "hsc_efficacy_class": ["high", "medium", "high", "low", "medium", "low"],
        "composition_confidence": ["HIGH"] * n,
        "molecular_weight": [200.0] * 3 + [None] * 3,
        "logp": [5.0] * 3 + [None] * 3,
        "tpsa": [40.0] * 3 + [None] * 3,
        "hbd": [1] * 3 + [None] * 3,
        "hba": [3] * 3 + [None] * 3,
        "rotatable_bonds": [10] * 3 + [None] * 3,
        "num_rings": [0] * 3 + [None] * 3,
        "heavy_atom_count": [14] * 3 + [None] * 3,
    })


# ---------------------------------------------------------------------------
# Formulation features
# ---------------------------------------------------------------------------


class TestFormulationFeatures:
    """Tests for formulation feature engineering."""

    def test_mol_percent_columns(self) -> None:
        df = _make_hsc_df()
        feats = build_formulation_features(df)
        assert "ionizable_mol_pct" in feats.columns
        assert "helper_mol_pct" in feats.columns
        assert feats["ionizable_mol_pct"].iloc[0] == 50.0

    def test_pairwise_ratios(self) -> None:
        df = _make_hsc_df()
        feats = build_formulation_features(df)
        assert "il_to_helper_ratio" in feats.columns
        assert feats["il_to_helper_ratio"].iloc[0] == pytest.approx(5.0)

    def test_ratio_div_by_zero(self) -> None:
        df = pd.DataFrame({
            "il_mol_percent": [50.0],
            "hl_mol_percent": [0.0],
            "chl_mol_percent": [50.0],
            "peg_mol_percent": [0.0],
        })
        feats = build_formulation_features(df)
        assert pd.isna(feats["il_to_helper_ratio"].iloc[0])

    def test_peg_chain_extraction(self) -> None:
        df = _make_hsc_df()
        feats = build_formulation_features(df)
        assert feats["peg_chain_numeric"].iloc[0] == 14.0
        assert feats["peg_chain_numeric"].iloc[1] == 18.0

    def test_targeting_encoding(self) -> None:
        df = _make_hsc_df()
        feats = build_formulation_features(df)
        assert feats["targeting_encoded"].iloc[0] == 2  # antibody
        assert feats["targeting_encoded"].iloc[2] == 1  # intrinsic

    def test_helper_charge(self) -> None:
        df = _make_hsc_df()
        feats = build_formulation_features(df)
        assert feats["helper_is_cationic"].iloc[0] == 0  # DSPC
        assert feats["helper_is_cationic"].iloc[2] == 1  # DOTAP

    def test_species_onehot(self) -> None:
        df = _make_hsc_df()
        feats = build_formulation_features(df)
        assert feats["species_mouse"].iloc[0] == 1
        assert feats["species_human"].iloc[3] == 1
        assert feats["species_nhp"].iloc[4] == 1

    def test_assay_onehot(self) -> None:
        df = _make_hsc_df()
        feats = build_formulation_features(df)
        assert "assay_editing" in feats.columns
        assert feats["assay_editing"].iloc[0] == 1
        assert feats["assay_editing"].iloc[2] == 0

    def test_missing_mol_percent(self) -> None:
        df = _make_hsc_df()
        feats = build_formulation_features(df)
        assert pd.isna(feats["ionizable_mol_pct"].iloc[4])


# ---------------------------------------------------------------------------
# Molecular features
# ---------------------------------------------------------------------------


class TestMolecularFeatures:
    """Tests for molecular descriptor features."""

    def test_precomputed_descriptors(self) -> None:
        df = _make_hsc_df()
        feats = build_molecular_features(df, include_fp=False)
        assert "il_molecular_weight" in feats.columns
        assert feats["il_molecular_weight"].iloc[0] == 200.0

    def test_fingerprint_shape(self) -> None:
        df = _make_hsc_df()
        feats = build_molecular_features(df, include_fp=True, fp_nbits=64)
        fp_cols = [c for c in feats.columns if c.startswith("fp_")]
        assert len(fp_cols) == 64

    def test_missing_smiles_no_fp(self) -> None:
        df = _make_hsc_df()
        feats = build_molecular_features(df, include_fp=True, fp_nbits=64)
        fp_cols = [c for c in feats.columns if c.startswith("fp_")]
        if fp_cols:
            # Rows without SMILES should have NaN fps
            assert pd.isna(feats[fp_cols[0]].iloc[3])


class TestMorganFP:
    """Tests for Morgan fingerprint computation."""

    def test_valid_smiles(self) -> None:
        from external_data.descriptors import compute_morgan_fp

        fp = compute_morgan_fp(VALID_SMILES, nbits=64)
        assert fp is not None
        assert fp.shape == (64,)
        assert fp.dtype == np.int8
        assert fp.sum() > 0

    def test_invalid_smiles(self) -> None:
        from external_data.descriptors import compute_morgan_fp

        assert compute_morgan_fp("INVALID") is None

    def test_empty_smiles(self) -> None:
        from external_data.descriptors import compute_morgan_fp

        assert compute_morgan_fp("") is None


# ---------------------------------------------------------------------------
# PEG chain extraction
# ---------------------------------------------------------------------------


class TestPegChain:
    """Tests for PEG chain length extraction."""

    def test_c14(self) -> None:
        assert _extract_peg_chain("C14") == 14.0

    def test_c18(self) -> None:
        assert _extract_peg_chain("C18") == 18.0

    def test_from_name(self) -> None:
        assert _extract_peg_chain("C14PEG2000") == 14.0

    def test_none(self) -> None:
        assert _extract_peg_chain(None) is None

    def test_empty(self) -> None:
        assert _extract_peg_chain("") is None


class TestSafeRatio:
    """Tests for safe division."""

    def test_normal(self) -> None:
        a = pd.Series([10.0])
        b = pd.Series([2.0])
        assert _safe_ratio(a, b).iloc[0] == pytest.approx(5.0)

    def test_zero_denominator(self) -> None:
        a = pd.Series([10.0])
        b = pd.Series([0.0])
        assert pd.isna(_safe_ratio(a, b).iloc[0])


# ---------------------------------------------------------------------------
# Feature matrix assembly
# ---------------------------------------------------------------------------


class TestFeatureMatrix:
    """Tests for feature matrix assembly."""

    def test_build_from_parquet(self, tmp_path: Path) -> None:
        df = _make_hsc_df()
        pq = tmp_path / "hsc.parquet"
        df.to_parquet(pq, index=False)
        out = tmp_path / "features.parquet"
        result = build_feature_matrix(pq, output_path=out, include_fp=False)
        assert len(result) == 6
        assert "target" in result.columns
        assert out.exists()

    def test_drops_unlabeled(self, tmp_path: Path) -> None:
        df = _make_hsc_df()
        df.loc[0, "hsc_efficacy_class"] = ""
        pq = tmp_path / "hsc.parquet"
        df.to_parquet(pq, index=False)
        result = build_feature_matrix(pq, include_fp=False)
        assert len(result) == 5

    def test_target_values(self, tmp_path: Path) -> None:
        df = _make_hsc_df()
        pq = tmp_path / "hsc.parquet"
        df.to_parquet(pq, index=False)
        result = build_feature_matrix(pq, include_fp=False)
        assert set(result["target"].unique()) == {0, 1, 2}

    def test_metadata_preserved(self, tmp_path: Path) -> None:
        df = _make_hsc_df()
        pq = tmp_path / "hsc.parquet"
        df.to_parquet(pq, index=False)
        result = build_feature_matrix(pq, include_fp=False)
        assert "paper" in result.columns
        assert "source" in result.columns


# ---------------------------------------------------------------------------
# GroupKFold splits
# ---------------------------------------------------------------------------


class TestGroupKFold:
    """Tests for paper-based CV splits."""

    def test_no_paper_leakage(self, tmp_path: Path) -> None:
        df = _make_hsc_df()
        pq = tmp_path / "hsc.parquet"
        df.to_parquet(pq, index=False)
        result = build_feature_matrix(pq, include_fp=False)
        splits = get_paper_groupkfold_splits(result, n_splits=3)
        assert len(splits) == 3
        for train_idx, test_idx in splits:
            train_papers = set(result.iloc[train_idx]["paper"])
            test_papers = set(result.iloc[test_idx]["paper"])
            assert train_papers.isdisjoint(test_papers), (
                f"Paper leakage: {train_papers & test_papers}"
            )

    def test_all_data_used(self, tmp_path: Path) -> None:
        df = _make_hsc_df()
        pq = tmp_path / "hsc.parquet"
        df.to_parquet(pq, index=False)
        result = build_feature_matrix(pq, include_fp=False)
        splits = get_paper_groupkfold_splits(result, n_splits=3)
        all_test: set[int] = set()
        for _, test_idx in splits:
            all_test.update(test_idx)
        assert all_test == set(range(len(result)))
