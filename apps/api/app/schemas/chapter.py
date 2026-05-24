from pydantic import BaseModel, Field


class ChapterCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    number: int = Field(ge=1)
    content: str | None = ""


class ChapterUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = None
    status: str | None = None


class ChapterPublic(BaseModel):
    id: str
    project_id: str
    title: str
    number: int
    content: str
    word_count: int
    status: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class ChapterList(BaseModel):
    items: list[ChapterPublic]
    total: int
