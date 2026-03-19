"""Tests for the extraction evaluator."""

from __future__ import annotations

from pathlib import Path

from pubmed_agent.evaluator import (
    EvaluationReport,
    evaluate_directory,
    evaluate_paper,
    finalise_report,
    fuzzy_match_score,
    match_experiments,
    match_formulations,
    numerics_match,
    report_to_dict,
    strings_match,
)
from pubmed_agent.extractor import (
    Biodistribution,
    Dosing,
    Efficacy,
    ExperimentExtraction,
    ExperimentModel,
    ExtractionResult,
    FormulationExtraction,
    IonizableLipid,
    LabelForML,
    MolarRatios,
    PaperMetadata,
    Payload,
    Physicochemical,
    Targeting,
    load_extraction_file,
)

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# String matching
# ---------------------------------------------------------------------------


class TestStringMatching:
    """Tests for string comparison utilities."""

    def test_exact_match(self) -> None:
        assert strings_match("DSPC", "DSPC")

    def test_case_insensitive(self) -> None:
        assert strings_match("dspc", "DSPC")

    def test_synonym_match(self) -> None:
        assert strings_match("DLin-MC3-DMA", "MC3")
        assert strings_match("mc3", "DLin-MC3-DMA")

    def test_no_match(self) -> None:
        assert not strings_match("DSPC", "DOPE")

    def test_synonym_dmg_peg(self) -> None:
        assert strings_match("DMG-PEG2000", "DMG-PEG-2000")

    def test_fuzzy_score(self) -> None:
        score = fuzzy_match_score("CD117-LNP", "CD117-LNP-v2")
        assert score > 0.7

    def test_fuzzy_low_score(self) -> None:
        score = fuzzy_match_score("CD117-LNP", "something-else")
        assert score < 0.5


# ---------------------------------------------------------------------------
# Numeric matching
# ---------------------------------------------------------------------------


class TestNumericMatching:
    """Tests for numeric comparison with tolerance."""

    def test_exact_match(self) -> None:
        assert numerics_match(100.0, 100.0)

    def test_within_tolerance(self) -> None:
        assert numerics_match(102.0, 100.0)  # 2% error

    def test_outside_tolerance(self) -> None:
        assert not numerics_match(110.0, 100.0)  # 10% error

    def test_both_none(self) -> None:
        assert numerics_match(None, None)

    def test_one_none(self) -> None:
        assert not numerics_match(None, 100.0)
        assert not numerics_match(100.0, None)

    def test_zero_truth(self) -> None:
        assert numerics_match(0.0, 0)
        assert not numerics_match(1.0, 0)


# ---------------------------------------------------------------------------
# Formulation matching
# ---------------------------------------------------------------------------


class TestFormulationMatching:
    """Tests for formulation pairing logic."""

    def test_exact_name_match(self) -> None:
        preds = [FormulationExtraction(formulation_name="LNP-A")]
        truths = [FormulationExtraction(formulation_name="LNP-A")]
        pairs = match_formulations(preds, truths)
        assert len(pairs) == 1
        assert pairs[0][1] is not None

    def test_fuzzy_name_match(self) -> None:
        preds = [FormulationExtraction(formulation_name="CD117-LNP")]
        truths = [FormulationExtraction(formulation_name="CD117 LNP")]
        pairs = match_formulations(preds, truths)
        assert pairs[0][1] is not None

    def test_no_match(self) -> None:
        preds = [FormulationExtraction(formulation_name="CD117-targeted")]
        truths = [FormulationExtraction(formulation_name="untargeted-control")]
        pairs = match_formulations(preds, truths)
        assert pairs[0][1] is None

    def test_multiple_formulations(self) -> None:
        preds = [
            FormulationExtraction(formulation_name="LNP-A"),
            FormulationExtraction(formulation_name="LNP-B"),
        ]
        truths = [
            FormulationExtraction(formulation_name="LNP-B"),
            FormulationExtraction(formulation_name="LNP-A"),
        ]
        pairs = match_formulations(preds, truths)
        assert all(t is not None for _, t in pairs)


# ---------------------------------------------------------------------------
# Experiment matching
# ---------------------------------------------------------------------------


class TestExperimentMatching:
    """Tests for experiment pairing logic."""

    def test_exact_match(self) -> None:
        preds = [
            ExperimentExtraction(
                formulation_name="LNP-A",
                payload=Payload(type="mRNA"),
                model=ExperimentModel(system="in_vivo"),
            )
        ]
        truths = [
            ExperimentExtraction(
                formulation_name="LNP-A",
                payload=Payload(type="mRNA"),
                model=ExperimentModel(system="in_vivo"),
            )
        ]
        pairs = match_experiments(preds, truths)
        assert pairs[0][1] is not None

    def test_different_payload_no_match(self) -> None:
        preds = [
            ExperimentExtraction(
                formulation_name="LNP-A",
                payload=Payload(type="mRNA"),
                model=ExperimentModel(system="in_vivo"),
            )
        ]
        truths = [
            ExperimentExtraction(
                formulation_name="LNP-A",
                payload=Payload(type="siRNA"),
                model=ExperimentModel(system="in_vivo"),
            )
        ]
        pairs = match_experiments(preds, truths)
        assert pairs[0][1] is None


