"""PolishAgent — targeted prose polish driven by ReviewIssue dimensions."""

import json
from app.agents.base import BaseAgent
from app.agents.llm import LLMMessage


POLISH_AXES = {
    "ai_flavor": "消除 AI 模板句式（如'不是…而是…''总而言之''首先…其次…最后'），替换为自然叙事语言",
    "coherence": "修复叙事连贯性问题，确保段落间逻辑过渡流畅",
    "pacing": "调整节奏：检查段落长度分布，避免冗长描述或过快跳过场景",
    "dialogue": "优化对话：消除角色同质化语气，增强对话真实感和角色辨识度",
    "description": "增强描写：补充感官细节（视觉/听觉/触觉），避免纯叙述段落",
    "emotion": "强化情感表达：检查角色情绪描写是否充分，避免情感转折生硬",
    "hook": "优化章节钩子：确保开篇吸引力和结尾悬念设置到位",
    "consistency": "修复设定不一致：纠正角色名、能力、世界观规则与合同矛盾之处",
}


POLISH_SYSTEM = """你是专业小说润色师，根据指定的审查 issue 对正文进行定向润色。

## 润色原则
- 只修改与 issue 相关的段落，保留原文风格和叙事节奏
- 最小化改动：能改一词不改一句，能改一句不改一段
- 不新增角色、情节或设定
- 保持原文字数在 ±5% 范围

## 可用润色轴
{axes_desc}

## 输出格式
```json
{{
  "summary": "润色变更摘要",
  "diff": [
    {{"before": "原文片段...", "after": "润色后片段...", "axis": "使用的润色轴"}}
  ]
}}
```"""


class PolishAgent(BaseAgent):
    agent_type = "polish"

    async def _execute(
        self,
        chapter_content: str,
        issues: list[dict],
        enabled_axes: list[str] | None = None,
        **kwargs,
    ) -> dict:
        axes = enabled_axes or list(POLISH_AXES.keys())
        axes_desc = "\n".join(f"- {a}: {POLISH_AXES.get(a, a)}" for a in axes)

        issues_text = json.dumps(issues, ensure_ascii=False, indent=2)
        context = f"""## 待润色正文
{chapter_content}

## 审查 Issues（需定向修复）
{issues_text}

## 启用的润色轴
{', '.join(axes)}

请对正文进行定向润色，只修复与上述 issues 直接相关的部分。"""
        messages = [
            LLMMessage(role="system", content=POLISH_SYSTEM.format(axes_desc=axes_desc)),
            LLMMessage(role="user", content=context),
        ]
        resp = await self.llm.chat(messages, temperature=0.3)
        try:
            result = json.loads(resp.content)
        except json.JSONDecodeError:
            result = {
                "summary": "润色结果解析失败",
                "diff": [],
                "raw": resp.content,
            }
        return {
            "result": result,
            "token_input": resp.token_input,
            "token_output": resp.token_output,
        }
