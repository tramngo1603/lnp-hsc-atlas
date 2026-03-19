# Contributing to HSC-LNP Atlas

Thanks for your interest in contributing. This project aims to become a community-maintained quantitative atlas of in vivo HSC delivery approaches — **The Marrow Map** — and contributions from researchers across the field are essential to that vision.

## How to Contribute

1. **Open an issue first.** Describe what you'd like to add or change. This avoids duplicate work and lets us discuss the approach.
2. **Fork and branch.** Create a feature branch from `main`.
3. **Submit a PR.** Reference the issue number. Keep PRs focused on a single change.

## What We Most Need

### Paper annotations (highest priority)
New papers measuring bone marrow delivery of LNPs, VLPs, or other non-viral vectors. We especially need:
- Papers reporting **both** BM and liver delivery for the same formulation (very rare)
- Independent replication of the **DOTAP-BM tropism** finding outside Kim's screen
- **Liver de-targeting** data paired with BM measurements
- Full-text access to paywalled papers with BM data (Lian/Siegwart 2024, Da Silva Sanchez 2022)

### Annotation format
Each data point should include:
- **Source:** Paper DOI, figure/table reference
- **Confidence tier:**
  - `HIGH` — explicitly stated in text or table
  - `MEDIUM` — estimated from figures or inferred from context
  - `LOW` — ambiguous, conflicting, or extrapolated
- **Formulation:** ionizable lipid, helper lipid, cholesterol, PEG lipid (mol% where available)
- **Efficacy:** metric type (editing %, uptake %, barcode count, protein expression), value, cell type, timepoint
- **Species and model system**

See `annotations/kim_2024.json` for the most thorough example.

### Other contributions
- Bug reports and fixes
- Analysis improvements or alternative statistical approaches
- Visualization suggestions
- Clinical trial data integration

## Code Standards

- **Linting:** `ruff check .` must pass
- **Type checking:** `mypy --ignore-missing-imports` must pass
- **Tests:** `pytest tests/ -v` — all 259 tests must pass, and new code should include tests
- **Style:** Type hints on all functions. No function >50 lines. No module >300 lines.

## Vision: The Marrow Map

This repo is the seed of a living quantitative review — updated monthly as new data drops, with standardized metrics (EC30, therapeutic window, Pareto position, safety profile) across all in vivo HSC delivery platforms. The goal is a resource that any researcher can use to understand where their formulation sits in the landscape and what the most promising next experiments are.

Every new paper annotated makes the map more complete. Every contribution compounds.
