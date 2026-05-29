"""Pydantic schemas for Reference Corpus API."""

from pydantic import BaseModel, Field


# --- Request Schemas ---

class ReferenceCorpusCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    author: str | None = None
    description: str | None = None
    content: str = Field(min_length=1, description="Full text content (pasted)")


class ReferenceSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    top_k: int = Field(default=10, ge=1, le=50)


# --- Response Schemas ---

class ReferenceChapterPublic(BaseModel):
    id: str
    sequence: int
    title: str
    char_count: int
    chunk_count: int

    model_config = {"from_attributes": True}


class ReferenceCorpusPublic(BaseModel):
    id: str
    title: str
    author: str | None
    description: str | None
    source_type: str
    source_filename: str | None
    total_chapters: int
    total_chunks: int
    total_chars: int
    index_status: str
    index_error: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class ReferenceCorpusDetail(ReferenceCorpusPublic):
    chapters: list[ReferenceChapterPublic]


class ReferenceCorpusList(BaseModel):
    items: list[ReferenceCorpusPublic]
    total: int


class ReferenceSearchResult(BaseModel):
    doc_id: str
    title: str
    content: str
    score: float
    meta: dict
    chapter_title: str | None = None


class ReferenceSearchResponse(BaseModel):
    query: str
    total: int
    results: list[ReferenceSearchResult]
