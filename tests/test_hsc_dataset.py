"""Tests for HSC fine-tuning dataset curation."""

from __future__ import annotations

import json
from pathlib import Path

from external_data.hsc_dataset import (
    HscDataset,
    HscRecord,
    build_hsc_dataset,
    classify_efficacy,
    parse_annotation,
    parse_approx,
)


class TestClassifyEfficacy:
    """Tests for efficacy class thresholds."""

    def test_high(self) -> None:
        assert classify_efficacy(50.0) == "high"

    def test_medium(self) -> None:
        assert classify_efficacy(20.0) == "medium"

    def test_low(self) -> None:
        assert classify_efficacy(5.0) == "low"

    def test_boundary_30(self) -> None:
        assert classify_efficacy(30.0) == "medium"

    def test_none(self) -> None:
        assert classify_efficacy(None) == ""


class TestParseApprox:
    """Tests for approximate value parsing."""

    def test_tilde(self) -> None:
        assert parse_approx("~30%") == 30.0

    def test_range(self) -> None:
        assert parse_approx("50-80%") == 65.0

    def test_minimal(self) -> None:
        assert parse_approx("minimal") == 0.0

    def test_plain_number(self) -> None:
        assert parse_approx("90") == 90.0

    def test_intermediate_text(self) -> None:
        result = parse_approx("intermediate (estimated ~60% from figure)")
        # Contains non-numeric text, should return None
        assert result is None or result == 60.0

    def test_not_effective(self) -> None:
        assert parse_approx("not effective") == 0.0


def _breda_fixture() -> dict[str, object]:
    """Minimal Breda-style annotation."""
    return {
        "formulations": [{
            "formulation_name": "CD117-LNP",
            "ionizable_lipid": {"name": "MC3"},
            "helper_lipid": {"name": "DSPC"},
            "peg_lipid": {"name": "DMG-PEG", "chain_length": "C14"},
            "molar_ratios": {
                "ionizable_percent": 50, "helper_percent": 10,
                "cholesterol_percent": 38.5, "peg_percent": 1.5,
            },
            "targeting": {
                "strategy": "antibody_conjugated",
                "target_receptor": "CD117", "antibody_clone": "2B8",
            },
        }],
        "experiments": [{
            "formulation_name": "CD117-LNP", "experiment_id": "E1",
            "payload": {"type": "mRNA", "specific_cargo": "Cre"},
            "model": {"system": "in_vivo", "species": "mouse", "strain": "Ai14"},
            "dosing": {"dose_mg_per_kg": 1.0, "route": "IV"},
            "efficacy": {
                "hsc_transfection_percent": 55,
                "editing_efficiency_percent": 55, "hsc_definition": "LSK",
            },
            "biodistribution": {"bone_marrow_percent": 55, "liver_percent": 76},
        }],
    }


def _shi_fixture() -> dict[str, object]:
    """Minimal Shi-style annotation."""
    return {
        "formulations": [
            {
                "formulation_id": "F5_ALC0315_C14PEG",
                "ionizable_lipid": {"name": "ALC-0315"},
                "peg_lipid": {"name": "DMG-PEG", "alkyl_chain": "C14"},
                "helper_lipid": {"name": "DSPC"},
                "molar_ratios": {
                    "ionizable_percent": 50, "helper_percent": 10,
                    "cholesterol_percent": 38, "peg_percent": 1.5,
                },
                "targeting": {"strategy": "antibody_conjugated"},
            },
            {
                "formulation_id": "F7_ALC0315_C18PEG",
                "ionizable_lipid": {"name": "ALC-0315"},
                "peg_lipid": {"name": "DSG-PEG", "alkyl_chain": "C18"},
                "helper_lipid": {"name": "DSPC"},
                "molar_ratios": {
                    "ionizable_percent": 50, "cholesterol_percent": 38,
                    "peg_percent": 1.5,
                },
                "targeting": {"strategy": "antibody_conjugated"},
            },
        ],
        "experiments": [{
            "experiment_id": "E2",
            "formulations_tested": [
                "F5_ALC0315_C14PEG", "F7_ALC0315_C18PEG"
            ],
            "payload": {"type": "siRNA", "specific_cargo": "siCD45"},
            "model_system": {
                "species": "mouse", "strain": "C57BL/6",
                "hspc_definition": "LSK",
            },
            "dosing": {"dose_mg_per_kg": 1.0, "route": "IV"},
            "primary_outcome": {
                "unit": "% uptake",
                "values": {"DMG_PEG_C14": "~30%", "DSG_PEG_C18": "~90%"},
            },
        }],
    }


