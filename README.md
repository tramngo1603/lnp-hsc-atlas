# LNP-HSC Atlas

The LNP-HSC Atlas is a curated dataset and analysis framework for in vivo lipid nanoparticle delivery to hematopoietic stem and progenitor cells (HSPCs). It contains 333 formulation-experiment evidence rows from 19 published sources.

**Release snapshot:** 333 rows | 19 matrix sources | 48 columns | 315 efficacy labels | 154 rows with ionizable-lipid descriptors

Missing values are preserved when the literature does not support a defensible value.

## Dataset composition

The largest sources are Xu 2026 (148 rows), Kim 2024 (80), Lian 2024 (25), Shi 2023 (21), Hanafy 2025 (14), Breda 2023 (9), and Hofstraat 2025 (9). Twelve additional sources contribute the remaining records.

Rows are formulation-experiment evidence units, not guaranteed unique chemical formulations. The release audit found no exact matrix duplicates and removed no rows. Repeated observations of the same formulation remain grouped during model validation.

## Release decisions

- `palchaudhuri_2025` is the canonical flat-schema representation of the Blood 2025 abstract. The `tessera_*` annotation files contribute no matrix rows and remain as conference-series provenance.
- Chappell 2024 is not duplicated by Breda 2023. Breda provides platform-level analog support only, so Chappell composition remains null.
- Figure-only efficacy for Chander, Peng, Zhao, and Iida remains null. Only user-confirmed PRELIVE estimates use figure-derived values.
- Absolute per-mouse doses are not converted to mg/kg without verified animal weights.
- The source-reported 116% Xu LNP-123 replicate is retained and explicitly flagged as an outlier.
- Ionizable-lipid structures and other missing values are never inferred from an analog.
- The current labeling rule is strictly `high >30%`, `medium 10-30%`, and `low <10%`. Four `lian_2024` rows measured at exactly 30% retain their established `high` labels. They are boundary cases, not errors, and are identified by `label_boundary_case = 1`.

See the [labeling conventions](docs/LABELING_CONVENTIONS.md), [coverage report](docs/COVERAGE_REPORT.md), and [dedupe and contradiction audit](data/audit/consolidated_audit.json) for the complete release accounting.

## Repository layout

| Path | Contents |
| --- | --- |
| `data/features/hsc_features.parquet` | Canonical 333 x 48 feature matrix |
| `data/features/hsc_features.csv` | CSV rendering of the same matrix |
| `data/hsc/hsc_curated.parquet` | Curated source table for the established atlas records |
| `data/literature_records.json` | Rich literature records plus 3 paywalled source stubs |
| `annotations/` | Source annotations and provenance-chain records |
| `data/audit/` | Machine-readable and narrative validation outputs |
| `data/models/atlas_analysis.json` | Sensitivity analysis and established Pareto results |
| `docs/COVERAGE_REPORT.md` | Per-column fill rates and sparse evidence blocks |
| `explorer/src/App.jsx` | Interactive explorer generated from the atlas matrix and model reports |

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
make release
```

The individual release steps are also reproducible:

```bash
uv run python scripts/build_feature_matrix.py
uv run python scripts/audit_literature_records.py
uv run python scripts/audit_combined_atlas.py
uv run python scripts/generate_coverage_report.py
uv run python scripts/analyze_atlas.py
```

Regenerate the explorer data blocks with the existing extraction and patch pipeline, then build
the deployable site:

```bash
make patch
cd explorer && npm ci && npm run build
```

## Leakage-aware model validation

`make train` reports three LightGBM validation views on the threshold-comparable labeled rows:

- Five-fold formulation-grouped validation is the primary within-literature estimate. Repeated observations of the same formulation stay in one fold.
- Five-fold row-random validation is retained only as a diagnostic of leakage-driven optimism.
- Leave-one-paper-out validation remains the broader source-shift stress test.

Results and per-fold overlap audits are stored in `data/models/validation_comparison.json`.

## Coverage and analysis cautions

- Thirty of 48 matrix columns are complete across all 333 rows.
- The efficacy label covers 315/333 rows (94.6%). Unlabeled rows must be excluded from supervised training.
- Four exact-boundary Lian rows retain their established labels. The training loader excludes these rows from threshold-sensitive evaluation and removes `label_boundary_case` from predictor features.
- Each of the eight ionizable-lipid descriptor columns covers 154/333 rows (46.2%).
- Physicochemical and toxicity fields remain in the rich records rather than the fixed 48-column matrix. Detailed toxicity evidence is available for 13 literature records.
- `lgbm_model.pkl`, `shap_values.parquet`, `lopocv_results.json`, and `validation_comparison.json` use the 311 threshold-comparable labeled rows. The corrected screen and validation Pareto analyses include only comparable, same-record absolute bone-marrow and liver percentage pairs.
- Feature-target correlations are descriptive. They are confounded by paper, assay, and repeated-formulation structure and should not be interpreted causally.

## Known open sources

- Two Xue 2022 records remain `partial_pending_main_text`.
- Ramishetti 2020, Zhu 2026, and Dacoba 2025 remain paywalled stubs and do not contribute matrix rows.
- Proprietary and structurally unresolved lipids remain without fabricated structures or descriptors.

## Contributing

Contributions are welcome through pull requests and issues. New records should include per-value provenance, use null for unsupported values, and pass the annotation and combined-data audits. See [CONTRIBUTING.md](CONTRIBUTING.md) and the templates in `docs/`.

## License

Licensed under the [Apache License 2.0](LICENSE).
