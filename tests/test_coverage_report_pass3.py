"""Tests for the generated Pass 3 coverage report."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "generate_coverage_report_pass3",
    _ROOT / "scripts" / "generate_coverage_report_pass3.py",
)
assert _SPEC is not None and _SPEC.loader is not None
_COVERAGE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_COVERAGE)


def test_report_contains_all_48_columns_and_sparse_blocks() -> None:
    report = _COVERAGE.build_report()
    matrix_rows = [line for line in report.splitlines() if line.startswith("| `")]
    assert len(matrix_rows) == 48
    assert "154/333 (46.2%)" in report
    assert "Any toxicity detail beyond reported flag | 13/198 (6.6%)" in report
    assert "partial_pending_main_text" in report
    assert "`label_boundary_case`" in report
