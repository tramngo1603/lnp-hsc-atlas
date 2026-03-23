"""ORM model for papers (publications) table."""

from __future__ import annotations

import enum
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.db import Base

if TYPE_CHECKING:
    from shared.models.extraction_run import ExtractionRun
    from shared.models.formulation import Formulation


class PaperType(enum.StrEnum):
    """Type of publication."""

    RESEARCH = "research"
    REVIEW = "review"
    PREPRINT = "preprint"
    CONFERENCE = "conference"
    CASE_REPORT = "case_report"


class Paper(Base):
    """A published paper or preprint in the knowledge base."""

    __tablename__ = "papers"

    id: Mapped[int] = mapped_column(primary_key=True)
    pmid: Mapped[str | None] = mapped_column(unique=True, index=True)
    doi: Mapped[str | None] = mapped_column(unique=True)
    title: Mapped[str] = mapped_column(Text)
    authors: Mapped[str | None] = mapped_column(Text)  # JSON array stored as text
    journal: Mapped[str | None]
    publication_date: Mapped[date | None]
    paper_type: Mapped[PaperType | None] = mapped_column(Enum(PaperType))
    abstract: Mapped[str | None] = mapped_column(Text)
    full_text_available: Mapped[bool] = mapped_column(default=False)
    full_text: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    # Relationships
    formulations: Mapped[list[Formulation]] = relationship(
        back_populates="paper", cascade="all, delete-orphan"
    )
    extraction_runs: Mapped[list[ExtractionRun]] = relationship(
        back_populates="paper", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Paper(id={self.id}, pmid={self.pmid!r}, title={self.title[:50]!r}...)>"
