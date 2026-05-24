"""Settings request/response schemas."""
from pydantic import BaseModel, Field


class LlmSettingsRequest(BaseModel):
    api_key: str | None = Field(default=None, description="LLM API key (plaintext, stored encrypted)")
    base_url: str | None = Field(default=None, description="LLM base URL (e.g. https://api.openai.com/v1)")
    model: str | None = Field(default=None, description="Model name (e.g. gpt-4o)")


class LlmSettingsResponse(BaseModel):
    id: str
    user_id: str
    api_key_masked: str | None = Field(default=None, description="Masked API key (starts with sk-...****)")
    base_url: str | None
    model: str | None
    created_at: str
    updated_at: str


class ConnectionTestRequest(BaseModel):
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None


class ConnectionTestResponse(BaseModel):
    success: bool
    message: str
    elapsed_ms: int = 0
