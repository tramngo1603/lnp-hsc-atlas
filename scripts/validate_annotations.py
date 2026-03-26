"""Validate annotation JSON files for completeness and consistency.

Exit code 0 if all pass, 1 if any errors (warnings are non-blocking).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_ANN_DIR = _ROOT / "annotations"

_VALID_HELPERS = {"DOTAP", "DDAB", "DOTMA", "DOPE", "DSPC", "EPC", "18:1 EPC", "NONE", "ESM"}
_VALID_CONFIDENCE = {"HIGH", "MEDIUM", "LOW", "DISPROVEN",
                     "HIGH_n3", "MEDIUM_n1", "LOW_n1"}
_VALID_SPECIES = {"mouse", "nhp", "human", "humanized_mouse"}
_VALID_METRIC = {"editing_pct", "reporter_pct", "barcode_normalized", "luminescence"}


def _check_paper(data: dict, path: str) -> tuple[list[str], list[str]]:
    """Validate a single annotation file. Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    # Must have paper field (accept both 'paper' and 'paper_metadata' schemas)
    paper = data.get("paper") or data.get("paper_metadata")
    if not paper:
        errors.append(f"{path}: missing 'paper' or 'paper_metadata' field")
        return errors, warnings

    pid = paper.get("id", paper.get("pmid", path))

    for field in ("title", "authors"):
        if not paper.get(field):
            warnings.append(f"{pid}: paper.{field} missing")

    if paper.get("doi_or_id") and not (
        paper["doi_or_id"].startswith("10.") or paper["doi_or_id"].startswith("ASH")
        or "press" in paper["doi_or_id"].lower()
    ):
        warnings.append(f"{pid}: unusual DOI format: {paper['doi_or_id']}")

    # Check formulations
    formulations = data.get("formulations", data.get("formulations_screen", {}).get("formulations", []))
    if not formulations:
        warnings.append(f"{pid}: no formulations array")

    seen_ids: set[str] = set()
    for i, form in enumerate(formulations):
        fid = form.get("id", f"formulation_{i}")

        if fid in seen_ids:
            errors.append(f"{pid}/{fid}: duplicate formulation ID")
        seen_ids.add(fid)

        # Check mol% sums if available
        mol_fields = ["ionizable_lipid_mol_pct", "ionizable_mol_pct",
                       "helper_lipid_mol_pct", "helper_mol_pct",
                       "cholesterol_mol_pct", "peg_lipid_mol_pct", "peg_mol_pct"]
        mol_vals = []
        for mf in mol_fields:
            v = form.get(mf)
            if v is not None and isinstance(v, (int, float)):
                mol_vals.append(v)

        if len(mol_vals) >= 4:
            total = sum(mol_vals)
            # Account for covalent lipid
            cov = form.get("covalent_lipid_mol_pct", 0) or 0
            total += cov
            if not (90 <= total <= 110):
                warnings.append(f"{pid}/{fid}: mol% sum = {total:.1f} (expected ~100)")

        # Confidence check
        conf = form.get("confidence", form.get("composition_confidence"))
        if conf and isinstance(conf, str) and conf not in _VALID_CONFIDENCE:
            warnings.append(f"{pid}/{fid}: unknown confidence '{conf}'")

    return errors, warnings


def main() -> int:
    """Run validation on all annotation JSONs."""
    total_errors: list[str] = []
    total_warnings: list[str] = []
    n_files = 0

    for f in sorted(_ANN_DIR.glob("*.json")):
        if f.name in ("kim_2024_experiments.json",):
            continue
        try:
            data = json.loads(f.read_text())
        except json.JSONDecodeError as e:
            total_errors.append(f"{f.name}: invalid JSON: {e}")
            continue

        n_files += 1

        # Handle both single-paper and multi-paper formats
        if isinstance(data, list):
            for entry in data:
                errs, warns = _check_paper(entry, f.name)
                total_errors.extend(errs)
                total_warnings.extend(warns)
        else:
            errs, warns = _check_paper(data, f.name)
            total_errors.extend(errs)
            total_warnings.extend(warns)

    print(f"Validated {n_files} annotation files")

    if total_warnings:
        print(f"\n⚠ {len(total_warnings)} warnings:")
        for w in total_warnings:
            print(f"  {w}")

    if total_errors:
        print(f"\n✗ {len(total_errors)} errors:")
        for e in total_errors:
            print(f"  {e}")
        return 1

    print("✓ All validations passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
