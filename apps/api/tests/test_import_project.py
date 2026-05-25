import pytest
from httpx import AsyncClient
from pathlib import Path


def _write_sample_project(root: Path) -> None:
    (root / "设定集").mkdir(parents=True)
    (root / "大纲").mkdir(parents=True)
    (root / "正文").mkdir(parents=True)
    (root / "设定集" / "世界观.md").write_text("# 世界观\n\n测试设定", encoding="utf-8")
    (root / "大纲" / "总纲.md").write_text("# 总纲\n\n测试故事", encoding="utf-8")
    (root / "正文" / "第1章-开篇.md").write_text("# 第一章\n\n正文内容", encoding="utf-8")


class TestImportProject:
    async def test_import_project_creates_cards_and_chapters(
        self, async_client: AsyncClient, auth_headers: dict, tmp_path: Path, monkeypatch
    ):
        source = tmp_path / "sample-novel"
        _write_sample_project(source)

        monkeypatch.setattr(
            "app.config.settings.novelcraft_data_root",
            str(tmp_path / "data"),
        )

        scan_resp = await async_client.post(
            "/api/v1/projects/import/scan",
            json={"source_path": str(source)},
            headers=auth_headers,
        )
        assert scan_resp.status_code == 200
        assert scan_resp.json()["valid"] is True
        assert scan_resp.json()["chapter_count"] == 1
        assert scan_resp.json()["settings_count"] == 1

        import_resp = await async_client.post(
            "/api/v1/projects/import",
            json={"source_path": str(source)},
            headers=auth_headers,
        )
        assert import_resp.status_code == 201, import_resp.text
        data = import_resp.json()
        assert data["title"] == "sample-novel"

        pid = data["id"]
        chapters_resp = await async_client.get(
            f"/api/v1/projects/{pid}/chapters",
            headers=auth_headers,
        )
        assert chapters_resp.status_code == 200
        chapters = chapters_resp.json()["items"]
        assert len(chapters) == 1
        assert "正文内容" in chapters[0]["content"]

        cards_resp = await async_client.get(
            f"/api/v1/projects/{pid}/cards",
            headers=auth_headers,
        )
        assert cards_resp.status_code == 200
        cards = cards_resp.json()
        assert len(cards) >= 1
        assert any(c["label"] == "世界观" for c in cards)
