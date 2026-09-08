"""Integrate literature records into the atlas feature matrix.

Reads data/literature_records.json (flat per-record schema) and projects each
record onto the established feature schema. The matrix is a projection, not
the source of truth; per-record notes, null_fields, replicate arrays, and other
rich fields stay in literature_records.json.

Column conventions follow src/lnp_optimizer/integrate_lian.py:
- mol% from composition (ionizable/helper/cholesterol/peg)
- ratio features il_to_helper, il_to_chol, chol_to_helper
- peg_chain_numeric from PEG-lipid chain length (C14 -> 14)
- targeting_encoded (established ordinal: 0 none, 1 intrinsic, 2 active targeting)
- helper_is_cationic (DOTAP/DDAB/DOTMA -> 1)
- species one-hot (mouse/nhp/human)
- assay one-hot (barcode_delivery/depletion/editing/knockdown/protein_expression)
- helper-lipid one-hot (hl_dspc/dope/dotap/ddab/dotma/epc)
- receptor one-hot (receptor_cd117/cd45) and clone one-hot (clone_2b8/ack2/igg)
- il_* molecular descriptors (NaN unless the ionizable SMILES is known)
- covalent_lipid_mol_pct (0 unless a 5th covalent lipid is present)
- metric_type from assay_category (barcode_normalized/editing_pct/reporter_pct)
- target from label_for_ml (high=2, medium=1, low=0, NaN if unlabeled)
- label_boundary_case (1 for four retained 30% Lian labels, else 0)
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parent.parent.parent
_RECORDS = _ROOT / "data" / "literature_records.json"
_ANNOTATIONS = _ROOT / "annotations" / "new_paper_annotations.json"
_FEATURES_PATH = _ROOT / "data" / "features" / "hsc_features.parquet"

_LABEL_MAP = {"high": 2, "medium": 1, "low": 0}

_CATIONIC_HELPERS = {"dotap", "ddab", "dotma"}

_TARGETING_ENCODING = {
    "none": 0,
    "intrinsic_tropism": 1,
    "antibody_conjugated": 2,
    "peptide": 2,
    "aptamer": 2,
    "other": 2,
}

# Only functionalized/conjugated lipids belong in the established
# covalent_lipid_mol_pct feature. The rich record schema also stores numeric
# non-covalent components under composition.other_components, including
# tricaprylin, apoA1 mol%, and apoA1 mass. Summing the whole mapping would mix
# incompatible chemistry and units in this feature.
_COVALENT_COMPONENT_MARKERS = (
    "azide",
    "covalent",
    "dbco",
    "conjugat",
    "maleimide",
)

_LIAN_30_PERCENT_BOUNDARY_EXPERIMENTS = frozenset(
    {
        "Lian_A7_screen_n1",
        "Lian_A13_validated_n3",
        "Lian_C6_validated_n3",
        "Lian_C9_screen_n1",
    }
)

# IL molecular descriptors computed with RDKit from verified PubChem SMILES
# (see data/enrichment.json). Applied to literature records whose ionizable
# lipid is known and non-proprietary.
_IL_DESCRIPTORS = {
    "mc3": {"il_molecular_weight": 641.61, "il_logp": 13.647,
            "il_tpsa": 29.54, "il_hbd": 0, "il_hba": 3,
            "il_rotatable_bonds": 35, "il_num_rings": 0,
            "il_heavy_atom_count": 46},
    "sm-102": {"il_molecular_weight": 709.66, "il_logp": 12.669,
               "il_tpsa": 76.07, "il_hbd": 1, "il_hba": 6,
               "il_rotatable_bonds": 41, "il_num_rings": 0,
               "il_heavy_atom_count": 50},
    "alc-0315": {"il_molecular_weight": 765.72, "il_logp": 13.942,
                 "il_tpsa": 76.07, "il_hbd": 1, "il_hba": 6,
                 "il_rotatable_bonds": 44, "il_num_rings": 0,
                 "il_heavy_atom_count": 54},
}

_ASSAY_METRIC = {
    "barcode_delivery": "barcode_normalized",
    "editing": "editing_pct",
    "knockdown": "reporter_pct",
    "protein_expression": "reporter_pct",
    "depletion": "editing_pct",
}


def _classify(pct: float) -> str:
    if pct > 30.0:
        return "high"
    if pct >= 10.0:
        return "medium"
    return "low"


def _norm_lipid(name) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(name or "").lower())


def _il_key(name) -> str | None:
    n = str(name or "").lower()
    if "mc3" in n or "dlin" in n:
        return "mc3"
    if "sm-102" in n or "sm102" in n:
        return "sm-102"
    if "alc-0315" in n or "alc0315" in n:
        return "alc-0315"
    return None


def _primary_pct(efficacy: dict):
    for key in ("editing_efficiency_percent", "knockdown_percent_LSK",
                "knockdown_percent", "hsc_transfection_percent",
                "bm_mm_occupancy_percent"):
        v = efficacy.get(key)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return key, float(v)
    return None, None


def _tok(s) -> str:
    """Normalize a label key or formulation id to an alphanumeric token."""
    return re.sub(r"[^a-z0-9]", "", str(s or "").lower())


# Hanafy efficacy is whole-BM-tissue luciferase radiance, not a 0-100% HSC
# metric, so the 0-100 label thresholds do not apply. Map the user-confirmed
# Fig. S19 good/poor BM classification onto the atlas label scale instead:
# good -> high (functional BM delivery confirmed), poor -> low.
_HANAFY_CLASS_LABEL = {"good": "high", "poor": "low"}

# Explicit per-record label overrides for cases the annotation shortname keys
# cannot reach (annotation key references the platform, not the formulation id).
# Chappell: annotations label mRNACre_LNPCD117 high (near-total deletion);
# both the ex vivo deletion record and the post-transplant ddPCR confirmation
# record map to that platform. Documented in annotations/new_paper_annotations
# (chappell_2024 label_for_ml) and the key_findings text.
_LABEL_OVERRIDES = {
    "chappell_2024_mRNACre_LNPCD117_exvivo_deletion": "high",
    "chappell_2024_mRNACre_LNPCD117_posttransplant_ddPCR": "high",
}


def _record_label(record: dict, paper_labels: dict) -> str | None:
    """Resolve the efficacy label: record label_for_ml, else paper-level
    label_for_ml keyed by formulation shortname, else Hanafy BM class, else
    computed from a clean 0-100% primary metric."""
    lab = record.get("label_for_ml")
    if lab in _LABEL_MAP:
        return lab

    # explicit per-record overrides (documented in _LABEL_OVERRIDES)
    rid = record.get("record_id")
    if rid in _LABEL_OVERRIDES:
        return _LABEL_OVERRIDES[rid]

    # Hanafy: radiance is not a 0-100% metric; use the BM good/poor class.
    if record.get("source_paper") == "hanafy_2025":
        cls = (record.get("efficacy") or {}).get("bm_class_good_poor")
        return _HANAFY_CLASS_LABEL.get(str(cls).lower())

    # paper-level dict keyed by formulation fragment
    fid = _tok(record.get("formulation_id"))
    rid = _tok(record.get("record_id"))
    for key, val in paper_labels.items():
        if key in ("_thresholds", "_note", "primary_metric_used"):
            continue
        if not (isinstance(val, str) and val in _LABEL_MAP):
            continue
        token = _tok(key)
        if token and (token in fid or token in rid):
            return val

    # fall back to computing from a clean 0-100% primary HSC metric, but only
    # for in-vivo HSC-directed editing/knockdown/protein records. Off-target
    # organ (endothelial/lung), disease-burden, and in-vitro metrics stay
    # unlabeled (they are not HSC efficacy measurements).
    dl = record.get("delivery") or {}
    organ = str(dl.get("target_organ") or "").lower()
    system = str(dl.get("system") or record.get("assay_category") or "").lower()
    on_target_bm = "bone" in organ or "marrow" in organ or "hsc" in organ
    in_vivo = system in ("in_vivo", "editing", "knockdown", "protein_expression",
                         "barcode_delivery", "depletion")
    if on_target_bm and in_vivo:
        _, pct = _primary_pct(record.get("efficacy") or {})
        if pct is not None:
            return _classify(pct)
    return None


def _peg_chain(peg_name) -> float:
    n = _norm_lipid(peg_name)
    if "c14" in n or "dmg" in n:
        return 14.0
    if "c18" in n or "dsg" in n or "dspe" in n:
        return 18.0
    if "c16" in n or "dpg" in n:
        return 16.0
    return np.nan


def _targeting_encoded(strategy: object) -> int:
    """Project targeting strategy onto the matrix's established ordinal scale."""
    return _TARGETING_ENCODING.get(str(strategy or "").lower(), 0)


