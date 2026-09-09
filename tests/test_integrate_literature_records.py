"""Regression tests for projecting literature records onto the feature matrix."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from lnp_optimizer.integrate_literature_records import (
    _make_row,
    add_label_boundary_marker,
)

_ROOT = Path(__file__).resolve().parent.parent
_RECORDS = json.loads(
    (_ROOT / "data" / "literature_records.json").read_text()
)["records"]
_BY_ID = {record["record_id"]: record for record in _RECORDS}


def _row(record_id: str) -> dict:
    return _make_row(_BY_ID[record_id], label=None)


def test_targeting_uses_established_ordinal_encoding() -> None:
    assert _row("xu_2026_LNP168_Cre_miR122T_Ai14")["targeting_encoded"] == 1
    assert _row("chappell_2024_mRNACre_LNPCD117_exvivo_deletion")[
        "targeting_encoded"
    ] == 2
    assert _row("swart_2023_LDV_LNP")["targeting_encoded"] == 2
    assert _row("palchaudhuri_2025_HSCLNP_GFP_delivery")[
        "targeting_encoded"
    ] == 2
    assert _row("swart_2023_LNP_untargeted")["targeting_encoded"] == 0


def test_covalent_feature_excludes_non_covalent_components_and_mass() -> None:
    assert _row("hofstraat_2025_aNP27_invivo_siLAMP1")[
        "covalent_lipid_mol_pct"
    ] == 0.0
    assert _row("hofstraat_2025_LNP_control_invivo_siLAMP1")[
        "covalent_lipid_mol_pct"
    ] == 0.0


def test_covalent_feature_keeps_functionalized_lipid_mol_percent() -> None:
    assert _row("shi_2025_thesis_FLS_20DSPC_aCD117_ABE_invivo")[
        "covalent_lipid_mol_pct"
    ] == 0.5
    assert _row("swart_2023_LDV_LNP")["covalent_lipid_mol_pct"] == 0.1


def test_only_four_lian_rows_receive_boundary_marker() -> None:
    rows = pd.DataFrame(
        {
            "paper": ["lian_2024"] * 5 + ["xu_2026"],
            "experiment_id": [
                "Lian_A7_screen_n1",
                "Lian_A13_validated_n3",
                "Lian_C6_validated_n3",
                "Lian_C9_screen_n1",
                "Lian_C6_screen_n1",
                "Lian_A7_screen_n1",
            ],
        }
    )
    marked = add_label_boundary_marker(rows)
    assert marked["label_boundary_case"].tolist() == [1, 1, 1, 1, 0, 0]
