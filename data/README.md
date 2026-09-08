# Data

## `features/`

The canonical machine-learning feature matrix. `hsc_features.parquet` and `hsc_features.csv` contain 333 formulation-experiment rows across 19 papers and 48 columns. The first 135 rows are the protected baseline and the following 198 rows are the Pass 1 expansion. The `target` column is populated for 315 rows.

`label_boundary_case` is labeling metadata, not a predictor. It is 1 for four protected `lian_2024` rows measured at exactly 30% that retain their v1 `high` labels, and 0 otherwise. The current convention for new rows is strictly `high >30%`, `medium 10-30%`, and `low <10%`. Threshold-sensitive training and evaluation exclude rows where the marker is 1.

## `hsc/`

The protected legacy source table. `hsc_curated.parquet` contains 131 rich records that project to 110 of the original feature rows. Together with 25 Lian integration rows, they form the original 135-row matrix block. Pass 3 does not modify this file.

## `new_records_pass1.json`

The rich flat-schema expansion: 198 records from 15 sources plus 3 paywalled source stubs. This file retains provenance, source confidence, physicochemical measurements, toxicity observations, and open-action status that do not all fit into the fixed feature matrix.

## `kim_screen/`

Decoded Kim 2024 barcoded screen data. `kim_2024_screen_corrected.json` contains 128 LNP formulations with helper lipid, PEG lipid, and molar-ratio assignments. Sixty-six have bone-marrow barcode delivery data.

## `audit/`

Validation outputs and post-hoc claim checks. `pass2_new_records_audit.json` records the 198-row source audit. `pass3_dedupe_report.json` records consolidation, dedupe decisions, contradiction checks, protected-baseline invariants, and unresolved items. The older `AUDIT_REPORT.md` and supporting scripts document baseline analyses.

## `models/`

Analysis outputs and serialized baseline models. `pass3_analysis.json` records the combined 333-row class balance, descriptive feature-target correlations, and the refreshed corrected Pareto analysis. `validation_comparison.json` reports row-random, formulation-grouped, and leave-one-paper-out LightGBM evaluation on the combined release, after excluding unlabeled and marked boundary rows. `lgbm_model.pkl`, `shap_values.parquet`, and `lopocv_results.json` use those same 311 threshold-comparable rows. Other legacy artifacts may describe earlier analysis stages and should not be assumed to use the combined release.

## `extractions/`

LLM-extracted paper data indexed by PMID and used to evaluate extraction accuracy against ground-truth annotations.

## `unified/`

Earlier combined training data that merges HSC records with external dataset features. It is not the canonical Pass 3 matrix.

Coverage details for every feature-matrix column are in [`docs/COVERAGE_REPORT.md`](../docs/COVERAGE_REPORT.md). Label semantics are in [`docs/LABELING_CONVENTIONS.md`](../docs/LABELING_CONVENTIONS.md).
