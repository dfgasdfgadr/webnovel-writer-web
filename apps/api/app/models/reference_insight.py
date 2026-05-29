"""ReferenceInsight — extracted insights from reference corpus with evidence."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, ForeignKey, JSON, DateTime, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class InsightType:
    """Insight type constants."""

    MACRO_STRUCTURE = "macro_structure"
    VOLUME_STRUCTURE = "volume_structure"
    HOOK = "hook"
    PACING = "pacing"
    CHARACTER_ARC = "character_arc"
    WORLD_PATTERN = "world_pattern"
    POWER_SYSTEM = "power_system"
    VILLAIN_PATTERN = "villain_pattern"
    FORESHADOWING_PATTERN = "foreshadowing_pattern"
    READER_REWARD = "reader_reward"
    ANTI_COPYING_RISK = "anti_copying_risk"

    ALL = [
        MACRO_STRUCTURE,
        VOLUME_STRUCTURE,
        HOOK,
        PACING,
        CHARACTER_ARC,
        WORLD_PATTERN,
        POWER_SYSTEM,
        VILLAIN_PATTERN,
        FORESHADOWING_PATTERN,
        READER_REWARD,
        ANTI_COPYING_RISK,
    ]


class ReferenceInsight(Base):
    """An insight extracted from reference corpus with evidence chunk ids."""

    __tablename__ = "reference_insights"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("deconstruction_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    corpus_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("reference_corpora.id", ondelete="CASCADE"), nullable=False, index=True
    )
    insight_type: Mapped[str] = mapped_column(String(32), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_chunk_ids: Mapped[list] = mapped_column(JSON, default=list)
    transferable_pattern: Mapped[str | None] = mapped_column(Text)
    forbidden_copying_risk: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
