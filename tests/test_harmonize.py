"""Tests for cross-dataset harmonization."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from external_data.harmonize import (
    build_unified_dataset,
    filter_by_expt_unit,
    find_smiles_overlaps,
)


def _write_parquet(path: Path, data: dict[str, list[object]]) -> None:
    """Write a simple parquet fixture."""
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(data).to_parquet(path, index=False)


class TestFindOverlaps:
    """Tests for SMILES overlap detection."""

    def test_basic_overlap(self) -> None:
        overlaps = find_smiles_overlaps(
            ["CCN", "CCO"], ["C(C)N", "CCCC"], "a", "b"
        )
        assert len(overlaps) == 1

    def test_no_overlap(self) -> None:
        overlaps = find_smiles_overlaps(["CCN"], ["CCO"])
        assert len(overlaps) == 0


class TestBuildUnified:
    """Tests for unified dataset merging."""

    def test_merge_three_sources(self, tmp_path: Path) -> None:
        agile_path = tmp_path / "agile.parquet"
        lnpdb_path = tmp_path / "lnpdb.parquet"
        lance_path = tmp_path / "lance.parquet"

        _write_parquet(agile_path, {
            "source": ["agile"], "smiles": ["CCN"],
            "expt_unit": ["normalized_luminescence"],
            "molecular_weight": [45.0], "logp": [0.1],
        })
        _write_parquet(lnpdb_path, {
            "source": ["lnpdb"], "il_smiles": ["CCO"],
            "il_canonical_smiles": ["CCO"],
            "expt_unit": ["luminescence_normalized"],
            "molecular_weight": [46.0], "logp": [0.2],
        })
        _write_parquet(lance_path, {
            "source": ["lance"], "il_smiles": ["CCCC"],
            "il_canonical_smiles": ["CCCC"],
            "expt_unit": ["normalized_luminescence"],
            "molecular_weight": [58.0], "logp": [1.0],
        })

        df = build_unified_dataset(agile_path, lnpdb_path, lance_path)
        assert len(df) == 3
        assert set(df["source"]) == {"agile", "lnpdb", "lance"}
        assert "duplicate_in" in df.columns

    def test_parquet_output(self, tmp_path: Path) -> None:
        agile_path = tmp_path / "agile.parquet"
        lnpdb_path = tmp_path / "lnpdb.parquet"
        lance_path = tmp_path / "lance.parquet"
        out_path = tmp_path / "unified.parquet"

        for p, src in [(agile_path, "agile"), (lnpdb_path, "lnpdb"), (lance_path, "lance")]:
            name = "smiles" if src == "agile" else "il_smiles"
            data: dict[str, list[object]] = {
                "source": [src], name: ["CCN"],
                "expt_unit": ["x"], "molecular_weight": [45.0],
            }
            if src != "agile":
                data["il_canonical_smiles"] = ["CCN"]
            _write_parquet(p, data)

        build_unified_dataset(agile_path, lnpdb_path, lance_path, out_path)
        assert out_path.exists()
        df = pd.read_parquet(out_path)
        assert len(df) == 3

    def test_duplicate_flagging(self, tmp_path: Path) -> None:
        agile_path = tmp_path / "agile.parquet"
        lnpdb_path = tmp_path / "lnpdb.parquet"
        lance_path = tmp_path / "lance.parquet"

        _write_parquet(agile_path, {
            "source": ["agile"], "smiles": ["CCN"],
            "expt_unit": ["x"],
        })
        _write_parquet(lnpdb_path, {
            "source": ["lnpdb"], "il_smiles": ["C(C)N"],
            "il_canonical_smiles": ["CCN"],
            "expt_unit": ["x"],
        })
        _write_parquet(lance_path, {
            "source": ["lance"], "il_smiles": ["CCCC"],
            "il_canonical_smiles": ["CCCC"],
            "expt_unit": ["x"],
        })

        df = build_unified_dataset(agile_path, lnpdb_path, lance_path)
        agile_row = df[df["source"] == "agile"].iloc[0]
        assert "agile" in agile_row["duplicate_in"]
        assert "lnpdb" in agile_row["duplicate_in"]

        lance_row = df[df["source"] == "lance"].iloc[0]
        assert lance_row["duplicate_in"] == ""


class TestFilterByUnit:
    """Tests for expt_unit filtering."""

    def test_filter(self) -> None:
        df = pd.DataFrame({
            "expt_unit": ["luminescence", "diameter", "luminescence"],
            "value": [1.0, 100.0, 2.0],
        })
        filtered = filter_by_expt_unit(df, "luminescence")
        assert len(filtered) == 2

    def test_filter_empty(self) -> None:
        df = pd.DataFrame({"expt_unit": ["diameter"], "value": [100.0]})
        filtered = filter_by_expt_unit(df, "luminescence")
        assert len(filtered) == 0
