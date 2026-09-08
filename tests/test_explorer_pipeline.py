"""Regression tests for the combined-data explorer pipeline."""

from __future__ import annotations

import importlib.util
import json
import re
from collections import Counter
from pathlib import Path

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


def test_extracted_data_matches_combined_release() -> None:
    data = _EXTRACT.build_data()

    assert data["stats"] == {
        "rows": 333,
        "sources": 19,
        "columns": 48,
        "labeled": 315,
        "addedRows": 198,
        "addedSources": 15,
        "modelFeatures": 37,
        "descriptorRows": 154,
    }
    assert len(data["formulations"]) == 333
    assert len(data["papers"]) == 19
    paper_counts = Counter(row["paperId"] for row in data["formulations"])
    assert paper_counts["xu_2026"] == 148
    assert paper_counts["hanafy_2025"] == 14
    assert paper_counts["hofstraat_2025"] == 9

    assert data["coverageStats"]["completeColumns"] == 30
    assert data["coverageStats"]["totalColumns"] == 48
    assert data["labelDistribution"]["baseline"]["lowShare"] == 45.9
    assert data["labelDistribution"]["combined"]["lowShare"] == 58.4
    assert data["validationSummary"]["formulationGrouped"][
        "formulationDisjoint"
    ] is True
    assert data["validationSummary"]["rowRandom"]["formulationDisjoint"] is False

    boundary_rows = [row for row in data["formulations"] if row["boundary"]]
    assert len(boundary_rows) == 4
    assert {row["cls"] for row in boundary_rows} == {"high"}
    record_types = Counter(row["recordType"] for row in data["formulations"])
    assert record_types == {
        "baseline": 135,
        "screen": 142,
        "detailed": 51,
        "abstract-only": 3,
        "partial": 2,
    }


def test_patcher_replaces_every_required_block() -> None:
    data = _EXTRACT.build_data()
    jsx = "\n".join(
        f"// DATA:{key}\nconst old = null;\n// END:{key}"
        for key in _PATCH._KEY_TO_VAR
    )

    patched, count, missing = _PATCH.patch_jsx(jsx, data)

    assert missing == []
    assert count == len(_PATCH._KEY_TO_VAR)
    assert "const formulations = [" in patched
    assert "const validationSummary = {" in patched


def test_deployed_explorer_embeds_v2_data_and_matches_root_copy() -> None:
    deployed = (_ROOT / "explorer" / "src" / "App.jsx").read_text()
    root_copy = (_ROOT / "explorer.jsx").read_text()

    assert deployed == root_copy
    assert chr(0x2014) not in deployed
    assert len(_embedded_block(deployed, "formulations")) == 333
    assert len(_embedded_block(deployed, "papers")) == 19
    stats = _embedded_block(deployed, "stats")
    assert stats["rows"] == 333
    assert stats["sources"] == 19
