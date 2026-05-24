"""InitAgent — generates world-building, power-system, and protagonist card from premise."""

import json
import logging

from app.agents.base import BaseAgent
from app.agents.llm import LLMMessage

logger = logging.getLogger("novelcraft.init_agent")

INIT_SYSTEM = """你是网文设定架构师，负责基于前提信息生成完整的世界观设定。

你需要生成三份设定文档，输出为 JSON 格式，包含三个字段：
{
  "world_building": "世界观设定 Markdown 全文（800-1500字）：包含世界背景、种族、势力格局、历史大事、地理环境",
  "power_system": "力量体系设定 Markdown 全文（500-1000字）：包含修炼/能力等级、体系分类、力量来源、关键规则",
  "protagonist_card": "主角卡 Markdown 全文（500-1000字）：包含姓名、性格、能力、背景故事、核心欲望与缺陷、成长路线"
}

只输出 JSON，不要其他内容。"""


class InitAgent(BaseAgent):
    agent_type = "init"

    async def generate_settings(self, premise: dict) -> dict:
        prompt = f"""请基于以下前提信息生成世界观、力量体系和主角卡：

- 题材：{premise.get('genre', '未指定')}
- 核心卖点：{premise.get('hook', '未指定')}
- 主角：{json.dumps(premise.get('protagonist', {}), ensure_ascii=False)}
- 世界观描述：{json.dumps(premise.get('world_building', {}), ensure_ascii=False) if premise.get('world_building') else '未指定'}
- 力量体系：{premise.get('power_system', '未指定')}
- 金手指：{premise.get('golden_finger', '未指定')}
- 创意约束：{json.dumps(premise.get('constraints', []), ensure_ascii=False)}"""

        messages = [
            LLMMessage(role="system", content=INIT_SYSTEM),
            LLMMessage(role="user", content=prompt),
        ]
        resp = await self.llm.chat(messages, temperature=0.7)
        try:
            data = json.loads(resp.content)
        except json.JSONDecodeError:
            logger.warning("InitAgent JSON parse failed, returning raw")
            data = {
                "world_building": resp.content,
                "power_system": "",
                "protagonist_card": "",
            }
        return data

    async def _execute(self, **kwargs) -> dict:
        return await self.generate_settings(kwargs.get("premise", {}))
