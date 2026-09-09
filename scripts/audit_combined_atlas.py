"""Deduplication, integrity, and logical-contradiction audit for the atlas.

The audit checks stable content fingerprints, reviews cross-layer overlaps,
detects duplicate matrix identities, and checks feature encodings for internal
contradictions. It exits nonzero only for blocking errors. Documented source
anomalies and labeling boundary cases are reported without changing source data.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
_FEATURES = _ROOT / "data" / "features" / "hsc_features.parquet"
_HSC = _ROOT / "data" / "hsc" / "hsc_curated.parquet"
_LITERATURE_RECORDS = _ROOT / "data" / "literature_records.json"
_LITERATURE_ANNOTATIONS = _ROOT / "annotations" / "new_paper_annotations.json"
_REPORT = _ROOT / "data" / "audit" / "consolidated_audit.json"

_CURATED_ROWS = 135
_LITERATURE_ROWS = 198
_EXPECTED_COLUMNS = 48
_EXPECTED_HSC_SHA256 = "8a19ad2fd52ec1a1beec2c8bfee67e474e234f1e8c3121358ca3617e20b99172"
_EXPECTED_CURATED_MATRIX_SHA256 = (
    "7ae79acbefedb1db7b50d8a26cd84a82270a8de248cc3d1d7f3850b9defa57ad"
)
_EXPECTED_LIAN_ROWS_SHA256 = (
    "56035c2236d97ed72f0bdb22252902d15470c92ec07dee31652f68a13c6f6957"
)
_EXPECTED_LIAN_ANNOTATION_SHA256 = (
    "bab56df74238e646b19afed19ca4887052d81a7378b1dd95e361961c06a8bc23"
)
_LIAN_BOUNDARY_EXPERIMENTS = frozenset(
    {
        "Lian_A7_screen_n1",
        "Lian_A13_validated_n3",
        "Lian_C6_validated_n3",
        "Lian_C9_screen_n1",
    }
)

_ASSAY_COLUMNS = {
    "barcode_delivery": "assay_barcode_delivery",
    "depletion": "assay_depletion",
    "editing": "assay_editing",
    "knockdown": "assay_knockdown",
    "protein_expression": "assay_protein_expression",
}
_SPECIES_COLUMNS = ["species_mouse", "species_nhp", "species_human"]
_HELPER_COLUMNS = ["hl_dspc", "hl_dope", "hl_dotap", "hl_ddab", "hl_dotma", "hl_epc"]
_CLONE_COLUMNS = ["clone_2b8", "clone_ack2", "clone_igg"]
_DESCRIPTOR_COLUMNS = [
    "il_molecular_weight",
    "il_logp",
    "il_tpsa",
    "il_hbd",
    "il_hba",
    "il_rotatable_bonds",
    "il_num_rings",
    "il_heavy_atom_count",
]
_TARGETING_ENCODING = {
    "none": 0,
    "intrinsic_tropism": 1,
    "antibody_conjugated": 2,
    "peptide": 2,
    "aptamer": 2,
    "other": 2,
}
_COVALENT_MARKERS = ("azide", "covalent", "dbco", "conjugat", "maleimide")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _frame_sha256(frame: pd.DataFrame) -> str:
    payload = frame.to_csv(index=False, lineterminator="\n").encode()
    return hashlib.sha256(payload).hexdigest()


def _normalize_doi(value: object) -> str:
    doi = str(value or "").strip().lower()
    doi = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", doi)
    return doi.rstrip("/")


def _normalize_title(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def _paper_metadata(entry: dict[str, Any]) -> dict[str, Any]:
    paper = entry.get("paper") or entry.get("paper_metadata") or {}
    return paper if isinstance(paper, dict) else {}


def _existing_annotation_papers() -> list[dict[str, Any]]:
    papers: list[dict[str, Any]] = []
    for path in sorted((_ROOT / "annotations").glob("*.json")):
        if path.name == _LITERATURE_ANNOTATIONS.name:
            continue
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue

        if isinstance(data, list):
            entries = data
        elif isinstance(data, dict) and isinstance(data.get("papers"), list):
            entries = data["papers"]
        elif isinstance(data, dict):
            entries = [data]
        else:
            entries = []

        for entry in entries:
            if not isinstance(entry, dict):
                continue
            metadata = _paper_metadata(entry)
            if not metadata:
                continue
            papers.append(
                {
                    "annotation_file": f"annotations/{path.name}",
                    "doi": metadata.get("doi") or metadata.get("doi_or_id"),
                    "title": metadata.get("title"),
                }
            )
    return papers


def _cross_layer_paper_overlaps(
    literature_annotations: dict[str, Any],
) -> list[dict[str, Any]]:
    overlaps: list[dict[str, Any]] = []
    existing = _existing_annotation_papers()
    for entry in literature_annotations.get("papers", []):
        metadata = _paper_metadata(entry)
        doi = _normalize_doi(metadata.get("doi") or metadata.get("doi_or_id"))
        title = _normalize_title(metadata.get("title"))
        for candidate in existing:
            candidate_doi = _normalize_doi(candidate.get("doi"))
            candidate_title = _normalize_title(candidate.get("title"))
            doi_match = bool(doi and candidate_doi and doi == candidate_doi)
            title_match = bool(title and candidate_title and title == candidate_title)
            if doi_match or title_match:
                overlaps.append(
                    {
                        "paper_id": entry.get("paper_id"),
                        "matching_annotation_file": candidate["annotation_file"],
                        "doi": doi or None,
                        "doi_match": doi_match,
                        "title_match": title_match,
                    }
                )
    return overlaps


def _structured_replicates(record: dict[str, Any]) -> dict[str, Any] | None:
    replicates = (record.get("efficacy") or {}).get("replicates")
    return replicates if isinstance(replicates, dict) else None


def _xu_evidence_overlaps(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        if record.get("source_paper") != "xu_2026":
            continue
        experiment = str(record.get("experiment_id") or "")
        if "PCSK9" not in experiment:
            continue
        match = re.search(r"LNP-?(\d+)", str(record.get("formulation_id") or ""))
        if not match:
            continue
        groups.setdefault(match.group(1).zfill(3), []).append(record)

    overlaps: list[dict[str, Any]] = []
    for lipid_id, members in sorted(groups.items()):
        if len(members) < 2:
            continue
        arrays = [_structured_replicates(record) for record in members]
        structured = [array for array in arrays if array is not None]
        same_arrays = len(structured) > 1 and all(
            array == structured[0] for array in structured[1:]
        )
        overlaps.append(
            {
                "formulation_token": f"LNP-{lipid_id}",
                "record_ids": [record["record_id"] for record in members],
                "experiment_ids": [record["experiment_id"] for record in members],
                "primary_values": [
                    (record.get("efficacy") or {}).get("editing_efficiency_percent")
                    for record in members
                ],
                "structured_replicates_equal": same_arrays if len(structured) > 1 else None,
                "classification": "same_formulation_evidence_overlap",
                "decision": (
                    "Retain both roles. The lead record preserves narrative and lead-level "
                    "context; the library record preserves the uniform screen row and replicate "
                    "structure. They have distinct record_id and experiment_id values. Group by "
                    "formulation token in formulation-level validation to avoid leakage."
                ),
            }
        )
    return overlaps


def _expected_covalent(record: dict[str, Any]) -> float:
    other = (record.get("composition") or {}).get("other_components")
    if not isinstance(other, dict):
        return 0.0
    total = 0.0
    for name, value in other.items():
        key = str(name).lower()
        if not key.endswith("mol_pct"):
            continue
        if not any(marker in key for marker in _COVALENT_MARKERS):
            continue
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            total += float(value)
    return total


def _check(condition: bool, check_id: str, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if condition else "fail", "detail": detail}


def _duplicate_groups(df: pd.DataFrame, columns: list[str]) -> list[dict[str, Any]]:
    duplicated = df[df.duplicated(columns, keep=False)]
    groups: list[dict[str, Any]] = []
    if duplicated.empty:
        return groups
    for key, group in duplicated.groupby(columns, dropna=False, sort=True):
        values = key if isinstance(key, tuple) else (key,)
        groups.append(
            {
                "identity": {
                    column: None if pd.isna(value) else value
                    for column, value in zip(columns, values, strict=True)
                },
                "row_indices": group.index.astype(int).tolist(),
            }
        )
    return groups


def _lian_boundary_warnings(df: pd.DataFrame) -> list[dict[str, Any]]:
    annotation = json.loads((_ROOT / "annotations" / "lian_2024.json").read_text())
    flagged: list[dict[str, Any]] = []
    for formulation in annotation["formulations_screen"]["formulations"]:
        fid = formulation["id"]
        candidates = [
            (
                formulation.get("bm_delivery_screen_n1") or formulation.get("bm_delivery"),
                "screen_n1",
            ),
            (formulation.get("bm_delivery_validated_n3"), "validated_n3"),
        ]
        for delivery, suffix in candidates:
            if not delivery or delivery.get("LT_HSC") != 30:
                continue
            experiment_id = f"{fid}_{suffix}"
            row = df[(df["paper"] == "lian_2024") & (df["experiment_id"] == experiment_id)]
            target = None if row.empty else float(row.iloc[0]["target"])
            flagged.append(
                {
                    "formulation_id": fid,
                    "experiment_id": experiment_id,
                    "lt_hsc_percent": 30,
                    "stored_target": target,
                    "threshold_target": 1,
                }
            )
    return flagged


def build_report() -> dict[str, Any]:
    df = pd.read_parquet(_FEATURES)
    records_doc = json.loads(_LITERATURE_RECORDS.read_text())
    records = records_doc["records"]
    literature_annotations = json.loads(_LITERATURE_ANNOTATIONS.read_text())
    curated = df.iloc[:_CURATED_ROWS].reset_index(drop=True)
    literature = df.iloc[_CURATED_ROWS:].reset_index(drop=True)

    errors: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []

    data_hsc_equal = _sha256(_HSC) == _EXPECTED_HSC_SHA256
    if not data_hsc_equal:
        errors.append(
            {
                "id": "protected_hsc_source_changed",
                "detail": "data/hsc/hsc_curated.parquet content fingerprint changed",
            }
        )
    checks.append(
        _check(
            data_hsc_equal,
            "protected_hsc_source_identity",
            "matches the curated source content fingerprint",
        )
    )

    checks.append(
        _check(
            df.shape == (_CURATED_ROWS + _LITERATURE_ROWS, _EXPECTED_COLUMNS),
            "matrix_shape",
            f"observed {df.shape[0]} rows x {df.shape[1]} columns; expected 333 x 48",
        )
    )

    value_columns = [column for column in df.columns if column != "label_boundary_case"]
    curated_values_equal = (
        _frame_sha256(curated.loc[:, value_columns]) == _EXPECTED_CURATED_MATRIX_SHA256
    )
    if not curated_values_equal:
        errors.append(
            {
                "id": "curated_matrix_values_changed",
                "detail": "curated matrix content fingerprint changed",
            }
        )
    checks.append(
        _check(
            curated_values_equal,
            "curated_matrix_value_identity",
            "all curated matrix values match the expected content fingerprint",
        )
    )

    current_lian_boundary = df.loc[
        df["paper"].eq("lian_2024")
        & df["experiment_id"].isin(_LIAN_BOUNDARY_EXPERIMENTS),
        value_columns,
    ]
    lian_boundary_values_equal = (
        _frame_sha256(current_lian_boundary) == _EXPECTED_LIAN_ROWS_SHA256
    )
    lian_annotation_equal = (
        _sha256(_ROOT / "annotations" / "lian_2024.json")
        == _EXPECTED_LIAN_ANNOTATION_SHA256
    )
    if not lian_boundary_values_equal or not lian_annotation_equal:
        errors.append(
            {
                "id": "lian_boundary_values_changed",
                "matrix_values_match": lian_boundary_values_equal,
                "annotation_file_matches": lian_annotation_equal,
            }
        )
    checks.append(
        _check(
            lian_boundary_values_equal and lian_annotation_equal,
            "lian_boundary_identity",
            "four boundary rows and their source annotation match expected fingerprints",
        )
    )

    projection_mismatches: list[dict[str, Any]] = []
    if len(literature) == len(records):
        for offset, (row, record) in enumerate(
            zip(literature.to_dict("records"), records, strict=True)
        ):
            for field, record_field in (
                ("paper", "source_paper"),
                ("formulation_id", "formulation_id"),
                ("experiment_id", "experiment_id"),
                ("assay_category", "assay_category"),
            ):
                if row[field] != record[record_field]:
                    projection_mismatches.append(
                        {
                            "row_index": _CURATED_ROWS + offset,
                            "record_id": record["record_id"],
                            "field": field,
                            "matrix": row[field],
                            "record": record[record_field],
                        }
                    )
    else:
        projection_mismatches.append(
            {"detail": f"matrix literature rows {len(literature)} != records {len(records)}"}
        )
    if projection_mismatches:
        errors.append(
            {"id": "literature_projection_alignment", "examples": projection_mismatches[:20]}
        )
    checks.append(
        _check(
            not projection_mismatches,
            "literature_projection_alignment",
            f"{len(records) - len(projection_mismatches)}/{len(records)} records "
            "aligned by order and identity",
        )
    )

    record_id_counts = Counter(record.get("record_id") for record in records)
    duplicate_record_ids = sorted(
        str(record_id) for record_id, count in record_id_counts.items() if count > 1
    )
    exact_duplicate_rows = int(df.duplicated(keep=False).sum())
    exact_rows_removable = int(df.duplicated().sum())
    identity_columns = ["paper", "formulation_id", "experiment_id", "assay_category"]
    identity_duplicate_groups = _duplicate_groups(df, identity_columns)

    if duplicate_record_ids:
        errors.append(
            {"id": "duplicate_literature_record_ids", "record_ids": duplicate_record_ids}
        )
    if exact_rows_removable:
        errors.append(
            {"id": "exact_matrix_duplicates", "removable_rows": exact_rows_removable}
        )
    if identity_duplicate_groups:
        errors.append(
            {"id": "duplicate_matrix_identity", "groups": identity_duplicate_groups}
        )

    numeric = df.select_dtypes(include=[np.number])
    nonfinite: dict[str, int] = {}
    for column in numeric.columns:
        count = int(np.isinf(numeric[column].dropna()).sum())
        if count:
            nonfinite[column] = count
    if nonfinite:
        errors.append({"id": "infinite_numeric_values", "columns": nonfinite})
    checks.append(
        _check(not nonfinite, "finite_numeric_values", "no positive or negative infinity")
    )

    ratio_failures: list[dict[str, Any]] = []
    for column, numerator, denominator in (
        ("il_to_helper_ratio", "ionizable_mol_pct", "helper_mol_pct"),
        ("il_to_chol_ratio", "ionizable_mol_pct", "cholesterol_mol_pct"),
        ("chol_to_helper_ratio", "cholesterol_mol_pct", "helper_mol_pct"),
    ):
        expected = df[numerator] / df[denominator].replace(0, np.nan)
        comparable = df[column].notna() & expected.notna()
        bad = comparable & ~np.isclose(df[column], expected, rtol=1e-10, atol=1e-10)
        for index in df.index[bad]:
            ratio_failures.append(
                {
                    "row_index": int(index),
                    "column": column,
                    "stored": float(df.at[index, column]),
                    "expected": float(expected.at[index]),
                }
            )
    if ratio_failures:
        errors.append({"id": "ratio_mismatch", "examples": ratio_failures[:20]})
    checks.append(
        _check(not ratio_failures, "ratio_consistency", "all populated engineered ratios reproduce")
    )

    assay_failures: list[int] = []
    assay_sum = df[list(_ASSAY_COLUMNS.values())].sum(axis=1)
    for index, row in df.iterrows():
        expected_column = _ASSAY_COLUMNS.get(row["assay_category"])
        if assay_sum.at[index] != 1 or expected_column is None or row[expected_column] != 1:
            assay_failures.append(int(index))
    if assay_failures:
        errors.append({"id": "assay_one_hot_mismatch", "row_indices": assay_failures[:50]})
    checks.append(
        _check(
            not assay_failures,
            "assay_one_hot_consistency",
            "each row has exactly one assay bit matching assay_category",
        )
    )

    binary_columns = _SPECIES_COLUMNS + _HELPER_COLUMNS + _CLONE_COLUMNS + list(
        _ASSAY_COLUMNS.values()
    ) + ["helper_is_cationic", "label_boundary_case"]
    binary_failures = {
        column: sorted(df.loc[~df[column].isin([0, 1]), column].dropna().unique().tolist())
        for column in binary_columns
        if not df[column].isin([0, 1]).all()
    }
    if binary_failures:
        errors.append({"id": "nonbinary_one_hot_values", "columns": binary_failures})
    checks.append(
        _check(
            not binary_failures,
            "binary_feature_domains",
            "all one-hot and binary values are 0 or 1",
        )
    )

    expected_boundary = (
        df["paper"].eq("lian_2024")
        & df["experiment_id"].isin(_LIAN_BOUNDARY_EXPERIMENTS)
    ).astype("int8")
    boundary_marker_matches = bool(df["label_boundary_case"].eq(expected_boundary).all())
    if not boundary_marker_matches:
        errors.append(
            {
                "id": "label_boundary_marker_mismatch",
                "row_indices": df.index[
                    df["label_boundary_case"].ne(expected_boundary)
                ].astype(int).tolist(),
            }
        )
    checks.append(
        _check(
            boundary_marker_matches,
            "label_boundary_marker",
            "exactly four Lian 30% boundary rows are marked",
        )
    )

    helper_multi = df[_HELPER_COLUMNS].sum(axis=1) > 1
    clone_multi = df[_CLONE_COLUMNS].sum(axis=1) > 1
    if helper_multi.any() or clone_multi.any():
        errors.append(
            {
                "id": "mutually_exclusive_encoding",
                "helper_rows": df.index[helper_multi].astype(int).tolist(),
                "clone_rows": df.index[clone_multi].astype(int).tolist(),
            }
        )
    checks.append(
        _check(
            not helper_multi.any() and not clone_multi.any(),
            "mutually_exclusive_encodings",
            "helper and clone one-hot groups contain at most one positive bit",
        )
    )

    descriptor_counts = df[_DESCRIPTOR_COLUMNS].notna().sum(axis=1)
    partial_descriptors = df.index[~descriptor_counts.isin([0, len(_DESCRIPTOR_COLUMNS)])]
    if len(partial_descriptors):
        errors.append(
            {
                "id": "partial_descriptor_blocks",
                "row_indices": partial_descriptors.astype(int).tolist(),
            }
        )
    checks.append(
        _check(
            len(partial_descriptors) == 0,
            "descriptor_block_consistency",
            f"{int((descriptor_counts == len(_DESCRIPTOR_COLUMNS)).sum())} complete blocks and "
            f"{int((descriptor_counts == 0).sum())} fully null blocks",
        )
    )

    domain_failures: dict[str, list[float]] = {}
    for column in (
        "ionizable_mol_pct",
        "helper_mol_pct",
        "cholesterol_mol_pct",
        "peg_mol_pct",
    ):
        bad = df.loc[df[column].notna() & ~df[column].between(0, 100), column]
        if not bad.empty:
            domain_failures[column] = sorted(set(float(value) for value in bad))
    bad_dose = df.loc[df["dose_mg_per_kg"].notna() & (df["dose_mg_per_kg"] <= 0)]
    bad_target = df.loc[df["target"].notna() & ~df["target"].isin([0, 1, 2])]
    if not bad_dose.empty:
        domain_failures["dose_mg_per_kg"] = bad_dose["dose_mg_per_kg"].tolist()
    if not bad_target.empty:
        domain_failures["target"] = bad_target["target"].tolist()
    if domain_failures:
        errors.append({"id": "numeric_domain_failures", "columns": domain_failures})
    checks.append(
        _check(not domain_failures, "numeric_domains", "mol%, dose, and target domains valid")
    )

    targeting_mismatches: list[dict[str, Any]] = []
    covalent_mismatches: list[dict[str, Any]] = []
    for offset, record in enumerate(records):
        row = literature.iloc[offset]
        strategy = str((record.get("targeting") or {}).get("strategy") or "").lower()
        expected_targeting = _TARGETING_ENCODING.get(strategy, 0)
        if int(row["targeting_encoded"]) != expected_targeting:
            targeting_mismatches.append(
                {
                    "record_id": record["record_id"],
                    "strategy": strategy,
                    "stored": int(row["targeting_encoded"]),
                    "expected": expected_targeting,
                }
            )
        expected_covalent = _expected_covalent(record)
        if not math.isclose(
            float(row["covalent_lipid_mol_pct"]), expected_covalent, rel_tol=0, abs_tol=1e-12
        ):
            covalent_mismatches.append(
                {
                    "record_id": record["record_id"],
                    "stored": float(row["covalent_lipid_mol_pct"]),
                    "expected": expected_covalent,
                }
            )
    if targeting_mismatches:
        errors.append({"id": "targeting_projection_mismatch", "examples": targeting_mismatches})
    if covalent_mismatches:
        errors.append({"id": "covalent_projection_mismatch", "examples": covalent_mismatches})
    checks.append(
        _check(
            not targeting_mismatches,
            "targeting_projection_semantics",
            "literature rows use the established ordinal encoding: 0 none, 1 intrinsic, "
            "and 2 active",
        )
    )
    checks.append(
        _check(
            not covalent_mismatches,
            "covalent_projection_semantics",
            "non-covalent oils, proteins, and mass values are excluded",
        )
    )

    cross_layer_overlaps = _cross_layer_paper_overlaps(literature_annotations)
    tessera_matrix_rows = int(
        df["paper"].fillna("").str.lower().str.startswith("tessera").sum()
    )
    palchaudhuri_rows = int((df["paper"] == "palchaudhuri_2025").sum())
    chappell_rows = int((df["paper"] == "chappell_2024").sum())
    breda_rows = int((df["paper"] == "breda_2023").sum())

    palchaudhuri_tessera_confirmed = any(
        overlap["paper_id"] == "palchaudhuri_2025"
        and overlap["matching_annotation_file"]
        == "annotations/tessera_ash2025_blood.json"
        and overlap["doi_match"]
        and overlap["title_match"]
        for overlap in cross_layer_overlaps
    )
    palchaudhuri_check = (
        palchaudhuri_tessera_confirmed
        and palchaudhuri_rows == 3
        and tessera_matrix_rows == 0
    )
    if not palchaudhuri_check:
        errors.append(
            {
                "id": "palchaudhuri_tessera_resolution_failed",
                "source_match": palchaudhuri_tessera_confirmed,
                "palchaudhuri_matrix_rows": palchaudhuri_rows,
                "tessera_matrix_rows": tessera_matrix_rows,
            }
        )
    checks.append(
        _check(
            palchaudhuri_check,
            "palchaudhuri_tessera_resolution",
            "DOI and title match; 3 canonical rows and 0 Tessera provenance rows in matrix",
        )
    )

    matrix_identity = ["formulation_id", "experiment_id", "assay_category"]
    chappell_identities = {
        tuple(row)
        for row in df.loc[df["paper"] == "chappell_2024", matrix_identity].itertuples(
            index=False, name=None
        )
    }
    breda_identities = {
        tuple(row)
        for row in df.loc[df["paper"] == "breda_2023", matrix_identity].itertuples(
            index=False, name=None
        )
    }
    chappell_breda_shared = sorted(chappell_identities & breda_identities)
    chappell_records = [
        record for record in records if record["source_paper"] == "chappell_2024"
    ]
    composition_value_keys = (
        "ionizable_lipid",
        "helper_lipid",
        "cholesterol",
        "peg_lipid",
        "ionizable_mol_pct",
        "helper_mol_pct",
        "cholesterol_mol_pct",
        "peg_mol_pct",
    )
    chappell_rich_composition_null = all(
        all((record.get("composition") or {}).get(key) is None for key in composition_value_keys)
        for record in chappell_records
    )
    matrix_composition_columns = [
        "ionizable_mol_pct",
        "helper_mol_pct",
        "cholesterol_mol_pct",
        "peg_mol_pct",
        "il_to_helper_ratio",
        "il_to_chol_ratio",
        "chol_to_helper_ratio",
        "peg_chain_numeric",
    ]
    chappell_matrix_composition_null = bool(
        df.loc[df["paper"] == "chappell_2024", matrix_composition_columns]
        .isna()
        .all()
        .all()
    )
    chappell_check = (
        chappell_rows == 2
        and breda_rows == 9
        and not chappell_breda_shared
        and chappell_rich_composition_null
        and chappell_matrix_composition_null
    )
    if not chappell_check:
        errors.append(
            {
                "id": "chappell_breda_resolution_failed",
                "chappell_matrix_rows": chappell_rows,
                "breda_matrix_rows": breda_rows,
                "shared_identities": chappell_breda_shared,
                "rich_composition_null": chappell_rich_composition_null,
                "matrix_composition_null": chappell_matrix_composition_null,
            }
        )
    checks.append(
        _check(
            chappell_check,
            "chappell_breda_resolution",
            "2 Chappell and 9 Breda rows; no shared identity; Chappell composition remains null",
        )
    )

    warnings: list[dict[str, Any]] = []
    lian_boundary = _lian_boundary_warnings(df)

    outlier_record = next(
        record
        for record in records
        if record["record_id"] == "xu_2026_LNP123_ABE8e_PCSK9_secondary_screen"
    )
    outlier_values = (outlier_record.get("efficacy") or {}).get("replicates", {}).get(
        "single_dose", []
    )
    warnings.append(
        {
            "id": "xu_LNP123_source_outlier",
            "severity": "medium",
            "status": "documented_no_change",
            "record_id": outlier_record["record_id"],
            "single_dose_replicates": outlier_values,
            "description": (
                "The source-reported 116% replicate is impossible but preserved verbatim."
            ),
        }
    )

    species_multi = df[df[_SPECIES_COLUMNS].sum(axis=1) > 1]
    informational = [
        {
            "id": "lian_30_percent_boundary",
            "status": "documented_boundary_convention",
            "records": lian_boundary,
            "description": (
                "The current rule is high >30% and medium 10-30%. Four Lian rows at exactly "
                "30% retain their established high labels. They are marked boundary "
                "cases, are excluded from threshold-sensitive evaluation, and are not errors."
            ),
        },
        {
            "id": "multi_species_aggregate_rows",
            "count": int(len(species_multi)),
            "rows": [
                {
                    "paper": row["paper"],
                    "formulation_id": row["formulation_id"],
                    "experiment_id": row["experiment_id"],
                }
                for _, row in species_multi.iterrows()
            ],
            "description": (
                "The three Palchaudhuri abstract records aggregate humanized-mouse and NHP "
                "claims, so multiple species bits are intentional."
            ),
        },
    ]

    failed_checks = [check for check in checks if check["status"] == "fail"]
    if failed_checks and not errors:
        errors.append({"id": "failed_checks", "checks": failed_checks})

    return {
        "audit": "atlas_dedupe_and_contradiction_scan",
        "date": date.today().isoformat(),
        "inputs": {
            "feature_matrix": {
                "path": "data/features/hsc_features.parquet",
                "sha256": _sha256(_FEATURES),
            },
            "curated_source": {
                "path": "data/hsc/hsc_curated.parquet",
                "sha256": _sha256(_HSC),
            },
            "literature_records": {
                "path": "data/literature_records.json",
                "sha256": _sha256(_LITERATURE_RECORDS),
            },
        },
        "dataset": {
            "rows": len(df),
            "curated_rows": len(curated),
            "literature_rows": len(literature),
            "columns": len(df.columns),
            "papers": int(df["paper"].nunique()),
            "paper_row_counts": {
                str(key): int(value)
                for key, value in df["paper"].value_counts().sort_index().items()
            },
        },
        "invariants": {
            "curated_matrix_values_match": curated_values_equal,
            "lian_boundary_values_match": lian_boundary_values_equal,
            "lian_annotation_matches": lian_annotation_equal,
            "curated_source_matches": data_hsc_equal,
            "literature_projection_records_aligned": len(projection_mismatches) == 0,
        },
        "dedupe": {
            "status": "complete" if not errors else "failed",
            "exact_48_column_duplicate_rows": exact_duplicate_rows,
            "exact_rows_removable": exact_rows_removable,
            "duplicate_literature_record_ids": duplicate_record_ids,
            "duplicate_matrix_identity_groups": identity_duplicate_groups,
            "cross_layer_source_overlaps": cross_layer_overlaps,
            "palchaudhuri_tessera_decision": {
                "same_source_confirmed": palchaudhuri_tessera_confirmed,
                "canonical_flat_schema_source": "data/literature_records.json",
                "canonical_record_ids": [
                    record["record_id"]
                    for record in records
                    if record["source_paper"] == "palchaudhuri_2025"
                ],
                "canonical_matrix_rows": palchaudhuri_rows,
                "tessera_annotation_matrix_rows": tessera_matrix_rows,
                "provenance_chain_retained": [
                    "annotations/tessera_esgct2024_press.json",
                    "annotations/tessera_ash2024_blood.json",
                    "annotations/tessera_asgct2025_press.json",
                    "annotations/tessera_ash2025_blood.json",
                    "annotations/tessera_ash2025_press.json",
                ],
                "action": "No matrix row removed; Tessera files remain provenance-only.",
            },
            "chappell_breda_decision": {
                "chappell_matrix_rows": chappell_rows,
                "breda_matrix_rows": breda_rows,
                "duplicate_identity_groups": chappell_breda_shared,
                "rich_record_composition_null": chappell_rich_composition_null,
                "matrix_composition_null": chappell_matrix_composition_null,
                "composition_backfilled": not (
                    chappell_rich_composition_null and chappell_matrix_composition_null
                ),
                "action": (
                    "Retain both Chappell records with null composition. Breda is analog support "
                    "for the platform, not the same experiment or a duplicate row."
                ),
            },
            "same_source_evidence_overlaps": _xu_evidence_overlaps(records),
            "rows_removed": 0,
            "final_rows": len(df),
        },
        "logical_contradiction_scan": {
            "status": "pass_with_documented_warnings" if not errors else "fail",
            "errors": errors,
            "warnings": warnings,
            "informational": informational,
            "checks": checks,
        },
        "open_items_not_stubbed": {
            "partial_pending_main_text": [
                record["record_id"]
                for record in records
                if record.get("status") == "partial_pending_main_text"
            ],
            "pending_paywall_stubs": [stub["source_paper"] for stub in records_doc["stubs"]],
        },
    }


def main() -> int:
    report = build_report()
    _REPORT.parent.mkdir(parents=True, exist_ok=True)
    _REPORT.write_text(json.dumps(report, indent=2) + "\n")

    dataset = report["dataset"]
    dedupe = report["dedupe"]
    scan = report["logical_contradiction_scan"]
    print(
        f"Audited {dataset['rows']} rows x {dataset['columns']} columns"
    )
    print(f"Exact duplicate rows removable: {dedupe['exact_rows_removable']}")
    print(f"Contradiction errors: {len(scan['errors'])}")
    print(f"Documented warning groups: {len(scan['warnings'])}")
    print(f"Wrote {_REPORT.relative_to(_ROOT)}")
    return 1 if scan["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
