# LNP-HSC Atlas

The LNP-HSC Atlas is a curated dataset and analysis framework for in vivo lipid nanoparticle delivery to hematopoietic stem and progenitor cells (HSPCs). It contains 331 formulation-experiment evidence rows from 18 published sources.

[**Open the interactive explorer →**](https://tramngo1603.github.io/lnp-hsc-atlas/)

Compare formulations, explore marrow and liver results, and read the key findings with their supporting evidence.

**Release snapshot:** 331 rows | 18 matrix sources | 48 columns | 315 efficacy labels | 154 rows with ionizable-lipid descriptors

Missing values are preserved when the literature does not support a defensible value.

## Dataset composition

The largest sources are Xu 2026 (148 rows), Kim 2024 (80), Lian 2024 (25), Shi 2023 (21), Hanafy 2025 (14), Breda 2023 (9), and Hofstraat 2025 (9). Eleven additional sources contribute the remaining records.

Rows are formulation-experiment evidence units, not guaranteed unique chemical formulations. The release audit found no exact matrix duplicates and removed no rows. Repeated observations of the same formulation remain grouped during model validation.

## Repository layout

| Path | Contents |
| --- | --- |
| `data/features/hsc_features.parquet` | Canonical 331 x 48 feature matrix |
| `data/features/hsc_features.csv` | CSV rendering of the same matrix |
| `data/hsc/hsc_curated.parquet` | Curated source table for the established atlas records |
| `data/literature_records.json` | Rich literature records with field-level source context |
| `annotations/` | Source annotations and provenance-chain records |
| `data/audit/` | Machine-readable and narrative validation outputs |
| `data/models/atlas_analysis.json` | Sensitivity analysis and established Pareto results |
| `docs/COVERAGE_REPORT.md` | Per-column fill rates and sparse evidence blocks |
| `docs/MODEL_VALIDATION.md` | Leakage-aware model validation design and results |
| `explorer/src/App.jsx` | Generated explorer data from the atlas matrix and model reports |
| `explorer/src/Explorer.jsx` | Explorer layout and interactive charts |
| `src/lnp_optimizer/explorer_analysis.py` | Source-specific chart data and measurement checks |

## Installation

Python 3.12 or 3.13 and [uv](https://docs.astral.sh/uv/) are recommended.

```bash
uv sync --extra dev
```

## Usage

```python
import pandas as pd

features = pd.read_parquet("data/features/hsc_features.parquet")
assert features.shape == (331, 48)

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

Regenerate the explorer data after updating the dataset:

```bash
make patch
```

Build and serve the explorer from the repository root:

```bash
npm --prefix explorer ci
npm --prefix explorer run build
npm --prefix explorer run preview -- --host 127.0.0.1 --port 4173 --strictPort
```

Open the [local explorer](http://localhost:4173/lnp-hsc-atlas/). Keep the preview command
running while you use it.

Pushing to `main` runs the GitHub Pages workflow, which builds and publishes the
[public explorer](https://tramngo1603.github.io/lnp-hsc-atlas/).

This pipeline refreshes the Pareto, PEG lipid, helper lipid, and dose charts when records
are added. Charts compare measurements within a source, assay, unit, species, and target
cell group. Pareto points require numeric bone-marrow and liver results from the same
experiment. The 196 added literature records currently contain no such percentage pairs;
usable single-organ results still appear in the other charts. Barcode counts are kept
separate from percentages, and estimated light measurements are labeled as estimates.

## Coverage and analysis cautions

- Thirty of 48 matrix columns are complete across all 331 rows.
- The efficacy label covers 315/331 rows (95.2%). Unlabeled rows must be excluded from supervised training.
- Four exact-boundary Lian rows retain their established labels. The training loader excludes these rows from threshold-sensitive evaluation and removes `label_boundary_case` from predictor features.
- Each of the eight ionizable-lipid descriptor columns covers 154/331 rows (46.5%).
- Physicochemical and toxicity fields remain in the rich records rather than the fixed 48-column matrix. Detailed toxicity evidence is available for 11 literature records.
- `lgbm_model.pkl`, `shap_values.parquet`, `lopocv_results.json`, and `validation_comparison.json` use the 311 threshold-comparable labeled rows. The corrected screen and validation Pareto analyses include only comparable, same-record absolute bone-marrow and liver percentage pairs.
- Feature-target correlations are descriptive. They are confounded by paper, assay, and repeated-formulation structure and should not be interpreted causally.

## Contributing

Contributions are welcome through pull requests and issues. New records should include per-value provenance, use null for unsupported values, and pass the annotation and combined-data audits. See [CONTRIBUTING.md](CONTRIBUTING.md) and the templates in `docs/`.

## License

Licensed under the [Apache License 2.0](LICENSE).
