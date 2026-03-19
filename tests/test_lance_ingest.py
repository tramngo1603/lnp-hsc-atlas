"""Tests for LANCE dataset ingestion."""

from __future__ import annotations

import json
from pathlib import Path

from external_data.lance_ingest import (
    LanceDataset,
    LanceRecord,
    _map_entry,
    _to_pct,
    ingest_lance,
)

VALID_SMILES = "CCN(CC)CCNC(=O)CCCCCCCCC"


def _make_entry(
    *,
    dual_il: bool = False,
    dc24: float = 0.7,
    b16f10: float = 0.5,
) -> dict[str, object]:
    """Create a minimal LANCE entry dict."""
    components: list[dict[str, object]] = [
        {"smi": VALID_SMILES, "component_type": "IL", "mol": 0.35},
        {"smi": "CCCCCCCCCCCCCCCCCCCC", "component_type": "HL", "mol": 0.16},
        {"smi": "CC(C)CCCC(C)C1CCC2C3CC=C4CC(O)CCC4C3CCC12C", "component_type": "CH", "mol": 0.47},
        {"smi": "CCCCCCCCCCCCCCCCCC", "component_type": "PEG", "mol": 0.02},
    ]
    if dual_il:
        components.insert(1, {"smi": "CCCCCCCCN(CC)CC", "component_type": "IL", "mol": 0.14})
    return {
        "components": components,
        "labels": {
            "in_house_lnp_DC24_luc": dc24,
            "in_house_lnp_B16F10_luc": b16f10,
        },
        "volumetric_ratio": "1:1",
        "il_rna_wt_ratio": "10:1",
        "dataset_name": "in_house_lnp",
        "phase": "2",
        "lipid_ratio": "P1",
        "NP_ratio": 5.28,
    }


def _write_lance_json(path: Path, entries: dict[str, object]) -> None:
    """Write a LANCE-format JSON fixture."""
    path.write_text(json.dumps(entries), encoding="utf-8")


# ---------------------------------------------------------------------------
# Entry mapping
# ---------------------------------------------------------------------------


class TestMapEntry:
    """Tests for mapping LANCE entries to our schema."""

    def test_single_il(self) -> None:
        rec = _map_entry("0", _make_entry())
        assert rec.source == "lance"
        assert rec.lance_id == "0"
        assert rec.il_smiles == VALID_SMILES
        assert rec.il_canonical_smiles != ""
        assert rec.il_mol_percent == 35.0
        assert rec.il2_smiles == ""
        assert rec.is_dual_il is False
        assert rec.rdkit_valid is True

    def test_dual_il(self) -> None:
        rec = _map_entry("1", _make_entry(dual_il=True))
        assert rec.is_dual_il is True
        assert rec.il_mol_percent == 35.0
        assert rec.il2_smiles != ""
        assert rec.il2_mol_percent == 14.0
        assert rec.il2_canonical_smiles != ""

    def test_molar_fractions_to_percent(self) -> None:
        rec = _map_entry("0", _make_entry())
        assert rec.hl_mol_percent == 16.0
        assert rec.chl_mol_percent == 47.0
        assert rec.peg_mol_percent == 2.0

    def test_labels_mapped(self) -> None:
        rec = _map_entry("0", _make_entry(dc24=0.8, b16f10=0.3))
        assert rec.luc_dc24 == 0.8
        assert rec.luc_b16f10 == 0.3
        assert rec.expt_unit == "normalized_luminescence"

    def test_np_ratio(self) -> None:
        rec = _map_entry("0", _make_entry())
        assert rec.np_ratio == 5.28

    def test_to_pct(self) -> None:
        assert _to_pct(0.355) == 35.5
        assert _to_pct(None) is None


# ---------------------------------------------------------------------------
# CSV ingestion
# ---------------------------------------------------------------------------


class TestIngestLance:
    """Tests for full ingestion pipeline."""

    def test_basic(self, tmp_path: Path) -> None:
        json_path = tmp_path / "lance.json"
        _write_lance_json(json_path, {
            "0": _make_entry(),
            "1": _make_entry(dual_il=True),
        })
        dataset = ingest_lance(json_path)
        assert dataset.total_parsed == 2
        assert dataset.total_single_il == 1
        assert dataset.total_dual_il == 1

    def test_parquet_output(self, tmp_path: Path) -> None:
        import pandas as pd

        json_path = tmp_path / "lance.json"
        out_dir = tmp_path / "output"
        _write_lance_json(json_path, {"0": _make_entry()})
        ingest_lance(json_path, output_dir=out_dir)

        df = pd.read_parquet(out_dir / "lance.parquet")
        assert len(df) == 1
        assert "il_canonical_smiles" in df.columns
        assert "il2_smiles" in df.columns
        assert "descriptors" not in df.columns
        assert "molecular_weight" in df.columns

    def test_to_dataframe(self, tmp_path: Path) -> None:
        json_path = tmp_path / "lance.json"
        _write_lance_json(json_path, {
            "0": _make_entry(),
            "1": _make_entry(dual_il=True),
        })
        dataset = ingest_lance(json_path)
        df = dataset.to_dataframe()
        assert len(df) == 2
        assert set(df["is_dual_il"]) == {True, False}


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class TestModels:
    """Tests for Pydantic model behavior."""

    def test_defaults(self) -> None:
        r = LanceRecord()
        assert r.source == "lance"
        assert r.is_dual_il is False
        assert r.expt_unit == "normalized_luminescence"

    def test_roundtrip(self) -> None:
        ds = LanceDataset(
            records=[LanceRecord(lance_id="0")],
            total_parsed=1,
        )
        ds2 = LanceDataset.model_validate_json(ds.model_dump_json())
        assert ds2.total_parsed == 1