def _covalent_lipid_mol_pct(other_components: object) -> float:
    """Sum only explicitly functionalized lipid mol% components."""
    if not isinstance(other_components, dict):
        return 0.0

    total = 0.0
    for name, value in other_components.items():
        key = str(name).lower()
        if not key.endswith("mol_pct"):
            continue
        if not any(marker in key for marker in _COVALENT_COMPONENT_MARKERS):
            continue
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            total += float(value)
    return total


def add_label_boundary_marker(df: pd.DataFrame) -> pd.DataFrame:
    """Mark retained labels at the strict 30% decision boundary.

    The four Lian target values remain unchanged. This metadata marker lets
    threshold-sensitive model evaluation exclude the boundary cases while
    preserving the released evidence rows.
    """
    marked = df.copy()
    is_boundary = (
        marked["paper"].eq("lian_2024")
        & marked["experiment_id"].isin(_LIAN_30_PERCENT_BOUNDARY_EXPERIMENTS)
    )
    marked["label_boundary_case"] = is_boundary.astype("int8")
    return marked


def _make_row(record: dict, label: str | None) -> dict:
    comp = record.get("composition") or {}
    dl = record.get("delivery") or {}
    tgt = record.get("targeting") or {}
    assay = record.get("assay_category")

    il = comp.get("ionizable_mol_pct")
    hl = comp.get("helper_mol_pct")
    ch = comp.get("cholesterol_mol_pct")
    pg = comp.get("peg_mol_pct")

    def ratio(a, b):
        return (a / b) if (isinstance(a, (int, float)) and
                           isinstance(b, (int, float)) and b) else np.nan

    helper = _norm_lipid(comp.get("helper_lipid"))
    receptor = str(tgt.get("target_receptor") or "").lower()
    clone = str(tgt.get("antibody_clone") or "").lower()
    strategy = str(tgt.get("strategy") or "").lower()
    species = str(dl.get("species") or "").lower()

    il_key = _il_key(comp.get("ionizable_lipid"))
    il_desc = _IL_DESCRIPTORS.get(il_key, {})

    # Covalent/functionalized fifth lipid only. Other numeric components may
    # be proteins, neutral oils, or mass values and must not enter this field.
    covalent = _covalent_lipid_mol_pct(comp.get("other_components"))

    row = {
        "source": record.get("source_paper"),
        "paper": record.get("source_paper"),
        "formulation_id": record.get("formulation_id"),
        "experiment_id": record.get("experiment_id"),
        "assay_category": assay,
        "composition_confidence": record.get("confidence"),
        "ionizable_mol_pct": il if isinstance(il, (int, float)) else np.nan,
        "helper_mol_pct": hl if isinstance(hl, (int, float)) else np.nan,
        "cholesterol_mol_pct": ch if isinstance(ch, (int, float)) else np.nan,
        "peg_mol_pct": pg if isinstance(pg, (int, float)) else np.nan,
        "il_to_helper_ratio": ratio(il, hl),
        "il_to_chol_ratio": ratio(il, ch),
        "chol_to_helper_ratio": ratio(ch, hl),
        "peg_chain_numeric": _peg_chain(comp.get("peg_lipid")),
        "dose_mg_per_kg": dl.get("dose_mg_per_kg")
            if isinstance(dl.get("dose_mg_per_kg"), (int, float)) else np.nan,
        "targeting_encoded": _targeting_encoded(strategy),
        "helper_is_cationic": 1 if helper in _CATIONIC_HELPERS else 0,
        "species_mouse": 1 if "mouse" in species and "humanized" not in species else 0,
        "species_nhp": 1 if ("nhp" in species or "macaque" in species
                             or "cynomolgus" in species) else 0,
        "species_human": 1 if ("human" in species or "humanized" in species) else 0,
        "assay_barcode_delivery": 1 if assay == "barcode_delivery" else 0,
        "assay_depletion": 1 if assay == "depletion" else 0,
        "assay_editing": 1 if assay == "editing" else 0,
        "assay_knockdown": 1 if assay == "knockdown" else 0,
        "assay_protein_expression": 1 if assay == "protein_expression" else 0,
        "hl_dspc": 1 if helper == "dspc" else 0,
        "hl_dope": 1 if helper == "dope" else 0,
        "hl_dotap": 1 if helper == "dotap" else 0,
        "hl_ddab": 1 if helper == "ddab" else 0,
        "hl_dotma": 1 if helper == "dotma" else 0,
        "hl_epc": 1 if helper == "epc" else 0,
        "receptor_cd117": 1 if "cd117" in receptor or "ckit" in receptor else 0,
        "receptor_cd45": 1 if "cd45" in receptor else 0,
        "clone_2b8": 1 if "2b8" in clone else 0,
        "clone_ack2": 1 if "ack2" in clone else 0,
        "clone_igg": 1 if "igg" in clone or "isotype" in clone else 0,
        "il_molecular_weight": il_desc.get("il_molecular_weight", np.nan),
        "il_logp": il_desc.get("il_logp", np.nan),
        "il_tpsa": il_desc.get("il_tpsa", np.nan),
        "il_hbd": il_desc.get("il_hbd", np.nan),
        "il_hba": il_desc.get("il_hba", np.nan),
        "il_rotatable_bonds": il_desc.get("il_rotatable_bonds", np.nan),
        "il_num_rings": il_desc.get("il_num_rings", np.nan),
        "il_heavy_atom_count": il_desc.get("il_heavy_atom_count", np.nan),
        "covalent_lipid_mol_pct": covalent,
        "metric_type": _ASSAY_METRIC.get(assay, "unknown"),
        "target": _LABEL_MAP.get(label, np.nan),
        "label_boundary_case": 0,
    }
    return row


