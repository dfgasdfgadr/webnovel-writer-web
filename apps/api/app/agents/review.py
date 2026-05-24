"""ReviewAgent — structured review against the Story System contract."""

import json
from app.agents.base import BaseAgent
from app.agents.llm import LLMMessage


REVIEW_SYSTEM = """你是严格的小说审查编辑，负责根据设定合同审查章节正文，输出结构化问题清单。

审查维度：
- consistency：设定一致性（角色名、能力、世界观规则是否与设定集一致）
- timeline：时间线（事件顺序是否合理，有无时间矛盾）
- coherence：叙事连贯性（前后逻辑是否通顺）
- ooc：角色 OOC（角色行为是否偏离设定性格）
- logic：逻辑因果（事件因果关系是否成立）
- foreshadowing：伏笔状态（伏笔推进或回收情况）
- ai_flavor：AI 味检测（是否出现「不是…而是…」「总而言之」等模板句式）

severity 分为：blocking（阻断，必须修复）、major（严重，强烈建议修复）、minor（轻微，可选修复）
每条 issue 必须引用原文 evidence（直接引用原文片段）。

同时输出 7 维评分（0–100），作为 issues 的同级字段：
- consistency_score：设定一致性
- timeline_score：时间线
- coherence_score：叙事连贯性
- ooc_score：角色 OOC
- logic_score：逻辑因果
- foreshadowing_score：伏笔状态
- ai_flavor_score：AI 味控制（越高越好）

只输出 JSON 对象，不要其他内容。格式：
{{"issues": [...], "review_metrics": {{"consistency_score": 0-100, "timeline_score": 0-100, "coherence_score": 0-100, "ooc_score": 0-100, "logic_score": 0-100, "foreshadowing_score": 0-100, "ai_flavor_score": 0-100}}, "summary": "一句话审查总结"}}"""


class ReviewAgent(BaseAgent):
    agent_type = "review"

    async def _execute(self, chapter_content: str, setting_json: dict, chapter_outline: str = "", **kwargs) -> dict:
        context = f"""## 章节正文
{chapter_content}

## 设定集
{json.dumps(setting_json, ensure_ascii=False, indent=2)}

## 本章章纲
{chapter_outline}

请审查并输出结构化问题清单。"""
        messages = [
            LLMMessage(role="system", content=REVIEW_SYSTEM),
            LLMMessage(role="user", content=context),
        ]
        resp = await self.llm.chat(messages, temperature=0.2)
        try:
            data = json.loads(resp.content)
            if isinstance(data, list):
                # Legacy format: plain issue list
                issues = data
                metrics = {}
                summary = ""
            elif isinstance(data, dict):
                issues = data.get("issues", [])
                metrics = data.get("review_metrics", {})
                summary = data.get("summary", "")
            else:
                issues = []
                metrics = {}
                summary = ""
        except json.JSONDecodeError:
            issues = []
            metrics = {}
            summary = ""
        return {
            "issues": issues,
            "review_metrics": metrics,
            "summary": summary,
            "blocking_count": sum(1 for i in issues if i.get("severity") == "blocking"),
            "total_count": len(issues),
            "token_input": resp.token_input,
            "token_output": resp.token_output,
        }