def _kim_fixture() -> dict[str, object]:
    """Minimal Kim screen-style annotation."""
    return {
        "total_formulated": 3, "with_bm_delivery": 2,
        "full_composition_known": 1,
        "partial_composition_known": 2,
        "formulations": [
            {
                "lnp_name": "LNP67",
                "ionizable_lipid": "PPZ-A10",
                "helper_lipid_name": "DOTAP",
                "peg_lipid_name": "C14PEG2000",
                "peg_chain": "C14",
                "ionizable_mol_percent": 35,
                "cholesterol_mol_percent": 47.5,
                "peg_mol_percent": 2.5,
                "helper_mol_percent": 15,
                "composition_confidence": "HIGH",
                "bm_normalized_bc": 13,
                "liver_ec_normalized_bc": 5,
                "bm_delivery_class": "high",
            },
            {
                "lnp_name": "LNP1",
                "ionizable_lipid": "PPZ-A10",
                "helper_lipid_name": "DDAB",
                "peg_lipid_name": "C14PEG2000",
                "peg_chain": "C14",
                "composition_confidence": "PARTIAL",
                "bm_normalized_bc": 0.2,
                "bm_delivery_class": "background",
            },
            {
                "lnp_name": "LNP99",
                "ionizable_lipid": "PPZ-A10",
                "helper_lipid_name": "DSPC",
                "peg_lipid_name": "C18PEG2000",
                "peg_chain": "C18",
                "composition_confidence": "PARTIAL",
                "bm_delivery_class": "not_measured",
            },
        ],
    }


class TestBredaParsing:
    """Tests for Breda-style annotation parsing."""

    def test_basic(self, tmp_path: Path) -> None:
        path = tmp_path / "breda.json"
        path.write_text(json.dumps(_breda_fixture()))
        records = parse_annotation(path, "breda_2023")
        assert len(records) == 1
        r = records[0]
        assert r.hsc_transfection_percent == 55
        assert r.hsc_efficacy_class == "high"
        assert r.paired_biodistribution is True
        assert r.bone_marrow_percent == 55


class TestShiParsing:
    """Tests for Shi-style annotation parsing."""

    def test_key_mapping(self, tmp_path: Path) -> None:
        path = tmp_path / "shi.json"
        path.write_text(json.dumps(_shi_fixture()))
        records = parse_annotation(path, "shi_2023")
        assert len(records) == 2
        by_id = {r.formulation_id: r for r in records}
        assert by_id["F5_ALC0315_C14PEG"].hsc_transfection_percent == 30.0
        assert by_id["F7_ALC0315_C18PEG"].hsc_transfection_percent == 90.0

    def test_efficacy_class(self, tmp_path: Path) -> None:
        path = tmp_path / "shi.json"
        path.write_text(json.dumps(_shi_fixture()))
        records = parse_annotation(path, "shi_2023")
        by_id = {r.formulation_id: r for r in records}
        assert by_id["F5_ALC0315_C14PEG"].hsc_efficacy_class == "medium"
        assert by_id["F7_ALC0315_C18PEG"].hsc_efficacy_class == "high"

    def test_peg_chain(self, tmp_path: Path) -> None:
        path = tmp_path / "shi.json"
        path.write_text(json.dumps(_shi_fixture()))
        records = parse_annotation(path, "shi_2023")
        by_id = {r.formulation_id: r for r in records}
        assert by_id["F5_ALC0315_C14PEG"].peg_chain_length == "C14"
        assert by_id["F7_ALC0315_C18PEG"].peg_chain_length == "C18"


