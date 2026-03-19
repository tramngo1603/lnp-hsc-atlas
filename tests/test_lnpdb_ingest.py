"""Tests for LNPDB dataset ingestion."""

from __future__ import annotations

from pathlib import Path

import pytest

from external_data.descriptors import canonicalize_smiles
from external_data.harmonize import find_smiles_overlaps
from external_data.lnpdb_ingest import (
    LnpdbDataset,
    LnpdbRecord,
    _map_row,
    _safe_float,
    _safe_str,
    ingest_lnpdb,
)

# A real ionizable lipid SMILES (MC3 / DLin-MC3-DMA)
MC3_SMILES = (
    "CCCCCCCC/C=C\\CCCCCCCC(=O)OC(CCCCCCCCCCCC)"
    "CC(=O)OCC(C[N](C)C)OC(=O)CCCCCCCCC=CCCCCCCCC"
)


# ---------------------------------------------------------------------------
# Safe conversion helpers
# ---------------------------------------------------------------------------


class TestSafeConversions:
    """Tests for _safe_float and _safe_str."""

    def test_safe_float_valid(self) -> None:
        assert _safe_float(42.5) == 42.5

    def test_safe_float_string(self) -> None:
        assert _safe_float("3.14") == pytest.approx(3.14)

    def test_safe_float_none(self) -> None:
        assert _safe_float(None) is None

    def test_safe_float_nan(self) -> None:
        assert _safe_float(float("nan")) is None

    def test_safe_str_nan(self) -> None:
        assert _safe_str("nan") == ""

    def test_safe_str_none(self) -> None:
        assert _safe_str(None) == ""

    def test_safe_str_valid(self) -> None:
        assert _safe_str("DSPC") == "DSPC"


# ---------------------------------------------------------------------------
# Row mapping
# ---------------------------------------------------------------------------


def _make_row(**overrides: object) -> dict[str, object]:
    """Create a minimal LNPDB row dict with defaults."""
    row: dict[str, object] = {
        "LNP_ID": "LNP_0000001",
        "Experiment_ID": "EXP_001",
        "Formulation_ID": "F_001",
        "IL_name": "MC3",
        "IL_SMILES": MC3_SMILES,
        "IL_molratio": 50.0,
        "HL_name": "DSPC",
        "HL_SMILES": "CCCCCCCCCCCCCCCCCC(=O)OCC",
        "HL_molratio": 10.0,
        "CHL_name": "Cholesterol",
        "CHL_molratio": 38.5,
        "PEG_name": "DMG-PEG2000",
        "PEG_SMILES": "CCCCCCCCCCCCCCC",
        "PEG_molratio": 1.5,
        "fifthcomponent_name": None,
        "fifthcomponent_molratio": 0,
        "IL_to_nucleicacid_massratio": 10.0,
        "IL_to_nucleicacid_chargeratio": 6.0,
        "Model": "in_vivo",
        "Model_type": "Mouse_B6",
        "Model_target": "liver",
        "Route_of_administration": "intravenous",
        "Cargo": "mRNA",
        "Cargo_type": "FLuc",
        "Dose_ug_nucleicacid": 5.0,
        "Experiment_method": "luminescence_normalized",
        "Experiment_batching": "individual",
        "Experiment_value": 1.5,
        "Publication_link": "https://example.com",
        "Publication_PMID": "12345678",
        "Molecular.Weight": 710.2,
        "LogP": 10.5,
        "Topological.Polar.Surface.Area": 99.5,
        "Hydrogen.Bond.Donors": 0,
        "Hydrogen.Bond.Acceptors": 8,
        "Rotatable.Bonds": 40,
        "Rings": 0,
        "Heavy.Atoms": 50,
    }
    row.update(overrides)
    return row


class TestMapRow:
    """Tests for mapping LNPDB rows to our schema."""

    def test_basic_mapping(self) -> None:
        rec = _map_row(_make_row())
        assert rec.source == "lnpdb"
        assert rec.il_name == "MC3"
        assert rec.il_mol_percent == 50.0
        assert rec.hl_name == "DSPC"
        assert rec.chl_mol_percent == 38.5
        assert rec.peg_name == "DMG-PEG2000"
        assert rec.peg_mol_percent == 1.5
        assert rec.model_system == "in_vivo"
        assert rec.cargo == "mRNA"
        assert rec.experiment_value == 1.5
        assert rec.rdkit_valid is True

    def test_descriptors_from_precomputed(self) -> None:
        rec = _map_row(_make_row())
        assert rec.descriptors.molecular_weight == 710.2
        assert rec.descriptors.logp == 10.5
        assert rec.descriptors.heavy_atom_count == 50

    def test_canonical_smiles_computed(self) -> None:
        rec = _map_row(_make_row())
        assert rec.il_canonical_smiles != ""
        assert rec.rdkit_valid is True

    def test_missing_smiles(self) -> None:
        rec = _map_row(_make_row(IL_SMILES="", **{"Molecular.Weight": None}))
        assert rec.il_smiles == ""
        assert rec.il_canonical_smiles == ""
        assert rec.rdkit_valid is False

    def test_invalid_smiles(self) -> None:
        rec = _map_row(_make_row(IL_SMILES="NOT_VALID"))
        assert rec.il_canonical_smiles == ""
        assert rec.rdkit_valid is False

    def test_expt_unit_matches_method(self) -> None:
        rec = _map_row(_make_row(Experiment_method="diameter"))
        assert rec.expt_unit == "diameter"

    def test_missing_helper_lipid(self) -> None:
        rec = _map_row(_make_row(HL_name=None, HL_SMILES=None, HL_molratio=0))
        assert rec.hl_name == ""
        assert rec.hl_mol_percent == 0.0


