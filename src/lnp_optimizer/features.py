"""Feature engineering for LNP formulation ML models.

Transforms raw formulation data into numeric feature matrices
for both external (24K) and HSC (131) datasets.
"""

from __future__ import annotations

import logging
import re

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

_TARGETING_MAP = {"antibody_conjugated": 2, "intrinsic_tropism": 1, "none": 0}
_CHAIN_RE = re.compile(r"C(\d+)")


def _extract_peg_chain(val: object) -> float | None:
    """Extract numeric PEG chain length from string like 'C14'."""
    if pd.isna(val) or not val:
        return None
    m = _CHAIN_RE.search(str(val))
    return float(m.group(1)) if m else None


def _safe_ratio(a: pd.Series, b: pd.Series) -> pd.Series:  # type: ignore[type-arg]
    """Compute a/b ratio, returning NaN where b is 0 or NaN."""
    return a / b.replace(0, np.nan)


# ---------------------------------------------------------------------------
# Formulation features
# ---------------------------------------------------------------------------


def build_formulation_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build formulation-level numeric and categorical features.

    Args:
        df: Raw data with mol%, targeting, dosing columns.

    Returns:
        DataFrame with engineered features (same index).
    """
    out = pd.DataFrame(index=df.index)
    _add_mol_percent(df, out)
    _add_ratios(out)
    _add_peg_chain(df, out)
    _add_dose(df, out)
    _add_physicochemical(df, out)
    _add_targeting(df, out)
    _add_helper_charge(df, out)
    _add_species_onehot(df, out)
    _add_assay_onehot(df, out)
    _add_helper_lipid_onehot(df, out)
    _add_target_receptor(df, out)
    _add_antibody_clone(df, out)
    return out


def _add_mol_percent(df: pd.DataFrame, out: pd.DataFrame) -> None:
    """Add raw molar percent columns."""
    for col, alias in [
        ("il_mol_percent", "ionizable_mol_pct"),
        ("hl_mol_percent", "helper_mol_pct"),
        ("chl_mol_percent", "cholesterol_mol_pct"),
        ("peg_mol_percent", "peg_mol_pct"),
    ]:
        out[alias] = pd.to_numeric(df.get(col), errors="coerce")


def _add_ratios(out: pd.DataFrame) -> None:
    """Add pairwise mol% ratios."""
    out["il_to_helper_ratio"] = _safe_ratio(
        out["ionizable_mol_pct"], out["helper_mol_pct"]
    )
    out["il_to_chol_ratio"] = _safe_ratio(
        out["ionizable_mol_pct"], out["cholesterol_mol_pct"]
    )
    out["chol_to_helper_ratio"] = _safe_ratio(
        out["cholesterol_mol_pct"], out["helper_mol_pct"]
    )


def _add_peg_chain(df: pd.DataFrame, out: pd.DataFrame) -> None:
    """Add numeric PEG chain length."""
    if "peg_chain_length" in df.columns:
        out["peg_chain_numeric"] = df["peg_chain_length"].apply(
            _extract_peg_chain
        )


def _add_dose(df: pd.DataFrame, out: pd.DataFrame) -> None:
    """Add dose feature."""
    if "dose_mg_per_kg" in df.columns:
        out["dose_mg_per_kg"] = pd.to_numeric(
            df["dose_mg_per_kg"], errors="coerce"
        )


def _add_physicochemical(df: pd.DataFrame, out: pd.DataFrame) -> None:
    """Add sparse physicochemical properties."""
    for col in [
        "particle_size_nm", "pdi", "zeta_potential_mv",
        "encapsulation_efficiency_percent",
    ]:
        if col in df.columns:
            out[col] = pd.to_numeric(df[col], errors="coerce")


def _add_targeting(df: pd.DataFrame, out: pd.DataFrame) -> None:
    """Encode targeting strategy as ordinal."""
    if "targeting_strategy" in df.columns:
        out["targeting_encoded"] = (
            df["targeting_strategy"].map(_TARGETING_MAP).fillna(0).astype(int)
        )


def _add_helper_charge(df: pd.DataFrame, out: pd.DataFrame) -> None:
    """Binary feature: is helper lipid permanently cationic?"""
    if "hl_name" in df.columns:
        cationic = {"DOTAP", "DDAB", "DOTMA"}
        out["helper_is_cationic"] = (
            df["hl_name"].isin(cationic).astype(int)
        )


def _add_species_onehot(df: pd.DataFrame, out: pd.DataFrame) -> None:
    """One-hot encode species from animal_model string."""
    if "animal_model" not in df.columns:
        return
    col = df["animal_model"].fillna("").str.lower()
    out["species_mouse"] = col.str.contains("mouse").astype(int)
    out["species_nhp"] = (
        col.str.contains("rhesus") | col.str.contains("nhp")
    ).astype(int)
    out["species_human"] = col.str.contains("human").astype(int)


def _add_assay_onehot(df: pd.DataFrame, out: pd.DataFrame) -> None:
    """One-hot encode assay category."""
    if "assay_category" not in df.columns:
        return
    dummies = pd.get_dummies(
        df["assay_category"], prefix="assay"
    ).astype(int)
    for c in dummies.columns:
        out[c] = dummies[c]



def _add_helper_lipid_onehot(df: pd.DataFrame, out: pd.DataFrame) -> None:
    """One-hot encode helper lipid identity (normalized names)."""
    if "hl_name" not in df.columns:
        return
    normalized = df["hl_name"].fillna("").str.upper()
    for name, pattern in [
        ("DSPC", "DSPC"), ("DOPE", "DOPE"),
        ("DOTAP", "DOTAP"), ("DDAB", "DDAB"),
        ("DOTMA", "DOTMA"), ("EPC", "EPC"),
    ]:
        out[f"hl_{name.lower()}"] = normalized.str.contains(pattern).astype(int)


def _add_target_receptor(df: pd.DataFrame, out: pd.DataFrame) -> None:
    """Encode target receptor as ordinal."""
    if "target_receptor" not in df.columns:
        return
    normalized = df["target_receptor"].fillna("").str.upper()
    out["receptor_cd117"] = normalized.str.contains("CD117").astype(int)
    out["receptor_cd45"] = normalized.str.contains("CD45").astype(int)


def _add_antibody_clone(df: pd.DataFrame, out: pd.DataFrame) -> None:
    """Encode antibody clone identity."""
    if "antibody_clone" not in df.columns:
        return
    normalized = df["antibody_clone"].fillna("").str.upper()
    out["clone_2b8"] = normalized.str.contains("2B8").astype(int)
    out["clone_ack2"] = normalized.str.contains("ACK2").astype(int)
    out["clone_igg"] = (
        normalized.str.contains("IGG") | normalized.str.contains("ISOTYPE")
    ).astype(int)


# ---------------------------------------------------------------------------
# Molecular features
# ---------------------------------------------------------------------------


def build_molecular_features(
    df: pd.DataFrame,
    smiles_col: str = "il_smiles",
    include_fp: bool = True,
    fp_nbits: int = 2048,
) -> pd.DataFrame:
    """Build molecular descriptor + fingerprint features.

    Args:
        df: DataFrame with a SMILES column.
        smiles_col: Name of the SMILES column.
        include_fp: Whether to include Morgan fingerprint bits.
        fp_nbits: Number of fingerprint bits.

    Returns:
        DataFrame with descriptor + optional FP columns.
    """
    from external_data.descriptors import compute_morgan_fp

    out = pd.DataFrame(index=df.index)
    _add_descriptors(df, out)

    if include_fp:
        _add_fingerprints(df, out, smiles_col, fp_nbits, compute_morgan_fp)

    return out


_DESC_COLS = [
    "molecular_weight", "logp", "tpsa", "hbd", "hba",
    "rotatable_bonds", "num_rings", "heavy_atom_count",
]


def _add_descriptors(df: pd.DataFrame, out: pd.DataFrame) -> None:
    """Add scalar molecular descriptors (pre-computed if available)."""
    for c in _DESC_COLS:
        if c in df.columns:
            out[f"il_{c}"] = pd.to_numeric(df[c], errors="coerce")


def _add_fingerprints(
    df: pd.DataFrame,
    out: pd.DataFrame,
    smiles_col: str,
    nbits: int,
    fp_fn: object,
) -> None:
    """Compute Morgan fingerprint columns from SMILES."""
    fp_data: dict[object, np.ndarray] = {}
    for idx, row in df.iterrows():
        smi = row.get(smiles_col, "")
        if not smi or pd.isna(smi):
            continue
        fp = fp_fn(str(smi), nbits=nbits)  # type: ignore[operator]
        if fp is not None:
            fp_data[idx] = fp

    if fp_data:
        fp_df = pd.DataFrame.from_dict(
            fp_data, orient="index",
            columns=[f"fp_{i}" for i in range(nbits)],
        )
        for c in fp_df.columns:
            out[c] = fp_df[c]
