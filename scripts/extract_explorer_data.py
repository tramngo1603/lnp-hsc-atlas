"""Extract all data arrays for the interactive explorer JSX.

Reads model outputs + annotation JSONs → writes explorer_data.json
with every data constant the explorer needs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

_ROOT = Path(__file__).resolve().parent.parent
_FEAT_PATH = _ROOT / "data" / "features" / "hsc_features.parquet"
_KIM_PATH = _ROOT / "data" / "kim_screen" / "kim_2024_screen_corrected.json"
_LIAN_PATH = _ROOT / "annotations" / "lian_2024.json"
_SHAP_PATH = _ROOT / "data" / "models" / "shap_values.csv"
_LOPOCV_PATH = _ROOT / "data" / "models" / "lopocv_results.json"
_OUT_PATH = _ROOT / "explorer_data.json"


def _pareto_data() -> list[dict]:
    """Extract Pareto data points from hardcoded verified values."""
    return [
        {"name": "Breda CD117", "bm": 55, "liver": 76, "metric": "editing",
         "platform": "tLNP", "species": "Mouse",
         "detail": "Cre editing in LSK, CD117 antibody, 0.25 mg/kg", "n": 3},
        {"name": "Kim LNP67", "bm": 20.9, "liver": 20.1, "metric": "reporter",
         "platform": "LNP", "species": "Mouse",
         "detail": "aVHH protein expression, 0.5 mg/kg", "n": 3},
        {"name": "Kim LNP108", "bm": 8.8, "liver": 1.6, "metric": "reporter",
         "platform": "LNP", "species": "Mouse",
         "detail": "Best selectivity in Kim screen (BM:liver = 5.5)", "n": 3},
        {"name": "Lian AA11 Cas9", "bm": 5.2, "liver": 7.5, "metric": "editing",
         "platform": "LNP", "species": "Mouse",
         "detail": "BCL11A editing, covalent lipid approach, Townes mice", "n": 3},
        {"name": "Lian AA11 ABE", "bm": 2.4, "liver": 3.0, "metric": "editing",
         "platform": "LNP", "species": "Mouse",
         "detail": "Sickle to Makassar base editing, Townes mice", "n": 3},
        {"name": "Ensoma VLP", "bm": 31, "liver": 0.5, "metric": "editing",
         "platform": "VLP", "species": "Hum. mouse",
         "detail": "B2M editing, 8 wk, near-zero liver transduction", "n": 3},
        {"name": "Tessera 24%", "bm": 24, "liver": 8, "metric": "editing",
         "platform": "tLNP", "species": "NHP",
         "detail": "HBB Makassar, single dose, liver estimated", "n": None},
        {"name": "Tessera 40%", "bm": 40, "liver": 13.3, "metric": "editing",
         "platform": "tLNP", "species": "NHP",
         "detail": "Optimized Gene Writer cargo, same LNP platform", "n": None},
        {"name": "Tessera 60%", "bm": 60, "liver": 20, "metric": "editing",
         "platform": "tLNP", "species": "NHP",
         "detail": "Two doses, liver estimated from 3:1 BM:liver ratio", "n": None},
        {"name": "Kim LNP95", "bm": 48, "liver": 18.8, "metric": "reporter",
         "platform": "LNP", "species": "Mouse",
         "detail": "ALC-0159 PEG lipid, highest barcode in screen (30% DOTAP)", "n": 1},
        {"name": "Breda IgG control", "bm": 19, "liver": 78, "metric": "editing",
         "platform": "tLNP", "species": "Mouse",
         "detail": "Isotype control, liver comparable to CD117 LNP", "n": 3},
        {"name": "Kim E2 avg", "bm": 5.2, "liver": 44, "metric": "reporter",
         "platform": "LNP", "species": "Mouse",
         "detail": "4-LNP validation average, 0.5 mg/kg", "n": 4},
    ]


def _shap_data() -> list[dict]:
    """Read SHAP from CSV."""
    df = pd.read_csv(_SHAP_PATH)
    # Map feature names to readable labels
    label_map = {
        "ionizable_mol_pct": "Ionizable lipid %",
        "receptor_cd117": "CD117 targeting",
        "chol_to_helper_ratio": "Chol:helper ratio",
        "cholesterol_mol_pct": "Cholesterol %",
        "dose_mg_per_kg": "Dose (mg/kg)",
        "assay_editing": "Editing assay",
        "il_molecular_weight": "IL molecular weight",
        "hl_dotap": "DOTAP helper",
        "helper_mol_pct": "Helper lipid %",
        "helper_is_cationic": "Cationic helper",
        "il_to_chol_ratio": "IL:chol ratio",
    }
    rows = []
    for _, r in df.head(10).iterrows():
        rows.append({
            "feature": label_map.get(r["feature"], r["feature"]),
            "shap": round(r["mean_abs_shap"], 2),
            "type": r["type"],
        })
    return rows


def _kim_screen_analysis() -> tuple[list[dict], list[dict], list[dict], dict]:
    """Extract PEG comparison, helper×PEG interaction, and headgroup data."""
    with open(_KIM_PATH) as f:
        screen = json.load(f)
    forms = screen["formulations"]
    bm_forms = [f for f in forms if f.get("bm_normalized_bc") is not None]

    helpers = sorted(set(f.get("helper_lipid_name", "?") for f in bm_forms))
    pegs = sorted(set(f.get("peg_lipid_name", "?") for f in bm_forms))

    # Helper × PEG interaction
    interaction = []
    for hl in helpers:
        for peg in pegs:
            subset = [f["bm_normalized_bc"] for f in bm_forms
                      if f.get("helper_lipid_name") == hl and f.get("peg_lipid_name") == peg]
            if subset:
                interaction.append({"helper": hl, "peg": peg, "n": len(subset),
                                    "bm_mean": round(np.mean(subset), 1)})

    # Headgroup data
    headgroup_data = []
    for hl in helpers:
        subset = [f for f in bm_forms if f.get("helper_lipid_name") == hl]
        bm_vals = [f["bm_normalized_bc"] for f in subset]
        liver_vals = [f["liver_ec_normalized_bc"] for f in subset
                      if f.get("liver_ec_normalized_bc") is not None]
        headgroup_data.append({
            "helper": hl, "n": len(subset),
            "bm_mean": round(np.mean(bm_vals), 2),
            "bm_std": round(float(np.std(bm_vals)), 2),
            "bm_median": round(float(np.median(bm_vals)), 2),
            "bm_max": max(bm_vals),
            "liver_mean": round(np.mean(liver_vals), 2) if liver_vals else None,
            "bm_liver_ratio": round(np.mean(bm_vals) / np.mean(liver_vals), 2)
            if liver_vals and np.mean(liver_vals) > 0 else None,
            "bm_values": sorted(bm_vals, reverse=True),
        })

    # PEG comparison (DOTAP only)
    peg_comp = []
    for peg in pegs:
        subset = [f for f in bm_forms
                  if f.get("helper_lipid_name") == "DOTAP" and f.get("peg_lipid_name") == peg]
        if not subset:
            continue
        bm_vals = [f["bm_normalized_bc"] for f in subset]
        peg_comp.append({
            "peg": peg, "helper": "DOTAP", "n": len(subset),
            "bm_mean": round(np.mean(bm_vals), 2),
            "bm_max": max(bm_vals),
            "formulations": [{"id": f["lnp_name"], "bm": f["bm_normalized_bc"],
                              "il_pct": f.get("ionizable_mol_percent"),
                              "helper_pct": f.get("helper_mol_percent")} for f in subset],
        })

    # Mann-Whitney
    dotap_bm = [f["bm_normalized_bc"] for f in bm_forms if f.get("helper_lipid_name") == "DOTAP"]
    ddab_bm = [f["bm_normalized_bc"] for f in bm_forms if f.get("helper_lipid_name") == "DDAB"]
    stat, pval = mannwhitneyu(dotap_bm, ddab_bm, alternative="two-sided")
    stats = {"mann_whitney_U": float(stat), "p_value": round(pval, 4),
             "dotap_mean": round(np.mean(dotap_bm), 2),
             "ddab_mean": round(np.mean(ddab_bm), 2),
             "fold_change": round(np.mean(dotap_bm) / np.mean(ddab_bm), 1)}

    return peg_comp, interaction, headgroup_data, stats


def _lian_data() -> tuple[list[str], list[dict]]:
    """Extract Lian heatmap data."""
    with open(_LIAN_PATH) as f:
        lian = json.load(f)
    cell_types = ["LT_HSC", "LSK", "LMPP", "MPP", "CMP", "GMP", "MEP",
                  "B", "T_total", "T_CD4", "T_CD8", "macrophage", "monocyte", "neutrophil"]
    formulations = lian["formulations_screen"]["formulations"]
    heatmap = []
    for form in formulations:
        fid = form["id"].replace("Lian_", "")
        delivery = form.get("bm_delivery_screen_n1") or form.get("bm_delivery")
        if not delivery:
            continue
        validated = form.get("bm_delivery_validated_n3") is not None
        entry = {"id": fid, "validated": validated,
                 "cell_types": {ct: delivery.get(ct, 0) for ct in cell_types}}
        if validated:
            entry["validated_cell_types"] = {
                ct: form["bm_delivery_validated_n3"].get(ct, 0) for ct in cell_types}
        heatmap.append(entry)
    heatmap.sort(key=lambda x: -x["cell_types"]["LT_HSC"])
    return cell_types, heatmap


def _lopocv_data() -> dict:
    """Load LOPOCV results."""
    if _LOPOCV_PATH.exists():
        with open(_LOPOCV_PATH) as f:
            return json.load(f)
    return {"folds": [], "balanced_accuracy_mean": 0, "n_total": 0}


def _stats() -> dict:
    """Compute header stats."""
    df = pd.read_parquet(_FEAT_PATH)
    return {
        "rows": len(df),
        "labs": int(df["paper"].nunique()),
        "papers": 21,
        "features": 37,
    }


def main() -> int:
    """Extract all explorer data."""
    print("Extracting explorer data...")

    peg_comp, interaction, headgroup, headgroup_stats = _kim_screen_analysis()
    cell_types, lian_formulations = _lian_data()

    data = {
        "paretoData": _pareto_data(),
        "shapData": _shap_data(),
        "pegComparison": peg_comp,
        "helperPegInteraction": interaction,
        "headgroupData": headgroup,
        "headgroupStats": headgroup_stats,
        "doseResponse": [
            {"system": "Shi CD117/C18", "raw_points": [{"dose": 0.3, "response": 75}, {"dose": 1.0, "response": 90}],
             "ec30": 0.036, "ec50": 0.090, "species": "Mouse", "platform": "tLNP"},
            {"system": "Breda CD117", "raw_points": [{"dose": 0.05, "response": 10}, {"dose": 0.25, "response": 55}],
             "ec30": 0.124, "ec50": 0.218, "species": "Mouse", "platform": "tLNP"},
            {"system": "Kim LNP67 (mouse)", "raw_points": [{"dose": 0.5, "response": 12}, {"dose": 1.0, "response": 23}, {"dose": 2.0, "response": 35}],
             "ec30": 1.548, "ec50": 3.77, "species": "Mouse", "platform": "LNP"},
            {"system": "Lian AA11", "raw_points": [{"dose": 0.6, "response": 5.2}],
             "ec30": None, "species": "Mouse", "platform": "LNP",
             "note": "Single dose, Cas9 BCL11A editing"},
        ],
        "lianCellTypes": cell_types,
        "lianFormulations": lian_formulations,
        "lopocvFolds": _lopocv_data(),
        "bmGapData": [
            {"study": "Radmand 2024", "lnps": 196, "measured": False},
            {"study": "Radmand 2023", "lnps": 137, "measured": False},
            {"study": "Kim 2024", "lnps": 128, "measured": True},
            {"study": "Gentry 2025", "lnps": 109, "measured": False},
            {"study": "Sago 2018", "lnps": 160, "measured": True},
            {"study": "Da Silva Sanchez 2022", "lnps": 98, "measured": False},
            {"study": "Shi 2023", "lnps": 37, "measured": True},
            {"study": "Lian 2024", "lnps": 21, "measured": True},
            {"study": "SORT 2020", "lnps": 20, "measured": False},
            {"study": "Breda 2023", "lnps": 14, "measured": True},
            {"study": "Cullis 2025", "lnps": 10, "measured": True},
        ],
        "stats": _stats(),
    }

    with open(_OUT_PATH, "w") as f:
        json.dump(data, f, indent=2, default=str)

    print(f"Saved: {_OUT_PATH}")
    print(f"Stats: {data['stats']}")
    print(f"Pareto points: {len(data['paretoData'])}")
    print(f"SHAP features: {len(data['shapData'])}")
    print(f"Lian formulations: {len(data['lianFormulations'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
