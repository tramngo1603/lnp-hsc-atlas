"""AUDIT 7: Shi liver estimate verification.

The therapeutic_window.json has liver_at_ec30=null for Shi.
The app/paper may claim ~35% liver. Verify whether this is
supported by the raw Shi data and where it comes from.

Exploration script — no tests needed.
"""

from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
_SHI = _ROOT / "annotations" / "shi_2023.json"
_TW = _ROOT / "data" / "models" / "therapeutic_window.json"
_PARETO = _ROOT / "data" / "models" / "pareto_frontier.json"


def _check_shi_biodistribution() -> None:
    """Check all Shi experiments for biodistribution data."""
    print("\n" + "=" * 70)
    print("SHI 2023 — ALL BIODISTRIBUTION DATA")
    print("=" * 70)

    with open(_SHI) as f:
        shi = json.load(f)

    for exp in shi.get("experiments", []):
        exp_id = exp.get("experiment_id", "?")
        biodist = exp.get("biodistribution")
        if biodist:
            print(f"\n  {exp_id}:")
            liver = biodist.get("liver_percent")
            bm = biodist.get("bone_marrow_percent")
            spleen = biodist.get("spleen_percent")
            lung = biodist.get("lung_percent")
            method = biodist.get("measurement_method")
            note = biodist.get("_note", "")
            paired = biodist.get("paired_hsc_and_liver_data")
            print(f"    Liver: {liver}")
            print(f"    BM: {bm}")
            print(f"    Spleen: {spleen}")
            print(f"    Lung: {lung}")
            print(f"    Method: {method}")
            print(f"    Paired: {paired}")
            if note:
                print(f"    Note: {note}")

    # Search for ANY liver mention in the annotation
    shi_str = json.dumps(shi)
    liver_mentions = []
    for key in ["liver", "Liver", "hepat"]:
        idx = 0
        while True:
            idx = shi_str.find(key, idx)
            if idx == -1:
                break
            context = shi_str[max(0, idx - 50) : idx + 100]
            liver_mentions.append(context)
            idx += 1

    print(f"\n  Total 'liver' mentions in annotation: {len(liver_mentions)}")
    for i, ctx in enumerate(liver_mentions[:10]):
        print(f"    [{i}] ...{ctx}...")


def _check_shi_fig3() -> None:
    """Check Fig 3 biodistribution experiment specifically."""
    print("\n" + "=" * 70)
    print("SHI FIG 3 — BIODISTRIBUTION EXPERIMENT")
    print("=" * 70)

    with open(_SHI) as f:
        shi = json.load(f)

    for exp in shi.get("experiments", []):
        exp_id = exp.get("experiment_id", "")
        fig_ref = exp.get("figure_reference", "")
        exp_type = exp.get("experiment_type", "")

        if "biodist" in exp_type.lower() or "Fig 3" in fig_ref:
            print(f"\n  Experiment: {exp_id}")
            print(f"  Figure: {fig_ref}")
            print(f"  Type: {exp_type}")

            dosing = exp.get("dosing", {})
            print(f"  Dose: {dosing.get('dose_mg_per_kg')} mg/kg")

            primary = exp.get("primary_outcome", {})
            print(f"  Primary metric: {primary.get('metric')}")
            print(f"  Values: {primary.get('values')}")
            print(f"  Unit: {primary.get('unit')}")

            secondary = exp.get("secondary_outcomes", [])
            for s in secondary:
                print(f"  Secondary: {s}")


def _check_tw_liver() -> None:
    """Check what therapeutic_window.json says about Shi liver."""
    print("\n" + "=" * 70)
    print("THERAPEUTIC WINDOW — SHI LIVER ENTRY")
    print("=" * 70)

    with open(_TW) as f:
        tw = json.load(f)

    shi_tw = tw["therapeutic_windows"].get("Shi_CD117_C18", {})
    print("  Shi_CD117_C18 entry:")
    for k, v in shi_tw.items():
        if k != "dose_response":
            print(f"    {k}: {v}")

    print(f"\n  liver_at_ec30 = {shi_tw.get('liver_at_ec30')}")
    print(f"  hsc_liver_ratio = {shi_tw.get('hsc_liver_ratio')}")
    print(f"  therapeutic_index = {shi_tw.get('therapeutic_index')}")