class TestKimParsing:
    """Tests for Kim screen-style parsing."""

    def test_screen_entries(self, tmp_path: Path) -> None:
        path = tmp_path / "kim.json"
        path.write_text(json.dumps(_kim_fixture()))
        records = parse_annotation(path, "kim_2024")
        # LNP99 is not_measured, so only 2 records
        assert len(records) == 2

    def test_delivery_class_mapping(self, tmp_path: Path) -> None:
        path = tmp_path / "kim.json"
        path.write_text(json.dumps(_kim_fixture()))
        records = parse_annotation(path, "kim_2024")
        by_id = {r.formulation_id: r for r in records}
        assert by_id["LNP67"].hsc_efficacy_class == "high"
        assert by_id["LNP1"].hsc_efficacy_class == "low"  # background→low

    def test_intrinsic_tropism(self, tmp_path: Path) -> None:
        path = tmp_path / "kim.json"
        path.write_text(json.dumps(_kim_fixture()))
        records = parse_annotation(path, "kim_2024")
        for r in records:
            assert r.targeting_strategy == "intrinsic_tropism"

    def test_composition_confidence(self, tmp_path: Path) -> None:
        path = tmp_path / "kim.json"
        path.write_text(json.dumps(_kim_fixture()))
        records = parse_annotation(path, "kim_2024")
        by_id = {r.formulation_id: r for r in records}
        assert by_id["LNP67"].composition_confidence == "HIGH"
        assert by_id["LNP1"].composition_confidence == "PARTIAL"


class TestBuildDataset:
    """Tests for full dataset building."""

    def test_build(self, tmp_path: Path) -> None:
        ann_dir = tmp_path / "ann"
        ann_dir.mkdir()
        (ann_dir / "breda.json").write_text(json.dumps(_breda_fixture()))
        (ann_dir / "shi.json").write_text(json.dumps(_shi_fixture()))
        (ann_dir / "kim.json").write_text(json.dumps(_kim_fixture()))
        ds = build_hsc_dataset(ann_dir, output_dir=tmp_path / "out")
        assert ds.total_records == 5  # 1 breda + 2 shi + 2 kim
        assert (tmp_path / "out" / "hsc_curated.parquet").exists()

    def test_parquet_columns(self, tmp_path: Path) -> None:
        ann_dir = tmp_path / "ann"
        ann_dir.mkdir()
        (ann_dir / "b.json").write_text(json.dumps(_breda_fixture()))
        ds = build_hsc_dataset(ann_dir)
        df = ds.to_dataframe()
        for col in ["targeting_strategy", "hsc_efficacy_class",
                     "peg_chain_length", "composition_confidence"]:
            assert col in df.columns
        assert "descriptors" not in df.columns


class TestModels:
    """Tests for Pydantic model behavior."""

    def test_defaults(self) -> None:
        r = HscRecord()
        assert r.source == "hsc_curated"

    def test_roundtrip(self) -> None:
        ds = HscDataset(records=[HscRecord(paper="t")], total_records=1)
        ds2 = HscDataset.model_validate_json(ds.model_dump_json())
        assert ds2.total_records == 1


