"""ReaderPulseAgent — simulates reader engagement and drop risk per chapter."""

import json
import logging

from app.agents.base import BaseAgent
from app.agents.llm import LLMMessage

logger = logging.getLogger("novelcraft.reader_pulse")

READER_PULSE_SYSTEM = """你是资深网文读者模拟器，负责从读者视角评估章节质量。

评估维度：
- drop_risk: 弃读风险（0-100，越高越可能弃读）
- hook_quality: 钩子质量（0-100）
- pacing_score: 节奏评分（0-100）
- expectation: 读者期待感描述（一句话）
- strengths: 本章亮点（字符串数组，2-4条）
- weaknesses: 本章弱点（字符串数组，2-4条）
- next_chapter_suggestion: 下章建议（字符串，30字内）
- overall_verdict: 总体评价（一句话，20字内）

只输出 JSON 对象，不要其他内容。格式：
{"drop_risk": 0-100, "hook_quality": 0-100, "pacing_score": 0-100, "expectation": "...", "strengths": ["...", "..."], "weaknesses": ["...", "..."], "next_chapter_suggestion": "...", "overall_verdict": "..."}"""


class ReaderPulseAgent(BaseAgent):
    """Simulate reader reaction to a chapter."""

    agent_type = "reader_pulse"

    async def _execute(
        self,
        chapter_content: str,
        chapter_outline: str = "",
        previous_chapter_summary: str = "",
        prompt_resolver=None,
        **kwargs,
    ) -> dict:
        system = READER_PULSE_SYSTEM
        if prompt_resolver:
            try:
                override = await prompt_resolver.get("reader_pulse", "system_prompt")
                if override:
                    system = override
            except Exception:
                pass

        context_parts = ["## 本章正文", chapter_content[:3000]]
        if chapter_outline:
            context_parts.extend(["\n## 本章章纲", chapter_outline[:500]])
        if previous_chapter_summary:
            context_parts.extend(["\n## 前文摘要", previous_chapter_summary[:500]])
        context_parts.append("\n请从读者视角评估本章质量，输出 JSON。")

        messages = [
            LLMMessage(role="system", content=system),
            LLMMessage(role="user", content="\n".join(context_parts)),
        ]

        resp = await self.llm.chat(messages, temperature=0.3)
        try:
            data = json.loads(resp.content)
        except json.JSONDecodeError:
            data = {
                "drop_risk": 50,
                "hook_quality": 50,
                "pacing_score": 50,
                "expectation": "解析失败",
                "strengths": [],
                "weaknesses": ["JSON 解析失败"],
                "next_chapter_suggestion": "",
                "overall_verdict": "JSON 解析失败",
                "raw": resp.content,
            }

        # Clamp scores to valid ranges
        data["drop_risk"] = max(0, min(100, int(data.get("drop_risk", 50))))
        data["hook_quality"] = max(0, min(100, int(data.get("hook_quality", 50))))
        data["pacing_score"] = max(0, min(100, int(data.get("pacing_score", 50))))

        return {
            **data,
            "token_input": resp.token_input,
            "token_output": resp.token_output,
        }
