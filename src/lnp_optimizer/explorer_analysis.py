"""Source-linked explorer measurements, rebuilt from the current atlas inputs.

Keep studies and measurement scales separate. Never infer liver percentages from
ratios, prose, another construct, or a different experiment.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd


def number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) else None


def source_label(value: str) -> str:
    return {"shi_2025_thesis": "Shi thesis 2025", "tarab_ravski_2023": "Tarab-Ravski 2023"}.get(
        value, value.replace("_", " ").title()
    )


def _short_lipid(value: Any) -> str | None:
    if not isinstance(value, str) or not value or value in {"N/R", "PEG-lipid"}:
        return None
    return value.split(" (")[0]


def _measurement(row: dict, value: Any, label: str, unit: str, **extra: Any) -> dict | None:
    value = number(value)
    if value is None or value < 0 or (unit == "%" and value > 100):
        return None
    return {**row, "value": value, "measurement": label, "unit": unit, **extra}


def literature_measurements(records: list[dict]) -> list[dict]:
    """Use explicit numeric endpoints, retaining target, regimen, and provenance."""
    measurements = []
    for record in records:
        delivery = record.get("delivery") or {}
        target = str(delivery.get("target_organ") or "").lower()
        if "bone_marrow" not in target or delivery.get("system") in {"in_vitro", "ex_vivo"}:
            continue
        efficacy = record.get("efficacy") or {}
        composition = record.get("composition") or {}
        base = {
            "id": record["record_id"],
            "name": record["formulation_id"],
            "paperId": record["source_paper"],
            "source": source_label(record["source_paper"]),
            "experiment": record["experiment_id"],
            "peg": _short_lipid(composition.get("peg_lipid")),
            "helper": _short_lipid(composition.get("helper_lipid")),
            "dose": number(delivery.get("dose_mg_per_kg")),
            "target": delivery.get("target_cell") or "Bone marrow",
            "species": delivery.get("species") or "Not reported",
            "route": delivery.get("route") or "Not reported",
            "schedule": delivery.get("dose_schedule") or delivery.get("regimen") or "",
            "detail": efficacy.get("metric") or "",
            "reference": "; ".join(p.get("cite", "") for p in record.get("provenance", [])),
            "estimated": record.get("extraction_method") == "digitized_from_figure",
        }
        endpoints = [
            ("editing_efficiency_percent", "Gene editing", "%"),
            ("hsc_transfection_percent", "Cell uptake", "%"),
            ("knockdown_percent_LT_HSC", "LAMP1 reduction in LT-HSCs", "%"),
            ("knockdown_percent", "Gene knockdown", "%"),
            ("bm_radiance_mean_estimated", "Estimated light signal", "p/s/cm²/sr"),
            ("bone_marrow_percent", "Bone marrow delivery", "%"),
        ]
        for field, label, unit in endpoints:
            metric = str(efficacy.get("metric") or "").lower()
            if field == "editing_efficiency_percent" and "tdtomato" in metric:
                label = "Cre reporter activation"
            if (
                field == "hsc_transfection_percent"
                and record.get("assay_category") == "protein_expression"
            ):
                label = "Protein expression"
            point = _measurement(base, efficacy.get(field), label, unit, field=field)
            if point:
                if field == "bm_radiance_mean_estimated":
                    point["estimated"] = True
                measurements.append(point)
                break  # One explicit endpoint per record; never double count a cell subset.
    return measurements


def _curated_measurements(root: Path, frame: pd.DataFrame) -> list[dict]:
    curated = pd.read_parquet(root / "data/hsc/hsc_curated.parquet")
    keys = set(zip(frame.paper, frame.formulation_id, frame.experiment_id, strict=True))
    annotations = {
        paper: json.loads((root / "annotations" / (paper + ".json")).read_text())
        for paper in ("breda_2023", "kim_2024", "shi_2023")
    }
    measurements = []
    for _, row in curated.iterrows():
        key = (row.paper, row.formulation_id, row.experiment_id)
        if key not in keys or str(row.route).lower() in {"in_vitro", "ex_vivo", ""}:
            continue
        if row.assay_category == "barcode_delivery":
            continue  # The corrected screen file owns barcode values and PEG identities.
        experiment_id = str(row.experiment_id)
        if any(
            term in experiment_id.lower() for term in ("in_vitro", "ex_vivo", "peripheral_blood")
        ) or experiment_id.endswith("_PBS"):
            continue
        experiment: dict[str, Any] = next(
            (
                e
                for e in annotations.get(row.paper, {}).get("experiments", [])
                if experiment_id.startswith(e.get("experiment_id", "!"))
            ),
            {},
        )
        model = experiment.get("model_system") or experiment.get("model") or {}
        if model.get("system", model.get("system_type")) in {"in_vitro", "ex_vivo"}:
            continue
        target = (
            row.hsc_definition or model.get("hspc_definition") or model.get("cell_type_or_organ")
        )
        if "_LT_HSC" in experiment_id:
            target = model.get("lthsc_definition") or "LT-HSCs"
        if not target:
            continue
        unit_text = str(row.expt_unit).lower()
        value = number(row.hsc_transfection_percent)
        if value is None:
            value = number(row.editing_efficiency_percent)
        if value is None or not ("%" in unit_text or unit_text == "percent"):
            continue
        if "dir" in unit_text:
            label = "Cell uptake"
        elif row.assay_category == "editing":
            label = "Cre reporter activation"
        else:
            label = "Protein expression"
        point = _measurement(
            {
                "id": ":".join(key),
                "name": row.formulation_id,
                "paperId": row.paper,
                "source": source_label(row.paper),
                "experiment": row.experiment_id,
                "peg": _short_lipid(row.peg_name),
                "helper": _short_lipid(row.hl_name),
                "dose": number(row.dose_mg_per_kg),
                "target": target,
                "species": row.animal_model,
                "route": row.route,
                "schedule": "",
                "detail": str(row.expt_unit),
                "reference": str(row.experiment_id),
                "estimated": True,
            },
            value,
            label,
            "%",
        )
        if point:
            measurements.append(point)
    return measurements


def _legacy_measurements(root: Path, frame: pd.DataFrame) -> tuple[list[dict], list[dict]]:
    observations = _curated_measurements(root, frame)
    paired = []
    kim = json.loads((root / "data/kim_screen/kim_2024_screen_corrected.json").read_text())
    ids = set(frame.loc[frame.paper.eq("kim_2024"), "formulation_id"])
    for row in kim["formulations"]:
        if row["lnp_name"] not in ids:
            continue
        base = {
            "id": f"kim_2024:screen:{row['lnp_name']}",
            "name": row["lnp_name"],
            "paperId": "kim_2024",
            "source": "Kim 2024",
            "experiment": "barcoded_screen",
            "peg": row.get("peg_lipid_name"),
            "helper": row.get("helper_lipid_name"),
            "dose": None,
            "target": "Bone marrow",
            "species": "Mouse",
            "route": "IV",
            "schedule": "",
            "detail": "Normalized barcode counts",
            "reference": "Supplementary Figure 6",
            "estimated": True,
        }
        point = _measurement(
            base, row.get("bm_normalized_bc"), "Barcode delivery", "barcode counts"
        )
        if point:
            observations.append(point)
            liver = number(row.get("liver_ec_normalized_bc"))
            if liver is not None and liver >= 0:
                paired.append({**point, "bm": point["value"], "liver": liver})

    document = json.loads((root / "annotations/kim_2024.json").read_text())
    for experiment in document["experiments"]:
        if experiment["experiment_id"] != "E2_individual_validation":
            continue
        for name in experiment["formulations_tested"]:
            results = experiment["efficacy"].get(name.lower() + "_results", {})
            bm = results.get(
                "bone_marrow_LSK_percent", results.get("bone_marrow_LSK_percent_avhh_positive")
            )
            liver = results.get("liver_EC_percent")
            if number(bm) is not None and number(liver) is not None:
                paired.append(
                    {
                        "id": f"kim_2024:E2:{name}",
                        "name": name,
                        "paperId": "kim_2024",
                        "source": "Kim 2024",
                        "experiment": "Individual validation",
                        "measurement": "Protein expression",
                        "unit": "%",
                        "bm": bm,
                        "liver": liver,
                        "value": bm,
                        "target": "LSK cells / liver endothelial cells",
                        "species": "Mouse",
                        "dose": experiment["dosing"]["dose_mg_per_kg"],
                        "reference": experiment["figure"],
                        "detail": "aVHH-positive cells",
                        "estimated": False,
                    }
                )

    breda = json.loads((root / "annotations/breda_2023.json").read_text())
    for experiment in breda["experiments"]:
        distribution = experiment.get("biodistribution") or {}
        if experiment.get("model", {}).get("system") != "in_vivo":
            continue
        bm, liver = (
            number(distribution.get("bone_marrow_percent")),
            number(distribution.get("liver_percent")),
        )
        if bm is not None and liver is not None and distribution.get("paired_hsc_and_liver_data"):
            paired.append(
                {
                    "id": "breda_2023:" + experiment["experiment_id"],
                    "name": experiment["formulation_name"],
                    "source": "Breda 2023",
                    "paperId": "breda_2023",
                    "experiment": experiment["experiment_id"],
                    "measurement": "Cre reporter activation",
                    "unit": "%",
                    "bm": bm,
                    "liver": liver,
                    "value": bm,
                    "target": "LT-HSCs / liver",
                    "species": "Mouse",
                    "dose": number(experiment.get("dosing", {}).get("dose_mg_per_kg")),
                    "reference": experiment["experiment_id"],
                    "detail": distribution.get("measurement_method", ""),
                    "estimated": False,
                }
            )

    lian = json.loads((root / "annotations/lian_2024.json").read_text())
    lian_forms = {f["id"]: f for f in lian["formulations_screen"]["formulations"]}
    for _, row in frame.loc[frame.paper.eq("lian_2024")].iterrows():
        form = lian_forms.get(row.formulation_id)
        if not form:
            continue
        if "validated" in row.experiment_id:
            delivery = form.get("bm_delivery_validated_n3") or {}
        else:
            delivery = form.get("bm_delivery_screen_n1") or form.get("bm_delivery") or {}
        point = _measurement(
            {
                "id": f"lian_2024:{row.experiment_id}",
                "name": row.formulation_id,
                "paperId": "lian_2024",
                "source": "Lian 2024",
                "experiment": row.experiment_id,
                "peg": lian["base_formulation"]["peg_lipid"],
                "helper": lian["base_formulation"]["helper_lipid"],
                "dose": number(row.dose_mg_per_kg),
                "target": "LT-HSCs",
                "species": "Mouse",
                "route": "IV",
                "schedule": "Single dose",
                "detail": "tdTomato-positive LT-HSCs",
                "reference": "BM delivery screen / validation",
                "estimated": True,
            },
            delivery.get("LT_HSC"),
            "Cre reporter activation",
            "%",
        )
        if point:
            observations.append(point)
    for experiment in lian["experiments"]:
        pair = experiment.get("pareto_point") or {}
        bm, liver = number(pair.get("bm_hspc_editing_pct")), number(pair.get("liver_editing_pct"))
        if bm is None or liver is None:
            continue
        paired.append(
            {
                "id": "lian_2024:" + experiment["id"],
                "name": experiment["formulation_ref"],
                "source": "Lian 2024",
                "paperId": "lian_2024",
                "experiment": experiment["id"],
                "measurement": "Base editing" if "ABE" in experiment["id"] else "Gene editing",
                "unit": "%",
                "bm": bm,
                "liver": liver,
                "value": bm,
                "target": "CD117+ bone marrow cells / liver",
                "species": "Mouse",
                "dose": number(experiment.get("dose_mg_per_kg")),
                "reference": experiment["figure_source"],
                "detail": experiment["payload"],
                "estimated": True,
            }
        )
        observations.append(
            {
                **paired[-1],
                "peg": lian["base_formulation"]["peg_lipid"],
                "helper": lian["base_formulation"]["helper_lipid"],
                "route": experiment["route"],
                "schedule": str(experiment["num_doses"])
                + " doses; "
                + experiment.get("dose_interval", ""),
            }
        )
    return observations, paired


def grouped(points: list[dict], *, paired: bool = False) -> list[dict]:
    buckets = defaultdict(list)
    for point in points:
        # Percentages from different cell populations are not interchangeable.
        key = (
            point["paperId"],
            point["measurement"],
            point["unit"],
            point["target"],
            point["species"],
        )
        buckets[key].append(point)
    output = []
    for key, rows in buckets.items():
        rows = sorted(rows, key=lambda r: r["id"])
        if paired:
            rows = [
                {
                    **r,
                    "frontier": not any(
                        s["bm"] >= r["bm"]
                        and s["liver"] <= r["liver"]
                        and (s["bm"] > r["bm"] or s["liver"] < r["liver"])
                        for s in rows
                    ),
                }
                for r in rows
            ]
        output.append(
            {
                "id": hashlib.sha256(json.dumps(key).encode()).hexdigest()[:12],
                "paperId": key[0],
                "source": rows[0]["source"],
                "measurement": key[1],
                "unit": key[2],
                "target": key[3],
                "species": key[4],
                "points": rows,
            }
        )
    return sorted(
        output,
        key=lambda g: (
            g["paperId"] != "kim_2024",
            g["unit"] != "%",
            g["source"],
            g["measurement"],
            g["target"],
        ),
    )


def build_analysis(root: Path, frame: pd.DataFrame, records: list[dict]) -> dict:
    observations, paired = _legacy_measurements(root, frame)
    new_observations = literature_measurements(records)
    observations.extend(new_observations)
    record_index = {r["record_id"]: r for r in records}
    new_pairs = []
    for observation in new_observations:
        efficacy = record_index[observation["id"]].get("efficacy") or {}
        bm = number(efficacy.get("bone_marrow_percent"))
        liver = number(efficacy.get("liver_percent"))
        # Standardized fields certify a same-record percentage pair. Never parse prose.
        if bm is not None and liver is not None and 0 <= bm <= 100 and 0 <= liver <= 100:
            new_pairs.append(
                {
                    **observation,
                    "measurement": "Bone marrow delivery",
                    "unit": "%",
                    "value": bm,
                    "bm": bm,
                    "liver": liver,
                }
            )
    paired.extend(new_pairs)
    return {
        "pareto": grouped(paired, paired=True),
        "peg": grouped([p for p in observations if p.get("peg")]),
        "helper": grouped([p for p in observations if p.get("helper")]),
        "dose": grouped(
            [p for p in observations if number(p.get("dose")) is not None and p["dose"] > 0]
        ),
        "coverage": {
            "rows": len(frame),
            "literatureRecords": len(records),
            "newPairs": len(new_pairs),
            "responseRecords": len(observations),
            "newResponseRecords": len(new_observations),
            "responseSources": len({p["paperId"] for p in observations}),
        },
    }
