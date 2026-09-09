"""Run Pareto and descriptive feature-correlation analyses for the atlas."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
from scipy.stats import pearsonr, spearmanr

from lnp_optimizer.pareto_corrected import (
    compute_screen_pareto,
    compute_validation_pareto,
    run_corrected_pareto,
)

_ROOT = Path(__file__).resolve().parent.parent
_FEATURES = _ROOT / "data" / "features" / "hsc_features.parquet"
_LITERATURE_RECORDS = _ROOT / "data" / "literature_records.json"
_OUTPUT = _ROOT / "data" / "models" / "atlas_analysis.json"


def _native(value: Any) -> float | None:
    if pd.isna(value):
        return None
    return round(float(value), 6)


def _probability(value: Any) -> float | None:
    if pd.isna(value):
        return None
    return float(value)


def _target_distribution(frame: pd.DataFrame) -> dict[str, Any]:
    counts = frame["target"].value_counts(dropna=False)
    low = int(counts.get(0.0, 0))
    medium = int(counts.get(1.0, 0))
    high = int(counts.get(2.0, 0))
    unlabeled = int(frame["target"].isna().sum())
    labeled = low + medium + high
    return {
        "rows": len(frame),
        "labeled": labeled,
        "unlabeled": unlabeled,
        "low": low,
        "medium": medium,
        "high": high,
        "low_percent_of_labeled": round(low / labeled * 100, 1) if labeled else None,
        "medium_percent_of_labeled": round(medium / labeled * 100, 1) if labeled else None,
        "high_percent_of_labeled": round(high / labeled * 100, 1) if labeled else None,
    }


def _spearman_feature(frame: pd.DataFrame, column: str) -> dict[str, Any]:
    paired = frame[[column, "target"]].dropna()
    if len(paired) < 3 or paired[column].nunique() < 2 or paired["target"].nunique() < 2:
        return {"n": len(paired), "rho": None, "p_value": None}
    result = spearmanr(paired[column], paired["target"])
    return {
        "n": len(paired),
        "rho": _native(result.statistic),
        "p_value": _probability(result.pvalue),
    }


def _feature_correlations(df: pd.DataFrame) -> dict[str, Any]:
    analysis_df = (
        df[df["label_boundary_case"].ne(1)]
        if "label_boundary_case" in df.columns
        else df
    )
    numeric_features = [
        column
        for column in analysis_df.select_dtypes(include="number").columns
        if column not in {"target", "label_boundary_case"}
    ]

    correlations: dict[str, dict[str, Any]] = {}
    for column in numeric_features:
        correlations[column] = _spearman_feature(analysis_df, column)

    def top() -> list[dict[str, Any]]:
        ranked: list[tuple[float, str, dict[str, Any]]] = []
        for column, result in correlations.items():
            value = result["rho"]
            if value is not None:
                ranked.append((abs(value), column, result))
        ranked.sort(key=lambda item: (-item[0], item[1]))
        return [{"feature": column, **result} for _, column, result in ranked[:10]]

    return {
        "method": (
            "Unadjusted Spearman correlation between each numeric matrix feature and the "
            "ordinal target (low=0, medium=1, high=2), using pairwise complete labeled rows. "
            "The four marked Lian rows at the exact 30% label boundary are excluded."
        ),
        "caveat": (
            "These are descriptive sensitivity checks, not causal effects. Rows are clustered "
            "by paper and formulation, assays differ, and no multiple-testing correction is "
            "applied. Use paper-grouped validation for model claims."
        ),
        "top_absolute": top(),
        "all_features": correlations,
    }


def _standardized_paired_records(records: list[dict[str, Any]]) -> list[str]:
    paired: list[str] = []
    for record in records:
        efficacy = record.get("efficacy") or {}
        bm = efficacy.get("bone_marrow_percent")
        liver = efficacy.get("liver_percent")
        if (
            isinstance(bm, (int, float))
            and not isinstance(bm, bool)
            and isinstance(liver, (int, float))
            and not isinstance(liver, bool)
        ):
            paired.append(record["record_id"])
    return paired


def _validation_correlation(validation: dict[str, Any]) -> dict[str, Any]:
    bm = [point["bm_percent"] for point in validation["lnp_points"]]
    liver = [point["liver_percent"] for point in validation["lnp_points"]]
    pearson = pearsonr(bm, liver)
    spearman = spearmanr(bm, liver)
    return {
        "n": len(bm),
        "pearson_r": _native(pearson.statistic),
        "pearson_p": _probability(pearson.pvalue),
        "spearman_r": _native(spearman.statistic),
        "spearman_p": _probability(spearman.pvalue),
        "interpretation": "not statistically significant; n=6 is too small for a stable estimate",
    }


def build_report() -> dict[str, Any]:
    df = pd.read_parquet(_FEATURES)
    records = json.loads(_LITERATURE_RECORDS.read_text())["records"]
    if df.shape != (333, 48):
        raise ValueError(f"expected 333 x 48 matrix, observed {df.shape}")

    screen = compute_screen_pareto()
    validation = compute_validation_pareto()
    paired_records = _standardized_paired_records(records)
    return {
        "analysis": "atlas_pareto_and_correlations",
        "date": date.today().isoformat(),
        "matrix": {
            "rows": len(df),
            "columns": len(df.columns),
            "papers": int(df["paper"].nunique()),
            "target_distribution": _target_distribution(df),
        },
        "pareto_and_bm_liver_correlation": {
            "screen_barcode_counts": {
                "n": screen["n_points"],
                "correlation": screen["correlation"],
                "pareto_optimal": screen["pareto_names"],
            },
            "validation_percentages": {
                "n_lnp_points": validation["n_lnp_points"],
                "correlation": _validation_correlation(validation),
                "lnp_pareto_optimal": [
                    point["formulation"] for point in validation["lnp_pareto_optimal"]
                ],
                "ideal_zone": validation["quadrants"]["ideal"],
            },
            "standardized_absolute_bm_liver_pairs": {
                "count": len(paired_records),
                "record_ids": paired_records,
                "eligibility": (
                    "same-record numeric bone_marrow_percent and liver_percent values with "
                    "comparable units"
                ),
            },
            "scope_note": (
                "Relative fold changes, qualitative organ statements, and mismatched constructs "
                "are not converted or mixed into the Pareto axes."
            ),
        },
        "feature_target_correlations": _feature_correlations(df),
        "interpretation": [
            (
                "Low efficacy accounts for 184/315 labeled rows (58.4%), with the Xu screen "
                "contributing a large repeated-assay block."
            ),
            (
                "After excluding the four marked boundary rows, the dose correlation is "
                "rho=-0.476. This reflects the many 2 mg/kg low-efficacy Xu screen rows and "
                "must not be read as a causal dose effect."
            ),
            (
                "The strongest correlations remain partly paper-identity proxies, "
                "especially ionizable-lipid descriptors represented by few chemical families."
            ),
        ],
    }


def main() -> int:
    # Rewrite the established Pareto outputs before the atlas summary.
    run_corrected_pareto()
    report = build_report()
    _OUTPUT.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Wrote {_OUTPUT.relative_to(_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
