"""Tests for the generated atlas coverage report."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "generate_coverage_report",
    _ROOT / "scripts" / "generate_coverage_report.py",
)
assert _SPEC is not None and _SPEC.loader is not None
_COVERAGE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_COVERAGE)


def test_report_contains_all_48_columns_and_sparse_blocks() -> None:
    report = _COVERAGE.build_report()
    matrix_rows = [line for line in report.splitlines() if line.startswith("| `")]
    assert len(matrix_rows) == 48
    assert "154/331 (46.5%)" in report
    assert "Any toxicity detail beyond reported flag | 11/196 (5.6%)" in report
    assert "partial_pending_main_text" not in report
    assert "pending_paywall" not in report
    assert "`label_boundary_case`" in report
    assert "| Column | Group | Coverage |" in report
