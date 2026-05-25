"""Tests for CLI emoji removal (BUG-4)."""

import ast
import inspect
from pathlib import Path


class TestCliNoEmoji:
    """Verify CLI cmd_list and cmd_review contain no emoji characters."""

    CLI_PATH = Path(__file__).resolve().parents[3] / "packages" / "cli" / "novelcraft.py"

    def test_cmd_list_has_no_emoji(self):
        """cmd_list function should not contain emoji characters."""
        source = self.CLI_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "cmd_list":
                func_source = ast.get_source_segment(source, node)
                assert func_source is not None, "Could not extract cmd_list source"
                assert "\U0001f4d7" not in func_source, "Emoji found in cmd_list"
                assert "\U0001f4d5" not in func_source, "Emoji found in cmd_list"
                assert "📗" not in func_source, "Emoji found in cmd_list"
                assert "📕" not in func_source, "Emoji found in cmd_list"
                break
        else:
            pytest.fail("cmd_list function not found in novelcraft.py")

    def test_cmd_review_has_no_emoji(self):
        """cmd_review function should not contain emoji characters."""
        source = self.CLI_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "cmd_review":
                func_source = ast.get_source_segment(source, node)
                assert func_source is not None, "Could not extract cmd_review source"
                assert "\U0001f534" not in func_source, "Emoji found in cmd_review"
                assert "\U0001f7e1" not in func_source, "Emoji found in cmd_review"
                assert "⚪" not in func_source, "Emoji found in cmd_review"
                assert "🔴" not in func_source, "Emoji found in cmd_review"
                assert "🟡" not in func_source, "Emoji found in cmd_review"
                assert "⚪" not in func_source, "Emoji found in cmd_review"
                break
        else:
            pytest.fail("cmd_review function not found in novelcraft.py")

    def test_uses_ascii_status_icons(self):
        """cmd_list should use ASCII [*] and [ ] instead of emoji."""
        source = self.CLI_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "cmd_list":
                func_source = ast.get_source_segment(source, node)
                assert "[*]" in func_source, "cmd_list should use [*] for active status"
                assert "[ ]" in func_source, "cmd_list should use [ ] for inactive status"
                break

    def test_uses_ascii_severity_icons(self):
        """cmd_review should use ASCII [X], [!], [-] instead of emoji."""
        source = self.CLI_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "cmd_review":
                func_source = ast.get_source_segment(source, node)
                assert "[X]" in func_source, "cmd_review should use [X] for blocking"
                assert "[!]" in func_source, "cmd_review should use [!] for major"
                break
