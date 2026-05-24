"""Disambiguation queue API — low-confidence fields needing human review."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models import User, Project, DisambiguationItem
from app.services.auth import get_current_user

logger = logging.getLogger("novelcraft.disambiguation")
router = APIRouter(prefix="/api/v1/disambiguation", tags=["disambiguation"])


class ResolveRequest(BaseModel):
    status: str  # accepted | rejected
    resolved_by: str


@router.get("/{project_id}")
async def list_items(
    project_id: str,
    status: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    query = select(DisambiguationItem).where(
        DisambiguationItem.project_id == project_id
    )
    if status:
        query = query.where(DisambiguationItem.status == status)
    query = query.order_by(DisambiguationItem.created_at.desc())

    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id, "project_id": i.project_id, "chapter_id": i.chapter_id,
                "field_name": i.field_name, "current_value": i.current_value,
                "confidence": i.confidence, "alternatives": i.alternatives,
                "suggestion": i.suggestion, "status": i.status,
                "resolved_by": i.resolved_by,
                "resolved_at": i.resolved_at.isoformat() if i.resolved_at else None,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in items
        ],
        "total": len(items),
    }


@router.patch("/{project_id}/{item_id}")
async def resolve_item(
    project_id: str,
    item_id: str,
    body: ResolveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if body.status not in ("accepted", "rejected"):
        raise HTTPException(status_code=400, detail="Status must be 'accepted' or 'rejected'")

    item = await db.get(DisambiguationItem, item_id)
    if not item or item.project_id != project_id:
        raise HTTPException(status_code=404, detail="Item not found")

    item.status = body.status
    item.resolved_by = body.resolved_by
    item.resolved_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "id": item.id, "project_id": item.project_id, "chapter_id": item.chapter_id,
        "field_name": item.field_name, "current_value": item.current_value,
        "confidence": item.confidence, "alternatives": item.alternatives,
        "suggestion": item.suggestion, "status": item.status,
        "resolved_by": item.resolved_by,
        "resolved_at": item.resolved_at.isoformat() if item.resolved_at else None,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }
