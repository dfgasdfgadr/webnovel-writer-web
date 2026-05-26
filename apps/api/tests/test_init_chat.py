"""Tests for InitChatAgent — conversational init flow and creative constraints."""
import pytest
import json


class TestInitChatAgent:
    def _make_agent(self):
        from app.agents.init_chat import InitChatAgent
        return InitChatAgent()  # no LLM → uses fallback

    def test_fallback_question_when_fields_missing(self):
        agent = self._make_agent()
        result = agent._fallback_question(["title"], {})
        assert result["status"] == "asking"
        assert "书名" in result["question"] or "title" in result["question"].lower()

    def test_fallback_question_for_genre(self):
        agent = self._make_agent()
        result = agent._fallback_question(["genre"], {"title": "测试书"})
        assert result["status"] == "asking"
        assert result["missing_fields"] == ["genre"]

    def test_fallback_schemes_generates_3_options(self):
        agent = self._make_agent()
        result = agent._fallback_schemes({"genre": "玄幻", "hook": "逆天改命"})
        assert result["status"] == "complete"
        assert len(result["schemes"]) == 3
        for scheme in result["schemes"]:
            assert "scores" in scheme
            assert all(k in scheme["scores"] for k in ["innovation", "marketability", "coherence", "depth", "readability"])

    def test_missing_fields_empty_state(self):
        agent = self._make_agent()
        missing = agent._missing_fields({})
        assert "title" in missing
        assert "genre" in missing
        assert "hook" in missing
        assert "protagonist_name" in missing

    def test_missing_fields_partial_state(self):
        agent = self._make_agent()
        missing = agent._missing_fields({
            "title": "测试书", "genre": "玄幻", "hook": "逆袭", "protagonist_name": "林凡",
        })
        assert any(k in missing for k in ["world_building", "power_system", "golden_finger"])

    def test_missing_fields_all_filled(self):
        agent = self._make_agent()
        state = {
            "title": "书", "genre": "玄幻", "hook": "h", "protagonist_name": "p",
            "world_building": "w", "power_system": "p", "golden_finger": "g",
        }
        missing = agent._missing_fields(state)
        assert missing == []

    @pytest.mark.asyncio
    async def test_process_message_without_llm(self):
        agent = self._make_agent()
        result = await agent.process_message(json.dumps({"genre": "玄幻"}))
        assert result["status"] == "asking"

    @pytest.mark.asyncio
    async def test_process_message_triggers_schemes_when_complete(self):
        agent = self._make_agent()
        full_msg = json.dumps({
            "title": "测试书", "genre": "玄幻", "hook": "逆袭之路",
            "protagonist_name": "叶凡", "world_building": "修仙世界",
            "power_system": "灵力修炼", "golden_finger": "时间回溯",
        })
        result = await agent.process_message(full_msg)
        assert result["status"] == "complete"
        assert len(result["schemes"]) == 3


class TestInitChatAPI:
    async def test_init_schemes_endpoint(self, async_client, auth_headers):
        resp = await async_client.post(
            "/api/v1/projects/init/schemes",
            json={
                "premise": {
                    "title": "测试", "genre": "玄幻", "hook": "逆袭",
                    "protagonist": {"name": "叶凡"},
                    "world_building": {"description": "修仙界"},
                    "power_system": "灵力", "golden_finger": "系统",
                }
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "complete"
        assert len(data["schemes"]) == 3

    async def test_init_chat_stream_returns_data(self, async_client, auth_headers):
        """SSE stream endpoint should return SSE-formatted data."""
        resp = await async_client.post(
            "/api/v1/projects/init/chat/stream",
            json={"message": json.dumps({"genre": "科幻"}), "history": []},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        text = resp.text.strip()
        assert text, "Response should not be empty"
        # SSE format: data: {...}\n\n
        assert "data: " in text

    async def test_deconstruct_stream_error_on_empty(self, async_client, auth_headers):
        """Deconstruct with no chapters should return an error status."""
        resp = await async_client.post(
            "/api/v1/projects/init/deconstruct/stream",
            json={"book_title": "测试书", "sample_chapters": []},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        text = resp.text.strip()
        assert "data: " in text

    async def test_project_export_manifest(self, async_client, auth_headers):
        """Export endpoint should return a zip file."""
        resp = await async_client.post("/api/v1/projects", json={
            "title": "ExportTestBook",
            "genre": "test",
        }, headers=auth_headers)
        assert resp.status_code == 201, f"Create failed: {resp.text}"

        # Export as zip
        resp2 = await async_client.get(
            f"/api/v1/projects/{resp.json()['id']}/export",
            headers=auth_headers,
        )
        assert resp2.status_code == 200
        assert resp2.headers.get("content-type") == "application/zip"
        assert "attachment" in resp2.headers.get("content-disposition", "")
