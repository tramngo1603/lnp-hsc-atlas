"""Tests for the Pass 3 combined-data audit."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "audit_combined_pass3", _ROOT / "scripts" / "audit_combined_pass3.py"
)
assert _SPEC is not None and _SPEC.loader is not None
_AUDIT = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_AUDIT)


def test_release_audit_has_no_blocking_errors() -> None:
    report = _AUDIT.build_report()
    assert report["dataset"] == {
        "old_rows": 135,
        "new_rows": 198,
        "combined_rows": 333,
        "columns": 48,
        "papers": 19,
        "paper_row_counts": report["dataset"]["paper_row_counts"],
    }
    assert report["logical_contradiction_scan"]["errors"] == []
    assert report["invariants"]["original_135_value_identical_to_77c8b7d"] is True
    assert report["invariants"]["all_v2_values_identical_before_marker"] is True
    assert report["invariants"]["legacy_lian_values_and_labels_match_v2"] is True
    assert report["invariants"]["data_hsc_matches_77c8b7d"] is True


def test_legacy_lian_boundary_is_marked_and_not_an_error() -> None:
    report = _AUDIT.build_report()
    scan = report["logical_contradiction_scan"]
    boundary = next(
        item
        for item in scan["informational"]
        if item["id"] == "legacy_lian_30_percent_boundary"
    )
    assert boundary["status"] == "documented_boundary_convention"
    assert len(boundary["records"]) == 4
    assert not any(item["id"] == boundary["id"] for item in scan["warnings"])
    marker_check = next(
        item for item in scan["checks"] if item["id"] == "label_boundary_marker"
    )
    assert marker_check["status"] == "pass"


def test_known_cross_layer_decisions_are_explicit() -> None:
    report = _AUDIT.build_report()
    palchaudhuri = report["dedupe"]["palchaudhuri_tessera_decision"]
    chappell = report["dedupe"]["chappell_breda_decision"]
    assert palchaudhuri["same_source_confirmed"] is True
    assert palchaudhuri["tessera_annotation_matrix_rows"] == 0
    assert palchaudhuri["canonical_matrix_rows"] == 3
    assert chappell["duplicate_identity_groups"] == []
    assert chappell["rich_record_composition_null"] is True
    assert chappell["matrix_composition_null"] is True
    assert chappell["composition_backfilled"] is False
