# Pass 3 Coverage Report

Generated from `data/features/hsc_features.parquet` after Pass 3 consolidation. The matrix contains 135 protected baseline rows followed by 198 new rows, for 333 rows across 19 papers and 48 columns.

## Method

Coverage is the count of non-null cells. Numeric zero and boolean-style zero are valid populated values, especially in one-hot encodings. Coverage therefore measures availability, not feature prevalence. The split boundary and value identity of the original 135 rows are verified by `scripts/audit_combined_pass3.py`.

## Summary

- 30/48 columns are complete across all 333 rows.
- `label_boundary_case` marks four protected Lian 2024 rows whose exact 30% measurements retain v1 `high` labels. New rows use the strict `high >30%` rule.
- The supervised target is populated for 315/333 rows (94.6%). The 18 unlabeled rows remain in the atlas but must be excluded from supervised training.
- Core molar composition coverage rises from 63/135 (46.7%) in the old block to 187/198 (94.4%) in the new block. Combined ionizable/helper/cholesterol coverage is 250/333 (75.1%).
- Dose coverage rises from 59/135 (43.7%) to 187/198 (94.4%), yielding 246/333 (73.9%) combined. Absolute per-mouse doses are intentionally not converted to mg/kg.
- All eight ionizable-lipid descriptor columns cover 154/333 (46.2%): 133/135 old and 21/198 new. The low new-record rate reflects proprietary or unverified lipid identities, not a failed calculation.

## Coverage by matrix column

| Column | Group | Old 135 | New 198 | Combined 333 |
| --- | --- | ---: | ---: | ---: |
| `source` | metadata | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |
| `paper` | metadata | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |
| `formulation_id` | metadata | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |
| `experiment_id` | metadata | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |
| `assay_category` | metadata | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |
| `composition_confidence` | metadata | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |
| `ionizable_mol_pct` | composition | 63/135 (46.7%) | 187/198 (94.4%) | 250/333 (75.1%) |
| `helper_mol_pct` | composition | 63/135 (46.7%) | 187/198 (94.4%) | 250/333 (75.1%) |
| `cholesterol_mol_pct` | composition | 63/135 (46.7%) | 187/198 (94.4%) | 250/333 (75.1%) |
| `peg_mol_pct` | composition | 63/135 (46.7%) | 181/198 (91.4%) | 244/333 (73.3%) |
| `il_to_helper_ratio` | engineered ratio | 63/135 (46.7%) | 187/198 (94.4%) | 250/333 (75.1%) |
| `il_to_chol_ratio` | engineered ratio | 63/135 (46.7%) | 187/198 (94.4%) | 250/333 (75.1%) |
| `chol_to_helper_ratio` | engineered ratio | 63/135 (46.7%) | 187/198 (94.4%) | 250/333 (75.1%) |
| `peg_chain_numeric` | composition | 124/135 (91.9%) | 179/198 (90.4%) | 303/333 (91.0%) |
| `dose_mg_per_kg` | dose | 59/135 (43.7%) | 187/198 (94.4%) | 246/333 (73.9%) |
| `targeting_encoded` | encoding | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |
| `helper_is_cationic` | encoding | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |
| `species_mouse` | encoding | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |
| `species_nhp` | encoding | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |
| `species_human` | encoding | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |
| `assay_barcode_delivery` | encoding | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |
| `assay_depletion` | encoding | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |
| `assay_editing` | encoding | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |
| `assay_knockdown` | encoding | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |
| `assay_protein_expression` | encoding | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |
| `hl_dspc` | encoding | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |
| `hl_dope` | encoding | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |
| `hl_dotap` | encoding | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |
| `hl_ddab` | encoding | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |
| `hl_dotma` | encoding | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |
| `hl_epc` | encoding | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |
| `receptor_cd117` | encoding | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |
| `receptor_cd45` | encoding | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |
| `clone_2b8` | encoding | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |
| `clone_ack2` | encoding | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |
| `clone_igg` | encoding | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |
| `il_molecular_weight` | IL descriptor | 133/135 (98.5%) | 21/198 (10.6%) | 154/333 (46.2%) |
| `il_logp` | IL descriptor | 133/135 (98.5%) | 21/198 (10.6%) | 154/333 (46.2%) |
| `il_tpsa` | IL descriptor | 133/135 (98.5%) | 21/198 (10.6%) | 154/333 (46.2%) |
| `il_hbd` | IL descriptor | 133/135 (98.5%) | 21/198 (10.6%) | 154/333 (46.2%) |
| `il_hba` | IL descriptor | 133/135 (98.5%) | 21/198 (10.6%) | 154/333 (46.2%) |
| `il_rotatable_bonds` | IL descriptor | 133/135 (98.5%) | 21/198 (10.6%) | 154/333 (46.2%) |
| `il_num_rings` | IL descriptor | 133/135 (98.5%) | 21/198 (10.6%) | 154/333 (46.2%) |
| `il_heavy_atom_count` | IL descriptor | 133/135 (98.5%) | 21/198 (10.6%) | 154/333 (46.2%) |
| `target` | label | 135/135 (100.0%) | 180/198 (90.9%) | 315/333 (94.6%) |
| `metric_type` | metric metadata | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |
| `covalent_lipid_mol_pct` | composition | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |
| `label_boundary_case` | metadata | 135/135 (100.0%) | 198/198 (100.0%) | 333/333 (100.0%) |

## Physicochemical and toxicity coverage

Physicochemical and toxicity fields are retained in the rich flat records but are not projected into the current 48-column matrix. Adding them to the matrix would be a schema change, so this release reports their new-record coverage separately. A row-level old-versus-new comparison is not claimed because the original annotation layer is not normalized one-to-one with the 135 feature rows.

| Rich-record field | New-record coverage |
| --- | ---: |
| Any physicochemical measurement | 183/198 (92.4%) |
| Particle size (any method) | 179/198 (90.4%) |
| PDI | 166/198 (83.8%) |
| Encapsulation efficiency | 173/198 (87.4%) |
| Zeta potential | 3/198 (1.5%) |
| Apparent pKa | 3/198 (1.5%) |
| Morphology | 2/198 (1.0%) |
| Stability | 2/198 (1.0%) |
| Any toxicity block | 16/198 (8.1%) |
| Any toxicity detail beyond reported flag | 13/198 (6.6%) |

Particle size, PDI, and encapsulation efficiency are well represented in the new records because the Xu screen includes per-formulation characterization. The remaining physicochemical block is sparse: zeta potential and apparent pKa each cover only 3/198 new records, while morphology and stability each cover 2/198. Toxicity is the largest evidence gap, with any detailed toxicity information in 13/198 new records (6.6%). Missing values were not inferred.

## Coverage limitations and open sources

- The two Xue 2022 rows remain `partial_pending_main_text`; efficacy and numeric ALT/AST values are not backfilled from figures.
- Ramishetti 2020, Zhu 2026, and Dacoba 2025 remain paywalled source stubs and do not contribute matrix rows.
- Chappell 2024 composition remains null. Breda 2023 is analog support only and was not copied into those records.
- Figure-only efficacy for Chander, Peng, Zhao, and Iida remains null. The only approved figure estimates are the user-confirmed PRELIVE fields.
- Zero-filled one-hot columns are structurally complete, but rare positive classes can still be statistically weak. Use prevalence and paper-grouped validation in addition to this availability report.