def build_literature_rows() -> pd.DataFrame:
    records = json.loads(_RECORDS.read_text())["records"]
    annotations = json.loads(_ANNOTATIONS.read_text())
    paper_labels = {p["paper_id"]: (p.get("label_for_ml") or {})
                    .get("hsc_efficacy_class", {})
                    for p in annotations.get("papers", [])}

    rows = []
    n_labeled = 0
    for r in records:
        plabels = paper_labels.get(r.get("source_paper"), {})
        label = _record_label(r, plabels if isinstance(plabels, dict) else {})
        rows.append(_make_row(r, label))
        if label in _LABEL_MAP:
            n_labeled += 1
    logger.info("Built %d literature rows (%d labeled)", len(rows), n_labeled)
    return pd.DataFrame(rows)


def integrate(save: bool = True) -> pd.DataFrame:
    existing = pd.read_parquet(_FEATURES_PATH)
    logger.info("Existing feature matrix: %d rows x %d cols", *existing.shape)

    literature_df = build_literature_rows()

    for col in existing.columns:
        if col not in literature_df.columns:
            literature_df[col] = np.nan
    for col in literature_df.columns:
        if col not in existing.columns:
            existing[col] = 0.0 if col == "covalent_lipid_mol_pct" else np.nan
    literature_df = literature_df[existing.columns]

    combined = pd.concat([existing, literature_df], ignore_index=True)
    combined = add_label_boundary_marker(combined)
    logger.info(
        "Integrated %d literature rows; matrix contains %d rows",
        len(literature_df),
        len(combined),
    )

    if save:
        combined.to_parquet(_FEATURES_PATH, index=False)
        combined.to_csv(_FEATURES_PATH.with_suffix(".csv"), index=False)
        logger.info("Saved consolidated matrix to %s", _FEATURES_PATH)
    return combined


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    df = integrate()
    print(f"\nFinal shape: {df.shape}")
    print(f"Papers: {df['paper'].value_counts().to_dict()}")
    print(f"Target distribution: {df['target'].value_counts(dropna=False).to_dict()}")
