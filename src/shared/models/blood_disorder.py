"""ORM model for blood_disorder_data table."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.db import Base

if TYPE_CHECKING:
    from shared.models.formulation import Formulation


class DiseaseTarget(enum.StrEnum):
    """Blood disorder being targeted."""

    BETA_THALASSEMIA = "beta_thalassemia"
    SICKLE_CELL = "sickle_cell"
    OTHER_HEMOGLOBINOPATHY = "other_hemoglobinopathy"
    OTHER = "other"


class EditingStrategy(enum.StrEnum):
    """Gene editing approach used."""

    BASE_EDITING = "base_editing"
    PRIME_EDITING = "prime_editing"
    HDR = "hdr"
    NHEJ = "nhej"
    GENE_ADDITION = "gene_addition"
    GENE_SILENCING = "gene_silencing"
    OTHER = "other"


class BloodDisorderData(Base):
    """Blood disorder-specific data for a formulation.

    Captures disease target, genetic target, editing strategy,
    HSC subtype, engraftment data, and hemoglobin outcomes.
    """

    __tablename__ = "blood_disorder_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    formulation_id: Mapped[int] = mapped_column(
        ForeignKey("formulations.id"), index=True
    )

    disease_target: Mapped[DiseaseTarget | None] = mapped_column(Enum(DiseaseTarget))
    genetic_target: Mapped[str | None]  # e.g., "BCL11A", "HBB", "HBG1/2 promoter"
    editing_strategy: Mapped[EditingStrategy | None] = mapped_column(Enum(EditingStrategy))

    # HSC specifics
    hsc_subtype: Mapped[str | None]  # e.g., "CD34+", "LT-HSC", "erythroid progenitor"
    engraftment_pct: Mapped[float | None]
    engraftment_timepoint: Mapped[str | None]  # e.g., "16 weeks"

    # Hemoglobin outcomes
    hbf_level_pct: Mapped[float | None]  # % of total hemoglobin
    hbf_induction_fold: Mapped[float | None]
    total_hemoglobin_gdl: Mapped[float | None]  # g/dL

    # Treatment context
    conditioning_regimen: Mapped[str | None]  # myeloablative, non-genotoxic, none
    off_target_rate_pct: Mapped[float | None]
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    formulation: Mapped[Formulation] = relationship(
        back_populates="blood_disorder_data"
    )

    def __repr__(self) -> str:
        return (
            f"<BloodDisorderData(id={self.id}, disease={self.disease_target}, "
            f"target={self.genetic_target!r})>"
        )
