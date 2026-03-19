"""Tests for SQLAlchemy ORM models — create, insert, query, relationships."""

from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from shared.db import Base
from shared.models import (
    BloodDisorderData,
    ConfidenceLevel,
    ConfidenceScore,
    DiseaseTarget,
    EditingStrategy,
    EfficacyMetric,
    ExperimentalCondition,
    ExtractionRun,
    Formulation,
    LipidComponent,
    LipidType,
    Paper,
    PaperType,
    PayloadType,
)


@pytest.fixture()
async def session() -> AsyncSession:  # type: ignore[misc]
    """In-memory SQLite session with all tables created."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session

    await engine.dispose()


def _make_paper() -> Paper:
    """Create a realistic Paper instance for testing."""
    return Paper(
        pmid="38547890",
        doi="10.1038/s41586-024-07234-1",
        title=(
            "In vivo delivery of base editors to hematopoietic stem cells "
            "via lipid nanoparticles for beta-thalassemia gene therapy"
        ),
        authors='["Zhang Y", "Liu X", "Chen M", "Wang J"]',
        journal="Nature",
        publication_date=date(2024, 3, 15),
        paper_type=PaperType.RESEARCH,
        abstract="We developed an LNP formulation targeting CD34+ HSCs...",
        full_text_available=True,
    )


def _make_formulation(paper_id: int) -> Formulation:
    """Create a realistic Formulation instance."""
    return Formulation(
        paper_id=paper_id,
        label="LNP-HSC-7",
        molar_ratio_str="50:10:38.5:1.5",
        molar_ratio_ionizable=50.0,
        molar_ratio_helper=10.0,
        molar_ratio_cholesterol=38.5,
        molar_ratio_peg=1.5,
        np_ratio=6.0,
        particle_size_nm=85.3,
        pdi=0.12,
        zeta_potential_mv=-5.2,
        encapsulation_efficiency_pct=94.7,
        manufacturing_method="microfluidics",
        targeting_strategy="antibody-conjugated LNP",
        targeting_ligand="anti-CD117",
    )


class TestPaperModel:
    """Test Paper ORM model."""

    async def test_create_and_read_paper(self, session: AsyncSession) -> None:
        paper = _make_paper()
        session.add(paper)
        await session.commit()

        result = await session.execute(select(Paper).where(Paper.pmid == "38547890"))
        fetched = result.scalar_one()

        assert fetched.title.startswith("In vivo delivery")
        assert fetched.journal == "Nature"
        assert fetched.paper_type == PaperType.RESEARCH
        assert fetched.publication_date == date(2024, 3, 15)
        assert fetched.full_text_available is True

    async def test_paper_pmid_unique(self, session: AsyncSession) -> None:
        session.add(_make_paper())
        await session.commit()

        duplicate = Paper(pmid="38547890", title="Duplicate")
        session.add(duplicate)
        with pytest.raises(Exception):  # noqa: B017, IntegrityError
            await session.commit()

    async def test_paper_type_enum(self, session: AsyncSession) -> None:
        for pt in PaperType:
            paper = Paper(title=f"Test {pt.value}", paper_type=pt)
            session.add(paper)
        await session.commit()

        result = await session.execute(select(Paper))
        papers = result.scalars().all()
        assert len(papers) == len(PaperType)


class TestFormulationModel:
    """Test Formulation model and its relationship to Paper."""

    async def test_create_formulation_with_paper(self, session: AsyncSession) -> None:
        paper = _make_paper()
        session.add(paper)
        await session.flush()

        form = _make_formulation(paper.id)
        session.add(form)
        await session.commit()

        result = await session.execute(
            select(Formulation).options(selectinload(Formulation.paper))
        )
        fetched = result.scalar_one()

        assert fetched.paper.pmid == "38547890"
        assert fetched.molar_ratio_str == "50:10:38.5:1.5"
        assert fetched.particle_size_nm == 85.3
        assert fetched.manufacturing_method == "microfluidics"
        assert fetched.targeting_ligand == "anti-CD117"

    async def test_cascade_delete_paper_removes_formulations(
        self, session: AsyncSession
    ) -> None:
        paper = _make_paper()
        session.add(paper)
        await session.flush()

        session.add(_make_formulation(paper.id))
        await session.commit()

        await session.delete(paper)
        await session.commit()

        result = await session.execute(select(Formulation))
        assert result.scalars().all() == []


class TestLipidComponents:
    """Test LipidComponent model — 4 lipids per formulation."""

    async def test_four_component_formulation(self, session: AsyncSession) -> None:
        paper = _make_paper()
        session.add(paper)
        await session.flush()

        form = _make_formulation(paper.id)
        session.add(form)
        await session.flush()

        lipids = [
            LipidComponent(
                formulation_id=form.id,
                lipid_type=LipidType.IONIZABLE,
                name="cKK-E12",
                smiles="CCCCCCCCCCCC(=O)OCC(COC(=O)CCCCCCCCCCC)OC(=O)CCCCCCCCCCC",
                mol_percent=50.0,
            ),
            LipidComponent(
                formulation_id=form.id,
                lipid_type=LipidType.HELPER,
                name="DOPE",
                mol_percent=10.0,
            ),
            LipidComponent(
                formulation_id=form.id,
                lipid_type=LipidType.CHOLESTEROL,
                name="Cholesterol",
                mol_percent=38.5,
            ),
            LipidComponent(
                formulation_id=form.id,
                lipid_type=LipidType.PEG,
                name="DMG-PEG2000",
                mol_percent=1.5,
            ),
        ]
        session.add_all(lipids)
        await session.commit()

        result = await session.execute(
            select(Formulation).options(selectinload(Formulation.lipid_components))
        )
        fetched = result.scalar_one()

        assert len(fetched.lipid_components) == 4
        ionizable = [lc for lc in fetched.lipid_components if lc.lipid_type == LipidType.IONIZABLE]
        assert len(ionizable) == 1
        assert ionizable[0].name == "cKK-E12"
        assert ionizable[0].smiles is not None


class TestExperimentalConditions:
    """Test ExperimentalCondition model."""

    async def test_create_in_vitro_and_in_vivo(self, session: AsyncSession) -> None:
        paper = _make_paper()
        session.add(paper)
        await session.flush()
        form = _make_formulation(paper.id)
        session.add(form)
        await session.flush()

        conditions = [
            ExperimentalCondition(
                formulation_id=form.id,
                payload_type=PayloadType.BASE_EDITOR,
                payload_cargo="ABE8e targeting BCL11A enhancer",
                target_cell_tissue="CD34+ HSC",
                cell_line=None,
                is_in_vivo=False,
                dose_value=1.0,
                dose_unit="µg/1e6 cells",
                timepoint="48h",
            ),
            ExperimentalCondition(
                formulation_id=form.id,
                payload_type=PayloadType.BASE_EDITOR,
                payload_cargo="ABE8e targeting BCL11A enhancer",
                target_cell_tissue="bone marrow HSC",
                is_in_vivo=True,
                animal_model="mouse",
                animal_strain="NSG",
                dose_value=2.0,
                dose_unit="mg/kg",
                administration_route="IV",
                timepoint="16 weeks",
            ),
        ]
        session.add_all(conditions)
        await session.commit()

        result = await session.execute(
            select(ExperimentalCondition).where(ExperimentalCondition.is_in_vivo.is_(True))
        )
        in_vivo = result.scalar_one()
        assert in_vivo.animal_strain == "NSG"
        assert in_vivo.payload_type == PayloadType.BASE_EDITOR


class TestEfficacyMetrics:
    """Test EfficacyMetric model."""

    async def test_multiple_metrics_per_formulation(self, session: AsyncSession) -> None:
        paper = _make_paper()
        session.add(paper)
        await session.flush()
        form = _make_formulation(paper.id)
        session.add(form)
        await session.flush()

        metrics = [
            EfficacyMetric(
                formulation_id=form.id,
                metric_type="editing_efficiency",
                value=45.2,
                unit="%",
                timepoint="48h",
                cell_tissue="CD34+ HSC",
            ),
            EfficacyMetric(
                formulation_id=form.id,
                metric_type="transfection_efficiency",
                value=78.9,
                unit="%",
                timepoint="24h",
            ),
            EfficacyMetric(
                formulation_id=form.id,
                metric_type="cell_viability",
                value=92.1,
                unit="%",
                timepoint="48h",
            ),
        ]
        session.add_all(metrics)
        await session.commit()

        result = await session.execute(
            select(EfficacyMetric)
            .where(EfficacyMetric.metric_type == "editing_efficiency")
        )
        editing = result.scalar_one()
        assert editing.value == 45.2


class TestBloodDisorderData:
    """Test BloodDisorderData model."""

    async def test_beta_thal_base_editing(self, session: AsyncSession) -> None:
        paper = _make_paper()
        session.add(paper)
        await session.flush()
        form = _make_formulation(paper.id)
        session.add(form)
        await session.flush()

        bd = BloodDisorderData(
            formulation_id=form.id,
            disease_target=DiseaseTarget.BETA_THALASSEMIA,
            genetic_target="BCL11A enhancer",
            editing_strategy=EditingStrategy.BASE_EDITING,
            hsc_subtype="CD34+",
            engraftment_pct=35.0,
            engraftment_timepoint="16 weeks",
            hbf_level_pct=28.5,
            hbf_induction_fold=4.2,
            conditioning_regimen="non-genotoxic",
        )
        session.add(bd)
        await session.commit()

        result = await session.execute(
            select(BloodDisorderData).where(
                BloodDisorderData.disease_target == DiseaseTarget.BETA_THALASSEMIA
            )
        )
        fetched = result.scalar_one()
        assert fetched.genetic_target == "BCL11A enhancer"
        assert fetched.hbf_level_pct == 28.5
        assert fetched.conditioning_regimen == "non-genotoxic"


class TestConfidenceScores:
    """Test ConfidenceScore model."""

    async def test_field_level_confidence(self, session: AsyncSession) -> None:
        paper = _make_paper()
        session.add(paper)
        await session.flush()
        form = _make_formulation(paper.id)
        session.add(form)
        await session.flush()

        scores = [
            ConfidenceScore(
                formulation_id=form.id,
                field_name="molar_ratio_str",
                confidence=ConfidenceLevel.HIGH,
                reason="Explicitly stated in methods section",
            ),
            ConfidenceScore(
                formulation_id=form.id,
                field_name="particle_size_nm",
                confidence=ConfidenceLevel.HIGH,
            ),
            ConfidenceScore(
                formulation_id=form.id,
                field_name="np_ratio",
                confidence=ConfidenceLevel.LOW,
                reason="Inferred from supplementary table, not directly stated",
            ),
        ]
        session.add_all(scores)
        await session.commit()

        # Query LOW confidence fields for human review
        result = await session.execute(
            select(ConfidenceScore).where(
                ConfidenceScore.confidence == ConfidenceLevel.LOW
            )
        )
        low = result.scalars().all()
        assert len(low) == 1
        assert low[0].field_name == "np_ratio"


class TestExtractionRun:
    """Test ExtractionRun model — extraction provenance tracking."""

    async def test_track_extraction_attempt(self, session: AsyncSession) -> None:
        paper = _make_paper()
        session.add(paper)
        await session.flush()

        run = ExtractionRun(
            paper_id=paper.id,
            model_used="claude-sonnet-4-5-20250929",
            prompt_version="v1",
            success=True,
            duration_seconds=3.45,
            input_tokens=2500,
            output_tokens=800,
        )
        session.add(run)
        await session.commit()

        result = await session.execute(
            select(ExtractionRun).options(selectinload(ExtractionRun.paper))
        )
        fetched = result.scalar_one()
        assert fetched.paper.pmid == "38547890"
        assert fetched.success is True
        assert fetched.duration_seconds == 3.45


class TestFullPipelineQuery:
    """Integration test — insert full realistic data and run complex queries."""

    async def test_query_hsc_formulations_by_efficiency(
        self, session: AsyncSession
    ) -> None:
        """Simulate: 'Show all HSC-targeting formulations with >40% editing efficiency.'"""
        # Insert a paper with a formulation
        paper = _make_paper()
        session.add(paper)
        await session.flush()

        form = _make_formulation(paper.id)
        session.add(form)
        await session.flush()

        # Add experimental condition targeting HSC
        session.add(
            ExperimentalCondition(
                formulation_id=form.id,
                payload_type=PayloadType.BASE_EDITOR,
                target_cell_tissue="CD34+ HSC",
                is_in_vivo=False,
            )
        )

        # Add editing efficiency metric
        session.add(
            EfficacyMetric(
                formulation_id=form.id,
                metric_type="editing_efficiency",
                value=45.2,
                unit="%",
            )
        )
        await session.commit()

        # Query: HSC-targeting formulations with >40% editing
        result = await session.execute(
            select(Formulation)
            .join(Formulation.experimental_conditions)
            .join(Formulation.efficacy_metrics)
            .where(ExperimentalCondition.target_cell_tissue.contains("HSC"))
            .where(EfficacyMetric.metric_type == "editing_efficiency")
            .where(EfficacyMetric.value > 40.0)
            .options(
                selectinload(Formulation.paper),
                selectinload(Formulation.lipid_components),
            )
        )
        formulations = result.unique().scalars().all()

        assert len(formulations) == 1
        assert formulations[0].label == "LNP-HSC-7"
        assert formulations[0].paper.journal == "Nature"
