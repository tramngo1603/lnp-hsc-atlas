"""ORM model for efficacy_metrics table."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.db import Base

if TYPE_CHECKING:
    from shared.models.formulation import Formulation


class EfficacyMetric(Base):
    """A measured outcome for a formulation under specific conditions.

    Stores flexible key-value metrics: transfection efficiency, editing
    efficiency, protein expression, biodistribution, toxicity, etc.
    """

    __tablename__ = "efficacy_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    formulation_id: Mapped[int] = mapped_column(
        ForeignKey("formulations.id"), index=True
    )

    metric_type: Mapped[str]  # e.g., "transfection_efficiency", "editing_efficiency"
    value: Mapped[float | None]
    unit: Mapped[str | None]  # e.g., "%", "ng/mL", "fold change"
    timepoint: Mapped[str | None]  # e.g., "48h", "7d"
    cell_tissue: Mapped[str | None]  # context for biodistribution metrics
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    formulation: Mapped[Formulation] = relationship(
        back_populates="efficacy_metrics"
    )

    def __repr__(self) -> str:
        return (
            f"<EfficacyMetric(id={self.id}, type={self.metric_type!r}, "
            f"value={self.value} {self.unit})>"
        )
