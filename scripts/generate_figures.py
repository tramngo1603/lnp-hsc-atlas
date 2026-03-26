"""Generate all publication figures from model outputs.

Saves to figures/ directory. Consistent style with INK/RUST/OCHRE accents.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.patches as mpatches  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

_ROOT = Path(__file__).resolve().parent.parent
_OUT = _ROOT / "figures"
_FEAT_PATH = _ROOT / "data" / "features" / "hsc_features.parquet"
_KIM_PATH = _ROOT / "data" / "kim_screen" / "kim_2024_screen_corrected.json"
_LIAN_PATH = _ROOT / "annotations" / "lian_2024.json"
_SHAP_PATH = _ROOT / "data" / "models" / "shap_values.csv"

INK = "#2B4162"
RUST = "#A63D40"
OCHRE = "#B08836"


def fig_shap_summary() -> None:
    """SHAP feature importance bar chart."""
    df = pd.read_csv(_SHAP_PATH)
    known = {"ionizable_mol_pct", "receptor_cd117", "dose_mg_per_kg", "hl_dotap", "helper_mol_pct"}
    il_desc = {c for c in df["feature"] if c.startswith("il_")}

    colors = []
    for _, r in df.iterrows():
        if r["feature"] in known:
            colors.append(INK)
        elif r["feature"] in il_desc:
            colors.append(OCHRE)
        else:
            colors.append("#969696")

    fig, ax = plt.subplots(figsize=(8, 7))
    y = range(len(df) - 1, -1, -1)
    ax.barh(list(y), df["mean_abs_shap"], color=colors)
    ax.set_yticks(list(y))
    ax.set_yticklabels(df["feature"], fontsize=7)
    ax.set_xlabel("Mean |SHAP value|", fontsize=10)
    ax.set_title("Feature Importance (LightGBM, LOPOCV)\n"
                 "Blue = known SAR · Orange = IL descriptor · Gray = other", fontsize=10)
    ax.grid(axis="x", alpha=0.2)
    plt.tight_layout()
    fig.savefig(_OUT / "shap_summary.png", dpi=200, bbox_inches="tight")
    plt.close()
    print("  shap_summary.png")


def fig_bm_blind_spot() -> None:
    """Horizontal bar chart of BM measurement coverage."""
    studies = [
        ("Radmand 2024", 196, False), ("Radmand 2023", 137, False),
        ("Kim 2024", 128, True), ("Gentry 2025", 109, False),
        ("Sago 2018", 160, True), ("Da Silva Sanchez 2022", 98, False),
        ("Shi 2023", 37, True), ("Lian 2024", 21, True),
        ("SORT 2020", 20, False), ("Breda 2023", 14, True),
        ("Cullis 2025", 10, True),
    ]
    studies.sort(key=lambda x: -x[1])
    names = [s[0] for s in studies]
    n_lnps = [s[1] for s in studies]
    measured = [s[2] for s in studies]
    colors = [INK if m else "#eeebe8" for m in measured]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(range(len(names)), n_lnps, color=colors, edgecolor="black", linewidth=0.3)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=9)
    ax.set_xlabel("LNPs screened", fontsize=11)
    ax.set_title("BM in the Organ Panel", fontsize=12)
    ax.invert_yaxis()
    no_bm = sum(n for n, m in zip(n_lnps, measured) if not m)
    ax.text(0.95, 0.05, f"Without BM: {no_bm}", transform=ax.transAxes,
            fontsize=10, ha="right", va="bottom", color=RUST, fontweight="bold")
    plt.tight_layout()
    fig.savefig(_OUT / "bm_blind_spot.png", dpi=200, bbox_inches="tight")
    plt.close()
    print("  bm_blind_spot.png")


def fig_lian_heatmap() -> None:
    """Lian 2024 heatmap: 21 formulations × 14 cell types."""
    with open(_LIAN_PATH) as f:
        lian = json.load(f)
    cell_types = ["LT_HSC", "LSK", "LMPP", "MPP", "CMP", "GMP", "MEP",
                  "B", "T_total", "T_CD4", "T_CD8", "macrophage", "monocyte", "neutrophil"]
    formulations = lian["formulations_screen"]["formulations"]

    names, matrix, val_idx = [], [], []
    for form in formulations:
        fid = form["id"].replace("Lian_", "")
        delivery = form.get("bm_delivery_screen_n1") or form.get("bm_delivery")
        if not delivery:
            continue
        row = [delivery.get(ct, 0) for ct in cell_types]
        names.append(fid)
        matrix.append(row)
        if form.get("bm_delivery_validated_n3"):
            val_idx.append(len(names) - 1)

    mat = np.array(matrix, dtype=float)
    order = np.argsort(-mat[:, 0])
    mat = mat[order]
    names = [names[i] for i in order]

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.imshow(mat, cmap="Blues", aspect="auto", vmin=0, vmax=70)
    ax.set_xticks(range(len(cell_types)))
    ax.set_xticklabels([ct.replace("_", " ") for ct in cell_types], fontsize=8, rotation=45, ha="right")
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=8)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            c = "white" if mat[i, j] > 40 else "black"
            ax.text(j, i, f"{mat[i, j]:.0f}", ha="center", va="center", fontsize=6, color=c)
    ax.set_title("Lian 2024: BM Delivery by Covalent Lipid (tdTom%, n=1 screen)", fontsize=11)
    plt.tight_layout()
    fig.savefig(_OUT / "lian_heatmap.png", dpi=200, bbox_inches="tight")
    plt.close()
    print("  lian_heatmap.png")


def main() -> int:
    """Generate all figures."""
    _OUT.mkdir(exist_ok=True)
    print("Generating figures...")
    fig_shap_summary()
    fig_bm_blind_spot()
    fig_lian_heatmap()
    print(f"✓ Figures saved to {_OUT}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
