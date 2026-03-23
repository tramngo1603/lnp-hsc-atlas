"""AUDIT 2: Dose-response sensitivity analysis.

Tests how sensitive EC50/EC30 values are to assumed hill slope and top
asymptote. Key question: Is the 44x potency premium robust?

Exploration script — no tests needed.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import curve_fit


def _logistic4(
    x: np.ndarray, top: float, ec50: float, hill: float,
) -> np.ndarray:
    """4-parameter logistic with bottom=0."""
    result: np.ndarray = top / (
        1.0 + (ec50 / np.maximum(x, 1e-10)) ** hill
    )
    return result


def _fit_ec50_fixed(
    doses: list[float],
    responses: list[float],
    top: float,
    hill: float,
) -> float | None:
    """Fit EC50 with fixed top and hill (1 free parameter)."""
    x = np.array(doses)
    y = np.array(responses)

    def model(xx: np.ndarray, ec50: float) -> np.ndarray:
        return _logistic4(xx, top, ec50, hill)

    try:
        popt, _ = curve_fit(model, x, y, p0=[0.5], maxfev=5000)
        return float(popt[0])
    except (RuntimeError, ValueError):
        return None


def _compute_ec30(top: float, ec50: float, hill: float) -> float:
    """Inverse 4PL to find dose giving 30% response."""
    if top <= 30:
        return float("inf")
    ratio = top / 30 - 1
    if ratio <= 0:
        return float("inf")
    return ec50 / (ratio ** (1 / hill))


def _sensitivity_2pt(
    name: str,
    doses: list[float],
    responses: list[float],
) -> list[dict[str, float | None]]:
    """Run sensitivity for 2-point formulations (Shi, Breda)."""
    hills = [0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0]
    tops = [70, 80, 90, 100]

    print(f"\n--- {name} (doses={doses}, resp={responses}) ---")
    hdr = f"{'Hill':>6s} {'Top':>5s} {'EC50':>8s} {'EC30':>8s}"
    print(hdr)
    print("-" * len(hdr))

    results = []
    for top in tops:
        for hill in hills:
            ec50 = _fit_ec50_fixed(doses, responses, top, hill)
            if ec50 is not None and ec50 > 0:
                ec30 = _compute_ec30(top, ec50, hill)
                if ec30 < 1000:
                    print(
                        f"{hill:6.1f} {top:5.0f} "
                        f"{ec50:8.4f} {ec30:8.4f}"
                    )
                    results.append({
                        "hill": hill, "top": float(top),
                        "ec50": ec50, "ec30": ec30,
                    })
    return results


def _sensitivity_3pt(
    name: str,
    doses: list[float],
    responses: list[float],
) -> list[dict[str, float | None]]:
    """Run sensitivity for 3+ point formulations (Kim)."""
    tops = [60, 70, 80, 90, 100]

    print(f"\n--- {name} (doses={doses}, resp={responses}) ---")
    hdr = f"{'Top':>5s} {'EC50':>8s} {'Hill':>6s} {'EC30':>8s}"
    print(hdr)
    print("-" * len(hdr))

    results = []
    x = np.array(doses)
    y = np.array(responses)

    for top in tops:
        def model(
            xx: np.ndarray, ec50: float, hill: float,
            _top: float = top,
        ) -> np.ndarray:
            return _logistic4(xx, _top, ec50, hill)

        try:
            popt, _ = curve_fit(
                model, x, y, p0=[3.0, 1.0], maxfev=5000,
            )
            ec50, hill = float(popt[0]), float(popt[1])
            ec30 = _compute_ec30(top, ec50, hill)
            if ec50 > 0 and ec30 < 1000:
                print(
                    f"{top:5.0f} {ec50:8.4f} {hill:6.3f} "
                    f"{ec30:8.4f}"
                )
                results.append({
                    "top": float(top), "ec50": ec50,
                    "hill": hill, "ec30": ec30,
                })
        except (RuntimeError, ValueError):
            print(f"{top:5.0f}  FAILED TO FIT")

    return results


def _summarize_range(
    name: str,
    results: list[dict[str, float | None]],
) -> dict[str, float]:
    """Summarize EC50 and EC30 ranges."""
    ec50s = [r["ec50"] for r in results if r.get("ec50")]
    ec30s = [r["ec30"] for r in results if r.get("ec30")]

    ec50_min = min(ec50s) if ec50s else 0
    ec50_max = max(ec50s) if ec50s else 0
    ec30_min = min(ec30s) if ec30s else 0
    ec30_max = max(ec30s) if ec30s else 0

    fold_50 = ec50_max / max(ec50_min, 1e-10)
    fold_30 = ec30_max / max(ec30_min, 1e-10)

    print(f"\n  {name} RANGE:")
    print(
        f"    EC50: [{ec50_min:.4f}, {ec50_max:.4f}] "
        f"({fold_50:.1f}-fold range)"
    )
    print(
        f"    EC30: [{ec30_min:.4f}, {ec30_max:.4f}] "
        f"({fold_30:.1f}-fold range)"
    )

    return {
        "ec50_min": ec50_min, "ec50_max": ec50_max,
        "ec30_min": ec30_min, "ec30_max": ec30_max,
    }


def main() -> None:
    """Run dose-response sensitivity analysis."""
    print("=" * 70)
    print("AUDIT 2: DOSE-RESPONSE SENSITIVITY ANALYSIS")
    print("=" * 70)

    shi_r = _sensitivity_2pt(
        "Shi CD117/F7", [0.3, 1.0], [75, 90],
    )
    breda_r = _sensitivity_2pt(
        "Breda CD117", [0.05, 0.25], [10, 55],
    )
    kim_r = _sensitivity_3pt(
        "Kim LNP67 mouse", [0.5, 1.0, 2.0], [12, 23, 35],
    )

    print("\n" + "=" * 70)
    print("EC50/EC30 RANGES ACROSS ALL ASSUMPTIONS")
    print("=" * 70)

    shi_s = _summarize_range("Shi", shi_r)
    breda_s = _summarize_range("Breda", breda_r)
    kim_s = _summarize_range("Kim", kim_r)

    # Potency premium robustness
    print("\n" + "=" * 70)
    print("POTENCY PREMIUM ROBUSTNESS")
    print("=" * 70)

    if shi_s["ec30_min"] > 0 and kim_s["ec30_max"] > 0:
        best_case = kim_s["ec30_max"] / shi_s["ec30_min"]
        worst_case = kim_s["ec30_min"] / shi_s["ec30_max"]
        print("  Shi vs Kim premium (EC30 ratio):")
        print(f"    Best case:  {best_case:.0f}x")
        print(f"    Worst case: {worst_case:.0f}x")
        if worst_case > 5:
            print("    VERDICT: Premium is ROBUST (>5x under all assumptions)")
        elif worst_case > 2:
            print("    VERDICT: Premium is MODERATE (2-5x under some assumptions)")
        else:
            print("    VERDICT: Premium is FRAGILE (<2x under some assumptions)")

    if breda_s["ec30_min"] > 0 and kim_s["ec30_max"] > 0:
        best_case = kim_s["ec30_max"] / breda_s["ec30_min"]
        worst_case = kim_s["ec30_min"] / breda_s["ec30_max"]
        print("\n  Breda vs Kim premium (EC30 ratio):")
        print(f"    Best case:  {best_case:.0f}x")
        print(f"    Worst case: {worst_case:.0f}x")

    # Is Shi always more potent than Kim?
    shi_worst_ec30 = shi_s["ec30_max"]
    kim_best_ec30 = kim_s["ec30_min"]
    always_more = shi_worst_ec30 < kim_best_ec30
    print("\n  Is Shi ALWAYS more potent than Kim?")
    print(
        f"    Shi worst EC30: {shi_worst_ec30:.4f}, "
        f"Kim best EC30: {kim_best_ec30:.4f}"
    )
    print(f"    Answer: {'YES' if always_more else 'NO — could overlap'}")


if __name__ == "__main__":
    main()
