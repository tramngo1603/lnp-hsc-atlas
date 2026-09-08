# LNP-HSC Atlas

The LNP-HSC Atlas is a curated dataset and analysis framework for in vivo lipid nanoparticle delivery to hematopoietic stem and progenitor cells (HSPCs). Version 2.0 expands the protected 135-row baseline with 198 literature-mined formulation-experiment records.

**Release snapshot:** 333 rows | 19 matrix sources | 48 columns | 315 efficacy labels | 154 rows with ionizable-lipid descriptors

The first 135 matrix rows remain value-identical to the pre-expansion baseline. Missing values are preserved when the literature does not support a defensible value.

## Dataset composition

| Block | Sources | Rows |
| --- | ---: | ---: |
| Protected baseline: Breda 2023, Shi 2023, Kim 2024, Lian 2024 | 4 | 135 |
| Pass 1 expansion | 15 | 198 |
| **Combined matrix** | **19** | **333** |

The 198-row expansion contains Xu 2026 (148), Hanafy 2025 (14), Hofstraat 2025 (9), Shi 2025 thesis (4), Chander 2023 (3), Palchaudhuri 2025 (3), and 17 rows from nine smaller sources.

Rows are formulation-experiment evidence units, not guaranteed unique chemical formulations. The Pass 3 audit found no exact matrix duplicates and removed no rows. Three Xu formulations have both lead-context and uniform-library records; group analyses by formulation token when leakage between those roles would matter.

## Release decisions

- `palchaudhuri_2025` is the canonical flat-schema representation of the Blood 2025 abstract. The `tessera_*` annotation files contribute no matrix rows and remain as conference-series provenance.
- Chappell 2024 is not duplicated by Breda 2023. Breda provides platform-level analog support only, so Chappell composition remains null.
- Figure-only efficacy for Chander, Peng, Zhao, and Iida remains null. Only user-confirmed PRELIVE estimates use figure-derived values.
- Absolute per-mouse doses are not converted to mg/kg without verified animal weights.
- The source-reported 116% Xu LNP-123 replicate is retained and explicitly flagged as an outlier.
- Ionizable-lipid structures and other missing values are never inferred from an analog.
- The current labeling rule is strictly `high >30%`, `medium 10-30%`, and `low <10%`. Four protected legacy `lian_2024` rows measured at exactly 30% retain their v1 `high` labels. They are boundary cases, not errors, and are identified by `label_boundary_case = 1`.

See the [labeling conventions](docs/LABELING_CONVENTIONS.md), [Pass 3 coverage report](docs/COVERAGE_REPORT.md), and [dedupe and contradiction audit](data/audit/pass3_dedupe_report.json) for the complete release accounting.

## Repository layout

| Path | Contents |
| --- | --- |
| `data/features/hsc_features.parquet` | Canonical 333 x 48 feature matrix |
| `data/features/hsc_features.csv` | CSV rendering of the same matrix |
| `data/hsc/hsc_curated.parquet` | Protected legacy source table used to build the original block |
| `data/new_records_pass1.json` | 198 rich flat records plus 3 paywalled source stubs |
| `annotations/` | Legacy annotations and provenance-chain records |
| `data/audit/` | Machine-readable and narrative validation outputs |
| `data/models/pass3_analysis.json` | Combined-data sensitivity analysis and established Pareto results |
| `docs/COVERAGE_REPORT.md` | Per-column old, new, and combined fill rates |
| `explorer/src/App.jsx` | Interactive v2 explorer generated from the combined matrix and model reports |

## Installation

Python 3.12 or 3.13 and [uv](https://docs.astral.sh/uv/) are recommended.

```bash
uv sync --extra dev
```

## Usage

```python
import pandas as pd

features = pd.read_parquet("data/features/hsc_features.parquet")
assert features.shape == (333, 48)

labeled = features.dropna(subset=["target"])
assert len(labeled) == 315

threshold_comparable = labeled[labeled["label_boundary_case"] == 0]
assert len(threshold_comparable) == 311
```

Rebuild and validate the release outputs with:

```bash
make pass3
```

The supplied history declares `src/external_data/` and `src/pubmed_agent/` in its package
configuration but does not contain either source package. Raw full-suite collection therefore
reports missing-module errors. After excluding those unavailable-package collectors, the release
runs 134 tests successfully; the four separately exercised fingerprint tests have the documented
`external_data` dependency.

The individual Pass 3 steps are also reproducible:

```bash
uv run python scripts/build_feature_matrix.py
uv run python scripts/audit_new_records_pass2.py
uv run python scripts/audit_combined_pass3.py
uv run python scripts/generate_coverage_report_pass3.py
uv run python scripts/analyze_pass3.py
```

Regenerate the explorer data blocks with the existing extraction and patch pipeline, then build
the deployable site:

```bash
make patch
cd explorer && npm ci && npm run build
```

## Leakage-aware model validation

`make train` reports three LightGBM validation views on the threshold-comparable labeled rows:

- Five-fold formulation-grouped validation is the primary within-literature estimate. Every record with the same source-qualified formulation token stays in one fold.
- Five-fold row-random validation is retained only as a diagnostic of leakage-driven optimism.
- Leave-one-paper-out validation remains the broader source-shift stress test.

For numbered formulations, the token uses the normalized LNP number and discards cargo and study-role suffixes. For example, Xu lead, HBG, Cre, and library appearances of `LNP-028` or `LNP-168` cannot cross the training and held-out partitions. Other tokens use the normalized full formulation identifier within the source paper. Results and per-fold overlap audits are stored in `data/models/validation_comparison.json`.

In the current release run, row-random balanced accuracy is 0.5975 +/- 0.0392 and formulation-grouped balanced accuracy is 0.5375 +/- 0.0630. Row-random folds share 7 to 12 formulation tokens across their partitions; every formulation-grouped fold has zero overlap.

## Coverage and analysis cautions

- Thirty of 48 matrix columns are complete across all 333 rows.
- The efficacy label covers 315/333 rows (94.6%). Unlabeled rows must be excluded from supervised training.
- Four exact-boundary Lian rows retain legacy labels. The training loader excludes these rows from threshold-sensitive evaluation and removes `label_boundary_case` from predictor features.
- Each of the eight ionizable-lipid descriptor columns covers 154/333 rows (46.2%).
- Physicochemical and toxicity fields remain in the rich records rather than the fixed 48-column matrix. Detailed toxicity evidence is available for only 13/198 new rows.
- `lgbm_model.pkl`, `shap_values.parquet`, `lopocv_results.json`, and `validation_comparison.json` use the 311 threshold-comparable labeled rows in the combined release. Other legacy model artifacts may describe earlier analysis stages. The corrected screen and validation Pareto frontiers are unchanged because the expansion adds no comparable, same-record absolute bone-marrow and liver percentage pair.
- Combined feature-target correlations are descriptive. They are confounded by paper, assay, and repeated-formulation structure and should not be interpreted causally.

## Known open sources

- Two Xue 2022 records remain `partial_pending_main_text`.
- Ramishetti 2020, Zhu 2026, and Dacoba 2025 remain paywalled stubs and do not contribute matrix rows.
- Proprietary and structurally unresolved lipids remain without fabricated structures or descriptors.

## Contributing

Contributions are welcome through pull requests and issues. New records should include per-value provenance, use null for unsupported values, and pass the annotation and combined-data audits. See [CONTRIBUTING.md](CONTRIBUTING.md) and the templates in `docs/`.

## License

Licensed under the [Apache License 2.0](LICENSE).
