"""ContextAgent — generates a 5-section writing brief from chapter outline + contract state."""

import json

from app.agents.base import BaseAgent, AgentResult
from app.agents.llm import LLMMessage


CONTEXT_SYSTEM = """你是资深网文编辑，负责为作者准备写前任务书。根据章纲、设定约束、最近章节摘要，生成一份结构化的写作任务书。

任务书必须包含以下五个部分（用 Markdown 标题分隔）：
1. ## 本章要点：用 3-5 条要点概括本章必须完成的剧情推进
2. ## 角色状态：列出本章出场的角色及其当前状态/动机
3. ## 伏笔清单：之前埋下、本章需推进或回收的伏笔
4. ## 禁区提醒：本章禁止触碰的设定禁区
5. ## 风格指引：本章的语气、节奏、视角建议

只输出任务书本身，不要加额外说明。"""


class ContextAgent(BaseAgent):
    agent_type = "context"

    async def _execute(self, chapter_outline: str, contracts: dict, summaries: list[str] = None, **kwargs) -> dict:
        context_text = "\n\n".join([
            f"## 章纲\n{chapter_outline}",
            f"## 合同约束\n{json.dumps(contracts, ensure_ascii=False, indent=2)}",
            f"## 最近章节摘要\n" + "\n---\n".join(summaries) if summaries else "",
        ])
        messages = [
            LLMMessage(role="system", content=CONTEXT_SYSTEM),
            LLMMessage(role="user", content=context_text),
        ]
        resp = await self.llm.chat(messages, temperature=0.5)
        return {
            "brief": resp.content,
            "token_input": resp.token_input,
            "token_output": resp.token_output,
        }
