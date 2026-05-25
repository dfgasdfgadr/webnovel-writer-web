from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    genre: str | None = None
    hook: str | None = None
    protagonist: dict | None = None
    world_building: dict | None = None
    power_system: str | None = None
    golden_finger: str | None = None
    constraints: list[str] | None = None
    target_words: int | None = None
    target_chapters: int | None = None


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
    root_dir: str | None = None
    warnings: list[str] = []
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class ProjectList(BaseModel):
    items: list[ProjectPublic]
    total: int
