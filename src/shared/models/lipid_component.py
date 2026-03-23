"""ORM model for lipid_components table."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.db import Base

if TYPE_CHECKING:
    from shared.models.formulation import Formulation


class LipidType(enum.StrEnum):
    """Classification of lipid within an LNP formulation."""

    IONIZABLE = "ionizable"
    HELPER = "helper"
    CHOLESTEROL = "cholesterol"
    PEG = "peg"
    OTHER = "other"


class LipidComponent(Base):
    """A single lipid component within a formulation.

    Each formulation typically has 4 components: ionizable lipid,
    helper lipid, cholesterol, and PEG-lipid.
    """

    __tablename__ = "lipid_components"

    id: Mapped[int] = mapped_column(primary_key=True)
    formulation_id: Mapped[int] = mapped_column(
        ForeignKey("formulations.id"), index=True
    )

    lipid_type: Mapped[LipidType] = mapped_column(Enum(LipidType))
    name: Mapped[str]  # e.g., "DLin-MC3-DMA", "DSPC", "DMG-PEG2000"
    smiles: Mapped[str | None] = mapped_column(Text)  # molecular structure
    mol_percent: Mapped[float | None]  # molar percentage in formulation

    # Relationships
    formulation: Mapped[Formulation] = relationship(
        back_populates="lipid_components"
    )

    def __repr__(self) -> str:
        return f"<LipidComponent(id={self.id}, type={self.lipid_type.value}, name={self.name!r})>"
