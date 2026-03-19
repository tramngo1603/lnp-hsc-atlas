"""Tests for AGILE dataset ingestion."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from external_data.agile_ingest import (
    AgileDataset,
    AgileRecord,
    ingest_agile,
    parse_agile_csv,
)
from external_data.descriptors import MolecularDescriptors, compute_descriptors

VALID_SMILES = "CCN(CC)CCNC(=O)CCCCCCCCC"
INVALID_SMILES = "NOT_A_MOLECULE"


# ---------------------------------------------------------------------------
# Descriptor computation
# ---------------------------------------------------------------------------


class TestComputeDescriptors:
    """Tests for RDKit descriptor computation."""

    def test_valid_smiles(self) -> None:
        desc = compute_descriptors(VALID_SMILES)
        assert desc is not None
        assert desc.molecular_weight is not None
        assert desc.molecular_weight > 0
        assert desc.logp is not None
        assert desc.hba is not None
        assert desc.hbd is not None
        assert desc.heavy_atom_count is not None
        assert desc.heavy_atom_count > 0

    def test_invalid_smiles_returns_none(self) -> None:
        desc = compute_descriptors(INVALID_SMILES)
        assert desc is None

    def test_empty_smiles_returns_none(self) -> None:
        desc = compute_descriptors("")
        assert desc is None

    def test_descriptor_ranges_sane(self) -> None:
        desc = compute_descriptors(VALID_SMILES)
        assert desc is not None
        assert 50 < desc.molecular_weight < 2000  # type: ignore[operator]
        assert -10 < desc.logp < 30  # type: ignore[operator]
        assert desc.tpsa >= 0  # type: ignore[operator]
        assert desc.hba >= 0  # type: ignore[operator]
        assert desc.hbd >= 0  # type: ignore[operator]


# ---------------------------------------------------------------------------
# CSV parsing
# ---------------------------------------------------------------------------


def _write_fixture_csv(path: Path, rows: list[dict[str, str]]) -> None:
    """Write a fixture CSV with AGILE columns."""
    fieldnames = [
        "id", "label", "combined_mol_SMILES",
        "A_smiles", "B_smiles", "C_smiles",
        "expt_Hela", "expt_Raw",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


class TestParseAgileCsv:
    """Tests for CSV parsing."""

    def test_basic_parse(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "test.csv"
        _write_fixture_csv(csv_path, [
            {
                "id": "0", "label": "A1B1C1",
                "combined_mol_SMILES": VALID_SMILES,
                "A_smiles": "CCN(CC)CCN", "B_smiles": "O=CCCCC",
                "C_smiles": "CCCCCCCCC",
                "expt_Hela": "4.05", "expt_Raw": "1.54",
            },
        ])
        records = parse_agile_csv(csv_path)
        assert len(records) == 1
        assert records[0].agile_id == 0
        assert records[0].label == "A1B1C1"
        assert records[0].smiles == VALID_SMILES
        assert records[0].expt_hela == pytest.approx(4.05)
        assert records[0].expt_raw == pytest.approx(1.54)
        assert records[0].rdkit_valid is True
        assert records[0].source == "agile"

    def test_invalid_smiles_still_parsed(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "test.csv"
        _write_fixture_csv(csv_path, [
            {
                "id": "1", "label": "BAD",
                "combined_mol_SMILES": INVALID_SMILES,
                "A_smiles": "", "B_smiles": "", "C_smiles": "",
                "expt_Hela": "2.0", "expt_Raw": "1.0",
            },
        ])
        records = parse_agile_csv(csv_path)
        assert len(records) == 1
        assert records[0].rdkit_valid is False

    def test_empty_smiles_skipped(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "test.csv"
        _write_fixture_csv(csv_path, [
            {
                "id": "2", "label": "EMPTY",
                "combined_mol_SMILES": "",
                "A_smiles": "", "B_smiles": "", "C_smiles": "",
                "expt_Hela": "", "expt_Raw": "",
            },
        ])
        records = parse_agile_csv(csv_path)
        assert len(records) == 0

    def test_missing_expt_values(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "test.csv"
        _write_fixture_csv(csv_path, [
            {
                "id": "3", "label": "X",
                "combined_mol_SMILES": VALID_SMILES,
                "A_smiles": "", "B_smiles": "", "C_smiles": "",
                "expt_Hela": "", "expt_Raw": "",
            },
        ])
        records = parse_agile_csv(csv_path)
        assert records[0].expt_hela is None
        assert records[0].expt_raw is None

    def test_multiple_records(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "test.csv"
        rows = [
            {
                "id": str(i), "label": f"L{i}",
                "combined_mol_SMILES": VALID_SMILES,
                "A_smiles": "", "B_smiles": "", "C_smiles": "",
                "expt_Hela": str(float(i)), "expt_Raw": str(float(i) / 2),
            }
            for i in range(5)
        ]
        _write_fixture_csv(csv_path, rows)
        records = parse_agile_csv(csv_path)
        assert len(records) == 5


# ---------------------------------------------------------------------------
# Full ingestion
# ---------------------------------------------------------------------------


class TestIngestAgile:
    """Tests for the full ingestion pipeline."""

    def test_ingest_with_output(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "input.csv"
        out_dir = tmp_path / "output"
        _write_fixture_csv(csv_path, [
            {
                "id": "0", "label": "A1B1C1",
                "combined_mol_SMILES": VALID_SMILES,
                "A_smiles": "", "B_smiles": "", "C_smiles": "",
                "expt_Hela": "4.0", "expt_Raw": "1.5",
            },
            {
                "id": "1", "label": "BAD",
                "combined_mol_SMILES": INVALID_SMILES,
                "A_smiles": "", "B_smiles": "", "C_smiles": "",
                "expt_Hela": "2.0", "expt_Raw": "1.0",
            },
        ])
        dataset = ingest_agile(csv_path, output_dir=out_dir)
        assert dataset.total_parsed == 2
        assert dataset.total_valid_smiles == 1
        assert dataset.total_invalid_smiles == 1
        assert (out_dir / "agile_ingested.json").exists()
        assert (out_dir / "agile.parquet").exists()

    def test_parquet_export(self, tmp_path: Path) -> None:
        import pandas as pd

        csv_path = tmp_path / "input.csv"
        out_dir = tmp_path / "output"
        _write_fixture_csv(csv_path, [
            {
                "id": "0", "label": "A1B1C1",
                "combined_mol_SMILES": VALID_SMILES,
                "A_smiles": "CCN", "B_smiles": "O=C", "C_smiles": "CCC",
                "expt_Hela": "4.0", "expt_Raw": "1.5",
            },
            {
                "id": "1", "label": "A1B1C2",
                "combined_mol_SMILES": VALID_SMILES,
                "A_smiles": "", "B_smiles": "", "C_smiles": "",
                "expt_Hela": "3.0", "expt_Raw": "2.0",
            },
        ])
        ingest_agile(csv_path, output_dir=out_dir)

        df = pd.read_parquet(out_dir / "agile.parquet")
        assert len(df) == 2

        # Descriptor columns are flattened (not nested)
        expected_cols = {
            "source", "agile_id", "label", "smiles",
            "component_a_smiles", "component_b_smiles", "component_c_smiles",
            "expt_hela", "expt_raw", "expt_unit", "rdkit_valid",
            "molecular_weight", "logp", "tpsa", "hbd", "hba",
            "rotatable_bonds", "num_rings", "heavy_atom_count",
        }
        assert expected_cols.issubset(set(df.columns))
        assert "descriptors" not in df.columns

    def test_ingest_without_output(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "input.csv"
        _write_fixture_csv(csv_path, [
            {
                "id": "0", "label": "X",
                "combined_mol_SMILES": VALID_SMILES,
                "A_smiles": "", "B_smiles": "", "C_smiles": "",
                "expt_Hela": "3.0", "expt_Raw": "2.0",
            },
        ])
        dataset = ingest_agile(csv_path)
        assert dataset.total_parsed == 1
        assert isinstance(dataset, AgileDataset)


# ---------------------------------------------------------------------------
# Model serialization
# ---------------------------------------------------------------------------


class TestModels:
    """Tests for Pydantic model behavior."""

    def test_agile_record_defaults(self) -> None:
        r = AgileRecord(agile_id=0, label="test", smiles="C")
        assert r.source == "agile"
        assert r.rdkit_valid is False
        assert r.expt_hela is None
        assert r.expt_unit == "normalized_luminescence"

    def test_dataset_json_roundtrip(self) -> None:
        ds = AgileDataset(
            records=[AgileRecord(agile_id=0, label="X", smiles="C")],
            total_parsed=1,
            total_valid_smiles=0,
            total_invalid_smiles=1,
        )
        json_str = ds.model_dump_json()
        ds2 = AgileDataset.model_validate_json(json_str)
        assert ds2.total_parsed == 1
        assert len(ds2.records) == 1

    def test_descriptors_defaults(self) -> None:
        d = MolecularDescriptors()
        assert d.molecular_weight is None
        assert d.logp is None
