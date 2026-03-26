"""Build feature matrix from annotation JSONs + existing curated data.

Combines the existing feature_matrix.py pipeline with Lian integration,
outputs data/features/hsc_features.parquet + .csv.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from lnp_optimizer.feature_matrix import build_feature_matrix  # noqa: E402
from lnp_optimizer.integrate_lian import integrate  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(message)s")

_ROOT = Path(__file__).resolve().parent.parent
_HSC_PATH = _ROOT / "data" / "hsc" / "hsc_curated.parquet"
_OUT_PATH = _ROOT / "data" / "features" / "hsc_features.parquet"


def main() -> int:
    """Build the feature matrix end-to-end."""
    print("=" * 60)
    print("Building feature matrix")
    print("=" * 60)

    # Step 1: Build base matrix from curated HSC data (Breda, Shi, Kim)
    print("\n1. Building base matrix from hsc_curated.parquet...")
    df = build_feature_matrix(_HSC_PATH, _OUT_PATH)
    print(f"   Base matrix: {df.shape[0]} rows × {df.shape[1]} cols")

    # Step 2: Integrate Lian 2024
    print("\n2. Integrating Lian 2024...")
    df = integrate(save=True)
    print(f"   Combined: {df.shape[0]} rows × {df.shape[1]} cols")

    # Step 3: Fill IL molecular descriptors
    print("\n3. Filling IL molecular descriptors...")
    import pandas as pd
    df = pd.read_parquet(_OUT_PATH)

    # PPZ-A10 (Kim 80 rows) — RDKit exact MW from SMILES (CAS 2941268-67-1)
    kim_mask = df["paper"] == "kim_2024"
    ppz = {"il_molecular_weight": 902.90, "il_logp": 13.564, "il_tpsa": 71.16,
           "il_hbd": 2, "il_hba": 6, "il_rotatable_bonds": 50,
           "il_num_rings": 1, "il_heavy_atom_count": 64}
    for col, val in ppz.items():
        df.loc[kim_mask, col] = val

    # 5A2-SC8 (Lian 25 rows)
    lian_mask = df["paper"] == "lian_2024"
    sc8 = {"il_molecular_weight": 677.56, "il_logp": 10.84, "il_tpsa": 82.14,
           "il_hbd": 0, "il_hba": 7, "il_rotatable_bonds": 35,
           "il_num_rings": 0, "il_heavy_atom_count": 48}
    for col, val in sc8.items():
        df.loc[lian_mask, col] = val

    # ALC-0315 (Breda 9 rows)
    breda_mask = df["paper"] == "breda_2023"
    alc = {"il_molecular_weight": 710.18, "il_logp": 13.41, "il_tpsa": 73.56,
           "il_hbd": 0, "il_hba": 7, "il_rotatable_bonds": 39,
           "il_num_rings": 0, "il_heavy_atom_count": 50}
    for col, val in alc.items():
        df.loc[breda_mask, col] = val

    df.to_parquet(_OUT_PATH, index=False)
    df.to_csv(_OUT_PATH.with_suffix(".csv"), index=False)

    il_coverage = df["il_molecular_weight"].notna().sum()
    print(f"   IL descriptor coverage: {il_coverage}/{len(df)} ({il_coverage/len(df)*100:.0f}%)")

    # Summary
    print(f"\n{'='*60}")
    print(f"Feature matrix: {df.shape[0]} rows × {df.shape[1]} cols")
    print(f"Papers: {df['paper'].value_counts().to_dict()}")
    print(f"Target: {df['target'].value_counts().sort_index().to_dict()}")
    print(f"IL coverage: {il_coverage}/{len(df)}")
    print(f"Saved: {_OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
