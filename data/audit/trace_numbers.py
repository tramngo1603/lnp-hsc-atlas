"""AUDIT 1: Trace every paper number to raw data.

For each quantitative claim in the paper seed, load the source file,
extract the actual value, and compare. Print PASS/FAIL/UNVERIFIABLE.

Exploration script — no tests needed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent.parent
_BREDA = _ROOT / "annotations" / "breda_2023.json"
_SHI = _ROOT / "annotations" / "shi_2023.json"
_KIM_EXP = _ROOT / "annotations" / "kim_2024_experiments.json"
_KIM_SCREEN = _ROOT / "data" / "kim_screen" / "kim_2024_screen_corrected.json"
_TW = _ROOT / "data" / "models" / "therapeutic_window.json"
_PARETO = _ROOT / "data" / "models" / "pareto_frontier.json"


def _load(path: Path) -> Any:
    with open(path) as f:
        return json.load(f)


def _get_nested(data: Any, keys: list[str | int]) -> Any:
    """Navigate nested dict/list by key path."""
    obj = data
    for k in keys:
        if isinstance(obj, list):
            obj = obj[int(k)]
        elif isinstance(obj, dict):
            obj = obj[str(k)]
        else:
            return None
    return obj


def _check(
    label: str,
    claimed: float | int | str,
    actual: Any,
    source: str,
    tol: float = 0.01,
) -> str:
    """Compare claimed vs actual. Return PASS/FAIL/UNVERIFIABLE."""
    if actual is None:
        print(f"  UNVERIFIABLE  {label}")
        print(f"    Claimed: {claimed}, Source: {source}")
        print("    Actual: NOT FOUND")
        return "UNVERIFIABLE"

    if isinstance(claimed, str) or isinstance(actual, str):
        actual_str = str(actual).strip()
        claimed_str = str(claimed).strip()
        match = actual_str == claimed_str
    else:
        match = abs(float(actual) - float(claimed)) <= tol * max(
            abs(float(claimed)), 1e-10,
        )

    status = "PASS" if match else "FAIL"
    marker = "OK" if match else "MISMATCH"
    print(f"  {status:13s}  {label}")
    print(f"    Claimed: {claimed}, Actual: {actual} [{marker}]")
    print(f"    Source: {source}")
    return status


def audit_breda(breda: dict[str, Any]) -> list[str]:
    """Audit Breda data claims."""
    print("\n" + "=" * 70)
    print("BREDA 2023 — Dose-response & biodistribution")
    print("=" * 70)

    results = []
    exps = breda.get("experiments", [])

    # Find experiments by dose
    for exp in exps:
        dose = exp.get("dosing", {}).get("dose_mg_per_kg")
        hsc = exp.get("efficacy", {}).get("hsc_transfection_percent")
        liver = (exp.get("biodistribution") or {}).get("liver_percent")
        fm = exp.get("formulation_name", "")

        if dose == 0.05 and "CD117" in fm:
            results.append(_check(
                "Breda CD117 HSC @ 0.05 mg/kg", 10, hsc,
                f"breda_2023.json: {fm}, dose={dose}",
            ))
        if dose == 0.25 and "CD117" in fm and "IgG" not in fm:
            results.append(_check(
                "Breda CD117 HSC @ 0.25 mg/kg", 55, hsc,
                f"breda_2023.json: {fm}, dose={dose}",
            ))
            results.append(_check(
                "Breda CD117 liver @ 0.25 mg/kg", 76, liver,
                f"breda_2023.json: {fm}, dose={dose}",
            ))

    # IgG control — search for it
    igg_hsc = None
    igg_liver = None
    for exp in exps:
        fm = exp.get("formulation_name", "")
        if "IgG" in fm:
            hsc = exp.get("efficacy", {}).get("hsc_transfection_percent")
            liver = (exp.get("biodistribution") or {}).get("liver_percent")
            if hsc is not None:
                igg_hsc = hsc
            if liver is not None:
                igg_liver = liver

    results.append(_check(
        "Breda IgG HSC editing", 19, igg_hsc,
        "breda_2023.json: IgG/LNP formulation",
    ))
    results.append(_check(
        "Breda IgG liver editing", 78, igg_liver,
        "breda_2023.json: IgG/LNP formulation",
    ))

    return results


def audit_shi(shi: dict[str, Any]) -> list[str]:
    """Audit Shi data claims."""
    print("\n" + "=" * 70)
    print("SHI 2023 — CD117/C18-PEG dose-response")
    print("=" * 70)

    results = []
    exps = shi.get("experiments", [])

    # Find E5 dose-response for F7
    for exp in exps:
        exp_id = exp.get("experiment_id", "")
        if "E5" in exp_id or "dose_response" in exp_id:
            vals = exp.get("primary_outcome", {}).get("values", {})
            # Check for 0.3 mg/kg
            v03 = (
                vals.get("0_3_mg_kg_HSPC")
                or vals.get("0_3_mg_kg_LT_HSC")
                or vals.get("0.3_mg_kg")
            )
            v10 = (
                vals.get("1_0_mg_kg_HSPC")
                or vals.get("1_0_mg_kg_LT_HSC")
                or vals.get("1.0_mg_kg")
            )

            results.append(_check(
                "Shi F7 HSC @ 0.3 mg/kg", "~75%", v03,
                f"shi_2023.json: {exp_id}, F7_ALC0315_C18PEG",
            ))
            results.append(_check(
                "Shi F7 HSC @ 1.0 mg/kg", "~90%", v10,
                f"shi_2023.json: {exp_id}, F7_ALC0315_C18PEG",
            ))
            break

    if not results:
        # Try navigating by structure
        for exp in exps:
            vals = exp.get("primary_outcome", {}).get("values", {})
            if any("mg_kg" in str(k) for k in vals):
                print(f"  Found dose keys in {exp.get('experiment_id')}: "
                      f"{list(vals.keys())}")

    return results


def audit_kim_experiments(kim: dict[str, Any]) -> list[str]:
    """Audit Kim experiment data claims."""
    print("\n" + "=" * 70)
    print("KIM 2024 — Experiments (E2, E3, E6)")
    print("=" * 70)

    results = []
    exps = kim.get("experiments", [])

    for exp in exps:
        exp_id = exp.get("experiment_id", "")
        vals = exp.get("primary_outcome", {}).get("values", {})

        if "E2" in exp_id:
            # E2 validation: BM delivery %
            results.append(_check(
                "Kim E2 LNP67 BM", 20.9, vals.get("F1_LNP67"),
                f"kim_2024_experiments.json: {exp_id}",
            ))
            results.append(_check(
                "Kim E2 LNP95 BM", 4.4, vals.get("F2_LNP95"),
                f"kim_2024_experiments.json: {exp_id}",
            ))
            results.append(_check(
                "Kim E2 LNP108 BM", 8.8, vals.get("F3_LNP108"),
                f"kim_2024_experiments.json: {exp_id}",
            ))
            results.append(_check(
                "Kim E2 LP01 BM", 5.0, vals.get("F4_LP01"),
                f"kim_2024_experiments.json: {exp_id}",
            ))

            # Check for liver data in E2
            liver_vals = exp.get("liver_outcome", {}).get("values", {})
            if not liver_vals:
                liver_vals = exp.get("secondary_outcomes", {})
            print(f"  NOTE: E2 liver data available: {bool(liver_vals)}")
            if liver_vals:
                print(f"    Liver keys: {list(liver_vals.keys())}")

        if "E3" in exp_id or "dose_response" in exp_id.lower():
            results.append(_check(
                "Kim E3 LNP67 @ 0.5 mg/kg", 12,
                vals.get("0_5_mg_kg"),
                f"kim_2024_experiments.json: {exp_id}",
            ))
            results.append(_check(
                "Kim E3 LNP67 @ 1.0 mg/kg", 23,
                vals.get("1_0_mg_kg"),
                f"kim_2024_experiments.json: {exp_id}",
            ))
            results.append(_check(
                "Kim E3 LNP67 @ 2.0 mg/kg", 35,
                vals.get("2_0_mg_kg"),
                f"kim_2024_experiments.json: {exp_id}",
            ))

        if "E6" in exp_id or "human" in exp_id.lower():
            results.append(_check(
                "Kim E6 human @ 0.25 µg/ml", 15,
                vals.get("0_25_ug_ml"),
                f"kim_2024_experiments.json: {exp_id}",
            ))
            results.append(_check(
                "Kim E6 human @ 0.5 µg/ml", 22,
                vals.get("0_5_ug_ml"),
                f"kim_2024_experiments.json: {exp_id}",
            ))
            results.append(_check(
                "Kim E6 human @ 1.0 µg/ml", 25,
                vals.get("1_0_ug_ml"),
                f"kim_2024_experiments.json: {exp_id}",
            ))
            results.append(_check(
                "Kim E6 human @ 2.0 µg/ml", 38,
                vals.get("2_0_ug_ml"),
                f"kim_2024_experiments.json: {exp_id}",
            ))
            results.append(_check(
                "Kim E6 human @ 4.0 µg/ml", 72,
                vals.get("4_0_ug_ml"),
                f"kim_2024_experiments.json: {exp_id}",
            ))

    return results


def audit_kim_screen(screen: dict[str, Any]) -> list[str]:
    """Audit Kim screen headgroup means."""
    print("\n" + "=" * 70)
    print("KIM SCREEN — Headgroup BM means")
    print("=" * 70)

    import numpy as np

    results = []
    by_hl: dict[str, list[float]] = {}
    for fm in screen["formulations"]:
        hl = fm.get("helper_lipid_name")
        bm = fm.get("bm_normalized_bc")
        if hl and bm is not None:
            by_hl.setdefault(hl, []).append(float(bm))

    claims = {
        "DOTAP": 5.2, "DDAB": 0.4, "DOTMA": 0.7, "18:1 EPC": 3.4,
    }
    for hl, claimed in claims.items():
        vals = by_hl.get(hl, [])
        actual = round(float(np.mean(vals)), 1) if vals else None
        results.append(_check(
            f"{hl} BM mean (n={len(vals)})", claimed, actual,
            "kim_2024_screen_corrected.json: mean of bm_normalized_bc",
            tol=0.15,
        ))

    return results


def audit_kim_e2_liver(kim_exp: dict[str, Any]) -> list[str]:
    """Audit Kim E2 liver values — trace origin."""
    print("\n" + "=" * 70)
    print("KIM E2 — Liver values (CRITICAL)")
    print("=" * 70)

    results = []
    exps = kim_exp.get("experiments", [])

    # Check all experiments for liver data
    liver_found = False
    for exp in exps:
        exp_id = exp.get("experiment_id", "")
        # Check multiple possible locations
        for key in ["liver_outcome", "secondary_outcomes",
                     "biodistribution"]:
            liver_data = exp.get(key)
            if liver_data:
                liver_found = True
                print(f"  Found liver data in {exp_id}.{key}:")
                if isinstance(liver_data, dict):
                    vals = liver_data.get("values", liver_data)
                    for k, v in vals.items():
                        print(f"    {k}: {v}")

    if not liver_found:
        print("  WARNING: No liver data found in kim_2024_experiments.json")
        print("  The claimed liver values (20.1, 14.7, 1.6, 42.4) must")
        print("  come from the main kim_2024.json annotation or the paper")
        print("  itself (Supplementary Fig 7).")

    # Check the main Kim annotation for liver
    kim_main = _ROOT / "annotations" / "kim_2024.json"
    if kim_main.exists():
        main = _load(kim_main)
        main_exps = main.get("experiments", [])
        for exp in main_exps:
            liver = (exp.get("biodistribution") or {}).get("liver_percent")
            if liver is not None:
                fm = exp.get("formulation_name", "?")
                print(f"  Kim main annotation: {fm} liver={liver}%")

    return results


def audit_pareto(pareto: dict[str, Any]) -> list[str]:
    """Audit Pareto frontier claims."""
    print("\n" + "=" * 70)
    print("PARETO FRONTIER — Correlation & counts")
    print("=" * 70)

    results = []
    results.append(_check(
        "Pareto n_points", 29, pareto.get("n_points"),
        "pareto_frontier.json: n_points",
    ))
    results.append(_check(
        "Pareto n_pareto", 4, pareto.get("n_pareto"),
        "pareto_frontier.json: n_pareto",
    ))

    corr = pareto.get("correlation", {})
    results.append(_check(
        "Spearman r", 0.37,
        round(corr.get("spearman_r", 0), 2),
        "pareto_frontier.json: correlation.spearman_r",
        tol=0.005,
    ))
    results.append(_check(
        "Pearson r", 0.79,
        round(corr.get("pearson_r", 0), 2),
        "pareto_frontier.json: correlation.pearson_r",
        tol=0.005,
    ))

    return results


def audit_computed(tw: dict[str, Any]) -> list[str]:
    """Audit computed values (EC50, EC30, ratios)."""
    print("\n" + "=" * 70)
    print("COMPUTED VALUES — EC50, EC30, potency premiums")
    print("=" * 70)

    results = []
    fits = tw.get("dose_response_fits", {})
    windows = tw.get("therapeutic_windows", {})

    ec50_claims = {
        "Shi_CD117_F7_mouse_iv": 0.090,
        "Breda_CD117_mouse_iv": 0.218,
        "Kim_LNP67_mouse_iv": 3.767,
    }
    for key, claimed in ec50_claims.items():
        actual = fits.get(key, {}).get("ec50")
        results.append(_check(
            f"{key} EC50", claimed, actual,
            f"therapeutic_window.json: dose_response_fits.{key}.ec50",
            tol=0.001,
        ))

    ec30_claims = {
        "Shi_CD117_F7_mouse_iv": 0.036,
        "Breda_CD117_mouse_iv": 0.124,
        "Kim_LNP67_mouse_iv": 1.548,
    }
    for key, claimed in ec30_claims.items():
        actual_raw = fits.get(key, {}).get("ec30")
        actual = round(actual_raw, 3) if actual_raw else None
        results.append(_check(
            f"{key} EC30", claimed, actual,
            f"therapeutic_window.json: dose_response_fits.{key}.ec30",
            tol=0.002,
        ))

    # Potency premiums
    shi_ec30 = fits.get("Shi_CD117_F7_mouse_iv", {}).get("ec30", 0)
    kim_ec30 = fits.get("Kim_LNP67_mouse_iv", {}).get("ec30", 1)
    breda_ec30 = fits.get("Breda_CD117_mouse_iv", {}).get("ec30", 1)

    if shi_ec30 and kim_ec30:
        premium_shi = round(kim_ec30 / shi_ec30, 0)
        results.append(_check(
            "Potency premium Shi vs Kim", 44, premium_shi,
            f"Kim_EC30 / Shi_EC30 = {kim_ec30:.4f} / {shi_ec30:.4f}",
            tol=1.0,
        ))

    if breda_ec30 and kim_ec30:
        premium_breda = round(kim_ec30 / breda_ec30, 0)
        results.append(_check(
            "Potency premium Breda vs Kim", 12, premium_breda,
            f"Kim_EC30 / Breda_EC30 = {kim_ec30:.4f} / {breda_ec30:.4f}",
            tol=1.0,
        ))

    # HSC:liver ratios
    breda_w = windows.get("Breda_CD117", {})
    kim_w = windows.get("Kim_LNP67", {})
    results.append(_check(
        "Breda HSC:liver ratio", 0.39,
        breda_w.get("hsc_liver_ratio"),
        "therapeutic_window.json: Breda_CD117.hsc_liver_ratio",
        tol=0.01,
    ))
    results.append(_check(
        "Kim HSC:liver ratio", 1.20,
        kim_w.get("hsc_liver_ratio"),
        "therapeutic_window.json: Kim_LNP67.hsc_liver_ratio",
        tol=0.01,
    ))

    return results


def main() -> None:
    """Run full number trace audit."""
    print("=" * 70)
    print("AUDIT 1: TRACE EVERY PAPER NUMBER TO RAW DATA")
    print("=" * 70)

    breda = _load(_BREDA)
    shi = _load(_SHI)
    kim_exp = _load(_KIM_EXP)
    screen = _load(_KIM_SCREEN)
    tw = _load(_TW)
    pareto = _load(_PARETO)

    all_results: list[str] = []
    all_results.extend(audit_breda(breda))
    all_results.extend(audit_shi(shi))
    all_results.extend(audit_kim_experiments(kim_exp))
    all_results.extend(audit_kim_screen(screen))
    all_results.extend(audit_kim_e2_liver(kim_exp))
    all_results.extend(audit_pareto(pareto))
    all_results.extend(audit_computed(tw))

    # Summary
    n_pass = sum(1 for r in all_results if r == "PASS")
    n_fail = sum(1 for r in all_results if r == "FAIL")
    n_unv = sum(1 for r in all_results if r == "UNVERIFIABLE")

    print("\n" + "=" * 70)
    print("AUDIT 1 SUMMARY")
    print("=" * 70)
    print(f"  PASS: {n_pass}")
    print(f"  FAIL: {n_fail}")
    print(f"  UNVERIFIABLE: {n_unv}")
    print(f"  Total: {len(all_results)}")


if __name__ == "__main__":
    main()
