"""Reference Corpus management — upload, split, index, search."""

import json
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import ReferenceCorpus, ReferenceChapter, ReferenceChunk
from app.schemas.reference_corpus import (
    ReferenceCorpusCreate,
    ReferenceCorpusPublic,
    ReferenceCorpusDetail,
    ReferenceCorpusList,
    ReferenceChapterPublic,
    ReferenceSearchRequest,
    ReferenceSearchResponse,
    ReferenceSearchResult,
)
from app.services.auth import get_current_user
from app.services.text_splitter import split_into_chapters, split_chapter_into_chunks
from app.search import BM25, ReferenceSearchIndex
from app.models.user import User

logger = logging.getLogger("novelcraft.reference_corpus")
router = APIRouter(prefix="/api/v1/reference-corpora", tags=["reference-corpora"])


# --- Helpers ---


def _corpus_public(c: ReferenceCorpus) -> ReferenceCorpusPublic:
    return ReferenceCorpusPublic(
        id=c.id,
        title=c.title,
        author=c.author,
        description=c.description,
        source_type=c.source_type,
        source_filename=c.source_filename,
        total_chapters=c.total_chapters,
        total_chunks=c.total_chunks,
        total_chars=c.total_chars,
        index_status=c.index_status,
        index_error=c.index_error,
        created_at=c.created_at.isoformat() if c.created_at else "",
        updated_at=c.updated_at.isoformat() if c.updated_at else "",
    )


def _chapter_public(ch: ReferenceChapter) -> ReferenceChapterPublic:
    return ReferenceChapterPublic(
        id=ch.id,
        sequence=ch.sequence,
        title=ch.title,
        char_count=ch.char_count,
        chunk_count=ch.chunk_count,
    )


async def _get_owned_corpus(
    corpus_id: str, user_id: str, db: AsyncSession, *, load_chapters: bool = False
) -> ReferenceCorpus:
    query = select(ReferenceCorpus).where(
        ReferenceCorpus.id == corpus_id,
        ReferenceCorpus.owner_id == user_id,
    )
    if load_chapters:
        query = query.options(selectinload(ReferenceCorpus.chapters))
    result = await db.execute(query)
    corpus = result.scalar_one_or_none()
    if not corpus:
        raise HTTPException(status_code=404, detail="Reference corpus not found")
    return corpus


async def _process_corpus_text(db: AsyncSession, corpus: ReferenceCorpus, text: str) -> None:
    """Split text into chapters and chunks, persist to DB."""
    corpus.index_status = "splitting"
    await db.commit()

    # Step 1: Split into chapters
    chapters = split_into_chapters(text)

    total_chars = 0
    total_chunks = 0

    for ch_split in chapters:
        chapter = ReferenceChapter(
            corpus_id=corpus.id,
            sequence=ch_split.sequence,
            title=ch_split.title,
            content=ch_split.content,
            char_count=len(ch_split.content),
        )
        db.add(chapter)
        await db.flush()  # Get chapter.id

        total_chars += chapter.char_count

        # Step 2: Split chapter into chunks
        chunk_splits = split_chapter_into_chunks(ch_split.content)
        chapter.chunk_count = len(chunk_splits)

        for ck_split in chunk_splits:
            tokens = BM25.tokenize(ck_split.content)
            chunk = ReferenceChunk(
                corpus_id=corpus.id,
                chapter_id=chapter.id,
                sequence=ck_split.sequence,
                content=ck_split.content,
                char_count=len(ck_split.content),
                tokens_json=json.dumps(tokens, ensure_ascii=False),
            )
            db.add(chunk)
            total_chunks += 1

        await db.flush()

    # Update corpus stats
    corpus.total_chapters = len(chapters)
    corpus.total_chunks = total_chunks
    corpus.total_chars = total_chars
    corpus.index_status = "ready"
    await db.commit()


# --- CRUD Endpoints ---


@router.get("", response_model=ReferenceCorpusList)
async def list_corpora(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all reference corpora owned by the current user."""
    result = await db.execute(
        select(ReferenceCorpus)
        .where(ReferenceCorpus.owner_id == current_user.id)
        .order_by(ReferenceCorpus.updated_at.desc())
    )
    corpora = result.scalars().all()
    return ReferenceCorpusList(
        items=[_corpus_public(c) for c in corpora],
        total=len(corpora),
    )


@router.post("", response_model=ReferenceCorpusPublic, status_code=status.HTTP_201_CREATED)
async def create_corpus(
    body: ReferenceCorpusCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a reference corpus from pasted text. Auto-splits chapters and chunks."""
    corpus = ReferenceCorpus(
        title=body.title,
        author=body.author,
        description=body.description,
        source_type="paste",
        owner_id=current_user.id,
        index_status="splitting",
    )
    db.add(corpus)
    await db.commit()
    await db.refresh(corpus)

    try:
        await _process_corpus_text(db, corpus, body.content)
    except Exception as e:
        logger.exception("Failed to process corpus %s", corpus.id)
        corpus.index_status = "error"
        corpus.index_error = str(e)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"文本处理失败: {e}")

    return _corpus_public(corpus)


