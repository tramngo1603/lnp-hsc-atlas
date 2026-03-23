"""AUDIT 6: Kim HSC:liver ratio verification.

Verifies the claimed HSC:liver ratio of 1.20 for LNP67.
Traces to raw data and checks arithmetic.

Exploration script — no tests needed.
"""

from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
_KIM_EXP = _ROOT / "annotations" / "kim_2024_experiments.json"
_KIM_SCREEN = _ROOT / "data" / "kim_screen" / "kim_2024_screen_corrected.json"
_PARETO = _ROOT / "data" / "models" / "pareto_frontier.json"
_TW = _ROOT / "data" / "models" / "therapeutic_window.json"


def _verify_e2_ratio() -> None:
    """Verify the E2 validation BM and liver values for all 4 LNPs."""
    print("\n" + "=" * 70)
    print("E2 VALIDATION DATA — BM and liver percentages")
    print("=" * 70)

    with open(_KIM_EXP) as f:
        kim_exp = json.load(f)

    # Find E2 experiment
    e2 = None
    for exp in kim_exp.get("experiments", []):
        if "E2" in exp.get("experiment_id", ""):
            e2 = exp
            break

    if not e2:
        print("  ERROR: E2 experiment not found!")
        return

    bm_vals = e2["primary_outcome"]["values"]
    print("  E2 BM values (% aVHH+ in BM LSK):")
    for k, v in bm_vals.items():
        print(f"    {k}: {v}%")

    # Check if liver values exist in E2
    liver_data = e2.get("secondary_outcome", e2.get("liver_data"))
    if liver_data:
        print("\n  E2 liver values found:")
        for k, v in liver_data.items():
            print(f"    {k}: {v}")
    else:
        print("\n  E2 liver values: NOT in this experiment!")
        print("  Checking other experiments for liver data...")

    # Search all experiments for liver data
    print("\n  Scanning ALL experiments for liver data:")
    for exp in kim_exp.get("experiments", []):
        exp_id = exp.get("experiment_id", "?")
        # Check various places liver data might be
        for key in [
            "secondary_outcome", "liver_data", "biodistribution",
        ]:
            if exp.get(key):
                print(f"    {exp_id}.{key}: {exp[key]}")


def _verify_pareto_values() -> None:
    """Check Pareto data for LNP67 BM and liver values."""
    print("\n" + "=" * 70)
    print("PARETO DATA — LNP67 BM and Liver values")
    print("=" * 70)

    with open(_PARETO) as f:
        pareto = json.load(f)

    lnp67_pts = [
        p for p in pareto["points"]
        if p["formulation"] == "LNP67"
    ]

    for pt in lnp67_pts:
        bm = pt["bm_percent"]
        liver = pt["liver_percent"]
        ratio = bm / liver if liver != 0 else float("inf")
        claimed_ratio = pt.get("bm_liver_ratio", "N/A")
        print(f"  Source: {pt['source']}")
        print(f"  BM: {bm}%")
        print(f"  Liver: {liver}%")
        print(f"  Computed ratio: {ratio:.4f}")
        print(f"  Stored ratio: {claimed_ratio}")
        if isinstance(claimed_ratio, float):
            diff = abs(ratio - claimed_ratio)
            print(
                f"  Ratio match: "
                f"{'PASS' if diff < 0.001 else 'FAIL'} "
                f"(diff={diff:.6f})"
            )
        print()


def _verify_tw_ratio() -> None:
    """Check therapeutic_window.json for the 1.20 claim."""
    print("\n" + "=" * 70)
    print("THERAPEUTIC WINDOW — HSC:liver ratio claim")
    print("=" * 70)

    with open(_TW) as f:
        tw = json.load(f)

    kim_tw = tw["therapeutic_windows"].get("Kim_LNP67", {})
    if not kim_tw:
        print("  Kim_LNP67 not found in therapeutic_windows!")
        return

    ratio = kim_tw.get("hsc_liver_ratio")
    liver = kim_tw.get("liver_at_ec30")
    print(f"  Stored HSC:liver ratio: {ratio}")
    print(f"  Liver at EC30: {liver}")

    # Where does liver=25% come from?
    print("\n  TRACING liver value:")
    print(f"  therapeutic_window.json says liver_at_ec30 = {liver}")

    # Check all Kim experiments for liver data
    with open(_KIM_EXP) as f:
        kim_exp = json.load(f)

    print("\n  Kim experiment liver mentions:")
    for exp in kim_exp.get("experiments", []):
        exp_id = exp.get("experiment_id", "")
        exp_str = json.dumps(exp, indent=None)
        if "liver" in exp_str.lower():
            # Find the specific field
            for key in ["primary_outcome", "secondary_outcome"]:
                outcome = exp.get(key, {})
                outcome_str = json.dumps(outcome, indent=None)
                if "liver" in outcome_str.lower():
                    print(f"    {exp_id}.{key}: {outcome}")


