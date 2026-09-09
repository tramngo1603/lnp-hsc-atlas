# Atlas Coverage Report

Generated from `data/features/hsc_features.parquet`. The matrix contains 333 rows across 19 papers and 48 columns.

## Method

Coverage is the count of non-null cells. Numeric zero and boolean-style zero are valid populated values, especially in one-hot encodings. Coverage therefore measures availability, not feature prevalence. Data integrity and logical consistency are verified by `scripts/audit_combined_atlas.py`.

## Summary

- 30/48 columns are complete across all 333 rows.
- `label_boundary_case` marks four Lian 2024 rows whose exact 30% measurements retain their established `high` labels. The current rule is strictly `high >30%`.
- The supervised target is populated for 315/333 rows (94.6%). The 18 unlabeled rows remain in the atlas but must be excluded from supervised training.
- Core ionizable/helper/cholesterol composition is available for 250/333 rows (75.1%).
- Dose is available for 246/333 rows (73.9%). Absolute per-mouse doses are intentionally not converted to mg/kg.
- All eight ionizable-lipid descriptor columns cover 154/333 (46.2%). Missing descriptors reflect proprietary or unverified lipid identities, not a failed calculation.

## Coverage by matrix column

| Column | Group | Coverage |
| --- | --- | ---: |
| `source` | metadata | 333/333 (100.0%) |
| `paper` | metadata | 333/333 (100.0%) |
| `formulation_id` | metadata | 333/333 (100.0%) |
| `experiment_id` | metadata | 333/333 (100.0%) |
| `assay_category` | metadata | 333/333 (100.0%) |
| `composition_confidence` | metadata | 333/333 (100.0%) |
| `ionizable_mol_pct` | composition | 250/333 (75.1%) |
| `helper_mol_pct` | composition | 250/333 (75.1%) |
| `cholesterol_mol_pct` | composition | 250/333 (75.1%) |
| `peg_mol_pct` | composition | 244/333 (73.3%) |
| `il_to_helper_ratio` | engineered ratio | 250/333 (75.1%) |
| `il_to_chol_ratio` | engineered ratio | 250/333 (75.1%) |
| `chol_to_helper_ratio` | engineered ratio | 250/333 (75.1%) |
| `peg_chain_numeric` | composition | 303/333 (91.0%) |
| `dose_mg_per_kg` | dose | 246/333 (73.9%) |
| `targeting_encoded` | encoding | 333/333 (100.0%) |
| `helper_is_cationic` | encoding | 333/333 (100.0%) |
| `species_mouse` | encoding | 333/333 (100.0%) |
| `species_nhp` | encoding | 333/333 (100.0%) |
| `species_human` | encoding | 333/333 (100.0%) |
| `assay_barcode_delivery` | encoding | 333/333 (100.0%) |
| `assay_depletion` | encoding | 333/333 (100.0%) |
| `assay_editing` | encoding | 333/333 (100.0%) |
| `assay_knockdown` | encoding | 333/333 (100.0%) |
| `assay_protein_expression` | encoding | 333/333 (100.0%) |
| `hl_dspc` | encoding | 333/333 (100.0%) |
| `hl_dope` | encoding | 333/333 (100.0%) |
| `hl_dotap` | encoding | 333/333 (100.0%) |
| `hl_ddab` | encoding | 333/333 (100.0%) |
| `hl_dotma` | encoding | 333/333 (100.0%) |
| `hl_epc` | encoding | 333/333 (100.0%) |
| `receptor_cd117` | encoding | 333/333 (100.0%) |
| `receptor_cd45` | encoding | 333/333 (100.0%) |
| `clone_2b8` | encoding | 333/333 (100.0%) |
| `clone_ack2` | encoding | 333/333 (100.0%) |
| `clone_igg` | encoding | 333/333 (100.0%) |
| `il_molecular_weight` | IL descriptor | 154/333 (46.2%) |
| `il_logp` | IL descriptor | 154/333 (46.2%) |
| `il_tpsa` | IL descriptor | 154/333 (46.2%) |
| `il_hbd` | IL descriptor | 154/333 (46.2%) |
| `il_hba` | IL descriptor | 154/333 (46.2%) |
| `il_rotatable_bonds` | IL descriptor | 154/333 (46.2%) |
| `il_num_rings` | IL descriptor | 154/333 (46.2%) |
| `il_heavy_atom_count` | IL descriptor | 154/333 (46.2%) |
| `target` | label | 315/333 (94.6%) |
| `metric_type` | metric metadata | 333/333 (100.0%) |
| `covalent_lipid_mol_pct` | composition | 333/333 (100.0%) |
| `label_boundary_case` | metadata | 333/333 (100.0%) |

## Physicochemical and toxicity coverage

Physicochemical and toxicity fields are retained in the rich flat records but are not projected into the current 48-column matrix. Adding them to the matrix would be a schema change, so their coverage is reported for the normalized rich-record collection separately.

| Rich-record field | Coverage |
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

Particle size, PDI, and encapsulation efficiency are well represented in the rich records because the Xu screen includes per-formulation characterization. The remaining physicochemical block is sparse: zeta potential and apparent pKa each cover only 3/198 records, while morphology and stability each cover 2/198. Toxicity is the largest evidence gap, with any detailed toxicity information in 13/198 records (6.6%). Missing values were not inferred.

## Coverage limitations and open sources

- The two Xue 2022 rows remain `partial_pending_main_text`; efficacy and numeric ALT/AST values are not backfilled from figures.
- Ramishetti 2020, Zhu 2026, and Dacoba 2025 remain paywalled source stubs and do not contribute matrix rows.
- Chappell 2024 composition remains null. Breda 2023 is analog support only and was not copied into those records.
- Figure-only efficacy for Chander, Peng, Zhao, and Iida remains null. The only approved figure estimates are the user-confirmed PRELIVE fields.
- Zero-filled one-hot columns are structurally complete, but rare positive classes can still be statistically weak. Use prevalence and paper-grouped validation in addition to this availability report.
