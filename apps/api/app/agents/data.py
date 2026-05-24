"""DataAgent — extracts structured facts from accepted chapter into CHAPTER_COMMIT."""

import json
from app.agents.base import BaseAgent
from app.agents.llm import LLMMessage


DATA_SYSTEM = """你是数据提取专家，负责从已通过的章节正文中提取结构化事实。

你需要输出以下 JSON 结构：
{
  "state_changes": [{"entity": "角色名/势力名", "field": "状态字段", "old_value": "...", "new_value": "...", "evidence": "原文引用"}],
  "new_entities": [{"label": "实体名", "entity_type": "character|faction|location|item|concept", "attributes": {}, "evidence": "原文引用"}],
  "new_relationships": [{"source": "实体A", "target": "实体B", "relation_type": "...", "description": "...", "evidence": "原文引用"}],
  "foreshadowing_planted": [{"description": "伏笔描述", "importance": "major|minor", "evidence": "原文引用"}],
  "foreshadowing_resolved": [{"reference": "原有伏笔描述", "resolution": "回收方式", "evidence": "原文引用"}],
  "summary": "本章 200 字以内摘要",
  "word_count": 数字
}

只输出 JSON，不要其他内容。"""


class DataAgent(BaseAgent):
    agent_type = "data"

    async def _execute(self, chapter_content: str, chapter_outline: str = "", existing_entities: list = None, **kwargs) -> dict:
        context = f"""## 章节正文
{chapter_content}

## 本章章纲
{chapter_outline}

## 已有实体
{json.dumps(existing_entities, ensure_ascii=False) if existing_entities else "无"}

请提取结构化事实。"""
        messages = [
            LLMMessage(role="system", content=DATA_SYSTEM),
            LLMMessage(role="user", content=context),
        ]
        resp = await self.llm.chat(messages, temperature=0.2)
        try:
            data = json.loads(resp.content)
        except json.JSONDecodeError:
            data = {}
        return {
            "data": data,
            "token_input": resp.token_input,
            "token_output": resp.token_output,
        }
