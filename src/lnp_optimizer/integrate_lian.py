"""Integrate Lian 2024 annotation data into the HSC feature matrix.

Reads lian_2024.json from annotations/, creates feature matrix rows
matching the existing column schema, and appends to hsc_features.parquet.
Also adds `metric_type` and `covalent_lipid_mol_pct` columns to all rows.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parent.parent.parent
_ANNOTATION_PATH = _ROOT / "annotations" / "lian_2024.json"
_FEATURES_PATH = _ROOT / "data" / "features" / "hsc_features.parquet"

# Lian base formulation (adjusted for 20 mol% covalent lipid)
_BASE = {
    "ionizable_mol_pct": 19.0,
    "helper_mol_pct": 19.0,
    "cholesterol_mol_pct": 38.1,
    "peg_mol_pct": 3.8,
}

# Target classification thresholds (from CLAUDE.md)
_THRESHOLDS = {"high": 30, "medium": 10}  # >30% = high, 10-30% = medium, <10% = low

# Assay-to-metric-type mapping for existing data
_ASSAY_METRIC_MAP = {
    "barcode_delivery": "barcode_normalized",
    "editing": "editing_pct",
    "knockdown": "reporter_pct",
    "protein_expression": "reporter_pct",
    "depletion": "editing_pct",
}


def _classify_efficacy(lt_hsc_pct: float) -> str:
    """Classify LT-HSC delivery % into efficacy class."""
    if lt_hsc_pct >= _THRESHOLDS["high"]:
        return "high"
    if lt_hsc_pct >= _THRESHOLDS["medium"]:
        return "medium"
    return "low"


def _make_row(
    formulation: dict,
    lt_hsc_pct: float,
    experiment_id: str,
    confidence: str,
    assay: str = "protein_expression",
    dose: float = 0.6,
    metric_type: str = "reporter_pct",
) -> dict:
    """Create a single feature matrix row from Lian formulation data."""
    label = _classify_efficacy(lt_hsc_pct)
    label_map = {"high": 2, "medium": 1, "low": 0}

    il_pct = _BASE["ionizable_mol_pct"]
    hl_pct = _BASE["helper_mol_pct"]
    chol_pct = _BASE["cholesterol_mol_pct"]
    peg_pct = _BASE["peg_mol_pct"]

    return {
        # Metadata
        "source": "lian_2024",
        "paper": "lian_2024",
        "formulation_id": formulation["id"],
        "experiment_id": experiment_id,
        "assay_category": assay,
        "composition_confidence": confidence,
        "metric_type": metric_type,
        # Mol percentages
        "ionizable_mol_pct": il_pct,
        "helper_mol_pct": hl_pct,
        "cholesterol_mol_pct": chol_pct,
        "peg_mol_pct": peg_pct,
        # Ratios
        "il_to_helper_ratio": il_pct / hl_pct,
        "il_to_chol_ratio": il_pct / chol_pct,
        "chol_to_helper_ratio": chol_pct / hl_pct,
        # PEG
        "peg_chain_numeric": 14.0,  # DMG-PEG2000 = C14
        # Dose
        "dose_mg_per_kg": dose,
        # Targeting
        "targeting_encoded": 0,  # untargeted (corona-mediated)
        "helper_is_cationic": 0,  # DOPE is neutral
        # Species
        "species_mouse": 1,
        "species_nhp": 0,
        "species_human": 0,
        # Assay one-hot
        "assay_barcode_delivery": 0,
        "assay_depletion": 0,
        "assay_editing": 1 if assay == "editing" else 0,
        "assay_knockdown": 0,
        "assay_protein_expression": 1 if assay == "protein_expression" else 0,
        # Helper lipid one-hot
        "hl_dspc": 0,
        "hl_dope": 1,
        "hl_dotap": 0,
        "hl_ddab": 0,
        "hl_dotma": 0,
        "hl_epc": 0,
        # Receptor targeting
        "receptor_cd117": 0,
        "receptor_cd45": 0,
        # Clone
        "clone_2b8": 0,
        "clone_ack2": 0,
        "clone_igg": 0,
        # Molecular descriptors (sparse — NaN for now)
        "il_molecular_weight": np.nan,
        "il_logp": np.nan,
        "il_tpsa": np.nan,
        "il_hbd": np.nan,
        "il_hba": np.nan,
        "il_rotatable_bonds": np.nan,
        "il_num_rings": np.nan,
        "il_heavy_atom_count": np.nan,
        # NEW column: covalent lipid
        "covalent_lipid_mol_pct": 20.0,
        # Target
        "target": label_map[label],
    }


def build_lian_rows() -> pd.DataFrame:
    """Parse Lian 2024 annotation and build feature matrix rows."""
    with open(_ANNOTATION_PATH) as f:
        ann = json.load(f)

    formulations = ann["formulations_screen"]["formulations"]
    rows: list[dict] = []

    for form in formulations:
        fid = form["id"]

        # Screen data (n=1) — all 21 formulations
        delivery = form.get("bm_delivery_screen_n1") or form.get("bm_delivery")
        if delivery and "LT_HSC" in delivery:
            lt_hsc = delivery["LT_HSC"]
            rows.append(_make_row(
                formulation=form,
                lt_hsc_pct=lt_hsc,
                experiment_id=f"{fid}_screen_n1",
                confidence="MEDIUM",
            ))

        # Validated data (n=3) — C6, A8, A13, AA11
        validated = form.get("bm_delivery_validated_n3")
        if validated and "LT_HSC" in validated:
            lt_hsc_v = validated["LT_HSC"]
            rows.append(_make_row(
                formulation=form,
                lt_hsc_pct=lt_hsc_v,
                experiment_id=f"{fid}_validated_n3",
                confidence="HIGH",
            ))

    logger.info("Built %d rows from Lian 2024 (%d screen + %d validated)",
                len(rows),
                sum(1 for r in rows if "screen" in r["experiment_id"]),
                sum(1 for r in rows if "validated" in r["experiment_id"]))

    return pd.DataFrame(rows)


def assign_metric_type(df: pd.DataFrame) -> pd.DataFrame:
    """Add metric_type column to existing feature matrix rows."""
    if "metric_type" in df.columns:
        # Already has it — fill blanks
        mask = df["metric_type"].isna()
    else:
        df["metric_type"] = np.nan
        mask = pd.Series(True, index=df.index)

    for idx in df.index[mask]:
        cat = str(df.at[idx, "assay_category"]).lower()
        if "barcode" in cat:
            df.at[idx, "metric_type"] = "barcode_normalized"
        elif "editing" in cat:
            df.at[idx, "metric_type"] = "editing_pct"
        elif "knockdown" in cat or "protein" in cat or "expression" in cat:
            df.at[idx, "metric_type"] = "reporter_pct"
        elif "depletion" in cat:
            df.at[idx, "metric_type"] = "editing_pct"
        else:
            df.at[idx, "metric_type"] = "unknown"

    return df


def integrate(save: bool = True) -> pd.DataFrame:
    """Integrate Lian 2024 into the feature matrix.

    Steps:
    1. Load existing feature matrix
    2. Add metric_type column to existing rows
    3. Add covalent_lipid_mol_pct column (0 for existing rows)
    4. Build Lian rows
    5. Concatenate and save

    Returns:
        Updated feature matrix.
    """
    # Load existing
    existing = pd.read_parquet(_FEATURES_PATH)
    logger.info("Existing feature matrix: %d rows × %d cols", *existing.shape)

    # Add metric_type to existing rows
    existing = assign_metric_type(existing)

    # Add covalent_lipid_mol_pct to existing (0 — no 5th component)
    if "covalent_lipid_mol_pct" not in existing.columns:
        existing["covalent_lipid_mol_pct"] = 0.0

    # Build Lian rows
    lian_df = build_lian_rows()

    # Align columns — add any missing columns as NaN
    for col in existing.columns:
        if col not in lian_df.columns:
            lian_df[col] = np.nan
    for col in lian_df.columns:
        if col not in existing.columns:
            existing[col] = np.nan if col != "covalent_lipid_mol_pct" else 0.0

    # Reorder lian columns to match existing
    lian_df = lian_df[existing.columns]

    # Concatenate
    combined = pd.concat([existing, lian_df], ignore_index=True)
    logger.info("Combined: %d rows (added %d Lian rows)", len(combined), len(lian_df))

    if save:
        combined.to_parquet(_FEATURES_PATH, index=False)
        logger.info("Saved updated feature matrix to %s", _FEATURES_PATH)

        # Also save CSV for inspection
        csv_path = _FEATURES_PATH.with_suffix(".csv")
        combined.to_csv(csv_path, index=False)
        logger.info("Saved CSV to %s", csv_path)

    return combined


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    df = integrate()
    print(f"\nFinal shape: {df.shape}")
    print(f"Papers: {df['paper'].value_counts().to_dict()}")
    print(f"Target distribution: {df['target'].value_counts().to_dict()}")
    print(f"Metric types: {df['metric_type'].value_counts().to_dict()}")