@router.post("/upload", response_model=ReferenceCorpusPublic, status_code=status.HTTP_201_CREATED)
async def upload_corpus(
    file: UploadFile = File(...),
    title: str | None = Form(None),
    author: str | None = Form(None),
    description: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a .txt or .md file as reference corpus."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    allowed_exts = {".txt", ".md", ".markdown"}
    name_lower = file.filename.lower()
    if not any(name_lower.endswith(ext) for ext in allowed_exts):
        raise HTTPException(status_code=400, detail="Only .txt and .md files are supported")

    try:
        raw = await file.read()
        # Try UTF-8 first, fallback to GBK
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError:
            content = raw.decode("gbk", errors="replace")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")

    corpus_title = title or file.filename.rsplit(".", 1)[0]

    corpus = ReferenceCorpus(
        title=corpus_title,
        author=author,
        description=description,
        source_type="upload",
        source_filename=file.filename,
        owner_id=current_user.id,
        index_status="splitting",
    )
    db.add(corpus)
    await db.commit()
    await db.refresh(corpus)

    try:
        await _process_corpus_text(db, corpus, content)
    except Exception as e:
        logger.exception("Failed to process uploaded corpus %s", corpus.id)
        corpus.index_status = "error"
        corpus.index_error = str(e)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"文本处理失败: {e}")

    return _corpus_public(corpus)


@router.get("/{corpus_id}", response_model=ReferenceCorpusDetail)
async def get_corpus(
    corpus_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single reference corpus with its chapters."""
    corpus = await _get_owned_corpus(corpus_id, current_user.id, db, load_chapters=True)
    return ReferenceCorpusDetail(
        **_corpus_public(corpus).model_dump(),
        chapters=[_chapter_public(ch) for ch in corpus.chapters],
    )


@router.delete("/{corpus_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_corpus(
    corpus_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a reference corpus and all its chapters/chunks."""
    corpus = await _get_owned_corpus(corpus_id, current_user.id, db)
    await db.delete(corpus)
    await db.commit()


# --- Chapter Endpoints ---


@router.get("/{corpus_id}/chapters")
async def list_chapters(
    corpus_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all chapters in a reference corpus."""
    corpus = await _get_owned_corpus(corpus_id, current_user.id, db, load_chapters=True)
    return {
        "chapters": [_chapter_public(ch) for ch in corpus.chapters],
        "total": len(corpus.chapters),
    }


@router.get("/{corpus_id}/chapters/{chapter_id}/chunks")
async def list_chunks(
    corpus_id: str,
    chapter_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all chunks in a reference chapter."""
    await _get_owned_corpus(corpus_id, current_user.id, db)
    result = await db.execute(
        select(ReferenceChunk)
        .where(ReferenceChunk.chapter_id == chapter_id)
        .order_by(ReferenceChunk.sequence)
    )
    chunks = result.scalars().all()
    return {
        "chunks": [
            {
                "id": c.id,
                "sequence": c.sequence,
                "content": c.content,
                "char_count": c.char_count,
            }
            for c in chunks
        ],
        "total": len(chunks),
    }


# --- Search Endpoint ---


@router.post("/{corpus_id}/search", response_model=ReferenceSearchResponse)
async def search_corpus(
    corpus_id: str,
    body: ReferenceSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """BM25 search within a reference corpus."""
    corpus = await _get_owned_corpus(corpus_id, current_user.id, db, load_chapters=True)

    if corpus.index_status != "ready":
        raise HTTPException(
            status_code=400,
            detail=f"Corpus index not ready (status: {corpus.index_status})",
        )

    # Load all chunks
    result = await db.execute(
        select(ReferenceChunk)
        .where(ReferenceChunk.corpus_id == corpus_id)
        .order_by(ReferenceChunk.sequence)
    )
    chunks = result.scalars().all()

    if not chunks:
        return ReferenceSearchResponse(query=body.query, total=0, results=[])

    # Build index from pre-tokenized data
    idx = ReferenceSearchIndex.from_persisted_tokens(chunks)
    raw_results = idx.search(body.query, body.top_k)

    # Enrich with chapter titles
    chapter_map = {ch.id: ch.title for ch in corpus.chapters}
    results = []
    for r in raw_results:
        chapter_id = r.get("meta", {}).get("chapter_id", "")
        results.append(
            ReferenceSearchResult(
                doc_id=r["id"],
                title=r.get("title", ""),
                content=r["content"],
                score=r["score"],
                meta=r.get("meta", {}),
                chapter_title=chapter_map.get(chapter_id),
            )
        )

    return ReferenceSearchResponse(
        query=body.query,
        total=len(results),
        results=results,
    )