# ---------------------------------------------------------------------------
# Full evaluation
# ---------------------------------------------------------------------------


class TestEvaluatePaper:
    """Test evaluate_paper with known inputs."""

    def _make_pair(self) -> tuple[ExtractionResult, ExtractionResult]:
        """Create a pred/truth pair with known differences."""
        formulation = FormulationExtraction(
            formulation_name="CD117-LNP",
            ionizable_lipid=IonizableLipid(name="C12-200"),
            molar_ratios=MolarRatios(ratio_string="50:10:38.5:1.5", ionizable_percent=50.0),
            physicochemical=Physicochemical(particle_size_nm=100.0, pdi=0.15),
            targeting=Targeting(strategy="antibody_conjugated", target_receptor="CD117"),
        )
        experiment = ExperimentExtraction(
            formulation_name="CD117-LNP",
            payload=Payload(type="mRNA", specific_cargo="Cre"),
            model=ExperimentModel(system="in_vivo", species="mouse"),
            dosing=Dosing(dose_mg_per_kg=1.0, route="IV"),
            efficacy=Efficacy(hsc_transfection_percent=30.0, hsc_definition="LSK"),
            biodistribution=Biodistribution(bone_marrow_percent=25.0, liver_percent=60.0),
        )
        truth = ExtractionResult(
            paper_metadata=PaperMetadata(pmid="37499029"),
            formulations=[formulation],
            experiments=[experiment],
            label_for_ml=LabelForML(hsc_efficacy_class="medium"),
        )

        # Pred with slight differences
        pred_f = formulation.model_copy(deep=True)
        pred_f.physicochemical.particle_size_nm = 102.0  # within tolerance
        pred_e = experiment.model_copy(deep=True)
        pred_e.efficacy.hsc_transfection_percent = 31.0  # within tolerance
        pred = ExtractionResult(
            paper_metadata=PaperMetadata(pmid="37499029"),
            formulations=[pred_f],
            experiments=[pred_e],
            label_for_ml=LabelForML(hsc_efficacy_class="medium"),
        )
        return pred, truth

    def test_perfect_precision_recall(self) -> None:
        pred, truth = self._make_pair()
        report = EvaluationReport()
        evaluate_paper(pred, truth, report)
        report = finalise_report(report)
        assert report.formulation_precision == 1.0
        assert report.formulation_recall == 1.0
        assert report.experiment_precision == 1.0
        assert report.experiment_recall == 1.0

    def test_field_accuracy_within_tolerance(self) -> None:
        pred, truth = self._make_pair()
        report = EvaluationReport()
        evaluate_paper(pred, truth, report)
        finalise_report(report)
        # particle_size: 102 vs 100 = 2% error, should be correct
        size_acc = report.field_accuracies.get("physicochemical.particle_size_nm")
        assert size_acc is not None
        assert size_acc.correct == 1

    def test_critical_field_report(self) -> None:
        pred, truth = self._make_pair()
        report = EvaluationReport()
        evaluate_paper(pred, truth, report)
        finalise_report(report)
        assert "ionizable_lipid.name" in report.critical_field_accuracies
        assert "targeting.strategy" in report.critical_field_accuracies

    def test_report_to_dict(self) -> None:
        pred, truth = self._make_pair()
        report = EvaluationReport()
        evaluate_paper(pred, truth, report)
        finalise_report(report)
        d = report_to_dict(report)
        assert d["num_papers"] == 1
        assert "field_accuracies" in d
        assert "critical_fields" in d

    def test_zero_recall_when_missed(self) -> None:
        truth = ExtractionResult(
            paper_metadata=PaperMetadata(pmid="test"),
            formulations=[FormulationExtraction(formulation_name="LNP-A")],
        )
        pred = ExtractionResult(
            paper_metadata=PaperMetadata(pmid="test"),
            formulations=[],
        )
        report = EvaluationReport()
        evaluate_paper(pred, truth, report)
        finalise_report(report)
        assert report.formulation_recall == 0.0


# ---------------------------------------------------------------------------
# Directory evaluation
# ---------------------------------------------------------------------------


class TestEvaluateDirectory:
    """Test evaluate_directory with fixture files."""

    def test_with_fixture(self, tmp_path: Path) -> None:
        # Create pred and truth directories with same content
        pred_dir = tmp_path / "preds"
        truth_dir = tmp_path / "truth"
        pred_dir.mkdir()
        truth_dir.mkdir()

        fixture = load_extraction_file(FIXTURES / "sample_extraction.json")
        data = fixture.model_dump_json(indent=2)
        (pred_dir / "37499029.json").write_text(data)
        (truth_dir / "breda_2023.json").write_text(data)

        report = evaluate_directory(pred_dir, truth_dir)
        assert report.num_papers == 1
        assert report.formulation_precision == 1.0