# ---------------------------------------------------------------------------
# CSV ingestion
# ---------------------------------------------------------------------------


def _write_lnpdb_csv(path: Path, rows: list[dict[str, object]]) -> None:
    """Write a fixture CSV mimicking LNPDB format."""
    import csv

    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


class TestIngestLnpdb:
    """Tests for full ingestion pipeline."""

    def test_ingest_basic(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "lnpdb.csv"
        _write_lnpdb_csv(csv_path, [_make_row(), _make_row(LNP_ID="LNP_0000002")])
        dataset = ingest_lnpdb(csv_path)
        assert dataset.total_parsed == 2
        assert dataset.total_with_smiles == 2

    def test_parquet_output(self, tmp_path: Path) -> None:
        import pandas as pd

        csv_path = tmp_path / "lnpdb.csv"
        out_dir = tmp_path / "output"
        _write_lnpdb_csv(csv_path, [_make_row()])
        ingest_lnpdb(csv_path, output_dir=out_dir)

        parquet = out_dir / "lnpdb.parquet"
        assert parquet.exists()
        df = pd.read_parquet(parquet)
        assert len(df) == 1
        assert "il_name" in df.columns
        assert "molecular_weight" in df.columns
        assert "descriptors" not in df.columns

    def test_to_dataframe_columns(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "lnpdb.csv"
        _write_lnpdb_csv(csv_path, [_make_row()])
        dataset = ingest_lnpdb(csv_path)
        df = dataset.to_dataframe()
        expected = {
            "source", "lnp_id", "il_name", "il_smiles", "il_mol_percent",
            "hl_name", "hl_mol_percent", "peg_name", "peg_mol_percent",
            "chl_name", "chl_mol_percent", "experiment_value", "expt_unit",
            "molecular_weight", "logp", "tpsa", "rdkit_valid",
        }
        assert expected.issubset(set(df.columns))


# ---------------------------------------------------------------------------
# SMILES canonicalization / dedup
# ---------------------------------------------------------------------------


class TestDedup:
    """Tests for SMILES dedup logic."""

    def test_canonical_same_molecule(self) -> None:
        s1 = "C(C)N"
        s2 = "CCN"
        assert canonicalize_smiles(s1) == canonicalize_smiles(s2)

    def test_canonical_different_molecules(self) -> None:
        assert canonicalize_smiles("CCN") != canonicalize_smiles("CCO")

    def test_canonical_invalid(self) -> None:
        assert canonicalize_smiles("INVALID") is None

    def test_find_overlaps(self) -> None:
        overlaps = find_smiles_overlaps(
            ["CCN", "CCO", "CCCC"],
            ["C(C)N", "CCCCC"],
            label_a="agile",
            label_b="lnpdb",
        )
        assert len(overlaps) == 1
        canonical_ccn = canonicalize_smiles("CCN")
        assert canonical_ccn in overlaps
        assert overlaps[canonical_ccn] == ["agile", "lnpdb"]

    def test_no_overlaps(self) -> None:
        overlaps = find_smiles_overlaps(["CCN"], ["CCO"])
        assert len(overlaps) == 0


# ---------------------------------------------------------------------------
# Model serialization
# ---------------------------------------------------------------------------


class TestModels:
    """Tests for Pydantic model behavior."""

    def test_record_defaults(self) -> None:
        r = LnpdbRecord()
        assert r.source == "lnpdb"
        assert r.il_name == ""
        assert r.rdkit_valid is False

    def test_dataset_roundtrip(self) -> None:
        ds = LnpdbDataset(
            records=[LnpdbRecord(lnp_id="X")],
            total_parsed=1,
        )
        ds2 = LnpdbDataset.model_validate_json(ds.model_dump_json())
        assert ds2.total_parsed == 1
        assert ds2.records[0].lnp_id == "X"
