"""Therapeutic window console reporting.

Prints dose-response fits, therapeutic windows, Pareto frontier,
gap formulations, and intervention modeling results.
"""

from __future__ import annotations

from typing import Any


def print_report(results: dict[str, Any]) -> None:
    """Print full therapeutic window analysis report."""
    _print_dose_response(results["dose_response_fits"])
    _print_windows(results["therapeutic_windows"])
    _print_pareto(results["pareto"])
    _print_gaps(results["gap_formulations"])
    _print_interventions(results["interventions"])
    _print_summary(results)


def _print_dose_response(fits: dict[str, dict[str, Any]]) -> None:
    """Print dose-response fit results."""
    print("\n" + "=" * 70)
    print("DOSE-RESPONSE FITS (4PL, bottom=0)")
    print("=" * 70)
    hdr = f"{'Name':35s} {'EC50':>8s} {'EC30':>8s} {'Hill':>6s} {'R2':>6s}"
    print(hdr)
    print("-" * len(hdr))
    for f in fits.values():
        ec30_s = f"{f['ec30']:.3f}" if f["ec30"] else "N/A"
        print(
            f"{f['name']:35s} {f['ec50']:8.3f} {ec30_s:>8s} "
            f"{f['hill']:6.2f} {f['r_squared']:6.3f}"
        )


def _print_windows(windows: dict[str, dict[str, Any]]) -> None:
    """Print therapeutic window comparison table."""
    print("\n" + "=" * 70)
    print("THERAPEUTIC WINDOWS")
    print("=" * 70)
    cols = ["EC30", "Liver%", "HSC:Liv", "TI", "Premium", "Ab?", "NHP?"]
    hdr = f"{'Approach':20s}" + "".join(f"{c:>10s}" for c in cols)
    print(hdr)
    print("-" * len(hdr))
    for w in windows.values():
        vals = _format_window_row(w)
        print(f"{w['name']:20s}" + "".join(f"{v:>10s}" for v in vals))


def _format_window_row(w: dict[str, Any]) -> list[str]:
    """Format one row of the therapeutic window table."""
    return [
        f"{w['ec30_mg_kg']:.3f}" if w["ec30_mg_kg"] else "N/A",
        f"{w['liver_at_ec30']:.0f}" if w["liver_at_ec30"] else "N/A",
        f"{w['hsc_liver_ratio']:.2f}" if w["hsc_liver_ratio"] else "N/A",
        f"{w['therapeutic_index']:.1f}" if w["therapeutic_index"] else "N/A",
        f"{w['potency_premium']:.0f}x" if w["potency_premium"] else "ref",
        "Yes" if w["antibody_required"] else "No",
        "Yes" if w["has_nhp"] else "No",
    ]


def _print_pareto(pareto: dict[str, Any]) -> None:
    """Print Pareto frontier results."""
    print("\n" + "=" * 70)
    print("PARETO FRONTIER (BM vs Liver)")
    print("=" * 70)
    corr = pareto["correlation"]
    print(f"Total paired: {pareto['n_points']}")
    print(f"Pareto-optimal: {pareto['n_pareto']}")
    print(
        f"Pearson r={corr['pearson_r']:.3f}, "
        f"Spearman r={corr['spearman_r']:.3f}"
    )
    print("\nPareto-optimal formulations:")
    for p in pareto["pareto_optimal"]:
        hl = p.get("helper_lipid") or "?"
        peg = p.get("peg_chain") or "?"
        print(
            f"  {p['formulation']:15s} BM={p['bm_percent']:5.1f}% "
            f"liver={p['liver_percent']:5.1f}% "
            f"ratio={p['bm_liver_ratio']:5.1f} [{hl}, {peg}]"
        )


def _print_gaps(gaps: list[dict[str, Any]]) -> None:
    """Print gap formulation analysis."""
    print("\n" + "=" * 70)
    print("GAP FORMULATIONS (Untested Combinations)")
    print("=" * 70)
    for i, g in enumerate(gaps, 1):
        hsc = f"{g['predicted_hsc_percent']:.0f}%" if g["predicted_hsc_percent"] else "?"
        liver = f"{g['predicted_liver_percent']:.0f}%" if g["predicted_liver_percent"] else "?"
        ratio = f"{g['predicted_hsc_liver_ratio']:.1f}" if g["predicted_hsc_liver_ratio"] else "?"
        conf = g["confidence"].upper()
        print(f"\n  {i}. {g['name']} [{conf} confidence]")
        print(f"     Predicted: HSC={hsc}, liver={liver}, ratio={ratio}")
        print(f"     Test: {g['test_experiment']}")


def _print_interventions(interventions: dict[str, Any]) -> None:
    """Print intervention modeling results."""
    print("\n" + "=" * 70)
    print("INTERVENTION MODELING")
    print("=" * 70)
    for category, effects in interventions.items():
        print(f"\n  --- {category.upper()} ---")
        for e in effects:
            ec30_s = (
                f"{e['original_ec30']:.3f} -> "
                f"{e['adjusted_ec30']:.3f} mg/kg"
            )
            if e["original_liver"] and e["adjusted_liver"]:
                liver_s = (
                    f"{e['original_liver']:.0f}% -> "
                    f"{e['adjusted_liver']:.0f}%"
                )
            else:
                liver_s = "N/A"
            print(f"  EC30: {ec30_s}")
            print(f"  Liver: {liver_s}")
            print(f"  Confidence: {e['confidence']}")
            for caveat in e.get("caveats", []):
                print(f"    ! {caveat}")


def _print_summary(results: dict[str, Any]) -> None:
    """Print summary insight."""
    windows = results["therapeutic_windows"]
    pareto = results["pareto"]

    print("\n" + "=" * 70)
    print("SUMMARY: THE POTENCY-SELECTIVITY TRADEOFF")
    print("=" * 70)

    # Find best potency and best selectivity
    best_potency = min(
        windows.values(),
        key=lambda w: w["ec30_mg_kg"] if w["ec30_mg_kg"] else 999,
    )
    best_select = max(
        (w for w in windows.values() if w["hsc_liver_ratio"]),
        key=lambda w: w["hsc_liver_ratio"],  # type: ignore[arg-type]
        default=None,
    )

    print(f"\n  Most potent: {best_potency['name']} "
          f"(EC30={best_potency['ec30_mg_kg']:.3f} mg/kg)")
    if best_select:
        print(
            f"  Most selective: {best_select['name']} "
            f"(HSC:liver={best_select['hsc_liver_ratio']:.2f})"
        )

    corr = pareto["correlation"]
    print(f"\n  BM-liver correlation: Pearson={corr['pearson_r']:.3f}, "
          f"Spearman={corr['spearman_r']:.3f}")
    print(f"  Pareto-optimal: {pareto['n_pareto']}/{pareto['n_points']}")
    print("\n  KEY FINDING: No approach achieves both high potency AND")
    print("  high selectivity. The tradeoff is real but breakable.")
    print(f"\n  Gap formulations: {len(results['gap_formulations'])} "
          "untested combinations identified")
