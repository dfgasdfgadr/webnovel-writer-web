"""Tests for Full-book Deconstruction Agent and API endpoints."""

import json
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

from app.agents.fullbook_deconstruct import FullBookDeconstructionAgent


# --- Agent Tests ---

class TestFullBookDeconstructionAgent:
    async def test_chunk_summary_returns_json(self):
        """Agent chunk summary should return structured data."""
        mock_llm = AsyncMock()
        mock_llm.chat.return_value = AsyncMock(
            content=json.dumps({
                "summaries": [
                    {
                        "chunk_index": 0,
                        "summary": "主角获得机缘",
                        "key_events": ["获得宝物"],
                        "characters_present": ["主角"],
                        "emotional_beats": ["兴奋"],
                        "setting_hints": ["山洞"],
                    }
                ]
            }),
            token_input=100,
            token_output=50,
        )

        agent = FullBookDeconstructionAgent(llm=mock_llm)
        chunks = [
            {"id": "ch1", "content": "第一章内容" * 50, "chapter_id": "c1", "sequence": 1},
        ]
        result = await agent._summarize_chunks_batch(chunks)

        assert len(result) == 1
        assert result[0]["chunk_id"] == "ch1"
        assert "summary" in result[0]
        mock_llm.chat.assert_called_once()

    async def test_macro_structure_returns_valid_schema(self):
        """Macro structure analysis should return valid JSON schema."""
        mock_llm = AsyncMock()
        mock_llm.chat.return_value = AsyncMock(
            content=json.dumps({
                "overall_arc": "废材逆袭",
                "act_structure": {
                    "act1": {"chapters": "1-30", "purpose": "铺垫", "key_milestones": ["觉醒"]}
                },
                "volume_divisions": [
                    {"volume_num": 1, "chapters": "1-100", "theme": "崛起", "climax_type": "突破"}
                ],
                "climax_distribution": ["均匀分布"],
                "pacing_overview": "前慢后快",
            }),
            token_input=100,
            token_output=50,
        )

        agent = FullBookDeconstructionAgent(llm=mock_llm)
        chapter_summaries = [
            {
                "chapter_id": "c1",
                "chapter_title": "第一章",
                "chapter_sequence": 1,
                "chapter_summary": "主角被欺负",
                "plot_progression": "压抑",
                "character_moments": ["受辱"],
                "emotional_arc": "低落",
                "world_building_notes": [],
                "hook_quality": "强",
                "pacing_speed": "slow",
            }
        ]
        result = await agent._analyze_macro_structure(chapter_summaries, "")

        assert "overall_arc" in result
        assert "act_structure" in result
        assert "volume_divisions" in result
        assert result["overall_arc"] == "废材逆袭"

    async def test_pattern_extraction_has_evidence_chunk_ids(self):
        """Pattern extraction should include evidence_chunk_ids."""
        mock_llm = AsyncMock()
        mock_llm.chat.return_value = AsyncMock(
            content=json.dumps({
                "character_patterns": [
                    {
                        "pattern_name": "废材崛起",
                        "description": "主角从弱变强",
                        "function_role": "主角",
                        "growth_model": "阶梯式成长",
                        "evidence_chunks": ["ch1", "ch2"],
                    }
                ],
                "villain_patterns": [],
                "world_patterns": [],
                "power_system_patterns": [],
                "pacing_patterns": [],
                "foreshadowing_patterns": [],
                "reader_reward_patterns": [],
            }),
            token_input=100,
            token_output=50,
        )

        agent = FullBookDeconstructionAgent(llm=mock_llm)
        chapter_summaries = [{"chapter_summary": "测试"}]
        macro = {"overall_arc": "测试"}
        result = await agent._extract_patterns(chapter_summaries, macro, "")

        assert len(result["character_patterns"]) == 1
        assert result["character_patterns"][0]["evidence_chunks"] == ["ch1", "ch2"]

    async def test_originality_constraints_non_empty(self):
        """Constraints generation should produce non-empty constraints."""
        mock_llm = AsyncMock()
        mock_llm.chat.return_value = AsyncMock(
            content=json.dumps({
                "originality_constraints": [
                    "避免使用逆天改命作为核心设定",
                    "角色名不得与原作相似",
                ],
                "red_flags": [
                    "废材崛起桥段与原作高度相似",
                ],
                "transferable_patterns": [
                    "阶梯式成长节奏",
                    "压抑-释放情绪曲线",
                ],
                "forbidden_elements": [
                    {"element": "具体法宝名", "reason": "直接复制", "risk_level": "high"}
                ],
            }),
            token_input=100,
            token_output=50,
        )

        agent = FullBookDeconstructionAgent(llm=mock_llm)
        patterns = {"character_patterns": []}
        result = await agent._generate_constraints(patterns, "")

        assert len(result["originality_constraints"]) > 0
        assert len(result["red_flags"]) > 0
        assert len(result["transferable_patterns"]) > 0

    async def test_build_insights_has_evidence_chunk_ids(self):
        """Built insights must have evidence_chunk_ids."""
        agent = FullBookDeconstructionAgent()
        chunks = [{"id": "chunk-1"}, {"id": "chunk-2"}]
        patterns = {
            "character_patterns": [
                {
                    "pattern_name": "测试模式",
                    "description": "描述",
                    "function_role": "主角",
                    "evidence_chunks": ["chunk-1"],
                }
            ],
            "villain_patterns": [],
            "world_patterns": [],
            "power_system_patterns": [],
            "pacing_patterns": [],
            "foreshadowing_patterns": [],
            "reader_reward_patterns": [],
        }
        insights = agent._build_insights(patterns, chunks)

        assert len(insights) > 0
        for insight in insights:
            assert insight["insight_type"] in [
                "macro_structure", "volume_structure", "hook", "pacing",
                "character_arc", "world_pattern", "power_system",
                "villain_pattern", "foreshadowing_pattern", "reader_reward", "anti_copying_risk"
            ]
            assert len(insight["evidence_chunk_ids"]) > 0
            assert all(cid in ["chunk-1", "chunk-2"] for cid in insight["evidence_chunk_ids"])

    async def test_agent_full_pipeline(self):
        """Full agent pipeline should return complete report."""
        mock_llm = AsyncMock()
        mock_llm.chat.side_effect = [
            # chunk summaries
            AsyncMock(
                content=json.dumps({
                    "summaries": [{"chunk_index": 0, "summary": "摘要1", "key_events": [], "characters_present": [], "emotional_beats": [], "setting_hints": []}]
                }),
                token_input=100, token_output=50,
            ),
            # chapter summaries
            AsyncMock(
                content=json.dumps({
                    "chapter_summary": "章节摘要", "plot_progression": "", "character_moments": [],
                    "emotional_arc": "", "world_building_notes": [], "hook_quality": "", "pacing_speed": "medium",
                }),
                token_input=100, token_output=50,
            ),
            # macro structure
            AsyncMock(
                content=json.dumps({
                    "overall_arc": "弧线", "act_structure": {}, "volume_divisions": [],
                    "climax_distribution": [], "pacing_overview": "",
                }),
                token_input=100, token_output=50,
            ),
            # patterns
            AsyncMock(
                content=json.dumps({
                    "character_patterns": [{"pattern_name": "模式", "description": "描述", "function_role": "主角", "evidence_chunks": ["c1"]}],
                    "villain_patterns": [], "world_patterns": [], "power_system_patterns": [],
                    "pacing_patterns": [], "foreshadowing_patterns": [], "reader_reward_patterns": [],
                }),
                token_input=100, token_output=50,
            ),
            # constraints
            AsyncMock(
                content=json.dumps({
                    "originality_constraints": ["约束1"],
                    "red_flags": ["风险1"],
                    "transferable_patterns": ["模式1"],
                    "forbidden_elements": [],
                }),
                token_input=100, token_output=50,
            ),
        ]

        agent = FullBookDeconstructionAgent(llm=mock_llm)
        chunks = [{"id": "c1", "content": "内容" * 100, "chapter_id": "ch1", "sequence": 1}]
        chapters = [{"id": "ch1", "title": "第一章", "sequence": 1, "content": "内容", "chunks": [{"id": "c1"}]}]

        result = await agent.run(chunks=chunks, chapters=chapters)

        assert result.success is True
        assert "fullbook_report" in result.data
        assert "transferable_patterns" in result.data
        assert "originality_constraints" in result.data
        assert "red_flags" in result.data
        assert "insights" in result.data
        assert len(result.data["insights"]) > 0

    async def test_agent_fallback_on_llm_error(self):
        """Agent should handle LLM errors gracefully."""
        mock_llm = AsyncMock()
        mock_llm.chat.side_effect = Exception("LLM timeout")

        agent = FullBookDeconstructionAgent(llm=mock_llm)
        chunks = [{"id": "c1", "content": "内容", "chapter_id": "ch1", "sequence": 1}]
        chapters = [{"id": "ch1", "title": "第一章", "sequence": 1, "content": "内容", "chunks": [{"id": "c1"}]}]

        result = await agent.run(chunks=chunks, chapters=chapters)

        assert result.success is False
        assert result.error is not None


