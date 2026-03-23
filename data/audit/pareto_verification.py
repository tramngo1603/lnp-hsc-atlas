"""AUDIT 3: Pareto data verification.

Critical check: the Pareto plot mixes E2 validation (% of cells)
with screen data (barcode counts). Are these comparable?

Exploration script — no tests needed.
"""

from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
_PARETO = _ROOT / "data" / "models" / "pareto_frontier.json"
_KIM_SCREEN = _ROOT / "data" / "kim_screen" / "kim_2024_screen_corrected.json"
_KIM_EXP = _ROOT / "annotations" / "kim_2024_experiments.json"


def _verify_screen_points() -> None:
    """Verify Kim screen points in Pareto data."""
    print("\n" + "=" * 70)
    print("KIM SCREEN POINTS — BM + Liver barcode counts")
    print("=" * 70)

    with open(_KIM_SCREEN) as f:
        screen = json.load(f)
    with open(_PARETO) as f:
        pareto = json.load(f)

    # Build lookup from screen
    screen_lookup: dict[str, dict[str, float | None]] = {}
    for fm in screen["formulations"]:
        name = fm.get("lnp_name", f"LNP{fm.get('lnp_id', '?')}")
        screen_lookup[name] = {
            "bm": fm.get("bm_normalized_bc"),
            "liver": fm.get("liver_ec_normalized_bc"),
            "helper": fm.get("helper_lipid_name"),
        }

    # Check screen points in Pareto
    screen_pts = [
        p for p in pareto["points"] if p["source"] == "kim_screen"
    ]
    print(f"  Screen points in Pareto: {len(screen_pts)}")

    hdr = (
        f"{'Name':>10s} {'Pareto BM':>10s} {'Screen BM':>10s} "
        f"{'Pareto Liver':>12s} {'Screen Liver':>12s} {'Match':>6s}"
    )
    print(hdr)
    print("-" * len(hdr))

    mismatches = 0
    for pt in screen_pts:
        name = pt["formulation"]
        sc = screen_lookup.get(name, {})
        sc_bm = sc.get("bm")
        sc_liver = sc.get("liver")
        p_bm = pt["bm_percent"]
        p_liver = pt["liver_percent"]

        bm_ok = sc_bm is not None and abs(float(sc_bm) - p_bm) < 0.5
        liver_ok = sc_liver is not None and abs(
            float(sc_liver) - p_liver
        ) < 0.5
        match = "OK" if (bm_ok and liver_ok) else "DIFF"
        if match == "DIFF":
            mismatches += 1

        sc_bm_s = f"{sc_bm:.1f}" if sc_bm is not None else "N/A"
        sc_liver_s = f"{sc_liver:.1f}" if sc_liver is not None else "N/A"
        print(
            f"{name:>10s} {p_bm:10.1f} {sc_bm_s:>10s} "
            f"{p_liver:12.1f} {sc_liver_s:>12s} {match:>6s}"
        )

    print(f"\n  Mismatches: {mismatches}/{len(screen_pts)}")

    # Check for duplicates
    pairs = [(pt["bm_percent"], pt["liver_percent"]) for pt in screen_pts]
    dupes = len(pairs) - len(set(pairs))
    print(f"  Duplicate BM/liver pairs: {dupes}")

    # Value ranges
    bm_vals = [pt["bm_percent"] for pt in screen_pts]
    liver_vals = [pt["liver_percent"] for pt in screen_pts]
    print(f"  BM range: [{min(bm_vals):.1f}, {max(bm_vals):.1f}]")
    print(f"  Liver range: [{min(liver_vals):.1f}, {max(liver_vals):.1f}]")
    print(
        f"  All integers? BM: {all(v == int(v) for v in bm_vals)}, "
        f"Liver: {all(v == int(v) for v in liver_vals)}"
    )


def _verify_e2_points() -> None:
    """Verify E2 validation + Breda points."""
    print("\n" + "=" * 70)
    print("E2 VALIDATION + BREDA POINTS")
    print("=" * 70)

    with open(_PARETO) as f:
        pareto = json.load(f)
    with open(_KIM_EXP) as f:
        kim_exp = json.load(f)

    non_screen = [
        p for p in pareto["points"] if p["source"] != "kim_screen"
    ]

    print(f"  Non-screen points: {len(non_screen)}")
    for pt in non_screen:
        print(
            f"  {pt['formulation']:>15s} ({pt['source']:>10s}): "
            f"BM={pt['bm_percent']:.1f}%, "
            f"Liver={pt['liver_percent']:.1f}%"
        )

    # Check E2 BM values against experiments
    for exp in kim_exp.get("experiments", []):
        if "E2" in exp.get("experiment_id", ""):
            vals = exp.get("primary_outcome", {}).get("values", {})
            print("\n  E2 experiment values from annotation:")
            for k, v in vals.items():
                print(f"    {k}: {v}")