class TestBredaIgGExtraction:
    """Tests for IgG control value extraction from text."""

    def test_vs_pattern(self, tmp_path: Path) -> None:
        fixture = _breda_fixture()
        # Add other_metric with "vs X%" pattern
        fixture["experiments"][0]["efficacy"]["other_metric"] = (  # type: ignore[index]
            "3-fold higher than IgG control (55% vs 19%)"
        )
        # Add IgG formulation
        fixture["formulations"].append({  # type: ignore[attr-defined]
            "formulation_name": "IgG/LNP",
            "ionizable_lipid": {"name": "MC3"},
            "targeting": {"strategy": "none"},
            "molar_ratios": {"ionizable_percent": 50},
        })
        path = tmp_path / "breda.json"
        path.write_text(json.dumps(fixture))
        records = parse_annotation(path, "breda_2023")
        igg_recs = [r for r in records if r.formulation_id == "IgG/LNP"]
        assert len(igg_recs) == 1
        assert igg_recs[0].hsc_transfection_percent == 19.0
        assert igg_recs[0].hsc_efficacy_class == "medium"


class TestBredaPumaExtraction:
    """Tests for PUMA LSK decrease extraction."""

    def test_puma_lsk(self, tmp_path: Path) -> None:
        fixture = _breda_fixture()
        fixture["experiments"].append({  # type: ignore[attr-defined]
            "formulation_name": "CD117-LNP",
            "experiment_id": "10_in_vivo_PUMA_conditioning",
            "payload": {"type": "mRNA", "specific_cargo": "PUMA"},
            "model": {"species": "mouse", "strain": "C57BL/6"},
            "dosing": {"dose_mg_per_kg": 0.25, "route": "IV"},
            "efficacy": {
                "other_metric": "71% decrease in LSK frequency at 6 days"
            },
            "biodistribution": {},
        })
        path = tmp_path / "breda.json"
        path.write_text(json.dumps(fixture))
        records = parse_annotation(path, "breda_2023")
        puma = [r for r in records if "LSK_decrease" in r.experiment_id]
        assert len(puma) == 1
        assert puma[0].hsc_transfection_percent == 71.0
        assert puma[0].expt_unit == "pct_lsk_decrease"


class TestKimExperiments:
    """Tests for Kim experiment-level parsing."""

    def _kim_exp_fixture(self) -> dict[str, object]:
        return {
            "formulations": [{
                "formulation_id": "F1_LNP67",
                "formulation_name": "LNP67",
                "ionizable_lipid": {"name": "PPZ-A10"},
                "helper_lipid": {"name": "DOTAP"},
                "peg_lipid": {"name": "C14PEG2000", "chain_length": "C14"},
                "molar_ratios": {
                    "ionizable_percent": 35, "helper_percent": 15,
                    "cholesterol_percent": 47.5, "peg_percent": 2.5,
                },
                "targeting": {"strategy": "intrinsic_tropism"},
            }],
            "experiments": [{
                "experiment_id": "E3_dose_response",
                "formulations_tested": ["F1_LNP67"],
                "payload": {"type": "mRNA", "specific_cargo": "aVHH"},
                "model_system": {"species": "mouse", "strain": "C57BL/6J"},
                "dosing": {"route": "IV"},
                "primary_outcome": {
                    "unit": "% aVHH+ HSC",
                    "values": {"0.5_mg_kg": 12, "1.0_mg_kg": 23, "2.0_mg_kg": 35},
                },
            }],
        }

    def test_dose_response(self, tmp_path: Path) -> None:
        path = tmp_path / "kim_2024_experiments.json"
        path.write_text(json.dumps(self._kim_exp_fixture()))
        records = parse_annotation(path, "kim_2024")
        assert len(records) == 3
        doses = {r.dose_mg_per_kg for r in records}
        assert doses == {0.5, 1.0, 2.0}

    def test_source_and_targeting(self, tmp_path: Path) -> None:
        path = tmp_path / "kim_2024_experiments.json"
        path.write_text(json.dumps(self._kim_exp_fixture()))
        records = parse_annotation(path, "kim_2024")
        for r in records:
            assert r.source == "kim_2024_experiments"
            assert r.targeting_strategy == "intrinsic_tropism"

    def test_efficacy_classes(self, tmp_path: Path) -> None:
        path = tmp_path / "kim_2024_experiments.json"
        path.write_text(json.dumps(self._kim_exp_fixture()))
        records = parse_annotation(path, "kim_2024")
        by_dose = {r.dose_mg_per_kg: r for r in records}
        assert by_dose[0.5].hsc_efficacy_class == "medium"
        assert by_dose[1.0].hsc_efficacy_class == "medium"
        assert by_dose[2.0].hsc_efficacy_class == "high"


