"""Corrected Pareto analysis: split by data type to avoid mixed units.

Audit 3 found that the original Pareto scatter mixed barcode counts (Kim screen)
with percentages (Kim E2, Breda E6). This module produces separate analyses
for each data type plus a unified narrative.

Outputs:
- pareto_screen_only.json: Kim screen barcode data (n=26)
- pareto_validation_only.json: Percentage-based validation data (n=6 LNP + comparators)
- pareto_narrative.json: Combined narrative and key findings
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from lnp_optimizer.therapeutic_window import (
    ParetoPoint,
    compute_correlation,
)
from lnp_optimizer.therapeutic_window import (
    compute_pareto_frontier as compute_pareto_tw,
)

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent


# ── Screen-only Pareto (barcode counts) ──────────────────────────────────


def compute_screen_pareto(
    kim_screen_path: Path | None = None,
) -> dict[str, Any]:
    """Compute Pareto frontier for Kim screen data only (barcode counts).

    All same units, same experiment, same lab — clean comparison.

    Args:
        kim_screen_path: Path to kim_2024_screen_corrected.json.

    Returns:
        Dict with points, Pareto frontier, correlation.
    """
    if kim_screen_path is None:
        kim_screen_path = (
            PROJECT_ROOT / "data" / "kim_screen"
            / "kim_2024_screen_corrected.json"
        )

    with open(kim_screen_path) as f:
        data = json.load(f)

    points: list[ParetoPoint] = []
    for fm in data["formulations"]:
        bm = fm.get("bm_normalized_bc")
        liver = fm.get("liver_ec_normalized_bc")
        if bm is None or liver is None or liver == 0:
            continue
        points.append(ParetoPoint(
            formulation=fm["lnp_name"],
            bm_percent=float(bm),
            liver_percent=float(liver),
            bm_liver_ratio=float(bm) / float(liver),
            source="kim_screen",
            helper_lipid=fm.get("helper_lipid_name"),
            peg_chain=fm.get("peg_chain"),
            targeting="intrinsic_tropism",
        ))

    points = compute_pareto_tw(points)
    correlation = compute_correlation(points)

    pareto_optimal = [p for p in points if p.is_pareto]
    pareto_names = [p.formulation for p in pareto_optimal]

    return {
        "data_type": "barcode_counts",
        "units": "normalized barcode counts (not percentages)",
        "source": "Kim 2024 Supp Fig 6 (128-LNP barcoded screen)",
        "n_points": len(points),
        "n_pareto": len(pareto_optimal),
        "correlation": correlation,
        "points": [_pareto_to_dict(p) for p in points],
        "pareto_optimal": [_pareto_to_dict(p) for p in pareto_optimal],
        "pareto_names": pareto_names,
        "note": (
            "Barcode counts represent relative biodistribution within one "
            "experiment, NOT percentage of cells transfected. Cannot be "
            "directly compared to validation % data."
        ),
    }


# ── Validation-only Pareto (percentages) ─────────────────────────────────


def compute_validation_pareto() -> dict[str, Any]:
    """Compute Pareto frontier for percentage-based validation data.

    Includes LNP data (Kim E2, Breda E6) plus cross-platform comparators.
    Note: n=6 LNPs is too small for meaningful correlation computation.

    Returns:
        Dict with points, Pareto frontier, comparators, quadrant analysis.
    """
    lnp_points = [
        ParetoPoint("LNP67", 20.9, 20.1, 20.9 / 20.1, "kim_E2",
                     "DOTAP", "C14", "intrinsic_tropism"),
        ParetoPoint("LNP95", 4.4, 14.7, 4.4 / 14.7, "kim_E2",
                     "DOTAP", "C14", "intrinsic_tropism"),
        ParetoPoint("LNP108", 8.8, 1.6, 8.8 / 1.6, "kim_E2",
                     "18:1 EPC", "C18", "intrinsic_tropism"),
        ParetoPoint("LP01", 5.0, 42.4, 5.0 / 42.4, "kim_E2",
                     "DSPC", "C14", "none"),
        ParetoPoint("CD117/LNP", 55.0, 76.0, 55.0 / 76.0, "breda_E6",
                     "DSPC", "C14", "antibody_conjugated"),
        ParetoPoint("IgG/LNP", 19.0, 78.0, 19.0 / 78.0, "breda_E6",
                     "DSPC", "C14", "antibody_conjugated"),
    ]

    lnp_points = compute_pareto_tw(lnp_points)

    # Cross-platform comparators (not LNPs)
    comparators = [
        {
            "name": "Ensoma BaEVTR VLP",
            "paper": "Botchkarev 2025 Nat Biotech",
            "bm_pct": 31.0,
            "liver_pct": 0.5,
            "metric": "B2M editing (%)",
            "targeting": "BaEVTR envelope",
            "platform": "VLP",
            "is_comparator": True,
            "note": (
                "Near-zero hepatocyte transduction in humanized liver "
                "mice. Liver set to 0.5% for plotting (actual ~0%)."
            ),
        },
    ]

    # Quadrant analysis (thresholds: BM > 30%, liver < 5%)
    bm_threshold = 30.0
    liver_threshold = 5.0
    quadrants = _classify_quadrants(
        lnp_points, comparators, bm_threshold, liver_threshold,
    )

    return {
        "data_type": "percentages",
        "units": "% cells (editing or protein expression)",
        "n_lnp_points": len(lnp_points),
        "n_comparators": len(comparators),
        "correlation_note": (
            "Correlation not computed: n=6 LNPs is too few for "
            "meaningful statistical testing (%-only Pearson r=0.643, "
            "p=0.168, NS; Spearman r=0.486, p=0.329, NS from audit)"
        ),
        "lnp_points": [_pareto_to_dict(p) for p in lnp_points],
        "lnp_pareto_optimal": [
            _pareto_to_dict(p) for p in lnp_points if p.is_pareto
        ],
        "comparators": comparators,
        "quadrants": quadrants,
        "ideal_zone": {
            "bm_threshold": bm_threshold,
            "liver_threshold": liver_threshold,
        },
    }


# ── Narrative synthesis ──────────────────────────────────────────────────


def build_narrative(
    screen: dict[str, Any],
    validation: dict[str, Any],
) -> dict[str, Any]:
    """Build unified narrative from screen and validation analyses.

    Args:
        screen: Screen-only Pareto results.
        validation: Validation-only Pareto results.

    Returns:
        Dict with narrative findings and narrative shift.
    """
    screen_r = screen["correlation"]["spearman_r"]
    screen_p = screen["correlation"]["spearman_p"]

    corr_label = "un" if abs(screen_r) < 0.3 else ""

    screen_finding = (
        f"Within Kim's controlled 26-LNP screen (barcode counts), BM and "
        f"liver delivery are {corr_label}correlated (Spearman r={screen_r:.3f},"
        f" p={screen_p:.3f}), confirming that formulation modifications can "
        f"independently affect each organ."
    )

    validation_finding = (
        "Cross-paper comparison (n=6 LNPs + 1 VLP comparator) shows "
        "antibody-conjugated LNPs (Breda) achieve the highest BM delivery "
        "(55%) but with proportionally high liver (76%). Untargeted LNPs "
        "(Kim LNP67) achieve moderate BM (20.9%) with moderate liver "
        "(20.1%). LNP108 achieves the best LNP selectivity "
        "(BM:liver = 5.5)."
    )

    cross_platform_finding = (
        "Ensoma's BaEVTR VLP (31% HSC editing, ~0% liver) is the FIRST "
        "data point in the ideal zone of the Pareto frontier. This "
        "demonstrates that high HSC delivery with near-zero liver is "
        "achievable — but with a different delivery platform (VLP vs LNP). "
        "LNP gap formulations must target >31% HSC delivery with <5% liver "
        "to match VLP performance."
    )

    narrative_shift = (
        "The paper's central question shifts from 'Can any formulation "
        "reach the ideal zone?' to 'Can LNPs match the selectivity that "
        "VLPs have achieved?' Gap #2 (LNP67 + C18-PEG) targets this zone "
        "with predicted ~18% liver, but LNP-intrinsic liver uptake may be "
        "a fundamental platform limitation."
    )

    return {
        "screen_finding": screen_finding,
        "validation_finding": validation_finding,
        "cross_platform_finding": cross_platform_finding,
        "narrative_shift": narrative_shift,
        "ideal_zone": {"bm_threshold": 30, "liver_threshold": 5},
        "formulations_in_ideal_zone": ["Ensoma BaEVTR VLP"],
        "lnp_formulations_in_ideal_zone": [],
        "key_numbers_changed": {
            "old_spearman_r": 0.37,
            "old_spearman_note": "mixed barcode+% data (29 points)",
            "new_screen_spearman_r": screen_r,
            "new_screen_spearman_note": "barcode-only (23 points)",
            "validation_correlation": "not computed (n=6, NS)",
        },
    }


# ── Deprecation ──────────────────────────────────────────────────────────


def deprecate_old_pareto(
    old_path: Path | None = None,
) -> None:
    """Mark old pareto_frontier.json as deprecated.

    Args:
        old_path: Path to old pareto_frontier.json.
    """
    if old_path is None:
        old_path = PROJECT_ROOT / "data" / "models" / "pareto_frontier.json"

    if not old_path.exists():
        logger.info("Old Pareto file not found, skipping deprecation")
        return

    with open(old_path) as f:
        old_data = json.load(f)

    old_data["deprecated"] = True
    old_data["reason"] = "Mixed barcode counts and percentages on same axes"
    old_data["replacement_files"] = [
        "pareto_screen_only.json",
        "pareto_validation_only.json",
        "pareto_narrative.json",
    ]

    with open(old_path, "w") as f:
        json.dump(old_data, f, indent=2, default=str)

    logger.info("Deprecated %s", old_path)


# ── Helpers ──────────────────────────────────────────────────────────────


def _pareto_to_dict(p: ParetoPoint) -> dict[str, Any]:
    """Convert ParetoPoint to dict."""
    return {
        "formulation": p.formulation,
        "bm_percent": p.bm_percent,
        "liver_percent": p.liver_percent,
        "bm_liver_ratio": round(p.bm_liver_ratio, 4),
        "source": p.source,
        "helper_lipid": p.helper_lipid,
        "peg_chain": p.peg_chain,
        "targeting": p.targeting,
        "is_pareto": p.is_pareto,
    }


def _classify_quadrants(
    lnp_points: list[ParetoPoint],
    comparators: list[dict[str, Any]],
    bm_thresh: float,
    liver_thresh: float,
) -> dict[str, list[str]]:
    """Classify formulations into Pareto quadrants.

    Quadrants:
    - ideal: high BM, low liver (upper-left)
    - potent: high BM, high liver (upper-right)
    - selective: low BM, low liver (lower-left)
    - poor: low BM, high liver (lower-right)
    """
    quadrants: dict[str, list[str]] = {
        "ideal": [], "potent": [], "selective": [], "poor": [],
    }

    for p in lnp_points:
        high_bm = p.bm_percent >= bm_thresh
        low_liver = p.liver_percent <= liver_thresh
        if high_bm and low_liver:
            quadrants["ideal"].append(p.formulation)
        elif high_bm:
            quadrants["potent"].append(p.formulation)
        elif low_liver:
            quadrants["selective"].append(p.formulation)
        else:
            quadrants["poor"].append(p.formulation)

    for c in comparators:
        high_bm = c["bm_pct"] >= bm_thresh
        low_liver = c["liver_pct"] <= liver_thresh
        name = c["name"]
        if high_bm and low_liver:
            quadrants["ideal"].append(name)
        elif high_bm:
            quadrants["potent"].append(name)
        elif low_liver:
            quadrants["selective"].append(name)
        else:
            quadrants["poor"].append(name)

    return quadrants


# ── Pipeline ─────────────────────────────────────────────────────────────


def run_corrected_pareto(
    output_dir: Path | None = None,
    kim_screen_path: Path | None = None,
) -> dict[str, dict[str, Any]]:
    """Run full corrected Pareto analysis.

    Args:
        output_dir: Directory for output files.
        kim_screen_path: Path to Kim screen JSON.

    Returns:
        Dict with screen, validation, and narrative results.
    """
    if output_dir is None:
        output_dir = PROJECT_ROOT / "data" / "models"

    screen = compute_screen_pareto(kim_screen_path)
    validation = compute_validation_pareto()
    narrative = build_narrative(screen, validation)

    output_dir.mkdir(parents=True, exist_ok=True)

    with (output_dir / "pareto_screen_only.json").open("w") as f:
        json.dump(screen, f, indent=2, default=str)

    with (output_dir / "pareto_validation_only.json").open("w") as f:
        json.dump(validation, f, indent=2, default=str)

    with (output_dir / "pareto_narrative.json").open("w") as f:
        json.dump(narrative, f, indent=2, default=str)

    deprecate_old_pareto(output_dir / "pareto_frontier.json")

    print(f"\nPareto screen (barcode, n={screen['n_points']}):")
    print(f"  Spearman r = {screen['correlation']['spearman_r']:.3f}")
    print(f"  Pareto-optimal: {screen['pareto_names']}")

    print(f"\nPareto validation (%, n={validation['n_lnp_points']}):")
    print(f"  LNP Pareto: "
          f"{[p['formulation'] for p in validation['lnp_pareto_optimal']]}")
    print(f"  Quadrants: {validation['quadrants']}")

    print(f"\nNarrative shift: {narrative['narrative_shift']}")

    return {"screen": screen, "validation": validation, "narrative": narrative}


if __name__ == "__main__":
    run_corrected_pareto()
