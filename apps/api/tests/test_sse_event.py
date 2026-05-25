"""Tests for _sse_event helper and Polish SSE format (BUG-3)."""

import json


class TestSseEventHelper:
    def _sse_event(self, event: str, data: dict) -> str:
        from app.routers.agents import _sse_event
        return _sse_event(event, data)

    def test_format_includes_event_line(self):
        msg = self._sse_event("start", {"type": "start", "total_issues": 5})
        assert msg.startswith("event: start\n"), f"Missing event line: {msg[:50]}"

    def test_format_includes_data_line(self):
        msg = self._sse_event("done", {"type": "done"})
        assert "data: " in msg

    def test_data_is_valid_json(self):
        msg = self._sse_event("issue_done", {"type": "issue_done", "index": 1, "issue_id": "abc"})
        lines = msg.strip().split("\n")
        data_line = [l for l in lines if l.startswith("data: ")][0]
        payload = json.loads(data_line[6:])  # after "data: "
        assert payload["type"] == "issue_done"
        assert payload["index"] == 1

    def test_ends_with_double_newline(self):
        msg = self._sse_event("done", {"type": "done"})
        assert msg.endswith("\n\n"), f"Should end with \\n\\n: {repr(msg[-10:])}"

    def test_chinese_characters_preserved(self):
        msg = self._sse_event("issue_done", {"type": "issue_done", "title": "角色矛盾"})
        assert "角色矛盾" in msg
        parsed = json.loads(msg.split("\n")[1][6:])  # data: {json}
        assert parsed["title"] == "角色矛盾"

    def test_all_sse_event_types(self):
        """Verify start, issue_done, issue_error, done events all format correctly."""
        for event_type in ["start", "issue_done", "issue_error", "done"]:
            msg = self._sse_event(event_type, {"type": event_type})
            assert f"event: {event_type}\n" in msg
            assert msg.endswith("\n\n")
