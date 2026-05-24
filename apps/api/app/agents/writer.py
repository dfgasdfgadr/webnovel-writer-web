"""WriterAgent — generates chapter draft from a writing brief, supports SSE streaming."""

from typing import AsyncIterator
from app.agents.base import BaseAgent
from app.agents.llm import LLMMessage


WRITER_SYSTEM = """你是专业网文写手，负责根据写作任务书产出章节正文。

写作规则：
- 使用流畅的中文叙事，适当运用网文常见的节奏技巧
- 严格遵循任务书中的要点、角色状态、禁区提醒
- 每段控制在 3-8 句，保持阅读节奏
- 章末留下适当的悬念或期待点
- 如果任务书指定了字数范围，尽量匹配

直接输出章节正文，用 Markdown 格式，章节标题用 `#`。"""


class WriterAgent(BaseAgent):
    agent_type = "writer"

    async def _execute(self, brief: str, target_words: int = 3000, **kwargs) -> dict:
        messages = [
            LLMMessage(role="system", content=WRITER_SYSTEM),
            LLMMessage(role="user", content=f"## 写作任务书\n{brief}\n\n## 要求\n目标字数：约{target_words}字。请开始写作。"),
        ]
        resp = await self.llm.chat(messages, temperature=0.8)
        return {
            "content": resp.content,
            "token_input": resp.token_input,
            "token_output": resp.token_output,
        }

    async def stream(self, brief: str, target_words: int = 3000) -> AsyncIterator[str]:
        messages = [
            LLMMessage(role="system", content=WRITER_SYSTEM),
            LLMMessage(role="user", content=f"## 写作任务书\n{brief}\n\n## 要求\n目标字数：约{target_words}字。请开始写作。"),
        ]
        async for chunk in self.llm.chat_stream(messages, temperature=0.8):
            yield chunk
