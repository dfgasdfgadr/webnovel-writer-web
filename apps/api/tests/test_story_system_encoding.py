import json
import pytest
from pathlib import Path

from app.story_system import StorySystem


class TestStorySystemEncoding:
    def test_reads_utf8_master_setting_on_windows(self, tmp_path: Path, monkeypatch):
        """MASTER_SETTING.json with Chinese must not use system default encoding (GBK)."""
        ss_dir = tmp_path / ".story-system"
        ss_dir.mkdir()
        data = {"title": "第六面诊室", "hook": "心理诊所悬疑"}
        (ss_dir / "MASTER_SETTING.json").write_text(
            json.dumps(data, ensure_ascii=False),
            encoding="utf-8",
        )

        story = StorySystem(tmp_path)
        loaded = story.master_setting()
        assert loaded["title"] == "第六面诊室"
        assert loaded["hook"] == "心理诊所悬疑"

    def test_roundtrip_write_read(self, tmp_path: Path):
        story = StorySystem(tmp_path)
        payload = {"genre": "悬疑", "protagonist": {"name": "林凡"}}
        story.save_master_setting(payload)
        assert story.master_setting() == payload

    def test_reads_gbk_encoded_file_and_normalizes_to_utf8(self, tmp_path: Path):
        """GBK-encoded JSON must be readable and normalized back to UTF-8."""
        ss_dir = tmp_path / ".story-system"
        ss_dir.mkdir()
        data = {"title": "斗破苍穹", "chapter": 1, "body": "三十年河东三十年河西"}
        gbk_path = ss_dir / "MASTER_SETTING.json"
        gbk_path.write_bytes(
            json.dumps(data, ensure_ascii=False).encode("gbk")
        )

        story = StorySystem(tmp_path)
        loaded = story.master_setting()
        assert loaded == data

        # Verify the file was normalized: can be read as UTF-8 without fallback
        re_read = json.loads(gbk_path.read_bytes().decode("utf-8"))
        assert re_read == data

    def test_reads_cp936_encoded_chapter_contract(self, tmp_path: Path):
        ss_dir = tmp_path / ".story-system" / "chapters"
        ss_dir.mkdir(parents=True)
        data = {"title": "第001章", "nodes": ["开篇", "悬念设置"]}
        cp936_path = ss_dir / "chapter_001.json"
        cp936_path.write_bytes(
            json.dumps(data, ensure_ascii=False).encode("cp936")
        )

        story = StorySystem(tmp_path)
        loaded = story.chapter_contract(1)
        assert loaded == data

        # Verify normalized: readable as UTF-8 without fallback
        re_read = json.loads(cp936_path.read_bytes().decode("utf-8"))
        assert re_read == data

    def test_reads_gbk_encoded_volume_contract(self, tmp_path: Path):
        ss_dir = tmp_path / ".story-system" / "volumes"
        ss_dir.mkdir(parents=True)
        data = {"title": "第一卷·崛起", "arc": "蛮荒大陆"}
        gbk_path = ss_dir / "volume_001.json"
        gbk_path.write_bytes(
            json.dumps(data, ensure_ascii=False).encode("gbk")
        )

        story = StorySystem(tmp_path)
        loaded = story.volume_contract(1)
        assert loaded == data

        # Verify normalized: readable as UTF-8 without fallback
        re_read = json.loads(gbk_path.read_bytes().decode("utf-8"))
        assert re_read == data

    def test_nonexistent_files_return_empty_dict(self, tmp_path: Path):
        story = StorySystem(tmp_path)
        assert story.master_setting() == {}
        assert story.volume_contract(99) == {}
        assert story.chapter_contract(99) == {}
