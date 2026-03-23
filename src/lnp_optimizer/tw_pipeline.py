"""Therapeutic window pipeline: data loading, gaps, interventions, reporting.

Orchestration module that loads paired data, runs gap analysis,
models interventions, and produces outputs.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any

from lnp_optimizer.therapeutic_window import (
    DOSE_RESPONSE_DATA,
    DoseResponseFit,
    GapFormulation,
    InterventionEffect,
    ParetoPoint,
    TherapeuticWindow,
    compute_correlation,
    compute_pareto_frontier,
    compute_therapeutic_window,
    fit_dose_response,
)

logger = logging.getLogger(__name__)


# ── Paired data loading ──────────────────────────────────────────────────


def load_paired_data(
    kim_screen_path: Path | None = None,
) -> list[ParetoPoint]:
    """Load all paired BM + liver delivery data from annotations.

    Args:
        kim_screen_path: Path to kim_2024_screen_corrected.json.

    Returns:
        List of ParetoPoints with BM and liver delivery.
    """
    points: list[ParetoPoint] = []
    points.extend(_kim_validation_points())
    points.extend(_breda_points())
    if kim_screen_path and kim_screen_path.exists():
        points.extend(_kim_screen_points(kim_screen_path))
    return points


def _kim_validation_points() -> list[ParetoPoint]:
    """Kim E2 validation data (0.5 mg/kg, in vivo)."""
    return [
        ParetoPoint("LNP67", 20.9, 20.1, 20.9 / 20.1, "kim_E2",
                     "DOTAP", "C14", "intrinsic_tropism"),
        ParetoPoint("LNP95", 4.4, 14.7, 4.4 / 14.7, "kim_E2",
                     "DOTAP", "C14", "intrinsic_tropism"),
        ParetoPoint("LNP108", 8.8, 1.6, 8.8 / 1.6, "kim_E2",
                     "18:1 EPC", "C18", "intrinsic_tropism"),
        ParetoPoint("LP01", 5.0, 42.4, 5.0 / 42.4, "kim_E2",
                     "DSPC", "C14", "none"),
    ]


def _breda_points() -> list[ParetoPoint]:
    """Breda E6 in vivo data."""
    return [
        ParetoPoint("CD117/LNP", 55.0, 76.0, 55.0 / 76.0, "breda_E6",
                     "DSPC", "C14", "antibody_conjugated"),
        ParetoPoint("IgG/LNP", 19.0, 78.0, 19.0 / 78.0, "breda_E6",
                     "DSPC", "C14", "antibody_conjugated"),
    ]


def _kim_screen_points(kim_path: Path) -> list[ParetoPoint]:
    """Kim screen barcode paired data."""
    with open(kim_path) as f:
        data = json.load(f)

    points: list[ParetoPoint] = []
    e2_names = {"LNP67", "LNP95", "LNP108", "LP01"}

    for fm in data["formulations"]:
        bm = fm.get("bm_normalized_bc")
        liver = fm.get("liver_ec_normalized_bc")
        if bm is None or liver is None or liver == 0:
            continue
        name = fm["lnp_name"]
        if name in e2_names:
            continue
        points.append(ParetoPoint(
            formulation=name,
            bm_percent=float(bm), liver_percent=float(liver),
            bm_liver_ratio=float(bm) / float(liver),
            source="kim_screen",
            helper_lipid=fm.get("helper_lipid_name"),
            peg_chain=fm.get("peg_chain"),
            targeting="intrinsic_tropism",
        ))
    return points


# ── Gap analysis ─────────────────────────────────────────────────────────


def identify_gaps() -> list[GapFormulation]:
    """Identify untested formulation combinations."""
    return [
        GapFormulation(
            name="CD117/2B8 + DOTAP 15% + C18-PEG",
            rationale=(
                "Combines Shi's targeting (EC50=0.09) with Kim's DOTAP "
                "BM-tropism and C18-PEG optimization. Untested combination."
            ),
            components={
                "ionizable_lipid": "ALC-0315 (35 mol%)",
                "helper_lipid": "DOTAP (15 mol%)",
                "cholesterol": "47.5 mol%",
                "peg_lipid": "DSG-PEG2000 / C18 (2.5 mol%)",
                "targeting": "anti-CD117 clone 2B8",
            },
            predicted_hsc_percent=70.0, predicted_liver_percent=40.0,
            predicted_hsc_liver_ratio=1.75, confidence="low",
            test_experiment=(
                "Mouse IV 0.1 mg/kg Cre mRNA, LSK tdTomato+ and "
                "liver EC tdTomato+ at 48h. n=5."
            ),
            source_papers=["Shi 2023", "Kim 2024", "Breda 2023"],
        ),
        GapFormulation(
            name="LNP67 + C18-PEG swap",
            rationale=(
                "Kim's LNP67 uses C14PEG. Shi showed C18 > C14 for BM "
                "delivery (3x). Would C18-PEG improve untargeted BM too?"
            ),
            components={
                "ionizable_lipid": "PPZ-A10 (35 mol%)",
                "helper_lipid": "DOTAP (15 mol%)",
                "cholesterol": "47.5 mol%",
                "peg_lipid": "DSG-PEG2000 / C18 (2.5 mol%)",
            },
            predicted_hsc_percent=35.0, predicted_liver_percent=15.0,
            predicted_hsc_liver_ratio=2.33, confidence="medium",
            test_experiment=(
                "Mouse IV 0.5 mg/kg DiR-LNP, BM LSK vs liver EC at "
                "24h. Head-to-head with LNP67 (C14)."
            ),
            source_papers=["Kim 2024", "Shi 2023"],
        ),
        GapFormulation(
            name="Breda formulation + C16GalCer de-targeting",
            rationale=(
                "Breda's 76% liver is ApoE-mediated. Replace DSPC with "
                "C16GalCer at 10 mol% (Gentry 2025). Conservative "
                "substitution to reduce liver, preserve CD117 targeting."
            ),
            components={
                "ionizable_lipid": "ALC-0315 (50 mol%)",
                "helper_lipid": "C16GalCer (10 mol%)",
                "cholesterol": "38 mol%",
                "peg_lipid": "DMG-PEG2000 / C14 (1.5 mol%)",
                "targeting": "anti-CD117 clone 2B8 (post-insertion)",
            },
            predicted_hsc_percent=50.0, predicted_liver_percent=50.0,
            predicted_hsc_liver_ratio=1.0, confidence="low",
            test_experiment=(
                "Mouse IV 0.25 mg/kg Cre mRNA, LSK and liver tdTomato+ "
                "at 48h. Compare to standard Breda (DSPC)."
            ),
            source_papers=["Breda 2023", "Gentry 2025"],
        ),
        GapFormulation(
            name="Any approach + dexamethasone pre-treatment",
            rationale=(
                "Loughrey 2025: dex suppresses Kupffer TLR1/TLR6. Less "
                "first-pass scavenging means more LNP reaches BM. "
                "No new chemistry — immediately testable."
            ),
            components={
                "pre_treatment": "Dex 1 mg/kg IP, 4h before LNP",
                "lnp": "Any existing HSC-LNP",
            },
            predicted_hsc_percent=None, predicted_liver_percent=None,
            predicted_hsc_liver_ratio=None, confidence="medium",
            test_experiment=(
                "Mouse: dex 1 mg/kg IP at -4h, LNP67 0.5 mg/kg IV. "
                "BM LSK and liver EC vs no-dex control."
            ),
            source_papers=["Loughrey 2025", "Kim 2024"],
        ),
        GapFormulation(
            name="Low-dose CD117 + high-dose untargeted combo",
            rationale=(
                "CD117-LNP at 0.1 mg/kg (below toxicity) + LNP67 at "
                "1.0 mg/kg. Antibody edits a fraction of HSCs; "
                "untargeted covers the rest. Lower total liver exposure."
            ),
            components={
                "component_1": "CD117/LNP 0.1 mg/kg (Breda)",
                "component_2": "LNP67 1.0 mg/kg (Kim)",
                "dosing": "Sequential: CD117 first, LNP67 at +1h",
            },
            predicted_hsc_percent=45.0, predicted_liver_percent=50.0,
            predicted_hsc_liver_ratio=0.9, confidence="low",
            test_experiment=(
                "Mouse IV: CD117/LNP-Cre 0.1 mg/kg, then 1h later "
                "LNP67-Cre 1.0 mg/kg. Measure combined LSK editing."
            ),
            source_papers=["Breda 2023", "Kim 2024"],
        ),
    ]


# ── Intervention modeling ────────────────────────────────────────────────


def model_dex_intervention(
    windows: list[TherapeuticWindow],
    bm_boost_factor: float = 1.4,
) -> list[InterventionEffect]:
    """Model dexamethasone pre-treatment effect.

    Args:
        windows: Existing therapeutic windows.
        bm_boost_factor: Assumed BM bioavailability increase (1.4=40%).

    Returns:
        InterventionEffect for each approach.
    """
    effects: list[InterventionEffect] = []
    for w in windows:
        if w.ec30_mg_kg <= 0:
            continue
        effects.append(InterventionEffect(
            intervention="Dexamethasone 1 mg/kg pre-treatment",
            mechanism="Suppresses Kupffer TLR1/TLR6, reduces scavenging",
            original_ec30=w.ec30_mg_kg,
            adjusted_ec30=round(w.ec30_mg_kg / bm_boost_factor, 4),
            original_liver=w.liver_at_ec30,
            adjusted_liver=w.liver_at_ec30,
            confidence="medium",
            caveats=[
                "Loughrey measured Kupffer delivery, not BM",
                "Dex may increase liver editing too",
                "40% BM boost is conservative estimate",
            ],
        ))
    return effects


def model_glycolipid_intervention(
    windows: list[TherapeuticWindow],
    liver_reduction: float = 0.34,
) -> list[InterventionEffect]:
    """Model glycolipid helper substitution for liver de-targeting.

    Args:
        windows: Existing therapeutic windows.
        liver_reduction: Relative liver reduction (0.34=34%).

    Returns:
        InterventionEffect for each approach with known liver data.
    """
    effects: list[InterventionEffect] = []
    for w in windows:
        if w.liver_at_ec30 is None:
            continue
        effects.append(InterventionEffect(
            intervention="C16GalCer helper (25 mol%)",
            mechanism="Gentry 2025: liver EC 82% to 54% (34% reduction)",
            original_ec30=w.ec30_mg_kg,
            adjusted_ec30=w.ec30_mg_kg,
            original_liver=w.liver_at_ec30,
            adjusted_liver=round(w.liver_at_ec30 * (1 - liver_reduction), 1),
            confidence="low",
            caveats=[
                "Gentry showed spleen tropism, not BM",
                "Glycolipid may alter HSC delivery mechanism",
                "Cytokine activation may limit clinical use",
            ],
        ))
    return effects


# ── Full pipeline ────────────────────────────────────────────────────────


def run_full_analysis(
    kim_screen_path: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Run complete therapeutic window analysis.

    Args:
        kim_screen_path: Path to Kim screen JSON.
        output_dir: Directory for output files.

    Returns:
        Dict with all analysis results.
    """
    fits = _fit_all_dose_responses()
    kim_ec30 = fits["Kim_LNP67_mouse_iv"].ec30 or 1.54
    windows = _compute_all_windows(fits, kim_ec30)

    points = load_paired_data(kim_screen_path)
    points = compute_pareto_frontier(points)
    correlation = compute_correlation(points)

    gaps = identify_gaps()
    dex = model_dex_intervention(windows)
    glyco = model_glycolipid_intervention(windows)

    results: dict[str, Any] = {
        "dose_response_fits": {f.name: asdict(f) for f in fits.values()},
        "therapeutic_windows": {w.name: asdict(w) for w in windows},
        "pareto": {
            "n_points": len(points),
            "n_pareto": sum(1 for p in points if p.is_pareto),
            "correlation": correlation,
            "points": [asdict(p) for p in points],
            "pareto_optimal": [asdict(p) for p in points if p.is_pareto],
        },
        "gap_formulations": [asdict(g) for g in gaps],
        "interventions": {
            "dexamethasone": [asdict(e) for e in dex],
            "glycolipid": [asdict(e) for e in glyco],
        },
    }

    if output_dir:
        _save_results(results, output_dir)

    return results


