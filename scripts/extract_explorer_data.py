"""Extract all data arrays for the interactive explorer JSX.

Reads model outputs and annotation JSONs and writes explorer_data.json
with every data constant the explorer needs.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

from lnp_optimizer.explorer_analysis import build_analysis

_ROOT = Path(__file__).resolve().parent.parent
_FEAT_PATH = _ROOT / "data" / "features" / "hsc_features.parquet"
_KIM_PATH = _ROOT / "data" / "kim_screen" / "kim_2024_screen_corrected.json"
_LIAN_PATH = _ROOT / "annotations" / "lian_2024.json"
_SHAP_PATH = _ROOT / "data" / "models" / "shap_values.csv"
_SHAP_PARQUET_PATH = _ROOT / "data" / "models" / "shap_values.parquet"
_LOPOCV_PATH = _ROOT / "data" / "models" / "lopocv_results.json"
_VALIDATION_PATH = _ROOT / "data" / "models" / "validation_comparison.json"
_LITERATURE_RECORDS_PATH = _ROOT / "data" / "literature_records.json"
_LITERATURE_ANNOTATIONS_PATH = _ROOT / "annotations" / "new_paper_annotations.json"
_OUT_PATH = _ROOT / "explorer_data.json"
_CURATED_ROWS = 135
_ATLAS_ROWS = 331
_LITERATURE_RECORD_COUNT = 196

_LEGACY_ANNOTATIONS = {
    "breda_2023": _ROOT / "annotations" / "breda_2023.json",
    "shi_2023": _ROOT / "annotations" / "shi_2023.json",
    "kim_2024": _ROOT / "annotations" / "kim_2024.json",
    "lian_2024": _ROOT / "annotations" / "lian_2024.json",
}
_KNOWN_SARS = {
    "ionizable_mol_pct",
    "receptor_cd117",
    "dose_mg_per_kg",
    "hl_dotap",
    "helper_mol_pct",
}
_LITERATURE_FINDINGS = {
    "chol_to_helper_ratio",
    "cholesterol_mol_pct",
    "il_molecular_weight",
}


def _shap_ranking() -> list[dict[str, Any]]:
    """Read the ranked SHAP summary, with a tracked-parquet fallback."""
    if _SHAP_PATH.exists():
        df = pd.read_csv(_SHAP_PATH)
        return df.to_dict("records")

    raw = pd.read_parquet(_SHAP_PARQUET_PATH)
    means = raw.abs().mean().sort_values(ascending=False)
    return [
        {
            "rank": rank,
            "feature": feature,
            "mean_abs_shap": float(value),
            "type": (
                "known"
                if feature in _KNOWN_SARS
                else "literature"
                if feature in _LITERATURE_FINDINGS
                else "other"
            ),
        }
        for rank, (feature, value) in enumerate(means.items(), 1)
    ]


def _shap_data(ranking: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert the atlas SHAP ranking to explorer labels."""
    label_map = {
        "ionizable_mol_pct": "Ionizable lipid %",
        "receptor_cd117": "CD117 targeting",
        "chol_to_helper_ratio": "Chol:helper ratio",
        "cholesterol_mol_pct": "Cholesterol %",
        "dose_mg_per_kg": "Dose (mg/kg)",
        "assay_editing": "Editing assay",
        "il_molecular_weight": "Lipid molecular weight",
        "hl_dotap": "DOTAP helper",
        "helper_mol_pct": "Helper lipid %",
        "helper_is_cationic": "Cationic helper",
        "il_to_chol_ratio": "IL:chol ratio",
        "il_to_helper_ratio": "Ionizable/helper ratio",
        "peg_chain_numeric": "PEG chain length",
    }
    return [
        {
            "feature": label_map.get(row["feature"], row["feature"]),
            "shap": round(float(row["mean_abs_shap"]), 2),
            "type": row["type"],
        }
        for row in ranking[:10]
    ]


