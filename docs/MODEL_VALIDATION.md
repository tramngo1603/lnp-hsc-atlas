# Model Validation

The training pipeline reports three LightGBM validation views on the 311 labeled,
threshold-comparable rows. Four Lian 2024 boundary rows are excluded before evaluation.

| Validation design | Balanced accuracy | Purpose |
| --- | ---: | --- |
| Five-fold formulation-grouped | 0.5375 | Primary within-literature estimate |
| Five-fold row-random | 0.5975 | Diagnostic for leakage-driven optimism |
| Leave-one-paper-out | 0.2568 | Source-shift stress test |

Formulation-grouped validation keeps every record sharing a formulation token in the same
fold. The split audit confirms that no formulation token appears in both training and held-out
partitions. Row-random validation does not provide that protection and is not the primary model
result.

Leave-one-paper-out validation tests a harder question: whether a model trained on the other
sources transfers to an unseen paper, assay context, and laboratory protocol. Its low result
shows that the current model should not be treated as a general predictor for an unseen research
program.

Detailed metrics, confusion matrices, and per-fold overlap audits are stored in
`data/models/validation_comparison.json`. The implementation is in
`src/lnp_optimizer/models.py`, and `tests/test_models.py` verifies formulation-disjoint
partitions.
