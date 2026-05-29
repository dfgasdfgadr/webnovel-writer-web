"""Tests for Reference Corpus endpoints and text splitting."""

import io
import pytest
from httpx import AsyncClient


# --- Text Splitter Tests ---

class TestChapterSplitter:
    def test_split_chinese_chapters(self):
        from app.services.text_splitter import split_into_chapters

        text = """第一章 起始
这是第一章的内容。
有很多文字在这里。

第二章 发展
这是第二章的内容。
更多文字在这里。

第三章 结局
最终章的内容。"""
        chapters = split_into_chapters(text)
        assert len(chapters) == 3
        assert chapters[0].title == "起始"
        assert chapters[0].sequence == 1
        # Header line should be removed from content (content should not start with the title line)
        assert not chapters[0].content.strip().startswith("第一章")
        assert "这是第一章的内容" in chapters[0].content
        assert chapters[1].title == "发展"
        assert chapters[2].title == "结局"

    def test_split_markdown_headers(self):
        from app.services.text_splitter import split_into_chapters

        text = """## 第1章 开始
内容开始

## 第2章 中间
中间内容

## 第3章 结束
结束内容"""
        chapters = split_into_chapters(text)
        assert len(chapters) == 3
        assert chapters[0].sequence == 1
        assert chapters[0].title == "开始"
        assert "内容开始" in chapters[0].content

    def test_split_numbered_headers(self):
        from app.services.text_splitter import split_into_chapters

        text = """## 1. 开始
内容开始

## 2. 中间
中间内容"""
        chapters = split_into_chapters(text)
        assert len(chapters) == 2
        assert chapters[0].sequence == 1
        assert chapters[0].title == "开始"

    def test_split_no_headers_fallback(self):
        from app.services.text_splitter import split_into_chapters

        text = "a" * 15000  # 15000 chars, no headers
        chapters = split_into_chapters(text)
        assert len(chapters) >= 2  # Should create pseudo-chapters
        assert all("伪章节" in ch.title for ch in chapters)

    def test_split_empty(self):
        from app.services.text_splitter import split_into_chapters
        assert split_into_chapters("") == []
        assert split_into_chapters("   ") == []

    def test_split_chapter_no_space(self):
        from app.services.text_splitter import split_into_chapters

        text = "第一章\n内容\n第二章\n更多内容"
        chapters = split_into_chapters(text)
        assert len(chapters) == 2
        assert chapters[0].sequence == 1
        assert chapters[1].sequence == 2


class TestChunkSplitter:
    def test_small_content_single_chunk(self):
        from app.services.text_splitter import split_chapter_into_chunks
        chunks = split_chapter_into_chunks("这是一小段文字。")
        assert len(chunks) == 1
        assert chunks[0].sequence == 1

    def test_large_content_multiple_chunks(self):
        from app.services.text_splitter import split_chapter_into_chunks
        text = "这是一句话。" * 500  # ~2500 chars
        chunks = split_chapter_into_chunks(text, chunk_size=800, overlap=100)
        assert len(chunks) >= 2

    def test_respects_sentence_boundary(self):
        from app.services.text_splitter import split_chapter_into_chunks
        text = "第一句。第二句。第三句。" * 200
        chunks = split_chapter_into_chunks(text, chunk_size=100, overlap=10)
        # Each chunk should end with a sentence boundary (except possibly last)
        for chunk in chunks[:-1]:
            assert chunk.content[-1] in "。！？.!?"

    def test_empty_content(self):
        from app.services.text_splitter import split_chapter_into_chunks
        assert split_chapter_into_chunks("") == []
        assert split_chapter_into_chunks("   ") == []


# --- API Tests ---