def _unit_comparison() -> None:
    """Critical: Are screen barcode counts comparable to E2 % values?"""
    print("\n" + "=" * 70)
    print("CRITICAL: UNIT COMPARISON (barcode counts vs %)")
    print("=" * 70)

    with open(_PARETO) as f:
        pareto = json.load(f)

    screen_pts = [
        p for p in pareto["points"] if p["source"] == "kim_screen"
    ]
    e2_pts = [
        p for p in pareto["points"] if p["source"] == "kim_E2"
    ]
    breda_pts = [
        p for p in pareto["points"] if p["source"] == "breda_E6"
    ]

    print(f"\n  Screen points (barcode counts): {len(screen_pts)}")
    print(
        f"    BM range: "
        f"[{min(p['bm_percent'] for p in screen_pts):.1f}, "
        f"{max(p['bm_percent'] for p in screen_pts):.1f}]"
    )
    print(
        f"    Liver range: "
        f"[{min(p['liver_percent'] for p in screen_pts):.1f}, "
        f"{max(p['liver_percent'] for p in screen_pts):.1f}]"
    )

    print(f"\n  E2 validation points (% aVHH+): {len(e2_pts)}")
    for p in e2_pts:
        print(f"    {p['formulation']}: BM={p['bm_percent']:.1f}%, "
              f"Liver={p['liver_percent']:.1f}%")

    print(f"\n  Breda points (% LT-HSC editing): {len(breda_pts)}")
    for p in breda_pts:
        print(f"    {p['formulation']}: BM={p['bm_percent']:.1f}%, "
              f"Liver={p['liver_percent']:.1f}%")

    print("\n  UNIT ANALYSIS:")
    print("    Kim screen: 'bm_normalized_bc' = normalized barcode count")
    print("      (higher = more delivery, but NOT percentage)")
    print("    Kim E2: '% aVHH+' = percentage of BM cells expressing")
    print("      payload (functional delivery)")
    print("    Breda: '% LT-HSC editing' = percentage of LT-HSCs with")
    print("      Cre-mediated editing")
    print()
    print("  VERDICT: MIXED UNITS on same scatter plot.")
    print("    Screen barcode counts (0-48) are plotted on same axis as")
    print("    E2 percentages (0-55%). These are NOT directly comparable.")
    print("    Screen values happen to be in similar range, which makes")
    print("    the plot visually coherent but scientifically misleading.")

    # Recompute Pareto with only comparable data
    print("\n" + "=" * 70)
    print("RECOMPUTED PARETO — Separated by data type")
    print("=" * 70)

    print("\n  Option A: E2 + Breda only (all in %, n=6)")
    pct_pts = e2_pts + breda_pts
    for p in pct_pts:
        print(
            f"    {p['formulation']:>15s}: "
            f"BM={p['bm_percent']:5.1f}% "
            f"Liver={p['liver_percent']:5.1f}% "
            f"Pareto={p['is_pareto']}"
        )

    # Recompute Pareto for this subset
    print("\n  Recomputed Pareto for %-only data:")
    _recompute_pareto(pct_pts)

    print(f"\n  Option B: Screen only (all in barcode, n={len(screen_pts)})")
    print("  Recomputed Pareto for barcode-only data:")
    _recompute_pareto(screen_pts)

    print("\n  Option C: Keep mixed but label clearly (current approach)")
    print("    Must add caveat: 'Data types are mixed; visual comparison")
    print("    is approximate. Screen barcode counts and E2/Breda")
    print("    percentages are on different scales.'")


def _recompute_pareto(points: list[dict[str, float]]) -> None:
    """Recompute Pareto frontier for a subset of points."""
    n = len(points)
    is_pareto = [True] * n
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            # j dominates i if j has higher BM AND lower liver
            if (points[j]["bm_percent"] >= points[i]["bm_percent"]
                    and points[j]["liver_percent"] <= points[i]["liver_percent"]
                    and (points[j]["bm_percent"] > points[i]["bm_percent"]
                         or points[j]["liver_percent"] < points[i]["liver_percent"])):
                is_pareto[i] = False
                break

    optimal = [points[i] for i in range(n) if is_pareto[i]]
    print(f"    {len(optimal)}/{n} Pareto-optimal:")
    for p in optimal:
        print(
            f"      {p['formulation']:>15s}: "
            f"BM={p['bm_percent']:5.1f}, "
            f"Liver={p['liver_percent']:5.1f}"
        )

    # Recompute correlation
    if n >= 4:
        from scipy.stats import pearsonr, spearmanr
        bm = [p["bm_percent"] for p in points]
        liver = [p["liver_percent"] for p in points]
        pr, pp = pearsonr(bm, liver)
        sr, sp = spearmanr(bm, liver)
        print(f"    Pearson r={pr:.3f} (p={pp:.4f})")
        print(f"    Spearman r={sr:.3f} (p={sp:.4f})")


def main() -> None:
    """Run Pareto data verification."""
    print("=" * 70)
    print("AUDIT 3: PARETO DATA VERIFICATION")
    print("=" * 70)

    _verify_screen_points()
    _verify_e2_points()
    _unit_comparison()


if __name__ == "__main__":
    main()
