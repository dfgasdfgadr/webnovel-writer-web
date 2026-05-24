"""Three-level summary API — volume → arc → chapter."""

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
