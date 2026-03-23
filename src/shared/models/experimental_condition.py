"""ORM model for experimental_conditions table."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.db import Base

if TYPE_CHECKING:
    from shared.models.formulation import Formulation


class PayloadType(enum.StrEnum):
    """Type of nucleic acid or editing payload."""

    MRNA = "mRNA"
    SIRNA = "siRNA"
    SGRNA = "sgRNA"
    RNP = "RNP"
    BASE_EDITOR = "base_editor"
    PRIME_EDITOR = "prime_editor"
    PLASMID = "plasmid"
    OTHER = "other"


class ExperimentalCondition(Base):
    """Experimental setup for testing a formulation.

    A single formulation may be tested under multiple conditions
    (different payloads, cell types, animal models, etc.).
    """

    __tablename__ = "experimental_conditions"

    id: Mapped[int] = mapped_column(primary_key=True)
    formulation_id: Mapped[int] = mapped_column(
        ForeignKey("formulations.id"), index=True
    )

    # Payload
    payload_type: Mapped[PayloadType | None] = mapped_column(Enum(PayloadType))
    payload_cargo: Mapped[str | None] = mapped_column(Text)  # e.g., "ABE8e targeting BCL11A"

    # Target
    target_cell_tissue: Mapped[str | None]  # e.g., "CD34+ HSC", "hepatocyte", "lung"
    cell_line: Mapped[str | None]  # e.g., "K562", "HEK293T"
    is_in_vivo: Mapped[bool | None]
    animal_model: Mapped[str | None]  # e.g., "mouse", "NHP"
    animal_strain: Mapped[str | None]  # e.g., "NSG", "C57BL/6"

    # Dosing
    dose_value: Mapped[float | None]
    dose_unit: Mapped[str | None]  # e.g., "µg/kg", "µg/1e6 cells"
    administration_route: Mapped[str | None]  # e.g., "IV", "intratracheal"

    # Timing
    timepoint: Mapped[str | None]  # e.g., "48h", "7d", "16 weeks"

    # Relationships
    formulation: Mapped[Formulation] = relationship(
        back_populates="experimental_conditions"
    )

    def __repr__(self) -> str:
        return (
            f"<ExperimentalCondition(id={self.id}, payload={self.payload_type}, "
            f"target={self.target_cell_tissue!r})>"
        )
