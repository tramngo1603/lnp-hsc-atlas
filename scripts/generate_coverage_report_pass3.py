"""Generate the Pass 3 old/new/combined coverage report."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
_FEATURES = _ROOT / "data" / "features" / "hsc_features.parquet"
_NEW_RECORDS = _ROOT / "data" / "new_records_pass1.json"
_OUTPUT = _ROOT / "docs" / "COVERAGE_REPORT.md"
_OLD_ROWS = 135
_NEW_ROWS = 198

_METADATA = {
    "source",
    "paper",
    "formulation_id",
    "experiment_id",
    "assay_category",
    "composition_confidence",
    "label_boundary_case",
}
_COMPOSITION = {
    "ionizable_mol_pct",
    "helper_mol_pct",
    "cholesterol_mol_pct",
    "peg_mol_pct",
    "peg_chain_numeric",
    "covalent_lipid_mol_pct",
}
_RATIOS = {"il_to_helper_ratio", "il_to_chol_ratio", "chol_to_helper_ratio"}
_ENCODINGS = {
    "targeting_encoded",
    "helper_is_cationic",
    "species_mouse",
    "species_nhp",
    "species_human",
    "assay_barcode_delivery",
    "assay_depletion",
    "assay_editing",
    "assay_knockdown",
    "assay_protein_expression",
    "hl_dspc",
    "hl_dope",
    "hl_dotap",
    "hl_ddab",
    "hl_dotma",
    "hl_epc",
    "receptor_cd117",
    "receptor_cd45",
    "clone_2b8",
    "clone_ack2",
    "clone_igg",
}
_DESCRIPTORS = {
    "il_molecular_weight",
    "il_logp",
    "il_tpsa",
    "il_hbd",
    "il_hba",
    "il_rotatable_bonds",
    "il_num_rings",
    "il_heavy_atom_count",
}


def _group(column: str) -> str:
    if column in _METADATA:
        return "metadata"
    if column in _COMPOSITION:
        return "composition"
    if column in _RATIOS:
        return "engineered ratio"
    if column == "dose_mg_per_kg":
        return "dose"
    if column in _ENCODINGS:
        return "encoding"
    if column in _DESCRIPTORS:
        return "IL descriptor"
    if column == "target":
        return "label"
    if column == "metric_type":
        return "metric metadata"
    return "other"


def _cell(series: pd.Series) -> str:
    count = int(series.notna().sum())
    return f"{count}/{len(series)} ({count / len(series) * 100:.1f}%)"


def _filled(value: Any) -> bool:
    return value is not None and value != "" and value != [] and value != {}


def _rich_record_coverage(records: list[dict[str, Any]]) -> list[tuple[str, int]]:
    measurement_keys = {
        "pdi",
        "zeta_potential_mv",
        "encapsulation_efficiency_percent",
        "pka",
        "morphology",
        "stability",
    }

    def physical(record: dict[str, Any], field: str) -> bool:
        value = (record.get("physicochemical") or {}).get(field)
        return _filled(value)

    def size(record: dict[str, Any]) -> bool:
        return any(
            key.startswith("particle_size") and _filled(value)
            for key, value in (record.get("physicochemical") or {}).items()
        )

    def any_physical(record: dict[str, Any]) -> bool:
        return any(
            (key.startswith("particle_size") or key in measurement_keys) and _filled(value)
            for key, value in (record.get("physicochemical") or {}).items()
        )

    def toxicity_block(record: dict[str, Any]) -> bool:
        toxicity = record.get("toxicity")
        return isinstance(toxicity, dict) and any(_filled(value) for value in toxicity.values())

    def toxicity_detail(record: dict[str, Any]) -> bool:
        toxicity = record.get("toxicity")
        return isinstance(toxicity, dict) and any(
            key != "reported" and _filled(value) for key, value in toxicity.items()
        )

    return [
        ("Any physicochemical measurement", sum(any_physical(record) for record in records)),
        ("Particle size (any method)", sum(size(record) for record in records)),
        ("PDI", sum(physical(record, "pdi") for record in records)),
        (
            "Encapsulation efficiency",
            sum(physical(record, "encapsulation_efficiency_percent") for record in records),
        ),
        ("Zeta potential", sum(physical(record, "zeta_potential_mv") for record in records)),
        ("Apparent pKa", sum(physical(record, "pka") for record in records)),
        ("Morphology", sum(physical(record, "morphology") for record in records)),
        ("Stability", sum(physical(record, "stability") for record in records)),
        ("Any toxicity block", sum(toxicity_block(record) for record in records)),
        (
            "Any toxicity detail beyond reported flag",
            sum(toxicity_detail(record) for record in records),
        ),
    ]


def build_report() -> str:
    df = pd.read_parquet(_FEATURES)
    records = json.loads(_NEW_RECORDS.read_text())["records"]
    if df.shape != (_OLD_ROWS + _NEW_ROWS, 48):
        raise ValueError(f"expected 333 x 48 matrix, observed {df.shape}")
    if len(records) != _NEW_ROWS:
        raise ValueError(f"expected 198 new records, observed {len(records)}")

    old = df.iloc[:_OLD_ROWS]
    new = df.iloc[_OLD_ROWS:]
    complete_combined = sum(df[column].notna().all() for column in df.columns)
    descriptor_count = int(df["il_molecular_weight"].notna().sum())
    old_descriptor_count = int(old["il_molecular_weight"].notna().sum())
    new_descriptor_count = int(new["il_molecular_weight"].notna().sum())
    target_count = int(df["target"].notna().sum())

    lines = [
        "# Pass 3 Coverage Report",
        "",
        "Generated from `data/features/hsc_features.parquet` after Pass 3 consolidation. "
        "The matrix contains 135 protected baseline rows followed by 198 new rows, for "
        "333 rows across 19 papers and 48 columns.",
        "",
        "## Method",
        "",
        "Coverage is the count of non-null cells. Numeric zero and boolean-style zero are "
        "valid populated values, especially in one-hot encodings. Coverage therefore measures "
        "availability, not feature prevalence. The split boundary and value identity of the "
        "original 135 rows are verified by `scripts/audit_combined_pass3.py`.",
        "",
        "## Summary",
        "",
        f"- {complete_combined}/48 columns are complete across all 333 rows.",
        "- `label_boundary_case` marks four protected Lian 2024 rows whose exact 30% "
        "measurements retain v1 `high` labels. New rows use the strict `high >30%` rule.",
        f"- The supervised target is populated for {target_count}/333 rows "
        f"({target_count / len(df) * 100:.1f}%). The 18 unlabeled rows remain in the atlas "
        "but must be excluded from supervised training.",
        "- Core molar composition coverage rises from 63/135 (46.7%) in the old block to "
        "187/198 (94.4%) in the new block. Combined ionizable/helper/cholesterol coverage is "
        "250/333 (75.1%).",
        "- Dose coverage rises from 59/135 (43.7%) to 187/198 (94.4%), yielding 246/333 "
        "(73.9%) combined. Absolute per-mouse doses are intentionally not converted to mg/kg.",
        f"- All eight ionizable-lipid descriptor columns cover {descriptor_count}/333 "
        f"({descriptor_count / len(df) * 100:.1f}%): {old_descriptor_count}/135 old and "
        f"{new_descriptor_count}/198 new. The low new-record rate reflects proprietary or "
        "unverified lipid identities, not a failed calculation.",
        "",
        "## Coverage by matrix column",
        "",
        "| Column | Group | Old 135 | New 198 | Combined 333 |",
        "| --- | --- | ---: | ---: | ---: |",
    ]

    for column in df.columns:
        lines.append(
            f"| `{column}` | {_group(column)} | {_cell(old[column])} | "
            f"{_cell(new[column])} | {_cell(df[column])} |"
        )

    lines.extend(
        [
            "",
            "## Physicochemical and toxicity coverage",
            "",
            "Physicochemical and toxicity fields are retained in the rich flat records but are "
            "not projected into the current 48-column matrix. Adding them to the matrix would be "
            "a schema change, so this release reports their new-record coverage separately. A "
            "row-level old-versus-new comparison is not claimed because the original annotation "
            "layer is not normalized one-to-one with the 135 feature rows.",
            "",
            "| Rich-record field | New-record coverage |",
            "| --- | ---: |",
        ]
    )
    for label, count in _rich_record_coverage(records):
        lines.append(f"| {label} | {count}/{len(records)} ({count / len(records) * 100:.1f}%) |")

    lines.extend(
        [
            "",
            "Particle size, PDI, and encapsulation efficiency are well represented in the new "
            "records because the Xu screen includes per-formulation characterization. The "
            "remaining physicochemical block is sparse: zeta potential and apparent pKa each "
            "cover only 3/198 new records, while morphology and stability each cover 2/198. "
            "Toxicity is the largest evidence gap, with any detailed toxicity information in "
            "13/198 new records (6.6%). Missing values were not inferred.",
            "",
            "## Coverage limitations and open sources",
            "",
            "- The two Xue 2022 rows remain `partial_pending_main_text`; efficacy and numeric "
            "ALT/AST values are not backfilled from figures.",
            "- Ramishetti 2020, Zhu 2026, and Dacoba 2025 remain paywalled source stubs and do "
            "not contribute matrix rows.",
            "- Chappell 2024 composition remains null. Breda 2023 is analog support only and "
            "was not copied into those records.",
            "- Figure-only efficacy for Chander, Peng, Zhao, and Iida remains null. The only "
            "approved figure estimates are the user-confirmed PRELIVE fields.",
            "- Zero-filled one-hot columns are structurally complete, but rare positive classes "
            "can still be statistically weak. Use prevalence and paper-grouped validation in "
            "addition to this availability report.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    _OUTPUT.write_text(build_report())
    print(f"Wrote {_OUTPUT.relative_to(_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
