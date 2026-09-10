"""Regression tests for the atlas explorer pipeline."""

from __future__ import annotations

import importlib.util
import json
import re
from collections import Counter
from copy import deepcopy
from pathlib import Path

import pandas as pd

from lnp_optimizer.explorer_analysis import literature_measurements

_ROOT = Path(__file__).resolve().parent.parent


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, _ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_EXTRACT = _load_script("extract_explorer_data")
_PATCH = _load_script("patch_explorer")


def _embedded_block(jsx: str, key: str) -> object:
    variable = _PATCH._KEY_TO_VAR[key]
    pattern = rf"const {re.escape(variable)} = (.*?);\n// END:{re.escape(key)}"
    match = re.search(pattern, jsx, re.DOTALL)
    assert match is not None, f"missing embedded block {key}"
    return json.loads(match.group(1))


def test_extracted_data_matches_atlas() -> None:
    data = _EXTRACT.build_data()

    assert data["stats"] == {
        "rows": 331,
        "sources": 18,
        "columns": 48,
        "labeled": 315,
        "modelFeatures": 37,
        "descriptorRows": 154,
    }
    assert len(data["formulations"]) == 331
    assert len(data["papers"]) == 18
    paper_counts = Counter(row["paperId"] for row in data["formulations"])
    assert paper_counts["xu_2026"] == 148
    assert paper_counts["hanafy_2025"] == 14
    assert paper_counts["hofstraat_2025"] == 9
    assert paper_counts["xue_2022"] == 0

    assert data["coverageStats"]["completeColumns"] == 30
    assert data["coverageStats"]["totalColumns"] == 48
    assert data["labelDistribution"]["lowShare"] == 58.4
    assert data["validationSummary"]["formulationGrouped"]["formulationDisjoint"] is True
    assert data["validationSummary"]["rowRandom"]["formulationDisjoint"] is False

    boundary_rows = [row for row in data["formulations"] if row["boundary"]]
    assert len(boundary_rows) == 4
    assert {row["cls"] for row in boundary_rows} == {"high"}
    record_types = Counter(row["recordType"] for row in data["formulations"])
    assert record_types == {
        "screen": 142,
        "detailed": 186,
        "abstract-only": 3,
    }


def test_patcher_replaces_every_required_block() -> None:
    data = _EXTRACT.build_data()
    jsx = "\n".join(f"// DATA:{key}\nconst old = null;\n// END:{key}" for key in _PATCH._KEY_TO_VAR)

    patched, count, missing = _PATCH.patch_jsx(jsx, data)

    assert missing == []
    assert count == len(_PATCH._KEY_TO_VAR)
    assert "const formulations = [" in patched
    assert "const validationSummary = {" in patched


def test_deployed_explorer_embeds_atlas_data_and_matches_root_copy() -> None:
    deployed = (_ROOT / "explorer" / "src" / "App.jsx").read_text()
    root_copy = (_ROOT / "explorer.jsx").read_text()

    assert deployed == root_copy
    assert chr(0x2014) not in deployed
    assert len(_embedded_block(deployed, "formulations")) == 331
    assert len(_embedded_block(deployed, "papers")) == 18
    stats = _embedded_block(deployed, "stats")
    assert stats["rows"] == 331
    assert stats["sources"] == 18
    assert _embedded_block(deployed, "analysisData") == _EXTRACT.build_data()["analysisData"]


