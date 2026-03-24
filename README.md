# HSC-LNP Atlas

Curated dataset and ML framework comparing every published approach for delivering gene editing cargo to hematopoietic stem cells (HSCs) in bone marrow. 135 formulation records from 4 independent laboratories, 21 papers reviewed.

**Key numbers:** 135 records | 37 model features | 0.484 LightGBM balanced accuracy (4-paper LOPOCV) | 5/5 known SARs confirmed by SHAP

**[Interactive Explorer](https://tramngo1603.github.io/lnp-hsc-atlas/)** — browse the Pareto frontier, SHAP feature importance, competitive timeline, and all 21 annotated papers.

## Key Findings

- **Potency-selectivity tradeoff:** Antibody-conjugated LNPs achieve 12-44x higher potency (EC30 = 0.04-0.12 mg/kg) but deliver 76% of cargo to liver. Untargeted LNPs show better selectivity at higher doses. Confirmed across all four labs.
- **DOTAP specifically enables BM tropism:** ~4-fold higher BM delivery than DDAB (Mann-Whitney U, p=0.001) within Kim's 128-LNP barcoded screen.
- **PEG architecture, not chain length:** All DOTAP + C18PEG2000 formulations show background BM (mean 0.3 barcode counts). ALC-0159 (also C18 chain, different architecture) enables BM=48 — a 160-fold divergence.
- **No LNP in the Pareto ideal zone:** Only Ensoma's VLP platform (31% HSC editing, ~0% liver) occupies the ideal zone (>20% BM, <5% liver).
- **Cholesterol as a liver predictor:** Elevated to SHAP ranks 3-4 after Lian 2024 integration. Converges with three independent liver de-targeting studies (Gentry 2025, Su 2024, Patel 2024).

## Dataset

| Source | Records | Efficacy Metric | Species |
|--------|---------|-----------------|---------|
| [Breda et al. (Science, 2023)](https://doi.org/10.1126/science.ade6967) | 9 | Cre-mediated editing in LSK cells | Mouse |
| [Shi et al. (Nano Letters, 2023)](https://doi.org/10.1021/acs.nanolett.3c00304) | 21 | DiR uptake / CD45 siRNA knockdown | Mouse |
| [Kim et al. (Nature Biotechnology, 2024)](https://doi.org/10.1038/s41587-024-02470-2) | 80 | Barcode biodistribution / aVHH expression | Mouse, NHP |
| [Lian et al. (Nature Nanotechnology, 2024)](https://doi.org/10.1038/s41565-024-01680-8) | 25 | tdTom reporter / base editing | Mouse |
| **Total** | **135** | | |

Cross-platform comparators: Editas (58% NHP HSC editing), Tessera (40-60% NHP HBB editing), Ensoma VLP (31% HSC, ~0% liver).

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

# Load feature matrix (135 formulations x 37 features)
df = pd.read_parquet("data/features/hsc_features.parquet")

# Load Kim screen data (128 decoded LNP formulations)
with open("data/kim_screen/kim_2024_screen_corrected.json") as f:
    screen = json.load(f)

# Run tests
# uv run python -m pytest tests/ -v
```

## Roadmap

The atlas is an active project, not a static dataset.

**Now**
- 135 formulation records from 4 labs (Breda, Shi, Kim, Lian)
- 21 papers reviewed and annotated
- LightGBM model recovering all 5 known SARs via SHAP (balanced accuracy 0.484, 4-paper LOPOCV)
- Interactive explorer with 9 analysis tabs

**In progress**
- Automated update pipeline: new annotation → model retrain → figures → explorer update in one command
- Additional paper annotations targeting 200+ rows (Sago 2018, Lian bioluminescence screen)
- Ionizable lipid structure resolution to expand molecular descriptor coverage

**Investigating**
- Whether molecular descriptors and external LNP databases (LNPDB, LANCE, AGILE) can improve the model beyond feature-importance analysis
- Nearest-neighbor lookup tool for comparing candidate formulations against the dataset

**Contributing**

The atlas grows with every new publication. If your lab has published or unpublished HSC delivery data, contributions are welcome:
- Submit an annotation JSON via pull request (see `annotations/` for schema examples)
- Report data corrections via GitHub Issues
- Suggest papers for annotation

All contributors are acknowledged in the explorer and in any resulting publications.

## License

[MIT](LICENSE)

---

The dataset and analysis are maintained and expanded as new data is published. Contributions welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).