def _shap_context(ranking: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Build context cards from the same SHAP artifact used by the chart."""
    by_feature = {row["feature"]: row for row in ranking}
    context_features = {
        "il": "ionizable_mol_pct",
        "cd117": "receptor_cd117",
        "chol": "cholesterol_mol_pct",
        "dose": "dose_mg_per_kg",
        "il_mw": "il_molecular_weight",
        "dotap": "hl_dotap",
        "helper_pct": "helper_mol_pct",
    }
    result: dict[str, dict[str, Any]] = {}
    for key, feature in context_features.items():
        row = by_feature[feature]
        result[key] = {
            "rank": int(row["rank"]),
            "shap": round(float(row["mean_abs_shap"]), 2),
            "direction": (
                "Atlas-wide feature importance is descriptive; paper, assay, and repeated "
                "formulations can contribute to this rank."
            ),
        }
    return result


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
            subset = [
                f["bm_normalized_bc"]
                for f in bm_forms
                if f.get("helper_lipid_name") == hl and f.get("peg_lipid_name") == peg
            ]
            if subset:
                interaction.append(
                    {
                        "helper": hl,
                        "peg": peg,
                        "n": len(subset),
                        "bm_mean": round(np.mean(subset), 1),
                    }
                )

    # Headgroup data
    headgroup_data = []
    for hl in helpers:
        subset = [f for f in bm_forms if f.get("helper_lipid_name") == hl]
        bm_vals = [f["bm_normalized_bc"] for f in subset]
        liver_vals = [
            f["liver_ec_normalized_bc"]
            for f in subset
            if f.get("liver_ec_normalized_bc") is not None
        ]
        headgroup_data.append(
            {
                "helper": hl,
                "n": len(subset),
                "bm_mean": round(np.mean(bm_vals), 2),
                "bm_std": round(float(np.std(bm_vals)), 2),
                "bm_median": round(float(np.median(bm_vals)), 2),
                "bm_max": max(bm_vals),
                "liver_mean": round(np.mean(liver_vals), 2) if liver_vals else None,
                "bm_liver_ratio": round(np.mean(bm_vals) / np.mean(liver_vals), 2)
                if liver_vals and np.mean(liver_vals) > 0
                else None,
                "bm_values": sorted(bm_vals, reverse=True),
            }
        )

    # PEG comparison (DOTAP only)
    peg_comp = []
    for peg in pegs:
        subset = [
            f
            for f in bm_forms
            if f.get("helper_lipid_name") == "DOTAP" and f.get("peg_lipid_name") == peg
        ]
        if not subset:
            continue
        bm_vals = [f["bm_normalized_bc"] for f in subset]
        peg_comp.append(
            {
                "peg": peg,
                "helper": "DOTAP",
                "n": len(subset),
                "bm_mean": round(np.mean(bm_vals), 2),
                "bm_max": max(bm_vals),
                "formulations": [
                    {
                        "id": f["lnp_name"],
                        "bm": f["bm_normalized_bc"],
                        "il_pct": f.get("ionizable_mol_percent"),
                        "helper_pct": f.get("helper_mol_percent"),
                    }
                    for f in subset
                ],
            }
        )

    # Mann-Whitney
    dotap_bm = [f["bm_normalized_bc"] for f in bm_forms if f.get("helper_lipid_name") == "DOTAP"]
    ddab_bm = [f["bm_normalized_bc"] for f in bm_forms if f.get("helper_lipid_name") == "DDAB"]
    stat, pval = mannwhitneyu(dotap_bm, ddab_bm, alternative="two-sided")
    stats = {
        "mann_whitney_U": float(stat),
        "p_value": round(pval, 4),
        "dotap_mean": round(np.mean(dotap_bm), 2),
        "ddab_mean": round(np.mean(ddab_bm), 2),
        "fold_change": round(np.mean(dotap_bm) / np.mean(ddab_bm), 1),
    }

    return peg_comp, interaction, headgroup_data, stats


def _lian_data() -> tuple[list[str], list[dict]]:
    """Extract Lian heatmap data."""
    with open(_LIAN_PATH) as f:
        lian = json.load(f)
    cell_types = [
        "LT_HSC",
        "LSK",
        "LMPP",
        "MPP",
        "CMP",
        "GMP",
        "MEP",
        "B",
        "T_total",
        "T_CD4",
        "T_CD8",
        "macrophage",
        "monocyte",
        "neutrophil",
    ]
    formulations = lian["formulations_screen"]["formulations"]
    heatmap = []
    for form in formulations:
        fid = form["id"].replace("Lian_", "")
        delivery = form.get("bm_delivery_screen_n1") or form.get("bm_delivery")
        if not delivery:
            continue
        validated = form.get("bm_delivery_validated_n3") is not None
        entry = {
            "id": fid,
            "validated": validated,
            "cell_types": {ct: delivery.get(ct, 0) for ct in cell_types},
        }
        if validated:
            entry["validated_cell_types"] = {
                ct: form["bm_delivery_validated_n3"].get(ct, 0) for ct in cell_types
            }
        heatmap.append(entry)
    heatmap.sort(key=lambda x: -x["cell_types"]["LT_HSC"])
    return cell_types, heatmap


def _lopocv_data() -> list[dict[str, Any]]:
    """Load the atlas leave-one-paper-out folds."""
    if _LOPOCV_PATH.exists():
        with open(_LOPOCV_PATH) as f:
            report = json.load(f)
        return [
            {
                "paper": ", ".join(fold["test_paper"]),
                "n": sum(sum(row) for row in fold["confusion_matrix"]),
                "lgbm": round(float(fold["balanced_accuracy"]), 3),
            }
            for fold in report["folds"]
        ]
    return []


def _paper_label(paper_id: str) -> str:
    """Format a stable source identifier for display."""
    overrides = {
        "shi_2025_thesis": "Shi thesis 2025",
        "tarab_ravski_2023": "Tarab-Ravski 2023",
    }
    if paper_id in overrides:
        return overrides[paper_id]
    return " ".join(part.upper() if part == "hsc" else part.title() for part in paper_id.split("_"))


def _number(value: object) -> float | None:
    """Return a JSON-safe number or null."""
    return None if pd.isna(value) else float(value)


def _helper_name(row: pd.Series, record: dict[str, Any] | None) -> str:
    if record:
        helper = (record.get("composition") or {}).get("helper_lipid")
        if helper:
            return str(helper)
    for column, label in (
        ("hl_dspc", "DSPC"),
        ("hl_dope", "DOPE"),
        ("hl_dotap", "DOTAP"),
        ("hl_ddab", "DDAB"),
        ("hl_dotma", "DOTMA"),
        ("hl_epc", "EPC"),
    ):
        if row[column] == 1:
            return label
    return "N/R"


def _targeting_name(row: pd.Series, record: dict[str, Any] | None) -> str:
    if record:
        receptor = str((record.get("targeting") or {}).get("target_receptor") or "")
        if receptor.lower() not in {"", "none", "null"}:
            return receptor.upper()
    if row["receptor_cd117"] == 1:
        return "CD117"
    if row["receptor_cd45"] == 1:
        return "CD45"
    if row["targeting_encoded"] == 2:
        return "Active"
    if row["targeting_encoded"] == 1:
        return "Intrinsic"
    return "None"


def _record_type(record: dict[str, Any] | None) -> str:
    if record is None:
        return "detailed"
    status = record.get("status")
    if status == "extracted_abstract_only":
        return "abstract-only"
    experiment = str(record.get("experiment_id") or "").lower()
    if "screen" in experiment or "library" in experiment:
        return "screen"
    return "detailed"


def _formulations(
    df: pd.DataFrame,
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Project all 331 matrix rows into the established explorer schema."""
    record_index = {
        (
            record["source_paper"],
            record["formulation_id"],
            record["experiment_id"],
            record["assay_category"],
        ): record
        for record in records
    }
    labels = {0.0: "low", 1.0: "medium", 2.0: "high"}
    rows: list[dict[str, Any]] = []
    for index, row in df.iterrows():
        record = None
        if index >= _CURATED_ROWS:
            key = (
                row["paper"],
                row["formulation_id"],
                row["experiment_id"],
                row["assay_category"],
            )
            record = record_index.get(key)
            if record is None:
                raise ValueError(f"matrix row has no matching rich record: {key}")
        target = _number(row["target"])
        rows.append(
            {
                "p": _paper_label(str(row["paper"])),
                "paperId": str(row["paper"]),
                "id": str(row["formulation_id"]),
                "experiment": str(row["experiment_id"]),
                "il": _number(row["ionizable_mol_pct"]),
                "hl": _helper_name(row, record),
                "hlPct": _number(row["helper_mol_pct"]),
                "chol": _number(row["cholesterol_mol_pct"]),
                "peg": _number(row["peg_mol_pct"]),
                "dose": _number(row["dose_mg_per_kg"]),
                "tgt": _targeting_name(row, record),
                "mt": str(row["assay_category"]),
                "cv": _number(row["covalent_lipid_mol_pct"]),
                "cls": labels.get(target),
                "boundary": bool(row["label_boundary_case"]),
                "recordType": _record_type(record),
                "status": str(record.get("status")) if record else "curated",
                "confidence": str(row["composition_confidence"]),
            }
        )
    return rows


def _paper_metadata() -> dict[str, dict[str, Any]]:
    metadata: dict[str, dict[str, Any]] = {}
    for paper_id, path in _LEGACY_ANNOTATIONS.items():
        document = json.loads(path.read_text())
        metadata[paper_id] = document.get("paper_metadata") or document.get("paper") or {}
    document = json.loads(_LITERATURE_ANNOTATIONS_PATH.read_text())
    for paper in document["papers"]:
        metadata[paper["paper_id"]] = paper.get("paper_metadata") or {}
    return metadata


def _paper_url(metadata: dict[str, Any]) -> str | None:
    url = metadata.get("url")
    if url:
        return str(url)
    doi = metadata.get("doi") or metadata.get("doi_or_id")
    if doi and str(doi).startswith("10."):
        return f"https://doi.org/{doi}"
    pmcid = metadata.get("pmcid")
    if pmcid and str(pmcid).startswith("PMC"):
        return f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/"
    pmid = metadata.get("pmid")
    if pmid:
        return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
    return None


def _papers(
    df: pd.DataFrame,
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    metadata = _paper_metadata()
    statuses: dict[str, set[str]] = {}
    for record in records:
        statuses.setdefault(record["source_paper"], set()).add(record["status"])
    papers = []
    for paper_id in df["paper"].drop_duplicates():
        paper_meta = metadata[str(paper_id)]
        papers.append(
            {
                "id": _paper_label(str(paper_id)),
                "paperId": str(paper_id),
                "journal": str(
                    paper_meta.get("journal")
                    or paper_meta.get("institution")
                    or paper_meta.get("paper_type")
                    or "N/R"
                ),
                "title": str(paper_meta.get("title") or paper_id),
                "role": "Atlas source",
                "records": int(df["paper"].eq(paper_id).sum()),
                "status": ", ".join(sorted(statuses.get(str(paper_id), {"curated"}))),
                "paperType": str(paper_meta.get("paper_type") or "N/R"),
                "url": _paper_url(paper_meta),
            }
        )
    return papers


def _coverage_stats(
    df: pd.DataFrame,
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    def block(label: str, filled: int, total: int, note: str) -> dict[str, Any]:
        return {
            "label": label,
            "filled": filled,
            "total": total,
            "percent": round(filled / total * 100, 1),
            "note": note,
        }

    detailed_toxicity = sum(
        isinstance(record.get("toxicity"), dict)
        and any(
            key != "reported" and value not in (None, "", [], {})
            for key, value in record["toxicity"].items()
        )
        for record in records
    )
    core_composition = int(
        df[["ionizable_mol_pct", "helper_mol_pct", "cholesterol_mol_pct"]].notna().all(axis=1).sum()
    )
    return {
        "completeColumns": int(sum(df[column].notna().all() for column in df.columns)),
        "totalColumns": len(df.columns),
        "reportPath": "docs/COVERAGE_REPORT.md",
        "blocks": [
            block(
                "Efficacy label",
                int(df["target"].notna().sum()),
                len(df),
                f"{int(df['target'].isna().sum())} unlabeled",
            ),
            block("Core composition", core_composition, len(df), "IL, helper, cholesterol"),
            block("Dose", int(df["dose_mg_per_kg"].notna().sum()), len(df), "mg/kg only"),
            block(
                "IL descriptors",
                int(df["il_molecular_weight"].notna().sum()),
                len(df),
                "8 descriptor columns",
            ),
            block(
                "Detailed toxicity",
                detailed_toxicity,
                len(records),
                "normalized rich records",
            ),
        ],
    }


def _target_distribution(frame: pd.DataFrame) -> dict[str, Any]:
    counts = frame["target"].value_counts()
    labeled = int(frame["target"].notna().sum())
    low = int(counts.get(0.0, 0))
    return {
        "rows": len(frame),
        "labeled": labeled,
        "low": low,
        "medium": int(counts.get(1.0, 0)),
        "high": int(counts.get(2.0, 0)),
        "unlabeled": int(frame["target"].isna().sum()),
        "lowShare": round(low / labeled * 100, 1),
    }


def _label_distribution(df: pd.DataFrame) -> dict[str, Any]:
    return _target_distribution(df)


def _source_summary(df: pd.DataFrame, records: list[dict[str, Any]]) -> dict[str, Any]:
    type_counts = Counter(_record_type(record) for record in records)
    type_counts["detailed"] += _CURATED_ROWS
    return {
        "sources": [
            {
                "id": str(paper_id),
                "label": _paper_label(str(paper_id)),
                "rows": int(count),
            }
            for paper_id, count in df["paper"].value_counts().items()
        ],
        "recordTypes": {key: int(value) for key, value in sorted(type_counts.items())},
    }


def _validation_summary() -> dict[str, Any]:
    report = json.loads(_VALIDATION_PATH.read_text())

    def summary(key: str) -> dict[str, Any]:
        result = report[key]
        overlaps = [fold["formulation_overlap_count"] for fold in result["folds"]]
        return {
            "balancedAccuracy": round(float(result["balanced_accuracy_mean"]), 4),
            "balancedAccuracyStd": round(float(result["balanced_accuracy_std"]), 4),
            "macroF1": round(float(result["macro_f1_mean"]), 4),
            "formulationDisjoint": bool(result["all_folds_formulation_disjoint"]),
            "overlapRange": [min(overlaps), max(overlaps)],
        }

    return {
        "evaluatedRows": int(report["dataset"]["evaluated_rows"]),
        "formulationTokens": int(report["dataset"]["formulation_tokens"]),
        "rowRandom": summary("row_random_5fold"),
        "formulationGrouped": summary("formulation_grouped_5fold"),
        "leaveOnePaperOut": {
            "balancedAccuracy": round(
                float(report["leave_one_paper_out"]["balanced_accuracy_mean"]), 4
            ),
            "folds": int(report["leave_one_paper_out"]["n_folds"]),
        },
    }


def _stats(df: pd.DataFrame) -> dict[str, int]:
    """Compute explorer header stats."""
    return {
        "rows": len(df),
        "sources": int(df["paper"].nunique()),
        "columns": len(df.columns),
        "labeled": int(df["target"].notna().sum()),
        "modelFeatures": 37,
        "descriptorRows": int(df["il_molecular_weight"].notna().sum()),
    }


def _findings(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    """Explain the meaning of observed comparisons; keep numbers in supporting evidence."""
    findings = []
    paired = next(
        (
            g
            for g in analysis["pareto"]
            if g["paperId"] == "kim_2024" and g["unit"] == "%"
        ),
        None,
    )
    if paired:
        frontier = [p for p in paired["points"] if p["frontier"]]
        most_marrow = max(frontier, key=lambda p: p["bm"])
        least_liver = min(frontier, key=lambda p: p["liver"])
        if most_marrow["bm"] > least_liver["bm"] and most_marrow["liver"] > least_liver["liver"]:
            comparison = (
                "In Kim's mouse study, the recipe with the strongest marrow response "
                "also produced a sizeable response in liver cells. Another recipe "
                "had a lower marrow response, but much less activity in the liver."
            )
            if least_liver["bm"] > 0 and least_liver["liver"] > 0:
                comparison = (
                    "Kim's mouse study counted cells making a protein after RNA delivery. "
                    "One recipe had about "
                    f"{most_marrow['bm'] / least_liver['bm']:.1f} times the marrow response "
                    "of another leading recipe, alongside "
                    f"{most_marrow['liver'] / least_liver['liver']:.0f} times the liver response."
                )
            findings.append(
                {
                    "id": "marrow-and-liver",
                    "title": "More marrow activity can mean more liver activity",
                    "text": comparison,
                    "meaning": (
                        "Choosing a recipe means weighing both results. The highest marrow "
                        "number alone does not tell you how well delivery stays in the cells "
                        "you want to reach."
                    ),
                    "evidence": [
                        f"{most_marrow['name']}: {most_marrow['bm']:.1f}% of the tested "
                        f"marrow cells and {most_marrow['liver']:.1f}% of the tested liver "
                        f"cells produced the marker protein. {least_liver['name']}: "
                        f"{least_liver['bm']:.1f}% and {least_liver['liver']:.1f}%, respectively.",
                        "Both were measured in the same mouse experiment at "
                        f"{most_marrow['dose']:g} mg/kg. The test counted early blood cells "
                        "in marrow and cells lining blood vessels in the liver. These are "
                        "percentages of cells, not percentages of the injected dose; a liver "
                        "response is not itself evidence of liver damage.",
                    ],
                    "sources": ["kim_2024"],
                }
            )

    hofstraat = next(
        (
            g
            for g in analysis["helper"]
            if g["paperId"] == "hofstraat_2025"
            and g["measurement"] == "LAMP1 reduction in LT-HSCs"
        ),
        None,
    )
    if hofstraat:
        values = [p["value"] for p in hofstraat["points"]]
        strongest = max(hofstraat["points"], key=lambda p: p["value"])
        findings.append(
            {
                "id": "rna-at-work",
                "title": "RNA can work inside blood stem cells",
                "text": (
                    "Hofstraat's mouse experiments delivered RNA designed to lower a "
                    "specific protein in blood stem cells. The strongest result was a "
                    f"reduction of about {max(values):.0f}% after four injections."
                ),
                "meaning": (
                    "Reaching a cell is only the first step. Measuring the intended protein "
                    "change checks whether the RNA did its job inside the cell. That is "
                    "useful evidence of delivery, although it does not establish a "
                    "treatment benefit."
                ),
                "evidence": [
                    f"Across {len(values)} records, the measured reduction in a protein "
                    f"called LAMP1 ranged from {min(values):.1f}% to {max(values):.1f}% "
                    "in long-term blood stem cells (LT-HSCs). These values compare the "
                    "protein signal with a matched control; they do not mean that this "
                    "percentage of cells was edited.",
                    f"The highest result was {strongest['name']}. Dosing: "
                    f"{strongest['schedule']}. Source: Figure 3 and its underlying data.",
                ],
                "sources": ["hofstraat_2025"],
            }
        )

    kim = next(
        (
            g
            for g in analysis["helper"]
            if g["paperId"] == "kim_2024" and g["unit"] == "barcode counts"
        ),
        None,
    )
    if kim:
        pegs: dict[str, list[float]] = {}
        for point in kim["points"]:
            if point["helper"] == "DOTAP" and point.get("peg"):
                pegs.setdefault(point["peg"], []).append(point["value"])
        if len(pegs) > 1:
            ranked = sorted(
                ((float(np.mean(values)), name, len(values)) for name, values in pegs.items()),
                reverse=True,
            )
            high, low = ranked[0], ranked[-1]
            findings.append(
                {
                    "id": "coating-comparison",
                    "title": "The outer coating is worth a closer look",
                    "text": (
                        "In Kim's mouse screen, recipes with different particle coatings "
                        "gave very different marrow signals. Several ingredients varied "
                        "together, so the data cannot tell us whether changing the coating "
                        "alone would improve delivery."
                    ),
                    "meaning": (
                        "This gives a useful starting point for the next comparison: "
                        "change the coating while keeping the rest of the recipe and the "
                        "dose the same. The current averages are a clue to investigate."
                    ),
                    "evidence": [
                        "PEG is part of the particle's outer coating. Among the recipes "
                        "using the same helper ingredient, DOTAP, "
                        f"{high[1]} had the highest mean marrow tracking signal "
                        f"({high[0]:.2f}; {high[2]} records), compared with {low[0]:.2f} "
                        f"for {low[1]} ({low[2]} records).",
                        "The signal comes from DNA tags used to track the particles "
                        "(normalized barcode counts). It measures a different outcome "
                        "from gene editing or protein reduction. These small groups do "
                        "not establish that one coating is better in other recipes.",
                    ],
                    "sources": ["kim_2024"],
                }
            )
    coverage = analysis["coverage"]
    liver_context = (
        "Those matching liver numbers are still missing from the newer records."
        if coverage["newPairs"] == 0
        else f"Currently, {coverage['newPairs']} of the {coverage['literatureRecords']} newer "
        "records contain those matching numbers."
    )
    findings.append(
        {
            "id": "comparing-studies",
            "title": "More records do not yet give us a clear winner",
            "text": (
                "The newer records mix different tests: some measure gene changes, "
                "others a protein decrease or light produced in marrow. A bigger score "
                "in one test does not mean a recipe would perform better in another."
            ),
            "meaning": (
                "Start with the test that matches your goal. To also judge how well "
                "delivery avoids the liver, we need marrow and liver measurements from "
                "the same experiment. " + liver_context
            ),
            "evidence": [
                "Xu 2026 measures gene editing; Hofstraat 2025 measures a reduction in "
                "a chosen protein; Hanafy 2025 measures light from a protein made after "
                "RNA delivery. These results describe different steps and cannot be "
                "combined into a single performance score.",
                f"Of {coverage['literatureRecords']} added literature records, "
                f"{coverage['newPairs']} currently have both numeric marrow and liver "
                "percentages from the same experiment. This is a gap in the collected "
                "records, not a claim that the original studies never measured the liver.",
            ],
            "sources": ["xu_2026", "hofstraat_2025", "hanafy_2025"],
        }
    )
    return findings


def build_data() -> dict[str, Any]:
    """Build every generated explorer data block."""
    df = pd.read_parquet(_FEAT_PATH)
    records = json.loads(_LITERATURE_RECORDS_PATH.read_text())["records"]
    if df.empty or df.shape[1] != 48:
        raise ValueError(f"expected a non-empty 48-column feature table, observed {df.shape}")

    analysis = build_analysis(_ROOT, df, records)
    ranking = _shap_ranking()
    peg_comp, interaction, headgroup, headgroup_stats = _kim_screen_analysis()
    cell_types, lian_formulations = _lian_data()
    coverage = _coverage_stats(df, records)
    labels = _label_distribution(df)
    validation = _validation_summary()
    stats = _stats(df)

    return {
        "paretoData": [point for group in analysis["pareto"] for point in group["points"]],
        "analysisData": analysis,
        "shapData": _shap_data(ranking),
        "shapContext": _shap_context(ranking),
        "pegComparison": peg_comp,
        "helperPegInteraction": interaction,
        "headgroupData": headgroup,
        "headgroupStats": headgroup_stats,
        "doseResponse": [
            {
                "system": "Shi CD117/C18",
                "raw_points": [
                    {"dose": 0.3, "response": 75},
                    {"dose": 1.0, "response": 90},
                ],
                "ec30": 0.036,
                "ec50": 0.090,
                "species": "Mouse",
                "platform": "tLNP",
            },
            {
                "system": "Breda CD117",
                "raw_points": [
                    {"dose": 0.05, "response": 10},
                    {"dose": 0.25, "response": 55},
                ],
                "ec30": 0.124,
                "ec50": 0.218,
                "species": "Mouse",
                "platform": "tLNP",
            },
            {
                "system": "Kim LNP67 (mouse)",
                "raw_points": [
                    {"dose": 0.5, "response": 12},
                    {"dose": 1.0, "response": 23},
                    {"dose": 2.0, "response": 35},
                ],
                "ec30": 1.548,
                "ec50": 3.77,
                "species": "Mouse",
                "platform": "LNP",
            },
            {
                "system": "Lian AA11",
                "raw_points": [{"dose": 0.6, "response": 5.2}],
                "ec30": None,
                "species": "Mouse",
                "platform": "LNP",
                "note": "Single dose, Cas9 BCL11A editing",
            },
        ],
        "lianCellTypes": cell_types,
        "lianFormulations": lian_formulations,
        "lopocvFolds": _lopocv_data(),
        "formulations": _formulations(df, records),
        "papers": _papers(df, records),
        "coverageStats": coverage,
        "labelDistribution": labels,
        "sourceSummary": _source_summary(df, records),
        "validationSummary": validation,
        "findings": _findings(analysis),
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
        "stats": stats,
    }


def main() -> int:
    """Extract all explorer data."""
    print("Extracting explorer data...")
    data = build_data()
    with open(_OUT_PATH, "w") as f:
        json.dump(data, f, indent=2, default=str)
        f.write("\n")

    print(f"Saved: {_OUT_PATH}")
    print(f"Stats: {data['stats']}")
    print(f"Pareto points: {len(data['paretoData'])}")
    print(f"SHAP features: {len(data['shapData'])}")
    print(f"Records: {len(data['formulations'])}")
    print(f"Sources: {len(data['papers'])}")
    print(f"Lian formulations: {len(data['lianFormulations'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
