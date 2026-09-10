"""Generate the atlas coverage report."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
_FEATURES = _ROOT / "data" / "features" / "hsc_features.parquet"
_LITERATURE_RECORDS_PATH = _ROOT / "data" / "literature_records.json"
_OUTPUT = _ROOT / "docs" / "COVERAGE_REPORT.md"
_ATLAS_ROWS = 331
_LITERATURE_RECORD_COUNT = 196

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
    records = json.loads(_LITERATURE_RECORDS_PATH.read_text())["records"]
    if df.shape != (_ATLAS_ROWS, 48):
        raise ValueError(f"expected {_ATLAS_ROWS} x 48 matrix, observed {df.shape}")
    if len(records) != _LITERATURE_RECORD_COUNT:
        raise ValueError(
            f"expected {_LITERATURE_RECORD_COUNT} literature records, observed {len(records)}"
        )

    complete_columns = sum(df[column].notna().all() for column in df.columns)
    descriptor_count = int(df["il_molecular_weight"].notna().sum())
    target_count = int(df["target"].notna().sum())
    unlabeled_count = len(df) - target_count
    core_composition_count = int(
        df[["ionizable_mol_pct", "helper_mol_pct", "cholesterol_mol_pct"]]
        .notna()
        .all(axis=1)
        .sum()
    )
    dose_count = int(df["dose_mg_per_kg"].notna().sum())
    rich_coverage = _rich_record_coverage(records)
    rich_counts = dict(rich_coverage)
    toxicity_detail_count = rich_counts["Any toxicity detail beyond reported flag"]

    lines = [
        "# Atlas Coverage Report",
        "",
        f"Generated from `data/features/hsc_features.parquet`. The matrix contains {len(df)} "
        f"rows across {df['paper'].nunique()} papers and 48 columns.",
        "",
        "## Method",
        "",
        "Coverage is the count of non-null cells. Numeric zero and boolean-style zero are "
        "valid populated values, especially in one-hot encodings. Coverage therefore measures "
        "availability, not feature prevalence. Data integrity and logical consistency are "
        "verified by `scripts/audit_combined_atlas.py`.",
        "",
        "## Summary",
        "",
        f"- {complete_columns}/48 columns are complete across all {len(df)} rows.",
        "- `label_boundary_case` marks four Lian 2024 rows whose exact 30% measurements "
        "retain their established `high` labels. The current rule is strictly `high >30%`.",
        f"- The supervised target is populated for {target_count}/{len(df)} rows "
        f"({target_count / len(df) * 100:.1f}%). The {unlabeled_count} unlabeled rows remain "
        "in the atlas "
        "but must be excluded from supervised training.",
        f"- Core ionizable/helper/cholesterol composition is available for "
        f"{core_composition_count}/{len(df)} rows "
        f"({core_composition_count / len(df) * 100:.1f}%).",
        f"- Dose is available for {dose_count}/{len(df)} rows "
        f"({dose_count / len(df) * 100:.1f}%). Absolute per-mouse doses are intentionally "
        "not converted to mg/kg.",
        f"- All eight ionizable-lipid descriptor columns cover {descriptor_count}/{len(df)} "
        f"({descriptor_count / len(df) * 100:.1f}%). Missing descriptors reflect proprietary "
        "or unverified lipid identities, not a failed calculation.",
        "",
        "## Coverage by matrix column",
        "",
        "| Column | Group | Coverage |",
        "| --- | --- | ---: |",
    ]

    for column in df.columns:
        lines.append(
            f"| `{column}` | {_group(column)} | {_cell(df[column])} |"
        )

    lines.extend(
        [
            "",
            "## Physicochemical and toxicity coverage",
            "",
            "Physicochemical and toxicity fields are retained in the rich flat records but are "
            "not projected into the current 48-column matrix. Adding them to the matrix would be "
            "a schema change, so their coverage is reported for the normalized rich-record "
            "collection separately.",
            "",
            "| Rich-record field | Coverage |",
            "| --- | ---: |",
        ]
    )
    for label, count in rich_coverage:
        lines.append(f"| {label} | {count}/{len(records)} ({count / len(records) * 100:.1f}%) |")

    lines.extend(
        [
            "",
            "Particle size, PDI, and encapsulation efficiency are well represented in the rich "
            "records because the Xu screen includes per-formulation characterization. The "
            "remaining physicochemical block is sparse: zeta potential covers "
            f"{rich_counts['Zeta potential']}/{len(records)} records, apparent pKa covers "
            f"{rich_counts['Apparent pKa']}/{len(records)}, morphology covers "
            f"{rich_counts['Morphology']}/{len(records)}, and stability covers "
            f"{rich_counts['Stability']}/{len(records)}. Toxicity is the largest evidence "
            "gap, with any detailed toxicity information in "
            f"{toxicity_detail_count}/{len(records)} records "
            f"({toxicity_detail_count / len(records) * 100:.1f}%). "
            "Missing values were not inferred.",
            "",
            "## Coverage limitations",
            "",
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
