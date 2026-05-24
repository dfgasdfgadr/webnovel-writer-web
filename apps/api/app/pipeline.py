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
    Harness, ContextAgent, WriterAgent, ReviewAgent, DataAgent,
    AgentResult,
)
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
    ):
        self.db = db
        self.harness = Harness(project_root)
        self.story = StorySystem(project_root)
        self.context_agent = ContextAgent()
        self.writer_agent = WriterAgent()
        self.review_agent = ReviewAgent()
        self.data_agent = DataAgent()
        self.chapter_id = chapter_id
        self.project_id = project_id
        self.chapter_num = chapter_num

    async def run_full(self, chapter_outline: str) -> PipelineResult:
        """Run the full pipeline: context → draft → review → extract → commit."""
        plr = PipelineResult(success=False)

        contracts = self.story.get_all_contracts_for_writing(self.chapter_num)
        summaries = self.story.get_recent_summaries(self.chapter_num, count=5)

        # Step 1: Context
        ctx_result = await self._run_agent("context", self.context_agent.run(
            chapter_outline=chapter_outline, contracts=contracts, summaries=summaries,
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

    async def stream_draft(self, chapter_outline: str) -> AsyncIterator[str]:
        """SSE streaming: run context then stream writer output."""
        contracts = self.story.get_all_contracts_for_writing(self.chapter_num)
        summaries = self.story.get_recent_summaries(self.chapter_num, count=5)

        ctx_result = await self.context_agent.run(
            chapter_outline=chapter_outline, contracts=contracts, summaries=summaries,
        )
        brief = chapter_outline
        if ctx_result.success:
            brief = ctx_result.data.get("brief", chapter_outline)

        async for chunk in self.writer_agent.stream(brief=brief):
            yield chunk
