"""Tests for PaperPreprocessor — PMC XML parsing, abstract handling, DB storage."""

from __future__ import annotations

from datetime import date
from typing import Any
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pubmed_agent.preprocessor import PaperPreprocessor, ProcessedPaper
from shared.models.paper import Paper

# ---------------------------------------------------------------------------
# Fixture XML — realistic PMC JATS structure
# ---------------------------------------------------------------------------

PMC_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<pmc-articleset>
  <article article-type="research-article">
    <front>
      <article-meta>
        <title-group>
          <article-title>LNP delivery of base editors to HSCs</article-title>
        </title-group>
        <abstract>
          <sec>
            <title>Background</title>
            <p>Beta-thalassemia requires new therapies.</p>
          </sec>
          <sec>
            <title>Results</title>
            <p>We achieved 45% editing in CD34+ cells.</p>
          </sec>
        </abstract>
      </article-meta>
    </front>
    <body>
      <sec>
        <title>Introduction</title>
        <p>Lipid nanoparticles are promising delivery vehicles.</p>
        <p>Prior work showed liver tropism with standard LNPs.</p>
      </sec>
      <sec>
        <title>Materials and Methods</title>
        <p>LNPs were formulated using microfluidic mixing.</p>
        <sec>
          <title>LNP Preparation</title>
          <p>MC3:DSPC:Chol:PEG at 50:10:38.5:1.5 molar ratio.</p>
        </sec>
        <sec>
          <title>Cell Culture</title>
          <p>CD34+ HSCs isolated from cord blood.</p>
        </sec>
      </sec>
      <sec>
        <title>Results</title>
        <p>Particle size was 80nm with PDI of 0.05.</p>
        <p>Editing efficiency reached 45% in CD34+ cells.</p>
        <p>
          Previous studies <xref ref-type="bibr" rid="r1">[1]</xref>
          showed lower efficiency
          <xref ref-type="bibr" rid="r2,r3">[2,3]</xref>.
        </p>
      </sec>
      <sec>
        <title>Discussion</title>
        <p>These results demonstrate the potential of LNP-mediated delivery.</p>
      </sec>
      <sec>
        <title>Supplementary Material</title>
        <p>See supplementary figures S1-S5.</p>
      </sec>
    </body>
    <back>
      <app-group>
        <app>
          <title>Supplementary Tables</title>
          <p>Table S1: Full formulation screen data.</p>
        </app>
      </app-group>
    </back>
  </article>
</pmc-articleset>
"""

PMC_XML_MINIMAL = """\
<?xml version="1.0" encoding="UTF-8"?>
<pmc-articleset>
  <article>
    <front>
      <article-meta>
        <abstract>
          <p>A simple unstructured abstract about LNPs.</p>
        </abstract>
      </article-meta>
    </front>
    <body>
      <sec>
        <title>Results and Discussion</title>
        <p>Combined results and discussion section.</p>
      </sec>
    </body>
  </article>
