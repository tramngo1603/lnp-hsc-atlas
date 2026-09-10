# Atlas Coverage Report

Generated from `data/features/hsc_features.parquet`. The matrix contains 331 rows across 18 papers and 48 columns.

## Method

Coverage is the count of non-null cells. Numeric zero and boolean-style zero are valid populated values, especially in one-hot encodings. Coverage therefore measures availability, not feature prevalence. Data integrity and logical consistency are verified by `scripts/audit_combined_atlas.py`.

## Summary

- 30/48 columns are complete across all 331 rows.
- `label_boundary_case` marks four Lian 2024 rows whose exact 30% measurements retain their established `high` labels. The current rule is strictly `high >30%`.
- The supervised target is populated for 315/331 rows (95.2%). The 16 unlabeled rows remain in the atlas but must be excluded from supervised training.
- Core ionizable/helper/cholesterol composition is available for 248/331 rows (74.9%).
- Dose is available for 244/331 rows (73.7%). Absolute per-mouse doses are intentionally not converted to mg/kg.
- All eight ionizable-lipid descriptor columns cover 154/331 (46.5%). Missing descriptors reflect proprietary or unverified lipid identities, not a failed calculation.

## Coverage by matrix column

| Column | Group | Coverage |
| --- | --- | ---: |
| `source` | metadata | 331/331 (100.0%) |
| `paper` | metadata | 331/331 (100.0%) |
| `formulation_id` | metadata | 331/331 (100.0%) |
| `experiment_id` | metadata | 331/331 (100.0%) |
| `assay_category` | metadata | 331/331 (100.0%) |
| `composition_confidence` | metadata | 331/331 (100.0%) |
| `ionizable_mol_pct` | composition | 248/331 (74.9%) |
| `helper_mol_pct` | composition | 248/331 (74.9%) |
| `cholesterol_mol_pct` | composition | 248/331 (74.9%) |
| `peg_mol_pct` | composition | 242/331 (73.1%) |
| `il_to_helper_ratio` | engineered ratio | 248/331 (74.9%) |
| `il_to_chol_ratio` | engineered ratio | 248/331 (74.9%) |
| `chol_to_helper_ratio` | engineered ratio | 248/331 (74.9%) |
| `peg_chain_numeric` | composition | 301/331 (90.9%) |
| `dose_mg_per_kg` | dose | 244/331 (73.7%) |
| `targeting_encoded` | encoding | 331/331 (100.0%) |
| `helper_is_cationic` | encoding | 331/331 (100.0%) |
| `species_mouse` | encoding | 331/331 (100.0%) |
| `species_nhp` | encoding | 331/331 (100.0%) |
| `species_human` | encoding | 331/331 (100.0%) |
| `assay_barcode_delivery` | encoding | 331/331 (100.0%) |
| `assay_depletion` | encoding | 331/331 (100.0%) |
| `assay_editing` | encoding | 331/331 (100.0%) |
| `assay_knockdown` | encoding | 331/331 (100.0%) |
| `assay_protein_expression` | encoding | 331/331 (100.0%) |
| `hl_dspc` | encoding | 331/331 (100.0%) |
| `hl_dope` | encoding | 331/331 (100.0%) |
| `hl_dotap` | encoding | 331/331 (100.0%) |
| `hl_ddab` | encoding | 331/331 (100.0%) |
| `hl_dotma` | encoding | 331/331 (100.0%) |
| `hl_epc` | encoding | 331/331 (100.0%) |
| `receptor_cd117` | encoding | 331/331 (100.0%) |
| `receptor_cd45` | encoding | 331/331 (100.0%) |
| `clone_2b8` | encoding | 331/331 (100.0%) |
| `clone_ack2` | encoding | 331/331 (100.0%) |
| `clone_igg` | encoding | 331/331 (100.0%) |
| `il_molecular_weight` | IL descriptor | 154/331 (46.5%) |
| `il_logp` | IL descriptor | 154/331 (46.5%) |
| `il_tpsa` | IL descriptor | 154/331 (46.5%) |
| `il_hbd` | IL descriptor | 154/331 (46.5%) |
| `il_hba` | IL descriptor | 154/331 (46.5%) |
| `il_rotatable_bonds` | IL descriptor | 154/331 (46.5%) |
| `il_num_rings` | IL descriptor | 154/331 (46.5%) |
| `il_heavy_atom_count` | IL descriptor | 154/331 (46.5%) |
| `target` | label | 315/331 (95.2%) |
| `metric_type` | metric metadata | 331/331 (100.0%) |
| `covalent_lipid_mol_pct` | composition | 331/331 (100.0%) |
| `label_boundary_case` | metadata | 331/331 (100.0%) |

## Physicochemical and toxicity coverage

Physicochemical and toxicity fields are retained in the rich flat records but are not projected into the current 48-column matrix. Adding them to the matrix would be a schema change, so their coverage is reported for the normalized rich-record collection separately.

| Rich-record field | Coverage |
| --- | ---: |
| Any physicochemical measurement | 182/196 (92.9%) |
| Particle size (any method) | 179/196 (91.3%) |
| PDI | 166/196 (84.7%) |
| Encapsulation efficiency | 173/196 (88.3%) |
| Zeta potential | 3/196 (1.5%) |
| Apparent pKa | 3/196 (1.5%) |
| Morphology | 2/196 (1.0%) |
| Stability | 1/196 (0.5%) |
| Any toxicity block | 14/196 (7.1%) |
| Any toxicity detail beyond reported flag | 11/196 (5.6%) |

Particle size, PDI, and encapsulation efficiency are well represented in the rich records because the Xu screen includes per-formulation characterization. The remaining physicochemical block is sparse: zeta potential covers 3/196 records, apparent pKa covers 3/196, morphology covers 2/196, and stability covers 1/196. Toxicity is the largest evidence gap, with any detailed toxicity information in 11/196 records (5.6%). Missing values were not inferred.

## Coverage limitations

- Chappell 2024 composition remains null. Breda 2023 is analog support only and was not copied into those records.
- Figure-only efficacy for Chander, Peng, Zhao, and Iida remains null. The only approved figure estimates are the user-confirmed PRELIVE fields.
- Zero-filled one-hot columns are structurally complete, but rare positive classes can still be statistically weak. Use prevalence and paper-grouped validation in addition to this availability report.
