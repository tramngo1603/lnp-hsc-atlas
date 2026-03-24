# Data

## `features/`
ML feature matrix. `hsc_features.parquet` contains 135 rows x 47 columns (37 model features + metadata + target). One row per formulation-experiment pair across 4 papers (Breda, Shi, Kim, Lian).

## `kim_screen/`
Decoded Kim 2024 barcoded screen. `kim_2024_screen_corrected.json` contains 128 LNP formulations with helper lipid, PEG lipid, and molar ratio assignments. 66 have BM barcode delivery data.

## `models/`
Analysis outputs — JSON and parquet files from the ML pipeline:
- `therapeutic_window.json` — 4PL dose-response fits, EC30/EC50 values
- `pareto_validation_only.json` — 6 LNP + 1 VLP Pareto data points (% units)
- `pareto_screen_only.json` — 26 Kim screen Pareto points (barcode units)
- `gap_scores.json` — GP-scored gap formulations with confidence bands
- `headgroup_tropism.json` — DOTAP vs DDAB analysis (~4x, p=0.001)
- `sar_validation.json` — 4/8 confirmed, 2 supported, 2 inconclusive
- `shap_values.parquet` — SHAP feature importance matrix
- `cv_results*.json` — cross-validation results

## `hsc/`
Curated HSC-LNP records. `hsc_curated.parquet` contains the raw 156 records before feature engineering and filtering.

## `audit/`
Post-hoc verification scripts. Each script validates a specific claim (Pareto mixed units, headgroup statistics, dose-response sensitivity, etc.). `AUDIT_REPORT.md` summarizes findings.

## `extractions/`
LLM-extracted paper data indexed by PMID. Used for evaluating extraction accuracy against ground truth annotations.

## `unified/`
Combined training data parquet merging HSC records with external dataset features.
