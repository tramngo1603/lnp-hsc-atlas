# Ground Truth Annotations

Human-annotated extraction ground truth for evaluating LLM extraction accuracy.

## Schema

Each JSON file conforms to `ExtractionResult` from `pubmed_agent/extractor.py`.

## Annotation Process

1. Read the full paper (not just abstract)
2. Extract every distinct LNP formulation into a `formulations[]` entry
3. Extract every experiment into an `experiments[]` entry, linked by `formulation_name`
4. Set confidence: HIGH (from text/table), MEDIUM (from figure), LOW (ambiguous)
5. Set `label_for_ml.hsc_efficacy_class`: high (>30%), medium (10-30%), low (<10%), null

## Files

| File | Paper | PMID |
|------|-------|------|
| `breda_2023.json` | Breda et al., Science 2023 — CD117/LNP-mRNA | 37499029 |
| `shi_2023.json` | Shi et al., Nano Letters 2023 — CD117/LNP-siRNA | 36637988 |
| `kim_2024.json` | Kim et al., Nature Biotech 2024 — LNP67 | 39578569 |
| `paper_annotations.json` | Cross-platform comparators (Editas, Kim ASH, Ensoma ×2, Breda correction) | — |

## Validation

```bash
python -m pubmed_agent evaluate --predictions data/extractions/ --ground-truth annotations/
```
