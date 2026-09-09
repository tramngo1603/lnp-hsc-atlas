"""Tests for atlas analysis outputs."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "analyze_atlas", _ROOT / "scripts" / "analyze_atlas.py"
)
assert _SPEC is not None and _SPEC.loader is not None
_ANALYSIS = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_ANALYSIS)


def test_analysis_preserves_pareto_inputs_and_reports_matrix_summary() -> None:
    report = _ANALYSIS.build_report()
    pareto = report["pareto_and_bm_liver_correlation"]
    targets = report["matrix"]["target_distribution"]
    assert pareto["standardized_absolute_bm_liver_pairs"]["count"] == 0
    assert pareto["screen_barcode_counts"]["pareto_optimal"] == [
        "LNP84",
        "LNP85",
        "LNP95",
        "LNP111",
    ]
    assert pareto["validation_percentages"]["lnp_pareto_optimal"] == [
        "LNP67",
        "LNP108",
        "CD117/LNP",
    ]
    assert targets["labeled"] == 315
    assert targets["low"] == 184


def test_feature_correlations_exclude_boundary_rows() -> None:
    report = _ANALYSIS.build_report()
    dose = report["feature_target_correlations"]["all_features"]["dose_mg_per_kg"]
    assert dose["n"] < 333
    assert "exact 30% label boundary are excluded" in (
        report["feature_target_correlations"]["method"]
    )
    assert "label_boundary_case" not in report["feature_target_correlations"]["all_features"]
