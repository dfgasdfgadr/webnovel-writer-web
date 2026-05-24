from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    genre: str | None = None


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    genre: str | None = None
    status: str | None = None
    synopsis_json: str | None = None


class ProjectPublic(BaseModel):
    id: str
    title: str
    description: str | None
    genre: str | None
    status: str
    owner_id: str
    synopsis_json: str | None = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class ProjectList(BaseModel):
    items: list[ProjectPublic]
    total: int
