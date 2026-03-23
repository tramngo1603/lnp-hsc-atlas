"""ORM model for formulations table — the central entity of the schema."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.db import Base

if TYPE_CHECKING:
    from shared.models.blood_disorder import BloodDisorderData
    from shared.models.confidence import ConfidenceScore
    from shared.models.efficacy_metric import EfficacyMetric
    from shared.models.experimental_condition import ExperimentalCondition
    from shared.models.lipid_component import LipidComponent
    from shared.models.paper import Paper


class Formulation(Base):
    """An LNP formulation reported in a paper.

    A paper may describe multiple formulations (e.g., a screening study).
    Each formulation links to its lipid components, experimental conditions,
    efficacy metrics, and blood disorder specifics.
    """

    __tablename__ = "formulations"

    id: Mapped[int] = mapped_column(primary_key=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("papers.id"), index=True)
    label: Mapped[str | None]  # e.g., "Formulation A", "LNP-3" within a paper

    # Molar ratios — stored both as string and individual floats for querying
    molar_ratio_str: Mapped[str | None]  # e.g., "50:10:38.5:1.5"
    molar_ratio_ionizable: Mapped[float | None]
    molar_ratio_helper: Mapped[float | None]
    molar_ratio_cholesterol: Mapped[float | None]
    molar_ratio_peg: Mapped[float | None]

    # Physicochemical properties
    np_ratio: Mapped[float | None]
    particle_size_nm: Mapped[float | None]
    pdi: Mapped[float | None]
    zeta_potential_mv: Mapped[float | None]
    encapsulation_efficiency_pct: Mapped[float | None]

    # Manufacturing
    manufacturing_method: Mapped[str | None]  # microfluidics, ethanol injection, etc.

    # Targeting
    targeting_strategy: Mapped[str | None] = mapped_column(Text)  # antibody, peptide, SORT, etc.
    targeting_ligand: Mapped[str | None]  # e.g., "anti-CD117", "HSC-homing peptide"

    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

    # Relationships
    paper: Mapped[Paper] = relationship(back_populates="formulations")
    lipid_components: Mapped[list[LipidComponent]] = relationship(
        back_populates="formulation", cascade="all, delete-orphan"
    )
    experimental_conditions: Mapped[list[ExperimentalCondition]] = relationship(
        back_populates="formulation", cascade="all, delete-orphan"
    )
    efficacy_metrics: Mapped[list[EfficacyMetric]] = relationship(
        back_populates="formulation", cascade="all, delete-orphan"
    )
    blood_disorder_data: Mapped[list[BloodDisorderData]] = relationship(
        back_populates="formulation", cascade="all, delete-orphan"
    )
    confidence_scores: Mapped[list[ConfidenceScore]] = relationship(
        back_populates="formulation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Formulation(id={self.id}, paper_id={self.paper_id}, label={self.label!r})>"
