# Labeling Conventions

The canonical feature matrix stores the harmonized efficacy class in `target`:

| Class | Target | Current threshold |
| --- | ---: | --- |
| Low | 0 | Less than 10% |
| Medium | 1 | 10% through 30%, inclusive |
| High | 2 | Greater than 30%, strictly |
| Unlabeled | null | No defensible numeric label |

The current high rule is `>30%`, not `>=30%`.

## Lian boundary cases

Four `lian_2024` rows report exactly 30% LT-HSC delivery and retain their established `high` labels:

| Formulation | Experiment | Stored target | Boundary marker |
| --- | --- | ---: | ---: |
| `Lian_A7` | `Lian_A7_screen_n1` | 2 | 1 |
| `Lian_A13` | `Lian_A13_validated_n3` | 2 | 1 |
| `Lian_C6` | `Lian_C6_validated_n3` | 2 | 1 |
| `Lian_C9` | `Lian_C9_screen_n1` | 2 | 1 |

These are boundary cases, not errors. Their source values and labels remain untouched. The metadata column `label_boundary_case` is 1 for these four rows and 0 for all other rows, so consumers can apply the strict current convention when needed.

## Model handling

`lnp_optimizer.models.load_feature_matrix` excludes rows with `label_boundary_case = 1` from threshold-sensitive training and validation. It also removes the marker itself from predictor features. Unlabeled rows remain part of the atlas but are excluded from supervised modeling.

For descriptive release counts, retain all stored labels. For comparisons that interpret the class thresholds, filter to `label_boundary_case = 0`.
