"""ORM model for extraction_runs table — tracks LLM extraction provenance."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.db import Base

if TYPE_CHECKING:
    from shared.models.paper import Paper


class ExtractionRun(Base):
    """Record of a single extraction attempt on a paper.

    Tracks which model and prompt version were used, whether the
    extraction succeeded, and timing metadata for cost analysis.
    """

    __tablename__ = "extraction_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("papers.id"), index=True)

    extraction_date: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    model_used: Mapped[str | None]  # e.g., "claude-sonnet-4-5-20250929"
    prompt_version: Mapped[str | None]  # e.g., "v1", "v2"
    success: Mapped[bool] = mapped_column(default=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    duration_seconds: Mapped[float | None]
    input_tokens: Mapped[int | None]
    output_tokens: Mapped[int | None]

    # Relationships
    paper: Mapped[Paper] = relationship(back_populates="extraction_runs")

    def __repr__(self) -> str:
        return (
            f"<ExtractionRun(id={self.id}, paper_id={self.paper_id}, "
            f"success={self.success})>"
        )
