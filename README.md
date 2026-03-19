# HSC-LNP Atlas: Cross-Paper Quantitative Analysis of In Vivo HSC-Targeted Lipid Nanoparticle Delivery

The first standardized cross-paper quantitative comparison of all published approaches for delivering lipid nanoparticles (LNPs) to hematopoietic stem cells (HSCs) in bone marrow. This analysis reveals a fundamental potency-selectivity tradeoff between antibody-conjugated and untargeted LNP approaches, identifies DOTAP as a specific enabler of bone marrow tropism (~4-fold over DDAB, p=0.001), demonstrates that PEG lipid molecular architecture — not chain length alone — determines BM delivery, constructs Pareto frontiers from paired BM/liver data, and scores untested formulation combinations using a Gaussian process classifier. The curated dataset spans 131 HSC-LNP records from three independent laboratories plus cross-platform comparators. [bioRxiv preprint forthcoming]

## Key Findings

- **Potency-selectivity tradeoff:** Antibody-conjugated LNPs (CD117-targeted) achieve 12-44x higher potency (EC30 = 0.04-0.12 mg/kg) but deliver 76% of cargo to liver, while untargeted LNPs show better selectivity at higher doses.
- **Liver uptake is antibody-independent:** CD117 antibody targeting adds BM delivery without subtracting liver delivery. Liver accumulation is comparable between targeted and isotype control LNPs across two independent labs (Breda 2023, Shi 2023). Active de-targeting must be a separate intervention.
- **DOTAP specifically enables BM tropism:** ~4-fold higher BM delivery than DDAB (Mann-Whitney U, p=0.001) within Kim's 128-LNP barcoded screen. The differentiator is the glycerol ester backbone, not cationic charge class.
- **PEG architecture, not chain length, determines BM tropism:** All DOTAP + C18PEG2000 formulations show background BM delivery (mean 0.3 barcode counts) while ALC-0159 (also C18 chain, different molecular architecture) enables the highest BM delivery in the screen (barcode count 48). The C18-PEG benefit observed by Shi et al. for antibody-conjugated LNPs is antibody-dependent.
- **No LNP in the Pareto ideal zone:** The ideal zone (>30% BM, <5% liver) is occupied only by Ensoma's VLP platform (31% HSC editing, ~0% liver). No LNP formulation has reached this zone.

## Dataset

| Source | Records | Efficacy Metric | Species |
|--------|---------|-----------------|---------|
| Breda et al. (Science, 2023) | 14 | Cre-mediated editing in LSK cells | Mouse |
| Shi et al. (Nano Letters, 2023) | 37 | DiR uptake / CD45 siRNA knockdown | Mouse |
| Kim et al. (Nature Biotechnology, 2024) | 80 | Barcode biodistribution / aVHH expression | Mouse, NHP, Humanized |
| **Total** | **131** | | |

After filtering for records with efficacy classification: **110 rows x ~40 features** in the ML feature matrix.

Cross-platform comparators (not in ML pipeline): Editas Medicine (EHA 2025, 58% HBG1/2 editing in NHP), Ensoma (Nature Biotechnology 2025, 31% HSC editing via VLP).

## Repository Structure

```
hsc-lnp-atlas/
├── README.md
├── LICENSE
├── requirements.txt
├── CONTRIBUTING.md
├── pyproject.toml
│
├── annotations/                       # Ground truth paper annotations
│   ├── breda_2023.json
│   ├── shi_2023.json
│   ├── kim_2024.json
│   └── paper_annotations.json         # Cross-platform comparators
│
├── data/
│   ├── features/
│   │   └── hsc_features.parquet       # 110 x ~40 feature matrix
│   ├── kim_screen/
│   │   └── kim_2024_screen_corrected.json  # 128 decoded LNP formulations
│   └── models/
│       ├── therapeutic_window.json    # Dose-response fits + EC30/EC50
│       ├── pareto_validation_only.json
│       ├── gap_scores.json            # GP-scored gap formulations
│       ├── headgroup_tropism.json     # DOTAP vs DDAB analysis
│       └── sar_validation.json        # 4/8 confirmed SARs
│
├── src/
│   ├── lnp_optimizer/                 # ML pipeline, feature engineering, GP scoring
│   ├── pubmed_agent/                  # PubMed search + LLM extraction
│   ├── external_data/                 # AGILE, LNPDB, LANCE ingestion
│   └── shared/                        # Shared types and utilities
│
├── outputs/
│   ├── generate_paper.py              # Paper draft generator (.docx)
│   └── generate_figures.py            # 5 publication figures (matplotlib)
│
├── papers/
│   └── seeds/
│       └── potency_selectivity_tradeoff.md
│
├── tests/                             # 259 tests (pytest)
│
└── docs/
    └── EXPLORE.md                     # Exploration notes and paper summaries
```

## Installation

```bash
# Python 3.10+ required
pip install -r requirements.txt

# Or with uv (recommended)
uv sync
```

## Usage

```python
# Load the feature matrix
import pandas as pd
df = pd.read_parquet("data/features/hsc_features.parquet")

# Load Kim screen data (128 decoded LNP formulations)
import json
with open("data/kim_screen/kim_2024_screen_corrected.json") as f:
    screen = json.load(f)

# Load therapeutic window (dose-response fits)
with open("data/models/therapeutic_window.json") as f:
    tw = json.load(f)

# Load gap formulation scores
with open("data/models/gap_scores.json") as f:
    gaps = json.load(f)
```

```bash
# Generate publication figures
uv run python outputs/generate_figures.py

# Generate paper draft (.docx)
uv run python outputs/generate_paper.py

# Run tests
uv run python -m pytest tests/ -v

# Lint
uv run ruff check .
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
  doi={10.1101/XXXX.XXXX},
  note={Preprint}
}
```

## License

[MIT](LICENSE)

---

## The Marrow Map

This repository is the foundation for **The Marrow Map** — a living, open-source quantitative review of all in vivo HSC delivery approaches. The vision is a community-maintained atlas covering LNPs (targeted and untargeted), VLPs, adenoviral vectors, and clinical trials, with standardized metrics (EC30, therapeutic window, Pareto position) and honest assessments.

Updated as new papers and clinical data emerge. Every new publication refines the quantitative map guiding rational formulation design for in vivo HSC gene therapy.

Contributions welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).