def _fit_all_dose_responses() -> dict[str, DoseResponseFit]:
    """Fit all hardcoded dose-response data."""
    fits: dict[str, DoseResponseFit] = {}
    for name, data in DOSE_RESPONSE_DATA.items():
        doses = [d[0] for d in data]
        responses = [d[1] for d in data]
        fix_top = 100.0 if len(data) <= 3 else None
        fits[name] = fit_dose_response(
            doses, responses, name=name, fix_top=fix_top,
        )
    return fits


def _compute_all_windows(
    fits: dict[str, DoseResponseFit],
    untargeted_ec30: float,
) -> list[TherapeuticWindow]:
    """Compute therapeutic windows for all three approaches."""
    return [
        compute_therapeutic_window(
            "Breda_CD117", fits.get("Breda_CD117_mouse_iv"),
            76.0, 3.0, untargeted_ec30, True, False, True, "high",
        ),
        compute_therapeutic_window(
            "Shi_CD117_C18", fits.get("Shi_CD117_F7_mouse_iv"),
            None, None, untargeted_ec30, True, False, False, "high",
        ),
        compute_therapeutic_window(
            "Kim_LNP67", fits.get("Kim_LNP67_mouse_iv"),
            25.0, 4.0, untargeted_ec30, False, True, True, "low",
        ),
    ]


def _save_results(results: dict[str, Any], output_dir: Path) -> None:
    """Save analysis results to JSON files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "therapeutic_window.json").open("w") as f:
        json.dump(results, f, indent=2, default=str)
    with (output_dir / "pareto_frontier.json").open("w") as f:
        json.dump(results["pareto"], f, indent=2, default=str)
    logger.info("Saved results to %s", output_dir)