class TestReferenceCorpusAPI:
    async def test_create_corpus_from_text(self, async_client: AsyncClient, auth_headers: dict):
        resp = await async_client.post("/api/v1/reference-corpora", headers=auth_headers, json={
            "title": "测试参考书",
            "content": "第一章 开始\n这是开始的内容。\n\n第二章 结束\n这是结束的内容。",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "测试参考书"
        assert data["index_status"] == "ready"
        assert data["total_chapters"] == 2
        assert data["total_chunks"] >= 2
        assert data["total_chars"] > 0

    async def test_list_corpora(self, async_client: AsyncClient, auth_headers: dict):
        # Create a corpus first
        await async_client.post("/api/v1/reference-corpora", headers=auth_headers, json={
            "title": "列表测试书",
            "content": "第一章\n内容",
        })

        resp = await async_client.get("/api/v1/reference-corpora", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert any(c["title"] == "列表测试书" for c in data["items"])

    async def test_get_corpus_detail(self, async_client: AsyncClient, auth_headers: dict):
        create_resp = await async_client.post("/api/v1/reference-corpora", headers=auth_headers, json={
            "title": "详情测试书",
            "content": "第一章 A\n内容A\n\n第二章 B\n内容B",
        })
        corpus_id = create_resp.json()["id"]

        resp = await async_client.get(f"/api/v1/reference-corpora/{corpus_id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "详情测试书"
        assert len(data["chapters"]) == 2
        assert data["chapters"][0]["title"] == "A"
        assert data["chapters"][1]["title"] == "B"

    async def test_list_chapters(self, async_client: AsyncClient, auth_headers: dict):
        create_resp = await async_client.post("/api/v1/reference-corpora", headers=auth_headers, json={
            "title": "章节列表测试",
            "content": "第一章 X\n内容\n第二章 Y\n内容",
        })
        corpus_id = create_resp.json()["id"]

        resp = await async_client.get(f"/api/v1/reference-corpora/{corpus_id}/chapters", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert data["chapters"][0]["title"] == "X"
        assert data["chapters"][1]["title"] == "Y"

    async def test_list_chunks(self, async_client: AsyncClient, auth_headers: dict):
        create_resp = await async_client.post("/api/v1/reference-corpora", headers=auth_headers, json={
            "title": "Chunk列表测试",
            "content": "第一章 测试\n" + "这是一句话。" * 200,
        })
        corpus_id = create_resp.json()["id"]

        # Get chapter id
        chapters_resp = await async_client.get(f"/api/v1/reference-corpora/{corpus_id}/chapters", headers=auth_headers)
        chapter_id = chapters_resp.json()["chapters"][0]["id"]

        resp = await async_client.get(
            f"/api/v1/reference-corpora/{corpus_id}/chapters/{chapter_id}/chunks",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert all("content" in c for c in data["chunks"])

    async def test_search_corpus(self, async_client: AsyncClient, auth_headers: dict):
        create_resp = await async_client.post("/api/v1/reference-corpora", headers=auth_headers, json={
            "title": "搜索测试书",
            "content": "第一章\n这是一个关于修仙的故事。主角获得了逆天机缘。\n\n第二章\n修仙之路充满艰辛，主角不断突破。",
        })
        corpus_id = create_resp.json()["id"]

        resp = await async_client.post(
            f"/api/v1/reference-corpora/{corpus_id}/search",
            headers=auth_headers,
            json={"query": "修仙", "top_k": 5},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "修仙"
        assert data["total"] > 0
        assert len(data["results"]) > 0
        # Results should contain the keyword
        for r in data["results"]:
            assert "score" in r
            assert "content" in r

    async def test_search_not_ready(self, async_client: AsyncClient, auth_headers: dict):
        # Create corpus manually to simulate not-ready state
        create_resp = await async_client.post("/api/v1/reference-corpora", headers=auth_headers, json={
            "title": "搜索状态测试",
            "content": "第一章\n内容",
        })
        corpus_id = create_resp.json()["id"]

        # This corpus should be ready by now, but test a non-existent corpus
        resp = await async_client.post(
            f"/api/v1/reference-corpora/nonexistent/search",
            headers=auth_headers,
            json={"query": "测试", "top_k": 5},
        )
        assert resp.status_code == 404

    async def test_delete_corpus(self, async_client: AsyncClient, auth_headers: dict):
        create_resp = await async_client.post("/api/v1/reference-corpora", headers=auth_headers, json={
            "title": "删除测试书",
            "content": "第一章\n内容",
        })
        corpus_id = create_resp.json()["id"]

        resp = await async_client.delete(f"/api/v1/reference-corpora/{corpus_id}", headers=auth_headers)
        assert resp.status_code == 204

        get_resp = await async_client.get(f"/api/v1/reference-corpora/{corpus_id}", headers=auth_headers)
        assert get_resp.status_code == 404

    async def test_corpus_isolation(self, async_client: AsyncClient, auth_headers: dict):
        # Create corpus as testuser
        create_resp = await async_client.post("/api/v1/reference-corpora", headers=auth_headers, json={
            "title": "隔离测试",
            "content": "第一章\n内容",
        })
        corpus_id = create_resp.json()["id"]

        # Create another user
        await async_client.post("/api/v1/auth/register", json={
            "username": "otheruser_ref",
            "password": "otherpass",
        })
        login_resp = await async_client.post("/api/v1/auth/login", data={
            "username": "otheruser_ref",
            "password": "otherpass",
        })
        other_token = login_resp.json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # Other user should not see this corpus
        resp = await async_client.get(f"/api/v1/reference-corpora/{corpus_id}", headers=other_headers)
        assert resp.status_code == 404

        # Other user's list should not include this corpus
        list_resp = await async_client.get("/api/v1/reference-corpora", headers=other_headers)
        assert list_resp.status_code == 200
        assert not any(c["id"] == corpus_id for c in list_resp.json()["items"])

    async def test_upload_file(self, async_client: AsyncClient, auth_headers: dict):
        file_content = "第一章 上传测试\n这是上传的内容。\n\n第二章 结束\n结束了。"
        file = io.BytesIO(file_content.encode("utf-8"))

        resp = await async_client.post(
            "/api/v1/reference-corpora/upload",
            headers=auth_headers,
            data={"title": "上传测试书"},
            files={"file": ("test.txt", file, "text/plain")},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "上传测试书"
        assert data["source_type"] == "upload"
        assert data["source_filename"] == "test.txt"
        assert data["total_chapters"] == 2

    async def test_upload_invalid_extension(self, async_client: AsyncClient, auth_headers: dict):
        file = io.BytesIO(b"some content")
        resp = await async_client.post(
            "/api/v1/reference-corpora/upload",
            headers=auth_headers,
            files={"file": ("test.pdf", file, "application/pdf")},
        )
        assert resp.status_code == 400

    async def test_create_corpus_empty_content(self, async_client: AsyncClient, auth_headers: dict):
        resp = await async_client.post("/api/v1/reference-corpora", headers=auth_headers, json={
            "title": "空内容测试",
            "content": "",
        })
        assert resp.status_code == 422  # Pydantic validation error

    async def test_get_corpus_not_found(self, async_client: AsyncClient, auth_headers: dict):
        resp = await async_client.get("/api/v1/reference-corpora/nonexistent-id", headers=auth_headers)
        assert resp.status_code == 404

    async def test_pseudo_chapters_fallback(self, async_client: AsyncClient, auth_headers: dict):
        # Text with no chapter headers — should create pseudo-chapters
        text = "这是一段没有章节标题的长文本。" * 500  # ~8500 chars
        resp = await async_client.post("/api/v1/reference-corpora", headers=auth_headers, json={
            "title": "伪章节测试",
            "content": text,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["total_chapters"] >= 1
        # Get detail and verify chapter titles are pseudo
        detail_resp = await async_client.get(
            f"/api/v1/reference-corpora/{data['id']}", headers=auth_headers
        )
        assert detail_resp.status_code == 200
        chapters = detail_resp.json()["chapters"]
        assert all("伪章节" in ch["title"] for ch in chapters)
