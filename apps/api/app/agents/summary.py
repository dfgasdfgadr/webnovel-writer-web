"""SummaryAgent — auto-generates volume/arc level summaries from chapter data."""

import json
import logging

from app.agents.base import BaseAgent
from app.agents.llm import LLMMessage

logger = logging.getLogger("novelcraft.summary_agent")

SUMMARY_SYSTEM = """你是网文编辑，负责从章节摘要中提炼出卷/故事弧级别的高层摘要。

输出格式（JSON）：
{
  "title": "卷/弧 标题",
  "content": "500-1000字的连贯摘要，覆盖本卷/弧的主要事件、角色成长、伏笔进展和主题线索",
  "key_events": ["关键事件1", "关键事件2", ...],
  "character_arcs": [{"name": "角色名", "arc": "本卷/弧的角色变化"}],
  "cliffhangers": ["结尾悬念点"]
}

只输出 JSON，不要其他内容。"""


class SummaryAgent(BaseAgent):
    agent_type = "summary"

    async def generate_volume_summary(
        self,
        volume_label: str,
        chapter_summaries: list[str],
        synopsis_context: str = "",
    ) -> dict:
        """Generate a volume-level summary from chapter summaries."""
        chapters_text = "\n\n".join(
            f"第{i+1}章摘要：{s}" for i, s in enumerate(chapter_summaries)
        )
        context = f"{'总纲背景：' + synopsis_context if synopsis_context else ''}\n\n{chapters_text}"

        prompt = f"请为 {volume_label} 生成卷级摘要，涵盖以下{len(chapter_summaries)}章的摘要内容：\n\n{context}"
        messages = [
            LLMMessage(role="system", content=SUMMARY_SYSTEM),
            LLMMessage(role="user", content=prompt),
        ]
        resp = await self.llm.chat(messages, temperature=0.5)
        try:
            return json.loads(resp.content)
        except json.JSONDecodeError:
            return {"title": volume_label, "content": resp.content, "key_events": [], "character_arcs": [], "cliffhangers": []}

    async def generate_arc_summary(
        self,
        arc_label: str,
        volume_summaries: list[str],
    ) -> dict:
        """Generate an arc-level summary from volume summaries."""
        volumes_text = "\n\n".join(
            f"第{i+1}卷摘要：{s}" for i, s in enumerate(volume_summaries)
        )
        prompt = f"请为 {arc_label} 生成故事弧级摘要，涵盖以下{len(volume_summaries)}卷的摘要内容：\n\n{volumes_text}"
        messages = [
            LLMMessage(role="system", content=SUMMARY_SYSTEM),
            LLMMessage(role="user", content=prompt),
        ]
        resp = await self.llm.chat(messages, temperature=0.5)
        try:
            return json.loads(resp.content)
        except json.JSONDecodeError:
            return {"title": arc_label, "content": resp.content, "key_events": [], "character_arcs": [], "cliffhangers": []}

    async def _execute(self, **kwargs) -> dict:
        mode = kwargs.get("mode", "volume")
        if mode == "volume":
            return await self.generate_volume_summary(
                kwargs.get("volume_label", "卷"),
                kwargs.get("chapter_summaries", []),
                kwargs.get("synopsis_context", ""),
            )
        return await self.generate_arc_summary(
            kwargs.get("arc_label", "弧"),
            kwargs.get("volume_summaries", []),
        )
