"""Unified prompt resolver — checks ProjectPrompt first, falls back to hardcoded defaults."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.project_prompt import ProjectPrompt


DEFAULT_PROMPTS = {
    "reader_pulse": {
        "system_prompt": """你是资深网文读者模拟器...""",
    },
    "review": {
        "system_prompt": """你是严格的小说审查编辑...""",
    },
    "polish": {
        "system_prompt": """你是专业小说润色师...""",
    },
}


class PromptResolver:
    def __init__(self, project_id: str, db: AsyncSession):
        self.project_id = project_id
        self.db = db

    async def get(self, scope: str, key: str) -> str:
        """Get prompt content for scope/key. Checks DB first, falls back to default."""
        result = await self.db.execute(
            select(ProjectPrompt).where(
                ProjectPrompt.project_id == self.project_id,
                ProjectPrompt.scope == scope,
                ProjectPrompt.key == key,
            )
        )
        prompt = result.scalar_one_or_none()
        if prompt:
            return prompt.content
        return DEFAULT_PROMPTS.get(scope, {}).get(key, "")

    async def set(self, scope: str, key: str, content: str) -> ProjectPrompt:
        """Set or update a project prompt override."""
        result = await self.db.execute(
            select(ProjectPrompt).where(
                ProjectPrompt.project_id == self.project_id,
                ProjectPrompt.scope == scope,
                ProjectPrompt.key == key,
            )
        )
        prompt = result.scalar_one_or_none()
        if prompt:
            prompt.content = content
        else:
            prompt = ProjectPrompt(
                project_id=self.project_id,
                scope=scope,
                key=key,
                content=content,
                is_default=False,
            )
            self.db.add(prompt)
        await self.db.commit()
        await self.db.refresh(prompt)
        return prompt

    async def reset(self, scope: str, key: str) -> None:
        """Reset a prompt to default (delete override)."""
        result = await self.db.execute(
            select(ProjectPrompt).where(
                ProjectPrompt.project_id == self.project_id,
                ProjectPrompt.scope == scope,
                ProjectPrompt.key == key,
            )
        )
        prompt = result.scalar_one_or_none()
        if prompt:
            await self.db.delete(prompt)
            await self.db.commit()
