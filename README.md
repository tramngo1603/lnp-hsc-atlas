# HSC-LNP Atlas

Curated dataset and ML framework comparing every published approach for delivering gene editing cargo to hematopoietic stem cells (HSCs) in bone marrow. 135 formulation records from 4 independent laboratories, 21 papers reviewed.

**Key numbers:** 135 records | 37 model features | 0.484 LightGBM balanced accuracy (4-paper LOPOCV) | 5/5 known SARs confirmed by SHAP

## Key Findings

- **Potency-selectivity tradeoff:** Antibody-conjugated LNPs achieve 12-44x higher potency (EC30 = 0.04-0.12 mg/kg) but deliver 76% of cargo to liver. Untargeted LNPs show better selectivity at higher doses. Confirmed across all four labs.
- **DOTAP specifically enables BM tropism:** ~4-fold higher BM delivery than DDAB (Mann-Whitney U, p=0.001) within Kim's 128-LNP barcoded screen.
- **PEG architecture, not chain length:** All DOTAP + C18PEG2000 formulations show background BM (mean 0.3 barcode counts). ALC-0159 (also C18 chain, different architecture) enables BM=48 — a 160-fold divergence.
- **No LNP in the Pareto ideal zone:** Only Ensoma's VLP platform (31% HSC editing, ~0% liver) occupies the ideal zone (>20% BM, <5% liver).
- **Cholesterol as a liver predictor:** Elevated to SHAP ranks 3-4 after Lian 2024 integration. Converges with three independent liver de-targeting studies (Gentry 2025, Su 2024, Patel 2024).

## Dataset

| Source | Records | Efficacy Metric | Species |
|--------|---------|-----------------|---------|
| Breda et al. (Science, 2023) | 9 | Cre-mediated editing in LSK cells | Mouse |
| Shi et al. (Nano Letters, 2023) | 21 | DiR uptake / CD45 siRNA knockdown | Mouse |
| Kim et al. (Nature Biotechnology, 2024) | 80 | Barcode biodistribution / aVHH expression | Mouse, NHP |
| Lian et al. (Nature Nanotechnology, 2024) | 25 | tdTom reporter / base editing | Mouse |
| **Total** | **135** | | |

Cross-platform comparators: Editas (58% NHP HSC editing), Tessera (40-60% NHP HBB editing), Ensoma VLP (31% HSC, ~0% liver).

## Repository Structure

```
hsc-lnp-atlas/
├── README.md
├── LICENSE                            # MIT
├── pyproject.toml
├── requirements.txt
│
├── annotations/                       # Paper annotations (21 papers)
│   ├── breda_2023.json               # 14 formulations
│   ├── shi_2023.json                 # 37 formulations
│   ├── kim_2024.json                 # 80 formulations
│   ├── lian_2024.json                # 21 formulations (full text + supplement)
│   ├── paper_annotations.json        # Cross-platform comparators
│   └── [16 additional paper annotations]
│
├── data/
│   ├── features/
│   │   └── hsc_features.parquet      # 135 × 37 feature matrix
│   ├── kim_screen/
│   │   └── kim_2024_screen_corrected.json  # 128 decoded LNPs
│   └── models/                       # Analysis outputs
│       ├── therapeutic_window.json
│       ├── pareto_validation_only.json
│       ├── gap_scores.json
│       ├── headgroup_tropism.json
│       ├── sar_validation.json
│       ├── shap_values.parquet
│       └── cv_results_with_il_descriptors.json
│
├── src/
│   ├── lnp_optimizer/                # ML pipeline, feature engineering, GP scoring
│   └── shared/                       # Pydantic models and utilities
│
├── tests/                            # 295 tests (pytest)
│
└── docs/
    └── EXPLORE.md                    # Exploration notes and paper summaries
```

## Installation

```bash
# Python 3.12+ required
uv sync

# Or with pip
pip install -r requirements.txt
```

## Usage

```python
import pandas as pd
import json

# Load feature matrix (135 formulations × 37 features)
df = pd.read_parquet("data/features/hsc_features.parquet")

# Load Kim screen data (128 decoded LNP formulations)
with open("data/kim_screen/kim_2024_screen_corrected.json") as f:
    screen = json.load(f)

# Run tests
# uv run python -m pytest tests/ -v
```

## Citation

```bibtex
@article{ngo2026hsc_lnp_atlas,
  title={The Potency-Selectivity Tradeoff in {HSC}-Targeted Lipid Nanoparticle
         Delivery: A Cross-Paper Quantitative Analysis with Model-Backed
         Formulation Recommendations},
  author={Ngo, Tram},
  journal={bioRxiv},
  year={2026},
  note={Preprint — bioRxiv DOI forthcoming}
}
```

## License

[MIT](LICENSE)

---

The dataset and analysis are maintained and expanded as new data is published. Contributions welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).
