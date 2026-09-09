"""Validate data/literature_records.json (198 flat records).

Applies the repo's existing validation semantics (scripts/validate_annotations.py,
docs/annotation_template.json vocabularies, label_for_ml thresholds) to the
flat per-record schema, plus the atlas unit rules:
sizes in nm, doses in mg/kg, percentages within 0-100.

Exit code 0 if no errors (warnings are non-blocking), mirroring
validate_annotations.py. Writes a machine-readable report to
data/audit/literature_records_audit.json.

Documented audit exceptions:
- Computed knockdown may be negative (formulation had no effect). Clamping
  to 0 would falsify low-efficacy records needed for label balance.
  Affected: hofstraat_2025_aNP72_invivo_siLAMP1 (LT-HSC -2.4%).
- Absolute per-mouse doses (Swart 50 ug, Zhao 10 ug) keep
  dose_mg_per_kg = null with reason; no assumed mouse weight is introduced.
- Hanafy record-level evidence_strength stays empirically_measured;
  field-level field_extraction_methods marks the BM radiance estimate.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_RECORDS = _ROOT / "data" / "literature_records.json"
_ANNOTATIONS = _ROOT / "annotations" / "new_paper_annotations.json"
_REPORT = _ROOT / "data" / "audit" / "literature_records_audit.json"
_XU_SRC = _ROOT / "data" / "audit" / "xu_2026_screen_replicates_source.json"

_XU_CACHE: dict | None = None


def _xu_source_arrays() -> dict:
    """Load Xu 2026 screen replicate arrays captured from source data
    (Extended Data Fig. 3/4/5 and Fig. 4a). Empty dict if unavailable."""
    global _XU_CACHE
    if _XU_CACHE is None:
        _XU_CACHE = json.loads(_XU_SRC.read_text()) if _XU_SRC.exists() else {}
    return _XU_CACHE

# --- vocabularies (docs/annotation_template.json + flat-record schema) ------

_REQUIRED_KEYS = [
    "record_id", "source_paper", "tier", "status", "formulation_id",
    "experiment_id", "assay_category", "payload", "composition",
    "delivery", "efficacy", "evidence_strength", "extraction_method",
    "provenance", "null_fields", "confidence",
]

_VALID_ASSAY = {"knockdown", "editing", "protein_expression",
                "barcode_delivery", "depletion"}
_VALID_PAYLOAD = {"mRNA", "siRNA", "sgRNA", "RNP", "base_editor",
                  "prime_editor", "Cre_mRNA", "DNA_barcode"}
_VALID_STRATEGY = {"antibody_conjugated", "intrinsic_tropism", "aptamer",
                   "peptide", "none", "other"}
_VALID_CONFIDENCE = {"HIGH", "MEDIUM", "LOW", "DISPROVEN"}
_VALID_EXTRACTION = {"extracted_from_table", "extracted_from_text",
                     "estimated_from_figure"}
_VALID_STATUS = {"extracted", "extracted_abstract_only",
                 "partial_pending_main_text"}
_VALID_EVIDENCE = {"empirically_measured", "estimated_from_figure",
                   "abstract_claim"}

# Percentage-like leaf keys that must sit in 0-100 when numeric.
_PCT_RE = re.compile(r"(mol_pct|percent|efficiency|knockdown|transfection)",
                     re.IGNORECASE)
# Keys exempt from the 0-100 rule (ratios, counts, radiance, fold-changes).
_PCT_EXEMPT = {"np_ratio", "protein_expression", "bm_radiance_mean_estimated"}

# Documented exception: computed negative knockdown (no-effect formulation).
# (aNP72 was corrected to +5.7% after source review; the exception policy
# remains in place as a rule for any future genuinely-negative computed value.)
_NEGATIVE_KD_EXCEPTION = {"hofstraat_2025_aNP72_invivo_siLAMP1"}

# label_for_ml thresholds (atlas convention; docs/annotation_template.json).
_LABEL_THRESHOLDS = {"high": (30.0, None), "medium": (10.0, 30.0),
                     "low": (None, 10.0)}

# Meta fields whose nulls do not require a null_fields reason.
_META_NULL_OK = {"confidence_notes", "needs_user_confirmation", "notes",
                 "label_for_ml"}


def _walk(o, path=""):
    """Yield (path, value) for every leaf."""
    if isinstance(o, dict):
        for k, v in o.items():
            yield from _walk(v, f"{path}.{k}" if path else k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _walk(v, f"{path}[{i}]")
    else:
        yield path, o


def _null_leaves(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from _null_leaves(v, f"{path}.{k}" if path else k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _null_leaves(v, f"{path}[{i}]")
    elif o is None:
        yield path


def _null_covered(path: str, null_fields: dict) -> bool:
    """A null leaf is covered if null_fields names it by leaf key,
    dotted path, or underscore-joined path."""
    leaf = path.split(".")[-1]
    us_path = path.replace(".", "_")
    return any(
        k in (leaf, us_path) or path.endswith(k) or us_path.endswith(k)
        for k in null_fields
    )


def _classify(value: float) -> str:
    if value > _LABEL_THRESHOLDS["high"][0]:
        return "high"
    if value >= _LABEL_THRESHOLDS["medium"][0]:
        return "medium"
    return "low"


def _primary_pct(efficacy: dict, assay: str):
    """Best-effort primary percentage metric for label consistency checks."""
    for key in ("editing_efficiency_percent", "knockdown_percent_LSK",
                    "knockdown_percent", "hsc_transfection_percent"):
        v = efficacy.get(key)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return key, v
    return None, None


def audit_record(r: dict) -> tuple[list[str], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    info: list[str] = []
    rid = r.get("record_id", "<no id>")

    # 1. schema completeness ------------------------------------------------
    for k in _REQUIRED_KEYS:
        if k not in r:
            errors.append(f"{rid}: missing required key '{k}'")

    # 2. record_id / source_paper agreement ---------------------------------
    sp = r.get("source_paper", "")
    if sp and not rid.startswith(sp):
        errors.append(f"{rid}: record_id does not start with source_paper '{sp}'")

    # 3. controlled vocabularies --------------------------------------------
    if r.get("assay_category") not in _VALID_ASSAY:
        errors.append(f"{rid}: unknown assay_category '{r.get('assay_category')}'")
    ptype = (r.get("payload") or {}).get("type")
    if ptype not in _VALID_PAYLOAD:
        errors.append(f"{rid}: unknown payload.type '{ptype}'")
    strat = (r.get("targeting") or {}).get("strategy")
    if strat not in _VALID_STRATEGY:
        errors.append(f"{rid}: unknown targeting.strategy '{strat}'")
    if r.get("confidence") not in _VALID_CONFIDENCE:
        errors.append(f"{rid}: unknown confidence '{r.get('confidence')}'")
    if r.get("extraction_method") not in _VALID_EXTRACTION:
        errors.append(f"{rid}: unknown extraction_method '{r.get('extraction_method')}'")
    if r.get("status") not in _VALID_STATUS:
        errors.append(f"{rid}: unknown status '{r.get('status')}'")
    if r.get("evidence_strength") not in _VALID_EVIDENCE:
        warnings.append(f"{rid}: unusual evidence_strength '{r.get('evidence_strength')}'")

    # 4. unit and range rules ------------------------------------------------
    for path, v in _walk(r):
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            continue
        leaf = path.split(".")[-1]
        if leaf in _PCT_EXEMPT or "replicates" in path:
            continue
        if _PCT_RE.search(leaf) and not (0.0 <= v <= 100.0):
            if rid in _NEGATIVE_KD_EXCEPTION and v < 0:
                warnings.append(
                    f"{rid}: {path} = {v} (documented exception: computed "
                    f"negative knockdown, no-effect formulation)")
            else:
                errors.append(f"{rid}: {path} = {v} outside 0-100")
        if leaf == "pdi" and not (0.0 <= v <= 1.0):
            errors.append(f"{rid}: pdi = {v} outside 0-1")
        if leaf == "dose_mg_per_kg" and v <= 0:
            errors.append(f"{rid}: dose_mg_per_kg = {v} not positive")
        if leaf.startswith("particle_size") and isinstance(v, (int, float)) and v <= 0:
            errors.append(f"{rid}: {path} = {v} not positive (nm)")

    # replicate outliers: reported but not auto-fixed (see validation flags)
    eff = r.get("efficacy") or {}
    reps = eff.get("replicates") or {}
    for arm, vals in reps.items():
        if isinstance(vals, list):
            for v in vals:
                if isinstance(v, (int, float)) and not (0.0 <= v <= 100.0):
                    warnings.append(
                        f"{rid}: replicate {arm} value {v} outside 0-100 "
                        f"(source-data anomaly; flagged, not altered)")

    # 4b. Xu screen replicate completeness (source review finding 2026-09-06):
    # compare stored replicate arrays against the source-data arrays embedded
    # in data/audit/xu_2026_screen_replicates_source.json. Incomplete = error;
    # complete = info (bar-vs-replicate-mean is a documented source property).
    if r.get("source_paper") == "xu_2026" and reps:
        src = _xu_source_arrays()
        m = re.search(r"LNP-(\d+)", r.get("formulation_id") or "")
        key = f"LNP-{m.group(1)}" if m else None
        key = key if key in src else None
        if key:
            src_sd = src[key]["single"]
            src_dd = src[key]["second"]
            sd_rec = reps.get("single_dose") or []
            dd_rec = reps.get("second_dose") or []
            if sorted(sd_rec) != sorted(src_sd) or sorted(dd_rec) != sorted(src_dd):
                errors.append(
                    f"{rid}: replicate array(s) incomplete vs source data "
                    f"(single {sd_rec} vs {src_sd}; second {dd_rec} vs {src_dd}; "
                    f"see flag xu_screen_replicates_missing_first_value)")
            else:
                info.append(
                    f"{rid}: replicates complete; bar-vs-replicate-mean deltas "
                    f"are a documented source-data property")

    # string sizes like "54 +/- 14" are documented ranges: informational
    phys = r.get("physicochemical") or {}
    for k, v in phys.items():
        if k.startswith("particle_size") and isinstance(v, str):
            info.append(f"{rid}: {k} is a string range '{v}' (nm, documented)")

    # 5. dose representation --------------------------------------------------
    dl = r.get("delivery") or {}
    if "dose_mg_per_kg" not in dl:
        errors.append(f"{rid}: delivery.dose_mg_per_kg key absent "
                      f"(must be explicit null with reason)")
    elif dl["dose_mg_per_kg"] is None:
        nf = r.get("null_fields") or {}
        if not _null_covered("delivery.dose_mg_per_kg", nf):
            errors.append(f"{rid}: dose_mg_per_kg null without null_fields reason")
        elif dl.get("dose_absolute"):
            info.append(f"{rid}: absolute dose kept ({dl['dose_absolute']}); "
                        f"mg/kg null per source review decision (no assumed weight)")

    # 6. null_reason completeness --------------------------------------------
    nf = r.get("null_fields") or {}
    for path in _null_leaves(r):
        leaf = path.split(".")[-1]
        if leaf in _META_NULL_OK:
            continue
        if not _null_covered(path, nf):
            errors.append(f"{rid}: null at {path} has no null_fields reason")

    # 7. mol% sum (validator semantics: 90-110 when >= 4 components) ----------
    comp = r.get("composition") or {}
    mol_keys = ["ionizable_mol_pct", "helper_mol_pct", "cholesterol_mol_pct",
                "peg_mol_pct"]
    vals = [comp[k] for k in mol_keys
            if isinstance(comp.get(k), (int, float))]
    other = comp.get("other_components") or {}
    if isinstance(other, dict):
        other_mol = [v for v in other.values()
                     if isinstance(v, (int, float)) and not isinstance(v, bool)]
    else:
        other_mol = []  # free-text description, no numeric mol%
    if len(vals) >= 4:
        total = sum(vals) + sum(other_mol)
        if not (90.0 <= total <= 110.0):
            warnings.append(f"{rid}: mol% sum = {total:.1f} (expected ~100)")

    # 8. assay-category vs efficacy-metric agreement --------------------------
    # A record is acceptable if its efficacy block carries any quantitative
    # readout (disease-burden metrics are documented as such in annotations).
    assay = r.get("assay_category")
    metric_txt = json.dumps(eff).lower()
    has_numeric_readout = any(
        isinstance(v, (int, float)) and not isinstance(v, bool)
        for _, v in _walk(eff))
    if assay == "editing" and not (
            "editing" in metric_txt or "edit" in str(eff.get("metric", "")).lower()):
        warnings.append(f"{rid}: assay editing but efficacy block has no editing metric")
    if assay == "knockdown" and "knockdown" not in metric_txt:
        if has_numeric_readout:
            info.append(f"{rid}: knockdown payload with disease-burden in vivo "
                        f"readout (documented in annotations label_for_ml)")
        else:
            warnings.append(f"{rid}: assay knockdown but no knockdown metric in efficacy")

    # 9. label_for_ml consistency --------------------------------------------
    label = r.get("label_for_ml")
    if label in ("high", "medium", "low"):
        key, val = _primary_pct(eff, assay)
        if val is not None:
            derived = _classify(val)
            # boundary note: classify uses high >30, medium 10-30, low <10
            if derived != label:
                errors.append(
                    f"{rid}: label_for_ml '{label}' inconsistent with {key}={val} "
                    f"(atlas thresholds -> '{derived}')")

    # 10. provenance -----------------------------------------------------------
    prov = r.get("provenance")
    if not isinstance(prov, list) or not prov:
        errors.append(f"{rid}: provenance missing or empty")
    else:
        for i, p in enumerate(prov):
            if not p.get("fields") or not p.get("cite"):
                errors.append(f"{rid}: provenance[{i}] lacks fields or cite")

    # 11. efficacy metric present ----------------------------------------------
    if not eff.get("metric"):
        warnings.append(f"{rid}: efficacy.metric missing")

    return errors, warnings, info


def main() -> int:
    records = json.loads(_RECORDS.read_text())["records"]
    annotations = json.loads(_ANNOTATIONS.read_text())

    total_errors: list[str] = []
    total_warnings: list[str] = []
    total_info: list[str] = []

    seen: set[str] = set()
    for r in records:
        rid = r.get("record_id", "<no id>")
        if rid in seen:
            total_errors.append(f"{rid}: duplicate record_id")
        seen.add(rid)
        errs, warns, info = audit_record(r)
        total_errors.extend(errs)
        total_warnings.extend(warns)
        total_info.extend(info)

    # cross-check: annotations record_ids <-> records file
    ann_ids = set()
    for p in annotations.get("papers", []):
        ann_ids.update(p.get("record_ids", []))
    rec_ids = {r["record_id"] for r in records}
    for missing in sorted(ann_ids - rec_ids):
        total_errors.append(f"annotations list {missing} but no such record")
    for orphan in sorted(rec_ids - ann_ids):
        total_warnings.append(f"{orphan}: not listed in new_paper_annotations.json")

    report = {
        "audit": "literature_records",
        "date": "2026-09-06",
        "records_audited": len(records),
        "errors": total_errors,
        "warnings": total_warnings,
        "info": total_info,
        "exceptions_documented": [
            "computed negative knockdown allowed (hofstraat aNP72 LT-HSC -2.4%)",
            "absolute per-mouse doses keep null mg/kg (swart_2023 x2, zhao_2026 x2)",
            "hanafy_2025 record-level evidence_strength unchanged (empirically_measured)",
        ],
    }
    _REPORT.write_text(json.dumps(report, indent=2) + "\n")

    print(f"Audited {len(records)} literature records")
    if total_info:
        print(f"\n{len(total_info)} info (documented, non-blocking):")
        for i in total_info:
            print(f"  {i}")
    if total_warnings:
        print(f"\n{len(total_warnings)} warnings:")
        for w in total_warnings:
            print(f"  {w}")
    if total_errors:
        print(f"\n{len(total_errors)} errors:")
        for e in total_errors:
            print(f"  {e}")
        return 1
    print("\nAll source review record audits passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