def _verify_screen_ratios() -> None:
    """Check screen BM:liver ratios for all formulations with both."""
    print("\n" + "=" * 70)
    print("KIM SCREEN — All BM:liver ratios")
    print("=" * 70)

    with open(_KIM_SCREEN) as f:
        screen = json.load(f)

    pairs = []
    for fm in screen["formulations"]:
        bm = fm.get("bm_normalized_bc")
        liver = fm.get("liver_ec_normalized_bc")
        stored_ratio = fm.get("bm_liver_ratio")
        if bm is not None and liver is not None:
            computed = bm / liver if liver != 0 else float("inf")
            name = fm.get("lnp_name", "?")
            pairs.append({
                "name": name,
                "bm": bm,
                "liver": liver,
                "computed_ratio": computed,
                "stored_ratio": stored_ratio,
            })

    print(f"  Formulations with both BM and liver: {len(pairs)}")

    # Check for LNP67 specifically
    lnp67 = [p for p in pairs if "67" in p["name"]]
    if lnp67:
        print("\n  LNP67 in screen data:")
        for p in lnp67:
            print(f"    BM (barcode): {p['bm']}")
            print(f"    Liver (barcode): {p['liver']}")
            print(f"    Ratio: {p['computed_ratio']:.4f}")
            print(
                "    NOTE: These are BARCODE COUNTS, "
                "not percentages!"
            )
            print(
                "    The screen ratio is NOT comparable "
                "to E2 ratio."
            )

    # Summary stats on screen ratios
    ratios = [
        p["computed_ratio"] for p in pairs
        if p["computed_ratio"] != float("inf")
    ]
    if ratios:
        import numpy as np
        arr = np.array(ratios)
        print("\n  Screen BM:liver ratio distribution:")
        print(f"    N: {len(arr)}")
        print(f"    Mean: {arr.mean():.2f}")
        print(f"    Median: {float(np.median(arr)):.2f}")
        print(f"    Range: [{arr.min():.2f}, {arr.max():.2f}]")
        print(
            f"    % with ratio > 1.0: "
            f"{(arr > 1.0).sum()}/{len(arr)}"
        )

    # Check arithmetic consistency of stored ratios
    mismatches = 0
    for p in pairs:
        if p["stored_ratio"] is not None:
            diff = abs(
                p["computed_ratio"] - p["stored_ratio"]
            )
            if diff > 0.01:
                mismatches += 1
                print(
                    f"\n  RATIO MISMATCH: {p['name']}: "
                    f"computed={p['computed_ratio']:.4f}, "
                    f"stored={p['stored_ratio']}"
                )
    if mismatches == 0:
        print("\n  All stored ratios match computed: PASS")


def _where_does_1_20_come_from() -> None:
    """Trace the specific 1.20 ratio claim."""
    print("\n" + "=" * 70)
    print("CRITICAL: WHERE DOES HSC:LIVER = 1.20 COME FROM?")
    print("=" * 70)

    with open(_PARETO) as f:
        pareto = json.load(f)

    lnp67_e2 = [
        p for p in pareto["points"]
        if p["formulation"] == "LNP67" and p["source"] == "kim_E2"
    ]
    if lnp67_e2:
        pt = lnp67_e2[0]
        bm = pt["bm_percent"]
        liver = pt["liver_percent"]
        ratio = bm / liver
        print("  From Pareto data:")
        print(f"    LNP67 E2: BM={bm}%, Liver={liver}%")
        print(f"    Ratio = {bm}/{liver} = {ratio:.4f}")
        print()

    with open(_TW) as f:
        tw = json.load(f)

    tw_ratio = tw["therapeutic_windows"]["Kim_LNP67"]["hsc_liver_ratio"]
    tw_liver = tw["therapeutic_windows"]["Kim_LNP67"]["liver_at_ec30"]
    tw_ec30 = tw["therapeutic_windows"]["Kim_LNP67"]["ec30_mg_kg"]

    print("  From therapeutic_window.json:")
    print(f"    hsc_liver_ratio = {tw_ratio}")
    print(f"    liver_at_ec30 = {tw_liver}")
    print(f"    ec30_mg_kg = {tw_ec30}")
    print()

    # The 1.20 claim
    print("  ANALYSIS:")
    if tw_ratio and tw_liver:
        implied_hsc = tw_ratio * tw_liver
        print(f"    If ratio={tw_ratio} and liver={tw_liver}%,")
        print(f"    then implied HSC = {implied_hsc}%")
        print(
            f"    But EC30={tw_ec30} mg/kg gives 30% HSC "
            f"(by definition)"
        )
        print(f"    So ratio at EC30 = 30/{tw_liver} = "
              f"{30/tw_liver:.2f}")
        print()
    if lnp67_e2:
        pt = lnp67_e2[0]
        print(f"    The Pareto ratio {pt['bm_percent']}/{pt['liver_percent']}"
              f" = {pt['bm_percent']/pt['liver_percent']:.4f}")
        print("    This is at 0.5 mg/kg (E2 dose), NOT at EC30")
        print(
            "    Ratio 'HSC:liver = 1.20' should specify: "
            "'at 0.5 mg/kg' or 'at EC30'"
        )


def main() -> None:
    """Run Kim ratio verification audit."""
    print("=" * 70)
    print("AUDIT 6: KIM HSC:LIVER RATIO VERIFICATION")
    print("=" * 70)

    _verify_e2_ratio()
    _verify_pareto_values()
    _verify_tw_ratio()
    _verify_screen_ratios()
    _where_does_1_20_come_from()


if __name__ == "__main__":
    main()