def _check_pareto_for_shi() -> None:
    """Check if Shi appears in Pareto data."""
    print("\n" + "=" * 70)
    print("PARETO DATA — ANY SHI ENTRIES?")
    print("=" * 70)

    with open(_PARETO) as f:
        pareto = json.load(f)

    shi_pts = [
        p for p in pareto["points"]
        if "shi" in p.get("source", "").lower()
        or "shi" in p.get("formulation", "").lower()
    ]

    if shi_pts:
        print(f"  Shi points in Pareto: {len(shi_pts)}")
        for pt in shi_pts:
            print(f"    {pt}")
    else:
        print("  No Shi entries in Pareto data.")
        print(
            "  This means Shi has NO paired BM+liver data "
            "for the scatter plot."
        )


def _assess_liver_estimate() -> None:
    """Assess whether ~35% liver claim is supportable."""
    print("\n" + "=" * 70)
    print("CRITICAL: IS '~35% LIVER' ESTIMATE SUPPORTABLE?")
    print("=" * 70)

    with open(_SHI) as f:
        shi = json.load(f)

    print("  Sources of liver information in Shi 2023:")
    print()

    # E7 biodistribution is IVIS imaging, not flow cytometry
    for exp in shi.get("experiments", []):
        if "biodist" in exp.get("experiment_type", "").lower():
            print(f"  {exp['experiment_id']}:")
            print(f"    Type: {exp['experiment_type']}")
            metric = exp.get("primary_outcome", {}).get("metric", "")
            unit = exp.get("primary_outcome", {}).get("unit", "")
            print(f"    Metric: {metric}")
            print(f"    Unit: {unit}")
            vals = exp.get("primary_outcome", {}).get("values", {})
            print(f"    Values: {vals}")
            print()
            print("    ISSUE: IVIS average radiance is NOT equivalent")
            print("    to % cells transfected (flow cytometry).")
            print("    Cannot derive liver % from this data.")

    # E5 Cre experiment — any liver editing data?
    for exp in shi.get("experiments", []):
        if "E5" in exp.get("experiment_id", ""):
            fig = exp.get("figure_reference", "")
            primary = exp.get("primary_outcome", {})
            print(f"\n  {exp['experiment_id']} ({fig}):")
            print(f"    Metric: {primary.get('metric')}")
            vals = primary.get("values", {})
            for k, v in vals.items():
                print(f"    {k}: {v}")

            # Liver data in secondary outcomes
            secondary = exp.get("secondary_outcomes", [])
            for s in secondary:
                if "liver" in str(s).lower():
                    print(f"    Liver secondary: {s}")

    print("\n  VERDICT:")
    print("  1. Shi E7 biodistribution uses IVIS (radiance), not flow")
    print("     cytometry (% cells). No quantitative liver % available.")
    print("  2. Shi does not report liver editing % in any experiment.")
    print("  3. A '~35%' liver estimate would have to come from:")
    print("     a) Visual interpretation of Fig 3a IVIS images")
    print("     b) Analogy to Breda's 76% liver with similar LNP")
    print("     c) Assumption from isotype control signal in Fig 3b")
    print("  4. NONE of these give a defensible liver percentage.")
    print()
    print("  RECOMMENDATION: Report Shi liver as 'not measured'")
    print("  (which is why therapeutic_window.json correctly has null).")
    print("  Any liver estimate for Shi should be clearly labeled")
    print("  as extrapolation/assumption, not measured data.")


def main() -> None:
    """Run Shi liver check audit."""
    print("=" * 70)
    print("AUDIT 7: SHI LIVER ESTIMATE VERIFICATION")
    print("=" * 70)

    _check_shi_biodistribution()
    _check_shi_fig3()
    _check_tw_liver()
    _check_pareto_for_shi()
    _assess_liver_estimate()


if __name__ == "__main__":
    main()