def test_chart_groups_use_current_studies_and_keep_measurements_separate() -> None:
    data = _EXTRACT.build_data()
    analysis = data["analysisData"]
    for view in ("peg", "helper", "dose"):
        assert {"hanafy_2025", "xu_2026"} <= {g["paperId"] for g in analysis[view]}
        for group in analysis[view]:
            assert {p["unit"] for p in group["points"]} == {group["unit"]}
            assert {p["paperId"] for p in group["points"]} == {group["paperId"]}
            assert {p["target"] for p in group["points"]} == {group["target"]}
    assert analysis["coverage"]["newPairs"] == 0
    kim_percent = next(
        g for g in analysis["pareto"] if g["paperId"] == "kim_2024" and g["unit"] == "%"
    )
    lnp95 = next(p for p in kim_percent["points"] if p["name"] == "LNP95")
    assert (lnp95["bm"], lnp95["liver"]) == (4.4, 14.7)
    kim_screen = next(
        g
        for g in analysis["pareto"]
        if g["paperId"] == "kim_2024" and g["unit"] == "barcode counts"
    )
    assert len(kim_screen["points"]) == 26
    assert all(p["liver"] is not None for g in analysis["pareto"] for p in g["points"])
    dose_points = [p for g in analysis["dose"] for p in g["points"]]
    assert not any(
        "ex_vivo" in p["experiment"] or "peripheral_blood" in p["experiment"] for p in dose_points
    )
    lian_editing = next(p for p in dose_points if p["id"] == "lian_2024:E1_Cas9_BCL11A_Townes")
    assert lian_editing["dose"] == 3.0
    assert lian_editing["value"] == 5.2


def test_new_record_flows_into_all_relevant_charts_without_hand_editing(
    tmp_path, monkeypatch
) -> None:
    frame = pd.read_parquet(_EXTRACT._FEAT_PATH)
    records = json.loads(_EXTRACT._LITERATURE_RECORDS_PATH.read_text())["records"]
    new = deepcopy(next(r for r in records if r["source_paper"] == "hanafy_2025"))
    new.update(
        record_id="test_new_measurement", formulation_id="New-LNP", experiment_id="new_experiment"
    )
    new["efficacy"] = {
        "metric": "Paired percentage measurements",
        "bone_marrow_percent": 72.0,
        "liver_percent": 4.0,
    }
    row = frame.loc[frame.paper.eq("hanafy_2025")].iloc[0].copy()
    row["formulation_id"], row["experiment_id"] = new["formulation_id"], new["experiment_id"]
    augmented = pd.concat([frame, row.to_frame().T], ignore_index=True).astype(
        frame.dtypes.to_dict()
    )
    features_path = tmp_path / "features.parquet"
    records_path = tmp_path / "records.json"
    augmented.to_parquet(features_path)
    records_path.write_text(json.dumps({"records": [*records, new]}))
    monkeypatch.setattr(_EXTRACT, "_FEAT_PATH", features_path)
    monkeypatch.setattr(_EXTRACT, "_LITERATURE_RECORDS_PATH", records_path)
    data = _EXTRACT.build_data()
    assert data["stats"]["rows"] == 332
    assert len(data["formulations"]) == 332
    for view in ("pareto", "peg", "helper", "dose"):
        assert any(
            p["id"] == new["record_id"]
            for group in data["analysisData"][view]
            for p in group["points"]
        )
    assert data["analysisData"]["coverage"]["newPairs"] == 1


def test_missing_or_unrelated_measurements_do_not_become_chart_points() -> None:
    records = json.loads(_EXTRACT._LITERATURE_RECORDS_PATH.read_text())["records"]
    seed = deepcopy(next(r for r in records if r["source_paper"] == "hanafy_2025"))
    seed["efficacy"] = {
        "metric": "Relative improvement",
        "bone_marrow_percent": "3-fold",
        "liver_percent": 4,
    }
    assert literature_measurements([seed]) == []
    seed["efficacy"] = {"bone_marrow_percent": True, "liver_percent": 4}
    assert literature_measurements([seed]) == []
    seed["efficacy"] = {"bone_marrow_percent": 40, "liver_percent": 4}
    seed["delivery"]["target_organ"] = "lung"
    assert literature_measurements([seed]) == []
    seed["delivery"]["target_organ"] = "bone_marrow"
    seed["delivery"]["system"] = "ex_vivo"
    assert literature_measurements([seed]) == []
