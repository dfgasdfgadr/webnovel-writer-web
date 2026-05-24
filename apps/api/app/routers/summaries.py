"""Three-level summary API — volume → arc → chapter."""

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models import User, Project, Summary
from app.services.auth import get_current_user

logger = logging.getLogger("novelcraft.summaries")
router = APIRouter(prefix="/api/v1/summaries", tags=["summaries"])


class SummaryCreate(BaseModel):
    level: str = "chapter"  # volume | arc | chapter
    scope_label: str
    parent_id: str | None = None
    title: str = ""
    content: str = ""


class SummaryUpdate(BaseModel):
    title: str | None = None
    content: str | None = None


def _to_dict(s: Summary) -> dict:
    return {
        "id": s.id, "project_id": s.project_id,
        "level": s.level, "scope_label": s.scope_label,
        "parent_id": s.parent_id,
        "title": s.title, "content": s.content,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


@router.get("/{project_id}")
async def list_summaries(
    project_id: str,
    level: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    query = select(Summary).where(Summary.project_id == project_id)
    if level:
        query = query.where(Summary.level == level)
    query = query.order_by(Summary.level, Summary.scope_label)

    result = await db.execute(query)
    return [_to_dict(s) for s in result.scalars().all()]


@router.post("/{project_id}")
async def create_summary(
    project_id: str,
    body: SummaryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if body.level not in ("volume", "arc", "chapter"):
        raise HTTPException(status_code=400, detail="Level must be 'volume', 'arc', or 'chapter'")

    summary = Summary(
        project_id=project_id,
        level=body.level,
        scope_label=body.scope_label,
        parent_id=body.parent_id,
        title=body.title,
        content=body.content,
    )
    db.add(summary)
    await db.commit()
    await db.refresh(summary)
    return _to_dict(summary)


@router.patch("/{project_id}/{summary_id}")
async def update_summary(
    project_id: str,
    summary_id: str,
    body: SummaryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    summary = await db.get(Summary, summary_id)
    if not summary or summary.project_id != project_id:
        raise HTTPException(status_code=404, detail="Summary not found")

    if body.title is not None:
        summary.title = body.title
    if body.content is not None:
        summary.content = body.content
    summary.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return _to_dict(summary)


@router.delete("/{project_id}/{summary_id}")
async def delete_summary(
    project_id: str,
    summary_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    summary = await db.get(Summary, summary_id)
    if not summary or summary.project_id != project_id:
        raise HTTPException(status_code=404, detail="Summary not found")

    await db.delete(summary)
    await db.commit()
    return {"ok": True}


class GenerateSummaryRequest(BaseModel):
    level: str = "volume"  # volume | arc
    scope_label: str = ""
    chapter_ids: list[str] | None = None
    parent_id: str | None = None


@router.post("/{project_id}/generate")
async def generate_summary(
    project_id: str,
    body: GenerateSummaryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Auto-generate a volume or arc-level summary using SummaryAgent."""
    project = await db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if body.level not in ("volume", "arc"):
        raise HTTPException(status_code=400, detail="Level must be 'volume' or 'arc'")

    # Gather context from existing summaries or chapters
    from app.models.chapter import Chapter as ChapterModel
    from app.agents.summary import SummaryAgent
    from app.agents.llm import LLMProvider

    chapter_summaries: list[str] = []
    if body.chapter_ids:
        for ch_id in body.chapter_ids:
            ch = await db.get(ChapterModel, ch_id)
            if ch:
                chapter_summaries.append(f"[{ch.title}] {ch.content[:200]}")
    else:
        # Auto-fetch recent chapter summaries
        result = await db.execute(
            select(Summary).where(
                Summary.project_id == project_id,
                Summary.level == "chapter",
            ).order_by(Summary.scope_label).limit(20)
        )
        chapter_summaries = [s.content for s in result.scalars().all()]

    synopsis_ctx = ""
    if project.synopsis_json:
        try:
            synopsis = json.loads(project.synopsis_json)
            synopsis_ctx = synopsis.get("synopsis", "")
        except Exception:
            pass

    llm = await LLMProvider.for_user(current_user.id, db)
    agent = SummaryAgent(llm=llm)

    if body.level == "volume":
        result_data = await agent.generate_volume_summary(
            body.scope_label or "卷",
            chapter_summaries,
            synopsis_ctx,
        )
    else:
        volume_summaries = []
        if not body.chapter_ids:
            result = await db.execute(
                select(Summary).where(
                    Summary.project_id == project_id,
                    Summary.level == "volume",
                ).order_by(Summary.scope_label).limit(10)
            )
            volume_summaries = [s.content for s in result.scalars().all()]
        result_data = await agent.generate_arc_summary(
            body.scope_label or "故事弧",
            volume_summaries or chapter_summaries,
        )

    summary = Summary(
        project_id=project_id,
        level=body.level,
        scope_label=body.scope_label or "自动生成",
        parent_id=body.parent_id,
        title=result_data.get("title", body.scope_label),
        content=result_data.get("content", ""),
    )
    db.add(summary)
    await db.commit()
    await db.refresh(summary)

    return {**_to_dict(summary), "key_events": result_data.get("key_events", []), "character_arcs": result_data.get("character_arcs", []), "cliffhangers": result_data.get("cliffhangers", [])}
