"""DeconstructAgent — analyzes reference books for transferable craft patterns.

IMPORTANT: Output must NOT be written directly to project canon.
Results must pass through user confirmation before adoption.
"""

import json
import logging

from app.agents.base import BaseAgent
from app.agents.llm import LLMMessage

logger = logging.getLogger("novelcraft.deconstruct_agent")

DECONSTRUCT_SYSTEM = """你是网文拆书专家，负责分析参考书籍的可迁移创作模式。

## 分析维度
1. 黄金三章技巧：开篇钩子、信息投放节奏、角色引入方式
2. 爽点设计：打脸/升级/反转的节奏与密度
3. 人设架构：角色欲望-缺陷-成长弧线模式
4. 世界观展开：设定投放方式、揭秘节奏
5. 叙事节奏：章节长度、视角切换、时间跳跃模式

## 输出格式（JSON）
{
  "book_title": "原书名",
  "analysis": {
    "golden_three": {"hook_pattern": "", "info_density": "", "character_intro": ""},
    "pleasure_points": {"patterns": [], "density_per_10chapters": 0},
    "character_design": {"desire_defect_pattern": "", "growth_arc_pattern": ""},
    "world_building": {"reveal_method": "", "pace": ""},
    "narration": {"avg_chapter_words": 0, "pov_pattern": "", "time_jump_pattern": ""}
  },
  "transferable_patterns": [],
  "warnings": ["不可直接复制的元素"]
}

## 红线
- 只提取模式，不复制具体情节
- 跨题材迁移时必须进行变形
- 标注哪些模式与原书的特定设定耦合

只输出 JSON，不要其他内容。"""


class DeconstructAgent(BaseAgent):
    agent_type = "deconstruct"

    async def analyze_book(self, book_title: str, sample_chapters: list[str]) -> dict:
        """Analyze reference book chapters for transferable patterns."""
        chapters_text = "\n\n---\n\n".join(
            f"## 第{i+1}章\n{ch[:3000]}" for i, ch in enumerate(sample_chapters[:3])
        )
        prompt = f"""分析以下参考书的前几章，提取可迁移的创作模式：

书名：{book_title}

{chapters_text}

请提取创作技巧和可迁移模式，不要直接复制情节或角色。"""

        messages = [
            LLMMessage(role="system", content=DECONSTRUCT_SYSTEM),
            LLMMessage(role="user", content=prompt),
        ]
        resp = await self.llm.chat(messages, temperature=0.4)
        try:
            return json.loads(resp.content)
        except json.JSONDecodeError:
            return {"book_title": book_title, "raw_analysis": resp.content, "transferable_patterns": [], "warnings": ["解析失败"]}

    async def _execute(self, **kwargs) -> dict:
        return await self.analyze_book(
            kwargs.get("book_title", ""),
            kwargs.get("sample_chapters", []),
        )
