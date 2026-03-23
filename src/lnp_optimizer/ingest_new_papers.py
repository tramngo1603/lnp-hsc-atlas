"""Ingest newly annotated papers into dataset and comparison tables.

Parses annotations/paper_annotations.json and extracts:
- Feature matrix rows (for LNP ML pipeline)
- Therapeutic window comparison rows (for cross-platform analysis)
- Pareto points (for BM vs liver tradeoff)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent


def load_annotations(path: Path | None = None) -> list[dict[str, Any]]:
    """Load paper annotations JSON.

    Args:
        path: Path to paper_annotations.json.

    Returns:
        List of paper annotation dicts.
    """
    if path is None:
        path = PROJECT_ROOT / "annotations" / "paper_annotations.json"
    with open(path) as f:
        result: list[dict[str, Any]] = json.load(f)
    return result


def extract_kim_ash_2025_rows(
    annotations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Extract feature matrix rows from Kim ASH 2025.

    Kim ASH 2025 uses LNP67 (already in dataset) in humanized mice.
    Adds new rows with existing formulation features + new species/dose.

    Args:
        annotations: All paper annotations.

    Returns:
        List of dicts suitable for hsc_features addition.
    """
    kim_ash = _find_paper(annotations, "KIM_2025_ASH")
    if kim_ash is None:
        logger.warning("Kim ASH 2025 not found in annotations")
        return []

    rows: list[dict[str, Any]] = []
    for exp in kim_ash.get("experiments", []):
        if exp["id"] == "E1_humanized_mouse_aVHH_2mpk":
            rows.append({
                "paper": "Kim_2025_ASH",
                "formulation_name": "LNP67",
                "source": "kim_2025_ash",
                "species": "humanized_mouse",
                "model_system": "in_vivo",
                "dose_mg_per_kg": 2.0,
                "hsc_transfection_percent": 37.0,
                "hsc_definition": "CD34+CD38-CD90+CD45RA-",
                "hsc_metric": "protein_expression_pct",
                "assay_category": "protein_expression",
                "hsc_efficacy_class": "high",
                "liver_percent": None,
                "bone_marrow_percent": None,
                "targeting_strategy": "intrinsic_tropism",
                # LNP67 formulation features (from Kim 2024)
                "ionizable_lipid": "PPZ-A10",
                "ionizable_mol_pct": 35.0,
                "helper_lipid": "DOTAP",
                "helper_mol_pct": 15.0,
                "cholesterol_mol_pct": 47.5,
                "peg_lipid": "DMG-PEG2000",
                "peg_mol_pct": 2.5,
                "peg_chain": "C14",
                "confidence": "HIGH",
                "notes": (
                    "Median 37% (range 22-65%) aVHH+ in human "
                    "CD34+CD38-CD90+CD45RA- HSCs. Liver NOT reported."
                ),
            })

            # Subtype rows
            subtypes = [
                ("CMP", 70.45, "CD34+CD38+CD45RA-CD135+"),
                ("GMP", 59.55, "CD34+CD38+CD45RA+CD135+"),
                ("MEP", 52.15, "CD34+CD38+CD45RA-CD135-"),
            ]
            for subtype, pct, definition in subtypes:
                rows.append({
                    "paper": "Kim_2025_ASH",
                    "formulation_name": "LNP67",
                    "source": "kim_2025_ash",
                    "species": "humanized_mouse",
                    "model_system": "in_vivo",
                    "dose_mg_per_kg": 2.0,
                    "hsc_transfection_percent": pct,
                    "hsc_definition": definition,
                    "hsc_metric": "protein_expression_pct",
                    "assay_category": "protein_expression",
                    "hsc_efficacy_class": "high",
                    "liver_percent": None,
                    "bone_marrow_percent": None,
                    "targeting_strategy": "intrinsic_tropism",
                    "ionizable_lipid": "PPZ-A10",
                    "ionizable_mol_pct": 35.0,
                    "helper_lipid": "DOTAP",
                    "helper_mol_pct": 15.0,
                    "cholesterol_mol_pct": 47.5,
                    "peg_lipid": "DMG-PEG2000",
                    "peg_mol_pct": 2.5,
                    "peg_chain": "C14",
                    "confidence": "HIGH",
                    "notes": f"{subtype}: {pct}% (Kim ASH 2025)",
                })

    logger.info("Extracted %d rows from Kim ASH 2025", len(rows))
    return rows


