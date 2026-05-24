"""LLM provider abstraction supporting OpenAI-compatible APIs.

Priority: user settings (DB) > .env globals > defaults.
"""
import asyncio
from dataclasses import dataclass
from typing import AsyncIterator

import httpx
from sqlalchemy import select

from app.config import settings


@dataclass
class LLMMessage:
    role: str  # system, user, assistant
    content: str


@dataclass
class LLMResponse:
    content: str
    token_input: int = 0
    token_output: int = 0


class LLMProvider:
    """Talks to any OpenAI-compatible API.

    If `user_id` is provided, resolves config from user_llm_settings table
    with fallback to .env globals.
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str = "gpt-4o",
        timeout: float = 120.0,
        user_id: str | None = None,
    ):
        self.base_url = (base_url or settings.llm_base_url).rstrip("/")
        self.api_key = api_key or settings.llm_api_key
        self.model = model or settings.llm_model
        self.timeout = timeout
        self.user_id = user_id

    @classmethod
    async def for_user(cls, user_id: str, db_session=None) -> "LLMProvider":
        """Create LLMProvider with user-specific settings from DB, falling back to .env.

        If db_session is None, uses .env defaults only.
        """
        provider = cls(user_id=user_id)
        if db_session is not None:
            try:
                from app.models.user_llm_settings import UserLlmSettings
                result = await db_session.execute(
                    select(UserLlmSettings).where(UserLlmSettings.user_id == user_id)
                )
                record = result.scalar_one_or_none()
                if record:
                    if record.api_key_encrypted:
                        try:
                            from app.routers.settings import _decrypt_api_key
                            provider.api_key = _decrypt_api_key(record.api_key_encrypted)
                        except Exception:
                            pass
                    if record.base_url:
                        provider.base_url = record.base_url.rstrip("/")
                    if record.model:
                        provider.model = record.model
            except Exception:
                pass  # graceful fallback to .env
        return provider

    async def chat(self, messages: list[LLMMessage], temperature: float = 0.7) -> LLMResponse:
        body = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()
            choice = data["choices"][0]["message"]
            return LLMResponse(
                content=choice["content"],
                token_input=data.get("usage", {}).get("prompt_tokens", 0),
                token_output=data.get("usage", {}).get("completion_tokens", 0),
            )

    async def chat_stream(self, messages: list[LLMMessage], temperature: float = 0.7) -> AsyncIterator[str]:
        body = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json=body,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        import json
                        chunk = json.loads(data)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        if delta.get("content"):
                            yield delta["content"]
