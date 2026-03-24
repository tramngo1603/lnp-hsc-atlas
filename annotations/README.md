# Annotations

Structured paper annotations for the HSC-LNP Atlas. Each JSON file follows the template in `docs/annotation_template.json`.

## Annotation Schema

Each file contains:
- `_annotation_meta` — annotator, date, source quality
- `paper` — title, authors, journal, DOI, platform type
- `formulations[]` — composition (IL, helper, cholesterol, PEG, mol%), targeting, physical properties
- `experiments[]` — dose, route, species, timepoint, BM/liver delivery results, editing data
- `key_findings_for_project` — relevance to the atlas
- `comparison_to_existing_data` — vs Breda, Shi, Kim, Pareto implications
- `limitations_and_caveats`

## Confidence Tiers

- **HIGH** — explicitly stated in text or table
- **MEDIUM** — estimated from figures or inferred from context
- **LOW** — ambiguous, conflicting, or extrapolated

## Efficacy Classification

- `high` — >30% HSC delivery/editing
- `medium` — 10-30%
- `low` — <10%
