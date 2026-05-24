from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.chapter import Chapter
from app.models.project import Project
from app.models.user import User
from app.schemas.chapter import ChapterCreate, ChapterUpdate, ChapterPublic, ChapterList
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/v1/projects/{project_id}/chapters", tags=["chapters"])


async def _get_owned_project(project_id: str, user_id: str, db: AsyncSession) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == user_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("", response_model=ChapterList)
async def list_chapters(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_owned_project(project_id, current_user.id, db)
    result = await db.execute(
        select(Chapter)
        .where(Chapter.project_id == project_id)
        .order_by(Chapter.number)
    )
    chapters = result.scalars().all()
    return ChapterList(items=[_chapter_public(c) for c in chapters], total=len(chapters))


@router.post("", response_model=ChapterPublic, status_code=status.HTTP_201_CREATED)
async def create_chapter(
    project_id: str,
    body: ChapterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_owned_project(project_id, current_user.id, db)

    content = body.content or ""
    chapter = Chapter(
        project_id=project_id,
        title=body.title,
        number=body.number,
        content=content,
        word_count=_count_words(content),
    )
    db.add(chapter)
    await db.commit()
    await db.refresh(chapter)
    return _chapter_public(chapter)


@router.get("/{chapter_id}", response_model=ChapterPublic)
async def get_chapter(
    project_id: str,
    chapter_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_owned_project(project_id, current_user.id, db)
    chapter = await _get_chapter(chapter_id, project_id, db)
    return _chapter_public(chapter)


@router.patch("/{chapter_id}", response_model=ChapterPublic)
async def update_chapter(
    project_id: str,
    chapter_id: str,
    body: ChapterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_owned_project(project_id, current_user.id, db)
    chapter = await _get_chapter(chapter_id, project_id, db)

    update_data = body.model_dump(exclude_unset=True)
    if "content" in update_data:
        update_data["word_count"] = _count_words(update_data["content"])

    for key, value in update_data.items():
        setattr(chapter, key, value)

    await db.commit()
    await db.refresh(chapter)
    return _chapter_public(chapter)


@router.delete("/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chapter(
    project_id: str,
    chapter_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_owned_project(project_id, current_user.id, db)
    chapter = await _get_chapter(chapter_id, project_id, db)
    await db.delete(chapter)
    await db.commit()


async def _get_chapter(chapter_id: str, project_id: str, db: AsyncSession) -> Chapter:
    result = await db.execute(
        select(Chapter).where(Chapter.id == chapter_id, Chapter.project_id == project_id)
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter


def _count_words(text: str) -> int:
    return len(text.replace("\n", "").replace("\r", ""))


def _chapter_public(c: Chapter) -> ChapterPublic:
    return ChapterPublic(
        id=c.id,
        project_id=c.project_id,
        title=c.title,
        number=c.number,
        content=c.content,
        word_count=c.word_count,
        status=c.status,
        created_at=c.created_at.isoformat(),
        updated_at=c.updated_at.isoformat(),
    )