def extract_comparison_benchmarks(
    annotations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Extract cross-platform comparison rows from all new papers.

    These go into cross_platform_comparison.json, NOT the ML feature matrix.

    Args:
        annotations: All paper annotations.

    Returns:
        List of benchmark comparison dicts.
    """
    benchmarks: list[dict[str, Any]] = []

    # Editas EHA 2025
    editas = _find_paper(annotations, "GUPTA_2025_EHA")
    if editas:
        benchmarks.extend(_extract_editas_benchmarks(editas))

    # Ensoma NBT 2025
    ensoma = _find_paper(annotations, "BOTCHKAREV_2025_NATBIOTECH")
    if ensoma:
        benchmarks.extend(_extract_ensoma_benchmarks(ensoma))

    # Kim ASH 2025
    kim_ash = _find_paper(annotations, "KIM_2025_ASH")
    if kim_ash:
        benchmarks.extend(_extract_kim_ash_benchmarks(kim_ash))

    logger.info("Extracted %d comparison benchmarks", len(benchmarks))
    return benchmarks


def build_therapeutic_window_entries(
    benchmarks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build therapeutic window entries from benchmarks.

    Args:
        benchmarks: Comparison benchmark dicts.

    Returns:
        List of therapeutic window entry dicts.
    """
    entries: list[dict[str, Any]] = []
    for bm in benchmarks:
        entry: dict[str, Any] = {
            "name": bm["name"],
            "platform": bm["platform"],
            "paper": bm["paper"],
            "species": bm["species"],
            "targeting": bm.get("targeting", "unknown"),
            "dose_mg_per_kg": bm.get("dose_mg_per_kg"),
            "hsc_metric": bm.get("hsc_metric", "unknown"),
            "hsc_value": bm.get("hsc_value"),
            "hsc_definition": bm.get("hsc_definition"),
            "timepoint": bm.get("timepoint"),
            "liver_pct": bm.get("liver_pct"),
            "liver_note": bm.get("liver_note"),
            "conditioning": bm.get("conditioning", "none"),
            "is_lnp": bm.get("is_lnp", True),
            "is_comparator": bm.get("is_comparator", True),
        }
        entries.append(entry)
    return entries


def _find_paper(
    annotations: list[dict[str, Any]], paper_id: str,
) -> dict[str, Any] | None:
    """Find a paper by its ID in annotations list."""
    for paper in annotations:
        pid = paper.get("paper", {}).get("id", "")
        if pid == paper_id:
            return paper
    return None


def _extract_editas_benchmarks(
    paper: dict[str, Any],
) -> list[dict[str, Any]]:
    """Extract Editas EHA 2025 benchmark rows."""
    benchmarks: list[dict[str, Any]] = []
    for exp in paper.get("experiments", []):
        if exp["id"] == "E1_NHP_GFP_delivery_24h":
            benchmarks.append({
                "name": "Editas tLNP (NHP, GFP delivery)",
                "platform": "tLNP (proprietary)",
                "paper": "Gupta 2025 EHA",
                "species": "NHP",
                "targeting": "proprietary moiety",
                "dose_mg_per_kg": 2.0,
                "hsc_value": 75.0,
                "hsc_metric": "GFP protein expression (%)",
                "hsc_definition": "CD34+CD90+CD45RA-",
                "timepoint": "24 hours",
                "liver_pct": None,
                "liver_note": (
                    "Qualitative 'minimal in hepatocytes' by ISH/IHC; "
                    "no quantitative %"
                ),
                "conditioning": "none",
                "is_lnp": True,
                "is_comparator": True,
            })
        elif exp["id"] == "E2_NHP_HBG_editing_5mo":
            benchmarks.append({
                "name": "Editas tLNP (NHP, HBG editing)",
                "platform": "tLNP (proprietary)",
                "paper": "Gupta 2025 EHA",
                "species": "NHP",
                "targeting": "proprietary moiety",
                "dose_mg_per_kg": 2.0,
                "hsc_value": 58.0,
                "hsc_metric": "HBG1/2 promoter editing (%)",
                "hsc_definition": "CD34+CD90+CD45RA-",
                "timepoint": "5 months",
                "liver_pct": None,
                "liver_note": "Not assessed in editing group",
                "conditioning": "none",
                "is_lnp": True,
                "is_comparator": True,
            })
        elif exp["id"] == "E3_humanized_mouse_HBG_editing":
            benchmarks.append({
                "name": "Editas tLNP (humanized mouse, HBG editing)",
                "platform": "tLNP (proprietary)",
                "paper": "Gupta 2025 EHA",
                "species": "humanized_mouse",
                "targeting": "proprietary moiety",
                "dose_mg_per_kg": None,
                "hsc_value": exp.get("results", {}).get(
                    "on_target_editing_pct",
                ),
                "hsc_metric": "HBG1/2 promoter editing (%)",
                "hsc_definition": "CD34+CD90+CD45RA-",
                "timepoint": "8 weeks",
                "liver_pct": None,
                "liver_note": "Not reported",
                "conditioning": "busulfan (for engraftment)",
                "is_lnp": True,
                "is_comparator": True,
            })
    return benchmarks


def _extract_ensoma_benchmarks(
    paper: dict[str, Any],
) -> list[dict[str, Any]]:
    """Extract Ensoma NBT 2025 benchmark rows."""
    benchmarks: list[dict[str, Any]] = []
    for exp in paper.get("experiments", []):
        if exp["id"] == "E1_BaEVTR_B2M_LT_HSC_8wk":
            benchmarks.append({
                "name": "Ensoma BaEVTR VLP (humanized mouse)",
                "platform": "VLP",
                "paper": "Botchkarev 2025 Nat Biotech",
                "species": "humanized_mouse",
                "targeting": "BaEVTR envelope (ASCT1/2 binding)",
                "dose_mg_per_kg": None,
                "dose_note": (
                    "VLP dosing in transduction units, not directly "
                    "comparable to LNP mg/kg"
                ),
                "hsc_value": 31.0,
                "hsc_metric": "B2M editing (HTS)",
                "hsc_definition": "LT-HSPC (long-term engrafting)",
                "timepoint": "8 weeks",
                "liver_pct": 0.5,
                "liver_note": (
                    "Near-zero hepatocyte transduction demonstrated "
                    "in humanized liver mice"
                ),
                "conditioning": "none",
                "is_lnp": False,
                "is_comparator": True,
            })
        elif exp["id"] == "E2_BaEVTR_BCL11A_5d":
            benchmarks.append({
                "name": "Ensoma BaEVTR VLP (BCL11A, 5d)",
                "platform": "VLP",
                "paper": "Botchkarev 2025 Nat Biotech",
                "species": "humanized_mouse",
                "targeting": "BaEVTR envelope (ASCT1/2 binding)",
                "dose_mg_per_kg": None,
                "hsc_value": 26.0,
                "hsc_metric": "BCL11A editing (%)",
                "hsc_definition": "HSPC",
                "timepoint": "5 days",
                "liver_pct": None,
                "liver_note": "Not assessed at 5d timepoint",
                "conditioning": "none",
                "is_lnp": False,
                "is_comparator": True,
            })
        elif exp["id"] == "E3_BaEVTR_HBG_5d":
            benchmarks.append({
                "name": "Ensoma BaEVTR VLP (HBG1/2, 5d)",
                "platform": "VLP",
                "paper": "Botchkarev 2025 Nat Biotech",
                "species": "humanized_mouse",
                "targeting": "BaEVTR envelope (ASCT1/2 binding)",
                "dose_mg_per_kg": None,
                "hsc_value": 7.5,
                "hsc_metric": "HBG1/2 editing (%)",
                "hsc_definition": "HSPC",
                "timepoint": "5 days",
                "liver_pct": None,
                "liver_note": "Not assessed at 5d timepoint",
                "conditioning": "none",
                "is_lnp": False,
                "is_comparator": True,
            })
    return benchmarks


def _extract_kim_ash_benchmarks(
    paper: dict[str, Any],
) -> list[dict[str, Any]]:
    """Extract Kim ASH 2025 benchmark rows."""
    benchmarks: list[dict[str, Any]] = []
    for exp in paper.get("experiments", []):
        if exp["id"] == "E1_humanized_mouse_aVHH_2mpk":
            benchmarks.append({
                "name": "Kim LNP67 (humanized mouse)",
                "platform": "LNP",
                "paper": "Kim 2025 ASH",
                "species": "humanized_mouse",
                "targeting": "none (antibody-free)",
                "dose_mg_per_kg": 2.0,
                "hsc_value": 37.0,
                "hsc_metric": "aVHH protein expression (%)",
                "hsc_definition": "CD34+CD38-CD90+CD45RA-",
                "timepoint": "16 hours",
                "liver_pct": None,
                "liver_note": "Not reported in ASH abstract",
                "conditioning": (
                    "busulfan 12.5 mg/kg (for engraftment only)"
                ),
                "is_lnp": True,
                "is_comparator": False,
            })
    return benchmarks


def save_cross_platform_comparison(
    benchmarks: list[dict[str, Any]],
    output_path: Path | None = None,
) -> Path:
    """Save cross-platform comparison to JSON.

    Args:
        benchmarks: Comparison benchmark dicts.
        output_path: Output file path.

    Returns:
        Path to saved file.
    """
    if output_path is None:
        output_path = (
            PROJECT_ROOT / "data" / "models" / "cross_platform_comparison.json"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(benchmarks, f, indent=2, default=str)
    logger.info("Saved %d benchmarks to %s", len(benchmarks), output_path)
    return output_path


def main() -> None:
    """Run full ingestion pipeline for new papers."""
    annotations = load_annotations()

    # Extract feature matrix rows (Kim ASH 2025 only)
    kim_rows = extract_kim_ash_2025_rows(annotations)
    print(f"Kim ASH 2025: {len(kim_rows)} new feature matrix rows")
    for row in kim_rows:
        print(
            f"  {row['formulation_name']} | "
            f"{row['species']} | "
            f"{row['dose_mg_per_kg']} mg/kg | "
            f"{row['hsc_transfection_percent']}% {row['hsc_definition']}"
        )

    # Extract comparison benchmarks (all papers)
    benchmarks = extract_comparison_benchmarks(annotations)
    print(f"\nCross-platform benchmarks: {len(benchmarks)} entries")
    for bm in benchmarks:
        print(
            f"  {bm['name']} | "
            f"{bm['platform']} | "
            f"{bm['species']} | "
            f"HSC={bm.get('hsc_value', '?')}% | "
            f"Liver={bm.get('liver_pct', 'N/A')}"
        )

    # Save cross-platform comparison
    save_cross_platform_comparison(benchmarks)

    # Build therapeutic window entries
    tw_entries = build_therapeutic_window_entries(benchmarks)
    tw_path = (
        PROJECT_ROOT / "data" / "models" / "therapeutic_window_new_entries.json"
    )
    tw_path.parent.mkdir(parents=True, exist_ok=True)
    with open(tw_path, "w") as f:
        json.dump(tw_entries, f, indent=2, default=str)
    print(f"\nTherapeutic window entries saved to {tw_path}")


if __name__ == "__main__":
    main()
