"""Therapeutic window: dose-response fitting and potency-selectivity metrics.

Core module with dataclasses, 4PL dose-response fitting, therapeutic window
computation, and Pareto frontier logic.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
from scipy import stats
from scipy.optimize import curve_fit

logger = logging.getLogger(__name__)


# ── Dataclasses ──────────────────────────────────────────────────────────


@dataclass
class DoseResponseFit:
    """Result of 4-parameter logistic dose-response fit."""

    name: str
    ec50: float
    hill: float
    top: float
    bottom: float
    r_squared: float
    ec30: float | None
    doses: list[float]
    responses: list[float]
    fixed_top: bool = False
    error: str | None = None


@dataclass
class TherapeuticWindow:
    """Therapeutic window metrics for one approach."""

    name: str
    ec30_mg_kg: float
    liver_at_ec30: float | None
    hsc_liver_ratio: float | None
    therapeutic_index: float | None
    potency_premium: float | None
    antibody_required: bool
    has_nhp: bool
    has_human_exvivo: bool
    manufacturing_complexity: str
    dose_response: DoseResponseFit | None = None


@dataclass
class ParetoPoint:
    """A formulation with paired BM + liver delivery data."""

    formulation: str
    bm_percent: float
    liver_percent: float
    bm_liver_ratio: float
    source: str
    helper_lipid: str | None = None
    peg_chain: str | None = None
    targeting: str | None = None
    is_pareto: bool = False


@dataclass
class GapFormulation:
    """An untested formulation combination."""

    name: str
    rationale: str
    components: dict[str, str]
    predicted_hsc_percent: float | None
    predicted_liver_percent: float | None
    predicted_hsc_liver_ratio: float | None
    confidence: str
    test_experiment: str
    source_papers: list[str] = field(default_factory=list)


@dataclass
class InterventionEffect:
    """Modeled effect of an intervention on therapeutic window."""

    intervention: str
    mechanism: str
    original_ec30: float
    adjusted_ec30: float
    original_liver: float | None
    adjusted_liver: float | None
    confidence: str
    caveats: list[str] = field(default_factory=list)


# ── Constants ────────────────────────────────────────────────────────────

DOSE_RESPONSE_DATA: dict[str, list[tuple[float, float]]] = {
    "Kim_LNP67_mouse_iv": [(0.5, 12), (1.0, 23), (2.0, 35)],
    "Kim_LNP67_human_exvivo": [
        (0.25, 15), (0.5, 22), (1.0, 25), (2.0, 38), (4.0, 72),
    ],
    "Breda_CD117_mouse_iv": [(0.05, 10), (0.25, 55)],
    "Shi_CD117_F7_mouse_iv": [(0.3, 75), (1.0, 90)],
}

PATISIRAN_DOSE_MG_KG = 0.3


# ── Dose-response modeling ───────────────────────────────────────────────


def _logistic_4pl(
    x: np.ndarray, top: float, ec50: float, hill: float,
) -> np.ndarray:
    """4-parameter logistic with bottom fixed at 0."""
    return top / (1.0 + (ec50 / x) ** hill)


def fit_dose_response(
    doses: list[float],
    responses: list[float],
    name: str = "",
    fix_bottom: float = 0.0,
    fix_top: float | None = None,
) -> DoseResponseFit:
    """Fit 4-parameter logistic to dose-response data.

    Args:
        doses: Dose values (mg/kg or ug/ml).
        responses: Response values (% efficacy).
        name: Formulation name for labeling.
        fix_bottom: Fixed bottom parameter (default 0).
        fix_top: If set, fixes the top asymptote.

    Returns:
        DoseResponseFit with EC50, hill, R², and EC30.
    """
    x = np.array(doses, dtype=np.float64)
    y = np.array(responses, dtype=np.float64)
    auto_fix = fix_top is not None or len(x) <= 3
    top_val = fix_top if fix_top is not None else 100.0

    try:
        if auto_fix:
            top_val, ec50, hill, y_pred = _fit_fixed_top(x, y, top_val)
        else:
            top_val, ec50, hill, y_pred = _fit_free_top(x, y)
    except RuntimeError:
        return DoseResponseFit(
            name=name, ec50=0, hill=0, top=0, bottom=fix_bottom,
            r_squared=0, ec30=None, doses=doses, responses=responses,
            error="curve_fit failed",
        )

    r_sq = _r_squared(y, y_pred)
    ec30 = _compute_ecx(top_val, ec50, hill, target=30.0)

    return DoseResponseFit(
        name=name, ec50=round(ec50, 4), hill=round(hill, 3),
        top=round(top_val, 1), bottom=fix_bottom,
        r_squared=round(r_sq, 4), ec30=round(ec30, 4) if ec30 else None,
        doses=doses, responses=responses, fixed_top=auto_fix,
    )


def _fit_fixed_top(
    x: np.ndarray, y: np.ndarray, top: float,
) -> tuple[float, float, float, np.ndarray]:
    """Fit 4PL with top fixed."""
    def model(x_: np.ndarray, ec50: float, hill: float) -> np.ndarray:
        return _logistic_4pl(x_, top, ec50, hill)

    popt, _ = curve_fit(
        model, x, y, p0=[float(np.median(x)), 1.0],
        bounds=([0.001, 0.1], [100.0, 10.0]), maxfev=10000,
    )
    return top, float(popt[0]), float(popt[1]), model(x, *popt)


def _fit_free_top(
    x: np.ndarray, y: np.ndarray,
) -> tuple[float, float, float, np.ndarray]:
    """Fit 4PL with top as free parameter."""
    popt, _ = curve_fit(
        _logistic_4pl, x, y,
        p0=[float(max(y)) * 1.2, float(np.median(x)), 1.0],
        bounds=([0.0, 0.001, 0.1], [200.0, 100.0, 10.0]), maxfev=10000,
    )
    y_pred = _logistic_4pl(x, *popt)
    return float(popt[0]), float(popt[1]), float(popt[2]), y_pred


def _r_squared(y: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute R² from actual and predicted values."""
    ss_res = float(np.sum((y - y_pred) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0


def _compute_ecx(
    top: float, ec50: float, hill: float, target: float = 30.0,
) -> float | None:
    """Inverse 4PL: dose needed for target% response."""
    if top <= target:
        return None
    result: float = ec50 * ((top / target - 1) ** (-1.0 / hill))
    return result


# ── Therapeutic window ───────────────────────────────────────────────────


def compute_therapeutic_window(
    name: str,
    dose_response: DoseResponseFit | None,
    liver_at_ec30: float | None,
    therapeutic_index: float | None,
    untargeted_ec30: float,
    antibody_required: bool,
    has_nhp: bool,
    has_human_exvivo: bool,
    manufacturing_complexity: str,
) -> TherapeuticWindow:
    """Compute therapeutic window metrics for one approach.

    Args:
        name: Approach name.
        dose_response: Fitted dose-response (or None).
        liver_at_ec30: Liver delivery % at EC30 dose.
        therapeutic_index: Toxic dose / EC30.
        untargeted_ec30: EC30 of untargeted reference.
        antibody_required: Whether antibody conjugation needed.
        has_nhp: NHP data available.
        has_human_exvivo: Human ex vivo data available.
        manufacturing_complexity: "low" | "medium" | "high".

    Returns:
        TherapeuticWindow with all computed metrics.
    """
    ec30 = dose_response.ec30 if dose_response else None
    if ec30 is None:
        ec30 = 0.0

    hsc_liver = 30.0 / liver_at_ec30 if liver_at_ec30 else None
    premium = untargeted_ec30 / ec30 if ec30 > 0 else None

    return TherapeuticWindow(
        name=name, ec30_mg_kg=ec30,
        liver_at_ec30=liver_at_ec30,
        hsc_liver_ratio=round(hsc_liver, 3) if hsc_liver else None,
        therapeutic_index=therapeutic_index,
        potency_premium=round(premium, 1) if premium else None,
        antibody_required=antibody_required, has_nhp=has_nhp,
        has_human_exvivo=has_human_exvivo,
        manufacturing_complexity=manufacturing_complexity,
        dose_response=dose_response,
    )


# ── Pareto frontier ─────────────────────────────────────────────────────


def compute_pareto_frontier(
    points: list[ParetoPoint],
) -> list[ParetoPoint]:
    """Mark Pareto-optimal formulations (maximize BM, minimize liver).

    Args:
        points: Formulations with paired BM and liver data.

    Returns:
        Same list with is_pareto flags set.
    """
    n = len(points)
    for i in range(n):
        dominated = False
        for j in range(n):
            if i == j:
                continue
            if _dominates(points[j], points[i]):
                dominated = True
                break
        points[i].is_pareto = not dominated
    return points


def _dominates(a: ParetoPoint, b: ParetoPoint) -> bool:
    """Check if point a dominates b (higher BM AND lower liver)."""
    return (
        a.bm_percent >= b.bm_percent
        and a.liver_percent <= b.liver_percent
        and (a.bm_percent > b.bm_percent or a.liver_percent < b.liver_percent)
    )


def compute_correlation(
    points: list[ParetoPoint],
) -> dict[str, float]:
    """Pearson and Spearman correlation of BM vs liver.

    Args:
        points: Formulations with paired BM/liver data.

    Returns:
        Dict with pearson_r, pearson_p, spearman_r, spearman_p.
    """
    bm = np.array([p.bm_percent for p in points])
    liver = np.array([p.liver_percent for p in points])
    pr, pp = stats.pearsonr(bm, liver)
    sr, sp = stats.spearmanr(bm, liver)
    return {
        "pearson_r": round(float(pr), 4),
        "pearson_p": round(float(pp), 6),
        "spearman_r": round(float(sr), 4),
        "spearman_p": round(float(sp), 6),
    }