</pmc-articleset>
"""

METADATA: dict[str, Any] = {
    "pmid": "38547890",
    "title": "LNP delivery of base editors to HSCs",
    "authors": ["Zhang Yi", "Liu Xiao"],
    "journal": "Nature Biotechnology",
    "doi": "10.1038/s41587-024-01234-5",
    "pub_date": "2024-03-15",
    "abstract": (
        "BACKGROUND: Beta-thalassemia requires new therapies.\n"
        "RESULTS: We achieved 45% editing in CD34+ cells."
    ),
}


@pytest.fixture()
def mock_client() -> AsyncMock:
    """PubMedClient mock that returns controlled responses."""
    client = AsyncMock()
    client.fetch_abstract = AsyncMock(return_value=METADATA)
    client.fetch_full_text = AsyncMock(return_value=PMC_XML)
    return client


@pytest.fixture()
def preprocessor(mock_client: AsyncMock) -> PaperPreprocessor:
    """PaperPreprocessor with mocked client."""
    return PaperPreprocessor(client=mock_client)


# ===================================================================
# PMC XML Parsing
# ===================================================================


class TestParsePmcXml:
    """Test parsing of PMC JATS XML into sections."""

    def test_extracts_abstract(self, preprocessor: PaperPreprocessor) -> None:
        sections = preprocessor.parse_pmc_xml(PMC_XML)
        assert "abstract" in sections
        assert "Beta-thalassemia" in sections["abstract"]
        assert "45% editing" in sections["abstract"]

    def test_extracts_body_sections(
        self, preprocessor: PaperPreprocessor
    ) -> None:
        sections = preprocessor.parse_pmc_xml(PMC_XML)
        assert "introduction" in sections
        assert "methods" in sections
        assert "results" in sections
        assert "discussion" in sections

    def test_normalises_section_names(
        self, preprocessor: PaperPreprocessor
    ) -> None:
        sections = preprocessor.parse_pmc_xml(PMC_XML)
        # "Materials and Methods" -> "methods"
        assert "methods" in sections
        assert "materials_and_methods" not in sections

    def test_includes_subsection_text(
        self, preprocessor: PaperPreprocessor
    ) -> None:
        sections = preprocessor.parse_pmc_xml(PMC_XML)
        assert "microfluidic" in sections["methods"]
        assert "50:10:38.5:1.5" in sections["methods"]
        assert "CD34+ HSCs" in sections["methods"]

    def test_strips_bibliography_references(
        self, preprocessor: PaperPreprocessor
    ) -> None:
        sections = preprocessor.parse_pmc_xml(PMC_XML)
        # xref bibr tags like [1] [2,3] should be removed
        assert "[1]" not in sections["results"]
        assert "[2,3]" not in sections["results"]
        assert "Previous studies" in sections["results"]

    def test_extracts_supplementary(
        self, preprocessor: PaperPreprocessor
    ) -> None:
        sections = preprocessor.parse_pmc_xml(PMC_XML)
        assert "supplementary" in sections

    def test_combined_results_discussion(
        self, preprocessor: PaperPreprocessor
    ) -> None:
        sections = preprocessor.parse_pmc_xml(PMC_XML_MINIMAL)
        assert "results_and_discussion" in sections

    def test_unstructured_abstract(
        self, preprocessor: PaperPreprocessor
    ) -> None:
        sections = preprocessor.parse_pmc_xml(PMC_XML_MINIMAL)
        assert "abstract" in sections
        assert "simple unstructured abstract" in sections["abstract"]


# ===================================================================
# Abstract-Only Parsing
# ===================================================================


class TestParseAbstractOnly:
    """Test parsing of abstract-only papers."""

    def test_labelled_sections_split(
        self, preprocessor: PaperPreprocessor
    ) -> None:
        abstract = (
            "BACKGROUND: Beta-thalassemia is a blood disorder.\n"
            "METHODS: We formulated LNPs using microfluidics.\n"
            "RESULTS: Editing efficiency was 45%."
        )
        sections = preprocessor.parse_abstract_only(abstract)
        assert "introduction" in sections  # BACKGROUND -> introduction
        assert "methods" in sections
        assert "results" in sections
        assert "abstract" in sections  # full abstract always included

    def test_unlabelled_abstract(
        self, preprocessor: PaperPreprocessor
    ) -> None:
        abstract = "We tested LNP delivery of base editors to CD34+ HSCs."
        sections = preprocessor.parse_abstract_only(abstract)
        assert sections == {"abstract": abstract}

    def test_empty_abstract(self, preprocessor: PaperPreprocessor) -> None:
        sections = preprocessor.parse_abstract_only("")
        assert sections == {}


# ===================================================================
# Text Cleaning
# ===================================================================


class TestCleanText:
    """Test text cleaning utilities."""

    def test_collapses_whitespace(
        self, preprocessor: PaperPreprocessor
    ) -> None:
        assert preprocessor.clean_text("hello   world\n\nfoo") == "hello world foo"

    def test_strips_html_tags(
        self, preprocessor: PaperPreprocessor
    ) -> None:
        assert preprocessor.clean_text("some <b>bold</b> text") == "some bold text"

    def test_handles_special_spaces(
        self, preprocessor: PaperPreprocessor
    ) -> None:
        text = "non\u00a0breaking\u2009thin\u200bzero"
        result = preprocessor.clean_text(text)
        assert result == "non breaking thin zero"


# ===================================================================
# Date Parsing
# ===================================================================


class TestParsePubDate:
    """Test publication date parsing."""

    def test_full_date(self) -> None:
        assert PaperPreprocessor._parse_pub_date("2024-03-15") == date(
            2024, 3, 15
        )

    def test_month_name(self) -> None:
        assert PaperPreprocessor._parse_pub_date("2024-Mar-15") == date(
            2024, 3, 15
        )

    def test_year_month_only(self) -> None:
        assert PaperPreprocessor._parse_pub_date("2024-06") == date(
            2024, 6, 1
        )

    def test_year_only(self) -> None:
        assert PaperPreprocessor._parse_pub_date("2024") == date(2024, 1, 1)

    def test_empty_string(self) -> None:
        assert PaperPreprocessor._parse_pub_date("") is None

    def test_month_abbreviation_jan(self) -> None:
        result = PaperPreprocessor._parse_pub_date("2026-Jan-09")
        assert result == date(2026, 1, 9)


# ===================================================================
# Full Pipeline (process_paper)
# ===================================================================


class TestProcessPaper:
    """Test end-to-end process_paper with mocked client + real DB."""

    async def test_creates_paper_with_full_text(
        self,
        preprocessor: PaperPreprocessor,
        db_session: AsyncSession,
    ) -> None:
        result = await preprocessor.process_paper("38547890", db_session)

        assert isinstance(result, ProcessedPaper)
        assert result.pmid == "38547890"
        assert result.full_text_available is True
        assert "introduction" in result.sections
        assert "methods" in result.sections
        assert "results" in result.sections

        # Verify DB record
        stmt = select(Paper).where(Paper.pmid == "38547890")
        db_result = await db_session.execute(stmt)
        paper = db_result.scalar_one()
        assert paper.title == "LNP delivery of base editors to HSCs"
        assert paper.full_text_available is True
        assert paper.full_text is not None
        assert paper.doi == "10.1038/s41587-024-01234-5"

    async def test_creates_paper_abstract_only(
        self,
        preprocessor: PaperPreprocessor,
        mock_client: AsyncMock,
        db_session: AsyncSession,
    ) -> None:
        mock_client.fetch_full_text.return_value = None

        result = await preprocessor.process_paper("38547890", db_session)

        assert result.full_text_available is False
        assert "abstract" in result.sections
        assert len(result.sections) > 0

        # DB record should have no full text
        stmt = select(Paper).where(Paper.pmid == "38547890")
        db_result = await db_session.execute(stmt)
        paper = db_result.scalar_one()
        assert paper.full_text is None
        assert paper.full_text_available is False

    async def test_upsert_updates_existing_paper(
        self,
        preprocessor: PaperPreprocessor,
        mock_client: AsyncMock,
        db_session: AsyncSession,
    ) -> None:
        # First pass: abstract only
        mock_client.fetch_full_text.return_value = None
        await preprocessor.process_paper("38547890", db_session)

        # Second pass: full text now available
        mock_client.fetch_full_text.return_value = PMC_XML
        await preprocessor.process_paper("38547890", db_session)

        # Should still be one paper, now with full text
        stmt = select(Paper).where(Paper.pmid == "38547890")
        db_result = await db_session.execute(stmt)
        paper = db_result.scalar_one()
        assert paper.full_text is not None
        assert paper.full_text_available is True

    async def test_raises_on_fetch_error(
        self,
        preprocessor: PaperPreprocessor,
        mock_client: AsyncMock,
        db_session: AsyncSession,
    ) -> None:
        mock_client.fetch_abstract.return_value = {
            "pmid": "00000000",
            "error": "Article not found",
        }
        with pytest.raises(ValueError, match="Could not fetch metadata"):
            await preprocessor.process_paper("00000000", db_session)

    async def test_stores_authors_as_json(
        self,
        preprocessor: PaperPreprocessor,
        db_session: AsyncSession,
    ) -> None:
        await preprocessor.process_paper("38547890", db_session)

        stmt = select(Paper).where(Paper.pmid == "38547890")
        db_result = await db_session.execute(stmt)
        paper = db_result.scalar_one()

        import json

        authors = json.loads(paper.authors)  # type: ignore[arg-type]
        assert authors == ["Zhang Yi", "Liu Xiao"]

    async def test_parses_publication_date(
        self,
        preprocessor: PaperPreprocessor,
        db_session: AsyncSession,
    ) -> None:
        await preprocessor.process_paper("38547890", db_session)

        stmt = select(Paper).where(Paper.pmid == "38547890")
        db_result = await db_session.execute(stmt)
        paper = db_result.scalar_one()
        assert paper.publication_date == date(2024, 3, 15)
