"""Cards and Entities management — setting assets for projects."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models import User, Project, Card, Entity, Relationship, Foreshadowing
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/v1/projects/{project_id}", tags=["cards"])


# --- Schemas ---

class CardCreate(BaseModel):
    card_type: str
    label: str
    content: dict = {}

class CardUpdate(BaseModel):
    label: str | None = None
    content: dict | None = None

class EntityCreate(BaseModel):
    entity_type: str
    label: str
    aliases: list[str] = []
    attributes: dict = {}

class EntityUpdate(BaseModel):
    label: str | None = None
    aliases: list[str] | None = None
    attributes: dict | None = None

class RelationshipCreate(BaseModel):
    source_entity_id: str
    target_entity_id: str
    relation_type: str
    description: str | None = None
    attributes: dict = {}


# --- Cards ---

@router.get("/cards")
async def list_cards(
    project_id: str,
    card_type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    query = select(Card).where(Card.project_id == project_id)
    if card_type:
        query = query.where(Card.card_type == card_type)
    result = await db.execute(query.order_by(Card.card_type, Card.label))
    cards = result.scalars().all()
    return [
        {"id": c.id, "card_type": c.card_type, "label": c.label, "content": c.content,
         "created_at": c.created_at.isoformat() if c.created_at else None}
        for c in cards
    ]


@router.post("/cards")
async def create_card(
    project_id: str,
    body: CardCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    card = Card(project_id=project_id, card_type=body.card_type, label=body.label, content=body.content)
    db.add(card)
    await db.commit()
    await db.refresh(card)
    return {"id": card.id, "card_type": card.card_type, "label": card.label, "content": card.content}


@router.delete("/cards/{card_id}")
async def delete_card(
    project_id: str, card_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    card = await db.get(Card, card_id)
    if not card or card.project_id != project_id:
        raise HTTPException(status_code=404, detail="Card not found")
    await db.delete(card)
    await db.commit()
    return {"ok": True}


# --- Entities ---

@router.get("/entities")
async def list_entities(
    project_id: str,
    entity_type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    query = select(Entity).where(Entity.project_id == project_id)
    if entity_type:
        query = query.where(Entity.entity_type == entity_type)
    result = await db.execute(query.order_by(Entity.entity_type, Entity.label))
    entities = result.scalars().all()
    return [
        {"id": e.id, "entity_type": e.entity_type, "label": e.label,
         "aliases": e.aliases, "attributes": e.attributes,
         "created_at": e.created_at.isoformat() if e.created_at else None}
        for e in entities
    ]


@router.post("/entities")
async def create_entity(
    project_id: str,
    body: EntityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    entity = Entity(project_id=project_id, entity_type=body.entity_type,
                    label=body.label, aliases=body.aliases, attributes=body.attributes)
    db.add(entity)
    await db.commit()
    await db.refresh(entity)
    return {"id": entity.id, "entity_type": entity.entity_type, "label": entity.label,
            "aliases": entity.aliases, "attributes": entity.attributes}


@router.put("/entities/{entity_id}")
async def update_entity(
    project_id: str, entity_id: str, body: EntityUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    entity = await db.get(Entity, entity_id)
    if not entity or entity.project_id != project_id:
        raise HTTPException(status_code=404, detail="Entity not found")
    if body.label is not None:
        entity.label = body.label
    if body.aliases is not None:
        entity.aliases = body.aliases
    if body.attributes is not None:
        entity.attributes = body.attributes
    await db.commit()
    return {"ok": True}


@router.delete("/entities/{entity_id}")
async def delete_entity(
    project_id: str, entity_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    entity = await db.get(Entity, entity_id)
    if not entity or entity.project_id != project_id:
        raise HTTPException(status_code=404, detail="Entity not found")
    await db.delete(entity)
    await db.commit()
    return {"ok": True}


# --- Relationships ---

@router.get("/relationships")
async def list_relationships(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    result = await db.execute(select(Relationship).where(Relationship.project_id == project_id))
    rels = result.scalars().all()
    return [
        {"id": r.id, "source_entity_id": r.source_entity_id, "target_entity_id": r.target_entity_id,
         "relation_type": r.relation_type, "description": r.description, "attributes": r.attributes}
        for r in rels
    ]


# --- Foreshadowing ---

@router.get("/foreshadowing")
async def list_foreshadowing(
    project_id: str,
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    query = select(Foreshadowing).where(Foreshadowing.project_id == project_id)
    if status:
        query = query.where(Foreshadowing.status == status)
    result = await db.execute(query.order_by(Foreshadowing.created_at))
    rows = result.scalars().all()
    return [
        {"id": r.id, "description": r.description, "status": r.status,
         "planted_in_chapter_id": r.planted_in_chapter_id,
         "resolved_in_chapter_id": r.resolved_in_chapter_id,
         "confidence": r.confidence}
        for r in rows
    ]
