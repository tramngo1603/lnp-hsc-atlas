# Contributing to LNP-HSC Atlas

Thanks for your interest in contributing to the LNP-HSC Atlas, a curated dataset and computational framework comparing in vivo HSPC delivery approaches. Contributions from researchers across the field help make the analysis more complete and robust.

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
- Full-text access to paywalled papers with BM data, especially Zhu 2026, Ramishetti 2020, and Dacoba 2025

### Annotation format
Each data point should include:
- **Source:** Paper DOI, figure/table reference
- **Confidence tier:**
  - `HIGH`: explicitly stated in text or table
  - `MEDIUM`: supported but incomplete, such as an abstract-only claim
  - `LOW`: ambiguous or conflicting
- **Formulation:** ionizable lipid, helper lipid, cholesterol, PEG lipid (mol% where available)
- **Efficacy:** metric type (editing %, uptake %, barcode count, protein expression), value, cell type, timepoint
- **Species and model system**

See `annotations/kim_2024.json` for the most thorough example.

Do not infer a missing value from an analog, convert an absolute animal dose without a verified weight, or estimate figure-only efficacy. Use null with an explicit reason when the source does not support a value. Every numeric value must be traceable to source text, a table, source data, or a specifically approved extraction method.

### Other contributions
- Bug reports and fixes
- Analysis improvements or alternative statistical approaches
- Visualization suggestions
- Clinical trial data integration

## Code Standards

- **Linting:** `ruff check .` must pass
- **Type checking:** `mypy --ignore-missing-imports` must pass
- **Tests:** new code must include focused tests for the affected modules.
- **Style:** Type hints on all functions. No function >50 lines. No module >300 lines.

The goal is a resource that any researcher can use to understand where their formulation sits in the landscape and what the most promising next experiments are. Every new paper annotated makes the analysis more complete.