# --- API Tests ---

class TestFullBookDeconstructAPI:
    async def test_start_deconstruct_returns_run_id_and_running(self, async_client: AsyncClient, auth_headers: dict):
        """P3-1: Starting async task should return run_id and running status."""
        # Create a corpus first
        create_resp = await async_client.post("/api/v1/reference-corpora", headers=auth_headers, json={
            "title": "拆书测试书",
            "content": "第一章 开始\n这是开始的内容。\n\n第二章 结束\n这是结束的内容。",
        })
        assert create_resp.status_code == 201
        corpus_id = create_resp.json()["id"]

        # Mock the background task to avoid actual LLM calls
        with patch("app.routers.deconstruct_runs._run_deconstruction") as mock_task:
            mock_task.return_value = None

            resp = await async_client.post(
                "/api/v1/agents/foundry/deconstruct/fullbook",
                headers=auth_headers,
                json={"corpus_id": corpus_id, "target_genre": "玄幻"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "run_id" in data
            assert data["status"] == "running"
            assert data["phase"] == "starting"
            mock_task.assert_called_once()

    async def test_get_run_not_found(self, async_client: AsyncClient, auth_headers: dict):
        """Querying non-existent run should return 404."""
        resp = await async_client.get(
            "/api/v1/agents/foundry/deconstruct-runs/nonexistent-id",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    async def test_get_run_isolation(self, async_client: AsyncClient, auth_headers: dict):
        """Other users should not access another user's run."""
        # Create corpus and run as first user
        create_resp = await async_client.post("/api/v1/reference-corpora", headers=auth_headers, json={
            "title": "隔离测试书",
            "content": "第一章\n内容",
        })
        corpus_id = create_resp.json()["id"]

        with patch("app.routers.deconstruct_runs._run_deconstruction"):
            start_resp = await async_client.post(
                "/api/v1/agents/foundry/deconstruct/fullbook",
                headers=auth_headers,
                json={"corpus_id": corpus_id},
            )
            run_id = start_resp.json()["run_id"]

        # Create another user
        await async_client.post("/api/v1/auth/register", json={
            "username": "otheruser_decon",
            "password": "otherpass",
        })
        login_resp = await async_client.post("/api/v1/auth/login", data={
            "username": "otheruser_decon",
            "password": "otherpass",
        })
        other_token = login_resp.json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # Other user should not see this run
        resp = await async_client.get(
            f"/api/v1/agents/foundry/deconstruct-runs/{run_id}",
            headers=other_headers,
        )
        assert resp.status_code == 403

    async def test_start_deconstruct_corpus_not_ready(self, async_client: AsyncClient, auth_headers: dict):
        """Starting deconstruct on non-ready corpus should fail."""
        # Note: reference-corpora POST auto-indexes, so we test with non-existent
        resp = await async_client.post(
            "/api/v1/agents/foundry/deconstruct/fullbook",
            headers=auth_headers,
            json={"corpus_id": "nonexistent-corpus", "target_genre": "玄幻"},
        )
        assert resp.status_code == 404

    async def test_get_run_returns_full_report(self, async_client: AsyncClient, auth_headers: dict):
        """P3-2: Completed run should return fullbook_report."""
        from app.database import async_session
        from app.models.deconstruction_run import DeconstructionRun
        from app.models.reference_insight import ReferenceInsight

        # Create corpus
        create_resp = await async_client.post("/api/v1/reference-corpora", headers=auth_headers, json={
            "title": "报告测试书",
            "content": "第一章\n内容",
        })
        corpus_id = create_resp.json()["id"]

        # Get current user ID
        me_resp = await async_client.get("/api/v1/auth/me", headers=auth_headers)
        user_id = me_resp.json()["id"]

        # Create run directly in DB
        async with async_session() as db:
            run = DeconstructionRun(
                corpus_id=corpus_id,
                user_id=user_id,
                status="done",
                phase="done",
                progress=100,
                fullbook_report={
                    "macro_structure": {"overall_arc": "测试弧线"},
                    "volume_patterns": [],
                    "character_patterns": [{"name": "主角", "description": "描述"}],
                    "world_patterns": [],
                    "power_progression": {},
                    "pacing_curve": {},
                    "foreshadowing_patterns": [],
                    "villain_patterns": [],
                    "reader_reward_patterns": [],
                },
                transferable_patterns=["可迁移模式1"],
                originality_constraints=["约束1"],
                red_flags=["风险1"],
            )
            db.add(run)
            await db.commit()
            await db.refresh(run)

            # Add insight
            insight = ReferenceInsight(
                run_id=run.id,
                corpus_id=corpus_id,
                insight_type="character_arc",
                summary="测试洞察",
                evidence_chunk_ids=["chunk-1"],
                transferable_pattern="成长模式",
                forbidden_copying_risk="角色名不可复制",
            )
            db.add(insight)
            await db.commit()

            run_id = run.id

        # Query the run
        resp = await async_client.get(
            f"/api/v1/agents/foundry/deconstruct-runs/{run_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "done"
        assert data["fullbook_report"]["macro_structure"]["overall_arc"] == "测试弧线"
        assert len(data["transferable_patterns"]) > 0
        assert len(data["originality_constraints"]) > 0
        assert len(data["red_flags"]) > 0

        # P3-3: Insights should have evidence_chunk_ids
        assert len(data["insights"]) > 0
        assert data["insights"][0]["evidence_chunk_ids"] == ["chunk-1"]

    async def test_run_failed_state(self, async_client: AsyncClient, auth_headers: dict):
        """P3-6: Failed run should have failed status."""
        from app.database import async_session
        from app.models.deconstruction_run import DeconstructionRun

        # Create corpus
        create_resp = await async_client.post("/api/v1/reference-corpora", headers=auth_headers, json={
            "title": "失败测试书",
            "content": "第一章\n内容",
        })
        corpus_id = create_resp.json()["id"]

        # Get current user ID
        me_resp = await async_client.get("/api/v1/auth/me", headers=auth_headers)
        user_id = me_resp.json()["id"]

        # Create failed run directly
        async with async_session() as db:
            run = DeconstructionRun(
                corpus_id=corpus_id,
                user_id=user_id,
                status="failed",
                phase="pattern_extraction",
                progress=65,
                error_message="LLM API timeout",
            )
            db.add(run)
            await db.commit()
            await db.refresh(run)
            run_id = run.id

        resp = await async_client.get(
            f"/api/v1/agents/foundry/deconstruct-runs/{run_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "failed"
        assert data["error_message"] == "LLM API timeout"
        assert data["phase"] == "pattern_extraction"

    async def test_background_task_catches_exception(self, async_client: AsyncClient, auth_headers: dict):
        """Background task should catch exceptions and update run to failed."""
        from app.database import async_session
        from app.models.deconstruction_run import DeconstructionRun

        # Create corpus
        create_resp = await async_client.post("/api/v1/reference-corpora", headers=auth_headers, json={
            "title": "异常测试书",
            "content": "第一章\n内容" * 100,
        })
        corpus_id = create_resp.json()["id"]

        # Mock LLM to raise exception
        with patch("app.routers.deconstruct_runs.LLMProvider.for_user") as mock_for_user:
            mock_llm = AsyncMock()
            mock_llm.chat.side_effect = Exception("Simulated LLM failure")
            mock_for_user.return_value = mock_llm

            # Start deconstruct
            start_resp = await async_client.post(
                "/api/v1/agents/foundry/deconstruct/fullbook",
                headers=auth_headers,
                json={"corpus_id": corpus_id},
            )
            assert start_resp.status_code == 200
            run_id = start_resp.json()["run_id"]

            # Wait for background task to complete
            import asyncio
            await asyncio.sleep(0.5)

            # Verify run status updated to failed
            async with async_session() as db:
                run = await db.get(DeconstructionRun, run_id)
                assert run is not None
                assert run.status == "failed"
                assert run.error_message is not None
                assert "Simulated LLM failure" in run.error_message
