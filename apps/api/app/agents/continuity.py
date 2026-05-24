"""ContinuityAgent — reads last 2 chapters, outputs timeline/foreshadowing/character snapshots for long-novel consistency."""
from app.agents.base import BaseAgent
from app.agents.llm import LLMMessage


CONTINUITY_SYSTEM = """你是长篇网文的连续性编辑。根据最近章节的正文和提取的实体/伏笔数据，
生成一份结构化的一致性快照。

输出必须是一个严格的 JSON 对象，包含以下字段：
{
  "timeline_snapshot": "时间线摘要（1-2 句概括最近章节发生的关键事件）",
  "character_states": [{"name": "角色名", "status": "当前状态", "location": "当前位置", "goal": "当前目标"}],
  "active_foreshadowing": [{"id": "伏笔id", "title": "伏笔名称", "status": "planted/due/resolved", "chapter_planted": 1, "progress": "推进情况"}],
  "pending_conflicts": ["需要在本章解决的剧情冲突"],
  "continuity_risks": [{"risk": "风险描述", "severity": "low/medium/high"}],
  "disambiguation_items": [{"field": "字段名", "current_value": "当前值", "confidence": 0.5, "alternatives": ["候选值1"]}]
}

只输出 JSON，不要额外说明。"""


class ContinuityAgent(BaseAgent):
    agent_type = "continuity"

    async def _execute(
        self,
        project_id: str = "",
        chapter_texts: list[dict] = None,
        entities: list[dict] = None,
        foreshadowing_items: list[dict] = None,
        recent_commits: list[dict] = None,
        **kwargs,
    ) -> dict:
        """Generate continuity snapshot from recent chapters and extracted data.

        Args:
            chapter_texts: List of {number, title, content} for last 2-3 chapters
            entities: List of entity dicts from DB
            foreshadowing_items: List of foreshadowing dicts
            recent_commits: List of ChapterCommit summaries
        """
        chapter_context = ""
        for ch in (chapter_texts or [])[-3:]:
            chapter_context += f"\n## 第{ch.get('number', '?')}章 {ch.get('title', '')}\n{ch.get('content', '')[:2000]}\n"

        entity_context = "\n".join(
            f"- {e.get('name', '?')} ({e.get('type', '?')}): {e.get('description', '')[:200]}"
            for e in (entities or [])
        )

        foreshadowing_context = "\n".join(
            f"- [{f.get('id', '?')}] {f.get('title', '?')} | status={f.get('status', '?')} | planted_ch={f.get('chapter_planted', '?')}"
            for f in (foreshadowing_items or [])
        )

        commit_context = "\n".join(
            f"- 第{c.get('chapter_number', '?')}章: {c.get('summary', '')[:300]}"
            for c in (recent_commits or [])
        )

        user_message = f"""请分析以下数据，生成连续性快照 JSON。

## 最近章节正文
{chapter_context or '(无章节数据)'}

## 已注册实体
{entity_context or '(无实体数据)'}

## 活跃伏笔
{foreshadowing_context or '(无伏笔数据)'}

## 最近提交摘要
{commit_context or '(无提交数据)'}"""

        messages = [
            LLMMessage(role="system", content=CONTINUITY_SYSTEM),
            LLMMessage(role="user", content=user_message),
        ]
        resp = await self._chat_json(messages, temperature=0.3)

        import json
        parsed = {}
        try:
            parsed = json.loads(resp.content)
        except json.JSONDecodeError:
            parsed = {
                "timeline_snapshot": "Failed to parse continuity data",
                "character_states": [],
                "active_foreshadowing": [],
                "pending_conflicts": [],
                "continuity_risks": [],
                "disambiguation_items": [],
            }

        return {
            "continuity_snapshot": parsed,
            "token_input": resp.token_input,
            "token_output": resp.token_output,
        }
