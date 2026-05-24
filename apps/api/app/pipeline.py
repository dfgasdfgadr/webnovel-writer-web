"""Pipeline orchestrator — ties Harness + Agents into the full writing flow.

Flow: plan → context → draft → review → polish → extract → commit → backup
"""

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import (
    Harness, ContextAgent, WriterAgent, ReviewAgent, DataAgent, ContinuityAgent,
    AgentResult,
)
from app.agents.llm import LLMProvider
from app.models import (
    Chapter, ChapterCommit, ReviewIssue, AgentRun, Entity, Relationship, Foreshadowing,
)
from app.story_system import StorySystem


@dataclass
class PipelineResult:
    success: bool
    step_results: list[dict] = field(default_factory=list)
    blocking_issues: list[dict] = field(default_factory=list)
    chapter_text: str = ""
    error: str | None = None


class WritingPipeline:
    """Executes the full writing pipeline for a single chapter."""

    def __init__(
        self,
        db: AsyncSession,
        project_root: str,
        chapter_id: str,
        project_id: str,
        chapter_num: int,
        user_id: str | None = None,
        llm: LLMProvider | None = None,
    ):
        self.db = db
        self.user_id = user_id
        self.llm = llm or LLMProvider()
        self.harness = Harness(project_root)
        self.story = StorySystem(project_root)
        self.context_agent = ContextAgent(llm=self.llm)
        self.writer_agent = WriterAgent(llm=self.llm)
        self.review_agent = ReviewAgent(llm=self.llm)
        self.data_agent = DataAgent(llm=self.llm)
        self.chapter_id = chapter_id
        self.project_id = project_id
        self.chapter_num = chapter_num

    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        project_root: str,
        chapter_id: str,
        project_id: str,
        chapter_num: int,
        user_id: str,
    ) -> "WritingPipeline":
        llm = await LLMProvider.for_user(user_id, db)
        return cls(
            db=db,
            project_root=project_root,
            chapter_id=chapter_id,
            project_id=project_id,
            chapter_num=chapter_num,
            user_id=user_id,
            llm=llm,
        )

    def ensure_llm_configured(self) -> None:
        if not (self.llm.api_key or "").strip():
            raise ValueError("未配置 LLM API Key，请前往设置页配置或在 .env 中设置 LLM_API_KEY")

    async def run_full(self, chapter_outline: str) -> PipelineResult:
        """Run the full pipeline: context → draft → review → extract → commit."""
        plr = PipelineResult(success=False)
        try:
            self.ensure_llm_configured()
        except ValueError as e:
            plr.error = str(e)
            return plr

        contracts = self.story.get_all_contracts_for_writing(self.chapter_num)
        summaries = self.story.get_recent_summaries(self.chapter_num, count=5)

        # Step 0: Continuity snapshot (before context)
        continuity_data = {}
        try:
            continuity_data = await self._run_continuity()
            plr.step_results.append({"step": "continuity", "result": continuity_data})
        except Exception as e:
            # Continuity is non-blocking; proceed with empty snapshot
            plr.step_results.append({"step": "continuity", "result": {"error": str(e)}})

        # Step 1: Context
        ctx_result = await self._run_agent("context", self.context_agent.run(
            chapter_outline=chapter_outline,
            contracts=contracts,
            summaries=summaries,
            continuity=continuity_data,
        ))
        if not ctx_result.success:
            plr.error = f"ContextAgent failed: {ctx_result.error}"
            return plr
        plr.step_results.append({"step": "context", "result": ctx_result.data})

        # Step 2: Draft
        brief = ctx_result.data.get("brief", chapter_outline)
        draft_result = await self._run_agent("writer", self.writer_agent.run(brief=brief))
        if not draft_result.success:
            plr.error = f"WriterAgent failed: {draft_result.error}"
            return plr
        chapter_text = draft_result.data.get("content", "")
        plr.chapter_text = chapter_text
        plr.step_results.append({"step": "draft", "result": draft_result.data})

        # Step 3: Review
        setting_json = contracts.get("master_setting", {})
        review_result = await self._run_agent("review", self.review_agent.run(
            chapter_content=chapter_text, setting_json=setting_json, chapter_outline=chapter_outline,
        ))
        if not review_result.success:
            plr.error = f"ReviewAgent failed: {review_result.error}"
            return plr
        issues = review_result.data.get("issues", [])
        plr.blocking_issues = [i for i in issues if i.get("severity") == "blocking"]
        plr.step_results.append({"step": "review", "result": review_result.data})

        # Persist review issues
        for issue in issues:
            self.db.add(ReviewIssue(
                chapter_id=self.chapter_id,
                project_id=self.project_id,
                severity=issue.get("severity", "minor"),
                category=issue.get("category", "unknown"),
                title=issue.get("title", ""),
                description=issue.get("description", ""),
                evidence=issue.get("evidence", ""),
                suggestion=issue.get("suggestion"),
            ))

        # Step 4: Extract (runs regardless of blocking)
        extract_result = await self._run_agent("data", self.data_agent.run(
            chapter_content=chapter_text, chapter_outline=chapter_outline,
        ))
        plr.step_results.append({"step": "extract", "result": extract_result.data})

        # Step 5: Commit
        commit_data = extract_result.data.get("data", {}) if extract_result.success else {}
        commit = ChapterCommit(
            chapter_id=self.chapter_id,
            project_id=self.project_id,
            content_json={"text": chapter_text, "outline": chapter_outline},
            state_changes=commit_data.get("state_changes", []),
            new_entities=commit_data.get("new_entities", []),
            new_relationships=commit_data.get("new_relationships", []),
            foreshadowing_planted=commit_data.get("foreshadowing_planted", []),
            foreshadowing_resolved=commit_data.get("foreshadowing_resolved", []),
            summary=commit_data.get("summary", ""),
        )
        self.db.add(commit)
        self.story.write_commit(self.chapter_num, {
            "version": 1,
            "content": chapter_text,
            "state_changes": commit_data.get("state_changes", []),
            "summary": commit_data.get("summary", ""),
        })
        self.story.write_summary(self.chapter_num, commit_data.get("summary", ""))
        plr.step_results.append({"step": "commit", "result": {"summary": commit_data.get("summary", "")}})

        # Update chapter status
        if plr.blocking_issues:
            chapter = await self.db.get(Chapter, self.chapter_id)
            if chapter:
                chapter.status = "reviewing"
        else:
            chapter = await self.db.get(Chapter, self.chapter_id)
            if chapter:
                chapter.status = "accepted"
                chapter.content = chapter_text
                from app.models.chapter import calculate_word_count
                chapter.word_count = calculate_word_count(chapter_text)

        await self.db.commit()
        self.story.write_review(self.chapter_num, {"issues": issues})
        self.harness.save_state({"phase": "writing", "last_chapter": self.chapter_num})
        plr.success = True
        return plr

    async def _run_agent(self, agent_type: str, agent_coro) -> AgentResult:
        start = time.time()
        run_record = AgentRun(
            project_id=self.project_id,
            chapter_id=self.chapter_id,
            agent_type=agent_type,
            phase="writing",
            status="running",
        )
        self.db.add(run_record)
        await self.db.flush()

        result = await agent_coro
        elapsed = int((time.time() - start) * 1000)

        run_record.status = "done" if result.success else "failed"
        run_record.output_payload = result.data or {}
        run_record.token_input = result.token_input
        run_record.token_output = result.token_output
        run_record.elapsed_ms = elapsed
        run_record.finished_at = datetime.utcnow()
        run_record.error_message = result.error
        await self.db.flush()
        return result

    async def _run_continuity(self) -> dict:
        """Fetch previous chapters/entities/commits and run ContinuityAgent."""
        import json

        # Fetch previous chapter texts
        result = await self.db.execute(
            select(Chapter)
            .where(
                Chapter.project_id == self.project_id,
                Chapter.number < self.chapter_num,
            )
            .order_by(Chapter.number.desc())
            .limit(3)
        )
        prev_chapters = result.scalars().all()
        chapter_texts = [
            {"number": ch.number, "title": ch.title, "content": ch.content or ""}
            for ch in reversed(prev_chapters)
        ]

        # Fetch entities
        entity_result = await self.db.execute(
            select(Entity).where(Entity.project_id == self.project_id)
        )
        entities = entity_result.scalars().all()
        entity_list = [
            {"name": e.name, "type": e.entity_type, "description": e.description or ""}
            for e in entities
        ]

        # Fetch foreshadowing
        fs_result = await self.db.execute(
            select(Foreshadowing).where(Foreshadowing.project_id == self.project_id)
        )
        foreshadowings = fs_result.scalars().all()
        fs_list = [
            {"id": f.id, "title": f.title, "status": f.status, "chapter_planted": f.chapter_planted}
            for f in foreshadowings
        ]

        # Fetch recent commits
        commit_result = await self.db.execute(
            select(ChapterCommit)
            .where(ChapterCommit.project_id == self.project_id)
            .order_by(ChapterCommit.created_at.desc())
            .limit(5)
        )
        commits = commit_result.scalars().all()
        commit_list = [
            {"chapter_number": c.chapter_number, "summary": c.summary or ""}
            for c in commits
        ]

        if not chapter_texts and not entities and not foreshadowings:
            return {"timeline_snapshot": "首章，无历史数据", "character_states": [], "active_foreshadowing": [], "pending_conflicts": [], "continuity_risks": [], "disambiguation_items": []}

        continuity_agent = ContinuityAgent(llm=self.llm)
        result = await continuity_agent.run(
            project_id=self.project_id,
            chapter_texts=chapter_texts,
            entities=entity_list,
            foreshadowing_items=fs_list,
            recent_commits=commit_list,
        )
        if result.success and result.data:
            return result.data.get("continuity_snapshot", {})
        return {"error": result.error or "Continuity agent returned no data"}

    async def stream_draft(self, chapter_outline: str) -> AsyncIterator[str | dict]:
        """SSE streaming: run continuity then context then stream writer output."""
        self.ensure_llm_configured()
        contracts = self.story.get_all_contracts_for_writing(self.chapter_num)
        summaries = self.story.get_recent_summaries(self.chapter_num, count=5)

        # Continuity snapshot
        continuity_data = {}
        try:
            yield {"type": "status", "message": "正在分析前文连续性..."}
            continuity_data = await self._run_continuity()
        except Exception:
            yield {"type": "status", "message": "连续性分析跳过，继续生成..."}

        yield {"type": "status", "message": "正在生成写作任务书..."}

        ctx_result = await self.context_agent.run(
            chapter_outline=chapter_outline,
            contracts=contracts,
            summaries=summaries,
            continuity=continuity_data,
        )
        brief = chapter_outline
        if ctx_result.success:
            brief = ctx_result.data.get("brief", chapter_outline)
        elif ctx_result.error:
            yield {"type": "status", "message": f"任务书生成跳过：{ctx_result.error}，直接使用章纲"}

        yield {"type": "status", "message": "开始流式写作..."}

        async for chunk in self.writer_agent.stream(brief=brief):
            yield {"type": "content", "content": chunk}
