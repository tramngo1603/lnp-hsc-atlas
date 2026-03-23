"""ORM model for confidence_scores table."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.db import Base

if TYPE_CHECKING:
    from shared.models.formulation import Formulation


class ConfidenceLevel(enum.StrEnum):
    """Confidence level for an extracted field."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ConfidenceScore(Base):
    """Per-field confidence score from LLM extraction.

    Each extracted field gets a confidence level. LOW-confidence fields
    are flagged for human review.
    """

    __tablename__ = "confidence_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    formulation_id: Mapped[int] = mapped_column(
        ForeignKey("formulations.id"), index=True
    )

    field_name: Mapped[str]  # e.g., "molar_ratio_str", "particle_size_nm"
    confidence: Mapped[ConfidenceLevel] = mapped_column(Enum(ConfidenceLevel))
    reason: Mapped[str | None] = mapped_column(Text)  # why this confidence level

    # Relationships
    formulation: Mapped[Formulation] = relationship(
        back_populates="confidence_scores"
    )

    def __repr__(self) -> str:
        return (
            f"<ConfidenceScore(id={self.id}, field={self.field_name!r}, "
            f"confidence={self.confidence.value})>"
        )
