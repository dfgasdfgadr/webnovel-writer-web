"""ArchitectAgent — generates synopsis and chapter outlines."""

import json

from app.agents.base import BaseAgent
from app.agents.llm import LLMMessage


ARCHITECT_SYSTEM = """你是网文架构师，负责为作者设计总纲和章纲。

对于总纲：基于题材、卖点、主角设定，输出完整的总纲结构。
对于章纲：基于总纲和卷纲，输出单章的详细章纲。

总纲输出格式（JSON）：
{
  "title": "书名",
  "genre": "题材",
  "hook": "核心卖点一句话",
  "synopsis": "500字故事概述",
  "volumes": [{"num": 1, "title": "卷名", "summary": "卷概要", "target_chapters": 100}]
}

章纲输出格式（JSON）：
{
  "chapter_num": N,
  "title": "章标题",
  "outline": "章纲正文（200-500字）",
  "must_cover_nodes": ["必须写到的剧情点1", "必须写到的剧情点2"],
  "forbidden_zones": ["不能触碰的禁区"],
  "key_characters": [{"name": "角色名", "role_in_chapter": "本章角色"}],
  "target_words": 3000
}

只输出 JSON，不要其他内容。"""


class ArchitectAgent(BaseAgent):
    agent_type = "architect"

    async def synopsis(self, premise: dict) -> dict:
        """Generate story synopsis and volume plan."""
        prompt = f"""请基于以下前提生成总纲：
- 题材：{premise.get('genre', '未指定')}
- 卖点：{premise.get('hook', '未指定')}
- 主角：{json.dumps(premise.get('protagonist', {}), ensure_ascii=False)}
- 世界观要点：{json.dumps(premise.get('world_building', {}), ensure_ascii=False) if premise.get('world_building') else '未指定'}
- 力量体系：{premise.get('power_system', '未指定')}"""
        messages = [
            LLMMessage(role="system", content=ARCHITECT_SYSTEM),
            LLMMessage(role="user", content=prompt),
        ]
        resp = await self.llm.chat(messages, temperature=0.6)
        try:
            data = json.loads(resp.content)
        except json.JSONDecodeError:
            data = {}
        return data

    async def chapter_outline(self, synopsis: dict, volume: dict, chapter_num: int, prev_summaries: list[str] = None) -> dict:
        """Generate a single chapter outline."""
        context = f"""总纲：{json.dumps(synopsis, ensure_ascii=False)}
当前卷纲：{json.dumps(volume, ensure_ascii=False)}
章节号：第{chapter_num}章
"""
        if prev_summaries:
            context += f"最近章节摘要：\n" + "\n".join(prev_summaries)
        messages = [
            LLMMessage(role="system", content=ARCHITECT_SYSTEM),
            LLMMessage(role="user", content=context),
        ]
        resp = await self.llm.chat(messages, temperature=0.6)
        try:
            data = json.loads(resp.content)
            data["chapter_num"] = chapter_num
        except json.JSONDecodeError:
            data = {"chapter_num": chapter_num, "outline": resp.content}
        return data

    async def _execute(self, **kwargs) -> dict:
        mode = kwargs.get("mode", "synopsis")
        if mode == "synopsis":
            return await self.synopsis(kwargs.get("premise", {}))
        return await self.chapter_outline(
            kwargs.get("synopsis", {}),
            kwargs.get("volume", {}),
            kwargs.get("chapter_num", 1),
            kwargs.get("prev_summaries"),
        )