class TestBredaIgGPattern2:
    """Tests for IgG 'X% (dose)' pattern extraction."""

    def test_dose_pattern(self, tmp_path: Path) -> None:
        fixture = _breda_fixture()
        fixture["experiments"][0]["efficacy"]["other_metric"] = (  # type: ignore[index]
            "IgG control: 13.5% (0.1ug) and 20% (1ug)"
        )
        fixture["formulations"].append({  # type: ignore[attr-defined]
            "formulation_name": "IgG/LNP",
            "ionizable_lipid": {"name": "MC3"},
            "targeting": {"strategy": "none"},
            "molar_ratios": {"ionizable_percent": 50},
        })
        path = tmp_path / "breda.json"
        path.write_text(json.dumps(fixture))
        records = parse_annotation(path, "breda_2023")
        igg = [r for r in records if "IgG" in r.formulation_id]
        assert len(igg) == 2
        vals = {r.hsc_transfection_percent for r in igg}
        assert vals == {13.5, 20.0}


class TestAssayCategory:
    """Tests for assay category inference."""

    def test_breda_editing(self, tmp_path: Path) -> None:
        path = tmp_path / "b.json"
        path.write_text(json.dumps(_breda_fixture()))
        records = parse_annotation(path, "breda_2023")
        # Breda fixture has Cre payload → editing
        assert records[0].assay_category == "editing"

    def test_kim_screen_barcode(self, tmp_path: Path) -> None:
        path = tmp_path / "k.json"
        path.write_text(json.dumps(_kim_fixture()))
        records = parse_annotation(path, "kim_2024")
        for r in records:
            assert r.assay_category == "barcode_delivery"

    def test_all_records_have_category(self, tmp_path: Path) -> None:
        ann_dir = tmp_path / "ann"
        ann_dir.mkdir()
        (ann_dir / "b.json").write_text(json.dumps(_breda_fixture()))
        (ann_dir / "s.json").write_text(json.dumps(_shi_fixture()))
        (ann_dir / "k.json").write_text(json.dumps(_kim_fixture()))
        ds = build_hsc_dataset(ann_dir)
        for r in ds.records:
            assert r.assay_category != "", f"Missing assay_category for {r.experiment_id}"


class TestSmilesLookup:
    """Tests for ionizable lipid SMILES lookup."""

    def test_known_lipids(self) -> None:
        from external_data.descriptors import lookup_il_smiles
        for name in ["ALC-0315", "DLin-MC3-DMA", "SM-102", "cKK-E12", "Lipid 5"]:
            smi = lookup_il_smiles(name)
            assert smi is not None, f"Missing SMILES for {name}"

    def test_rdkit_valid(self) -> None:
        from rdkit import Chem

        from external_data.descriptors import KNOWN_IL_SMILES
        for name, smi in KNOWN_IL_SMILES.items():
            mol = Chem.MolFromSmiles(smi)
            assert mol is not None, f"Invalid SMILES for {name}: {smi}"

    def test_shi_records_get_descriptors(self, tmp_path: Path) -> None:
        path = tmp_path / "shi.json"
        path.write_text(json.dumps(_shi_fixture()))
        records = parse_annotation(path, "shi_2023")
        alc_recs = [r for r in records if "ALC-0315" in r.il_name]
        assert len(alc_recs) > 0
        for r in alc_recs:
            assert r.il_smiles != "", f"Missing SMILES for {r.il_name}"
            assert r.rdkit_valid is True
            assert r.descriptors.molecular_weight is not None
