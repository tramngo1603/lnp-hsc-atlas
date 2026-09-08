# Data

## `features/`

The canonical feature matrix. `hsc_features.parquet` and `hsc_features.csv` contain 333 formulation-experiment rows across 19 papers and 48 columns. The `target` column is populated for 315 rows.

`label_boundary_case` is labeling metadata, not a predictor. It is 1 for four `lian_2024` rows measured at exactly 30% that retain their established `high` labels, and 0 otherwise. The current convention is strictly `high >30%`, `medium 10-30%`, and `low <10%`. Threshold-sensitive training and evaluation exclude rows where the marker is 1.

## `hsc/`

The established curated source table. `hsc_curated.parquet` contains 131 rich records used to build the feature matrix.

## `literature_records.json`

Rich flat-schema records from the literature sources, plus 3 paywalled source stubs. This file retains provenance, source confidence, physicochemical measurements, toxicity observations, and open-action status that do not all fit into the fixed feature matrix.

## `kim_screen/`

Decoded Kim 2024 barcoded screen data. `kim_2024_screen_corrected.json` contains 128 LNP formulations with helper lipid, PEG lipid, and molar-ratio assignments. Sixty-six have bone-marrow barcode delivery data.

## `audit/`

Validation outputs and post-hoc claim checks. `literature_records_audit.json` records the source audit. `consolidated_audit.json` records dedupe decisions, contradiction checks, data-integrity invariants, and unresolved items. `AUDIT_REPORT.md` and its supporting scripts document related analyses.

## `models/`

Analysis outputs and serialized models. `atlas_analysis.json` records the 333-row class balance, descriptive feature-target correlations, and corrected Pareto analysis. `validation_comparison.json` reports row-random, formulation-grouped, and leave-one-paper-out LightGBM evaluation after excluding unlabeled and marked boundary rows. `lgbm_model.pkl`, `shap_values.parquet`, and `lopocv_results.json` use those same 311 threshold-comparable rows.

## `unified/`

Supporting training data that merges HSC records with external dataset features. It is not the canonical atlas matrix.

Coverage details for every feature-matrix column are in [`docs/COVERAGE_REPORT.md`](../docs/COVERAGE_REPORT.md). Label semantics are in [`docs/LABELING_CONVENTIONS.md`](../docs/LABELING_CONVENTIONS.md).
