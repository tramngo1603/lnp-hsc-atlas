"""Tests for the LLM extraction pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from pubmed_agent.extractor import (
    ExtractionResult,
    FormulationExtraction,
    SectionIdentificationResult,
    build_pass2_content,
    extract_paper,
    load_extraction_file,
    parse_extraction_json,
)
from pubmed_agent.preprocessor import ProcessedPaper

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sample_paper() -> ProcessedPaper:
    return ProcessedPaper(
        pmid="37499029",
        title="In vivo HSC modification by mRNA delivery",
        authors=["Breda L", "Papp TE"],
        journal="Science",
        doi="10.1126/science.adi8798",
        pub_date="2023-07-28",
        abstract="We developed CD117-targeted LNPs...",
        sections={
            "abstract": "We developed CD117-targeted LNPs for HSC delivery.",
            "methods": "LNPs were formulated with C12-200:DOPE:Chol:PEG "
            "at 50:10:38.5:1.5 molar ratio. N/P ratio was 6.",
            "results": "CD117-LNP delivered Cre mRNA to 30% of LSK cells. "
            "Particle size was 100 nm with PDI 0.15.",
        },
        full_text_available=True,
    )


def _sample_result_json() -> str:
    return (FIXTURES / "sample_extraction.json").read_text()


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------


class TestExtractionModels:
    """Tests for Pydantic extraction schema."""

    def test_extraction_result_defaults(self) -> None:
        result = ExtractionResult()
        assert result.formulations == []
        assert result.experiments == []
        assert result.paper_metadata.pmid is None

    def test_formulation_defaults(self) -> None:
        f = FormulationExtraction()
        assert f.formulation_name == ""
        assert f.targeting.strategy == "none"
        assert f.confidence == "MEDIUM"

    def test_load_fixture(self) -> None:
        result = load_extraction_file(FIXTURES / "sample_extraction.json")
        assert result.paper_metadata.pmid == "37499029"
        assert len(result.formulations) == 2
        assert len(result.experiments) == 2
        assert result.formulations[0].formulation_name == "CD117-LNP"
        assert result.formulations[0].targeting.strategy == "antibody_conjugated"

    def test_round_trip_json(self) -> None:
        result = load_extraction_file(FIXTURES / "sample_extraction.json")
        dumped = result.model_dump_json()
        reloaded = ExtractionResult.model_validate_json(dumped)
        assert reloaded.paper_metadata.pmid == result.paper_metadata.pmid
        assert len(reloaded.formulations) == len(result.formulations)


# ---------------------------------------------------------------------------
# JSON parsing tests
# ---------------------------------------------------------------------------


class TestParseExtractionJson:
    """Tests for parse_extraction_json with various input formats."""

    def test_clean_json(self) -> None:
        raw = _sample_result_json()
        result = parse_extraction_json(raw)
        assert result.paper_metadata.pmid == "37499029"

    def test_markdown_fenced_json(self) -> None:
        raw = f"```json\n{_sample_result_json()}\n```"
        result = parse_extraction_json(raw)
        assert result.paper_metadata.pmid == "37499029"

    def test_markdown_fenced_no_lang(self) -> None:
        raw = f"```\n{_sample_result_json()}\n```"
        result = parse_extraction_json(raw)
        assert result.paper_metadata.pmid == "37499029"

    def test_json_with_surrounding_text(self) -> None:
        raw = f"Here is the result:\n{_sample_result_json()}\n\nDone."
        result = parse_extraction_json(raw)
        assert result.paper_metadata.pmid == "37499029"

    def test_invalid_json_raises(self) -> None:
        with pytest.raises(ValueError, match="No JSON"):
            parse_extraction_json("not json at all")

    def test_malformed_json_raises(self) -> None:
        with pytest.raises(ValueError):
            parse_extraction_json('{"paper_metadata": {"pmid": }')

    def test_empty_string_raises(self) -> None:
        with pytest.raises(ValueError, match="No JSON"):
            parse_extraction_json("")


# ---------------------------------------------------------------------------
# Pass 2 content builder
# ---------------------------------------------------------------------------


class TestBuildPass2Content:
    """Tests for build_pass2_content."""

    def test_includes_abstract_methods_results(self) -> None:
        paper = _sample_paper()
        relevant = SectionIdentificationResult(relevant_sections=[])
        content = build_pass2_content(paper, relevant)
        assert "ABSTRACT" in content
        assert "METHODS" in content
        assert "RESULTS" in content

    def test_includes_paper_metadata(self) -> None:
        paper = _sample_paper()
        relevant = SectionIdentificationResult(relevant_sections=[])
        content = build_pass2_content(paper, relevant)
        assert "37499029" in content
        assert "Science" in content


# ---------------------------------------------------------------------------
# Integration test with mocked LLM
# ---------------------------------------------------------------------------


class TestExtractPaperIntegration:
    """Integration test: mock LLM → parse → validate."""

    async def test_full_pipeline_mocked(self) -> None:
        paper = _sample_paper()
        sample = _sample_result_json()

        # Mock both LLM calls (Pass 1 and Pass 2)
        pass1_response = SectionIdentificationResult(
            relevant_sections=[]
        )
        pass2_response = ExtractionResult.model_validate_json(sample)

        with patch(
            "pubmed_agent.extractor.identify_sections",
            new_callable=AsyncMock,
            return_value=pass1_response,
        ), patch(
            "pubmed_agent.extractor.extract_formulations",
            new_callable=AsyncMock,
            return_value=pass2_response,
        ):
            result = await extract_paper(paper)

        assert result.paper_metadata.pmid == "37499029"
        assert len(result.formulations) == 2
        assert result.formulations[0].formulation_name == "CD117-LNP"

    async def test_saves_output_file(self, tmp_path: Path) -> None:
        paper = _sample_paper()
        sample = _sample_result_json()
        pass1 = SectionIdentificationResult(relevant_sections=[])
        pass2 = ExtractionResult.model_validate_json(sample)

        with patch(
            "pubmed_agent.extractor.identify_sections",
            new_callable=AsyncMock,
            return_value=pass1,
        ), patch(
            "pubmed_agent.extractor.extract_formulations",
            new_callable=AsyncMock,
            return_value=pass2,
        ):
            await extract_paper(paper, output_dir=tmp_path)

        out_file = tmp_path / "37499029.json"
        assert out_file.exists()
        loaded = json.loads(out_file.read_text())
        assert loaded["paper_metadata"]["pmid"] == "37499029"
